import sys
import asyncio
import os
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.core.agent import SQLAgent
from src.utils.config import Config
from src.models.query import QueryRequest

async def setup_database(agent):
    """Set up database with sample data."""
    try:
        # Create tables
        await agent.execute_query("""
            DROP TABLE IF EXISTS books;
            
            CREATE TABLE IF NOT EXISTS books (
                book_id SERIAL PRIMARY KEY,
                title VARCHAR NOT NULL,
                author VARCHAR NOT NULL,
                published_year INTEGER
            );
        """)
        
        # Insert sample data with explicit commit
        await agent.execute_query("""
            INSERT INTO books (title, author, published_year) VALUES
            ('The Great Gatsby', 'F. Scott Fitzgerald', 1925),
            ('To Kill a Mockingbird', 'Harper Lee', 1960),
            ('1984', 'George Orwell', 1949),
            ('Pride and Prejudice', 'Jane Austen', 1813);
        """)
        
    except Exception as e:
        print(f"Error in setup_database: {str(e)}")
        raise

async def main():
    # Initialize config
    config = Config()
    
    # Initialize agent
    agent = SQLAgent(config)
    
    print("Setting up database...")
    await setup_database(agent)
    
    # Get actual schema from database
    schema = await agent.get_schema_from_database()
    agent.db_schema = schema.to_sql()
    
    # Example query
    request = QueryRequest(
        question="What books were published after 1930?",
        include_explanation=True
    )
    
    print("\nProcessing query:", request.question)
    result = await agent.process_request(request)
    
    print("\nGenerated SQL:")
    print(result.query)
    
    if result.explanation:
        print("\nExplanation:")
        print(result.explanation)
    
    print("\nResults:")
    for row in result.results:
        print(row)

if __name__ == "__main__":
    asyncio.run(main()) 