from langgraph.graph import StateGraph, START, END
from typing import TypedDict
from langgraph.graph.state import CompiledStateGraph
import random


class SampleState(TypedDict):
    name: str


def greet(state: SampleState):
    return {"name": "Hello " + state.get("name")}


def add_exclamation(state: SampleState):
    return {"name": state.get("name") + " !"}


def tell_bye(state: SampleState):
    return {"name": "Bye " + state.get("name").split()[1]}


def tell_bye_if(state: SampleState):
    random_number = random.choice([1, 2])

    if random_number == 1:
        return "END"
    if random_number == 2:
        return "bye"


builder = StateGraph(SampleState)


builder.add_node("greet", greet)
builder.add_node("surprise", add_exclamation)
builder.add_node("bye", tell_bye)


builder.add_edge(START, "greet")
builder.add_edge("greet", "surprise")
builder.add_conditional_edges(
    "surprise",
    tell_bye_if,
    {
        "bye": "bye",
        "END": END,
    },
)
builder.add_edge("bye", END)

graph: CompiledStateGraph = builder.compile()


result = graph.invoke({"name": "Kathir"})
img = graph.get_graph().draw_mermaid_png()

with open("graph.png", "wb") as f:
    f.write(img)

print(result)
