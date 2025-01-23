from src.core.agent import SQLAgent
from src.utils.config import Config
from src.models.query import QueryRequest
from src.database.schema import SchemaManager

async def main():
    try:
        # Initialize configuration
        config = Config()
        
        # Get database schema
        schema_manager = SchemaManager(config.connection_string)
        db_schema = schema_manager.get_schema_text()  # Get formatted schema for OpenAI
        
        # Initialize SQL Agent
        agent = SQLAgent(config)
        
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
        print(result.format_results())  # Using the new format_results method
        print(f"\nExecution time: {result.execution_time:.2f} seconds")
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 