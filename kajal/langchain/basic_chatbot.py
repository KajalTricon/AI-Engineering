from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv


load_dotenv()

model = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
)

while True:
    user_message = input("Type here: ")
    print(f"User: {user_message}")
    if user_message.strip().lower() in ["exit","quit","bye"]:
        break
    bot = model.invoke(user_message)
    print(f"Bot: {bot.content}" )