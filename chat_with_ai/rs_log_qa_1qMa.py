import autogen
import os
import json
from autogen.retrieve_utils import TEXT_FORMATS
from autogen.agentchat.contrib.retrieve_assistant_agent import RetrieveAssistantAgent
from autogen.agentchat.contrib.retrieve_ragproxyagent_agent import RetrieveUserProxyAgent
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

gpt_config = {
    "cache_seed": 42,  # change the cache_seed for different trials
    "temperature": 0,
    "config_list": config_list,
    "timeout": 120,
}

#TODO: change the input context and question
PROMPT_MULTIHOP = """You're a retrieve augmented chatbot. You answer user's questions based on your own knowledge and the context provided by the user. You must think step-by-step.
First, please learn the following examples of context and question pairs and their corresponding answers.

Context:
Kurram Garhi: Kurram Garhi is a small village located near the city of Bannu, which is the part of Khyber Pakhtunkhwa province of Pakistan. Its population is approximately 35000.
Trojkrsti: Trojkrsti is a village in Municipality of Prilep, Republic of Macedonia.
Q: Are both Kurram Garhi and Trojkrsti located in the same country?
A: Kurram Garhi is located in the country of Pakistan. Trojkrsti is located in the country of Republic of Macedonia. Thus, they are not in the same country. So the answer is: no.


Context:
Early Side of Later: Early Side of Later is the third studio album by English singer- songwriter Matt Goss. It was released on 21 June 2004 by Concept Music and reached No. 78 on the UK Albums Chart.
What's Inside: What's Inside is the fourteenth studio album by British singer- songwriter Joan Armatrading.
Q: Which album was released earlier, What'S Inside or Cassandra'S Dream (Album)?
A: What's Inside was released in the year 1995. Cassandra's Dream (album) was released in the year 2008. Thus, of the two, the album to release earlier is What's Inside. So the answer is: What's Inside.


Context:
Maria Alexandrovna (Marie of Hesse): Maria Alexandrovna , born Princess Marie of Hesse and by Rhine (8 August 1824 – 3 June 1880) was Empress of Russia as the first wife of Emperor Alexander II.
Grand Duke Alexei Alexandrovich of Russia: Grand Duke Alexei Alexandrovich of Russia,(Russian: Алексей Александрович; 14 January 1850 (2 January O.S.) in St. Petersburg – 14 November 1908 in Paris) was the fifth child and the fourth son of Alexander II of Russia and his first wife Maria Alexandrovna (Marie of Hesse).
Q: What is the cause of death of Grand Duke Alexei Alexandrovich Of Russia's mother?
A: The mother of Grand Duke Alexei Alexandrovich of Russia is Maria Alexandrovna. Maria Alexandrovna died from tuberculosis. So the answer is: tuberculosis.


Context:
Laughter in Hell: Laughter in Hell is a 1933 American Pre-Code drama film directed by Edward L. Cahn and starring Pat O'Brien. The film's title was typical of the sensationalistic titles of many Pre-Code films.
Edward L. Cahn: Edward L. Cahn (February 12, 1899 – August 25, 1963) was an American film director.
Q: When did the director of film Laughter In Hell die?
A: The film Laughter In Hell was directed by Edward L. Cahn. Edward L. Cahn died on August 25, 1963. So the answer is: August 25, 1963.

Second, please complete the answer by thinking step-by-step.

Context:
{input_context}
Q: {input_question}
A:
"""

#create the RetrieveUserProxyAgent instance named "ragproxyagent"
current_file_path = os.path.abspath(__file__)
data_dir = os.path.dirname(os.path.dirname(current_file_path))
corpus_file = os.path.join(data_dir, 'data', 'test_log1.out')

# Create a new collection for NaturalQuestions dataset
ragproxyagent = RetrieveUserProxyAgent(
    name="ragproxyagent",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=3,
    retrieve_config={
        "task": "qa",
        "docs_path": corpus_file,
        "chunk_token_size": 2000,
        "model": config_list[0]["model"],
        "client": chromadb.PersistentClient(path="/tmp/chromadb"),
        "collection_name": "2wikimultihopqa",
        "chunk_mode": "one_line",
        "embedding_model": "all-MiniLM-L6-v2",
        "customized_prompt": PROMPT_MULTIHOP,
        "customized_answer_prefix": "the answer is",
        "get_or_create": True
    },
)

ragproxyagent = autogen.UserProxyAgent(
   name="Admin",
   system_message="A human admin. Interact with the planner to discuss the plan. Plan execution needs to be approved by this admin.",
   code_execution_config=False,
)
engineer = autogen.AssistantAgent(
    name="Engineer",
    llm_config=gpt_config,
    system_message='''Engineer. You follow an approved plan. You write python/shell code to solve tasks. Wrap the code in a code block that specifies the script type. The user can't modify your code. So do not suggest incomplete code which requires others to modify. Don't use a code block if it's not intended to be executed by the executor.
Don't include multiple code blocks in one response. Do not ask others to copy and paste the result. Check the execution result returned by the executor.
If the result indicates there is an error, fix the error and output the code again. Suggest the full code instead of partial code or code changes. If the error can't be fixed or if the task is not solved even after the code is executed successfully, analyze the problem, revisit your assumption, collect additional info you need, and think of a different approach to try.
''',
)
scientist = autogen.AssistantAgent(
    name="Scientist",
    llm_config=gpt_config,
    system_message="""Scientist. You follow an approved plan. You are able to categorize papers after seeing their abstracts printed. You don't write code."""
)
planner = autogen.AssistantAgent(
    name="Planner",
    system_message='''Planner. Suggest a plan. Revise the plan based on feedback from admin and critic, until admin approval.
The plan may involve an engineer who can write code and a scientist who doesn't write code.
Explain the plan first. Be clear which step is performed by an engineer, and which step is performed by a scientist.
''',
    llm_config=gpt_config,
)
executor = autogen.UserProxyAgent(
    name="Executor",
    system_message="Executor. Execute the code written by the engineer and report the result.",
    human_input_mode="NEVER",
    code_execution_config={"last_n_messages": 3, "work_dir": "paper"},
)
critic = autogen.AssistantAgent(
    name="Critic",
    system_message="Critic. Double check plan, claims, code from other agents and provide feedback. Check whether the plan includes adding verifiable info such as source URL.",
    llm_config=gpt_config,
)
groupchat = autogen.GroupChat(agents=[ragproxyagent, engineer, scientist, planner, executor, critic], messages=[], max_round=50)
manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=gpt_config)

ragproxyagent.initiate_chat(
    manager,
    message="""
find papers on LLM applications from arxiv in the last week, create a markdown table of different domains.
""",
)