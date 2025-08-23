import logging
from typing import Dict, Any
from http import HTTPStatus
import json
import os
import boto3
logger = logging.getLogger()
logger.setLevel(logging.INFO)

kb_id = os.environ.get("KB_ID")

bedrock_agent_runtime_client = boto3.client(
    'bedrock-agent-runtime')

ratings = {
    "aws123123": "6.25",
    "aws234234": "7.52",
    "aws234567": "8.61",
    "aws234890": "7.51",
    "aws567234": "8.46",
    "aws567567": "7.91",
    "aws567890": "8.91",
    "aws890234": "9.58",
    "aws890567": "7.96",
    "aws890890": "8.75",
    "aws345345": "7.48",
    "aws123456": "6.91",
    "aws345678": "7.28",
    "aws345901": "8.49",
    "aws456456": "9.05",
    "aws456789": "7.98",
    "aws456012": "8.54",
    "aws456123": "7.50",
    "aws123789": "6.58",
    "aws456123": "6.98",
    "aws456456": "7.54",
    "aws456789": "8.29",
    "aws789123": "7.86",
    "aws789456": "9.01",
    "aws789789": "9.08"
}

def title_search(query):
    try:
        response = bedrock_agent_runtime_client.retrieve(
            knowledgeBaseId=kb_id,
            retrievalQuery={
                'text': query
            }
        )

        # Process the retrieved results
        retrieval_results = response['retrievalResults']
        contents = []
        for result in retrieval_results:
            content = result['content']['text']
            contents.append(content)
            print(f"Content: {content}\n")
        return contents
    
    except Exception as e:
        print(f"Error retrieving from Knowledge Base: {e}")

def _get_title_rating(title_id: str) -> Dict[str, Any]:
    """
    Retrieves the title rating for a given IMDb ID.
    Args:
        title_id (str): The ID of the title
    Returns:
        Dict[str, Any]: A dictionary containing the title rating information
    """
    if title_id not in ratings:
        return {"not available"}
    else:
        data = {
            "title_id": title_id,
            "rating": ratings[title_id]
        }
    return data
    
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """AWS Lambda handler serves as tooling support for media assistant
    
    Args:
        event (dict): The Lambda event object containing title ID
                      Expected format: {
                          "title_id": "12345"
                      }
                      or query about specific title or genres
        
        context (dict): AWS Lambda context object

    Returns:
        dict: tool results
    """
    
    toolName = context.client_context.custom['bedrockAgentCoreToolName']
    print(context.client_context)
    print(event)
    print(f"Original toolName: , {toolName}")
    delimiter = "___"
    if delimiter in toolName:
        toolName = toolName[toolName.index(delimiter) + len(delimiter):]
    print(f"Converted toolName: , {toolName}")

    if toolName == 'get_title_rating':
        title_id = event.get('title_id')
        response = _get_title_rating(title_id)
        # Log the title
        logger.info('Response: %s', response)
        return response
    if toolName == "get_show_detail":
        query = event.get("query")
        response = title_search(query)
        return response