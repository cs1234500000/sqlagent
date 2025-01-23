from typing import Dict, List, Any, Set
import pandas as pd
import openai
from ..utils.config import Config
from ..models.schema import DatabaseSchema
from ..ai.templates import DataImportTemplates
import json
from collections import defaultdict

class DataImporter:
    def __init__(self, config: Config):
        """Initialize the Data Importer."""
        self.client = openai.OpenAI(api_key=config.openai_api_key)
        self.templates = DataImportTemplates()

    def _build_dependency_graph(self, schema: DatabaseSchema) -> Dict[str, Set[str]]:
        """Build a graph of table dependencies based on foreign keys."""
        dependencies = defaultdict(set)
        for table in schema.tables:
            for fk in table.foreign_keys:
                dependencies[table.name].add(fk.referenced_table)
        return dependencies

    def _get_insertion_order(self, dependencies: Dict[str, Set[str]]) -> List[str]:
        """Get correct table insertion order using topological sort."""
        visited = set()
        temp_visited = set()
        order = []

        def visit(table: str):
            if table in temp_visited:
                raise ValueError(f"Circular dependency detected at table {table}")
            if table in visited:
                return
            temp_visited.add(table)
            for dep in dependencies.get(table, []):
                visit(dep)
            temp_visited.remove(table)
            visited.add(table)
            order.append(table)

        # Visit all tables
        tables = set(dependencies.keys()) | {t for deps in dependencies.values() for t in deps}
        for table in tables:
            if table not in visited:
                visit(table)

        return order

    async def generate_import_statements(self, schema: DatabaseSchema, csv_path: str) -> List[str]:
        """Generate SQL INSERT statements to import CSV data according to schema."""
        # Read CSV data
        df = pd.read_csv(csv_path)
        
        # Build dependency graph and get insertion order
        dependencies = self._build_dependency_graph(schema)
        table_order = self._get_insertion_order(dependencies)
        
        insert_statements = []
        id_mappings = {}  # Store generated IDs: {table_name: {lookup_value: id}}

        for table_name in table_order:
            table = schema.get_table(table_name)
            if not table:
                continue

            # Get non-SERIAL columns
            data_columns = [col for col in table.columns 
                          if not col.type.upper().startswith('SERIAL')]
            
            # Map CSV columns to database columns
            csv_to_db = {}
            for col in data_columns:
                # Try different variations of column names
                possible_names = [
                    col.name,
                    f"{table_name}_{col.name}",
                    col.name.replace('_', '')
                ]
                for name in possible_names:
                    if name in df.columns:
                        csv_to_db[name] = col.name
                        break

            if csv_to_db:
                # Get unique rows for this table
                table_data = df[list(csv_to_db.keys())].drop_duplicates()
                
                # Generate INSERT statements
                for _, row in table_data.iterrows():
                    columns = []
                    values = []
                    
                    for csv_col, db_col in csv_to_db.items():
                        # Check if this is a foreign key
                        fk = next((fk for fk in table.foreign_keys if fk.column == db_col), None)
                        if fk:
                            # Get the lookup value from CSV
                            lookup_col = f"{fk.referenced_table}_name"  # e.g., customer_name
                            if lookup_col in df.columns:
                                lookup_value = row[lookup_col]
                                # Get previously generated ID
                                if lookup_value in id_mappings.get(fk.referenced_table, {}):
                                    columns.append(db_col)
                                    values.append(str(id_mappings[fk.referenced_table][lookup_value]))
                        else:
                            value = row[csv_col]
                            if pd.notna(value):
                                columns.append(db_col)
                                values.append(f"'{value}'" if isinstance(value, str) else str(value))

                    if columns and values:
                        # Add RETURNING clause for tables that others depend on
                        returning_clause = ""
                        if any(fk.referenced_table == table_name for t in schema.tables for fk in t.foreign_keys):
                            lookup_col = f"{table_name}_name"
                            if lookup_col in df.columns:
                                returning_clause = f" RETURNING id, {csv_to_db[lookup_col]}"

                        insert_sql = f"""
                        INSERT INTO {table_name} 
                        ({', '.join(columns)})
                        VALUES ({', '.join(values)})
                        {returning_clause};
                        """
                        insert_statements.append(insert_sql.strip())

        return insert_statements 