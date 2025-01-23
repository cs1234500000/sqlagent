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
   
   For Ubuntu/Debian:
   ```bash
   sudo -u postgres psql

   # In psql console:
   CREATE DATABASE your_database_name;
   CREATE USER your_username WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE your_database_name TO your_username;
   GRANT ALL ON SCHEMA public TO your_username;
   ALTER USER your_username CREATEDB;
   ```

   For macOS:
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
   ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO your_username;
   ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO your_username;
   ```

4. Connect to your new database:
   ```bash
   psql your_database_name
   ```

5. Clone the repository:
   ```bash
   git clone https://github.com/cs1234500000/sqlagent
   cd sqlagent
   ```

6. Create and activate virtual environment:
   ```bash
   python -m venv venv
   
   # Windows
   .\venv\Scripts\activate
   
   # Unix/macOS
   source venv/bin/activate
   ```

7. Install dependencies:
   ```bash
   pip install openai python-dotenv sqlalchemy psycopg2-binary
   ```

8. Create a .env file:
   ```bash
   touch .env
   ```

9. Add your configuration to .env:
   ```
   OPENAI_API_KEY=your_openai_api_key
   DB_CONNECTION_STRING=postgresql://your_username:your_password@localhost:5432/your_database_name
   ```

## Usage

1. Update the connection string in `example_usage.py` with your database credentials:
   ```python
   connection_string = "postgresql://your_username:your_password@localhost:5432/your_database_name"
   ```

2. Run the example:
   ```bash
   python example_usage.py
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

1. If you get a database connection error, verify:
   - PostgreSQL service is running
   - Database credentials in .env are correct
   - PostgreSQL is accepting connections (check pg_hba.conf)

2. If you get a "permission denied" error:
   ```bash
   psql your_database_name
   
   # In psql console:
   GRANT ALL PRIVILEGES ON SCHEMA public TO your_username;
   GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_username;
   GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO your_username;
   ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO your_username;
   ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO your_username;
   ```

3. If you get an OpenAI API error:
   - Verify your API key in .env is correct
   - Check your OpenAI account has sufficient credits

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.