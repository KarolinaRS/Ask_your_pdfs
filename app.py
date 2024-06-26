import streamlit as st
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.embeddings import OpenAIEmbeddings
from langchain.vectorstores.faiss import FAISS
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from langchain.chat_models import ChatOpenAI
from htmlTemplated import css, bot_template, user_template


def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text

def get_text_chunks(text):
    text_spliter =CharacterTextSplitter(
        separator='\n',
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    chunks = text_spliter.split_text(text)
    return chunks

def get_vectorstore(text_chunks, openai_api_key):
    embeddings = OpenAIEmbeddings(openai_api_key = openai_api_key)
    vectorstore = FAISS.from_texts(texts=text_chunks, embedding=embeddings)
    return vectorstore

def get_conversation_chain(vectorstore, openai_api_key):
    llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo-0613", openai_api_key= openai_api_key, streaming=True
    )
    memory = ConversationBufferMemory(memory_key='chat_history', return_messages=True)


    conversation_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectorstore.as_retriever(),
        memory=memory
    )
    return conversation_chain

def handle_userinput(user_question):
    response = st.session_state.conversation({'question': user_question})
    st.session_state.chat_history = response['chat_history']

    for i, message in enumerate(st.session_state.chat_history):
        if i % 2 == 0:
            st.write(user_template.replace("{{MSG}}", message.content), unsafe_allow_html=True)
        else:
            st.write(bot_template.replace("{{MSG}}", message.content), unsafe_allow_html=True)
    


def main():
    st.set_page_config(page_title="Chat with multiple PDFs", page_icon=':books:')
    st.write(css, unsafe_allow_html=True)

    if "conversation" not in st.session_state:
        st.session_state.conversation = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = None

    st.header("Chat with multiple PDFs :books:") 
    user_question = st.text_input("Ask a question about your documents:")
    
    if user_question:
        handle_userinput(user_question)
    
    with st.sidebar:
        "[Get an OpenAI API key](https://platform.openai.com/account/api-keys)"

        openai_api_key = st.session_state.get("openai_api_key", None)
        if openai_api_key is None:
            openai_api_key = st.text_input('Enter your OPENAI_API_KEY: ', type='password')
            if not openai_api_key:
                st.warning('Please, enter your OPENAI_API_KEY', icon='⚠️')
                stop = True
            else:
                st.success('Upload your PDFs and ask them what you want!', icon='👉')
                st.session_state["openai_api_key"] = openai_api_key

        st.subheader("Your documents")
        pdf_docs = st.file_uploader("Upload your PDFs here and click on 'Process'", accept_multiple_files=True)
        if st.button("Process"):
            with st.spinner("Processing"):
                #get a pdf text
                raw_text = get_pdf_text(pdf_docs)
    
                #get the text chunks
                text_chunks = get_text_chunks(raw_text)
                #st.write(text_chunks)
                
                #create vector store
                vectorstore  = get_vectorstore(text_chunks, openai_api_key)
                
                # coversation chain
                st.session_state.conversation = get_conversation_chain(vectorstore, openai_api_key)
    
                #client = OpenAI(api_key=openai_api_key)


if __name__ == '__main__':
    main()