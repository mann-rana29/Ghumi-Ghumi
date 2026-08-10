import os
import certifi
import sys

from pathlib import Path
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_groq import ChatGroq

os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
AVIATIONSTACK_API_KEY = os.getenv("AVIATIONSTACK_API_KEY")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

PROJECT_DIR = Path(__file__).resolve().parent
WEATHER_SERVER_PATH = PROJECT_DIR/ "custom_weather_mcp_server.py"

AVIATION_ENV = os.environ.copy()
AVIATION_ENV["AVIATIONSTACK_API_KEY"] = (
    AVIATIONSTACK_API_KEY or ""
)

WEATHER_ENV = os.environ.copy()
WEATHER_ENV["OPENWEATHER_API_KEY"] = (
    OPENWEATHER_API_KEY or ""
)

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=GROQ_API_KEY
)

client = MultiServerMCPClient(
    {
        "tavily":{
            "transport" : "streamable_http",
            "url" : f"https://mcp.tavily.com/mcp/?tavilyApiKey={TAVILY_API_KEY}"
        },

        "aviationstack" : {
            "transport" : "stdio",
            "command" : "uvx",
            "args" : [
                "aviationstack-mcp"
            ],
            "env" : AVIATION_ENV
        }
    }
)

async def get_all_tools():
    all_tools = []

    for server_name in ("tavily","aviationstack", "weather"):
        try:
            tools = await client.get_tools(
                server_name=server_name
            )

            all_tools.extend(tools)

            print(
                f"\nAvailable tools from "
                f"{server_name} MCP:\n"
            )

            for tool in tools:
                print(tool.name)

        except Exception as error:
            print(
                f"\nCould not connect to "
                f"{server_name} MCP:\n{error}\n"
            )

    return all_tools

search_tool = None

async def initialize_mcp():
    global search_tool

    if search_tool is not None:
        return

    tools = await client.get_tools(
        server_name="tavily"
    )

    tools_by_name = {
        tool.name : tools for tool in tools
    }

    search_tool = tools_by_name.get(
        "tavily_search"
    )

    if search_tool is None:
        available_tools = ", ".join( tools_by_name.keys())

        raise RuntimeError(
            "Tavily MCP connected, but the "
            "'tavily_search' tool was not found. "
            f"Available tools: "
            f"{available_tools or 'none'}"
        )

async def tavily_mcp_search(query: str):
    await initialize_mcp()

    result = await search_tool.ainvoke(
        {
            "query" : query
        }
    )

    return result

aviation_tools = {}

async def initialize_aviation_tools():
    global aviation_tools

    if aviation_tools:
        return

    tools = await client.get_tools(
        server_name="aviationstack"
    )

    aviation_tools = {
        tool.name : tool for tool in tools
    }

    if not aviation_tools:
        raise RuntimeError(
            "AviationStack MCP connected but "
            "returned no tools."
        )

async def aviation_mcp_call(tool_name : str, tool_args : dict = None):
    await initialize_aviation_tools()

    tool = aviation_tools.get(tool_name)

    if tool is None:
        available_tools = ", ".join(
            sorted(aviation_tools.keys())
        )

        raise ValueError(
            f"AviationStack tool '{tool_name}' "
            "was not found. "
            f"Available tools: "
            f"{available_tools or 'none'}"
        )

    result = await tool.ainvoke(tool_args or {})

    return result

