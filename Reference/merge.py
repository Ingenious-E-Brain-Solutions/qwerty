import os
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

def clean_excel_file(df):
    """Cleans an entire Excel file (all sheets)."""
    cleaned_dfs = {}
    for sheet_name, sheet_df in df.items():
        cleaned_df = sheet_df.applymap(lambda x: clean_text(str(x)) if isinstance(x, str) else x)
        cleaned_dfs[sheet_name] = cleaned_df
    return cleaned_dfs

def merge_excel_files(folder_path, output_file):
    """Merges all Excel files in a folder after cleaning them."""
    all_sheets = {}
    
    # Loop through each file in the folder
    for file_name in os.listdir(folder_path):
        if file_name.endswith('.xlsx'):
            file_path = os.path.join(folder_path, file_name)
            print(f"Processing file: {file_path}")
            
            # Load the Excel file
            df = pd.read_excel(file_path, sheet_name=None)
            
            # Clean the Excel file
            cleaned_dfs = clean_excel_file(df)
            
            # Merge each sheet into all_sheets
            for sheet_name, cleaned_df in cleaned_dfs.items():
                if sheet_name in all_sheets:
                    all_sheets[sheet_name] = pd.concat([all_sheets[sheet_name], cleaned_df], ignore_index=True)
                else:
                    all_sheets[sheet_name] = cleaned_df
    
    # Write the merged and cleaned data to the output file
    with pd.ExcelWriter(output_file) as writer:
        for sheet_name, merged_df in all_sheets.items():
            merged_df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    print(f"Merged and cleaned Excel file saved to: {output_file}")

# Example usage:
folder_path = r'unclean'  # Replace with the path to your folder
output_file = r'clean\merged_cleaned_output.xlsx'  # Replace with desired output file path
merge_excel_files(folder_path, output_file)
