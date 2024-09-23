import argparse
from Reference.utilities import set_paths

def get_args():
    parser = argparse.ArgumentParser(description='Categorization Model')
    
    parser.add_argument('--keyword', type=str, default='German', help='Keyword to search for')
    parser.add_argument('--batch_size', type=int, default=10, help='Batch size for processing')
    parser.add_argument('--cleanup_frequency', type=int, default=30, help='Frequency of cleanup')
    parser.add_argument('--process_from', type=str, default='2013-10-01_AM-RL-XII_Pertuzumab_BAnz.de.en.pdf', help='File to start processing from')
    
    return parser.parse_args()

config = get_args()
DATA_PATH, STORAGE_PATH, QueryExcel, CLEAN_PATH, UNCLEAN_PATH = set_paths(config.keyword)

config.DATA_PATH = DATA_PATH
config.STORAGE_PATH = STORAGE_PATH
config.QueryExcel = QueryExcel
config.CLEAN_PATH = CLEAN_PATH
config.UNCLEAN_PATH = UNCLEAN_PATH

