from pydantic import BaseModel, Field, validator
from typing import List, Optional
from enum import Enum
import re

class ColumnType(str, Enum):
    """Enum for common PostgreSQL column types"""
    INTEGER = "INTEGER"
    INT = "INT"
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
        
        # Map common type variations
        type_mapping = {
            'INT': 'INTEGER',
            'INT4': 'INTEGER',
            'INT8': 'BIGINT',
            'SERIAL4': 'SERIAL',
            'SERIAL8': 'BIGSERIAL',
            'STRING': 'TEXT',
            'BOOL': 'BOOLEAN',
            'FLOAT8': 'DOUBLE PRECISION',
            'FLOAT4': 'REAL'
        }
        
        # Apply type mapping if exists
        if v_upper in type_mapping:
            return type_mapping[v_upper]
        
        # Regular expressions for complex types
        numeric_pattern = r'^NUMERIC\(\d+(?:,\s*\d+)?\)$'
        varchar_pattern = r'^VARCHAR\(\d+\)$'
        decimal_pattern = r'^DECIMAL\(\d+(?:,\s*\d+)?\)$'
        
        # Check if it's a basic type
        if any(t.value == v_upper for t in ColumnType):
            return v
            
        # Check if it's a complex type with parameters
        if (re.match(numeric_pattern, v_upper) or 
            re.match(varchar_pattern, v_upper) or 
            re.match(decimal_pattern, v_upper)):
            return v
            
        # Check for other common PostgreSQL types
        common_types = [
            'CHAR', 'CHARACTER VARYING', 'TIME', 'TIMESTAMPTZ',
            'DOUBLE PRECISION', 'REAL', 'SMALLINT', 'BIGSERIAL'
        ]
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
    
    def get_primary_key(self) -> Column:
        """Get the primary key column of the table."""
        for col in self.columns:
            if col.is_primary:
                return col
        # If no primary key found, return first SERIAL column
        for col in self.columns:
            if "SERIAL" in col.type.upper():
                return col
        raise ValueError(f"No primary key found for table {self.name}")
    
    def to_sql(self) -> str:
        """Convert schema to SQL CREATE statements"""
        sql_statements = []
        
        # Sort tables by dependencies
        sorted_tables = self._sort_tables_by_dependencies()
        
        # First create all tables
        for table in sorted_tables:
            columns = []
            constraints = []
            
            # Add columns
            for col in table.columns:
                col_def = f"{col.name} {col.type}"
                if not col.is_nullable:
                    col_def += " NOT NULL"
                if col.default is not None:
                    col_def += f" DEFAULT {col.default}"
                if col.is_primary:
                    constraints.append(f"PRIMARY KEY ({col.name})")
                columns.append(col_def)
            
            # Add foreign keys
            if table.foreign_keys:
                for fk in table.foreign_keys:
                    constraints.append(
                        f"FOREIGN KEY ({fk.column}) REFERENCES {fk.referenced_table} ({fk.referenced_column})"
                    )
            
            # Combine all parts
            all_lines = columns + constraints
            indented_lines = [f"    {line}" for line in all_lines]
            
            create_table = [
                f"CREATE TABLE {table.name} (",
                ",\n".join(indented_lines),
                ");"
            ]
            
            sql_statements.append("\n".join(create_table))
        
        # Then add all comments
        for table in sorted_tables:
            if table.description:
                # Escape single quotes in description
                escaped_description = table.description.replace("'", "''")
                sql_statements.append(
                    f"COMMENT ON TABLE {table.name} IS '{escaped_description}';"
                )
            
            # Add column comments if they exist
            for col in table.columns:
                if col.description:
                    # Escape single quotes in column description
                    escaped_description = col.description.replace("'", "''")
                    sql_statements.append(
                        f"COMMENT ON COLUMN {table.name}.{col.name} IS '{escaped_description}';"
                    )
        
        return "\n\n".join(sql_statements)

    def _sort_tables_by_dependencies(self) -> List[Table]:
        """Sort tables so that referenced tables are created first"""
        # Create dependency graph
        graph = {table.name.strip(): set() for table in self.tables}
        for table in self.tables:
            if table.foreign_keys:
                for fk in table.foreign_keys:
                    # Extract just the table name from the reference and clean it
                    ref_table = fk.referenced_table.split('.')[0] if '.' in fk.referenced_table else fk.referenced_table
                    ref_table = ref_table.strip()  # Remove any whitespace
                    graph[table.name.strip()].add(ref_table)
        
        # Topological sort
        sorted_names = []
        visited = set()
        temp_visited = set()
        
        def visit(name: str):
            if name in temp_visited:
                raise ValueError(f"Circular dependency detected involving table {name}")
            if name not in visited:
                temp_visited.add(name)
                for dep in graph[name]:
                    visit(dep)
                temp_visited.remove(name)
                visited.add(name)
                sorted_names.append(name)
        
        for name in graph:
            if name not in visited:
                visit(name)
                
        # Map sorted names back to Table objects
        name_to_table = {table.name.strip(): table for table in self.tables}
        return [name_to_table[name] for name in sorted_names]

class GeneratedColumnInfo(BaseModel):
    """Column information generated by LLM"""
    name: str = Field(..., description="Column name")
    data_type: str = Field(..., description="PostgreSQL data type")
    nullable: bool = Field(True, description="Whether the column can be NULL")
    primary_key: bool = Field(False, description="Whether this is a primary key")
    foreign_key: Optional[str] = Field(None, description="Reference to another table (table.column)")
    description: Optional[str] = Field(None, description="Column description")

    def to_column(self) -> Column:
        """Convert to standard Column model"""
        return Column(
            name=self.name,
            type=self.data_type,
            is_nullable=self.nullable,
            is_primary=self.primary_key,
            description=self.description
        )

class GeneratedTableSchema(BaseModel):
    """Table schema generated by LLM"""
    table_name: str = Field(..., description="Table name")
    columns: List[GeneratedColumnInfo] = Field(..., description="List of columns")
    description: Optional[str] = Field(None, description="Table description")

    def to_table(self) -> Table:
        """Convert to standard Table model"""
        columns = [col.to_column() for col in self.columns]
        foreign_keys = []
        
        # Convert foreign key references to ForeignKey objects
        for col in self.columns:
            if col.foreign_key:
                try:
                    # Parse foreign key format: "table_name(column_name)"
                    if '(' in col.foreign_key and ')' in col.foreign_key:
                        table = col.foreign_key.split('(')[0]
                        referenced_column = col.foreign_key.split('(')[1].split(')')[0]
                    else:
                        table = col.foreign_key
                        referenced_column = col.name  # Use same column name if not specified
                    
                    foreign_keys.append(ForeignKey(
                        column=col.name,
                        referenced_table=table,
                        referenced_column=referenced_column
                    ))
                except Exception as e:
                    print(f"Warning: Invalid foreign key format for column {col.name}: {col.foreign_key}")
                    continue
        
        return Table(
            name=self.table_name,
            columns=columns,
            foreign_keys=foreign_keys,
            description=self.description
        )

class GeneratedDatabaseSchema(BaseModel):
    """Database schema generated by LLM"""
    tables: List[GeneratedTableSchema] = Field(..., description="List of tables")
    version: str = Field("1.0", description="Schema version")
    description: Optional[str] = Field(None, description="Database description")

    def to_database_schema(self) -> DatabaseSchema:
        """Convert to standard DatabaseSchema model"""
        return DatabaseSchema(
            tables=[table.to_table() for table in self.tables],
            version=self.version,
            description=self.description
        ) 