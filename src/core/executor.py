from typing import List, Dict, Any
from sqlalchemy.sql import text
from sqlalchemy.exc import SQLAlchemyError
from ..database.connection import DatabaseConnection
import time
from ..models.query import QueryResult
from ..models.schema import DatabaseSchema, Table, Column, ForeignKey

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
        try:
            with self.db.get_connection() as connection:
                # Split into individual statements
                statements = [stmt.strip() for stmt in query.split(';') if stmt.strip()]
                results = []
                
                for stmt in statements:
                    query_type = self._get_query_type(stmt)
                    
                    if query_type == "DDL":
                        # DDL needs immediate commit and no results
                        connection.execute(text(stmt))
                        connection.commit()
                        
                    elif query_type == "DML":
                        # DML needs transaction and no results
                        with connection.begin():
                            connection.execute(text(stmt))
                            
                    else:  # SELECT
                        result = connection.execute(text(stmt))
                        if result.returns_rows:
                            rows = result.mappings().all()
                            results.extend(list(map(dict, rows)))
                
                return results
                
        except Exception as e:
            error_msg = f"Unexpected error during query execution: {str(e)}"
            raise ExecutionError(error_msg)
            
    def _get_query_type(self, query: str) -> str:
        """Determine the type of SQL query."""
        query_start = query.strip().upper()
        
        if any(query_start.startswith(ddl) for ddl in 
            ['CREATE', 'DROP', 'ALTER', 'TRUNCATE']):
            return "DDL"
            
        if any(query_start.startswith(dml) for dml in 
            ['INSERT', 'UPDATE', 'DELETE']):
            return "DML"
            
        return "SELECT"

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

    async def get_schema(self) -> DatabaseSchema:
        """Get the current database schema."""
        # Query to get tables and columns
        sql = """
        SELECT 
            t.table_name,
            c.column_name,
            c.data_type,
            c.is_nullable = 'YES' as is_nullable,
            c.column_default,
            COALESCE(tc.constraint_type = 'PRIMARY KEY', false) as is_primary
        FROM information_schema.tables t
        JOIN information_schema.columns c 
            ON t.table_name = c.table_name 
            AND t.table_schema = c.table_schema
        LEFT JOIN information_schema.key_column_usage kcu 
            ON c.table_name = kcu.table_name 
            AND c.column_name = kcu.column_name
            AND c.table_schema = kcu.table_schema
        LEFT JOIN information_schema.table_constraints tc
            ON kcu.constraint_name = tc.constraint_name
            AND tc.table_schema = c.table_schema
        WHERE t.table_schema = 'public'
            AND t.table_type = 'BASE TABLE'
        ORDER BY t.table_name, c.ordinal_position;
        """
        
        # Query to get foreign keys
        fk_sql = """
        SELECT
            tc.table_name,
            kcu.column_name,
            ccu.table_name AS referenced_table,
            ccu.column_name AS referenced_column
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
            ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage ccu
            ON tc.constraint_name = ccu.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY';
        """
        
        tables = {}
        
        # Get table and column information
        columns_result = await self.execute(sql)
        for row in columns_result:
            table_name = row['table_name']
            if table_name not in tables:
                tables[table_name] = {
                    'name': table_name,
                    'columns': [],
                    'foreign_keys': []
                }
            
            tables[table_name]['columns'].append({
                'name': row['column_name'],
                'type': row['data_type'].upper(),
                'is_nullable': row['is_nullable'],
                'is_primary': row['is_primary'],
                'default': row['column_default']
            })
        
        # Get foreign key information
        fk_result = await self.execute(fk_sql)
        for row in fk_result:
            table_name = row['table_name']
            if table_name in tables:
                tables[table_name]['foreign_keys'].append({
                    'column': row['column_name'],
                    'referenced_table': row['referenced_table'],
                    'referenced_column': row['referenced_column']
                })
        
        # Convert to DatabaseSchema
        schema_tables = []
        for table_data in tables.values():
            columns = [
                Column(
                    name=col['name'],
                    type=col['type'],
                    is_nullable=col['is_nullable'],
                    is_primary=col['is_primary'],
                    default=col['default']
                )
                for col in table_data['columns']
            ]
            
            foreign_keys = [
                ForeignKey(
                    column=fk['column'],
                    referenced_table=fk['referenced_table'],
                    referenced_column=fk['referenced_column']
                )
                for fk in table_data['foreign_keys']
            ]
            
            schema_tables.append(
                Table(
                    name=table_data['name'],
                    columns=columns,
                    foreign_keys=foreign_keys
                )
            )
        
        return DatabaseSchema(tables=schema_tables) 