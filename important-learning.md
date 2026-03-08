# Types of Prompts

- Zero shot
- Few shot
- Chain of thought

# PromptTemplate

The difference between PromptTemplate and ChatPromptTemplate is that if you want just "an" answer for a question, you can use "PromptTemplate". For example, a Q&A bot that simply takes a question and provides an answer for that question.

# ChatPromptTemplate

However, if your application involves memory like a chatbot that has a conversation built on your questions (such as "What is AI?" or "Create a study plan for 1 week"), then use ChatPromptTemplate in these scenarios.

Unlike PromptTemplate, ChatPromptTemplate has a key called placeholder to store your chat_history.

**Text completion model vs Chat model**: For text completion, you can go with PromptTemplate, but for chat models with memory, you can go with ChatPromptTemplate.

# from_messages

To define a prompt with a system prompt, use `from_messages` in ChatPromptTemplate:

```python
chat_prompt1 = ChatPromptTemplate.from_messages([("system", "you're a helpful assistant"), ("user", "{user_query}")])
```

# from_template

To define a prompt without a system prompt, use `from_template` in ChatPromptTemplate:

```python
chat_prompt2 = ChatPromptTemplate.from_template(template="You're a helpful assistant. Answer the user query.")
```

# Chain

A Chain in LangChain is nothing but a bunch of runnables.

**Example:**

```python
chain = prompt | llm
```

In the above example, the chain works like this: the output of the prompt will be carried over/passed to the LLM through the pipe `|` symbol. This is an example of LCEL syntax using the pipe operator.

# Runnables

- RunnablePassthrough
- RunnableLambda
- RunnableParallel

# Difference between Runnable and Callable

# Callable

Callable is just a normal python function/method for example

```python
def add_two_numbers(a,b):
    return a+b
```

This above function is a callable because this can be invoked normally like

1.

```python
add_two_numbers(1,2)
```

2.

```python
add_two_numbers.__call__(1,2)
```

# Runnable

Runnables will support `.invoke()` func by default for instance when you look the llm call it supports invoke, in langchain you can use RunnableLambda, RunnablePassthrough, RunnableParallel to change any callable function into Runnable.

```python
response = llm.invoke("What is AI")
```

# RunnablePassthrough

Runnable passthrough is nothing just return whatever we send, if you want to use any callable function in this you can use `.assign()` to pass a callable function to it example below

```python
runnable_passthrough = RunnablePassthrough()
print("using RunnablePassthrough with dict", runnable_passthrough.invoke({"a": 2, "b": 3}))

def add_two_numbers_dict(inputs):
    return inputs["a"] + inputs["b"]

runnable_passthrough_with_assign = RunnablePassthrough.assign(answer=add_two_numbers_dict)
print("using RunnablePassthrough with assign", runnable_passthrough_with_assign.invoke({"a": 2, "b": 3}))
```

# RunnnableLambda

RunnableLambda is a function which will take a callable function as an input and returns a runnable, "Make a note that when you try invoking these runnable you should provide only one input or keywork args" so Ideally you callable can accept dict, tuple and list and the function can iterate throught that

```python
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
```

# Runnable in Action

```python
llm = ChatOpenAI(model="gpt-4o")

def add_my_name(response: AIMessage):
    return response.content + "by Kathiravan"

runnable_lambda = RunnableLambda(add_my_name)

prompt = PromptTemplate.from_template("{user_query}")

chain = prompt | llm | runnable_lambda

reponse = chain.invoke("What is AI in single line")

print(reponse)
```
