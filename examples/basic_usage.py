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
    """Setup database with sample schema and data."""
    # Clear existing schema
    await agent.executor.execute("DROP TABLE IF EXISTS books CASCADE;")
    
    # Create table
    create_sql = """
    CREATE TABLE books (
        book_id SERIAL PRIMARY KEY,
        title VARCHAR(200) NOT NULL,
        author VARCHAR(100) NOT NULL,
        published_year INTEGER
    );
    """
    await agent.executor.execute(create_sql)
    
    # Insert data
    insert_sql = """
    INSERT INTO books (title, author, published_year) VALUES
    ('The Great Gatsby', 'F. Scott Fitzgerald', 1925),
    ('1984', 'George Orwell', 1949),
    ('Pride and Prejudice', 'Jane Austen', 1813),
    ('To Kill a Mockingbird', 'Harper Lee', 1960);
    """
    await agent.executor.execute(insert_sql)

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