from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field


class CelebrityDetails(BaseModel):
    name: str = Field(description="name of the celebrity")
    age: str = Field(description="age of the celebrity")
    dob: str = Field(decimal_places="Date of birth of the celebrity")


load_dotenv()

llm = ChatOpenAI(model="gpt-4o")

# prompt = PromptTemplate.from_template("{user_query}")

# chain = prompt | llm | StrOutputParser()

# response = chain.invoke({"user_query": "What is AI in single line"})

# print(response)


json_parser = JsonOutputParser()
json_parser = JsonOutputParser(pydantic_object=CelebrityDetails)

# prompt = PromptTemplate.from_template(
#     "Giv me info about this celebrity: {celebrity_name}. I want name, age and date of birth {format_instructions}",
#     partial_variables={"format_instructions": json_parser.get_format_instructions()},
# )

prompt = PromptTemplate.from_template(
    "Giv me info about this celebrity: {celebrity_name}.\n {format_instructions}",
    partial_variables={"format_instructions": json_parser.get_format_instructions()},
)


chain = prompt | llm | json_parser


response = chain.invoke({"celebrity_name": "Max verstappen"})

print(response)
