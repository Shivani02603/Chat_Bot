"""
Utility functions for Streamlit UI
API client helpers
"""

import requests
import os
from typing import Optional

# API configuration
API_HOST = os.getenv("API_HOST", "localhost")
API_PORT = os.getenv("API_PORT", "8000")
API_BASE_URL = f"http://{API_HOST}:{API_PORT}"


def upload_excel(file) -> dict:
    """
    Upload Excel file to trigger ETL pipeline

    Args:
        file: Streamlit UploadedFile object

    Returns:
        Response dictionary from API
    """
    url = f"{API_BASE_URL}/api/ingest"

    files = {"file": (file.name, file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}

    try:
        response = requests.post(url, files=files, timeout=300)  # 5 min timeout for ETL
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"status": "error", "message": str(e)}


def send_chat_message(user_id: str, message: str) -> dict:
    """
    Send chat message to bot

    Args:
        user_id: User identifier
        message: User's message

    Returns:
        Response dictionary from API
    """
    url = f"{API_BASE_URL}/api/chat"

    payload = {
        "user_id": user_id,
        "message": message
    }

    try:
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"response": f"Error: {str(e)}", "intent": None, "sources": None}


def clear_chat_history(user_id: str) -> dict:
    """
    Clear conversation history for a user

    Args:
        user_id: User identifier

    Returns:
        Response dictionary from API
    """
    url = f"{API_BASE_URL}/api/chat/{user_id}/history"

    try:
        response = requests.delete(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"status": "error", "message": str(e)}


def get_preferences(user_id: str) -> dict:
    """
    Get user preferences

    Args:
        user_id: User identifier

    Returns:
        Dictionary of preferences
    """
    url = f"{API_BASE_URL}/api/chat/{user_id}/preferences"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"preferences": {}}


def check_api_health() -> bool:
    """
    Check if API is running

    Returns:
        True if API is healthy, False otherwise
    """
    url = f"{API_BASE_URL}/api/health"

    try:
        response = requests.get(url, timeout=5)
        return response.status_code == 200
    except:
        return False
