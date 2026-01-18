from typing import Dict, Any, Optional
import time
from sqlalchemy.orm import Session
from langchain.prompts import PromptTemplate
from langchain_anthropic import ChatAnthropic
from langchain.chains import LLMChain

from app.core.config import settings
from app.models import GlobalInstruction, ProjectMemory, ProjectInstruction, Project, Message


class TextToSQLChain:
    """
    LangChain-based Text-to-SQL converter with three-tier memory system
    """

    def __init__(
        self,
        project_id: str,
        user_id: str,
        conversation_id: Optional[str],
        db_session: Session,
        model: str = "claude-3-5-sonnet-20241022",
    ):
        self.project_id = project_id
        self.user_id = user_id
        self.conversation_id = conversation_id
        self.db = db_session
        self.model = model

        # Initialize Claude LLM
        self.llm = ChatAnthropic(
            model=model,
            temperature=0,
            max_tokens=4096,
            anthropic_api_key=settings.ANTHROPIC_API_KEY,
        )

        # Metrics
        self.metrics = {
            "tokens_used": 0,
            "start_time": None,
            "end_time": None,
        }

    def _load_global_memory(self) -> str:
        """Load global instructions from database"""
        instructions = (
            self.db.query(GlobalInstruction)
            .filter(GlobalInstruction.active == True)
            .order_by(GlobalInstruction.priority)
            .all()
        )

        if not instructions:
            return """- Always use LIMIT clause for safety
- Never use DROP, DELETE, or UPDATE statements
- Use BigQuery standard SQL syntax
- Optimize queries for cost (avoid SELECT *, use partitions when available)"""

        memory_text = "\n".join([f"- {inst.instruction_text}" for inst in instructions])
        return memory_text

    def _load_project_memory(self) -> str:
        """Load project-specific memory (business rules, instructions)"""
        # Get business rules
        rules = (
            self.db.query(ProjectMemory)
            .filter(ProjectMemory.project_id == self.project_id)
            .all()
        )

        # Get project instructions
        instructions = (
            self.db.query(ProjectInstruction)
            .filter(ProjectInstruction.project_id == self.project_id)
            .filter(ProjectInstruction.active == True)
            .order_by(ProjectInstruction.priority)
            .all()
        )

        memory_text = ""

        if rules:
            memory_text += "BUSINESS RULES & DOMAIN KNOWLEDGE:\n"
            for rule in rules:
                memory_text += f"- {rule.key}: {rule.content}\n"
            memory_text += "\n"

        if instructions:
            memory_text += "PROJECT-SPECIFIC INSTRUCTIONS:\n"
            for inst in instructions:
                memory_text += f"- {inst.instruction_text}\n"

        return memory_text if memory_text else "No project-specific rules defined."

    def _load_conversation_history(self) -> str:
        """Load recent conversation history for context"""
        if not self.conversation_id:
            return ""

        messages = (
            self.db.query(Message)
            .filter(Message.conversation_id == self.conversation_id)
            .order_by(Message.created_at.desc())
            .limit(5)  # Last 5 messages
            .all()
        )

        if not messages:
            return ""

        # Reverse to chronological order
        messages = list(reversed(messages))

        history_text = "RECENT CONVERSATION HISTORY:\n"
        for msg in messages:
            role = msg.role.upper()
            content = msg.content[:200]  # Truncate long messages
            history_text += f"{role}: {content}\n"

        return history_text

    def _get_schema_context(self) -> str:
        """Get BigQuery schema for the project"""
        project = self.db.query(Project).filter(Project.id == self.project_id).first()

        if not project or not project.schema_cache:
            return "No schema available. Please configure BigQuery connection first."

        schema_text = "AVAILABLE TABLES AND SCHEMA:\n\n"

        for table_name, table_info in project.schema_cache.items():
            schema_text += f"Table: {project.bigquery_project_id}.{project.bigquery_dataset}.{table_name}\n"

            if "columns" in table_info:
                schema_text += "Columns:\n"
                for col in table_info["columns"]:
                    col_name = col.get("name", "unknown")
                    col_type = col.get("type", "unknown")
                    schema_text += f"  - {col_name} ({col_type})\n"

            schema_text += "\n"

        return schema_text

    async def generate_sql(self, user_question: str) -> Dict[str, Any]:
        """
        Main method: Generate BigQuery SQL from natural language

        Returns:
            dict: {
                'sql': str,
                'tokens_used': int,
                'generation_time_ms': int
            }
        """
        self.metrics["start_time"] = time.time()

        # Assemble context from three-tier memory
        global_memory = self._load_global_memory()
        project_memory = self._load_project_memory()
        conversation_history = self._load_conversation_history()
        schema = self._get_schema_context()

        # Build prompt template
        template = """You are a SQL expert specializing in Google BigQuery.
Your task is to generate precise BigQuery SQL based on the user's question.

GLOBAL RULES (ALWAYS FOLLOW):
{global_memory}

{project_memory}

{schema}

{conversation_history}

IMPORTANT FORMATTING RULES:
- Return ONLY the SQL query, nothing else
- Do NOT wrap the query in ```sql``` or any markdown
- Use proper BigQuery syntax (not MySQL or PostgreSQL)
- Always use fully qualified table names (project.dataset.table)
- Include appropriate LIMIT clause (default: LIMIT 100)
- Optimize for performance and cost

USER QUESTION: {question}

SQL:"""

        prompt = PromptTemplate(
            input_variables=["question", "global_memory", "project_memory", "schema", "conversation_history"],
            template=template,
        )

        # Create chain
        chain = prompt | self.llm

        # Execute
        try:
            result = await chain.ainvoke(
                {
                    "question": user_question,
                    "global_memory": global_memory,
                    "project_memory": project_memory,
                    "schema": schema,
                    "conversation_history": conversation_history,
                }
            )

            # Extract SQL from response
            sql = result.content.strip()

            # Remove markdown code blocks if present
            if sql.startswith("```sql"):
                sql = sql.replace("```sql", "").replace("```", "").strip()
            elif sql.startswith("```"):
                sql = sql.replace("```", "").strip()

            # Calculate metrics
            self.metrics["end_time"] = time.time()

            # Estimate tokens (rough approximation: 4 chars = 1 token)
            total_chars = len(template) + len(user_question) + len(sql)
            self.metrics["tokens_used"] = total_chars // 4

            return {
                "sql": sql,
                "tokens_used": self.metrics["tokens_used"],
                "generation_time_ms": int(
                    (self.metrics["end_time"] - self.metrics["start_time"]) * 1000
                ),
            }

        except Exception as e:
            self.metrics["end_time"] = time.time()
            raise Exception(f"SQL generation failed: {str(e)}")
