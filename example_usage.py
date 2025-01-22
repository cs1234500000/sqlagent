from sql_agent import SQLAgent
from schema_manager import SchemaManager
from query_executor import QueryExecutor

# Initialize components
connection_string = "postgresql://user:password@localhost:5432/dbname"
schema_manager = SchemaManager(connection_string)
query_executor = QueryExecutor(connection_string)

# Get database schema
db_schema = schema_manager.get_schema()

# Initialize SQL Agent
agent = SQLAgent(db_schema=db_schema)

# Generate and execute a query
question = "Show me all customers who made purchases over $1000 last month"
sql_query = agent.generate_query(question)

if agent.validate_query(sql_query):
    results = query_executor.execute_query(sql_query)
    print(results) 