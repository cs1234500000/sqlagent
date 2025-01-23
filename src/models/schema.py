from pydantic import BaseModel, Field, validator
from typing import List, Optional
from enum import Enum
import re

class ColumnType(str, Enum):
    """Enum for common PostgreSQL column types"""
    INTEGER = "INTEGER"
    BIGINT = "BIGINT"
    SERIAL = "SERIAL"
    TEXT = "TEXT"
    VARCHAR = "VARCHAR"
    BOOLEAN = "BOOLEAN"
    TIMESTAMP = "TIMESTAMP"
    DATE = "DATE"
    DECIMAL = "DECIMAL"
    NUMERIC = "NUMERIC"
    FLOAT = "FLOAT"
    JSON = "JSON"
    JSONB = "JSONB"
    UUID = "UUID"

class Column(BaseModel):
    """Database column definition"""
    name: str = Field(..., description="Column name")
    type: str = Field(..., description="Column data type")
    is_nullable: bool = Field(True, description="Whether the column can be NULL")
    is_primary: bool = Field(False, description="Whether the column is a primary key")
    default: Optional[str] = Field(None, description="Default value for the column")
    description: Optional[str] = Field(None, description="Column description")

    @validator('type')
    def validate_type(cls, v):
        """Validate that the type is a known PostgreSQL type"""
        # Convert to uppercase for comparison
        v_upper = v.upper()
        
        # Regular expressions for complex types
        numeric_pattern = r'^NUMERIC\(\d+(?:,\s*\d+)?\)$'
        varchar_pattern = r'^VARCHAR\(\d+\)$'
        decimal_pattern = r'^DECIMAL\(\d+(?:,\s*\d+)?\)$'
        
        # Check if it's a basic type
        if any(t.value in v_upper for t in ColumnType):
            return v
            
        # Check if it's a complex type with parameters
        if (re.match(numeric_pattern, v_upper) or 
            re.match(varchar_pattern, v_upper) or 
            re.match(decimal_pattern, v_upper)):
            return v
            
        # Check for other common PostgreSQL types
        common_types = ['CHAR', 'CHARACTER VARYING', 'TIME', 'TIMESTAMPTZ']
        if any(t in v_upper for t in common_types):
            return v
            
        raise ValueError(f"Unknown column type: {v}")

class ForeignKey(BaseModel):
    """Foreign key constraint definition"""
    column: str = Field(..., description="Column name with the foreign key")
    referenced_table: str = Field(..., description="Referenced table name")
    referenced_column: str = Field(..., description="Referenced column name")
    on_delete: Optional[str] = Field(None, description="ON DELETE behavior")
    on_update: Optional[str] = Field(None, description="ON UPDATE behavior")

class Index(BaseModel):
    """Index definition"""
    name: str = Field(..., description="Index name")
    columns: List[str] = Field(..., description="Columns in the index")
    is_unique: bool = Field(False, description="Whether the index is unique")
    method: str = Field("btree", description="Index method (btree, hash, etc.)")

class Table(BaseModel):
    """Database table definition"""
    name: str = Field(..., description="Table name")
    columns: List[Column] = Field(..., description="List of columns")
    foreign_keys: Optional[List[ForeignKey]] = Field(default_factory=list, description="Foreign key constraints")
    indexes: Optional[List[Index]] = Field(default_factory=list, description="Table indexes")
    description: Optional[str] = Field(None, description="Table description")

class DatabaseSchema(BaseModel):
    """Complete database schema definition"""
    tables: List[Table] = Field(..., description="List of tables in the schema")
    version: str = Field("1.0", description="Schema version")
    description: Optional[str] = Field(None, description="Schema description")

    def get_table(self, table_name: str) -> Optional[Table]:
        """Get table by name"""
        for table in self.tables:
            if table.name == table_name:
                return table
        return None

    def has_table(self, table_name: str) -> bool:
        """Check if table exists in schema"""
        return any(table.name == table_name for table in self.tables) 