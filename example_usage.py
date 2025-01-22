from sql_agent import SQLAgent
from schema_manager import SchemaManager
from query_executor import QueryExecutor

# Initialize components
connection_string = "postgresql://shuchen:123123@localhost:5432/sqlagent"
schema_manager = SchemaManager(connection_string)
query_executor = QueryExecutor(connection_string)

# Get database schema
db_schema = schema_manager.get_schema()

# Initialize SQL Agent
agent = SQLAgent(db_schema=db_schema)

# Generate and execute a query
question = "Show me all customers who made purchases over $1000 in the previous month"
sql_query = agent.generate_query(question)

# For debugging
print("Generated SQL Query:")
print(sql_query)
print("\nExecuting query...")

if agent.validate_query(sql_query):
    try:
        results = query_executor.execute_query(sql_query)
        print("\nResults:")
        if not results:
            print("No customers found matching the criteria.")
        else:
            for row in results:
                print(f"Customer ID: {row['id']}")
                print(f"Name: {row['name']}")
                print(f"Email: {row['email']}")
                print("-" * 30)
    except Exception as e:
        print(f"Error executing query: {str(e)}") 