# Getting Started with SQL Agent

This guide will help you set up and start using the SQL Agent.

## Prerequisites

- Python 3.8+
- PostgreSQL 12+
- OpenAI API key

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/sqlagent
cd sqlagent
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the package:
```bash
pip install -e .
```

## Configuration

1. Create a `.env` file:
```env
OPENAI_API_KEY=your_openai_api_key
DB_CONNECTION_STRING=postgresql://user:password@localhost:5432/dbname
```

2. Configure your database:
```sql
CREATE DATABASE your_database;
\c your_database

CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100)
);

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(id),
    amount DECIMAL(10,2),
    order_date TIMESTAMP
);
```

## Basic Usage

```python
from src.core.agent import SQLAgent
from src.utils.config import Config
from src.models.query import QueryRequest

async def main():
    # Initialize configuration
    config = Config()
    
    # Initialize agent
    agent = SQLAgent(config)
    
    # Create request
    request = QueryRequest(
        question="Show me all customers who made purchases over $1000"
    )
    
    # Process request
    result = await agent.process_request(request)
    
    # Print results
    print(f"Query: {result.query}")
    print("\nResults:")
    print(result.format_results())

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

## Next Steps

- Read the [Configuration Guide](configuration.md) for detailed setup options
- Check out [Basic Query Examples](../examples/basic_queries.md)
- Learn about [Schema Management](schema_management.md) 