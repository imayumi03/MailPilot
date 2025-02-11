import os
import logging
import sys
import nest_asyncio
from dotenv import load_dotenv
from llama_index.core import SummaryIndex, Settings, VectorStoreIndex
from llama_index.core import SimpleDirectoryReader
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.core import StorageContext, load_index_from_storage
import openai
from llama_index.core.node_parser import (
    SentenceSplitter)

nest_asyncio.apply()
load_dotenv()
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))

def initialize_and_persist_vectorstore(dir_path, persist_dir):
    api_key = "sk-proj-vHbGimMSVyxKKCd0KKVXT3BlbkFJ7jH1F0rVIQAvJPokrAN7"
    if not api_key:
        openai.api_key = api_key

    if not os.path.exists(persist_dir):
        os.makedirs(persist_dir)

    if os.listdir(persist_dir):
        storage_context = StorageContext.from_defaults(persist_dir=persist_dir)
        summary_index = load_index_from_storage(storage_context)
    else:
        reader = SimpleDirectoryReader(input_dir=dir_path)
        documents = reader.load_data()

        Settings.llm = OpenAI(max_tokens=4000,model="gpt-4o")
        Settings.embed_model = OpenAIEmbedding(
            model_name="text-embedding-3-large", 
            api_key=api_key,
            max_tokens=4000
        )
        summary_index = SummaryIndex.from_documents(documents)
        summary_index.storage_context.persist(persist_dir=persist_dir)

    Settings.llm = OpenAI(max_tokens=4000, model="gpt-4o")
    chat_engine = summary_index.as_chat_engine(chat_mode="context")
    return chat_engine
