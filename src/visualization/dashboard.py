from typing import List, Dict, Any, Optional
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, html, dcc
import pandas as pd
import numpy as np
from datetime import datetime
import json
import openai
from ..utils.config import Config

class DashboardGenerator:
    def __init__(self, config: Config):
        """Initialize the dashboard generator."""
        self.app = Dash(__name__)
        self.client = openai.OpenAI(api_key=config.openai_api_key)
        
    def create_dashboard(self, query_results: List[Dict[str, Any]], query: str) -> Dash:
        """Create an interactive dashboard based on query results."""
        if not query_results:
            return self._create_empty_dashboard()
            
        # Convert results to DataFrame and preprocess
        df = pd.DataFrame(query_results)
        df = self._preprocess_dataframe(df)
        
        print("\nDebug - DataFrame Info:")
        print(df.dtypes)
        
        # Analyze data and determine appropriate visualizations
        viz_suggestions = self._analyze_data_for_visualization(df, query)
        
        # Create layout
        self.app.layout = html.Div([
            # Header Section
            html.Div([
                html.H1("Query Results Dashboard", style={'textAlign': 'center'}),
                html.Div([
                    html.H3("SQL Query:"),
                    html.Pre(query, style={'backgroundColor': '#f0f0f0', 'padding': '10px'})
                ])
            ]),
            
            # Data Overview Section
            html.Div([
                html.H2("Data Overview"),
                html.P(f"Total Records: {len(df)}"),
                html.P(f"Columns: {', '.join(df.columns)}")
            ]),
            
            # Dynamic Visualizations
            html.Div([
                self._create_visualization(df, viz_config) 
                for viz_config in viz_suggestions if viz_config
            ])
        ])
        
        return self.app
        
    def _preprocess_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Preprocess DataFrame to handle dates and numeric values."""
        # Define column types based on names
        date_columns = ['date', 'sale_date']
        numeric_columns = [
            'num_transactions', 'daily_revenue', 'avg_transaction_value',
            'times_sold', 'units_sold', 'total_revenue', 'avg_unit_price',
            'num_customers', 'unique_customers'
        ]
        
        for col in df.columns:
            try:
                if col in date_columns:
                    # Handle date columns
                    df[col] = pd.to_datetime(df[col], format='%Y-%m-%d')
                elif col in numeric_columns:
                    # Handle numeric columns
                    df[col] = pd.to_numeric(df[col])
                elif df[col].dtype == 'object':
                    # Try to convert other columns if they look numeric
                    try:
                        df[col] = pd.to_numeric(df[col])
                    except (ValueError, TypeError):
                        # Keep as string if not numeric
                        pass
            except Exception as e:
                print(f"Warning: Error processing column {col}: {str(e)}")
        
        return df
        
    def _analyze_data_for_visualization(self, df: pd.DataFrame, query: str) -> List[Dict]:
        """Analyze data and query to suggest appropriate visualizations."""
        try:
            # Get column types
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            datetime_cols = df.select_dtypes(include=['datetime64']).columns.tolist()
            categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
            
            print("\nDebug - Columns found:")
            print(f"Datetime: {datetime_cols}")
            print(f"Numeric: {numeric_cols}")
            print(f"Categorical: {categorical_cols}")
            
            suggestions = []
            
            # Time series visualization
            if datetime_cols and numeric_cols:
                for num_col in numeric_cols:
                    suggestions.append({
                        "type": "line",
                        "title": f"{num_col} Over Time",
                        "x_column": datetime_cols[0],
                        "y_column": num_col,
                        "color_by": categorical_cols[0] if categorical_cols else None,
                        "aggregation": "none",
                        "description": f"Time series analysis of {num_col}"
                    })
            
            # Bar charts for categorical analysis
            if categorical_cols and numeric_cols:
                for num_col in numeric_cols:
                    suggestions.append({
                        "type": "bar",
                        "title": f"{categorical_cols[0]} by {num_col}",
                        "x_column": categorical_cols[0],
                        "y_column": num_col,
                        "color_by": categorical_cols[1] if len(categorical_cols) > 1 else None,
                        "aggregation": "sum",
                        "description": f"Distribution of {num_col} across {categorical_cols[0]}"
                    })
            
            return suggestions
            
        except Exception as e:
            print(f"Error in visualization analysis: {str(e)}")
            return []
        
    def _get_llm_suggestions(self, df: pd.DataFrame, query: str, 
                           numeric_cols: List[str], datetime_cols: List[str], 
                           categorical_cols: List[str]) -> List[Dict]:
        """Get visualization suggestions from LLM."""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a data visualization expert. Return a JSON object with a 'visualizations' array containing visualization configs."},
                    {"role": "user", "content": self._create_llm_prompt(df, query, numeric_cols, datetime_cols, categorical_cols)}
                ]
            )
            
            # Extract JSON from the response
            content = response.choices[0].message.content
            try:
                # Try to find JSON-like content within the response
                start_idx = content.find('{')
                end_idx = content.rfind('}') + 1
                if start_idx >= 0 and end_idx > start_idx:
                    json_str = content[start_idx:end_idx]
                    suggestions = json.loads(json_str).get('visualizations', [])
                    return suggestions
            except:
                print("Warning: Could not parse LLM response as JSON")
                return []
                
        except Exception as e:
            print(f"Error getting LLM suggestions: {str(e)}")
            return []
            
    def _create_llm_prompt(self, df: pd.DataFrame, query: str, 
                          numeric_cols: List[str], datetime_cols: List[str], 
                          categorical_cols: List[str]) -> str:
        """Create prompt for LLM visualization suggestions."""
        return f"""Analyze this SQL query and data to suggest visualizations.
        
        Query: {query}
        
        Data Summary:
        - Rows: {len(df)}
        - Numeric columns: {', '.join(numeric_cols)}
        - DateTime columns: {', '.join(datetime_cols)}
        - Categorical columns: {', '.join(categorical_cols)}
        
        Sample data:
        {df.head().to_string()}
        
        Return a JSON object with a 'visualizations' array containing configs like:
        {{
            "visualizations": [
                {{
                    "type": "line|bar|scatter|pie",
                    "title": "chart title",
                    "x_column": "column_name",
                    "y_column": "column_name",
                    "color_by": "optional_column",
                    "aggregation": "sum|mean|count|none",
                    "description": "why this visualization is useful"
                }}
            ]
        }}
        """
        
    def _create_visualization(self, df: pd.DataFrame, config: Dict) -> html.Div:
        """Create a visualization based on configuration."""
        try:
            viz_type = config['type']
            title = config['title']
            
            if viz_type == 'line':
                fig = px.line(df, 
                            x=config['x_column'],
                            y=config['y_column'],
                            color=config.get('color_by'),
                            title=title)
                            
            elif viz_type == 'bar':
                agg_df = self._aggregate_data(df, config)
                fig = px.bar(agg_df,
                            x=config['x_column'],
                            y=config['y_column'],
                            color=config.get('color_by'),
                            title=title)
                            
            elif viz_type == 'scatter':
                fig = px.scatter(df,
                            x=config['x_column'],
                            y=config['y_column'],
                            color=config.get('color_by'),
                            title=title)
                            
            elif viz_type == 'pie':
                agg_df = self._aggregate_data(df, config)
                fig = px.pie(agg_df,
                            values=config['y_column'],
                            names=config['x_column'],
                            title=title)
                            
            else:  # fallback to histogram
                fig = px.histogram(df,
                                x=config['x_column'],
                                color=config.get('color_by'),
                                title=title)
                                
            return html.Div([
                html.H3(title),
                html.P(config['description']),
                dcc.Graph(figure=fig)
            ])
            
        except Exception as e:
            print(f"Error creating visualization: {str(e)}")
            return html.Div([
                html.P(f"Error creating visualization: {str(e)}")
            ])
        
    def _aggregate_data(self, df: pd.DataFrame, config: Dict) -> pd.DataFrame:
        """Aggregate data based on configuration."""
        if not config.get('aggregation') or config['aggregation'] == 'none':
            return df
            
        agg_func = {
            'sum': 'sum',
            'mean': 'mean',
            'count': 'count'
        }.get(config['aggregation'])
        
        return df.groupby(config['x_column'])[config['y_column']].agg(agg_func).reset_index()
        
    def _is_datetime(self, series: pd.Series) -> bool:
        """Check if a series contains datetime values."""
        try:
            pd.to_datetime(series)
            return True
        except:
            return False
            
    def _create_empty_dashboard(self) -> Dash:
        """Create an empty dashboard when no results are available."""
        self.app.layout = html.Div([
            html.H1("No Results Available", style={'textAlign': 'center'}),
            html.P("The query returned no results to visualize.")
        ])
        return self.app 