# ANSI escape codes for text colors
print("\033[91m" + "This is red text" + "\033[0m")
print("\033[92m" + "This is green text" + "\033[0m")
print("\033[93m" + "This is yellow text" + "\033[0m")
print("\033[94m" + "This is blue text" + "\033[0m")
print("\033[95m" + "This is purple text" + "\033[0m")
print("\033[96m" + "This is cyan text" + "\033[0m")

# from reference.utilities import create_embeddings
# from dotenv import load_dotenv
# import os
# load_dotenv()

# DATA_PATH = "./data/"
# STORAGE_PATH = "./storage/"

# # create a list of pdf paths in the data folder
# datalist = os.listdir(DATA_PATH)
# print(len(datalist))
# create_embeddings(data_path=DATA_PATH, storage_path=STORAGE_PATH, rowData=datalist[226])