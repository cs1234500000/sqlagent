import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.core.agent import SQLAgent
from src.utils.config import Config

async def main():
    try:
        print("\n=== Starting Data Import ===")
        
        config = Config()
        agent = SQLAgent(config)
        
        # Get existing schema
        print("\n1. Getting database schema...")
        schema = await agent.get_schema_from_database()
        print("Schema retrieved.")
        print("\nDatabase Schema:")
        print(schema.to_sql())

        # Import CSV data
        print("\n2. Importing data from CSV...")
        csv_path = "data/sales_data.csv"
        await agent.import_csv_data(schema, csv_path)
        print("Data import complete!")
        
        print("\n=== Data Import Complete ===")
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        import traceback
        print("\nTraceback:")
        print(traceback.format_exc())

if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 