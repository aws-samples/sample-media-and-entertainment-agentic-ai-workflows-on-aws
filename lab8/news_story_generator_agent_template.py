from strands import Agent, tool
from strands_tools import retrieve
from strands.models import BedrockModel
from bedrock_agentcore.runtime import BedrockAgentCoreApp

import logging
import boto3
import time
import argparse
import json
import re

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

s3_client = boto3.client('s3', region)
bedrock_client = boto3.client('bedrock-runtime', region)
bedrock_agent_runtime_client = boto3.client("bedrock-agent-runtime", region)

def extract_entities(news_facts: str) -> str:
    """
    Extract entities (people, organizations, products) from news facts.
    
    Args:
        news_facts: The news facts to extract entities from
        
    Returns:
        Extracted entities in markdown format
    """

    # Create a BedrockModel with specific configuration
    entity_extraction_model = BedrockModel(
        model_id="us.amazon.nova-lite-v1:0",
        region_name=region,
        temperature=1.0,
        max_tokens=2048
    )
    
    extract_agent = Agent(
        model=entity_extraction_model,
        system_prompt="""Your primary function is to extract entities (specifically people, companies/organizations, and products) from news facts collected by a journalist at a news event and output them in consistent markdown format. You must identify all relevant entities while maintaining context about their relationships and relevance. Your output will be used to determine if the entities exist or are fabricated. It is important that your output is in markdown format only.

Input Processing:
1. Accept text input of any length from journalists
2. Process all forms of journalistic content: news articles, interview transcripts, press releases, notes, etc.
3. Maintain the original text for reference and context

Entity Recognition Methodology:
1. Extract full names of people (first, middle, last) where available
2. Extract complete company/organization names, including legal designations (Inc., LLC, etc.)
3. Recognize and extract aliases, nicknames, and abbreviated forms of entities
4. Identify entities even when they appear in different linguistic forms (e.g., possessive, plural)
5. Consider contextual information to accurately identify entities (titles, roles, locations)

Entity Classification:
Categorize each entity as either:
PERSON: Individual human beings
ORGANIZATION: Companies, corporations, agencies, institutions, etc.
PRODUCT: products, items, goods, etc.

Assign specific sub-classifications when possible:
For PERSON: Political figure, executive, celebrity, expert, etc.
For ORGANIZATION: Corporation, government agency, non-profit, educational institution, etc.
For PRODUCT: type, industry

Contextual Information Extraction:
For each entity, extract and preserve:
1. Contextual role/title (CEO, President, Senator, etc.)
2. Associated organizations (for people)

Confidence Scoring:
Assign a confidence score (0.0-1.0).

Limitations and Boundaries
1. Do not attempt to verify entities' existence (this is for the downstream agent)
2. Do not add information about entities not present in the input text
3. Do not make assumptions about entities beyond what is explicitly or implicitly stated
4. Focus only on people and organizations; ignore other entity types

Output Format
Structure output in two sections in consistent markdown format. The first section will be titled "Entities" and it will be a list of the entities that you have identified. Each entity should only have the following attributes:
entity_id: unique identifier
text: extracted text of the entity
type: PERSON or ORGANIZATION or PRODUCT
subtype: specific classification
confidence: confidence score

The second section will be titled "New Facts" and will be followed by the original news facts.

Do not add preambles to your answer. Make sure your answer is in markdown format."""
    )
    
    # Extract entities using the agent
    result = extract_agent(news_facts)
    return result.message

def create_research_query(entities: str) -> str:
    """
    Create a research query for the entities extracted from news facts.
    
    Args:
        entities: The extracted entities in markdown format
        
    Returns:
        A research query for the knowledge base
    """

    # Create a BedrockModel with specific configuration
    research_query_generation_model = BedrockModel(
        model_id="us.amazon.nova-micro-v1:0",
        region_name=region,
        temperature=0.0,
        top_p=1.0,
        max_tokens=4096
    )
    
    research_query_agent = Agent(
        model=research_query_generation_model,
        system_prompt="""You have been provided a list of entities and news facts about a news event. Create a query for an LLM that asks to find research material on the entities indentified in the news facts.

Skip the preamble, your output should only include the query and nothing else.

Your response must start with:
"Conduct indepth research about only the list of entities under the 'Entities' heading provided in markdown format at the end of this input. Find as much relevant research material of a commercial, personal, financial nature as possible. Focus on all types of information which can help in writing a news article about the entities. Only add information if it is in the knowledge base. If an entity isn't found in your knowledge base, discard it from the output."

To the start, add the following regarding output format:
"Output Format
Structure output in two headings in consistent markdown format. The first heading will be titled "Researched Entities" and it will be a list of only those entities for which you found research information. Each entity should only have the following attributes:
entity_id: unique identifier
text: extracted text of the entity
type: PERSON or ORGANIZATION or PRODUCT
subtype: specific classification
confidence: confidence score
research: 
 - research item 1
 - research item 2
 - more research items

The second heading will be titled "New Facts" and will be followed by the original "News Facts" that were given to you.

Make sure to include proper line breaks by:
1. Using a blank line between paragraphs
2. Adding two spaces at the end of lines where you want a soft line break
3. Using proper markdown syntax for lists, headings, and other elements that require specific line formatting."

Your output must be limited to the query that you've constructed for the LLM and nothing more. Do not add any preamble."""
    )
    
    # Create research query using the agent
    result = research_query_agent(entities)
    return result.message

@tool(name="researchAgent")
def research_agent(news_facts: str) -> str:
    """
    Research agent that extracts entities from news facts and gathers background information.
    
    Use this tool when you need to gather comprehensive research about people, organizations, 
    and products mentioned in news facts. This tool will extract entities, create optimized
    research queries, and retrieve information from knowledge bases to provide context for
    article generation.
    
    Args:
        news_facts: The news facts to research (raw text from journalist notes)
        
    Returns:
        Structured research information about entities mentioned in the news facts
    """
    print("Research agent processing...")
    
    # Get region and account info for KB access
    session = boto3.session.Session()
    region = session.region_name
    account_id = sts_client.get_caller_identity()["Account"]
    print("STEP 1: EXTRACT ENTITIES")
    extract_entities_response = extract_entities(news_facts)
    entities = extract_entities_response['content'][0]['text']
    # print(entities)
    print("\n\nSTEP 2: CREATE RESEARCH QUERIES")
    create_research_query_response = create_research_query(entities)
    research_query = create_research_query_response['content'][0]['text']
    # print(research_query)
    research_results_response = bedrock_agent_runtime_client.retrieve_and_generate(
        input={ 'text': research_query },
        retrieveAndGenerateConfiguration={
            'knowledgeBaseConfiguration': {
                'knowledgeBaseId': "{{lab7_kb_id}}",
                'modelArn': f"arn:aws:bedrock:us-east-1:{account_id}:inference-profile/us.amazon.nova-micro-v1:0",
                'retrievalConfiguration': {
                    'vectorSearchConfiguration': {
                        'numberOfResults': 5,
                        'overrideSearchType': 'HYBRID'
                    }
                }
            },
            'type': 'KNOWLEDGE_BASE'
        }
    )
    print("\n\nSTEP 3: RETRIEVE AND GENERATE")
    research_results = research_results_response['output']['text']
    print(research_results)
    response = f"<research_results>{research_results}</research_results>"
    return response

@tool(name="articleWritingAgent")
def article_generation_agent(query: str) -> str:
    """
    Generates a professional news article based on research data and facts.
    
    Use this tool when you need to write a news article based on research data, or when revising an article
    to incorporate feedback from a reviewer.
    
    Args:
        query: The research data, facts, and any feedback for article generation.
        
    Returns:
        A professionally written news article.
    """
    print("Article Generation agent processing...")

    # Create a BedrockModel with specific configuration
    article_generation_model = BedrockModel(
        # model_id="us.anthropic.claude-3-5-haiku-20241022-v1:0",
        model_id="us.amazon.nova-pro-v1:0",
        region_name=region,
        temperature=0.5,
        top_k=1.0,
        top_p=1.0,
        max_tokens=4096
    )
    
    article_writer = Agent(
        model=article_generation_model,
        system_prompt="""You are an expert article writer creating engaging news, sports, and entertainment content tailored to audiences and publication requirements.

## Agent Role
You are an expert journalist who transforms raw news facts and related research material into compelling, professionally written news articles. Your articles must be accurate, engaging, and adhere to high journalistic standards.

## Input Processing
1. Carefully analyze all news facts provided about the event
2. Review all contextual research about entities mentioned in the news facts
3. Identify key information, connections, and the most newsworthy elements
4. Organize information in order of importance (inverted pyramid style)

## Article Creation Guidelines
1. Create a concise, attention-grabbing headline that accurately represents the story
2. Write approximately 800 words (adjust if specifically requested otherwise)
3. Begin with a strong lead paragraph that answers the key questions (who, what, when, where, why, how)
4. Structure the article with the most important information first, followed by supporting details
5. Incorporate relevant context from the research materials where appropriate
6. Use direct quotes from sources when available
7. Maintain a neutral, objective tone throughout
8. Ensure factual accuracy - only use information provided in the input materials
9. Avoid speculation, personal opinions, or unsupported claims
10. Use concise, clear language accessible to general readers
11. Break up text with appropriate paragraphs for readability
12. Include a conclusion that ties the story together or points to future developments

## Feedback Integration
1. When receiving feedback from review agents, analyze it thoroughly
2. Make all requested changes that align with journalistic standards
3. Revise for clarity, accuracy, balance, or completeness as directed
4. If feedback contains contradictory requests, prioritize factual accuracy and journalistic ethics
5. Return the revised article with all improvements implemented

## Output Format
The output should consist of only:
1. A headline
2. The article body

Do not include:
- Tags like "Headline:" or "Article:"
- Explanations about your writing process
- Notes about sources or research
- Additional formatting markers
- Thoughts or reflections on the article
- Metadata or structural elements

## Example Output Structure:
Major Discovery Transforms Scientific Understanding

Scientists at Stanford University have announced a breakthrough discovery that challenges existing theories...

[Article continues for approximately 200 words]""",
        tools=[], 
        callback_handler=None
    )
    response = str(article_writer(query))
    formatted_response = f"<article>{response}</article>"               
    return formatted_response

@tool(name="articleReviewerAgent")
def article_reviewer_agent(article_text: str) -> str:
    """
    Reviews and provides detailed feedback on news, sports, and entertainment articles.
    
    Use this tool when you need professional feedback on an article's clarity, accuracy,
    engagement, balance, and overall journalistic quality.
    
    Args:
        article_text: The complete article text to be reviewed
        
    Returns:
        Detailed review feedback with specific suggestions for improvement
    """
    print("Article Reviewer agent analyzing...")
    
    # Create a BedrockModel with specific configuration
    article_reviewer_model = BedrockModel(
        model_id="us.amazon.nova-micro-v1:0",
        region_name=region,
        temperature=0.1,
        top_k=1.0,
        top_p=1.0,
        max_tokens=4096
    )

    article_reviewer = Agent(
        model=article_reviewer_model,
        system_prompt="""You are a professional article reviewer for news, sports and entertainment. Provides expert analysis to improve clarity, accuracy, engagement and journalistic quality.

You are an AI assistant specialized in reviewing news, sports, and entertainment articles. Your expertise helps journalists and content creators refine their writing for clarity, engagement, and journalistic quality.

You will be provided an article in your input, when reviewing an article, analyze these key elements:

1. **Clarity and Readability**
   - Identify sentences longer than 40 words or spanning multiple lines
   - Flag sentences requiring multiple readings to understand
   - Point out repetitive word usage that weakens impact
   - Suggest ways to make complex information more digestible
   - Analyze paragraph length and structure for optimal readability
   - Check for smooth transitions between ideas and sections

2. **Accuracy and Substantiation**
   - Check for claims that lack proper sourcing or evidence
   - Identify potential factual inconsistencies or errors
   - Flag misleading statistics or improper contextualization of data
   - Suggest where additional verification or expert input might be needed
   - Evaluate the reliability and diversity of cited sources
   - Check dates, names, titles, and other factual details for accuracy


For each issue identified, provide:
- A clear explanation of why it weakens the article
- A specific suggestion for improvement
- Where helpful, a rewritten example demonstrating your suggestion
- A priority level (critical, important, or minor) for each feedback item

Conclude your review with:
- A summary of the article's major strengths
- The 3-5 most important areas for improvement
- An overall assessment of the article's effectiveness

Your feedback should be constructive and actionable, focusing on strengthening the article's journalistic quality and reader experience rather than simply pointing out flaws.""",
        tools=[],
        callback_handler=None,
    )
    response = str(article_reviewer(article_text))
    formatted_response = f"<review_feedback>{response}</review_feedback>"
    return formatted_response


@app.entrypoint
def interface_supervisor_agent(payload, context=None):
    """
    Orchestrates a complete news article generation workflow using specialized agents.
    
    This tool coordinates between research, article generation, and review agents to produce
    high-quality news articles from raw facts. It manages the entire workflow including:

    1. Research on entities mentioned in the news facts
    2. Article generation based on research and facts
    3. Article review and improvement through feedback
    
    Args:
        news_facts: Raw news facts collected by a journalist
        
    Returns:
        A professionally written and reviewed news article
    """
    print("Interface Supervisor agent processing...")
    if context:
        print("Runtime Session ID:", context.session_id)
    news_facts = payload["query"]

    # Create a BedrockModel with specific configuration
    interface_supervisor_model = BedrockModel(
        # model_id="us.amazon.nova-pro-v1:0",
        model_id="us.anthropic.claude-3-5-haiku-20241022-v1:0",
        region_name=region,
        temperature=0.1,
        top_k=1.0,
        top_p=1.0,
        max_tokens=4096
    )
    
    # Create the interface supervisor agent
    interface_supervisor = Agent(
        model=interface_supervisor_model,
        system_prompt="""You are a supervisor agent responsible for orchestrating a news article generation workflow.
Your role is to only coordinate between agents.

Your task is to carry out an article writing workflow that involves the following:

1. You will be provided news facts from a news event about the article to write. Your task is to submit the unmodified facts to the researchAgent. 
The research agent will provide you with additional research about the entities it identified in the news facts. The result from reseachAgent can be found in the <research_results> XML tag.

2. Once the research agent is finished, submit the research information to the articleWritingAgent, which will create an article from the research and news facts. 

3. The article must be reviewed before returning to the user. The content of the article can be found in <article> XML tag. Use the articleReviewerAgent to perform the review.

4. The review feedback can be found in <review_feedback> XML tag. You should perform the article writing and review iteratively until the reviewerAgent is satisfied with the result. 

Finally, you must return only the final article to the user. Do not provide any preemtive or additional explanation, just return the final article to the user.

# Guidelines:
- Do not modify, summarize, or filter the researchAgent agent's output before passing it to the articleWritingAgent agent.
- When working with the articleReviewAgent, always provide the the article generated by the articleWritingAgent as context without any modifications or summarization.
- Do not edit, rewrite, or enhance the articleWritingAgent agent's output before returning it to the user.

You should iterate between the writing (articleWritingAgent) and review (articleReviewAgent) process to come up with best article.

- You must not iterate the writing and review iteration processes more than 1 time. If you reached the maximum iteration, return the latest draft as the final article.
- If any agent returns an error or incomplete output, notify the user with the exact error message.
- Write your final draft in <final> XML tag.
""",
        tools=[research_agent, article_generation_agent, article_reviewer_agent]
    )

    return interface_supervisor(news_facts)

if __name__ == "__main__":
    app.run()