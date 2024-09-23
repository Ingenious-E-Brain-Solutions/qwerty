import os
import re
import requests
from openpyxl import load_workbook, Workbook
from typing import Union, List
import pandas as pd
from llama_index.core import SimpleDirectoryReader
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core import StorageContext, VectorStoreIndex, load_index_from_storage
from llama_index.embeddings.openai import OpenAIEmbedding

class ExcelPreProcessor:
    def __init__(self, filepath):
        self.filepath = filepath
        self.wb = load_workbook(filepath)
        self.ws = self.wb.active
        self.column_mapping = {
            "Display_Key": ["Display Key", "Publication numbers with kind code", "publication number", "PN"],
            "Description": ["English description"]
        }

    def modify_headers(self):
        headers = [cell.value for cell in self.ws[1]]
        new_headers = []
        for header in headers:
            new_header = self._get_new_column_name(header)
            new_headers.append(new_header)
        
        for col_num, new_header in enumerate(new_headers, start=1):
            self.ws.cell(row=1, column=col_num, value=new_header)

    def _get_new_column_name(self, column_name):
        normalized_column_name = re.sub(r'[^a-zA-Z0-9]', '', column_name).lower()
        for new_name, variants in self.column_mapping.items():
            for variant in variants:
                normalized_variant = re.sub(r'[^a-zA-Z0-9]', '', variant).lower()
                if normalized_column_name == normalized_variant:
                    return new_name
        return column_name

    def save(self):
        self.wb.save(self.filepath)

class ExcelFileProcessor:
    def __init__(self, file_path):
        self.file_path = file_path
        self.workbook = load_workbook(filename=file_path)
        self.sheet = self.workbook.active
        self.defaultKeys = ['Title', 'Abstract', 'Description', 'Claims', 'Display_Key']

    def find_column_by_header(self, header):
        """Finds and returns the column number of a given header."""
        for cell in self.sheet[1]:
            if cell.value == header:
                return cell.column
        return None

    def find_first_empty_column(self):
        """Finds and returns the first empty column."""
        for cell in self.sheet[1]:
            if cell.value is None:
                return cell.column
        return self.sheet.max_column + 1

    def find_first_empty_row_in_column(self, column):
        """Finds and returns the first empty row number in a specific column."""
        for row in range(2, self.sheet.max_row + 2):
            if self.sheet.cell(row=row, column=column).value is None:
                return row
        return self.sheet.max_row + 1

    def save_relevancy(self, relevancy, row_num=None):
        relevancy_header = 'Relevancy predicted'
        comments_header = 'Comments Made'
        
        # Find or create columns for relevancy and comments
        relevancy_column = self.find_column_by_header(relevancy_header)
        comments_column = self.find_column_by_header(comments_header)
        
        if relevancy_column is None:
            relevancy_column = self.find_first_empty_column()
            self.sheet.cell(row=1, column=relevancy_column, value=relevancy_header)
        
        if comments_column is None:
            comments_column = self.find_first_empty_column() if relevancy_column == self.find_first_empty_column() else relevancy_column + 1
            self.sheet.cell(row=1, column=comments_column, value=comments_header)
        
        # Find the first empty rows in each column
        if row_num is not None:
            start_row = row_num
        else:
            relevancy_start_row = self.find_first_empty_row_in_column(relevancy_column)
            comments_start_row = self.find_first_empty_row_in_column(comments_column)
            start_row = max(relevancy_start_row, comments_start_row)

        # Add data starting from the first empty row
        for i, (status, comment) in enumerate(relevancy, start=start_row):
            # print("row", start_row, "status", status, "comment", comment)
            self.sheet.cell(row=i, column=relevancy_column, value=status)
            self.sheet.cell(row=i, column=comments_column, value=comment)
        
        self.workbook.save(filename=self.file_path)
        
        
    def save_relevant_only_file(self):
        relevancy_header = 'Relevancy predicted'
        relevancy_column = self.find_column_by_header(relevancy_header)
        
        if relevancy_column is None:
            raise ValueError("Relevancy column not found. Ensure relevancy data has been saved first.")
        
        new_workbook = Workbook()
        new_sheet = new_workbook.active
        
        # Copy headers
        for col_num, cell in enumerate(self.sheet[1], 1):
            new_sheet.cell(row=1, column=col_num, value=cell.value)
        
        # Copy relevant rows
        new_row_idx = 2
        for row in self.sheet.iter_rows(min_row=2, values_only=False):
            if row[relevancy_column - 1].value == 'R':
                for col_num, cell in enumerate(row, 1):
                    new_sheet.cell(row=new_row_idx, column=col_num, value=cell.value)
                new_row_idx += 1
        
        new_file_path = os.path.splitext(self.file_path)[0] + '_relevant_only.xlsx'
        new_workbook.save(filename=new_file_path)
        
        return new_file_path

    def save_categories(self, category_data, categories, row_num=None):
        # Determine existing and new category columns
        category_columns = {}
        empty_column = self.find_first_empty_column()
        
        # Robust - can handle categories being present anywhere in the sheet
        # for category in categories:
        #     column = self.find_column_by_header(category)
        #     if column is None:
        #         column = empty_column
        #         self.sheet.cell(row=1, column=column, value=category)
        #         empty_column += 1
        #     category_columns[category] = column

        # Faster - assumes categories are present consequetively in the sheet
        firstcategory = categories[0]
        firstcolumn = self.find_column_by_header(firstcategory)
        if firstcolumn is None:
            for category in categories:
                self.sheet.cell(row=1, column=empty_column, value=category)
                category_columns[category] = empty_column
                empty_column += 1
        else:
            for i, category in enumerate(categories):
                category_columns[category] = firstcolumn + i

                
        
        # Add category data starting from the first empty row in each column
        
        for i, data_row in enumerate(category_data, start=2):
            for category, data in zip(categories, data_row):
                column = category_columns[category]
                if row_num is not None:
                    row_index = row_num
                else:
                    first_empty_row = self.find_first_empty_row_in_column(column)
                    row_index = max(i, first_empty_row)
                self.sheet.cell(row=row_index, column=column, value=data)
        
        self.workbook.save(filename=self.file_path)
        
    
    def extractor(self, keys : Union[List[str], str] = None):
        """
        Extracts specific data from the Excel file and returns it as a pandas DataFrame.

        Parameters:
        -----------
        keys : Union[List[str], str], optional
            A list of column names or a single column name to extract from the Excel file. 
            If 'all', all columns will be extracted. If None, the default keys specified 
            in `self.defaultKeys` will be used. Default is None.

        Returns:
        --------
        pd.DataFrame
            A pandas DataFrame containing the extracted data with columns in lowercase.

        Raises:
        -------
        KeyError
            If any of the specified keys are not found in the header of the Excel sheet.

        Example:
        --------
        >>> processor = ExcelFileProcessor('path/to/excel/file.xlsx')
        >>> df_all = processor.extractor(keys="all")
        >>> print(df_all)
        name  age      city
        0  John   30  New York
        1  Jane   25    Boston
        2   Doe   22   Chicago
        
        >>> df_selected = processor.extractor(keys=["Name", "City"])
        >>> print(df_selected)
        name      city
        0  John  New York
        1  Jane    Boston
        2   Doe   Chicago
        """
        data = []
        header = [cell.value for cell in self.sheet[1]]
        col_index = {name: index for index, name in enumerate(header, start=1)}

        if keys == "all":
            keys = header
        elif not keys:
            keys = self.defaultKeys

        available_cols = {key: col_index.get(key) for key in keys if key in col_index}
        print("using headers :", available_cols)
        
        data = []
        for row in self.sheet.iter_rows(min_row=2, values_only=True):
            if any(row):
                row_dict = {}
                for key, index in available_cols.items():
                    row_dict[key.lower()] = row[index - 1] if index is not None else None
                data.append(row_dict)
        
        # Convert to DataFrame
        # df = pd.DataFrame(data, columns=available_cols.keys())
        
        return data

    def row_extractor(self, row_num, keys : Union[List[str], str] = None ):
        """Extracts data from a specific row in the Excel file."""
        if row_num < 2 or row_num > self.sheet.max_row:
            raise ValueError("Invalid row number. It should be between 2 and the maximum row number.")
        
        header = [cell.value for cell in self.sheet[1]]
        col_index = {name: index for index, name in enumerate(header, start=1)}

        if keys == "all":
            keys = header
        elif not keys:
            keys = self.defaultKeys
        available_cols = {key: col_index.get(key) for key in keys if key in col_index}

        row_data = []
        for row in self.sheet.iter_rows(min_row=row_num, max_row=row_num, values_only=True):
            if any(row):
                row_dict = {}
                for key, index in available_cols.items():
                    row_dict[key.lower()] = row[index - 1] if index is not None else None
                row_data.append(row_dict)
        
        return row_data
    
    def calc_rows(self):
        """Calculates the number of rows in the Excel file."""
        # Find the index of the 'title' column
        title_column_index = None
        for col_idx, cell in enumerate(self.sheet[1]):  # Assuming the first row contains headers
            if cell.value.lower() == 'title':
                title_column_index = col_idx
                break

        if title_column_index is None:
            raise ValueError("Column 'title' not found in the sheet.")

        row_count = 0
        # Iterate through the rows until we find an empty cell in column A
        for row in self.sheet.iter_rows(min_row=2):
            if row[title_column_index].value is None:
                break
            row_count += 1
        return row_count

'''helper functions'''

# categorization

def convertListToDict(lst):
    return [{'col_name': i[0], 'description': i[1]} for i in lst]

def splitOutputs(input_string):
    # Split the string at 'Output' followed by a number and a colon
    split_list = re.split(r'Output \d+:', input_string)
    
    # Remove the first element if it's an empty string
    if split_list[0] == '':
        split_list.pop(0)
    
    return split_list

def create_catNquery_from_excel(file_path, source=None):
    # Read the Excel file
    df = pd.read_excel(file_path)
    
    if source is not None:
        df = df[df['Source'] == source]
        
    # Create the catNquery list of dictionaries
    catNquery = []
    
    # Iterate over the rows and build the list of dicts
    for index, row in df.iterrows():
        catNquery.append({
            'col_name': row['Headers'],           # Assuming the 'Headers' is the column name in the Excel
            'Question': row['Questions'],       # Assuming 'Questions' is the column name in the Excel
            'Guide': row['Guide']
        })
    
    return catNquery

def create_embeddings(data_path, storage_path, rowData: str):
    persist_dir = os.path.join(storage_path, rowData)
    # Check if embeddings already exist
    if os.path.exists(persist_dir):
        print(f"Embeddings for '{rowData}' already exist. Skipping creation.")
        return  # Exit the function if embeddings exist
    print(f"Creating embeddings for '{rowData}'.")
    document = SimpleDirectoryReader(input_dir=data_path, input_files=[os.path.join(data_path,rowData)]).load_data()
    storage_context = StorageContext.from_defaults()
    
    VectorStoreIndex.from_documents(
            documents=document,
            storage_context=storage_context,
            transformations=[
                SentenceSplitter(chunk_size=128, chunk_overlap=5),
                OpenAIEmbedding(),
            ]
        )
    storage_context.persist(persist_dir=persist_dir)     
    
def load_index(storage_path, rowData: str):
    
    storage_context = StorageContext.from_defaults(
                persist_dir=os.path.join(storage_path, rowData)
            )
    cur_index = load_index_from_storage(
                storage_context
            )
    return cur_index

# Define the cleanup functions
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
    
# Function to get the latest Excel file in the query path
def get_latest_excel(query_path):
    excel_files = [f for f in os.listdir(query_path) if f.endswith('.xlsx')]
    if not excel_files:
        raise FileNotFoundError(f"No Excel files found in {query_path}.")
    latest_file = max([os.path.join(query_path, f) for f in excel_files], key=os.path.getctime)
    return latest_file

# Function to set paths based on a given keyword
def set_paths(keyword):
    base_data_path = "Data"
    base_storage_path = "Storage"
    base_query_path = "Queries"
    base_clean_path = "Clean"
    base_unclean_path = "Unclean"

    data_path = os.path.join(base_data_path, keyword)
    storage_path = os.path.join(base_storage_path, keyword)
    query_path = os.path.join(base_query_path, keyword)
    clean_path = os.path.join(base_clean_path, keyword)
    unclean_path = os.path.join(base_unclean_path, keyword)

    # Ensure the paths exist
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data path not found: {data_path}")
    if not os.path.exists(storage_path):
        os.makedirs(storage_path)
    if not os.path.exists(query_path):
        raise FileNotFoundError(f"Query path not found: {query_path}")
    if not os.path.exists(clean_path):
        os.makedirs(clean_path)
    if not os.path.exists(unclean_path):
        os.makedirs(unclean_path)
    
    # Get the latest QueryExcel file
    query_excel = get_latest_excel(query_path)
    
    return data_path, storage_path, query_excel, clean_path, unclean_path
        
# relevancy

def extractReason(text):
    parts = text.split("Reason: ", 1)
    return parts[1] if len(parts) > 1 else ""
 
def extractRelated(text):
    return '1R1' in text

if __name__ == '__main__':
    processor = ExcelFileProcessor('data.xlsx')
    processor.save_relevancy([('R', 'Relevant'), ('N', 'Not relevant')])