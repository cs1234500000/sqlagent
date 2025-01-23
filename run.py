import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Now we can import from src
from src.core.agent import SQLAgent
from src.utils.config import Config
from src.models.query import QueryRequest
from src.database.schema import SchemaManager

async def main():
    try:
        # Initialize configuration
        config = Config()
        
        # Get database schema
        schema_manager = SchemaManager(config.db_connection_string)
        db_schema = schema_manager.get_schema_text()
        
        # Initialize SQL Agent with schema
        agent = SQLAgent(config, db_schema=db_schema)
        
        # Create query request
        request = QueryRequest(
            question="Show me all customers who made purchases over $1000 last month"
        )
        
        # Process request
        result = await agent.process_request(request)
        
        # Print results
        print(f"Query: {result.query}")
        print("\nExplanation:")
        print(result.explanation)
        print("\nResults:")
        print(result.format_results())
        print(f"\nExecution time: {result.execution_time:.2f} seconds")
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 