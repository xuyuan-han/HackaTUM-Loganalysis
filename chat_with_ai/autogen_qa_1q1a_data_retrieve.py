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
        "model": {
            "gpt-3.5-turbo-16k",
        }
    },
)

assert len(config_list) > 0
print("models to use: ", [config_list[i]["model"] for i in range(len(config_list))])

# Accepted file formats for that can be stored in 
# a vector database instance

print("Accepted file formats for `docs_path`:")
print(TEXT_FORMATS)

# 1. create an RetrieveAssistantAgent instance named "assistant"
assistant = RetrieveAssistantAgent(
    name="assistant",
    system_message="You are a helpful assistant.",
    llm_config={
        "timeout": 600,
        "cache_seed": 42,
        "config_list": config_list,
    },
)

# Example 6:
# use customized prompt and few-shot learning to address tasks that are not pre-defined in RetrieveChat.

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
corpus_file = os.path.join(data_dir, 'data', 'corpus.txt')

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

# queries_file = "https://huggingface.co/datasets/thinkall/2WikiMultihopQA/resolve/main/queries.jsonl"
queries = """{"_id": "61a46987092f11ebbdaeac1f6bf848b6", "text": "Which film came out first, Blind Shaft or The Mask Of Fu Manchu?", "metadata": {"answer": ["The Mask Of Fu Manchu"]}}
{"_id": "a7b9672009c311ebbdb0ac1f6bf848b6", "text": "Are North Marion High School (Oregon) and Seoul High School both located in the same country?", "metadata": {"answer": ["no"]}}
"""
queries = [json.loads(line) for line in queries.split("\n") if line]
questions = [q["text"] for q in queries]
answers = [q["metadata"]["answer"] for q in queries]
print(questions)
print(answers)

for i in range(len(questions)):
    print(f"\n\n>>>>>>>>>>>>  Below are outputs of Case {i+1}  <<<<<<<<<<<<\n\n")

    # reset the assistant. Always reset the assistant before starting a new conversation.
    assistant.reset()
    
    qa_problem = questions[i]
    ragproxyagent.initiate_chat(assistant, silent=False, problem=qa_problem, n_results=1) # Silent = False to print the output
