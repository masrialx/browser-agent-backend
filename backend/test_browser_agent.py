#!/usr/bin/env python3
"""
Quick test script for the Browser Agent API.
Make sure the Flask server is running before executing this script.
"""

import requests
import json
import sys

def test_browser_agent():
    """Test the browser agent API endpoint."""
    base_url = "http://localhost:5000"
    
    # Test health check
    print("Testing health check...")
    try:
        response = requests.get(f"{base_url}/api/v1/browser-agent/health")
        print(f"Health check status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Health check failed: {e}")
        print("Make sure the Flask server is running!")
        sys.exit(1)
    
    # Test browser task execution
    print("\nTesting browser task execution...")
    payload = {
        "query": "Search for AI on Google",
        "agent_id": "test_agent_001",
        "user_id": "test_user_001"
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/v1/browser-agent/execute",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        print(f"Execution status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Execution failed: {e}")

if __name__ == "__main__":
    test_browser_agent()

