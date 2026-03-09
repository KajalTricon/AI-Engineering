from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from fastapi import FastAPI
from pydantic import BaseModel
import os
import getpass

app = FastAPI()

load_dotenv()

if not os.environ.get("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = getpass.getpass("Enter your OPENAI_API_KEY ")

llm = ChatOpenAI(model="gpt-4o", temperature=1)

prompt = ChatPromptTemplate.from_messages(
    [("system", "You're a helpful assistant"), ("placeholder", "{chat_history}"), ("human", "{user_query}")]
)

store = {}

def get_chat_history(session_id: str):
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]


chain = prompt | llm

chat_with_history = RunnableWithMessageHistory(
    runnable=chain,
    get_session_history=get_chat_history,
    input_messages_key="user_query",
    history_messages_key="chat_history",
)


class ConversationRequest(BaseModel):
    user_query: str
    session_id: str


@app.post("/api/v1/conversation")
async def conversation_endpoint(request: ConversationRequest):
    response = chat_with_history.invoke(
        {"user_query": request.user_query}, {"configurable": {"session_id": request.session_id}}
    )
    return {"response": response}
