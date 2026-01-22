"""
Web Research Agent - Live Market Data
Uses Tavily API for real-time market information
"""

import os
import requests
from dotenv import load_dotenv


class WebResearchAgent:
    """Fetches live market data and neighborhood info"""

    def __init__(self):
        load_dotenv()
        self.tavily_api_key = os.getenv('TAVILY_API_KEY')
        self.tavily_url = "https://api.tavily.com/search"

    def research(self, query: str) -> dict:
        """
        Search for market information

        Returns: {
            "results": [{"title": str, "content": str, "url": str}],
            "summary": str
        }
        """

        if not self.tavily_api_key:
            return self._fallback_response(query)

        try:
            # Call Tavily API
            response = requests.post(
                self.tavily_url,
                json={
                    "api_key": self.tavily_api_key,
                    "query": query,
                    "search_depth": "basic",
                    "max_results": 3
                },
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                return {
                    "results": data.get('results', []),
                    "summary": self._summarize_results(data.get('results', []))
                }
            else:
                return self._fallback_response(query)

        except Exception as e:
            print(f"Tavily API error: {e}")
            return self._fallback_response(query)

    def _summarize_results(self, results: list) -> str:
        """Create a summary from search results"""

        if not results:
            return "No recent market data found."

        summary_parts = []
        for i, result in enumerate(results[:3], 1):
            summary_parts.append(
                f"{i}. {result.get('title', 'N/A')}: {result.get('content', 'N/A')[:200]}..."
            )

        return '\n\n'.join(summary_parts)

    def _fallback_response(self, query: str) -> dict:
        """Fallback when Tavily is not available"""

        return {
            "results": [],
            "summary": f"Real-time market data for '{query}' is not available. "
                      f"Please check with local real estate websites for current rates."
        }
