import openai
import time
from typing import List, Dict, Any, Optional
from ..models.schema import DatabaseSchema
from ..models.query import QueryRequest, QueryResult
from ..core.validator import QueryValidator
from ..core.executor import QueryExecutor, ExecutionError
from ..utils.config import Config
from pydantic import BaseModel

class SQLQueryOutput(BaseModel):
    query: str
    explanation: Optional[str] = None

class SQLAgent:
    def __init__(self, config: Config, db_schema: Optional[str] = None):
        """
        Initialize the SQL Agent.
        
        Args:
            config (Config): Configuration including API keys and database settings
            db_schema (Optional[str]): Database schema string for prompts
        """
        self.config = config
        self.validator = QueryValidator()
        self.executor = QueryExecutor(config.db_connection_string)
        self.client = openai.OpenAI(api_key=config.openai_api_key)
        self.context_history: List[Dict] = []
        self.db_schema = db_schema

    def _construct_prompt(self, question: str, context: Optional[str] = None) -> str:
        """
        Construct the prompt for the OpenAI API.
        """
        if not self.db_schema:
            raise ValueError("Database schema is required but not provided")
            
        base_prompt = f"""Given the following PostgreSQL database schema:
        {self.db_schema}
        
        Generate a PostgreSQL query for the following question: {question}
        
        Important notes:
        - Use PostgreSQL-specific date/time functions (e.g., date_trunc, extract)
        - Use INTERVAL syntax like: CURRENT_DATE - INTERVAL '1 month'
        - Always use single quotes for string and interval literals
        - For month comparison, use EXTRACT(MONTH FROM timestamp_column)
        """
        
        if context:
            base_prompt += f"\nAdditional context: {context}"
            
        return base_prompt

    async def generate_query(self, request: QueryRequest) -> QueryResult:
        """
        Generate SQL query from natural language using OpenAI.
        """
        start_time = time.time()
        prompt = self._construct_prompt(request.question, request.context)
        
        # Define the function schema for structured output
        functions = [
            {
                "name": "generate_sql_query",
                "description": "Generate a PostgreSQL query based on the natural language question",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The PostgreSQL query that answers the question"
                        },
                        "explanation": {
                            "type": "string",
                            "description": "Optional explanation of how the query works"
                        }
                    },
                    "required": ["query"]
                }
            }
        ]

        try:
            response = self.client.chat.completions.create(
                model=self.config.model_name,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a PostgreSQL expert. Generate PostgreSQL-compatible SQL queries using appropriate PostgreSQL date/time functions and syntax."
                    },
                    {"role": "user", "content": prompt}
                ],
                functions=functions,
                function_call={"name": "generate_sql_query"}
            )
            
            # Parse the function call response
            function_response = response.choices[0].message.function_call
            query_output = SQLQueryOutput.model_validate_json(function_response.arguments)
            
            # Execute the query
            results = await self.executor.execute(query_output.query)
            
            self.context_history.append({
                "question": request.question,
                "context": request.context,
                "generated_query": query_output.query,
                "explanation": query_output.explanation
            })
            
            return QueryResult(
                query=query_output.query,
                results=results,
                execution_time=time.time() - start_time,
                explanation=query_output.explanation
            )
            
        except Exception as e:
            raise Exception(f"Error generating SQL query: {str(e)}")

    async def process_request(self, request: QueryRequest) -> QueryResult:
        """
        Process a natural language query request.
        
        This is the main entry point that handles the complete workflow:
        1. Generate SQL query
        2. Validate the query
        3. Execute the query
        """
        try:
            start_time = time.time()
            query_result = await self.generate_query(request)
            is_valid, error = self.validator.validate(query_result.query)
            if not is_valid:
                raise ValidationError(error or "Query validation failed")
                
            results = await self.executor.execute_with_timeout(
                query_result.query,
                timeout_seconds=self.config.query_timeout
            )
            
            return QueryResult(
                query=query_result.query,
                results=results,
                execution_time=time.time() - start_time,
                explanation=query_result.explanation
            )
            
        except ExecutionError as e:
            raise Exception(f"Query execution failed: {str(e)}") 