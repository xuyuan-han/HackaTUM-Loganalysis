import streamlit as st
from Lc_read import load_log, qa_langchain
import os



def main():
    st.title("Need to read a log? Let me help you!")
    # Create a sidebar for user information
    with st.sidebar:
        user_name = st.text_input("Your Name", "User")
        st.write(f"Hello, {user_name}!")

    # Create a main chat area
    st.subheader("Chat Area")

    # User input
    user_input = st.text_input("You:", "")
    

    # Document upload
    uploaded_file = st.file_uploader("Upload a document", type=["txt", "pdf", "docx","out"])
    # Display user input in a chat bubble
    if user_input:
        st.write(f"{user_name}:", user_input)

        # Simulate a response (replace this with your logic)
        bot_response = generate_bot_response(user_input)

        # Display bot response in a chat bubble
        st.write("Botty:", bot_response)

        # Write user_input and bot_response to a text file
        with open('chat_history.txt', 'a') as file:
            file.write(f"User: {user_input}\n")
            file.write(f"Bot: {bot_response}\n")
        
        

    # Display uploaded document
    if uploaded_file:
        st.subheader("Uploaded Document:")
        # Display information about the uploaded file
        st.write("File Name:", uploaded_file.name)
        st.write("File Type:", uploaded_file.type)
        st.write("File Size:", f"{uploaded_file.size / 1024:.2f} KB")

        # Read the content of the uploaded file
        file_contents = uploaded_file.read()

        # Convert BytesIO to string (decode if it's a binary file)
        try:
            file_contents = file_contents.decode("utf-8")
        except UnicodeDecodeError:
            # Handle decoding error for binary files
            file_contents = f"Binary file content: {file_contents}"

        # Check if the file exists and delete it if it does
        if os.path.exists("data.txt"):
            os.remove("data.txt")

        # Write the content to the file
        with open("data.txt", "w", encoding="utf-8") as file:
            file.write(file_contents)

        # Load Document button
        if st.button("Load Document"):
            # Load the document into the chat
            load_log('data.txt')
            st.write("Document loaded successfully.")

    # Display chat history
        
            # Read the content of the text file
    with open('chat_history.txt', 'r') as file:
        chat_history = file.read()

    # Display the content in the "Chat History" section
    st.subheader("Chat History")
    st.text(chat_history)
    

def generate_bot_response(user_input):
    # Replace this function with your logic to generate a response
    try:
        ans = qa_langchain(user_input)
    except:
        return "Have you uploaded a document? I find nothing in my brain QAQ"

    return ans

if __name__ == "__main__":
    # Initialize chat history
    
    main()

     