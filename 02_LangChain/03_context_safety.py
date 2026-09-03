import os
import requests
import readline
from bs4 import BeautifulSoup
from langchain_google_genai import ChatGoogleGenerativeAI, HarmCategory, HarmBlockThreshold

def summarize_url(url):
    """Scrape a URL and ask the model to summarize its security issue."""
    # Configure a low-temperature model with explicit safety settings.
    llm = ChatGoogleGenerativeAI(model=os.getenv("GOOGLE_MODEL"),
             safety_settings = {
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
             },
             temperature=0
          )
    # Fetch the page and extract visible text for the prompt context.
    response = requests.get(url)
    if response.status_code == 200:    # 200 is the "OK" HTTP status code
        soup = BeautifulSoup(response.text, "html.parser")
        text = soup.get_text()
    else:
        return "Failed to scrape the website"

    # Ask the model to summarize the security issue from the scraped text.
    prompt = f"Explain the security issue in the following article: {text}"
    response = llm.invoke(prompt)
    return response.content[0]['text']


# url = "https://krebsonsecurity.com/2024/02/arrests-in-400m-sim-swap-tied-to-heist-at-ftx/"
print("Welcome to my URL summarizer.  Enter a URL about a security incident and I will summarize the security issue it involves.  A blank line exits.")
while True:
    content = input(">> ")
    if content:
        # Summarize each entered URL until the user submits a blank line.
        result = summarize_url(content)
        print(result)
    else:
        break
