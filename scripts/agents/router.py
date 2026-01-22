"""
Query Router - LLM-based Intent Classification & Complexity Detection
Detects if query is simple (single agent) or complex (multiple agents)
"""

import os
import json
import requests
from typing import Dict, Tuple, List
from dotenv import load_dotenv


class QueryRouter:
    """Routes user queries and detects complexity for planner"""

    def __init__(self):
        load_dotenv()
        self.hf_token = os.getenv('HF_TOKEN')
        self.model = "meta-llama/Llama-3.2-3B-Instruct:novita"
        self.api_url = "https://router.huggingface.co/v1/chat/completions"

    def route(self, user_input: str) -> Tuple[str, List[str], Dict]:
        """
        Main routing function - detects complexity and extracts intents
        
        Returns: (query_type, intents_list, slots)
            query_type: "simple-query" or "complex-query" or "out_of_scope"
            intents_list: List of intents to execute in order
            slots: Extracted parameters
        """
        # Build the prompt
        prompt = self._build_prompt(user_input)

        # Call LLM
        llm_response = self._call_llm(prompt)

        # Parse JSON response
        result = self._extract_json(llm_response)

        # Determine query type and return appropriate structure
        if not result['in_scope']:
            return 'out_of_scope', [], {}
        
        intents = result.get('intents', [])
        slots = result.get('slots', {})
        
        # Determine if simple or complex based on number of intents
        if len(intents) == 1:
            return 'simple-query', intents, slots
        else:
            return 'complex-query', intents, slots

    def _build_prompt(self, user_query: str) -> str:
        """Create the routing prompt for complexity detection and intent extraction"""
        return f"""You are a real estate query analyzer. Analyze the query and return ONLY valid JSON (no other text).

Query: {user_query}

Your task:
1. Determine if query is real estate related (in_scope: true/false)
2. Identify ALL distinct actions requested (intents array)
3. Extract property parameters (slots object)

IMPORTANT RULES:
- intents must be an ARRAY (even for single intent: ["search_property"])
- Do NOT include duplicate intents
- List intents in logical execution order
- If multiple actions requested, include ALL as separate intents
- Choose ONLY from: [search_property, estimate_renovation, generate_report, save_preference, web_research, general_query]

JSON structure:
{{
  "in_scope": boolean,
  "intents": [intent1, intent2, ...],
  "slots": {{
    "location": string or null,
    "num_rooms": number or null,
    "max_price": number or null,
    "property_size_sqft": number or null,
    "certificate_keywords": string or null
  }}
}}

IMPORTANT for certificate_keywords:
- Extract if query mentions: "certificate", "certified", "certification", "green building", "fire safety", "pest control", "structural safety"
- Store the specific certificate type mentioned (e.g., "green building", "fire safety")
- Set to null if no certificate-related terms found

Examples:

Query: "Find 2BHK in Mumbai under 50 lakh"
{{"in_scope": true, "intents": ["search_property"], "slots": {{"location": "Mumbai", "num_rooms": 2, "max_price": 5000000, "property_size_sqft": null, "certificate_keywords": null}}}}

Query: "Show me properties with green building certification"
{{"in_scope": true, "intents": ["general_query"], "slots": {{"location": null, "num_rooms": null, "max_price": null, "property_size_sqft": null, "certificate_keywords": "green building"}}}}

Query: "Find fire safety certified properties in Bangalore"
{{"in_scope": true, "intents": ["general_query"], "slots": {{"location": "Bangalore", "num_rooms": null, "max_price": null, "property_size_sqft": null, "certificate_keywords": "fire safety"}}}}

Query: "Find 3BHK properties in Bangalore, estimate renovation cost, and generate a comparison report"
{{"in_scope": true, "intents": ["search_property", "estimate_renovation", "generate_report"], "slots": {{"location": "Bangalore", "num_rooms": 3, "max_price": null, "property_size_sqft": null, "certificate_keywords": null}}}}

Query: "Show me properties under 1 crore and save my budget preference"
{{"in_scope": true, "intents": ["search_property", "save_preference"], "slots": {{"location": null, "num_rooms": null, "max_price": 10000000, "property_size_sqft": null, "certificate_keywords": null}}}}

Query: "What are current market rates in Delhi?"
{{"in_scope": true, "intents": ["web_research"], "slots": {{"location": "Delhi", "num_rooms": null, "max_price": null, "property_size_sqft": null, "certificate_keywords": null}}}}

Query: "Estimate renovation for 1200 sqft"
{{"in_scope": true, "intents": ["estimate_renovation"], "slots": {{"location": null, "num_rooms": null, "max_price": null, "property_size_sqft": 1200, "certificate_keywords": null}}}}

Query: "Who is the president?"
{{"in_scope": false, "intents": [], "slots": {{"location": null, "num_rooms": null, "max_price": null, "property_size_sqft": null, "certificate_keywords": null}}}}

Now analyze this query and return ONLY the JSON:"""

    def _call_llm(self, prompt: str) -> str:
        """Call HuggingFace API using chat completions endpoint"""
        headers = {
            "Authorization": f"Bearer {self.hf_token}",
        }

        payload = {
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "model": self.model,
            "max_tokens": 200,
            "temperature": 0.1
        }

        response = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()

        result = response.json()
        return result["choices"][0]["message"]["content"]

    def _extract_json(self, text: str) -> Dict:
        """Extract and validate JSON from LLM response"""
        # Find JSON between { }
        start = text.find('{')
        end = text.rfind('}') + 1

        if start == -1 or end == 0:
            # Fallback if no JSON found
            print(f"\nWarning: No JSON found in response")
            print(f"Raw LLM response: {text[:200]}")
            return {'in_scope': True, 'intents': ['general_query'], 'slots': {}}

        json_str = text[start:end]

        try:
            result = json.loads(json_str)
            
            # Validate and clean the result
            result = self._validate_and_clean(result)
            
            return result
            
        except json.JSONDecodeError as e:
            print(f"\nError: Failed to parse JSON")
            print(f"Raw LLM response: {text}")
            print(f"Extracted JSON string: {json_str}")
            print(f"JSON Error: {e}")
            # Fallback to general_query on JSON errors
            return {'in_scope': True, 'intents': ['general_query'], 'slots': {}}
    
    def _validate_and_clean(self, result: Dict) -> Dict:
        """
        Validate and clean the parsed JSON result
        - Ensure intents is a list
        - Remove duplicate intents while preserving order
        - Validate intent names
        """
        # Ensure intents exists and is a list
        if 'intents' not in result:
            result['intents'] = ['general_query']
        elif not isinstance(result['intents'], list):
            # If intents is a string, convert to list
            result['intents'] = [result['intents']]
        
        # Remove duplicates while preserving order
        seen = set()
        unique_intents = []
        for intent in result['intents']:
            if intent not in seen:
                seen.add(intent)
                unique_intents.append(intent)
        
        result['intents'] = unique_intents
        
        # Validate intent names (must be from allowed list)
        allowed_intents = {
            'search_property', 'estimate_renovation', 'generate_report',
            'save_preference', 'web_research', 'general_query'
        }
        
        validated_intents = [
            intent for intent in result['intents']
            if intent in allowed_intents
        ]
        
        # If no valid intents, default to general_query
        if not validated_intents:
            validated_intents = ['general_query']
        
        result['intents'] = validated_intents
        
        # Ensure slots exists
        if 'slots' not in result:
            result['slots'] = {}
        
        # Ensure in_scope exists
        if 'in_scope' not in result:
            result['in_scope'] = True
        
        return result
