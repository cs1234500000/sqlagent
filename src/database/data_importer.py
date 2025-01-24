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
        self.id_mappings = {}  # Store returned IDs from parent tables
        self.fk_mappings = {}  # Store foreign key relationships

    def _build_dependency_graph(self, schema: DatabaseSchema) -> Dict[str, Set[str]]:
        """Build a graph of table dependencies based on foreign keys."""
        dependencies = defaultdict(set)
        for table in schema.tables:
            # Make sure table is in graph even if it has no dependencies
            if table.name not in dependencies:
                dependencies[table.name] = set()
            # Add dependencies from foreign keys
            for fk in table.foreign_keys:
                # Table with foreign key depends on referenced table
                dependencies[table.name].add(fk.referenced_table)
                # Make sure referenced table is in graph
                if fk.referenced_table not in dependencies:
                    dependencies[fk.referenced_table] = set()

        print(f"Dependency graph: {dict(dependencies)}")
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
            # First visit all dependencies (referenced tables)
            for dep in dependencies[table]:
                visit(dep)
            temp_visited.remove(table)
            visited.add(table)
            # Add table after its dependencies
            order.append(table)

        # Start with tables that have foreign keys
        tables_with_fk = [t for t, deps in dependencies.items() if deps]
        for table in tables_with_fk:
            if table not in visited:
                visit(table)

        # Then add any remaining tables
        for table in dependencies:
            if table not in visited:
                visit(table)

        print(f"Table insertion order: {order}")
        return order

    async def generate_import_statements(self, schema: DatabaseSchema, csv_path: str) -> List[str]:
        """Generate SQL INSERT statements to import CSV data according to schema."""
        df = pd.read_csv(csv_path)
        print(f"CSV columns: {df.columns.tolist()}")
        
        # Process each row in the CSV
        statements = []
        for idx, row in df.iterrows():
            # First insert into parent tables, then child tables
            for table_name in self._get_insertion_order(self._build_dependency_graph(schema)):
                table = schema.get_table(table_name)
                if not table:
                    continue

                # Map all columns, including primary key if it exists in CSV
                csv_to_db = {}
                for col in table.columns:
                    # Include primary key if it exists in CSV
                    if col.name in df.columns:
                        csv_to_db[col.name] = col.name
                    # Otherwise exclude auto-generated primary keys
                    elif not (col.is_primary and 'nextval' in str(col.default)):
                        csv_to_db[col.name] = col.name

                # Check if we have data for this table in current row
                has_data = any(col in row.index and pd.notna(row[col]) for col in csv_to_db.keys())
                if not has_data:
                    continue

                # Get next ID if table has a sequence AND primary key is not in CSV
                pk_col = next((col for col in table.columns if col.is_primary), None)
                if pk_col and pk_col.name not in df.columns and 'nextval' in str(pk_col.default):
                    seq_name = str(pk_col.default).split("'")[1].split("'")[0]
                    statements.append({
                        'type': 'nextval',
                        'row': idx,
                        'table': table_name,
                        'sql': f"SELECT nextval('{seq_name}');"
                    })

                columns = []
                values = []
                
                # Add regular columns
                for csv_col, db_col in csv_to_db.items():
                    if csv_col in row.index and pd.notna(row[csv_col]):
                        columns.append(db_col)
                        values.append(f"'{row[csv_col]}'" if isinstance(row[csv_col], str) else str(row[csv_col]))

                # Add foreign key references
                for fk in table.foreign_keys:
                    ref_table = fk.referenced_table
                    ref_pk_col = next(col for col in schema.get_table(ref_table).columns if col.is_primary)
                    
                    # Only use currval if the referenced primary key is auto-generated
                    if 'nextval' in str(ref_pk_col.default):
                        seq_name = str(ref_pk_col.default).split("'")[1].split("'")[0]
                        columns.append(fk.column)
                        values.append(f"currval('{seq_name}')")

                if columns and values:
                    insert_sql = f"""
                    INSERT INTO {table_name} 
                    ({', '.join(columns)})
                    VALUES ({', '.join(values)});
                    """
                    statements.append({
                        'type': 'insert',
                        'row': idx,
                        'table': table_name,
                        'sql': insert_sql.strip()
                    })

        return statements 