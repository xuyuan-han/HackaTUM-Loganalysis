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

sslist = ["ragproxyagent", "summarizer", "analyst", "init_sum", "init_ana", "chosen_agent","file_path"]
for ss in sslist:
    if ss not in st.session_state:
        st.session_state[ss] = None

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
    df = pd.read_csv( input_file +'_templates.csv')

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
    
    def get_human_input(self, prompt: str) -> str:
        st.info(prompt, icon="ℹ️")
        return super().get_human_input(prompt)

def main():

    st.write("""# Auto LogGen""")
    
    with st.sidebar:
        st.header("OpenAI Configuration")
        uploaded_file = st.file_uploader("Upload a document", type=["txt", "pdf", "docx", "out"])

        if uploaded_file:
            
            st.subheader("Uploaded Document:")
            # Display information about the uploaded file
            st.write("File Name:", uploaded_file.name)
            st.write("File Type:", uploaded_file.type)
            st.write("File Size:", f"{uploaded_file.size / 1024:.2f} KB")
            file_path = os.path.join(os.path.dirname(__file__), "uploaded_file.out")
            
            # Check if the file exists and delete it if it does
            if os.path.exists(file_path):
                os.remove(file_path)
            
            with open(file_path, "wb") as file:
                file.write(uploaded_file.read())
                # get_log_data(os.path.dirname(__file__), file_path, 'test_log1_filtered.csv')
                if file is not None:
                    st.info("File successfully uploaded!")
                else:
                    st.warning("File not uploaded")

    if st.button("First click here to create agents"):
        get_log_data(os.path.dirname(__file__), file_path, 'test_log1_short_filtered.csv')

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

        print("starting agents")
        ragproxyagent = TrackableUserProxyAgent(
            name="ragproxyagent",
            human_input_mode="TERMINATE",
            max_consecutive_auto_reply=15,
            retrieve_config={
                "task": "qa",
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
        print("successfully created agents")

        st.session_state["ragproxyagent"] = ragproxyagent
        st.session_state["summarizer"] = summarizer
        st.session_state["analyst"] = analyst
        st.session_state["init_sum"] = False
        st.session_state["init_ana"] = False
        
        st.info("Agents successfully created!")

    with st.container():
        selected_agent = st.radio("Choose an agent", [ "summarizer", "analyst"])
        print("selected agent: ", selected_agent)

        # for message in st.session_state["messages"]:
        #    st.markdown(message)

        user_input = st.chat_input("Type something...")
        
        if user_input:
            with st.chat_message('ragproxyagent'):
                st.markdown(user_input)
            if selected_agent == "summarizer":
                # ask summarizer
                if st.session_state["init_sum"] == False:
                    reply = st.session_state["ragproxyagent"].initiate_chat(st.session_state["summarizer"],
                        problem=user_input)
                    st.session_state["init_sum"] = True
                else:
                    reply = st.session_state["ragproxyagent"].send(user_input, st.session_state["summarizer"])
            if selected_agent == "analyst":
                # ask analyst
                if st.session_state["init_ana"] == False:
                    reply = st.session_state["ragproxyagent"].initiate_chat(st.session_state["analyst"],
                        problem=user_input)
                    st.session_state["init_ana"] = True
                else:
                    reply = st.session_state["ragproxyagent"].send(user_input, st.session_state["analyst"])

if __name__ == "__main__":
    main()