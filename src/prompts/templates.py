from typing import Dict, Any
from enum import Enum

class TemplateType(str, Enum):
    """Types of query templates"""
    BASIC_SELECT = "basic_select"
    AGGREGATION = "aggregation"
    JOIN = "join"
    TEMPORAL = "temporal"
    SUBQUERY = "subquery"
    SCHEMA_GENERATION = "schema_generation"

class QueryTemplate:
    """Base class for query templates"""
    def __init__(self, template: str, parameters: Dict[str, Any]):
        self.template = template
        self.parameters = parameters

    def render(self, **kwargs) -> str:
        """Render the template with given parameters"""
        return self.template.format(**{**self.parameters, **kwargs})

class QueryTemplates:
    """Collection of SQL query templates"""
    templates = {
        TemplateType.BASIC_SELECT: QueryTemplate(
            template="SELECT {columns} FROM {table} WHERE {condition}",
            parameters={
                "columns": "*",
                "table": "",
                "condition": "1=1"
            }
        ),
        TemplateType.TEMPORAL: QueryTemplate(
            template="""
            SELECT {columns}
            FROM {table}
            WHERE {date_column} >= CURRENT_DATE - INTERVAL '{interval}'
            {additional_conditions}
            """,
            parameters={
                "columns": "*",
                "table": "",
                "date_column": "",
                "interval": "1 month",
                "additional_conditions": ""
            }
        ),
        TemplateType.AGGREGATION: QueryTemplate(
            template="""
            SELECT 
                {group_by_columns},
                {aggregations}
            FROM {table}
            {joins}
            WHERE {conditions}
            GROUP BY {group_by_columns}
            {having}
            """,
            parameters={
                "group_by_columns": "",
                "aggregations": "",
                "table": "",
                "joins": "",
                "conditions": "1=1",
                "having": ""
            }
        )
    }

    @classmethod
    def get_template(cls, template_type: TemplateType) -> QueryTemplate:
        """Get a query template by type"""
        return cls.templates[template_type]

    @classmethod
    def render_template(cls, template_type: TemplateType, **kwargs) -> str:
        """Render a template with given parameters"""
        template = cls.get_template(template_type)
        return template.render(**kwargs)

class SchemaPromptTemplates:
    """Templates for schema generation prompts"""
    
    BASE_SCHEMA = """Given the following data analysis, suggest an optimal PostgreSQL schema.

Data Analysis:
{analysis}

Requirements:
1. Use appropriate PostgreSQL data types (SERIAL for auto-incrementing IDs)
2. For foreign keys, reference the primary key of the parent table
3. Consider normalization when appropriate
4. Add appropriate constraints
5. Use clear naming conventions

Example of correct foreign key syntax:
- If a table has customer_id column referencing customers table:
  FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
- Column names should match between tables
- Always reference the primary key of the parent table
"""

    WITH_DESCRIPTION = BASE_SCHEMA + """
Additional Context:
{description}
"""

    SYSTEM_PROMPT = """You are a PostgreSQL expert. Design optimal database schemas following these principles:
1. Use appropriate PostgreSQL data types (SERIAL for auto-incrementing IDs)
2. For foreign keys:
   - Column names should match between tables (e.g., customer_id in both tables)
   - Only specify the referenced table name in foreign_key field
   - The referenced column will be derived from the foreign key column name
3. Follow naming conventions:
   - Use singular form for table names (customer not customers)
   - Use snake_case for all names
   - Use _id suffix for ID columns
4. Add meaningful constraints and descriptions
5. Consider performance implications"""

class SchemaFunctions:
    """Function definitions for schema generation"""
    
    SUGGEST_SCHEMA = {
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
                            "table_name": {
                                "type": "string",
                                "description": "Name of the table"
                            },
                            "description": {
                                "type": "string",
                                "description": "Description of the table's purpose"
                            },
                            "columns": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "name": {
                                            "type": "string",
                                            "description": "Name of the column"
                                        },
                                        "data_type": {
                                            "type": "string",
                                            "description": "PostgreSQL data type (e.g., SERIAL, INTEGER, VARCHAR(100))"
                                        },
                                        "nullable": {
                                            "type": "boolean",
                                            "description": "Whether the column can be NULL"
                                        },
                                        "primary_key": {
                                            "type": "boolean",
                                            "description": "Whether this is a primary key"
                                        },
                                        "foreign_key": {
                                            "type": "string",
                                            "description": "Reference table name only, e.g., 'customers' for a customer_id column"
                                        },
                                        "description": {
                                            "type": "string",
                                            "description": "Description of the column's purpose"
                                        }
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
    }

class DataImportTemplates:
    IMPORT_DATA = """
    Given this database schema:
    {schema}
    
    And CSV data with these columns:
    {csv_columns}
    
    Sample data:
    {data_sample}
    
    Generate a strategy to import this CSV data into the database tables.
    
    Requirements:
    1. For parent tables (no foreign keys):
       - Insert records using direct CSV values
       - Return SERIAL/generated IDs for later use
    
    2. For child tables (with foreign keys):
       - Use SELECT subqueries to get IDs from parent tables
       - Match on appropriate text columns (e.g., customer_name -> customers.name)
       - Never insert text values into foreign key columns
    
    3. Column mapping must:
       - Use exact CSV column names as source
       - Map to exact database column names
       - Skip SERIAL columns (they auto-generate)
       - Include all NOT NULL columns
    
    4. Import order must:
       - Start with parent tables
       - Follow with child tables after their parents
       - Respect all foreign key dependencies
    """ 