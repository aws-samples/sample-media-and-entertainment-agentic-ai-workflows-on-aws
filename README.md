# Agentic AI for Media and Entertainment

** WORK IN PROGRESS **
This repository is under construction. When the all the official changes are committed, we'll remove this notification accordingly


Welcome to the Agentic AI for Media and Entertainment workshop. The goal of this workshop is provide hands on experience of building applications using various AI patterns to effectively solve complex problems using Agents. 

The main audience for this workshop are developers, solution builders. This workshop introduces agents and workflows from the practical point view. The labs are designed to guide you through agent building processes step by step, from simple workflows like prompt chaining, to the most advanced patterns such as multi agent collaborations. 

The agents in this workshop is built using [Amazon Bedrock Agent](https://docs.aws.amazon.com/bedrock/latest/userguide/agents.html), and [Bedrock Flows](https://docs.aws.amazon.com/bedrock/latest/userguide/flows.html) and [Amazon Q Business](https://aws.amazon.com/q/business/)

Within this series of labs, you'll explore some of the common use cases focused in media and entertainment. You'll learn how to implement agent patterns to build powerful systems that automate repeatable tasks, significantly improving productivity and efficiency across media workflows. These hands-on exercises will demonstrate how AI-powered agents can streamline content creation, metadata management, and other industry-specific processes.

Labs in the workshop include:

- 01 - Amazon Q Business Action [Estimated time to complete - 45 mins] 
- 02 - Prompt Chaining [Estimated time to complete - 45 mins]
- 03 - Prompt Routing [Estimated time to complete - 30 mins]
- 04 - Prompt Parallelization [Estimated time to complete - 44 mins]
- 05 - Reflection [Estimated time to complete - 60 mins]
- 06 - Tool Use [Estimated time to complete - 45 mins]
- 07 - Multi Agent Collaboration [Estimated time to complete - 60 mins]

## Getting Started
Depending on the lab, this workshop is run using AWS Console and Python notebooks. For python notebooks, you can run from the environment of your choice. For labs that runs in AWS Console, navigate to the appropriate AWS Account and start the labs by following the instructions.

For a fully-managed environment with rich AI/ML features, we'd recommend using SageMaker AI Studio. To get started quickly, you can refer to the instructions for domain quick setup.

If you prefer to use your existing (local or other) notebook environment, make sure it has credentials for calling AWS.

Lab 1-4 are run directly in an AWS console. The labs that requires running python notebooks are Lab 5, Lab 6 and Lab 7. 

The following instructions are focused on labs that are running in a python notebook.
To get started, run the following CLI command in your notebook environment.

```bash
git clone https://github.com/aws-samples/sample-media-and-entertainment-agentic-ai-workflows-on-aws.git
cd sample-media-and-entertainment-agentic-ai-workflows-on-aws
```

You're now ready to explore the lab notebooks! Start with [00-start-here.ipynb](00-start-here.ipynb).

## Security
See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License
See [LICENSE](LICENSE)

## Contributing
See [CONTRIBUTING](CONTRIBUTING.md)

