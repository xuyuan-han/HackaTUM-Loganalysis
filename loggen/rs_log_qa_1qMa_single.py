import autogen
import os
from autogen.retrieve_utils import TEXT_FORMATS
from autogen.agentchat.contrib.retrieve_assistant_agent import RetrieveAssistantAgent
from autogen.agentchat.contrib.retrieve_user_proxy_agent import RetrieveUserProxyAgent
import chromadb

config_list = autogen.config_list_from_json(
    env_or_file="OAI_CONFIG_LIST_QA",
    # make sure the config file is in the same directory as this file
    file_location=os.path.dirname(__file__),
    filter_dict={
        "model": ["gpt-3.5-turbo"],
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
    # "temperature": 0,
    "config_list": config_list,
    "timeout": 600,
}

#TODO: change the input context and question
PROMPT_MULTIHOP = """You're a retrieve augmented chatbot. You answer user's questions based on your own knowledge and the context provided by the user. You must think step-by-step.

Some commom errors are:
sshd[1234]: Failed password for [user] from [IP address] port [port number] ssh2
sshd[1234]: error: maximum authentication attempts exceeded for [user] from [IP address] port [port number] ssh2

Context:
{input_context}
Question: {input_question}
Answer:
"""

#create the RetrieveUserProxyAgent instance named "ragproxyagent"
current_file_path = os.path.abspath(__file__)
data_dir = os.path.dirname(os.path.dirname(current_file_path))
log_file = os.path.join(data_dir, 'data', 'test_log1.txt')
# corpus_file = os.path.join(data_dir, 'data', 'test_log1_numbered.txt')
# with open(log_file, 'r') as infile, open(corpus_file, 'w') as outfile:
#     for line_number, line in enumerate(infile, 1):
#         outfile.write(f"{line_number}: {line}")
corpus_file = log_file

# Create a new collection for NaturalQuestions dataset
ragproxyagent = RetrieveUserProxyAgent(
    name="ragproxyagent",
    human_input_mode="TERMINATE",
    system_message="A human admin. Interact with the supervisor to offer instruction. The summarization and answers needs to satisfy this admin.",
    max_consecutive_auto_reply=10,
    retrieve_config={
        "task": "qa",
        "docs_path": [corpus_file],
        # "chunk_token_size": 2000,
        "model": config_list[0]["model"],
        "client": chromadb.PersistentClient(path="/tmp/chromadb"),
        "collection_name": "loganalysis",
        # "chunk_mode": "multi_lines",
        "embedding_model": "all-mpnet-base-v2",
        # "customized_prompt": PROMPT_MULTIHOP,
        #"customized_answer_prefix": "the summary of the log files is",
        "get_or_create": True
    },
)

supervisor = RetrieveAssistantAgent(
    name="supervisor",
    system_message='''Supervisor. Explain and extend the question from ragproxyagent, until ragproxyagent approval.
    The task may involve a summarizer who summarizes the log files, and an analyst who answer ragproxyagent's questions.
    Explain and extend the question first. Then pass it to the summarizer. Wait until summarizer generates the summary which satisfies the ragproxyagent. Let the analyst to answer all following questions based on the given file and the summary.
''',
    llm_config=gpt_config,
)

summarizer = RetrieveAssistantAgent(
    name="summarizer",
    # system_message="Summarizer. You generate a summary of the given files based on the instruction from the ragproxyagent. Especially, focus on the error messages and the ssh log messages. Return the line numbers of the error messages. You do not anwser any questions from ragproxyagent.",
    system_message = 'You are a helpful assistant',
    llm_config=gpt_config,
)

analyst = RetrieveAssistantAgent(
    name="analyst",
    system_message = 'You are a helpful assistant',
    # system_message="Analyst. You will first recieve a summary from summarizer and perform a QA (Question-Answering) task. Pay attention to the line numbers. You should provide answers to questions. You do not need to do any summarization.",
    llm_config=gpt_config,
)

# critic = autogen.AssistantAgent(
#     name="Critic",
#     system_message="Critic. Double check plan, claims, code from other agents and provide feedback. Check whether the plan includes adding verifiable info such as source URL.",
#     llm_config=gpt_config,
# )

def ask_summarizer(message, summarizer):
    ragproxyagent.initiate_chat(summarizer, problem=message)
    ragproxyagent.stop_reply_at_receive(summarizer)
    # ragproxyagent.human_input_mode, ragproxyagent.max_consecutive_auto_reply = "NEVER", 0
    # final message sent from the ragproxyagent
    ragproxyagent.send("summarize the solution and explain the answer in an easy-to-understand way", summarizer)
    # return the last message the ragproxyagent received
    return ragproxyagent.last_message()["content"]

def ask_analyst(message, analyst):
    ragproxyagent.initiate_chat(analyst, problem=message)
    ragproxyagent.stop_reply_at_receive(analyst)
    # ragproxyagent.human_input_mode, ragproxyagent.max_consecutive_auto_reply = "NEVER", 0
    # final message sent from the ragproxyagent
    ragproxyagent.send("summarize the solution and explain the answer in an easy-to-understand way", analyst)
    # return the last message the ragproxyagent received
    return ragproxyagent.last_message()["content"]


ragproxyagent.reset()
supervisor.reset()
summarizer.reset()
analyst.reset()
# critic.reset()

question = " "
question += "Summerize the general and concise summary of the given log file under 500 words, mainly focused on all different kinds of unusual ssh actions, such as invalid users and so on. This summerization will be used by experts for debugging, so please make sure it is accurate and do not need to explain simple definitions." 
question += " "

# ragproxyagent.initiate_chat(
#     supervisor,
#     problem = question
# )

# supervisor_answer = ragproxyagent.last_message()["content"]

ragproxyagent.initiate_chat(
    summarizer,
    problem = question
)

summarizer_answer = ragproxyagent.last_message()["content"]

ragproxyagent.initiate_chat(
    analyst,
    problem = summarizer_answer
)