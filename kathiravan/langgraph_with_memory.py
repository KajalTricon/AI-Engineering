from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.checkpoint.memory import MemorySaver  # for memory
from langchain_openai import ChatOpenAI
from langchain.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv
from langgraph.prebuilt import ToolNode, tools_condition


load_dotenv()


def add(a: int, b: int) -> int:
    """Adds two integers.
    Args:
    a: The first integer.
    b: The second integer.
    Returns:
    The sum of the two integers."""

    return a + b


def multiply(a: int, b: int) -> int:
    """Multiplies two integers.
    Args:
    a: The first integer.
    b: The second integer.
    Returns:
    The product of the two integers."""

    return a * b


def divide(a: int, b: int) -> int:
    """Divides two integers.
    Args:
    a: The first integer.
    b: The second integer.
    Returns:
    The quotient of the two integers."""

    return a / b


def subtract(a: int, b: int) -> int:
    """Subtracts two integers.
    Args:
    a: The first integer.
    b: The second integer.
    Returns:
    The difference of the two integers."""

    return a - b


tools = [add, divide, multiply, subtract]

llm = ChatOpenAI(model="gpt-4o", temperature=0)
llm_with_tools = llm.bind_tools(tools)


def agent(state: MessagesState):
    response = llm_with_tools.invoke(state.get("messages"))
    return {"messages": response}


builder = StateGraph(MessagesState)

builder.add_node("agent", agent)
builder.add_node("tools", ToolNode(tools))

builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", tools_condition)
builder.add_edge("tools", "agent")
builder.add_edge("agent", END)


memory = MemorySaver()

graph = builder.compile(checkpointer=memory)

config = {"configurable": {"thread_id": "session_1"}}  # thread_id is keyword

graph.invoke(
    {
        "messages": [
            SystemMessage(content="You're a helpful assistant.", id="sys_msg_123"),
            HumanMessage(content="What is the sum between 10 and 20"),
        ]
    },
    config=config,
)

graph.invoke(
    {
        "messages": [
            SystemMessage(content="You're a helpful assistant.", id="sys_msg_123"),
            HumanMessage(content="Subtract it by 5"),
        ]
    },
    config=config,
)

response = graph.invoke(
    {
        "messages": [
            SystemMessage(content="You're a helpful assistant.", id="sys_msg_123"),
            HumanMessage(content="Divide and multiply it by 2"),
        ]
    },
    config=config,
)

for res in response["messages"]:
    res.pretty_print()


img = graph.get_graph().draw_mermaid_png()

with open("with_tools.png", "wb") as f:
    f.write(img)
