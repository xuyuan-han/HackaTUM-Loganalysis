from logparser.Drain import LogParser
import pandas as pd
import pandas as pd

input_dir = 'data/'  # The input directory of log file
output_dir = 'result/'  # The output directory of parsing results
log_file = 'final_log.out'  # The input log file name
log_format = '<Month> <Day> <Time> <Hostname> <Process>:<Content>'  # Define log format to split message fields
# Regular expression list for optional preprocessing (default: [])
regex = [
    r'(/|)([0-9]+\.){3}[0-9]+(:[0-9]+|)(:|)'  # IP
]
st = 0.5  # Similarity threshold
depth = 5  # Depth of all leaf nodes

parser = LogParser(log_format, indir=input_dir, outdir=output_dir, depth=depth, st=st, rex=regex)
parsed_data = parser.parse(log_file)


# Read the CSV file
df = pd.read_csv('result/test_log1.out_templates.csv')

# Filter the lines where the event template contains the words "error" or "invalid"
filtered_df = df[df['EventTemplate'].str.contains('error|invalid', case=False, na=False)]


# Save the filtered lines as a CSV file
filtered_df.to_csv('result/filtered_finallog.csv', index=False)

