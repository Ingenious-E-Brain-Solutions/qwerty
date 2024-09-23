import os
import timeit
from typing import List, Dict

# Import llama_index components
from llama_index.core import PromptTemplate
from llama_index.core.retrievers import BaseRetriever, VectorIndexRetriever
from llama_index.core.response.pprint_utils import pprint_response
from llama_index.core.query_engine import CustomQueryEngine
from llama_index.llms.openai import OpenAI

from Reference.utilities import splitOutputs, load_index
from Reference.Embedloader import EmbeddingProcessor
from Reference.config import config

CATEGORIZATION_MODEL = OpenAI(model="gpt-4o-mini")
STORE_LOCALLY = True

print(f"Storage path: {config.STORAGE_PATH}")

IndexLoader = EmbeddingProcessor(store_locally=STORE_LOCALLY)


def callLLMCategorization(rowData,catNquery):

    # index = load_index(STORAGE_PATH,rowData) # load index for pdf
    index = IndexLoader.load_index(rowData) # load index for general case

    class RAGStringQueryEngine(CustomQueryEngine):
        """
        Custom Query Engine for RAG (Retrieval-Augmented Generation).
        """
        retriever: BaseRetriever
        llm: OpenAI
        qa_prompt: PromptTemplate

        def custom_query(self, query_list: List[Dict]):
            """
            Perform a custom query.
            
            Args:
                query_str (List[str]): The list of query strings.

            Returns:
                str: The response from the query.
            """

            context_list = []  # Initialize an empty list to store all context strings

            for query in query_list:  # Loop over each query dictionary in the list
                nodes = self.retriever.retrieve(query['description'])  # Retrieve nodes for the current description string
                context_str = "\n\n".join([n.node.get_content() for n in nodes])  # Create context string
                context_list.append(context_str)  # Append the context string to the list

                # # Uncomment the following to print context string as well.
                # print('--'*50)
                # print(context_str)
                # print('--'*50)

            # Now, context_str_list contains a context string for each description string
            n = len(context_list)
            prompt_str = '''You are an Pharmaceutical Consultant that extracts information from 'Context' which is related to the corresponding 'Description'. Then you put that information in front of corresponding 'Output'. Repeat this for all the given 'Description' and 'Context' pairs and return all filled 'Output'.  \n\n'''
            for i, (context, query) in enumerate(zip(context_list, query_list)):
                prompt_str += f"Description {i+1}: {query['description']} \n Context {i+1}: \n {context} \n\n"

            for i in range(n):
                prompt_str += f"Output {i+1}: \n"

            # print(prompt_str)

            response = self.llm.complete(qa_prompt.format(prompt_str=prompt_str))
            return str(response)

    qa_prompt = PromptTemplate("{prompt_str}")

    retriever = VectorIndexRetriever(index=index, similarity_top_k=5)

    llm = CATEGORIZATION_MODEL

    startt = timeit.default_timer()

    query_engine = RAGStringQueryEngine(
        retriever=retriever,
        llm=llm,
        qa_prompt=qa_prompt,
    )
    response = query_engine.query(catNquery)
    pprint_response(response)

    print("\n", f"Time taken is {timeit.default_timer() - startt}", "\n")

    response_list = splitOutputs(str(response))
    
    return response_list


def callLLM(rowData,catNquery):

    # Create documents from the dictionary item

    index = load_index(config.STORAGE_PATH,rowData) # load index for pdf
    # index = IndexLoader.load_index(rowData) # load index for general case

    retriever = VectorIndexRetriever(index=index, similarity_top_k=7)

    llm = CATEGORIZATION_MODEL

    class RAGStringQueryEngine(CustomQueryEngine):
        """
        Custom Query Engine for RAG (Retrieval-Augmented Generation).
        """
        retriever: BaseRetriever
        llm: OpenAI
        qa_prompt: PromptTemplate

        def custom_query(self, query_dict):
            """
            Perform a custom query.
            
            Args:
                query_str (str): The query string.

            Returns:
                str: The response from the query.
            """
            category =  query_dict['col_name'] 
            query = query_dict['Question']
            guide = query_dict['Guide']
            query_str = 'Question: '+query +'\n' + 'Guide: '+guide
            nodes = self.retriever.retrieve('Category: '+category +'\n' + query_str)
            context_str = "\n\n".join([n.node.get_content() for n in nodes])
            final_query = self.qa_prompt.format(context_str=context_str, query_str=query_str)
            
            print('--'*20)
            print("\033[96m" + str(query_dict) + "\033[0m")
            # print('--'*10)
            # print(query_str)
            # print('--'*10)
            # print(context_str)
            # print('--'*10)
            # print(final_query)
            print('--'*20)

            response = self.llm.complete(final_query)
            return str(response)

    

    rowCatData = []


    for column in catNquery:

        # note time for each loop
        start = timeit.default_timer()

        category = column['col_name']
        
        qa_prompt = PromptTemplate(
            "You are an pharmaceutical consultant that extracts information from 'Context' which is related to the corresponding 'Question' with the help of the 'Guide' and 'Example' provided. Then you put that information in front of 'Output: '.  \n\n"
            " Context:\n---------------------\n{context_str}\n---------------------\n"
            "Using only the context information and not your own knowledge, \nAnswer"
            " the {query_str}\n"
            "Output: \n"
        )
        query_engine = RAGStringQueryEngine(
        retriever=retriever,
        llm=llm,
        qa_prompt=qa_prompt
        )
        response = query_engine.query(column)
        pprint_response(response)
        rowCatData.append(str(response))
        print(f"Time taken for {category} is {timeit.default_timer() - start}")
        print("--"*40)


    return rowCatData

 
