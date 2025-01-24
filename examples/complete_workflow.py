import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.core.agent import SQLAgent
from src.utils.config import Config
from src.models.query import QueryRequest
import asyncio

async def drop_existing_schema(agent):
    """Drop any existing tables from previous runs"""
    print("\nDropping existing schema...")
    drop_sql = """
    DROP TABLE IF EXISTS shipping CASCADE;
    DROP TABLE IF EXISTS transactions CASCADE;
    DROP TABLE IF EXISTS products CASCADE;
    DROP TABLE IF EXISTS customers CASCADE;
    DROP TABLE IF EXISTS orders CASCADE;
    DROP TABLE IF EXISTS payment CASCADE;
    """
    await agent.executor.execute(drop_sql)
    print("Existing schema dropped.")

async def main():
    try:
        print("\n=== Starting Complete Workflow Demo ===")
        
        # Initialize configuration and agent
        config = Config()
        agent = SQLAgent(config)
        
        # Step 1: Generate and Apply Schema
        print("\n1. Schema Generation Phase")
        print("--------------------------")
        await drop_existing_schema(agent)
        
        csv_path = "data/sales_data.csv"
        schema_description = """
        This is a sales dataset containing customer transactions.
        Each row represents a sale with customer information,
        product details, and transaction data.
        We want to track customer purchase history and analyze sales trends.
        The schema should be optimized for:
        - Customer analytics
        - Sales reporting
        - Inventory management
        - Order tracking
        """
        
        print("\nGenerating schema from CSV...")
        schema = await agent.create_schema_from_csv(
            csv_path=csv_path,
            description=schema_description
        )
        
        print("\nGenerated Schema Structure:")
        agent.schema_generator.print_schema_structure(schema)
        
        print("\nApplying schema to database...")
        await agent.apply_schema(schema)
        print("Schema applied successfully!")
        
        # Step 2: Import Data
        print("\n2. Data Import Phase")
        print("-------------------")
        print("Importing data from CSV...")
        
        # Get fresh schema from database to ensure all sequence information is captured
        schema = await agent.get_schema_from_database()
        print("Schema retrieved from database.")
        
        await agent.import_csv_data(schema, csv_path)
        print("Data import complete!")
        
        # Step 3: Query Analysis
        print("\n3. Query Analysis Phase")
        print("----------------------")
        
        # Example analytical queries
        queries = [
            "What are the top 5 products by total sales amount?",
            "Show me the average transaction value by customer segment"
        ]
        
        for question in queries:
            print(f"\nProcessing query: {question}")
            request = QueryRequest(
                question=question,
                include_explanation=True
            )
            
            result = await agent.process_request(request)
            
            print("\nGenerated SQL:")
            print(result.query)
            
            if result.explanation:
                print("\nExplanation:")
                print(result.explanation)
            
            print("\nResults:")
            for row in result.results:
                print(row)
            
            print("\n" + "-"*50)
        
        print("\n=== Complete Workflow Demo Finished ===")
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        import traceback
        print("\nTraceback:")
        print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(main()) 