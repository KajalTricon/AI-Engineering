from langchain.agents import create_agent
from langchain.tools import tool
from dotenv import load_dotenv
import requests
import os

load_dotenv()


@tool
def calculator(a, b, action: str):
    """This tool is calculate the arithmetic operation for two numbers
    args:
        a : an integer/ float type number
        b : an integet/ float type number
        action: arithmetic opertation to be done
    """
    if action.lower() == "additon" or action.lower() == "add":
        return a + b
    elif action.lower() == "subtraction" or action.lower() == "sub":
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

    return


agent = create_agent(model="gpt-4o", tools=[calculator, get_git_user_info], system_prompt="You're a helpful assistant")


result = agent.invoke({"messages": [{"role": "user", "content": "Sum of 5 and 10"}]})
print(result)



# ----------------------------------------- Decision Making agent -----------------------------------------

'''
The below agent decides what the user should do in a day based on the weather 
'''

'''
from langchain.agents import create_agent
from langchain.tools import tool
from dotenv import load_dotenv

load_dotenv()


@tool
def get_weather(city: str) -> str:
    """Get weather of a city"""
    if city.lower() == "chennai":
        return "rain"
    return "sunny"


@tool
def suggest_movie() -> str:
    """Suggest a movie if weather is bad"""
    return "Watch Interstellar"


@tool
def suggest_place() -> str:
    """Suggest tourist place if weather is good"""
    return "Visit Marina Beach"


agent = create_agent(
    model="gpt-4o", tools=[suggest_movie, get_weather, suggest_place], system_prompt="You're a day planner"
)

respone = agent.invoke(
    {"messages": [{"role": "user", "content": "Check weather in Bangalore and suggest what I should do"}]}
)
print(respone)
'''
