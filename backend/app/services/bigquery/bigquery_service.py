from typing import Dict, Any, List, Optional
import json
import time
from google.cloud import bigquery
from google.oauth2 import service_account
from sqlalchemy.orm import Session

from app.models import Project
from app.core.logging import logger


class BigQueryService:
    """Service for BigQuery operations"""

    def __init__(self, project_id: str, db_session: Session):
        self.project_id = project_id
        self.db = db_session
        self.client: Optional[bigquery.Client] = None

    def _get_client(self) -> bigquery.Client:
        """Get or create BigQuery client"""
        if self.client:
            return self.client

        # Get project from database
        project = self.db.query(Project).filter(Project.id == self.project_id).first()

        if not project or not project.credentials_encrypted:
            raise ValueError("BigQuery credentials not configured for this project")

        # Decrypt credentials (in production, you'd decrypt here)
        # For now, assuming credentials_encrypted contains the JSON string
        credentials_dict = json.loads(project.credentials_encrypted)

        # Create credentials object
        credentials = service_account.Credentials.from_service_account_info(
            credentials_dict
        )

        # Create client
        self.client = bigquery.Client(
            credentials=credentials,
            project=project.bigquery_project_id,
        )

        return self.client

    async def execute_query(
        self, sql: str, timeout: int = 60
    ) -> Dict[str, Any]:
        """
        Execute a BigQuery SQL query

        Returns:
            dict: {
                'rows': List[Dict],
                'schema': List[Dict],
                'rows_returned': int,
                'execution_time_ms': int,
                'bytes_processed': int
            }
        """
        start_time = time.time()

        try:
            client = self._get_client()

            # Configure query job
            job_config = bigquery.QueryJobConfig(
                use_query_cache=True,
                use_legacy_sql=False,
            )

            # Execute query
            logger.info(f"Executing BigQuery SQL: {sql[:200]}...")
            query_job = client.query(sql, job_config=job_config, timeout=timeout)

            # Wait for results
            results = query_job.result()

            # Convert to list of dicts
            rows = []
            for row in results:
                rows.append(dict(row.items()))

            # Get schema
            schema = []
            if results.schema:
                for field in results.schema:
                    schema.append({
                        "name": field.name,
                        "type": field.field_type,
                    })

            # Calculate execution time
            execution_time_ms = int((time.time() - start_time) * 1000)

            # Get bytes processed
            bytes_processed = query_job.total_bytes_processed or 0

            logger.info(
                f"Query executed successfully. Rows: {len(rows)}, "
                f"Time: {execution_time_ms}ms, Bytes: {bytes_processed}"
            )

            return {
                "rows": rows,
                "schema": schema,
                "rows_returned": len(rows),
                "execution_time_ms": execution_time_ms,
                "bytes_processed": bytes_processed,
            }

        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            logger.error(f"BigQuery execution failed: {str(e)}")
            raise Exception(f"Query execution failed: {str(e)}")

    async def get_schema(self) -> Dict[str, Any]:
        """
        Extract schema from BigQuery dataset

        Returns:
            dict: {
                'table_name': {
                    'columns': [{'name': str, 'type': str}, ...],
                    'row_count': int
                },
                ...
            }
        """
        try:
            client = self._get_client()
            project = self.db.query(Project).filter(Project.id == self.project_id).first()

            if not project.bigquery_dataset:
                raise ValueError("BigQuery dataset not configured")

            dataset_id = f"{project.bigquery_project_id}.{project.bigquery_dataset}"
            dataset = client.get_dataset(dataset_id)

            schema_info = {}

            # List all tables in dataset
            tables = client.list_tables(dataset)

            for table_ref in tables:
                table = client.get_table(table_ref)

                # Get columns
                columns = []
                for field in table.schema:
                    columns.append({
                        "name": field.name,
                        "type": field.field_type,
                        "mode": field.mode,
                        "description": field.description or "",
                    })

                schema_info[table.table_id] = {
                    "columns": columns,
                    "row_count": table.num_rows,
                    "size_bytes": table.num_bytes,
                }

            logger.info(f"Schema extracted for {len(schema_info)} tables")
            return schema_info

        except Exception as e:
            logger.error(f"Schema extraction failed: {str(e)}")
            raise Exception(f"Failed to extract schema: {str(e)}")

    async def test_connection(self) -> bool:
        """Test BigQuery connection"""
        try:
            client = self._get_client()
            # Try a simple query
            query = "SELECT 1 as test"
            query_job = client.query(query, timeout=10)
            query_job.result()
            logger.info("BigQuery connection test successful")
            return True
        except Exception as e:
            logger.error(f"BigQuery connection test failed: {str(e)}")
            return False

    async def validate_sql(self, sql: str) -> Dict[str, Any]:
        """
        Validate SQL without executing (dry run)

        Returns:
            dict: {
                'valid': bool,
                'error': Optional[str],
                'estimated_bytes': int
            }
        """
        try:
            client = self._get_client()

            job_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)

            query_job = client.query(sql, job_config=job_config)

            return {
                "valid": True,
                "error": None,
                "estimated_bytes": query_job.total_bytes_processed,
            }

        except Exception as e:
            return {
                "valid": False,
                "error": str(e),
                "estimated_bytes": 0,
            }
