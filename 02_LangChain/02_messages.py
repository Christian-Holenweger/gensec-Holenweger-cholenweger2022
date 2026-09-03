import os
import readline
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

# Changed from original code: LLM response is in result.content[0]['text'] instead of result.content

# Configure the chat model from the environment so models can be swapped without code changes.
llm = ChatGoogleGenerativeAI(model=os.getenv("GOOGLE_MODEL"))
# use "gemini-3.5-flash-lite"


# Alternate providers can be enabled by importing the provider and reading its model name.
# from langchain_openai import ChatOpenAI
# llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL"))
# from langchain_anthropic import ChatAnthropic
# llm = ChatAnthropic(model=os.getenv("ANTHROPIC_MODEL"))
# from langchain_xai import ChatXAI
# llm = ChatXAI(model=os.getenv("XAI_MODEL"))

# Build a few-shot chat prompt that teaches the model the two allowed labels.
chat_template = ChatPromptTemplate.from_messages(
    [
        ('system', 'Classify the following e-mail snippet using one of two words: Malicious or Benign.'),
        ('human', 'Message: Unclaimed winning ticket.  View attachment for instructions to claim.'),
        ('ai',"Malicious"),
        ('human', 'Message: Thanks for your interest in Generative AI'),
        ('ai','Benign'),
        ('human', 'Message: {message}')
    ]
)

print("Welcome to my chat model spam detector.  Type an e-mail subject line and I will tell you if it is benign or malicious.  A blank line exits.")
while True:
    line = input("llm>> ")
    if line:
        # Render the chat messages with the user's text, then send them to the LLM.
        prompt = chat_template.format_messages(message=line)
        print(f"Rendered prompt is: {prompt}")
        result = llm.invoke(prompt)

        # Display the model's classification text from the provider-specific response shape.
        print(f"Result is: {result.content[0]['text']}")
    else:
        break
