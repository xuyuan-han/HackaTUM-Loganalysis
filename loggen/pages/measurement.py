import streamlit as st
from logparser.Drain import LogParser
import pandas as pd

import os

def get_log_data(log_file_path, input_file, output_file):

    log_format = '<Month> <Day> <Time> <Hostname> <Process>:<Content>'  # Define log format to split message fields
    # Regular expression list for optional preprocessing (default: [])
    regex = [
        r'(/|)([0-9]+\.){3}[0-9]+(:[0-9]+|)(:|)'  # IP
    ]
    stt = 0.5  # Similarity threshold
    depth = 5  # Depth of all leaf nodes

    parser = LogParser(log_format, indir=log_file_path, outdir=log_file_path, depth=depth, st=stt, rex=regex)
    parsed_data = parser.parse(input_file)


    # Read the CSV file
    df = pd.read_csv(log_file_path + '/' + input_file +'_templates.csv')

    # Filter the lines where the event template contains the words "error" or "invalid"
    filtered_df = df[df['EventTemplate'].str.contains('error|invalid', case=False, na=False)]

    # Display the contents of the structured CSV file
    st.subheader("Structured CSV File:")
    st.write(filtered_df)


    # Save the filtered lines as a CSV file
    filtered_df.to_csv(log_file_path + '/' + output_file, index=False)

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
                    line_numbers = int(lines_n)
                    view_lines = "\n".join([f"{i+line_numbers-5}: {line}" for i, line in enumerate(lines[line_numbers-5:min(line_numbers+5, len(lines))])])
                    st.write("Display:")
                    st.code(view_lines, language="plaintext")
                except ValueError:
                    st.write("Invalid line number(s) entered.")
            
            
            if st.button("analysis"):
                get_log_data(os.path.dirname(__file__), "../uploaded_file.out", 'test_log1_filtered.csv')
                file_location=os.path.dirname(__file__)
                df = pd.read_csv(os.path.join(file_location, "test_log1_filtered.csv"))

            
            
            


def display_lines(lines):
    st.write("Displaying Lines:")
    st.code("\n".join(lines), language="plaintext")



if __name__ == "__main__":
    read_documents()
    # BEGIN: ed8c6549bwf9
    # Add more functionality as needed
    
    # END: ed8c6549bwf9
            

