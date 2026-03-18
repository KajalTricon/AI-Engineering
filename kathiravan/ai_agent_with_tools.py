from langgraph.graph import START, END, StateGraph, MessagesState
from langchain_openai import ChatOpenAI
from langchain.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv
from langgraph.prebuilt import ToolNode, tools_condition
from langchain.tools import tool

load_dotenv()


def multiply(a: int, b: int) -> int:
    """Multiplies two integers.
    Args:
    a: The first integer.
    b: The second integer.
    Returns:
    The product of the two integers."""

    return a * b


@tool
def calculator(a, b, action: str):
    """This tool is calculate the arithmetic operation for two numbers
    args:
        a : an integer/ float type number
        b : an integet/ float type number
        action: arithmetic opertation to be done
    """
    if action.lower() == "additon" or "add":
        return a + b
    elif action.lower() == "subtraction" or "sub":
        return a - b
    elif action.lower() == "multiplication":
        return a * b
    elif action.lower() == "divide":
        return a / b


@tool
def get_git_user_info(username):
    """This tool is to get the GitHub user information
    args:
        username: GitHub username
    """
    url = f"https://api.github.com/users/{username}"
    headers = {"Authorization": f"token {os.getenv('GITHUB_TOKEN')}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to fetch user info: {response.status_code} - {response.text}")


# llm = ChatOpenAI(model="gpt-4o", temperature=0)
# llm_with_tools = llm.bind_tools(([multiply]))


# def tool_calling_llm(state: MessagesState) -> MessagesState:
#     response = llm_with_tools.invoke(state.get("messages"))
#     return {"messages": response}


# builder = StateGraph(MessagesState)
# builder.add_node("tool_calling_llm", tool_calling_llm)
# builder.add_edge(START, "tool_calling_llm")
# builder.add_edge("tool_calling_llm", END)

# graph = builder.compile()


# res = graph.invoke({"messages": HumanMessage(content="What is the result of multiplying 2 and 3?")})

# for res in res["messages"]:
#     res.pretty_print()


tools = [multiply, calculator, get_git_user_info]
llm = ChatOpenAI(model="gpt-4o", temperature=0)
llm_with_tools = llm.bind_tools((tools))


def agent_node(state: MessagesState) -> MessagesState:
    response = llm_with_tools.invoke(state.get("messages"))
    return {"messages": response}


builder = StateGraph(MessagesState)
builder.add_node("agent", agent_node)
builder.add_node("tools", ToolNode(tools))
builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", tools_condition)
builder.add_edge("tools", "agent")
builder.add_edge("agent", END)

graph = builder.compile()


res = graph.invoke(
    {
        "messages": [
            SystemMessage(content="You're a helpful assistant.", id="sys_msg_123"),
            HumanMessage(content="What is the result of multiplying 2 and 3?"),
        ]
    }
)

for res in res["messages"]:
    res.pretty_print()
