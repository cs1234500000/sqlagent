# SQL AI Agent

An intelligent agent that translates natural language to SQL queries, making database interactions more accessible and efficient.

## Why SQL AI Agent?

- Natural language to SQL conversion using OpenAI GPT
- PostgreSQL query validation and execution
- Schema introspection and management
- Query timeout and error handling
- Result formatting (table, JSON, CSV)
- Async support

## Prerequisites

- Python 3.8+
- PostgreSQL 12+
- pip (Python package manager)

## Setup

1. Install PostgreSQL:
   ```bash
   # Ubuntu/Debian
   sudo apt-get update
   sudo apt-get install postgresql postgresql-contrib

   # macOS using Homebrew
   brew install postgresql@14
   ```

2. Start PostgreSQL service:
   ```bash
   # Ubuntu/Debian
   sudo service postgresql start

   # macOS
   brew services start postgresql@14
   ```

3. Create a database and user:
   ```bash
   # Connect to PostgreSQL
   psql postgres

   # In psql console:
   CREATE DATABASE your_database_name;
   CREATE USER your_username WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE your_database_name TO your_username;
   
   # Connect to the new database
   \c your_database_name
   
   # Grant schema permissions
   GRANT ALL PRIVILEGES ON SCHEMA public TO your_username;
   GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_username;
   GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO your_username;
   ```

4. Clone the repository:
   ```bash
   git clone https://github.com/cs1234500000/sqlagent
   cd sqlagent
   ```

5. Create and activate virtual environment:
   ```bash
   python -m venv venv
   
   # Windows
   .\venv\Scripts\activate
   
   # Unix/macOS
   source venv/bin/activate
   ```

6. Install the package in development mode:
   ```bash
   pip install -e .
   ```

7. Create a .env file in the project root:
   ```bash
   # Create .env file
   touch .env

   # Add your configuration
   echo "OPENAI_API_KEY=your_openai_api_key" >> .env
   echo "DB_CONNECTION_STRING=postgresql://your_username:your_password@localhost:5432/your_database_name" >> .env
   ```

## Running Examples

You can run examples from either the project root or the examples directory:

1. From project root:
   ```bash
   python examples/basic_usage.py
   ```

2. From examples directory:
   ```bash
   cd examples
   python basic_usage.py
   ```

## Sample Database Setup

Here's a simple example to create and populate a test database:

```sql
-- Connect to your database first:
-- psql -U your_username -d your_database_name

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

-- Insert sample data
INSERT INTO customers (name, email) VALUES
('John Doe', 'john@example.com'),
('Jane Smith', 'jane@example.com');

INSERT INTO orders (customer_id, amount, order_date) VALUES
(1, 1200.00, NOW() - INTERVAL '1 month'),
(2, 800.00, NOW() - INTERVAL '1 month');
```

## Troubleshooting

1. If you get a "module not found" error:
   - Make sure you've installed the package in development mode (`pip install -e .`)
   - Check that you're running Python from the correct environment
   - Verify the project structure matches the repository

2. If you get environment variable errors:
   - Make sure .env file exists in the project root
   - Verify the environment variables are correctly set
   - Check file permissions on .env

3. If you get database connection errors:
   - Verify PostgreSQL is running
   - Check your database credentials in .env
   - Ensure the database exists and is accessible

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.