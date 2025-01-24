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
        
        dependencies = self._build_dependency_graph(schema)
        table_order = self._get_insertion_order(dependencies)
        
        # Get sequence names for each table
        sequence_names = {}  # table -> sequence_name
        for table in schema.tables:
            pk_col = next((col for col in table.columns if col.is_primary), None)
            if pk_col and 'nextval' in str(pk_col.default):
                # Extract sequence name from: nextval('sequence_name'::regclass)
                seq_name = str(pk_col.default).split("'")[1].split("'")[0]
                sequence_names[table.name] = seq_name
                print(f"Found sequence {seq_name} for table {table.name}")

        statements = []
        
        for table_name in table_order:
            print(f"\nProcessing table: {table_name}")
            table = schema.get_table(table_name)
            if not table:
                continue

            # Map all non-auto-generated columns
            csv_to_db = {}
            for col in table.columns:
                if not (col.is_primary and 'nextval' in str(col.default)):
                    csv_to_db[col.name] = col.name

            print(f"CSV to DB mapping for {table_name}: {csv_to_db}")

            if csv_to_db:
                # Get all required columns from CSV
                available_cols = [col for col in csv_to_db.keys() if col in df.columns]
                table_data = df[available_cols].drop_duplicates()
                
                for _, row in table_data.iterrows():
                    # First get the next ID if this table has a sequence
                    if table_name in sequence_names:
                        statements.append(f"SELECT nextval('{sequence_names[table_name]}');")

                    columns = []
                    values = []

                    # Add regular columns from CSV
                    for csv_col in csv_to_db.keys():
                        if csv_col in row.index and pd.notna(row[csv_col]):
                            columns.append(csv_col)
                            values.append(f"'{row[csv_col]}'" if isinstance(row[csv_col], str) else str(row[csv_col]))

                    # Add foreign key references using currval
                    for fk in table.foreign_keys:
                        ref_table = fk.referenced_table
                        if ref_table in sequence_names:
                            columns.append(fk.column)
                            values.append(f"currval('{sequence_names[ref_table]}')")

                    if columns and values:
                        insert_sql = f"""
                        INSERT INTO {table_name} 
                        ({', '.join(columns)})
                        VALUES ({', '.join(values)});
                        """
                        statements.append(insert_sql.strip())

        return statements 