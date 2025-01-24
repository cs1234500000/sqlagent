from typing import Dict, List, Any, Optional
from ..models.query import QueryRequest, QueryResult
import json

class ContextManager:
    def __init__(self):
        """Initialize the Context Manager"""
        self.conversation_history: List[Dict] = []
        self.context_window: int = 5  # Number of previous queries to consider

    def build_context(self, question: str, history: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Build context for the current question.
        
        Args:
            question (str): Current question
            history (Optional[List[Dict]]): Previous queries and results
            
        Returns:
            Dict[str, Any]: Context information
        """
        context = {
            "current_question": question,
            "previous_queries": [],
            "relevant_tables": [],
            "suggested_joins": []
        }
        
        if history:
            # Add relevant previous queries
            for item in history[-self.context_window:]:
                if self._is_relevant(question, item):
                    context["previous_queries"].append({
                        "question": item["question"],
                        "query": item["generated_query"]
                    })
                    
        return context

    def analyze_user_intent(self, question: str) -> Dict[str, Any]:
        """
        Analyze the user's question to understand intent.
        
        Args:
            question (str): User's question
            
        Returns:
            Dict[str, Any]: Intent analysis
        """
        # Simple keyword-based analysis (can be enhanced with NLP)
        intent = {
            "type": "query",
            "timeframe": None,
            "aggregation": False,
            "filters": []
        }
        
        # Check for time-related keywords
        if any(word in question.lower() for word in ["last month", "previous year", "today"]):
            intent["timeframe"] = "temporal"
            
        # Check for aggregation keywords
        if any(word in question.lower() for word in ["average", "total", "count", "sum"]):
            intent["aggregation"] = True
            
        return intent

    def maintain_conversation(self, request: QueryRequest, result: QueryResult):
        """
        Update conversation history with new query.
        
        Args:
            request (QueryRequest): Current request
            result (QueryResult): Query result
        """
        self.conversation_history.append({
            "question": request.question,
            "context": request.context,
            "generated_query": result.query,
            "execution_time": result.execution_time,
            "timestamp": result.metadata.timestamp if result.metadata else None
        })
        
        # Trim history if too long
        if len(self.conversation_history) > self.context_window * 2:
            self.conversation_history = self.conversation_history[-self.context_window:]

    def _is_relevant(self, current_question: str, historical_item: Dict) -> bool:
        """Check if a historical query is relevant to current question"""
        # Simple relevance check based on common words (can be enhanced)
        current_words = set(current_question.lower().split())
        historical_words = set(historical_item["question"].lower().split())
        
        common_words = current_words.intersection(historical_words)
        return len(common_words) >= 2  # At least 2 words in common 