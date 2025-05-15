import logging
from typing import Dict, Any
from http import HTTPStatus
import json
logger = logging.getLogger()
logger.setLevel(logging.INFO)
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
    """
    AWS Lambda handler for processing Bedrock agent requests.
    
    Args:
        event (Dict[str, Any]): The Lambda event containing action details
        context (Any): The Lambda context object
    
    Returns:
        Dict[str, Any]: Response containing the action execution results
    
    Raises:
        KeyError: If required fields are missing from the event
    """
    try:
        action_group = event['actionGroup']
        function = event['function']
        message_version = event.get('messageVersion',1)
        parameters = event.get('parameters', [])
        # Execute your business logic here. For more information, 
        # refer to: https://docs.aws.amazon.com/bedrock/latest/userguide/agents-lambda.html
        logger.info('Action group: %s', action_group)
        logger.info('Function: %s', function)
        logger.info('Message version: %s', message_version)
        logger.info('Parameters: %s', parameters)
        rating = _get_title_rating(parameters[0]['value'])
        # Log the title
        response_body = {
            'TEXT': {
                'body': f'The function {function} was called successfully, ratings are {rating}!'
            }
        }
        action_response = {
            'actionGroup': action_group,
            'function': function,
            'functionResponse': {
                'responseBody': response_body
            }
        }
        response = {
            'response': action_response,
            'messageVersion': message_version
        }
        logger.info('Response: %s', response)
        return response
    except KeyError as e:
        logger.error('Missing required field: %s', str(e))
        return {
            'statusCode': HTTPStatus.BAD_REQUEST,
            'body': f'Error: {str(e)}'
        }
    except Exception as e:
        logger.error('Unexpected error: %s', str(e))
        return {
            'statusCode': HTTPStatus.INTERNAL_SERVER_ERROR,
            'body': 'Internal server error'
        }