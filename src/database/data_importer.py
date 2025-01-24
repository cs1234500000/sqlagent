from typing import Dict, List, Any, Set
import pandas as pd
import openai
from ..utils.config import Config
from ..models.schema import DatabaseSchema
from ..prompts.templates import DataImportTemplates
import json
from collections import defaultdict

class DataImporter:
    def __init__(self, config: Config, executor=None):
        """Initialize the Data Importer."""
        self.client = openai.OpenAI(api_key=config.openai_api_key)
        self.templates = DataImportTemplates()
        self.id_mappings = defaultdict(dict)  # Store returned IDs from parent tables {table: {csv_key: db_id}}
        self.executor = executor

    def _build_dependency_graph(self, schema: DatabaseSchema) -> Dict[str, Set[str]]:
        """Build a graph of table dependencies based on foreign keys."""
        dependencies = defaultdict(set)
        for table in schema.tables:
            if table.name not in dependencies:
                dependencies[table.name] = set()
            for fk in table.foreign_keys:
                dependencies[table.name].add(fk.referenced_table)
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
            for dep in dependencies[table]:
                visit(dep)
            temp_visited.remove(table)
            visited.add(table)
            order.append(table)

        for table in dependencies:
            if table not in visited:
                visit(table)

        return order

    def _generate_composite_key(self, row: pd.Series, key_columns: List[str]) -> str:
        """Generate a composite key from multiple columns."""
        return "|".join(str(row[col]) for col in key_columns)

    async def generate_and_execute_statements(self, schema: DatabaseSchema, csv_path: str) -> None:
        """Generate and execute SQL INSERT statements in correct order."""
        df = pd.read_csv(csv_path)
        print(f"CSV columns: {df.columns.tolist()}")
        
        insertion_order = self._get_insertion_order(self._build_dependency_graph(schema))
        print(f"\nInsertion order: {insertion_order}")
        
        for table_name in insertion_order:
            table = schema.get_table(table_name)
            if not table:
                continue
                        
            # Get all required columns for this table
            required_columns = []
            for col in table.columns:
                if not col.is_primary and not col.is_nullable:
                    required_columns.append(col.name)
            
            # Group rows for bulk insert
            table_data = []
            row_indices = []
            
            # Process each row
            for idx, row in df.iterrows():
                columns = []
                values = []
                
                # First handle foreign keys
                for fk in table.foreign_keys:
                    ref_table = fk.referenced_table
                    if idx in self.id_mappings[ref_table]:
                        fk_value = self.id_mappings[ref_table][idx]
                        columns.append(fk.column)
                        values.append(fk_value)
                
                # Then add regular columns
                for col in table.columns:
                    if col.name in df.columns and pd.notna(row[col.name]) and not col.is_primary:
                        if col.name not in columns:  # Skip if already added as FK
                            columns.append(col.name)
                            values.append(row[col.name])
                
                # Verify all required columns are present
                missing_columns = set(required_columns) - set(columns)
                if missing_columns:
                    continue
                
                if columns and values:
                    table_data.append({
                        'columns': columns,
                        'values': values
                    })
                    row_indices.append(idx)
            
            if not table_data:
                print(f"No valid rows for {table_name}")
                continue
            
            # Generate and execute bulk insert
            all_columns = []
            # First add foreign key columns
            for fk in table.foreign_keys:
                if fk.column not in all_columns:
                    all_columns.append(fk.column)
            
            # Then add other required columns
            for col in required_columns:
                if col not in all_columns:
                    all_columns.append(col)
            
            # Finally add any remaining columns
            for data in table_data:
                for col in data['columns']:
                    if col not in all_columns:
                        all_columns.append(col)
            
            # Prepare values
            value_lists = []
            for data in table_data:
                row_values = []
                current_columns = data['columns']
                current_values = data['values']
                
                # Create row values in the same order as all_columns
                for col in all_columns:
                    try:
                        idx = current_columns.index(col)
                        val = current_values[idx]
                        row_values.append(f"'{val}'" if isinstance(val, str) else str(val))
                    except ValueError:
                        break
                else:
                    value_lists.append(f"({', '.join(row_values)})")
            
            if not value_lists:
                continue
            
            # Generate and execute INSERT
            pk_col = next((col for col in table.columns if col.is_primary), None)
            if pk_col:
                insert_sql = f"""
                WITH inserted_rows AS (
                    INSERT INTO {table_name} 
                    ({', '.join(all_columns)})
                    VALUES {', '.join(value_lists)}
                    RETURNING {pk_col.name}
                )
                SELECT {pk_col.name} FROM inserted_rows;
                """
            else:
                insert_sql = f"""
                INSERT INTO {table_name} 
                ({', '.join(all_columns)})
                VALUES {', '.join(value_lists)};
                """
            
            # Execute the statement and update mappings
            result = await self.executor.execute(insert_sql, commit=True)
            if result and pk_col:
                returned_ids = [dict(row)[pk_col.name] for row in result]
                self._update_id_mappings(table_name, row_indices, returned_ids)

    def _update_id_mappings(self, table_name: str, row_indices: List[int], returned_ids: List[Any]):
        """Update ID mappings with returned values using row indices."""
        
        for idx, db_id in zip(row_indices, returned_ids):
            self.id_mappings[table_name][idx] = db_id
            # print(f"Mapped {table_name}[{idx}] -> {db_id}") 