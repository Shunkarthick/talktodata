from typing import Dict, Any, Optional
import time
from uuid import UUID, uuid4
from sqlalchemy.orm import Session

from app.services.langchain.chains.text_to_sql_chain import TextToSQLChain
from app.services.bigquery.bigquery_service import BigQueryService
from app.models import QueryLog, Conversation, Message
from app.core.logging import logger


class QueryService:
    """
    Main service for handling text-to-SQL queries
    Orchestrates LangChain and BigQuery services
    """

    def __init__(self, db_session: Session):
        self.db = db_session

    async def process_question(
        self,
        project_id: str,
        user_id: str,
        question: str,
        conversation_id: Optional[str] = None,
        model: str = "claude-3-5-sonnet-20241022",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Process a natural language question:
        1. Convert to SQL using LangChain
        2. Execute on BigQuery
        3. Generate insights
        4. Log everything

        Returns:
            dict: Complete query response with SQL, results, insights
        """
        total_start_time = time.time()
        query_log_id = uuid4()

        # Initialize log entry
        log_entry = QueryLog(
            id=query_log_id,
            user_id=user_id,
            project_id=project_id,
            conversation_id=conversation_id,
            user_question=question,
            model_used=model,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        try:
            # Step 1: Generate SQL using LangChain
            logger.info(f"Generating SQL for question: {question}")

            sql_chain = TextToSQLChain(
                project_id=project_id,
                user_id=user_id,
                conversation_id=conversation_id,
                db_session=self.db,
                model=model,
            )

            sql_result = await sql_chain.generate_sql(question)

            # Update log
            log_entry.generated_sql = sql_result["sql"]
            log_entry.sql_generation_time_ms = sql_result["generation_time_ms"]
            log_entry.sql_tokens_used = sql_result["tokens_used"]

            # Step 2: Validate SQL (optional safety check)
            if self._is_dangerous_sql(sql_result["sql"]):
                raise Exception("SQL query contains forbidden operations (DROP, DELETE, etc.)")

            # Step 3: Execute SQL on BigQuery
            logger.info("Executing SQL on BigQuery")

            bigquery_service = BigQueryService(
                project_id=project_id, db_session=self.db
            )

            execution_result = await bigquery_service.execute_query(sql_result["sql"])

            # Update log
            log_entry.execution_status = "success"
            log_entry.execution_time_ms = execution_result["execution_time_ms"]
            log_entry.rows_returned = execution_result["rows_returned"]
            log_entry.bytes_processed = execution_result["bytes_processed"]

            # Step 4: Generate insights (optional - can be done with another LLM call)
            insights = self._generate_basic_insights(execution_result)

            # Step 5: Suggest visualization
            chart_suggestion = self._suggest_chart(execution_result)

            # Calculate total time
            total_time_ms = int((time.time() - total_start_time) * 1000)

            # Save log to database
            self.db.add(log_entry)

            # Save to conversation if provided
            if conversation_id:
                self._save_to_conversation(
                    conversation_id=conversation_id,
                    question=question,
                    sql=sql_result["sql"],
                    tokens=sql_result["tokens_used"],
                )

            self.db.commit()

            logger.info(f"Query processed successfully in {total_time_ms}ms")

            return {
                "query_id": query_log_id,
                "sql": sql_result["sql"],
                "result": execution_result,
                "insights": insights,
                "suggested_chart": chart_suggestion,
                "tokens_used": sql_result["tokens_used"],
                "sql_generation_time_ms": sql_result["generation_time_ms"],
                "total_time_ms": total_time_ms,
                "error": None,
            }

        except Exception as e:
            # Log error
            logger.error(f"Query processing failed: {str(e)}")

            log_entry.execution_status = "failed"
            log_entry.error_message = str(e)
            log_entry.error_type = type(e).__name__

            self.db.add(log_entry)
            self.db.commit()

            total_time_ms = int((time.time() - total_start_time) * 1000)

            return {
                "query_id": query_log_id,
                "sql": log_entry.generated_sql,
                "result": None,
                "insights": None,
                "suggested_chart": None,
                "tokens_used": log_entry.sql_tokens_used or 0,
                "sql_generation_time_ms": log_entry.sql_generation_time_ms or 0,
                "total_time_ms": total_time_ms,
                "error": str(e),
            }

    def _is_dangerous_sql(self, sql: str) -> bool:
        """Check for dangerous SQL operations"""
        sql_upper = sql.upper()
        forbidden_keywords = ["DROP", "DELETE", "TRUNCATE", "ALTER", "CREATE", "UPDATE"]

        for keyword in forbidden_keywords:
            if keyword in sql_upper:
                return True

        return False

    def _generate_basic_insights(self, result: Dict[str, Any]) -> str:
        """Generate basic insights from query results"""
        rows_count = result["rows_returned"]

        if rows_count == 0:
            return "No results found for your query."

        insights = f"Query returned {rows_count} row(s). "

        # Add more sophisticated insights here
        # Could use another LLM call to Claude for deeper analysis

        return insights

    def _suggest_chart(self, result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Suggest chart type based on result schema"""
        schema = result.get("schema", [])
        rows_count = result["rows_returned"]

        if rows_count == 0 or len(schema) == 0:
            return None

        # Simple heuristic
        if len(schema) == 1:
            return {"type": "metric", "title": "Single Value"}

        if len(schema) == 2:
            # Check if first column is date/string and second is numeric
            col1_type = schema[0]["type"]
            col2_type = schema[1]["type"]

            if col1_type in ["DATE", "DATETIME", "TIMESTAMP"]:
                return {"type": "line", "title": "Trend Over Time"}
            elif col1_type == "STRING" and col2_type in ["INTEGER", "FLOAT", "NUMERIC"]:
                return {"type": "bar", "title": "Comparison"}

        if len(schema) >= 3:
            return {"type": "table", "title": "Data Table"}

        return {"type": "table", "title": "Data View"}

    def _save_to_conversation(
        self,
        conversation_id: str,
        question: str,
        sql: str,
        tokens: int,
    ):
        """Save question and response to conversation"""
        # Save user message
        user_message = Message(
            conversation_id=conversation_id,
            role="user",
            content=question,
            tokens_used=0,
        )
        self.db.add(user_message)

        # Save assistant message with SQL
        assistant_content = f"Generated SQL:\n```sql\n{sql}\n```"
        assistant_message = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=assistant_content,
            tokens_used=tokens,
        )
        self.db.add(assistant_message)

        # Update conversation updated_at
        conversation = self.db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        if conversation:
            # Auto-generate title from first question if not set
            if not conversation.title:
                conversation.title = question[:100]

    async def execute_sql_directly(
        self,
        project_id: str,
        user_id: str,
        sql: str,
        conversation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute SQL directly without text-to-SQL conversion"""
        total_start_time = time.time()

        try:
            # Validate SQL
            if self._is_dangerous_sql(sql):
                raise Exception("SQL contains forbidden operations")

            # Execute on BigQuery
            bigquery_service = BigQueryService(project_id=project_id, db_session=self.db)
            result = await bigquery_service.execute_query(sql)

            total_time_ms = int((time.time() - total_start_time) * 1000)

            return {
                "sql": sql,
                "result": result,
                "total_time_ms": total_time_ms,
                "error": None,
            }

        except Exception as e:
            logger.error(f"Direct SQL execution failed: {str(e)}")
            total_time_ms = int((time.time() - total_start_time) * 1000)

            return {
                "sql": sql,
                "result": None,
                "total_time_ms": total_time_ms,
                "error": str(e),
            }
