from typing import Dict, List, Optional
import sqlalchemy as sa
from sqlalchemy import inspect

class SchemaManager:
    def __init__(self, connection_string: str):
        """
        Initialize the Schema Manager.
        
        Args:
            connection_string (str): Database connection string
        """
        self.engine = sa.create_engine(connection_string)
        
    def get_schema(self) -> str:
        """
        Extract and format the database schema.
        
        Returns:
            str: Formatted schema string
        """
        inspector = inspect(self.engine)
        schema_info = []
        
        for table_name in inspector.get_table_names():
            columns = inspector.get_columns(table_name)
            foreign_keys = inspector.get_foreign_keys(table_name)
            
            table_info = f"Table: {table_name}\n"
            table_info += "Columns:\n"
            
            for column in columns:
                table_info += f"  - {column['name']} ({str(column['type'])})\n"
            
            if foreign_keys:
                table_info += "Foreign Keys:\n"
                for fk in foreign_keys:
                    table_info += f"  - {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}\n"
            
            schema_info.append(table_info)
            
        return "\n".join(schema_info) 