import logging
import os
 
from autogen import config_list_from_json
from autogen.agentchat.contrib.gpt_assistant_agent import GPTAssistantAgent
from autogen import UserProxyAgent

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

assistant_id = os.environ.get("ASSISTANT_ID", None)

config_list = config_list_from_json(
    env_or_file="OAI_CONFIG_LIST_QA",
    # make sure the config file is in the same directory as this file
    file_location=os.path.dirname(__file__),
    filter_dict={
        "model": ["gpt-3.5-turbo-16k"],
    },
)

llm_config = {
    "config_list": config_list,
    "assistant_id": assistant_id,
    "tools": [
            {
                "type": "retrieval"
            }
        ],
    "file_ids": ["file-CmlT0YKLB3ZCdHmslF9FOv69"]  
    # add id of an existing file our openai account
    # in this case I added the implementation of conversable_agent.py
}

gpt_assistant = GPTAssistantAgent(name="assistant",
                                instructions="You are adapt at question answering",
                                llm_config=llm_config)

user_proxy = UserProxyAgent(name="user_proxy",
    code_execution_config=False,
    is_termination_msg=lambda msg: "TERMINATE" in msg["content"],
    human_input_mode="ALWAYS")
user_proxy.initiate_chat(gpt_assistant, message="What is the name of the class of agents I gave you?")

gpt_assistant.delete_assistant()