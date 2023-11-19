import autogen
import os
from autogen.agentchat.contrib.retrieve_assistant_agent import RetrieveAssistantAgent
from autogen.agentchat.contrib.retrieve_user_proxy_agent import RetrieveUserProxyAgent
import chromadb
from logparser.Drain import LogParser
import pandas as pd

def get_log_data(log_file_path, input_file, output_file):

    log_format = '<Month> <Day> <Time> <Hostname> <Process>:<Content>'  # Define log format to split message fields
    # Regular expression list for optional preprocessing (default: [])
    regex = [
        r'(/|)([0-9]+\.){3}[0-9]+(:[0-9]+|)(:|)'  # IP
    ]
    st = 0.5  # Similarity threshold
    depth = 5  # Depth of all leaf nodes

    parser = LogParser(log_format, indir=log_file_path, outdir=log_file_path, depth=depth, st=st, rex=regex)
    parsed_data = parser.parse(input_file)


    # Read the CSV file
    df = pd.read_csv(log_file_path + '/' + input_file +'_templates.csv')

    # Filter the lines where the event template contains the words "error" or "invalid"
    filtered_df = df[df['EventTemplate'].str.contains('error|invalid', case=False, na=False)]


    # Save the filtered lines as a CSV file
    filtered_df.to_csv(log_file_path + '/' + output_file, index=False)
    
get_log_data(os.path.dirname(__file__), 'test_log1.txt', 'test_log1_filtered.csv')

config_list = autogen.config_list_from_json(
    env_or_file="OAI_CONFIG_LIST_QA",
    file_location = os.path.dirname(__file__),
    filter_dict={
        "model": {
            "gpt-4",
            "gpt4",
            "gpt-4-32k",
            "gpt-4-32k-0314",
            "gpt-35-turbo",
            "gpt-3.5-turbo",
        }
    },
)

assert len(config_list) > 0
print("models to use: ", [config_list[i]["model"] for i in range(len(config_list))])

# Accepted file formats for that can be stored in 
# a vector database instance
from autogen.retrieve_utils import TEXT_FORMATS

print("Accepted file formats for `docs_path`:")
print(TEXT_FORMATS)

# 2. create the RetrieveUserProxyAgent instance named "ragproxyagent"
# By default, the human_input_mode is "ALWAYS", which means the agent will ask for human input at every step. We set it to "NEVER" here.
# `docs_path` is the path to the docs directory. It can also be the path to a single file, or the url to a single file. By default,
# it is set to None, which works only if the collection is already created.
# `task` indicates the kind of task we're working on. In this example, it's a `code` task.
# `chunk_token_size` is the chunk token size for the retrieve chat. By default, it is set to `max_tokens * 0.6`, here we set it to 2000.

log_filtered_path = os.path.join(os.path.dirname(__file__), 'test_log1_filtered.csv')
log_structured_path = os.path.join(os.path.dirname(__file__), 'test_log1.txt_structured.csv')
log_templates_path = os.path.join(os.path.dirname(__file__), 'test_log1.txt_templates.csv')

ragproxyagent = RetrieveUserProxyAgent(
    name="ragproxyagent",
    human_input_mode="TERMINATE",
    max_consecutive_auto_reply=6,
    retrieve_config={
        "task": "code",
        "docs_path": [
            # "https://raw.githubusercontent.com/microsoft/FLAML/main/website/docs/Examples/Integrate%20-%20Spark.md",
            # "https://raw.githubusercontent.com/microsoft/FLAML/main/website/docs/Research.md",
            # "./test_log1.txt"
            log_filtered_path,
            log_structured_path,
            # log_templates_path
        ],
        "collection_name" : "log",
        "chunk_token_size": 2000,
        "model": config_list[0]["model"],
        "client": chromadb.PersistentClient(path="/tmp/chromadb"),
        "embedding_model": "all-mpnet-base-v2",
        "get_or_create": True,  # set to False if you don't want to reuse an existing collection, but you'll need to remove the collection manually
    },
)

assistant_summarizer = RetrieveAssistantAgent(
    name="assistant_summarizer",
    system_message="You are a helpful assistant. Do not generate any code.",
    llm_config={
        "timeout": 600,
        "cache_seed": 42,
        "config_list": config_list,
    },
)

assistant_analyst = RetrieveAssistantAgent(
    name="assistant_analyst",
    system_message="You are a helpful assistant for analysis. You will receive a summary of the log file and then answer questions about it. Do not generate any code.",
    llm_config={
        "timeout": 600,
        "cache_seed": 42,
        "config_list": config_list,
    },
)

# reset the assistant. Always reset the assistant before starting a new conversation.
assistant_summarizer.reset()
assistant_analyst.reset()

assistant_summarizer.max_consecutive_auto_reply = 10  # set the maximum number of consecutive auto rep
summary_problem = "Summarize the general and concise summary of the given log file under 500 words, mainly focused on all different kinds of unusual ssh actions, such as invalid users and so on. This summarization will be used by experts for debugging, so please make sure it is accurate and do not need to explain simple definitions."
# qa_problem = "Is there any unautorized ssh login try?"
# qa_problem = "Is there any ssh key generation steps in the log file?"
ragproxyagent.initiate_chat(assistant_summarizer, problem=summary_problem)

# summary = assistant_summarizer.last_message()['content']

qa_problem = "Is there any unautorized ssh login try?"

ragproxyagent.initiate_chat(assistant_analyst, problem=qa_problem)