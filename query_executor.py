from typing import List, Dict, Any
import sqlalchemy as sa
from sqlalchemy.exc import SQLAlchemyError

class QueryExecutor:
    def __init__(self, connection_string: str):
        """
        Initialize the Query Executor.
        
        Args:
            connection_string (str): Database connection string
        """
        self.engine = sa.create_engine(connection_string)
        
    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """
        Execute the SQL query and return results.
        
        Args:
            query (str): SQL query to execute
            
        Returns:
            List[Dict[str, Any]]: Query results
        """
        try:
            # Create a new connection for each query
            with sa.create_engine(self.engine.url).connect() as connection:
                result = connection.execute(sa.text(query))
                # Convert each row to a dictionary using _asdict()
                return [row._asdict() for row in result]
                
        except SQLAlchemyError as e:
            raise Exception(f"Error executing query: {str(e)}") 