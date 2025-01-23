import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.core.agent import SQLAgent
from src.utils.config import Config
from src.models.query import QueryRequest
import pandas as pd

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
        print("\n=== Starting Schema Generation ===")
        
        config = Config()
        agent = SQLAgent(config)
        
        # First drop any existing schema
        await drop_existing_schema(agent)
        
        print("\n1. Reading CSV file...")
        csv_path = "data/sales_data.csv"
        description = """
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
        
        print("\n2. Analyzing data and generating schema...")
        schema = await agent.create_schema_from_csv(
            csv_path=csv_path,
            description=description
        )
        
        print("\n3. Generated Schema Structure:")
        agent.schema_generator.print_schema_structure(schema)
        
        print("\n4. Applying schema to database...")
        await agent.apply_schema(schema)
        print("Schema applied successfully!")
        
        print("\n=== Schema Generation Complete ===")
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        import traceback
        print("\nTraceback:")
        print(traceback.format_exc())

if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 