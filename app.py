import streamlit as st
import os
from langchain_groq import ChatGroq
from langchain_community.embeddings import GooglePalmEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

# Load the Groq and OpenAI API Key
os.environ['GOOGLE_API_KEY'] = os.getenv("GOOGLE_API_KEY")
groq_api_key = os.getenv('GROQ_API_KEY')

st.title("Bhagwat-Gita Chatbot")

# Beta message
st.info("This webpage is in beta phase and it will be developed over time.")

# Initialize the ChatGroq model
llm = ChatGroq(groq_api_key=groq_api_key, model_name="llama3-70b-8192")

# Define the prompt template
prompt = ChatPromptTemplate.from_template(
    """
    Answer the questions based on the provided context only.
    Please provide a detailed and thorough response based on the question.
    <context>
    {context}
    <context>
    Questions:{input}
    """
)

# Function to initialize vector embedding and ObjectBox Vectorstore DB
def vector_embedding():
    st.session_state.embeddings = GooglePalmEmbeddings()  # Embeddings instance
    if not os.path.exists('faiss_index'):
        st.session_state.loader = PyPDFDirectoryLoader(r'Document')  # Data Ingestion
        st.session_state.docs = st.session_state.loader.load()  # Document Loading
        st.session_state.text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)  # Chunk Creation
        st.session_state.final_documents = st.session_state.text_splitter.split_documents(st.session_state.docs)  # Splitting
        st.session_state.vectors = FAISS.from_documents(st.session_state.final_documents, st.session_state.embeddings)  # Vector embeddings
        st.session_state.vectors.save_local('faiss_index')
        st.write("ObjectBox Database is ready")
    else:
        st.session_state.vectors = FAISS.load_local("faiss_index", st.session_state.embeddings, allow_dangerous_deserialization=True)

# Ensure that the vector embeddings are loaded once per session
if "vectors" not in st.session_state:
    vector_embedding()

# Input prompt for user question
input_prompt = st.text_input("Enter Your Question From Documents")

# Process the input prompt if provided and search button is pressed
if st.button("Search"):
    if "vectors" not in st.session_state:
        st.warning("Please initialize the document embeddings first by pressing 'Documents Embedding' Button and wait while Database is loading")
    else:
        document_chain = create_stuff_documents_chain(llm, prompt)
        retriever = st.session_state.vectors.as_retriever()
        retrieval_chain = create_retrieval_chain(retriever, document_chain)

        # Measure the response time
        start = time.process_time()
        response = retrieval_chain.invoke({'input': input_prompt})
        st.write("Response time:", time.process_time() - start)
        st.write(response['answer'])

        # Display the relevant document chunks with a Streamlit expander
        with st.expander("Document Similarity Search"):
            for i, doc in enumerate(response["context"]):
                st.write(doc.page_content)
                st.write("--------------------------------")
