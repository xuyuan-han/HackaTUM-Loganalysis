import autogen
import os
import json
from autogen.retrieve_utils import TEXT_FORMATS
from autogen.agentchat.contrib.retrieve_assistant_agent import RetrieveAssistantAgent
from autogen.agentchat.contrib.retrieve_user_proxy_agent import RetrieveUserProxyAgent
import chromadb

config_list = autogen.config_list_from_json(
    env_or_file="OAI_CONFIG_LIST_QA",
    # make sure the config file is in the same directory as this file
    file_location=os.path.dirname(__file__),
    filter_dict={
        "model": ["gpt-3.5-turbo-16k"],
    },
)

assert len(config_list) > 0
print("models to use: ", [config_list[i]["model"] for i in range(len(config_list))])

# Accepted file formats for that can be stored in 
# a vector database instance

print("Accepted file formats for `docs_path`:")
print(TEXT_FORMATS)

gpt_config = {
    "cache_seed": 42,  # change the cache_seed for different trials
    "temperature": 0,
    "config_list": config_list,
    "timeout": 600,
}

#TODO: change the input context and question
PROMPT_MULTIHOP = """You're a retrieve augmented chatbot. You answer user's questions based on your own knowledge and the context provided by the user. You must think step-by-step.

In today's data-driven world, handling and understanding large log files is a significant challenge. You aim to simplify this process. The goal is to create a solution that can summarize these log files and to interact with the summarized data in a user-friendly way. Furthermore, by linking the answers back to the original log lines, you aim to maintain data credibility. It is an opportunity for you to contribute to a solution that can revolutionize how organizations interact with their log data, leading to more efficient data handling and informed decision-making.

A very usefull feature would be a dynamic summarization that allows for the creation of summaries that adapt to the context and content interacting with the user. Instead of a static summary, the dynamic summarization process continually updates and refines the summary based on new input given by the user.

Dialog with User: You chat in a dialog with the user to better understand their needs and preferences. This interactive process ensures that the final output is tailored to the user’s specific requirements and interests.

Summarize What Fits Best to User Question: You focuses on summarizing information that is most relevant to the user’s query. By prioritizing content that directly addresses the user’s question, you ensure that the summary is concise, relevant, and useful.

Allow to Remove Content for Summary That Users are Not Interested In: you provide users with the option to exclude certain content from the summary. For example, if a user specifies “remove layer rspias-daemon”, you will ignore messages with this context. This feature allows users to customize the summary according to their preferences.

Sequential Summarization: This approach involves adjusting the summary step by step based on user input. As the user provides more information or clarifies their needs, you refine the summary accordingly. This iterative process ensures that the final summary accurately reflects the user’s intent and information needs.

Context:
{input_context}
Question: {input_question}
Answer:
"""

#create the RetrieveUserProxyAgent instance named "ragproxyagent"
current_file_path = os.path.abspath(__file__)
data_dir = os.path.dirname(os.path.dirname(current_file_path))
corpus_file = os.path.join(data_dir, 'data', 'test_log1.txt')

# Create a new collection for NaturalQuestions dataset
ragproxyagent = RetrieveUserProxyAgent(
    name="ragproxyagent",
    human_input_mode="ALWAYS",
    system_message="A human admin. Give log files to summarizer. Ask questions about the log files.",
    max_consecutive_auto_reply=3,
    retrieve_config={
        "task": "qa",
        "docs_path": corpus_file,
        "chunk_token_size": 2000,
        "model": config_list[0]["model"],
        "client": chromadb.PersistentClient(path="/tmp/chromadb"),
        "collection_name": "loganalysis",
        "chunk_mode": "one_line",
        "embedding_model": "all-MiniLM-L6-v2",
        "customized_prompt": PROMPT_MULTIHOP,
        "customized_answer_prefix": "the summary of the log files is",
        "get_or_create": True
    },
)

summarizer = RetrieveAssistantAgent(
    name="summarizer",
    system_message="Summarizer. You parse through the log files, understand the context, and generate a summary of the logs. You also need to adjust the summary based on feedback from the ragproxyagent.",
    llm_config=gpt_config,
)

analyst = RetrieveAssistantAgent(
    name="analyst",
    system_message="Analyst. You analyse the log files, analyse the error in messages. You will perform a QA (Question-Answering) task with the summarized context provided by summarizer or the full log. ragproxyagent will ask questions related to the log files, and you should provide answers.",
    llm_config=gpt_config,
)

# critic = autogen.AssistantAgent(
#     name="Critic",
#     system_message="Critic. Double check plan, claims, code from other agents and provide feedback. Check whether the plan includes adding verifiable info such as source URL.",
#     llm_config=gpt_config,
# )

groupchat = autogen.GroupChat(agents=[ragproxyagent, 
                                      summarizer,
                                      analyst, 
                                      # critic,
                                      ], 
                                      messages=[], 
                                      max_round=50)
manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=gpt_config)

question = "Summerize the log file. And answer the following questions: What is the error in the log file?"

ragproxyagent.reset()
summarizer.reset()
analyst.reset()
# critic.reset()

ragproxyagent.initiate_chat(
    manager,
    problem = question
)