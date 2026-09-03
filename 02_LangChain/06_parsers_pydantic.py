import os
import readline
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI

# Configure the chat model that will produce structured JSON.
llm = ChatGoogleGenerativeAI(model=os.getenv("GOOGLE_MODEL"))
#from langchain_openai import ChatOpenAI
#llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL"))
#from langchain_anthropic import ChatAnthropic
#llm = ChatAnthropic(model=os.getenv("ANTHROPIC_MODEL"))
#from langchain_xai import ChatXAI
#llm = ChatXAI(model=os.getenv("XAI_MODEL"))

# Define the JSON shape the model should return.
class GenreMovies(BaseModel):
    """Structured response containing a genre and representative movies."""
    genre: str = Field(description="genre to lookup")
    movies: list[str] = Field(description="list of movies in genre")

# Create a parser that validates model output against the schema.
json_parser = JsonOutputParser(pydantic_object=GenreMovies)

# Include the parser's format instructions directly in the prompt.
json_prompt = PromptTemplate(
    template="Find the top 5 movies of the genre given by the user.\n{format_instructions}\n{genre}\n",
    input_variables=["genre"],
    partial_variables={"format_instructions": json_parser.get_format_instructions()},
)

print(f"This program lists the top 5 movies of a particular genre in a JSON format.\n"
      f"The format instructions given to the LLM from the parser are:\n"
      f"{json_parser.get_format_instructions()}")

# Chain prompt creation, model invocation, and JSON parsing.
chain = json_prompt | llm | json_parser

while True:
    line = input("llm>> ")
    if line:
        # Ask for one genre and print the parsed Python data structure.
        print(chain.invoke({"genre": line}))
    else:
        break
