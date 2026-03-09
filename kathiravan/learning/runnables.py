from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain.messages import AIMessage


load_dotenv()


llm = ChatOpenAI(model="gpt-4o")


def add_my_name(response: AIMessage):
    return response.content + "by Kathiravan"


runnable_lambda = RunnableLambda(add_my_name)

prompt = PromptTemplate.from_template("{user_query}")

chain = prompt | llm | runnable_lambda

reponse = chain.invoke("What is AI in single line")

print(reponse)


def add_two_numbers(a, b):
    return a + b


print("normal", add_two_numbers(2, 3))

print("using __call__", add_two_numbers.__call__(2, 3))

# Method 1: Wrapper lambda that unpacks tuple input
add_two_numbers_lambda = RunnableLambda(lambda inputs: add_two_numbers(*inputs))
print("using RunnableLambda with tuple", add_two_numbers_lambda.invoke((2, 3)))


# Method 2: Function that accepts dict input
def add_two_numbers_dict(inputs):
    return inputs["a"] + inputs["b"]


add_dict_lambda = RunnableLambda(add_two_numbers_dict)
print("using RunnableLambda with dict", add_dict_lambda.invoke({"a": 2, "b": 3}))


# Method 3: Function that accepts single tuple input
def add_two_numbers_tuple(inputs):
    a, b = inputs
    return a + b


# Method 3: Function that accepts single tuple input
def add_two_numbers_tuple(inputs):
    a, b = inputs
    return a + b

add_tuple_lambda = RunnableLambda(add_two_numbers_tuple)
print("using RunnableLambda with tuple input", add_tuple_lambda.invoke((2, 3)))


runnable_passthrough = RunnablePassthrough()

# RunnablePassthrough.assign() expects keyword arguments, not a dictionary
# Also, it expects dictionary inputs, not tuple inputs


def add_two_numbers_dict(inputs):
    return inputs["a"] + inputs["b"]


runnable_passthrough_with_assign = RunnablePassthrough.assign(answer=add_two_numbers_dict)

print("using RunnablePassthrough with dict", runnable_passthrough.invoke({"a": 2, "b": 3}))

print("using RunnablePassthrough with assign", runnable_passthrough_with_assign.invoke({"a": 2, "b": 3}))
