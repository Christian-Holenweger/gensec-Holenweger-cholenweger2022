"""Interactive command-line assistant powered by Gemini and LangChain."""

import os

from langchain_experimental.tools.python.tool import PythonREPLTool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent


def create_agent():
    """Create a Gemini agent equipped with a Python REPL tool."""
    model_name = os.getenv("GOOGLE_MODEL")
    if not model_name:
        raise ValueError("Set the GOOGLE_MODEL environment variable to a Gemini model name.")

    llm = ChatGoogleGenerativeAI(model=model_name)
    tools = [PythonREPLTool()]
    return create_react_agent(llm, tools)


def main():
    """Run an interactive command-line loop until the user exits."""
    try:
        agent = create_agent()
    except Exception as exc:
        print(f"Could not start the assistant: {exc}")
        return

    print("Cybersecurity assistant ready. Type 'exit' or 'quit' to stop.")
    while True:
        try:
            request = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break

        if request.lower() in {"exit", "quit"}:
            print("Goodbye.")
            break
        if not request:
            continue

        try:
            result = agent.invoke({"messages": [("user", request)]})
            print(f"Assistant: {result['messages'][-1].content}")
        except Exception as exc:
            print(f"Assistant error: {exc}")


if __name__ == "__main__":
    main()
