from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableSequence, RunnableLambda, RunnablePassthrough, RunnableParallel
from dotenv import load_dotenv

load_dotenv()

passthrough = RunnablePassthrough() # This runnable simply returns the input as output

print(passthrough.invoke("Hello, World!"))

prompt1 = PromptTemplate(
    template='Write a poem in 100 words from given words {words}',
    input_variables=['words']
)
model = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
)

parser = StrOutputParser()

prompt2 = PromptTemplate(
    template='Explain the following poem - {text}',
    input_variables=['text']
)

poem_gen_chain = RunnableSequence(prompt1, model, parser)

parallel_chain = RunnableParallel({
    'poem': RunnablePassthrough(),
    'explanation': RunnableSequence(prompt2, model, parser)
})

final_chain = RunnableSequence(poem_gen_chain, parallel_chain)

print(final_chain.invoke({'words':['sun','moon','stars']}))
