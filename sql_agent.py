import openai
import os
from typing import Optional, Dict, List
from dotenv import load_dotenv

class SQLAgent:
    def __init__(self, db_schema: str, model: str = "gpt-4"):
        """
        Initialize the SQL Agent.
        
        Args:
            db_schema (str): The database schema in SQL format
            model (str): The OpenAI model to use
        """
        load_dotenv()
        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.db_schema = db_schema
        self.model = model
        self.context_history: List[Dict] = []

    def _construct_prompt(self, question: str, context: Optional[str] = None) -> str:
        """
        Construct the prompt for the OpenAI API.
        """
        base_prompt = f"""Given the following database schema:
        {self.db_schema}
        
        Generate a SQL query for the following question: {question}"""
        
        if context:
            base_prompt += f"\nAdditional context: {context}"
            
        return base_prompt

    def generate_query(self, question: str, context: Optional[str] = None) -> str:
        """
        Generate SQL query from natural language.
        
        Args:
            question (str): The natural language question
            context (Optional[str]): Additional context for the query
            
        Returns:
            str: Generated SQL query
        """
        prompt = self._construct_prompt(question, context)
        
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a SQL expert. Generate only SQL queries without any explanations."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            sql_query = response.choices[0].message.content.strip()
            self.context_history.append({
                "question": question,
                "context": context,
                "generated_query": sql_query
            })
            
            return sql_query
            
        except Exception as e:
            raise Exception(f"Error generating SQL query: {str(e)}")

    def validate_query(self, query: str) -> bool:
        """
        Validate the generated SQL query for safety and correctness.
        
        Args:
            query (str): The SQL query to validate
            
        Returns:
            bool: True if query is valid, False otherwise
        """
        # Add validation logic here
        return True 