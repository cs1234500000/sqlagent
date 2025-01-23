from typing import Dict, List, Optional
from ..models.schema import DatabaseSchema
from ..models.query import QueryType
import json

class PromptBuilder:
    def __init__(self, templates_path: Optional[str] = None):
        """
        Initialize the PromptBuilder.
        
        Args:
            templates_path (Optional[str]): Path to custom prompt templates
        """
        self.templates = {}
        self.load_templates(templates_path)

    def load_templates(self, templates_path: Optional[str] = None):
        """Load prompt templates from file or use defaults"""
        if templates_path:
            with open(templates_path) as f:
                self.templates = json.load(f)
        else:
            # Default templates
            self.templates = {
                "base": """Given the following PostgreSQL database schema:
{schema}

Generate a PostgreSQL query for the following question: {question}

Important notes:
- Use PostgreSQL-specific date/time functions (e.g., date_trunc, extract)
- Use INTERVAL syntax like: CURRENT_DATE - INTERVAL '1 month'
- Always use single quotes for string and interval literals
- For month comparison, use EXTRACT(MONTH FROM timestamp_column)""",
                "with_context": """{base_prompt}

Additional context: {context}"""
            }

    def build_prompt(self, 
                    question: str, 
                    schema: str, 
                    query_type: Optional[QueryType] = None,
                    context: Optional[Dict] = None) -> str:
        """
        Build a prompt for the AI model.
        
        Args:
            question (str): User's question
            schema (str): Database schema
            query_type (Optional[QueryType]): Type of query to generate
            context (Optional[Dict]): Additional context
            
        Returns:
            str: Formatted prompt
        """
        base_prompt = self.templates["base"].format(
            schema=schema,
            question=question
        )
        
        if context:
            return self.templates["with_context"].format(
                base_prompt=base_prompt,
                context=json.dumps(context, indent=2)
            )
            
        return base_prompt

    def add_examples(self, prompt: str, examples: List[Dict]) -> str:
        """Add relevant examples to the prompt"""
        if not examples:
            return prompt
            
        examples_text = "\nHere are some similar examples:\n"
        for example in examples:
            examples_text += f"\nQuestion: {example['question']}\nQuery: {example['query']}\n"
            
        return prompt + examples_text

    def optimize_tokens(self, prompt: str, max_tokens: int = 4000) -> str:
        """Optimize prompt to fit within token limit"""
        # Simple token estimation (can be improved)
        estimated_tokens = len(prompt.split())
        if estimated_tokens <= max_tokens:
            return prompt
            
        # Truncate schema or examples if needed
        lines = prompt.split('\n')
        while estimated_tokens > max_tokens and len(lines) > 1:
            lines.pop(len(lines) // 2)  # Remove from middle to keep context
            estimated_tokens = len('\n'.join(lines).split())
            
        return '\n'.join(lines) 