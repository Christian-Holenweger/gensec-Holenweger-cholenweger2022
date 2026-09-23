"""Build the Security Study Notebook Chroma database from local study files."""

import os
from pathlib import Path

from langchain_chroma import Chroma
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    UnstructuredMarkdownLoader,
)
from langchain_google_vertexai import VertexAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

STUDY_DOCS_DIRECTORY = Path(__file__).resolve().parent / "study_docs"
CHROMA_PERSIST_DIRECTORY = Path(__file__).resolve().parent / "rag_data" / ".chromadb"


def load_study_documents(directory: Path):
    """Load supported study files from a directory, including its subfolders."""
    loaders = {
        ".txt": TextLoader,
        ".pdf": PyPDFLoader,
        ".md": UnstructuredMarkdownLoader,
    }
    documents = []
    for file_path in sorted(directory.rglob("*")):
        loader_class = loaders.get(file_path.suffix.lower())
        if file_path.is_file() and loader_class:
            documents.extend(loader_class(str(file_path)).load())
    return documents


def create_embeddings():
    """Create the Vertex AI embedding model used by the homework app."""
    return VertexAIEmbeddings(
        model_name="gemini-embedding-001",
        project=os.getenv("GOOGLE_CLOUD_PROJECT"),
        location="us-west1",
    )


def ingest_study_docs():
    """Split study files and save their embeddings in the homework database."""
    if not STUDY_DOCS_DIRECTORY.is_dir():
        print(f"Study documents directory not found: {STUDY_DOCS_DIRECTORY}")
        print("Create hw2/study_docs/ and add .txt, .pdf, or .md files, then run again.")
        return

    documents = load_study_documents(STUDY_DOCS_DIRECTORY)
    if not documents:
        print(f"No supported .txt, .pdf, or .md files found in {STUDY_DOCS_DIRECTORY}.")
        return

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = splitter.split_documents(documents)
    vectorstore = Chroma(
        persist_directory=str(CHROMA_PERSIST_DIRECTORY),
        embedding_function=create_embeddings(),
    )
    vectorstore.add_documents(chunks)
    print(f"Added {len(chunks)} chunks from {len(documents)} documents to {CHROMA_PERSIST_DIRECTORY}.")


if __name__ == "__main__":
    ingest_study_docs()
