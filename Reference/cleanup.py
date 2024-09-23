import pandas as pd
import re

def clean_text(text):
    """Remove unnecessary text and redundant characters."""
    if pd.isna(text):  # If the text is NaN, return it as is
        return text
    
    # Remove occurrences of 'Output:' and clean redundant characters like newlines and asterisks
    cleaned_text = re.sub(r'Output:\s*', '', text)  # Remove 'Output:' followed by spaces
    cleaned_text = re.sub(r'\n+', ' ', cleaned_text)  # Replace newline characters with space
    cleaned_text = re.sub(r'\*+', '', cleaned_text)  # Remove asterisks
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text)  # Replace multiple spaces with a single space
    return cleaned_text.strip()  # Remove leading and trailing spaces

def clean_excel_file(input_path, output_path):
    # Load the Excel file
    df = pd.read_excel(input_path, sheet_name=None)  # Load all sheets as a dictionary of DataFrames
    
    # Iterate through each sheet and clean the text
    cleaned_dfs = {}
    for sheet_name, sheet_df in df.items():
        cleaned_df = sheet_df.applymap(lambda x: clean_text(str(x)) if isinstance(x, str) else x)
        cleaned_dfs[sheet_name] = cleaned_df
    
    # Save the cleaned data to a new Excel file
    with pd.ExcelWriter(output_path) as writer:
        for sheet_name, cleaned_df in cleaned_dfs.items():
            cleaned_df.to_excel(writer, sheet_name=sheet_name, index=False)

    print(f"Cleaned Excel file saved to: {output_path}")

# Example usage:
input_file = 'categorized_data_260onwards.xlsx'
output_file = r'clean\cleaned_categorized_data_260onwards.xlsx'
clean_excel_file(input_file, output_file)
