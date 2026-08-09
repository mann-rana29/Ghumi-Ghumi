from tavily import TavilyClient
from dotenv import load_dotenv
import os

load_dotenv()

client = TavilyClient(
    api_key=os.getenv("TAVILY_API_KEY")
)

def tavily_search(query):
    response = client.search(
        query=query,
        max_results=5
    )

    results = []

    for i, r in enumerate(response["results"],1):
        title = r.get("title","Unknown")
        url = r.get("url","")
        content = r.get("content","").strip()
        
        if len(content) > 300:

            # r split is used here to make sure a full word is not cut in half . for eg - "hy my name is mann" lets say we doing [:16]  so mann is getting cut from btw , here rsplit returns ["my name is ", "mann"] , normal split would return "my name is ma"

            content = content[:300].rsplit(" ", 1)[0] + "..."

        results.append(f"{i}. **{title}** \n {url} \n {content}")

    return "\n\n".join(results)