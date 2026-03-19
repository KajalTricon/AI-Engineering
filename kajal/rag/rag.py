from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from dotenv import load_dotenv


load_dotenv()

loader = PyPDFLoader("/Users/kajal.gupta/Documents/Tricon-AI/AI-Engineering/kajal/rag/short-stories-for-children.pdf")
docs = loader.load()[:10]


splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
chunks = splitter.split_documents(docs)

# embeddings = GoogleGenerativeAIEmbeddings(model="gemini-embedding-001")
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)
vector_store = FAISS.from_documents(chunks, embeddings)

retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 4})

print(retriever.invoke('how many stories are there for primary school childrens?'))

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.2)

prompt = PromptTemplate(
    template="""
      You are a helpful assistant.
      Answer ONLY from the provided context.
      If the context is insufficient, just say you don't know.

      {context}
      Question: {question}
    """,
    input_variables = ['context', 'question']
)

# question          = "is the topic of nuclear fusion discussed in this video? if yes then what was discussed"
# retrieved_docs    = retriever.invoke(question)

# context_text = "\n\n".join(doc.page_content for doc in retrieved_docs)
# context_text

# final_prompt = prompt.invoke({"context": context_text, "question": question})

# answer = llm.invoke(final_prompt)
# print(answer.content)



from langchain_core.runnables import RunnableParallel, RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser

def format_docs(retrieved_docs):
  context_text = "\n\n".join(doc.page_content for doc in retrieved_docs)
  return context_text

parallel_chain = RunnableParallel({
    'context': retriever | RunnableLambda(format_docs),
    'question': RunnablePassthrough()
})

# parallel_chain.invoke('who is Demis')

parser = StrOutputParser()

main_chain = parallel_chain | prompt | llm | parser

print(main_chain.invoke('Can you summarize "work is worship" story?'))



# '''[Document(id='800aee0e-28e0-4c3b-97d7-e3beeb10439f', metadata={'producer': 'Microsoft® Word 2010', 'creator': 'Microsoft® Word 2010', 'creationdate': '2012-09-11T20:35:09+05:30', 'author': 'Pavithra', 'moddate': '2012-09-11T20:35:09+05:30', 'source': '/Users/kajal.gupta/Documents/Tricon-AI/AI-Engineering/kajal/rag/short-stories-for-children.pdf', 'total_pages': 44, 'page': 0, 'page_label': '1'}, page_content='Short Stories for Children \nfor  \nSpoken English Program'), Document(id='45493d5b-0f7d-48ee-97f0-d2a77f4f0b1d', metadata={'producer': 'Microsoft® Word 2010', 'creator': 'Microsoft® Word 2010', 'creationdate': '2012-09-11T20:35:09+05:30', 'author': 'Pavithra', 'moddate': '2012-09-11T20:35:09+05:30', 'source': '/Users/kajal.gupta/Documents/Tricon-AI/AI-Engineering/kajal/rag/short-stories-for-children.pdf', 'total_pages': 44, 'page': 1, 'page_label': '2'}, page_content='Spoken English: Short Stories \n2 \n \n \nShort Stories for Children \nLEVEL 1: STORIES FOR PRIMARY SCHOOL CHILDREN .............................................................................. 5 \nTHE WIND AND THE SUN .................................................................................................................... 5 \nTHE VILLAGER AND THE SPECTACLES ................................................................................................. 5 \nAS YOU SOW, SO SHALL YOU REAP ..................................................................................................... 6 \nTHE FARMER AND HIS SONS ............................................................................................................... 6 \nBIRBAL THE WISE ................................................................................................................................ 7 \nTHE WOLF IN SHEEP’S CLOTHING ....................................................................................................... 7 \nHARE AND THE TORTOISE ................................................................................................................... 7 \nNOBODY BELIEVES A LIAR ................................................................................................................... 8 \nWORK IS WORSHIP .............................................................................................................................. 9 \nNEVER BE UNGRATEFUL ...................................................................................................................... 9 \nKEEP YOUR EYES OPEN...................................................................................................................... 10 \nLIVE AND LET LIVE ............................................................................................................................. 10'), Document(id='b43e4f60-8271-41f0-9fd1-ff765c3e960b', metadata={'producer': 'Microsoft® Word 2010', 'creator': 'Microsoft® Word 2010', 'creationdate': '2012-09-11T20:35:09+05:30', 'author': 'Pavithra', 'moddate': '2012-09-11T20:35:09+05:30', 'source': '/Users/kajal.gupta/Documents/Tricon-AI/AI-Engineering/kajal/rag/short-stories-for-children.pdf', 'total_pages': 44, 'page': 4, 'page_label': '5'}, page_content='Spoken English: Short Stories \n5 \n \nLEVEL 1: STORIES FOR PRIMARY SCHOOL CHILDREN \nTHE WIND AND THE SUN \n \nOnce the Wind and the Sun had an argument. “I am stronger than you,” said the Wind. “No, \nyou are not,” said the Sun. Just at that moment they saw a traveler walking across the road. \nHe was wrapped in a shawl. The Sun and the Wind agreed that whoever could separate the \ntraveller from his shawl was stronger. \nThe Wind took the first turn. He blew with all his might to tear the traveller’s shawl from his \nshoulders. But the harder he blew, the tighter the traveller gripped the shawl to his body. \nThe struggle went on till the Wind’s turn was over. \nNow it was the Sun’s turn. The Sun smiled warmly. The traveller felt the warmth of the \nsmiling Sun. Soon he let the shawl fall open. The Sun’s smile grew warmer and warmer... \nhotter and hotter. Now the traveller no longer needed his shawl. He took it off and dropped \nit on the ground. The Sun was declared stronger than the Wind. \n \nMoral: Brute force can’t achieve what a gentle smile can. \n  \nTHE VILLAGER AND THE SPECTACLES \n \nThere was a villager. He was illiterate. He did not know how to read and write. He often saw \npeople wearing spectacles for reading books or papers. He thought, “If I have spectacles, I \ncan also read like these people. I must go to town and buy a pair of spectacles for myself.” \nSo one day he went to a town. He entered a spectacles shop He asked the shopkeeper for a \npair of spectacles for reading. The shopkeeper gave him various pairs of spectacles and a \nbook. The villager tried all the spectacles one by one. But he could not read anything. He \ntold the shopkeeper that all those spectacles were useless for him. The shopkeeper gave \nhim a doubtful look. Then he looked at the book. It was upside down! The shopkeeper said, \n“Perhaps you don’t know how to read.” \nThe villager said, “No, I don’t. I want to buy spectacles so that I can read like others. But I'), Document(id='a2eecffa-2c7b-4316-a1c1-834e3b610381', metadata={'producer': 'Microsoft® Word 2010', 'creator': 'Microsoft® Word 2010', 'creationdate': '2012-09-11T20:35:09+05:30', 'author': 'Pavithra', 'moddate': '2012-09-11T20:35:09+05:30', 'source': '/Users/kajal.gupta/Documents/Tricon-AI/AI-Engineering/kajal/rag/short-stories-for-children.pdf', 'total_pages': 44, 'page': 2, 'page_label': '3'}, page_content='THE WOODEN BOWL ........................................................................................................................ 24 \nTREES THAT WOOD ........................................................................................................................... 25 \nPENCIL ............................................................................................................................................... 27 \nDAD’S BLESSINGS .............................................................................................................................. 28 \nTHE GREEDY CLOUD .......................................................................................................................... 29 \nA MAD MAN IN THE CITY .................................................................................................................. 29 \nNEVER MAKE FUN OF A RHINO ......................................................................................................... 31 \nTHE MATH DUNCE ............................................................................................................................ 32 \nTHE WHITE ROSE ............................................................................................................................... 33 \nTHE RUBY THIEF ................................................................................................................................ 34')]
# In the story "WORK IS WORSHIP," a hungry grasshopper in winter asks ants for food, as he hasn't eaten since yesterday. An ant asks what he did all summer, to which the grasshopper replies he spent the time singing and didn't store any food. The ant then tells him to "dance the winter away," and the grasshopper walks away sadly. The story concludes with the moral "Work is real worship."'''