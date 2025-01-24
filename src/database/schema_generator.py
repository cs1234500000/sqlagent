import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import openai
from ..utils.config import Config
from ..models.schema import (
    GeneratedTableSchema, 
    GeneratedDatabaseSchema,
    DatabaseSchema
)
from ..prompts.templates import SchemaPromptTemplates, SchemaFunctions
import json

class SchemaGenerator:
    def __init__(self, config: Config):
        """Initialize the Schema Generator."""
        self.client = openai.OpenAI(api_key=config.openai_api_key)
        self.max_sample_rows = 100
        self.templates = SchemaPromptTemplates()
        self.functions = SchemaFunctions()

    def print_schema_structure(self, schema: DatabaseSchema) -> None:
        """Print the structure of a generated schema."""
        print("\nGenerated Schema Structure:")
        for table in schema.tables:
            print(f"\nTable: {table.name}")
            if table.description:
                print(f"Description: {table.description}")
            print("Columns:")
            for col in table.columns:
                col_def = f"  - {col.name}: {col.type}"
                if not col.is_nullable:
                    col_def += " NOT NULL"
                if col.is_primary:
                    col_def += " PRIMARY KEY"
                if col.description:
                    col_def += f" -- {col.description}"
                print(col_def)
            
            if table.foreign_keys:
                print("Foreign Keys:")
                for fk in table.foreign_keys:
                    print(f"  - {fk.column} -> {fk.referenced_table}.{fk.referenced_column}")

    async def generate_schema(self, 
                            csv_path: str, 
                            description: Optional[str] = None) -> DatabaseSchema:
        """Generate PostgreSQL schema from CSV file and optional description."""
        df = pd.read_csv(csv_path)
        data_analysis = self._analyze_data(df)
        
        if description:
            prompt = self.templates.WITH_DESCRIPTION.format(
                analysis=json.dumps(data_analysis, indent=2),
                description=description
            )
        else:
            prompt = self.templates.BASE_SCHEMA.format(
                analysis=json.dumps(data_analysis, indent=2)
            )
        
        suggestion = self._get_schema_suggestion(prompt)
        
        # Create GeneratedDatabaseSchema first
        generated_schema = GeneratedDatabaseSchema(
            tables=[GeneratedTableSchema(**table) for table in suggestion["tables"]],
            description=description
        )
        
        # Convert to standard DatabaseSchema
        return generated_schema.to_database_schema()

    def _analyze_data(self, df: pd.DataFrame) -> Dict:
        """Analyze CSV data for schema generation."""
        analysis = {
            "total_rows": int(len(df)),  # Convert to standard Python int
            "columns": {}
        }
        
        for column in df.columns:
            # Convert values to standard Python types
            sample_values = df[column].head(5).tolist()
            sample_values = [int(x) if isinstance(x, (pd.Int64Dtype, np.int64)) 
                           else float(x) if isinstance(x, (pd.Float64Dtype, np.float64))
                           else x for x in sample_values]
            
            col_analysis = {
                "name": str(column),
                "sample_values": sample_values,
                "unique_count": int(df[column].nunique()),
                "null_count": int(df[column].isnull().sum()),
                "data_type": str(df[column].dtype),
                "min": float(df[column].min()) if df[column].dtype in ['int64', 'float64'] else None,
                "max": float(df[column].max()) if df[column].dtype in ['int64', 'float64'] else None,
            }
            analysis["columns"][column] = col_analysis
            
        return analysis

    def _get_schema_suggestion(self, prompt: str) -> Dict:
        """Get schema suggestion from LLM."""
        functions = [{
            "name": "suggest_schema",
            "description": "Suggest PostgreSQL schema based on data analysis",
            "parameters": {
                "type": "object",
                "properties": {
                    "tables": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "table_name": {"type": "string"},
                                "description": {"type": "string"},
                                "columns": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "name": {"type": "string"},
                                            "data_type": {"type": "string"},
                                            "nullable": {"type": "boolean"},
                                            "primary_key": {"type": "boolean"},
                                            "foreign_key": {"type": "string"},
                                            "description": {"type": "string"}
                                        },
                                        "required": ["name", "data_type"]
                                    }
                                }
                            },
                            "required": ["table_name", "columns"]
                        }
                    }
                },
                "required": ["tables"]
            }
        }]

        response = self.client.chat.completions.create(
            model="gpt-4",  # Use GPT-4 for better schema design
            messages=[
                {
                    "role": "system",
                    "content": "You are a PostgreSQL expert. Design optimal database schemas."
                },
                {"role": "user", "content": prompt}
            ],
            functions=functions,
            function_call={"name": "suggest_schema"}
        )
        
        return json.loads(response.choices[0].message.function_call.arguments)

    def generate_sql(self, schemas: List[GeneratedTableSchema]) -> str:
        """Generate SQL CREATE TABLE statements."""
        sql_statements = []
        
        for schema in schemas:
            columns = []
            constraints = []
            
            for col in schema.columns:
                col_def = f"{col.name} {col.data_type}"
                if not col.nullable:
                    col_def += " NOT NULL"
                if col.primary_key:
                    constraints.append(f"PRIMARY KEY ({col.name})")
                if col.foreign_key:
                    constraints.append(
                        f"FOREIGN KEY ({col.name}) REFERENCES {col.foreign_key}"
                    )
                columns.append(col_def)
            
            all_lines = columns + constraints
            indented_lines = [f"    {line}" for line in all_lines]
            
            create_table = [
                f"CREATE TABLE {schema.table_name} (",
                ",\n".join(indented_lines),
                ");"
            ]
            
            table_sql = "\n".join(create_table)
            
            if schema.description:
                table_sql += f"\nCOMMENT ON TABLE {schema.table_name} IS '{schema.description}';"
            
            sql_statements.append(table_sql)
            
        return "\n\n".join(sql_statements) 