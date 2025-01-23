from sqlalchemy import inspect, MetaData
from sqlalchemy.exc import SQLAlchemyError
from typing import Dict, List, Optional, Any
from .connection import DatabaseConnection, DatabaseConnectionError
from ..models.schema import DatabaseSchema, Table, Column, ForeignKey

class SchemaError(Exception):
    """Custom exception for schema-related errors"""
    pass

class SchemaManager:
    def __init__(self, connection_string: Optional[str] = None):
        """
        Initialize Schema Manager.
        
        Args:
            connection_string (Optional[str]): Database connection string
        """
        try:
            self.db = DatabaseConnection(connection_string)
        except DatabaseConnectionError as e:
            raise SchemaError(f"Failed to initialize schema manager: {str(e)}")
        
    def get_schema(self) -> DatabaseSchema:
        """
        Extract and format the database schema.
        
        Returns:
            DatabaseSchema: Formatted schema object
            
        Raises:
            SchemaError: If schema extraction fails
        """
        try:
            inspector = inspect(self.db.engine)
            tables = []
            
            for table_name in inspector.get_table_names():
                # Get columns
                columns = []
                for col in inspector.get_columns(table_name):
                    columns.append(Column(
                        name=col['name'],
                        type=str(col['type']),
                        is_nullable=col.get('nullable', True),
                        is_primary=col.get('primary_key', False)
                    ))
                    
                # Get foreign keys
                foreign_keys = []
                for fk in inspector.get_foreign_keys(table_name):
                    foreign_keys.append(ForeignKey(
                        column=fk['constrained_columns'][0],
                        referenced_table=fk['referred_table'],
                        referenced_column=fk['referred_columns'][0]
                    ))
                    
                tables.append(Table(
                    name=table_name,
                    columns=columns,
                    foreign_keys=foreign_keys
                ))
                
            return DatabaseSchema(tables=tables)
            
        except SQLAlchemyError as e:
            raise SchemaError(f"Failed to extract schema: {str(e)}")
        except Exception as e:
            raise SchemaError(f"Unexpected error during schema extraction: {str(e)}")

    def get_schema_text(self) -> str:
        """
        Get schema as formatted text (for OpenAI prompt).
        
        Returns:
            str: Formatted schema string
        """
        schema = self.get_schema()
        schema_text = []
        
        for table in schema.tables:
            # Table header
            schema_text.append(f"Table: {table.name}")
            
            # Columns
            schema_text.append("Columns:")
            for column in table.columns:
                nullable = "" if column.is_nullable else "NOT NULL"
                primary = "PRIMARY KEY" if column.is_primary else ""
                schema_text.append(f"  - {column.name} ({column.type}) {nullable} {primary}".strip())
            
            # Foreign keys
            if table.foreign_keys:
                schema_text.append("Foreign Keys:")
                for fk in table.foreign_keys:
                    schema_text.append(f"  - {fk.column} -> {fk.referenced_table}.{fk.referenced_column}")
            
            schema_text.append("")  # Empty line between tables
            
        return "\n".join(schema_text)

    def validate_schema(self) -> bool:
        """
        Validate database schema.
        
        Returns:
            bool: True if schema is valid
            
        Raises:
            SchemaError: If schema validation fails
        """
        try:
            schema = self.get_schema()
            # Add validation logic here
            return True
        except Exception as e:
            raise SchemaError(f"Schema validation failed: {str(e)}") 