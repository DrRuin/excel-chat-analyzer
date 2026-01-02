from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import InMemorySaver
from tools import get_pandas_tools

load_dotenv()


async def create_agent():
    """Create LangGraph agent with pandas tools and memory."""

    llm = ChatOpenAI(model="gpt-5.2", streaming=True)
    pandas_tools = get_pandas_tools()
    memory = InMemorySaver()

    agent = create_react_agent(
        llm,
        tools=pandas_tools,
        checkpointer=memory,
        prompt="""You are a data analysis assistant. You help users analyze their uploaded Excel/CSV data.

When analyzing data:
1. First use get_data_info to understand the data structure
2. Use run_analysis to execute pandas code for calculations
3. Use get_column_stats for quick column statistics

When creating charts, output them in vis-chart markdown format like this:

```vis-chart
{"type": "line", "data": [{"time": "2020", "value": 100}, {"time": "2021", "value": 150}]}
```

Supported chart types:
- line: {"type": "line", "data": [{"time": "x", "value": y}, ...]}
- bar: {"type": "bar", "data": [{"category": "x", "value": y}, ...]}
- pie: {"type": "pie", "data": [{"category": "x", "value": y}, ...]}
- column: {"type": "column", "data": [{"category": "x", "value": y}, ...]}
- area: {"type": "area", "data": [{"time": "x", "value": y}, ...]}
- scatter: {"type": "scatter", "data": [{"x": 1, "y": 2}, ...]}
- histogram: {"type": "histogram", "data": [{"value": x}, ...]}
- treemap: {"type": "treemap", "data": [{"name": "x", "value": y, "children": [...]}, ...]}

Always:
1. First analyze data with tools to get actual values
2. Then create the chart with real data from analysis
3. Explain your findings clearly

Remember the conversation context. When user refers to "that data" or "the same", use context from previous messages.""",
    )

    return agent


async def stream_query(agent, query: str, thread_id: str = "default"):
    """Stream query results with step-by-step events and memory."""

    config = {"configurable": {"thread_id": thread_id}}

    async for event in agent.astream_events(
        {"messages": [{"role": "user", "content": query}]}, config=config, version="v2"
    ):
        kind = event["event"]

        if kind == "on_tool_start":
            tool_name = event["name"]
            tool_input = event["data"].get("input", {})
            yield {
                "type": "tool_start",
                "tool": tool_name,
                "input": str(tool_input)[:200],
            }

        elif kind == "on_tool_end":
            tool_name = event["name"]
            output = str(event["data"].get("output", ""))[:500]
            yield {"type": "tool_end", "tool": tool_name, "output": output}

        elif kind == "on_chat_model_stream":
            content = event["data"]["chunk"].content
            if content:
                yield {"type": "token", "content": content}

    yield {"type": "done"}
