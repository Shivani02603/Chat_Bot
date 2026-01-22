"""
Main Chatbot Interface
Orchestrates all agents for the real estate chatbot
"""

import sys
from agents.router import QueryRouter
from agents.planner import Planner
from agents.structured_agent import StructuredAgent
from agents.rag_agent import RAGAgent
from agents.web_research import WebResearchAgent
from agents.report_generator import ReportGenerator
from agents.renovation import RenovationEstimator
from agents.memory import Memory


class RealEstateChatbot:
    """Main chatbot that coordinates all agents"""

    def __init__(self, user_id: str = 'default_user'):
        print("Initializing Real Estate Chatbot...")

        # Initialize all agents
        self.router = QueryRouter()
        self.planner = Planner()
        self.structured_agent = StructuredAgent()
        self.rag_agent = RAGAgent()
        self.web_agent = WebResearchAgent()
        self.report_generator = ReportGenerator()
        self.renovation_estimator = RenovationEstimator()

        # Initialize memory
        self.memory = Memory(user_id)

        print("Chatbot ready!\n")

    def chat(self, user_input: str) -> str:
        """
        Main chat function with Router → Planner → Agent(s) flow

        Args:
            user_input: User's message

        Returns:
            Bot's response
        """

        # Save to episodic memory
        self.memory.add_message('user', user_input)

        # Step 1: Route the query (detect complexity + extract intents + slots)
        query_type, intents, slots = self.router.route(user_input)

        print(f"[DEBUG] Query Type: {query_type}")
        print(f"[DEBUG] Intents: {intents}")
        print(f"[DEBUG] Slots: {slots}")

        # Step 2: Planner creates execution plan
        tasks = self.planner.plan(query_type, intents, slots)
        
        print(f"[DEBUG] Tasks: {tasks}")

        # Step 3: Execute tasks and collect responses
        if query_type == 'out_of_scope':
            response = "I can only help with real estate queries. Please ask about properties, prices, or renovations."
        elif query_type == 'simple-query':
            # Single agent execution
            response = self._execute_task(tasks[0], user_input)
        elif query_type == 'complex-query':
            # Multi-agent execution
            response = self._execute_complex_tasks(tasks, user_input)
        else:
            response = "I'm not sure how to help with that. Try asking about property search or renovation estimates."

        # Save response to episodic memory
        self.memory.add_message('assistant', response)

        return response

    def _execute_task(self, task: dict, user_input: str) -> str:
        """
        Execute a single task
        
        Args:
            task: Task dictionary with agent and params
            user_input: Original user input for context
            
        Returns:
            Agent's response
        """
        agent = task['agent']
        params = task['params']
        
        if agent == 'search_property':
            return self._handle_search(params)
        elif agent == 'estimate_renovation':
            return self._handle_renovation(params)
        elif agent == 'generate_report':
            return self._handle_report(params)
        elif agent == 'save_preference':
            return self._handle_save_preference(params, user_input)
        elif agent == 'web_research':
            return self._handle_web_research(user_input)
        elif agent == 'general_query':
            return self._handle_general_query(user_input, params)
        else:
            return "I'm not sure how to help with that."
    
    def _execute_complex_tasks(self, tasks: list, user_input: str) -> str:
        """
        Execute multiple tasks in sequence and combine responses
        
        Args:
            tasks: List of task dictionaries
            user_input: Original user input for context
            
        Returns:
            Combined response from all agents
        """
        responses = []
        
        for i, task in enumerate(tasks):
            print(f"[DEBUG] Executing task {i+1}/{len(tasks)}: {task['agent']}")
            
            response = self._execute_task(task, user_input)
            
            # Add task header for clarity in multi-step responses
            agent_name = task['agent'].replace('_', ' ').title()
            responses.append(f"**{agent_name}:**\n{response}")
        
        # Combine all responses
        combined_response = "\n\n" + "\n\n---\n\n".join(responses)
        
        return combined_response


    def _handle_search(self, slots: dict) -> str:
        """Handle property search"""
        properties = self.structured_agent.search_properties(slots)

        if not properties:
            return f"No properties found matching your criteria: {slots}"

        # Format response
        response = f"Found {len(properties)} properties:\n\n"
        for prop in properties[:10]:  # Show up to 10 properties
            response += f"- {prop['property_id']}: {prop['location']} - "
            response += f"{prop['num_rooms']} BHK, {prop['property_size_sqft']} sqft - "
            response += f"Rs.{prop['price']:,}\n"

        if len(properties) > 10:
            response += f"\n... and {len(properties) - 10} more properties"

        # Save last search to short-term memory (save all properties, not just IDs)
        self.memory.set_context('last_search_results', properties)

        return response

    def _handle_renovation(self, slots: dict) -> str:
        """Handle renovation estimation"""
        costs = self.renovation_estimator.estimate(
            property_size_sqft=slots.get('property_size_sqft'),
            num_rooms=slots.get('num_rooms')
        )

        return self.renovation_estimator.format_estimate(costs)

    def _handle_report(self, slots: dict) -> str:
        """Generate PDF report"""
        # Get last search results from short-term memory
        properties = self.memory.get_context('last_search_results')

        if not properties:
            return "No recent property searches found. Please search for properties first."

        # Use up to 10 properties for the report
        properties = properties[:10]

        if not properties:
            return "Could not generate report. Please search for properties first."

        # Generate report
        pdf_path = self.report_generator.generate_report(properties)

        return f"Report generated successfully! Saved to: {pdf_path}"

    def _handle_save_preference(self, slots: dict, user_input: str) -> str:
        """Save user preferences"""
        # Save to long-term memory
        if slots.get('max_price'):
            self.memory.save_preference('budget', str(slots['max_price']))

        if slots.get('location'):
            self.memory.save_preference('preferred_location', slots['location'])

        if slots.get('num_rooms'):
            self.memory.save_preference('preferred_rooms', str(slots['num_rooms']))

        return "Preferences saved! I'll remember them for future searches."

    def _handle_web_research(self, user_input: str) -> str:
        """Handle market research queries"""
        result = self.web_agent.research(user_input)
        return result['summary']

    def _handle_general_query(self, user_input: str, params: dict = None) -> str:
        """Handle general queries using RAG"""
        if params is None:
            params = {}

        # Extract certificate keywords if present
        certificate_keywords = params.get('certificate_keywords')

        # Call RAG agent with certificate context
        result = self.rag_agent.answer(
            user_input,
            certificate_keywords=certificate_keywords
        )
        response = result['answer']

        if result['sources']:
            response += f"\n\nSources: {', '.join(result['sources'])}"

        return response


def main():
    """Run interactive chatbot"""
    print("=" * 60)
    print("     Real Estate Chatbot - Phase 2")
    print("=" * 60)
    print("\nCommands:")
    print("  - Type your query to search properties")
    print("  - Type 'quit' or 'exit' to end")
    print("  - Type 'history' to see conversation")
    print("  - Type 'prefs' to see saved preferences")
    print("=" * 60)

    chatbot = RealEstateChatbot()

    while True:
        user_input = input("\nYou: ").strip()

        if not user_input:
            continue

        if user_input.lower() in ['quit', 'exit', 'bye']:
            print("Goodbye!")
            break

        if user_input.lower() == 'history':
            history = chatbot.memory.get_conversation_history()
            for msg in history:
                print(f"{msg['role'].upper()}: {msg['content'][:100]}...")
            continue

        if user_input.lower() == 'prefs':
            prefs = chatbot.memory.get_all_preferences()
            print(f"Saved preferences: {prefs}")
            continue

        # Get response
        response = chatbot.chat(user_input)
        print(f"\nBot: {response}")


if __name__ == '__main__':
    main()
