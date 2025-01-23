from typing import List, Tuple, Optional
from sqlalchemy.sql import text
from sqlalchemy.exc import SQLAlchemyError
import re

class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass

class QueryValidator:
    def __init__(self):
        """
        Initialize the Query Validator with predefined patterns and rules.
        """
        # Dangerous SQL operations that should be blocked
        self.dangerous_keywords = [
            'DROP', 'TRUNCATE', 'DELETE', 'UPDATE', 'ALTER', 'GRANT', 
            'REVOKE', 'CREATE', 'INSERT', 'REPLACE', 'MERGE'
        ]
        
        # PostgreSQL-specific date/time patterns that should be used
        self.postgres_patterns = {
            r'\bINTERVAL\s+\'': 'INTERVAL syntax',
            r'\bEXTRACT\s*\(': 'EXTRACT function',
            r'\bdate_trunc\s*\(': 'date_trunc function'
        }
        
        # Patterns for detecting SQL comments
        self.comment_patterns = [
            r'--.*$',           # Single line comments
            r'/\*.*?\*/',       # Multi-line comments
        ]

    def validate(self, query: str) -> Tuple[bool, Optional[str]]:
        """
        Validate the generated SQL query for safety and correctness.
        
        Args:
            query (str): The SQL query to validate
            
        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        try:
            # Remove any leading/trailing whitespace
            query = query.strip()
            
            # Check if query is empty
            if not query:
                return False, "Query cannot be empty"
            
            # Convert query to uppercase for keyword checking
            query_upper = query.upper()
            
            # 1. Check for dangerous operations
            for keyword in self.dangerous_keywords:
                if keyword in query_upper:
                    return False, f"Query contains dangerous keyword: {keyword}"
            
            # 2. Check for multiple statements
            if ';' in query:
                statements = [stmt.strip() for stmt in query.split(';') if stmt.strip()]
                if len(statements) > 1:
                    return False, "Multiple SQL statements are not allowed"
            
            # 3. Check for comments that might hide malicious code
            for pattern in self.comment_patterns:
                if re.search(pattern, query, re.MULTILINE | re.DOTALL):
                    return False, "Comments are not allowed in queries"
            
            # 4. Check if it's a SELECT query
            if not query_upper.strip().startswith('SELECT'):
                return False, "Only SELECT queries are allowed"
            
            # 5. Validate basic syntax using SQLAlchemy
            try:
                text(query).compile(compile_kwargs={"literal_binds": True})
            except SQLAlchemyError as e:
                return False, f"Invalid SQL syntax: {str(e)}"
            
            # 6. PostgreSQL-specific validations for date/time operations
            if any(keyword in query_upper for keyword in ['DATE', 'TIMESTAMP', 'TIME', 'INTERVAL']):
                valid_syntax = False
                for pattern, feature in self.postgres_patterns.items():
                    if re.search(pattern, query, re.IGNORECASE):
                        valid_syntax = True
                        break
                if not valid_syntax:
                    return False, "Query uses non-PostgreSQL date/time syntax"
            
            # 7. Additional security checks
            if 'INTO OUTFILE' in query_upper or 'INTO DUMPFILE' in query_upper:
                return False, "File operations are not allowed"
                
            if 'INFORMATION_SCHEMA' in query_upper:
                return False, "Access to INFORMATION_SCHEMA is not allowed"
                
            if 'PG_' in query_upper:
                return False, "Access to PostgreSQL system tables is not allowed"
            
            # All validations passed
            return True, None
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"

    def _check_table_exists(self, table_name: str, schema: str) -> bool:
        """
        Check if a table exists in the schema.
        
        Args:
            table_name (str): Name of the table to check
            schema (str): Database schema
            
        Returns:
            bool: True if table exists, False otherwise
        """
        # This is a placeholder for actual table existence checking
        # In a real implementation, you would check against the database schema
        return True

    def _is_safe_column(self, column_name: str) -> bool:
        """
        Check if a column name is safe to use.
        
        Args:
            column_name (str): Name of the column to check
            
        Returns:
            bool: True if column name is safe, False otherwise
        """
        # Check for SQL injection patterns in column names
        unsafe_patterns = [
            r'[;"]',            # Semicolons or quotes
            r'--',              # SQL comments
            r'/\*|\*/',         # Multi-line comments
            r'\s+',             # Multiple spaces
            r'\\',              # Backslashes
            r'0x[0-9a-fA-F]+', # Hex values
        ]
        
        return not any(re.search(pattern, column_name) for pattern in unsafe_patterns) 