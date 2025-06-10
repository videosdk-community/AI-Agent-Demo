"""
This script builds a Pinecone vector store from the HR Policy PDF.
The vector store is used to find relevant HR policy information that can be used
by the AI voice agent when answering HR-related questions.

The script:
1. Loads and processes the HR Policy PDF
2. Splits content into chunks
3. Generates embeddings using OpenAI
4. Stores vectors in Pinecone for later retrieval

Usage:
    python build_pinecone_store.py

Environment variables required:
    - OPENAI_API_KEY
    - PINECONE_API_KEY
    - PINECONE_ENVIRONMENT
    - PINECONE_INDEX_NAME
"""

import os
import time
import hashlib
from pathlib import Path
from typing import List
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from pinecone import Pinecone
from tqdm import tqdm
import PyPDF2

# Load environment variables from .env file
load_dotenv()

# Configuration
PDF_PATH = "HR Policy Manual 2023 (8).pdf"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 5

# Ensure all necessary environment variables are set
if not all([OPENAI_API_KEY, PINECONE_API_KEY, PINECONE_ENVIRONMENT, PINECONE_INDEX_NAME]):
    print("CRITICAL Error: One or more environment variables (OPENAI_API_KEY, PINECONE_API_KEY, PINECONE_ENVIRONMENT, PINECONE_INDEX_NAME) are not set.")
    print("Please ensure your .env file is correctly configured.")
    exit(1)

def extract_text_from_pdf(pdf_path: str) -> List[Document]:
    """Extracts text from PDF and returns a list of Document objects."""
    print(f"Extracting text from PDF: {pdf_path}")
    documents = []
    
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            total_pages = len(pdf_reader.pages)
            
            for page_num in tqdm(range(total_pages), desc="Processing PDF pages"):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                
                if text.strip():  # Only add non-empty pages
                    documents.append(
                        Document(
                            page_content=text,
                            metadata={
                                "source": pdf_path,
                                "page": page_num + 1,
                                "type": "hr_policy"
                            }
                        )
                    )
        
        print(f"Successfully extracted text from {len(documents)} pages")
        return documents
    
    except Exception as e:
        print(f"Error processing PDF: {e}")
        return []

def generate_deterministic_id(source: str, text_chunk: str, page: int) -> str:
    """Generates a deterministic ID for a text chunk based on its source, content, and page number."""
    hasher = hashlib.md5()
    hasher.update(source.encode('utf-8'))
    hasher.update(text_chunk.encode('utf-8'))
    hasher.update(str(page).encode('utf-8'))
    return hasher.hexdigest()

def build_and_upsert_vector_store(clear_index_first: bool = False):
    """
    Processes the HR Policy PDF, generates embeddings, and upserts them to Pinecone.
    
    Args:
        clear_index_first (bool): If True, deletes all vectors from the index before upserting.
    """
    # Extract text from PDF
    documents = extract_text_from_pdf(PDF_PATH)
    
    if not documents:
        print("No documents were extracted from the PDF. Aborting vector store build.")
        return

    # Split documents into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,  # Smaller chunks for better context
        chunk_overlap=200,
        length_function=len,
    )
    split_docs = text_splitter.split_documents(documents)
    print(f"Total documents split into {len(split_docs)} chunks.")

    if not split_docs:
        print("No document chunks were created. Aborting.")
        return

    # Initialize embeddings model and Pinecone client
    print("Initializing embeddings model and Pinecone client...")
    try:
        embeddings_model = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY, request_timeout=60)
        pc = Pinecone(api_key=PINECONE_API_KEY)
        index = pc.Index(PINECONE_INDEX_NAME)
        print(f"Successfully connected to Pinecone index '{PINECONE_INDEX_NAME}'.")
    except Exception as e:
        print(f"Failed to initialize OpenAIEmbeddings or Pinecone client: {e}")
        return

    # Clear index if requested
    if clear_index_first:
        print(f"WARNING: Deleting all vectors from index '{PINECONE_INDEX_NAME}' as per request...")
        try:
            index.delete(delete_all=True)
            print("All vectors deleted from the index.")
        except Exception as e_del:
            print(f"Error deleting vectors from index: {e_del}. Proceeding without clearing.")

    # Process and upsert documents in batches
    EMBEDDING_BATCH_SIZE = 64
    total_chunks = len(split_docs)
    print(f"Starting to process and upsert {total_chunks} chunks in batches of {EMBEDDING_BATCH_SIZE}...")

    for i in tqdm(range(0, total_chunks, EMBEDDING_BATCH_SIZE), desc="Processing Batches"):
        batch_documents = split_docs[i : i + EMBEDDING_BATCH_SIZE]
        current_batch_num = (i // EMBEDDING_BATCH_SIZE) + 1
        total_batches = (total_chunks + EMBEDDING_BATCH_SIZE - 1) // EMBEDDING_BATCH_SIZE
        
        print(f"  Processing batch {current_batch_num}/{total_batches} ({len(batch_documents)} documents)...")

        batch_texts = [doc.page_content for doc in batch_documents]

        for attempt in range(MAX_RETRIES):
            try:
                print(f"    Attempt {attempt + 1}/{MAX_RETRIES}: Generating embeddings for batch {current_batch_num}...")
                batch_embeddings = embeddings_model.embed_documents(batch_texts)
                print(f"    Embeddings generated for batch {current_batch_num}.")

                vectors_to_upsert = []
                for doc, embedding in zip(batch_documents, batch_embeddings):
                    deterministic_id = generate_deterministic_id(
                        doc.metadata['source'],
                        doc.page_content,
                        doc.metadata['page']
                    )
                    metadata_for_pinecone = doc.metadata.copy()
                    metadata_for_pinecone['text'] = doc.page_content
                    
                    vectors_to_upsert.append({
                        "id": deterministic_id,
                        "values": embedding,
                        "metadata": metadata_for_pinecone
                    })
                
                print(f"    Attempt {attempt + 1}/{MAX_RETRIES}: Upserting {len(vectors_to_upsert)} vectors for batch {current_batch_num} to Pinecone...")
                index.upsert(vectors=vectors_to_upsert)
                print(f"    Batch {current_batch_num} successfully upserted.")
                break

            except Exception as e:
                print(f"An error occurred during processing or upserting batch {current_batch_num} (Attempt {attempt + 1}/{MAX_RETRIES}): {e}")
                if attempt < MAX_RETRIES - 1:
                    print(f"Waiting for {RETRY_DELAY_SECONDS} seconds before retrying...")
                    time.sleep(RETRY_DELAY_SECONDS)
                else:
                    print(f"Max retries reached for batch {current_batch_num}. Skipping this batch.")

    print("All HR Policy batches processed and stored in Pinecone.")

if __name__ == "__main__":
    print("Starting the process to build HR Policy vector store...")
    build_and_upsert_vector_store(clear_index_first=True)
    print("Process finished.")
