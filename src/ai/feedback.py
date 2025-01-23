from typing import Dict, List, Any, Optional
from ..models.query import QueryResult
import json
from datetime import datetime

class FeedbackCollector:
    def __init__(self, feedback_file: Optional[str] = None):
        """
        Initialize the Feedback Collector.
        
        Args:
            feedback_file (Optional[str]): Path to store feedback data
        """
        self.feedback_file = feedback_file or "feedback.json"
        self.feedback_data: List[Dict] = self._load_feedback()

    def add_feedback(self, 
                    query_result: QueryResult, 
                    feedback_type: str,
                    feedback_text: str,
                    user_id: Optional[str] = None) -> None:
        """
        Add user feedback for a query.
        
        Args:
            query_result (QueryResult): The query result
            feedback_type (str): Type of feedback (success/failure/improvement)
            feedback_text (str): Detailed feedback
            user_id (Optional[str]): ID of the user providing feedback
        """
        feedback = {
            "timestamp": datetime.now().isoformat(),
            "query": query_result.query,
            "question": query_result.metadata.question if query_result.metadata else None,
            "execution_time": query_result.execution_time,
            "feedback_type": feedback_type,
            "feedback_text": feedback_text,
            "user_id": user_id
        }
        
        self.feedback_data.append(feedback)
        self._save_feedback()

    def analyze_feedback(self) -> Dict[str, Any]:
        """
        Analyze collected feedback to improve query generation.
        
        Returns:
            Dict[str, Any]: Analysis results
        """
        analysis = {
            "total_feedback": len(self.feedback_data),
            "success_rate": 0,
            "common_issues": {},
            "improvement_suggestions": []
        }
        
        success_count = 0
        for feedback in self.feedback_data:
            if feedback["feedback_type"] == "success":
                success_count += 1
            elif feedback["feedback_type"] == "failure":
                issue = feedback["feedback_text"]
                analysis["common_issues"][issue] = analysis["common_issues"].get(issue, 0) + 1
                
        analysis["success_rate"] = success_count / len(self.feedback_data) if self.feedback_data else 0
        
        return analysis

    def get_learning_examples(self) -> List[Dict[str, Any]]:
        """
        Get successful queries as learning examples.
        
        Returns:
            List[Dict[str, Any]]: List of successful query examples
        """
        return [
            {
                "question": feedback["question"],
                "query": feedback["query"]
            }
            for feedback in self.feedback_data
            if feedback["feedback_type"] == "success"
        ]

    def _load_feedback(self) -> List[Dict]:
        """Load feedback data from file"""
        try:
            with open(self.feedback_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _save_feedback(self):
        """Save feedback data to file"""
        with open(self.feedback_file, 'w') as f:
            json.dump(self.feedback_data, f, indent=2) 