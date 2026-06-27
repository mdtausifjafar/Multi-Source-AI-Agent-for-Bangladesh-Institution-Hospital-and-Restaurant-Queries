# this tool is used when the question is general knowledge and not something
# that lives in our three databases, for example policy questions or definitions

import os
from langchain.tools import BaseTool
from tavily import TavilyClient


class WebSearchTool(BaseTool):
    name: str = "WebSearchTool"
    description: str = (
        "Use this tool for general knowledge questions that are not about "
        "specific institutions, hospitals, or restaurants in our databases. "
        "Examples: government policies, definitions, cultural context, "
        "history, or any question requiring up to date information from the web."
    )

    def _run(self, query: str) -> str:
        # tavily is free to start and built for ai agents so results come back clean
        api_key = os.environ.get("TAVILY_API_KEY")
        if not api_key:
            return "web search is not available because TAVILY_API_KEY is missing from the environment"

        client = TavilyClient(api_key=api_key)
        search_results = client.search(query=query, max_results=5)

        # tavily returns a list of result dicts, we combine their content into one block
        result_chunks = []
        for result in search_results.get("results", []):
            title = result.get("title", "untitled")
            content = result.get("content", "")
            result_chunks.append(f"{title}: {content}")

        if not result_chunks:
            return "no relevant web results were found for this query"

        combined_text = "\n\n".join(result_chunks)
        return combined_text

    async def _arun(self, query: str) -> str:
        return self._run(query)
