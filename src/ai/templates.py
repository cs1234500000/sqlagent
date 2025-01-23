from typing import Dict, Any
from enum import Enum

class TemplateType(str, Enum):
    """Types of query templates"""
    BASIC_SELECT = "basic_select"
    AGGREGATION = "aggregation"
    JOIN = "join"
    TEMPORAL = "temporal"
    SUBQUERY = "subquery"

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