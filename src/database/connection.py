from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager
from typing import Generator, Optional
import os
from dotenv import load_dotenv
from sqlalchemy import text

class DatabaseConnectionError(Exception):
    """Custom exception for database connection errors"""
    pass

class DatabaseConnection:
    def __init__(self, connection_string: Optional[str] = None):
        """
        Initialize database connection.
        
        Args:
            connection_string (Optional[str]): Database connection string.
                If not provided, will try to load from environment variables.
        """
        load_dotenv()
        self.connection_string = connection_string or os.getenv("DB_CONNECTION_STRING")
        if not self.connection_string:
            raise DatabaseConnectionError("Database connection string not provided")
        
        self._engine: Optional[Engine] = None
        
    @property
    def engine(self) -> Engine:
        """
        Get or create SQLAlchemy engine.
        
        Returns:
            Engine: SQLAlchemy engine instance
            
        Raises:
            DatabaseConnectionError: If engine creation fails
        """
        if not self._engine:
            try:
                self._engine = create_engine(
                    self.connection_string,
                    pool_pre_ping=True,  # Enable connection health checks
                    pool_size=5,         # Set connection pool size
                    max_overflow=10      # Maximum number of connections to overflow
                )
            except Exception as e:
                raise DatabaseConnectionError(f"Failed to create database engine: {str(e)}")
        return self._engine

    @contextmanager
    def get_connection(self):
        """Get a database connection."""
        try:
            with self.engine.connect() as connection:
                yield connection
        except Exception as e:
            raise DatabaseConnectionError(f"Database connection error: {str(e)}")

    def test_connection(self) -> bool:
        """
        Test database connection.
        
        Returns:
            bool: True if connection is successful
            
        Raises:
            DatabaseConnectionError: If connection test fails
        """
        try:
            with self.get_connection() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            raise DatabaseConnectionError(f"Connection test failed: {str(e)}") 