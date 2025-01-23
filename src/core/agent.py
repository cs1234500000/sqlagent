import openai
import time
import asyncio
from typing import List, Dict, Any, Optional
from ..models.schema import DatabaseSchema
from ..models.query import QueryRequest, QueryResult
from ..core.validator import QueryValidator
from ..core.executor import QueryExecutor, ExecutionError
from ..utils.config import Config
from pydantic import BaseModel
from ..ai.prompt_builder import PromptBuilder
from ..ai.context import ContextManager
from ..ai.feedback import FeedbackCollector
from ..ai.templates import QueryTemplates, TemplateType
from ..database.schema_generator import SchemaGenerator
from ..database.data_importer import DataImporter

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
        self.db_schema = db_schema  # User provided schema
        self.context = None
        self.templates = QueryTemplates()
        
        # Initialize AI components
        self.prompt_builder = PromptBuilder()
        self.context_manager = ContextManager()
        self.feedback_collector = FeedbackCollector()
        self.schema_generator = SchemaGenerator(config)

    def _construct_prompt(self, question: str, context: Optional[str] = None) -> str:
        """
        Construct the prompt for the OpenAI API using PromptBuilder.
        """
        # Check if we have either user-provided schema or generated schema
        if not self.db_schema and not self.context:
            raise ValueError("Database schema is required. Either provide it during initialization or generate it using create_schema_from_csv")
            
        # Use either the user-provided schema or the generated context
        schema_context = self.db_schema if self.db_schema else self.context
            
        # Analyze user intent
        intent = self.context_manager.analyze_user_intent(question)
        
        # Build context
        context_data = self.context_manager.build_context(
            question, 
            self.context_manager.conversation_history
        )
        
        # Get relevant examples
        examples = self.feedback_collector.get_learning_examples()
        
        # Build and optimize prompt
        prompt = self.prompt_builder.build_prompt(
            question=question,
            schema=schema_context,
            context=context_data if context else None
        )
        
        # Add examples if available
        if examples:
            prompt = self.prompt_builder.add_examples(prompt, examples)
            
        # Optimize tokens
        return self.prompt_builder.optimize_tokens(prompt, self.config.max_tokens)

    async def generate_query(self, request: QueryRequest) -> QueryResult:
        """
        Generate SQL query from natural language using OpenAI.
        """
        start_time = time.time()
        prompt = self._construct_prompt(request.question, request.context)
        
        # Define the function schema based on whether explanation is requested
        function_params = {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The PostgreSQL query that answers the question"
                }
            },
            "required": ["query"]
        }
        
        if request.include_explanation:
            function_params["properties"]["explanation"] = {
                "type": "string",
                "description": "Optional explanation of how the query works"
            }

        functions = [
            {
                "name": "generate_sql_query",
                "description": "Generate a PostgreSQL query based on the natural language question",
                "parameters": function_params
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
            
            # Create query result
            result = QueryResult(
                query=query_output.query,
                results=results,
                execution_time=time.time() - start_time,
                explanation=query_output.explanation if request.include_explanation else None
            )
            
            # Update conversation history
            self.context_manager.maintain_conversation(request, result)
            
            # Add successful query to feedback
            self.feedback_collector.add_feedback(
                query_result=result,
                feedback_type="success",
                feedback_text="Query executed successfully"
            )
            
            return result
            
        except Exception as e:
            # Record failed query in feedback
            error_result = QueryResult(
                query=str(e),
                results=[],
                execution_time=time.time() - start_time,
                error=str(e)
            )
            self.feedback_collector.add_feedback(
                query_result=error_result,
                feedback_type="failure",
                feedback_text=str(e)
            )
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

    async def create_schema_from_csv(self, 
                                   csv_path: str, 
                                   description: Optional[str] = None) -> DatabaseSchema:
        """
        Create database schema from CSV file using LLM.
        
        Args:
            csv_path: Path to CSV file
            description: Optional natural language description
            
        Returns:
            DatabaseSchema: Generated schema
        """
        return await self.schema_generator.generate_schema(csv_path, description)

    async def get_schema_from_database(self) -> DatabaseSchema:
        """
        Get existing schema from database.
        
        Returns:
            DatabaseSchema: Current database schema
        """
        return await self.executor.get_schema()

    async def apply_schema(self, schema: DatabaseSchema):
        """
        Apply database schema and store it for context.
        For LLM-generated schemas, also stores the schema description as context.
        """
        try:
            # Generate and execute SQL
            sql = schema.to_sql()
            await self.executor.execute(sql)
            
            # Store schema description as context if it's LLM-generated
            if any(table.description for table in schema.tables):
                self.context = self._generate_schema_description(schema)
                
            # Give the database a moment to complete the transaction
            await asyncio.sleep(0.5)
                
            # Verify tables were created
            verify_sql = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public';
            """
            tables = await self.executor.execute(verify_sql)
            expected_tables = {table.name.lower() for table in schema.tables}
            actual_tables = {row['table_name'] for row in tables}
            
            missing_tables = expected_tables - actual_tables
            if missing_tables:
                raise Exception(f"Failed to create tables: {', '.join(missing_tables)}")
                
        except Exception as e:
            raise Exception(f"Failed to apply schema: {str(e)}")

    def _generate_schema_description(self, schema: DatabaseSchema) -> str:
        """Generate a text description of the schema for context."""
        descriptions = []
        
        for table in schema.tables:
            table_desc = [f"Table {table.name}:"]
            if table.description:
                table_desc.append(f"Description: {table.description}")
            
            # Add columns
            table_desc.append("Columns:")
            for col in table.columns:
                col_desc = f"- {col.name} ({col.type})"
                if col.is_primary:
                    col_desc += " PRIMARY KEY"
                if not col.is_nullable:
                    col_desc += " NOT NULL"
                if col.description:
                    col_desc += f" -- {col.description}"
                table_desc.append(col_desc)
            
            # Add foreign keys
            if table.foreign_keys:
                table_desc.append("Foreign Keys:")
                for fk in table.foreign_keys:
                    table_desc.append(
                        f"- {fk.column} -> {fk.referenced_table}({fk.referenced_column})"
                    )
            
            descriptions.append("\n".join(table_desc))
        
        return "\n\n".join(descriptions) 

    async def import_csv_data(self, schema: DatabaseSchema, csv_path: str) -> None:
        """Import CSV data into database according to schema."""
        importer = DataImporter(self.config)
        statements = await importer.generate_import_statements(schema, csv_path)
        
        print(f"\nExecuting {len(statements)} INSERT statements...")
        for sql in statements:
            result = await self.executor.execute(sql)
            print(f"Result: {result}") 