#!/usr/bin/env python3
"""
Test script for the enhanced browser agent API.
Tests the strict JSON input/output format.
"""

import requests
import json
import sys

def test_enhanced_agent():
    """Test the enhanced browser agent API endpoint."""
    base_url = "http://localhost:5000"
    
    # Test 1: Health check
    print("=" * 60)
    print("Test 1: Health Check")
    print("=" * 60)
    try:
        response = requests.get(f"{base_url}/api/v1/browser-agent/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        print()
    except Exception as e:
        print(f"Health check failed: {e}")
        print("Make sure the Flask server is running!")
        sys.exit(1)
    
    # Test 2: Execute task with URL
    print("=" * 60)
    print("Test 2: Execute Task with URL")
    print("=" * 60)
    payload = {
        "query": "Open https://www.google.com",
        "agent_id": "test_agent_001"
    }
    
    try:
        print(f"Request: {json.dumps(payload, indent=2)}")
        response = requests.post(
            f"{base_url}/api/v1/browser-agent/execute",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
        print()
        
        # Validate response structure
        assert "success" in result
        assert "data" in result
        assert "agent_id" in result["data"]
        assert "overall_success" in result["data"]
        assert "query" in result["data"]
        assert "steps" in result["data"]
        print("✓ Response structure is valid")
        print()
    except Exception as e:
        print(f"Test 2 failed: {e}")
        print()
    
    # Test 3: Execute task with search query
    print("=" * 60)
    print("Test 3: Execute Task with Search Query")
    print("=" * 60)
    payload = {
        "query": "Search for artificial intelligence",
        "agent_id": "test_agent_002"
    }
    
    try:
        print(f"Request: {json.dumps(payload, indent=2)}")
        response = requests.post(
            f"{base_url}/api/v1/browser-agent/execute",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
        print()
        
        # Validate response structure
        assert "success" in result
        assert "data" in result
        assert "steps" in result["data"]
        print("✓ Response structure is valid")
        print()
    except Exception as e:
        print(f"Test 3 failed: {e}")
        print()
    
    # Test 4: Execute task without agent_id
    print("=" * 60)
    print("Test 4: Execute Task without agent_id")
    print("=" * 60)
    payload = {
        "query": "Open GitHub"
    }
    
    try:
        print(f"Request: {json.dumps(payload, indent=2)}")
        response = requests.post(
            f"{base_url}/api/v1/browser-agent/execute",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
        print()
        
        # Validate response structure
        assert "success" in result
        assert "data" in result
        assert "agent_id" in result["data"]
        print("✓ Response structure is valid (agent_id auto-generated)")
        print()
    except Exception as e:
        print(f"Test 4 failed: {e}")
        print()
    
    print("=" * 60)
    print("All tests completed!")
    print("=" * 60)

if __name__ == "__main__":
    test_enhanced_agent()

