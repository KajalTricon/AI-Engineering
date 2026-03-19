from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
from langchain_core.runnables import RunnableSequence, RunnableLambda, RunnablePassthrough, RunnableParallel

load_dotenv()

def word_count(text):
    return len(text.split())

prompt = PromptTemplate(
    template='Write a poem in 100 words about {topic}',
    input_variables=['topic']
)

model = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
)

parser = StrOutputParser()

poem_gen_chain = RunnableSequence(prompt, model, parser)

parallel_chain = RunnableParallel({
    'poem': RunnablePassthrough(),
    'word_count': RunnableLambda(word_count)
})

final_chain = RunnableSequence(poem_gen_chain, parallel_chain)

result = final_chain.invoke({'topic':'AI'})

final_result = """{} \n word count - {}""".format(result['poem'], result['word_count'])

print(final_result)