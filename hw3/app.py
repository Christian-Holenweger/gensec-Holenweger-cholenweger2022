"""Interactive command-line assistant powered by Gemini and LangChain."""

import os
import json
import string
from urllib.parse import parse_qs, urlsplit

from langchain_core.tools import tool
from langchain_experimental.tools.python.tool import PythonREPLTool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent


@tool
def analyze_url(url: str) -> str:
    """Parse a URL and summarize its protocol, host, port, and query.

    The port is inferred for HTTP and HTTPS when it is not written in the URL.
    """
    if not url or url != url.strip() or any(char.isspace() for char in url):
        return "Error: provide a valid URL without whitespace."

    try:
        parsed = urlsplit(url)
        scheme = parsed.scheme.lower()
        hostname = parsed.hostname
        if not scheme or not hostname:
            return "Error: URL must include a scheme and hostname (for example, https://example.com)."

        # Accessing .port validates its syntax and range; None means it was omitted.
        explicit_port = parsed.port
    except ValueError as exc:
        return f"Error: invalid URL: {exc}"

    default_ports = {"http": 80, "https": 443}
    port = explicit_port if explicit_port is not None else default_ports.get(scheme)
    details = {
        "scheme": scheme,
        "hostname": hostname,
        "port": port,
        "path": parsed.path or "/",
        "query_parameters": parse_qs(parsed.query, keep_blank_values=True),
        "uses_https": scheme == "https",
    }
    return json.dumps(details, indent=2)


@tool
def analyze_password_strength(password: str) -> str:
    """Rate password characteristics and suggest ways to improve them.

    The password is analyzed in memory only and is not stored or logged.
    """
    length = len(password)
    has_uppercase = any(char.isupper() for char in password)
    has_lowercase = any(char.islower() for char in password)
    has_number = any(char.isdigit() for char in password)
    has_special = any(char in string.punctuation for char in password)

    # A straightforward score combines length with character variety.
    score = sum((has_uppercase, has_lowercase, has_number, has_special))
    if length >= 12:
        score += 1
    if length >= 16:
        score += 1

    if length < 8 or score <= 2:
        rating = "Weak"
    elif length >= 12 and score >= 5:
        rating = "Strong"
    else:
        rating = "Moderate"

    recommendations = []
    if length < 12:
        recommendations.append("Use at least 12 characters; a longer passphrase is even better.")
    if not has_uppercase:
        recommendations.append("Add uppercase letters.")
    if not has_lowercase:
        recommendations.append("Add lowercase letters.")
    if not has_number:
        recommendations.append("Include numbers.")
    if not has_special:
        recommendations.append("Include special characters.")
    if not recommendations:
        recommendations.append("Keep it unique to this account and consider using a password manager.")

    details = {
        "strength": rating,
        "length": length,
        "has_uppercase": has_uppercase,
        "has_lowercase": has_lowercase,
        "has_numbers": has_number,
        "has_special_characters": has_special,
        "recommendations": recommendations,
    }
    return json.dumps(details, indent=2)


def create_agent():
    """Create a Gemini agent with URL, password, and Python tools."""
    model_name = os.getenv("GOOGLE_MODEL")
    if not model_name:
        raise ValueError("Set the GOOGLE_MODEL environment variable to a Gemini model name.")

    llm = ChatGoogleGenerativeAI(model=model_name)
    tools = [analyze_url, analyze_password_strength, PythonREPLTool()]
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
