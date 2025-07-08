import numpy as np
# import pandas as pd
# import torch
# import transformers
import langchain
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import UnstructuredWordDocumentLoader
from langchain_core.runnables import RunnablePassthrough
from langchain.chains import RetrievalQA
from langchain.prompts import ChatPromptTemplate
import os
import openai

class RAGForChatBot():

  def __init__(self, key=None, documents=None, llm=None, embedding_model=None, prompt_template=None, splitter=None, chunk_size=1000, overlap=200, n_chunks_to_pass=10, save_vdb=True, save_vdb_path='faiss_database_of_documents'):

      if documents:
        self.docs = documents
      else:
        raise ValueError('Please provide a path to documents')
      if llm:
        self.llm = llm
      else:
        raise ValueError('Please provide a model to use for text generation')
      if embedding_model:
        self.embedding_model = embedding_model
      else:
        raise ValueError('Please provide a model to use for embeddings calculations')
      self.splitter = splitter if splitter else None
      self.prompt_template = prompt_template if prompt_template else None
      self.chunk_size = chunk_size
      self.overlap = overlap
      self.save_vdb = save_vdb
      self.save_vdb_path = save_vdb_path
      self.n_chunks_to_pass = n_chunks_to_pass

      self._configure_everything()
      
  def _configure_everything(self):
      self.loader = UnstructuredWordDocumentLoader(self.docs)
      self.documents = self.loader.load()
      if self.splitter:
        self.chunks = self.splitter.split_documents(self.documents)
      else:
        self.splitter = RecursiveCharacterTextSplitter(chunk_size=self.chunk_size, chunk_overlap=self.overlap)
        self.chunks = self.splitter.split_documents(self.documents)  
      self.vectorstore = FAISS.from_documents(documents=self.chunks[:5], embedding=self.embedding_model)
      batch_size = 100
      for i in range(5, len(self.chunks), batch_size):
        batch = self.chunks[i:i+batch_size]
        self.vectorstore.add_documents(batch)
      if self.save_vdb:
        self.vectorstore.save_local(self.save_vdb_path)
      self.retriever = self.vectorstore.as_retriever(search_kwargs={'k':self.n_chunks_to_pass})
      print('configuration is completed successfully')
      return None

  def get_answer(self, query:str, prompt_template=None, args=None):
    if prompt_template:
      template = prompt_template 
    else:
      template = self.prompt_template if self.prompt_template else None
    if not template:
      raise ValueError('No prompt template was provided therefore cannot execute answering the question')
    args_for_template = {'docs':self.retriever, 'query':RunnablePassthrough()}
    if args:
      print('args')
      for k, v in args:
        args_for_template[k]=v
    chain = (
    args_for_template
    | template
    | self.llm

      )
    return chain.invoke(query)

def make_rag(key):
  loader = UnstructuredWordDocumentLoader('documents.docx', encoding='utf-8')
  documents = loader.load()
  splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
  chunks = splitter.split_documents(documents)
  llm = ChatOpenAI(openai_api_key=key, model_name="gpt-4o-mini", temperature=0)
  embedding = OpenAIEmbeddings(api_key=key, model="text-embedding-3-small")
  vectorstore = FAISS.from_documents(documents=chunks[:5], embedding=embedding)
  batch_size = 100
  for i in range(5, len(chunks), batch_size):
    batch = chunks[i:i+batch_size]
    vectorstore.add_documents(batch)
  vectorstore.save_local('docs')
  retriever = vectorstore.as_retriever(search_kwargs={'k':10})
  face = 'физическое лицо'
  template = """
  Ты — интеллектуальный помощник службы поддержки, обученный на внутренней документации тепловой электростанции (ТЭС), нормативно-правовых актах, технических регламентах, пользовательских инструкциях и архиве обращений.

  Твоя задача — **помогать пользователям с вопросами, связанными с функционированием, обслуживанием, правовым регулированием и пользовательскими сервисами ТЭС**, используя только те данные, которые предоставлены в документах ниже.

  Поддерживаемые типы запросов:
  – Технические: сбои, отключения, температура, энергоснабжение, аварийные ситуации
  – Административные: порядок подачи заявлений, сроки рассмотрения, личный кабинет
  – Юридические: компенсации, права потребителей, лицензии, ГОСТы, СНИПы
  – Общие: как подать жалобу, график работ, контактные данные
  Правила ответа:
  1. **Используй только предоставленную информацию.** Не выдумывай факты и не делай догадок, если данные отсутствуют.
  2. **Если ответ очевиден в контексте — дай его полно и точно.** Если в контексте присутствует частичная информация — сделай взвешенное обобщение с указанием возможных ограничений.
  3. **Если информация отсутствует — прямо скажи, что в документах ничего не указано.**
  4. **При наличии нормативных ссылок (дат, номеров, законов) — приводи их дословно.**
  5. **Стиль ответа:** вежливый, нейтральный, понятный. Пиши как сотрудник службы поддержки, обращайся на "Вы".
  6. **В документах есть информация как для физических, так и для юридических лиц. Тебе нужно тщательно вычленить информацию только для физичесмких лиц. Не добавляй никакой информации о другом лице, если этого явно не указано в запросе пользователя.

  Вот выдержки из внутренних документов, которые необходимо использовать:
  {docs}

  Сформулируй краткий, точный и полезный ответ на основе этих материалов.

  Если требуется инструкция — перечисли шаги.
  Если пользователь проявляет эмоции (волнение, недовольство) — постарайся проявить эмпатию, но оставайся деловым.

  **Отвечай на русском языке. Не добавляй ничего, что не подтверждено в источниках. Старайся давать максимально точный и подробный, развернутый ответ, если пользователь не просит иначе.**
  Если в контексте есть формулы, тебе обязательно нужно вывести ее в читаемом текстовом формате, не в виде LaTex.
  В качестве примера вывода формулы предлагаю тебе следующую формулу: что-то = что-то/что-то * что-то. !! используй ее как пример для вывода формулы, замени *что-то* на параметры из контекста
  Тебе нужно дать ответ на следующий вопрос:
  {query}
  Твой ответ с учетом контекста и всех поставленных выше условий:
  """
  prompt_template = ChatPromptTemplate.from_template(template)
  RAGForChatBot(documents='documents.docx', llm=llm, embedding_model=embedding, prompt_template=prompt_template, splitter=splitter)
  return RAGForChatBot(documents='documents.docx', llm=llm, embedding_model=embedding, prompt_template=prompt_template, splitter=splitter)

