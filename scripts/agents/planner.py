"""
Planner - Task Orchestration & Execution
Handles both simple (single agent) and complex (multi-agent) queries
"""

from typing import List, Dict, Tuple
from dotenv import load_dotenv


class Planner:
    """Orchestrates agent execution based on query complexity"""

    def __init__(self):
        load_dotenv()

    def plan(self, query_type: str, intents: List[str], slots: Dict) -> List[Dict]:
        """
        Create execution plan based on query complexity
        
        Args:
            query_type: "simple-query", "complex-query", or "out_of_scope"
            intents: List of intents from router (ordered)
            slots: Extracted parameters from router
            
        Returns: List of task dictionaries to execute in order
        Example: [
            {"agent": "search_property", "params": {"location": "Mumbai", "num_rooms": 2}},
            {"agent": "estimate_renovation", "params": {"property_size_sqft": 1200}},
            {"agent": "generate_report", "params": {}}
        ]
        """
        
        if query_type == 'out_of_scope':
            return []
        
        if query_type == 'simple-query':
            return self._plan_simple(intents, slots)
        
        elif query_type == 'complex-query':
            return self._plan_complex(intents, slots)
        
        else:
            # Fallback to simple
            return self._plan_simple(intents, slots)
    
    def _plan_simple(self, intents: List[str], slots: Dict) -> List[Dict]:
        """
        Plan for simple queries (single agent)
        
        Args:
            intents: List with single intent
            slots: All extracted parameters
            
        Returns: Single task with relevant parameters
        """
        if not intents:
            return [{"agent": "general_query", "params": {}}]
        
        intent = intents[0]
        params = self._extract_relevant_params(intent, slots)
        
        return [{"agent": intent, "params": params}]
    
    def _plan_complex(self, intents: List[str], slots: Dict) -> List[Dict]:
        """
        Plan for complex queries (multiple agents in sequence)
        
        Args:
            intents: Ordered list of intents to execute
            slots: All extracted parameters
            
        Returns: Multiple tasks with their parameters
        """
        if not intents:
            return [{"agent": "general_query", "params": {}}]
        
        tasks = []
        
        for intent in intents:
            params = self._extract_relevant_params(intent, slots)
            tasks.append({"agent": intent, "params": params})
        
        return tasks
    
    def _extract_relevant_params(self, intent: str, slots: Dict) -> Dict:
        """
        Extract only relevant parameters for each agent type
        
        Args:
            intent: The agent intent
            slots: All available slots
            
        Returns: Filtered parameters for the specific agent
        """
        # Define what parameters each agent needs
        agent_params = {
            'search_property': ['location', 'num_rooms', 'max_price', 'property_size_sqft'],
            'estimate_renovation': ['property_size_sqft', 'num_rooms'],
            'generate_report': [],  # Uses context from previous searches
            'save_preference': ['location', 'num_rooms', 'max_price'],
            'web_research': [],  # Uses full query context
            'general_query': ['certificate_keywords']  # Pass certificate info to RAG
        }
        
        relevant_keys = agent_params.get(intent, [])
        
        # Filter slots to only include relevant parameters with non-null values
        params = {
            key: slots[key] 
            for key in relevant_keys 
            if key in slots and slots[key] is not None
        }
        
        return params
