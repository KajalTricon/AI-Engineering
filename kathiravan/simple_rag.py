from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

load_dotenv()


llm = ChatOpenAI(model="gpt-4o", temperature=0)

# Loading
loader = TextLoader("msd.txt")
documents = loader.load()

# Splitting / Chunking
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
chunks = text_splitter.split_documents(documents)

# Embeddings

embeddings = OpenAIEmbeddings()

chunk_texts = [document.page_content for document in chunks]
doc_vectors = embeddings.embed_documents(chunk_texts)

# store in DB

vector_store = FAISS.from_documents(chunks, embeddings)
# results = vector_store.similarity_search("Who is MSD")
# print(results)
retriver = vector_store.as_retriever()


def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


prompt_template = ChatPromptTemplate.from_template(
    """
    Use the following context to answer the question:
    context: {context}
    question: {question}
    answer:
    """
)

chain = (
    {"context": retriver | format_docs, "question": RunnablePassthrough()} | prompt_template | llm | StrOutputParser()
)


print(chain.invoke("When MSD is born"))
