from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain.messages import AIMessage, SystemMessage, HumanMessage


ai_message = AIMessage(content="I am helpful assistant")

load_dotenv()

llm = ChatOpenAI(model="gpt-4o", temperature=0)


prompt1 = PromptTemplate(input_variables=["user_query"], template="Complete this user query : {user_query}")

prompt = PromptTemplate.from_template("What is the captial of {user_query}")

chat_prompt = ChatPromptTemplate(messages=[("system", "you're a helpful assistant"), ("user", "{user_query}")])

chat_prompt1 = ChatPromptTemplate.from_messages([("system", "you're a helpful assistant"), ("user", "{user_query}")])

chat_prompt2 = ChatPromptTemplate.from_template(template="You're a helpful assitant answer the user query")


print("chat_prompt --->", chat_prompt.invoke({"user_query": "What is the capital of india"}))
print("chat_prompt1 --->", chat_prompt1.invoke({"user_query": "What is the capital of italy"}))
print("chat_prompt2 --->", chat_prompt2.invoke({"user_query": "What is the capital of france"}))
print("prompt1 --->", prompt1.invoke({"user_query": "what is the captial of india"}))

chain = prompt | llm

response = chain.invoke("What is the captial of india")

print(response.content)
