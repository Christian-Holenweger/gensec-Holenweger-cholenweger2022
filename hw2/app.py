"""Chainlit application for the Security Study Notebook."""

import os
from pathlib import Path

import chainlit as cl
from langchain_chroma import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_vertexai import VertexAIEmbeddings

CHROMA_PERSIST_DIRECTORY = (
    Path(__file__).resolve().parent.parent
    / "02_LangChain"
    / "07_RAG"
    / "rag_data"
    / ".chromadb"
)


def create_vectorstore():
    """Create the Chroma vector store with Vertex AI embeddings."""
    embeddings = VertexAIEmbeddings(
        model_name="gemini-embedding-001",
        project=os.getenv("GOOGLE_CLOUD_PROJECT"),
        location="us-west1",
    )
    return Chroma(
        persist_directory=str(CHROMA_PERSIST_DIRECTORY),
        embedding_function=embeddings,
    )


def create_prompt():
    """Create the prompt used to answer questions from retrieved context."""
    return ChatPromptTemplate.from_template(
        """You are an assistant for question-answering tasks.
Use the following pieces of retrieved context to answer the question.
If you don't know the answer, just say that you don't know.
Use three sentences maximum and keep the answer concise.

Question: {question}

Context: {context}

Answer:"""
    )


def format_docs(docs):
    """Join retrieved document text into one context string."""
    return "\n\n".join(doc.page_content for doc in docs)


def create_rag_chain():
    """Build the retriever and answer-generation chain."""
    vectorstore = create_vectorstore()
    retriever = vectorstore.as_retriever()
    llm = ChatGoogleGenerativeAI(model=os.getenv("GOOGLE_MODEL"))

    answer_chain = create_prompt() | llm | StrOutputParser()
    return retriever, answer_chain


retriever, answer_chain = create_rag_chain()


def format_sources(docs):
    """Return unique source names from document metadata, if available."""
    sources = []
    for doc in docs:
        metadata = doc.metadata or {}
        source = metadata.get("source") or metadata.get("file_path")
        if source and source not in sources:
            sources.append(source)
    return sources


@cl.on_chat_start
async def on_chat_start():
    """Show the application logo and welcome message at chat start."""
    logo = cl.Image(
        name="logo",
        display="inline",
        url="https://codelabs.cs.pdx.edu/images/pdx-cs-logo.png",
    )
    await cl.Message(content="", elements=[logo]).send()

    welcome_text = (
        "**Welcome to Security Study Notebook!**\n\n"
        "Ask a question about the study documents.\n\n"
    )
    await cl.Message(content=welcome_text).send()


@cl.on_message
async def on_message(message: cl.Message):
    """Answer a question and show the retrieved documents as sources."""
    docs = retriever.invoke(message.content)
    answer = answer_chain.invoke(
        {"question": message.content, "context": format_docs(docs)}
    )
    sources = format_sources(docs)
    source_text = "\n".join(f"- {source}" for source in sources)
    if not source_text:
        source_text = "- Source metadata unavailable"

    await cl.Message(content=f"{answer}\n\n**Sources**\n{source_text}").send()


if __name__ == "__main__":
    cl.run()
