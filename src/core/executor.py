from typing import List, Dict, Any
from sqlalchemy.sql import text
from sqlalchemy.exc import SQLAlchemyError
from ..database.connection import DatabaseConnection
import time
from ..models.query import QueryResult

class ExecutionError(Exception):
    """Custom exception for query execution errors"""
    pass

class QueryExecutor:
    def __init__(self, connection_string: str):
        """
        Initialize the Query Executor.
        
        Args:
            connection_string (str): Database connection string
        """
        self.db = DatabaseConnection(connection_string)
        
    async def execute(self, query: str) -> List[Dict[str, Any]]:
        """
        Execute the SQL query and return results.
        
        Args:
            query (str): SQL query to execute
            
        Returns:
            List[Dict[str, Any]]: Query results
            
        Raises:
            ExecutionError: If query execution fails
        """
        start_time = time.time()
        
        try:
            with self.db.get_connection() as connection:
                # Execute the query
                result = connection.execute(text(query))
                
                # Convert results to list of dictionaries
                results = [row._asdict() for row in result]
                
                # Calculate execution time
                execution_time = time.time() - start_time
                
                return results
                
        except SQLAlchemyError as e:
            error_msg = f"Error executing query: {str(e)}"
            raise ExecutionError(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error during query execution: {str(e)}"
            raise ExecutionError(error_msg)

    def _format_results(self, results: List[Dict[str, Any]]) -> str:
        """
        Format query results for display.
        
        Args:
            results (List[Dict[str, Any]]): Query results
            
        Returns:
            str: Formatted results string
        """
        if not results:
            return "No results found."
            
        # Get column names from first row
        columns = list(results[0].keys())
        
        # Calculate column widths
        widths = {col: len(col) for col in columns}
        for row in results:
            for col in columns:
                widths[col] = max(widths[col], len(str(row[col])))
                
        # Create header
        header = " | ".join(col.ljust(widths[col]) for col in columns)
        separator = "-" * len(header)
        
        # Create rows
        rows = []
        for row in results:
            formatted_row = " | ".join(str(row[col]).ljust(widths[col]) for col in columns)
            rows.append(formatted_row)
            
        # Combine all parts
        return "\n".join([header, separator] + rows)

    async def execute_with_timeout(self, query: str, timeout_seconds: float = 30.0) -> List[Dict[str, Any]]:
        """
        Execute query with a timeout.
        
        Args:
            query (str): SQL query to execute
            timeout_seconds (float): Maximum execution time in seconds
            
        Returns:
            List[Dict[str, Any]]: Query results
            
        Raises:
            ExecutionError: If query execution times out or fails
        """
        import asyncio
        
        try:
            # Create a task for query execution
            task = asyncio.create_task(self.execute(query))
            
            # Wait for the task with timeout
            results = await asyncio.wait_for(task, timeout=timeout_seconds)
            
            return results
            
        except asyncio.TimeoutError:
            error_msg = f"Query execution timed out after {timeout_seconds} seconds"
            raise ExecutionError(error_msg)
        except Exception as e:
            raise ExecutionError(str(e)) 