import streamlit as st
from Lc_read import load_log, qa_langchain
import os


def read_documents():
    st.title("Read Multiple Documents")

    # Upload multiple documents
    uploaded_files = st.file_uploader("Upload multiple documents", type=["txt", "pdf", "docx", "out"], accept_multiple_files=True)

    # Display uploaded documents
    if uploaded_files:
        st.subheader("Uploaded Documents:")

        for uploaded_file in uploaded_files:
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

            # Display number of lines
            lines = file_contents.split('\n')
            st.write(f"Number of Lines: {len(lines)}")

            # Display first few lines
            st.write("Preview:")
            preview_lines = "\n".join([f"{i+1}: {line}" for i, line in enumerate(lines[:min(10, len(lines))])])
            st.code(preview_lines, language="plaintext")

            lines_n = st.text_input("Number of the line(s) needed:", "")
            if lines_n:
                try:
                    line_numbers = [int(num) for num in lines_n.split(",")]
                    view_lines = "\n".join([f"{num}: {lines[num-1]}" for num in line_numbers if 1 <= num <= len(lines)])
                    st.write("Display:")
                    st.code(view_lines, language="plaintext")
                except ValueError:
                    st.write("Invalid line number(s) entered.")


def display_lines(lines):
    st.write("Displaying Lines:")
    st.code("\n".join(lines), language="plaintext")


if __name__ == "__main__":
    read_documents()
    # BEGIN: ed8c6549bwf9
    # Add more functionality as needed
    
    # END: ed8c6549bwf9
            

