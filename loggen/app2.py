import streamlit as st
import asyncio
from autogen import AssistantAgent, UserProxyAgent
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

class TrackableAssistantAgent(RetrieveAssistantAgent):
    def _process_received_message(self, message, sender, silent):
        # with st.chat_message(sender.name):
        #     st.markdown(message)
        return super()._process_received_message(message, sender, silent)


class TrackableUserProxyAgent(RetrieveUserProxyAgent):
    def _process_received_message(self, message, sender, silent):
        if not message == "UPDATE CONTEXT":
            with st.chat_message(sender.name):
                st.markdown(message)
        return super()._process_received_message(message, sender, silent)


st.write("""# AutoGen Chat Agents""")

get_log_data(os.path.dirname(__file__), 'test_log1_short.txt', 'test_log1_short_filtered.csv')

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

log_filtered_path = os.path.join(os.path.dirname(__file__), 'test_log1_short_filtered.csv')
log_structured_path = os.path.join(os.path.dirname(__file__), 'test_log1_short.txt_structured.csv')
log_templates_path = os.path.join(os.path.dirname(__file__), 'test_log1_short.txt_templates.csv')

ragproxyagent = TrackableUserProxyAgent(
    name="ragproxyagent",
    human_input_mode="TERMINATE",
    max_consecutive_auto_reply=6,
    retrieve_config={
        "task": "code",
        "docs_path": [
            # "https://raw.githubusercontent.com/microsoft/FLAML/main/website/docs/Examples/Integrate%20-%20Spark.md",
            # "https://raw.githubusercontent.com/microsoft/FLAML/main/website/docs/Research.md",
            # "./test_log1_short.txt"
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

summarizer = TrackableAssistantAgent(
    name="summarizer",
    system_message="You are a helpful assistant. Do not generate any code.",
    llm_config={
        "timeout": 600,
        "cache_seed": 42,
        "config_list": config_list,
    },
)

analyst = TrackableAssistantAgent(
    name="analyst",
    system_message="You are a helpful assistant for analysis. You will receive a summary of the log file and then answer questions about it. Do not generate any code.",
    llm_config={
        "timeout": 600,
        "cache_seed": 42,
        "config_list": config_list,
    },
)

# reset the assistant. Always reset the assistant before starting a new conversation.
summarizer.reset()
analyst.reset()

summarizer.max_consecutive_auto_reply = 10  # set the maximum number of consecutive auto rep


with st.sidebar:
    st.header("OpenAI Configuration")

with st.container():
    # for message in st.session_state["messages"]:
    #    st.markdown(message)

    user_input = st.chat_input("Type something...")
    
    if user_input:
        with st.chat_message('ragproxyagent'):
            st.markdown(user_input)
        
        # Create an event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        print("--------------------------------------initiating chat with summarizer before loop--------------------------------------")

        # Define an asynchronous function
        async def initiate_chat_summarizer():
            print("--------------------------------------initiating chat with summarizer in the loop--------------------------------------")
            await ragproxyagent.a_initiate_chat(
                summarizer,
                problem=user_input,
                # clear_history=False
            )
            print("--------------------------------------after chat with summarizer in loop--------------------------------------")

        # Run the asynchronous function within the event loop
        loop.run_until_complete(initiate_chat_summarizer())

        print("--------------------------------------initiating chat with analyst before loop--------------------------------------")

        # Define an asynchronous function
        async def initiate_chat_analyst():
            print("--------------------------------------initiating chat with analyst in the loop--------------------------------------")
            await ragproxyagent.a_initiate_chat(
                analyst,
                problem=user_input,
                # clear_history=False
            )
            print("--------------------------------------after chat with analyst in the loop--------------------------------------")

        # Run the asynchronous function within the event loop
        loop.run_until_complete(initiate_chat_analyst())
        print("--------------------------------------END--------------------------------------")
