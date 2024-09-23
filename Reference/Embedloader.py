import os
import qdrant_client
from typing import Dict, Any, List
from llama_index.core import Document, StorageContext, VectorStoreIndex, load_index_from_storage
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.core.ingestion import IngestionPipeline

# Assuming the required libraries are already imported as per the provided function
# Example imports (uncomment these if necessary):
# from your_embedding_library import Document, StorageContext, VectorStoreIndex, SentenceSplitter, OpenAIEmbedding, load_index_from_storage

class EmbeddingProcessor:
    def __init__(self, base_path: str = "./storage", store_locally: bool = True, store_in_memory: bool = False):
        self.base_path = base_path
        self.store_locally = store_locally
        self.store_in_memory = store_in_memory
        if self.store_locally:
            os.makedirs(self.base_path, exist_ok=True)  # Ensure the base directory exists

    def IngestData(self, rowData: Dict[str, str]) -> VectorStoreIndex:

        documents = [Document(text=f"{key}: {val}") for key, val in rowData.items()]
        client = qdrant_client.QdrantClient(location=":memory:")
        vector_store = QdrantVectorStore(client=client, collection_name="test_store")

        pipeline = IngestionPipeline(
            transformations=[
                SentenceSplitter(chunk_size=128, chunk_overlap=5),
                OpenAIEmbedding(),
            ],
            vector_store=vector_store,
        )
        pipeline.run(documents=documents)
        
        return VectorStoreIndex.from_vector_store(vector_store)

    def create_embeddings(self, rowData: Dict[str, str]) -> str:
        """Create embeddings from row data and save to storage."""

        if not self.store_locally:
           return

        display_key = rowData['display_key']
        title = rowData['title']
        persist_dir = os.path.join(self.base_path, display_key)

        # Check if embeddings already exist
        if os.path.exists(persist_dir):
            print(f"Embeddings for '{title}' already exist. Skipping creation.")
            return  # Exit the function if embeddings exist
        
        print(f"Creating embeddings for '{title}'.")
        documents = [Document(text=f"{key}: {val}") for key, val in rowData.items()]

        # To store the index

        storage_context = StorageContext.from_defaults()

        VectorStoreIndex.from_documents(
            documents=documents,
            storage_context=storage_context,
            transformations=[
                SentenceSplitter(chunk_size=128, chunk_overlap=5),
                OpenAIEmbedding(),
            ]
        )
        
        storage_context.persist(persist_dir=persist_dir)


    def load_indexes(self, titles: List[str]) -> Dict[str, VectorStoreIndex]:
        
        if self.store_locally:
            index_set = {}
            for title in titles:
                storage_context = StorageContext.from_defaults(
                    persist_dir=os.path.join(self.base_path, title)
                )
                cur_index = load_index_from_storage(
                    storage_context
                )
                index_set[title] = cur_index
            return index_set
        

    def load_index(self, rowData: Dict[str, str]) -> VectorStoreIndex:
        """Load a single index from storage by title."""

        if self.store_locally:

            title = rowData['title']
            display_key = rowData['display_key']
            storage_context = StorageContext.from_defaults(
                persist_dir=os.path.join(self.base_path, display_key)
            )
            cur_index = load_index_from_storage(
                storage_context
            )

            print(f"Loaded index for '{title}'.")
            return cur_index
        
        else:

            index = self.IngestData(rowData)
            return index
    

# Example usage:
# embedding_creator = EmbeddingCreator('./storage')
# result = embedding_creator.create_embeddings({'title': 'example', 'content': 'This is some content to embed.'})
# print(result)
# indexes = embedding_creator.load_indexes(['example'])
# print(indexes)
# index = embedding_creator.load_index('example')
# print(index)

if __name__ == "__main__":
    embedding_creator = EmbeddingProcessor('./storage')
    result = embedding_creator.create_embeddings({'title': 'example', 'content': 'This is some content to embed.'})
    print(result)
    indexes = embedding_creator.load_indexes(['example'])
    print(indexes)
    index = embedding_creator.load_index('example')
    print(index)