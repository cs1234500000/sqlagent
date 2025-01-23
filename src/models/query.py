from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
from enum import Enum

class QueryType(str, Enum):
    """Types of supported queries"""
    SELECT = "SELECT"
    AGGREGATE = "AGGREGATE"
    JOIN = "JOIN"
    SUBQUERY = "SUBQUERY"
    WINDOW = "WINDOW"

class QueryParameter(BaseModel):
    """Query parameter definition"""
    name: str = Field(..., description="Parameter name")
    value: Any = Field(..., description="Parameter value")
    type: str = Field(..., description="Parameter type")

class QueryRequest(BaseModel):
    """Natural language query request"""
    question: str = Field(..., description="Natural language question")
    context: Optional[str] = Field(None, description="Additional context for the query")
    parameters: Optional[List[QueryParameter]] = Field(default_factory=list, description="Query parameters")
    max_results: Optional[int] = Field(None, description="Maximum number of results to return")
    timeout: Optional[float] = Field(30.0, description="Query timeout in seconds")

    @validator('question')
    def validate_question(cls, v):
        """Validate that the question is not empty"""
        if not v.strip():
            raise ValueError("Question cannot be empty")
        return v.strip()

class QueryMetadata(BaseModel):
    """Metadata about the executed query"""
    query_type: QueryType = Field(..., description="Type of query")
    tables_used: List[str] = Field(..., description="Tables used in the query")
    columns_used: List[str] = Field(..., description="Columns used in the query")
    execution_time: float = Field(..., description="Query execution time in seconds")
    timestamp: datetime = Field(default_factory=datetime.now, description="Query execution timestamp")

class QueryResult(BaseModel):
    """Query execution result"""
    query: str = Field(..., description="Executed SQL query")
    results: List[Dict[str, Any]] = Field(..., description="Query results")
    execution_time: float = Field(..., description="Query execution time in seconds")
    explanation: Optional[str] = Field(None, description="Query explanation")
    metadata: Optional[QueryMetadata] = Field(None, description="Query metadata")
    error: Optional[str] = Field(None, description="Error message if query failed")

    def format_results(self, format_type: str = "table") -> str:
        """
        Format query results for display.
        
        Args:
            format_type (str): Output format ("table", "json", "csv")
            
        Returns:
            str: Formatted results
        """
        if not self.results:
            return "No results found."
            
        if format_type == "json":
            import json
            return json.dumps(self.results, indent=2)
            
        elif format_type == "csv":
            import csv
            import io
            output = io.StringIO()
            if self.results:
                writer = csv.DictWriter(output, fieldnames=self.results[0].keys())
                writer.writeheader()
                writer.writerows(self.results)
            return output.getvalue()
            
        else:  # table format
            if not self.results:
                return "No results found."
                
            # Get column names from first row
            columns = list(self.results[0].keys())
            
            # Calculate column widths
            widths = {col: len(col) for col in columns}
            for row in self.results:
                for col in columns:
                    widths[col] = max(widths[col], len(str(row[col])))
                    
            # Create header
            header = " | ".join(col.ljust(widths[col]) for col in columns)
            separator = "-" * len(header)
            
            # Create rows
            rows = []
            for row in self.results:
                formatted_row = " | ".join(str(row[col]).ljust(widths[col]) for col in columns)
                rows.append(formatted_row)
                
            return "\n".join([header, separator] + rows) 