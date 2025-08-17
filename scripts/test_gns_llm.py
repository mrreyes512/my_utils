#!/usr/bin/env python3

"""
Simple test script to verify GNS_LLM connectivity
"""

import os
from dotenv import load_dotenv
from utils.gns_llm import GNS_LLM

# Load environment variables
load_dotenv()

def test_gns_llm():
    """Test basic GNS_LLM functionality"""
    try:
        print("Testing GNS_LLM connectivity...")
        
        # Get environment variables
        environment_url = os.getenv('AI_COE_ENV_URL')
        project_name = os.getenv('AI_COE_PROJECT_NAME')
        api_key = os.getenv('AI_COE_TOKEN')
        model = os.getenv('AI_COE_ENGINE', 'ai-coe-gpt4-auto:analyze')
        
        print(f"Environment URL: {environment_url}")
        print(f"Project Name: {project_name}")
        print(f"API Key: {api_key[:10]}..." if api_key else "None")
        print(f"Model: {model}")
        
        # Initialize LLM
        llm = GNS_LLM(
            environment_url=environment_url,
            projectname=project_name,
            api_key=api_key
        )
        
        # Simple test question
        response = llm.ask_question("Say hello", model=model)
        print(f"Response: {response}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_gns_llm()
