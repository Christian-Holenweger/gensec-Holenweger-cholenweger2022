import os
import readline
from langchain_core.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder
)
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_google_genai import ChatGoogleGenerativeAI

# Configure the chat model used by the memory example.
llm = ChatGoogleGenerativeAI(model=os.getenv("GOOGLE_MODEL"))

# Build a prompt that includes prior messages before the current input.
prompt = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template("You are a helpful assistant for the Generative Security class at Portland State University."),
    MessagesPlaceholder(variable_name="history"),
    HumanMessagePromptTemplate.from_template("{input}")
])

# Compose the prompt and model into a basic chat chain.
chain = prompt | llm

# Use one session ID for this command-line demo.
session_id = "psu-gensec-session"

# Store the history instance separately so we can print it
message_history = InMemoryChatMessageHistory()

# Wrap the chain so LangChain automatically injects and updates history.
chat_chain = RunnableWithMessageHistory(
    chain,
    lambda session_id: message_history,  # You could also return a new one per session
    input_messages_key="input",
    history_messages_key="history"
)

# Helper to print the message history
def pretty_print_history(messages):
    """Print chat history messages with simple human-readable roles."""
    # Show the retained conversation after each model response.
    print("  History")
    print("  =======")
    for i, msg in enumerate(messages, start=1):
        role = "User" if msg.type == "human" else ("Assistant" if msg.type == "ai" else "System")
        # msg is either a HumanMessage or AIMessage
        print(f"  {i}. {role}: {msg.content}")
    print("  =======")

# Interactive chat loop
print("Welcome to the Generative Security chat application. A blank line exits.")
while True:
    content = input(">> ")
    if content:
        # Invoke the chain with memory and the configured session ID.
        response = chat_chain.invoke({"input": content}, 
                        config={"configurable": {"session_id": session_id}})
        print("RESPONSE:", response.content[0]['text'])

        # Print the history from the retained instance
        pretty_print_history(message_history.messages)
        print("  =======")
    else:
        break
