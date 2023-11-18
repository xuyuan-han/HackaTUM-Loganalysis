import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI
from langchain.chains.question_answering import load_qa_chain
from langchain.document_loaders import TextLoader


# build environment
def load_log(log):
    os.environ["OPENAI_API_KEY"] = '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'

    # question = "Show does it provide transperency"
    
    # load data
    # loader = PyPDFLoader('sustainability-report-fy2022.pdf')
    
    # the type of loader must be txt
    # log = log.split('\n')
    loader = 
    loader = TextLoader(log)
    data = loader.load()

    
    #split
    text_splitter = RecursiveCharacterTextSplitter(chunk_size = 500, chunk_overlap = 0)
    all_splits = text_splitter.split_documents(data)
    
    #store
    global vectorstore
    vectorstore = Chroma.from_documents(documents=all_splits, embedding=OpenAIEmbeddings())
   
    # docs = vectorstore.similarity_search(question)
def qa_langchain(question):
    
    
    # generate answer
    llm = ChatOpenAI(model_name="gpt-3.5-turbo-16k-0613", temperature=0)
    qa_chain = RetrievalQA.from_chain_type(llm,retriever=vectorstore.as_retriever())
    
    
    return qa_chain.run({"query": question})


if __name__ == "__main__":
    
    load_log('chat_with_ai/test_log1.txt')
    print('finish loading pdf')
    while True:
        print('\n')
        question= input('Enter your question:')
        print(qa_langchain(question))