from strands import Agent
import argparse
import json
import logging
import boto3
import os
from mcp.client.streamable_http import streamablehttp_client 
from strands.tools.mcp.mcp_client import MCPClient
from bedrock_agentcore.runtime import BedrockAgentCoreApp


app = BedrockAgentCoreApp()

# Configure the root strands logger
logging.getLogger("strands").setLevel(logging.INFO)

# Add a handler to see the logs
logging.basicConfig(
    format="%(levelname)s | %(name)s | %(message)s", 
    handlers=[logging.StreamHandler()])


sts_client = boto3.client('sts')
session = boto3.session.Session()

account_id = sts_client.get_caller_identity()["Account"]
region = session.region_name
ssm_client = boto3.client('ssm')

os.environ["AWS_REGION"] = region

def get_secrets() -> dict:
        secrets_client = boto3.client('secretsmanager', region_name=region)
        response = secrets_client.get_secret_value(SecretId='mcp_server/cognito/credentials')
        secret_value = response['SecretString']
        parsed_secret = json.loads(secret_value)
        return parsed_secret

def get_gateway_url() -> str:
    gateway_url_response = ssm_client.get_parameter(Name='/mcp_server/gateway/gateway_url')
    gateway_url = gateway_url_response['Parameter']['Value']
    return gateway_url

agent = None
lambda_mcp_client = None

@app.entrypoint
def invoke_agent(payload, context=None):
    global agent
    global lambda_mcp_client
    
    prompt = payload.get("query")
    if not agent:
        secrets = get_secrets()
        bearer_access_token = secrets['bearer_access_token']
        gateway_url = get_gateway_url()

        def create_streamable_http_transport():
            return streamablehttp_client(gateway_url,headers={"Authorization": f"Bearer {bearer_access_token}"})

        lambda_mcp_client = MCPClient(create_streamable_http_transport)

        with lambda_mcp_client:
            # Get the tools from the MCP server
            tools = lambda_mcp_client.list_tools_sync()
            agent = Agent(model="us.amazon.nova-premier-v1:0", 
                        tools=tools,
                        system_prompt=f"""You are a professional media agent. Your task is to help users find the information
            related to the media based on the tools available to you.

            You have access to the following tools:
            1. get_show_detail - a tool that contains movie / show information including title, year, duration and genre.
            2. get_title_rating - a rating retrieval tool that provide information about media details, including the title, ratings.

            If you need to retrieve the title ID from the knowledge base, look for the title_id column for the value.
            For example, a retrieved media contains the following data:

            title_id: 123
            title: Some title
            year: 2025
            duration: 100 minutes
            """,
            callback_handler=None)
            return agent(prompt)

    else:
        with lambda_mcp_client:
            # Get the tools from the MCP server
            return agent(prompt)
    

if __name__ == "__main__":
    app.run()