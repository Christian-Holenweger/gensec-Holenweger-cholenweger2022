import os
import readline
from langchain_classic import hub
from langchain_chroma import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_google_genai import ChatGoogleGenerativeAI
import chainlit as cl

# fau-gensec changes:
from langchain_google_vertexai import VertexAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate

llm = ChatGoogleGenerativeAI(model=os.getenv("GOOGLE_MODEL"))

vectorstore = Chroma(
     persist_directory="./rag_data/.chromadb",
     embedding_function=VertexAIEmbeddings(
         model_name="gemini-embedding-001",
         project=os.getenv("GOOGLE_CLOUD_PROJECT"),
         location="us-west1"
     )
)

retriever = vectorstore.as_retriever()

# prompt = hub.pull("rlm/rag-prompt")
prompt = ChatPromptTemplate.from_template(
    """You are an assistant for question-answering tasks.
Use the following pieces of retrieved context to answer the question.
If you don't know the answer, just say that you don't know.
Use three sentences maximum and keep the answer concise.

Question: {question}

Context: {context}

Answer:"""
)

print("RAG prompt:", prompt)


def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

@cl.on_chat_start
async def on_chat_start():
    logo = cl.Image(name="logo", display="inline", url="https://codelabs.cs.pdx.edu/images/pdx-cs-logo.png")
    await cl.Message(content="", elements=[logo]).send()

    welcome_text = (
        "**Welcome to the PSU Generative Security Chatbot!**\n\n"
        "Ask me anything from my set of documents.\n\n"
    )
    await cl.Message(content=welcome_text).send()

@cl.on_message
async def on_message(message: cl.Message):
    user_query = message.content
    answer = rag_chain.invoke(user_query)
    await cl.Message(content=answer).send()

if __name__ == "__main__":
    cl.run()

