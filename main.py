from Reference.config import (
    config
)

from Reference.Models import (
    callLLM,
)
from Reference.utilities import (
    create_catNquery_from_excel,
    create_embeddings,
    clean_excel_file
)
import os
import timeit
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

DATA_PATH = config.DATA_PATH
STORAGE_PATH = config.STORAGE_PATH
CLEAN_PATH = config.CLEAN_PATH
UNCLEAN_PATH = config.UNCLEAN_PATH
QueryExcel = config.QueryExcel

# List PDF files in the data folder
datalist = os.listdir(DATA_PATH)
datalist = [file for file in datalist if file.endswith('.pdf')]

print(f"Total files to process: {len(datalist)}")

# Load Excel with categories and queries
catNquery = create_catNquery_from_excel(QueryExcel) 

# Initialize headers and data storage
category_headers = ['rowData'] + [item['col_name'] for item in catNquery]
category_data = []

batch_size = config.batch_size
cleanup_frequency = config.cleanup_frequency
process_from = config.process_from

# Start processing after finding `process_from`
process = False

# print(f"data path: {DATA_PATH}")
# print(f"storage path: {STORAGE_PATH}")
# print(f"query excel: {QueryExcel}")
# print(f"catNquery: {catNquery}")


# Loop through data files

for idx, rowData in enumerate(datalist):
    
    if not process:
        if rowData == process_from:
            process = True
        else:
            print(f"Skipping {rowData}...")
            print('--'*60)
            continue

    start_time = timeit.default_timer()
    
    # Call the LLM on the current rowData
    create_embeddings(data_path=DATA_PATH, storage_path=STORAGE_PATH, rowData=rowData)
    
    result = callLLM(rowData, catNquery)

    # Include rowData in the result list
    result_with_rowData = [rowData] + result
    
    # Append the categories result (with rowData) to the category data list
    category_data.append(result_with_rowData)
    
    print(f"Time taken for iteration {idx + 1}: {timeit.default_timer() - start_time:.2f} seconds")
    print('--'*50)
    
    # Save after every 10 iterations
    if (idx + 1) % batch_size == 0 or (idx + 1) == len(datalist):
        # Convert current category_data to a DataFrame
        data = pd.DataFrame(category_data, columns=category_headers)
        
        # Save to Excel, overwriting existing file
        file_name = os.path.join(UNCLEAN_PATH, f"unclean_categorized_data_{idx + 1}.xlsx")
        data.to_excel(file_name, index=False)
        
        print(f"Data saved after {idx + 1} iterations.")
        print('--'*60)
    
    # Run cleanup after every 100 iterations or at the end of the loop
    if (idx + 1) % cleanup_frequency == 0 or (idx + 1) == len(datalist):
        clean_output_file = os.path.join(CLEAN_PATH, f"cleaned_categorized_data_{idx + 1}.xlsx")
        clean_excel_file(file_name, clean_output_file)
        print(f"Cleanup performed after {idx + 1} iterations.")
            

# Final cleanup after the loop completes (if not already cleaned in the last iteration)
if len(datalist) % cleanup_frequency != 0:
    clean_output_file = os.path.join(CLEAN_PATH, f"cleaned_categorized_data_final.xlsx")
    clean_excel_file(file_name, clean_output_file)
    print(f"Final cleanup performed.")
