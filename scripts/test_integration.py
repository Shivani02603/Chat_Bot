"""
Test script for full integration of all agents
Tests the chatbot programmatically without interactive input
"""

import sys
from chat import RealEstateChatbot

def test_chatbot():
    print("=" * 60)
    print("Testing Real Estate Chatbot Integration")
    print("=" * 60)

    # Initialize chatbot
    chatbot = RealEstateChatbot(user_id='test_user_integration')

    # Test cases covering different intents
    test_queries = [
        "Find 2BHK apartments in Mumbai under 50 lakh",
        "Show me properties with 3 rooms",
        "Tell me about affordable properties",
        "What are current market rates in Bangalore?",
        "Estimate renovation cost for 1200 sqft apartment",
    ]

    print("\nRunning tests...\n")

    for i, query in enumerate(test_queries, 1):
        print(f"\nTest {i}: {query}")
        print("-" * 60)

        try:
            response = chatbot.chat(query)
            # Fix encoding for Windows
            response_clean = response.encode('ascii', 'ignore').decode('ascii')
            print(f"Response: {response_clean[:500]}...")
            print("Status: PASSED")
        except Exception as e:
            print(f"Status: FAILED")
            print(f"Error: {e}")

        print("-" * 60)

    print("\n" + "=" * 60)
    print("Integration Test Complete!")
    print("=" * 60)

if __name__ == '__main__':
    test_chatbot()
