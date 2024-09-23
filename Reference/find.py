import os
import shutil
from PyPDF2 import PdfReader

def find_rl_pdfs(directory):
    rl_pdfs = []
    
    # Walk through all directories and subdirectories
    for root, dirs, files in os.walk(directory):
        for file in files:
            # Check if the file is a PDF and contains 'RL' in its name
            if file.endswith('.en.pdf') and 'RL' in file:
                rl_pdfs.append(os.path.join(root, file))
    
    return rl_pdfs

def copy_pdfs_to_target(pdf_files, target_folder):
    # Ensure the target folder exists
    if not os.path.exists(target_folder):
        os.makedirs(target_folder)

    for pdf in pdf_files:
        # Copy each PDF to the target folder
        pdf_name = os.path.basename(pdf)
        shutil.copy2(pdf, target_folder)
        print(f"Copied: {pdf_name}")
        
        

def move_small_pdfs(pdf_files, source_folder):
    useless_folder = os.path.join(source_folder, 'useless')
    
    # Ensure the 'useless' sub-folder exists
    if not os.path.exists(useless_folder):
        os.makedirs(useless_folder)

    for pdf in pdf_files:
        try:
            # Open the PDF file and count the number of pages
            with open(pdf, 'rb') as file:
                reader = PdfReader(file)
                num_pages = len(reader.pages)
            
            # If the PDF has less than 3 pages, move it to 'useless' folder
            if num_pages < 3:
                
                pdf_name = os.path.basename(pdf)
                shutil.move(pdf, useless_folder)
                print(f"Moved: {pdf_name} (Pages: {num_pages})")
        
        except Exception as e:
            print(f"Failed to process {pdf}: {e}")
            
def delete_duplicates(directory):
    # Create a dictionary to store the file sizes and paths
    file_dict = {}
    
    # Walk through all directories and subdirectories
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            # Get the file size
            file_size = os.path.getsize(file_path)
            
            # If the file size is already in the dictionary, delete the file
            if file_size in file_dict:
                os.remove(file_path)
                print(f"Deleted duplicate: {file_path}")
            else:
                # Add the file size and path to the dictionary
                file_dict[file_size] = file_path


# Example usage
source_directory = r'Z:\Other Documents\Other\German_Dataset'  # Change to your source folder
target_directory = r'Data\German'  # Change to your target folder

# pdf_files = find_rl_pdfs(source_directory)
# copy_pdfs_to_target(pdf_files, target_directory)
# print(len(pdf_files), "files copied to", target_directory)

# pdf_files = find_rl_pdfs(target_directory)
# move_small_pdfs(pdf_files, target_directory)
# print(len(pdf_files), "files processed.")

delete_duplicates(target_directory)