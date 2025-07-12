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
from openai import OpenAI

from datetime import datetime

class RAGForChatBot():

  def __init__(self, documents=None, llm=None, embedding_model=None, prompt_template=None, splitter=None, chunk_size=1000, overlap=200, n_chunks_to_pass=10, save_vdb=True, save_vdb_path='faiss_database_of_documents', vectorstore=None, make_db=False):

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
      self.make_db = make_db
      self.vectorstore = vectorstore

      self._configure_everything()

  def _configure_everything(self):
      if self.make_db:
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
    print(type(args_for_template), type(template), type(self.llm))
    return chain.invoke(query)

def make_rag(db_path='docs', make_db=False, documents=None, key=''):
  llm = ChatOpenAI(openai_api_key=key, model_name="gpt-4o-mini", temperature=0)
  embedding = OpenAIEmbeddings(api_key=key, model="text-embedding-3-small")
  splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
  if make_db:
    loader = UnstructuredWordDocumentLoader('documents.docx', encoding='utf-8')
    documents = loader.load()
    chunks = splitter.split_documents(documents)
    vectorstore = FAISS.from_documents(documents=chunks[:5], embedding=embedding)
    batch_size = 100
    for i in range(5, len(chunks), batch_size):
      batch = chunks[i:i+batch_size]
      vectorstore.add_documents(batch)
    vectorstore.save_local('docs')
    #retriever = vectorstore.as_retriever(search_kwargs={'k':10})
  else:
    print(datetime.now())
    vectorstore = FAISS.load_local('docs', embedding, allow_dangerous_deserialization=True)
  return RAGForChatBot(documents='documents.docx', llm=llm, embedding_model=embedding, prompt_template=None, splitter=splitter, vectorstore=vectorstore)

def get_answer_to_query(query, system_prompt, rag_model):
    answer = rag_model.get_answer(query=query, prompt_template=system_prompt)
    return answer.content

def make_prompt(face='физических лиц', history='Отсутствует', acc_data='', label='4'):

    prefix = f"""
    Ты — интеллектуальный помощник службы поддержки, обученный на внутренней документации тепловой электростанции (ТЭС), нормативно-правовых актах, технических регламентах, пользовательских инструкциях и архиве обращений.

    Твоя задача — помогать пользователям с вопросами, связанными с функционированием, обслуживанием, правовым регулированием и пользовательскими сервисами ТЭС, используя только те данные, которые предоставлены в документах ниже.

    В этом запросе указано, что он относится к следующему типу: {label}.
    Следуй следующим правилам:
   1. **Используй только предоставленную информацию.** Не выдумывай факты и не делай догадок, если данные отсутствуют.
   2. **Если ответ очевиден в контексте — дай его полно и точно.** Если в контексте присутствует частичная информация — сделай взвешенное обобщение с указанием возможных ограничений.
   3. **Если информация отсутствует — прямо скажи, что в документах ничего не указано.**
   4. **При наличии нормативных ссылок (дат, номеров, законов) — приводи их дословно.**
   5. **Стиль ответа:** вежливый, нейтральный, понятный. Пиши как сотрудник службы поддержки, обращайся на "Вы".
   6. **В документах есть информация как для физических, так и для юридических лиц. Тебе нужно тщательно вычленить информацию только для {face}. Не добавляй никакой информации о других лиц, если этого явно не указано в запросе пользователя.
    Отвечай только для {face}.
    Важно! .
    """

    if label == "1. Жалоба пользователя":
        prefix += """
        Используй извинительный тон. Вырази сожаление и, если возможно, предложи решение. Важно! Если решение не найдено — сообщи, что специалисты займутся проблемой.
        """
    elif label == "2. Запрос на выдачу информации из личного кабинета":
        prefix += """
        Посмотри на данные из личного кабинета, указанные ниже. Сообщи пользователю нужную информацию. Если данных нет — скажи об этом с сожалением.
        """
    elif label == "3. Запрос на отправку информации в личный кабинет":
        prefix += """
        Сообщи, что пользователь может отправить данные в личный кабинет на сайте или через кнопку "Загрузить данные или показатели" в чате.
        """
    elif label == "5. Вызов оператора":
        prefix += """
        Используй доброжелательный, радостный тон. Сообщи, что оператор скоро подключится в чат.
        """
    elif label == "6. Бессмысленный вопрос":
        prefix += '''
        Максимально вежливо вырази свое сожаление о том, что ты не понял вопроса и попроси
        пользователя переформулировать вопрос. Больше ничего не выводи и не пиши.
        '''
        
    context = """
    Вот выдержки из внутренних документов, которые необходимо использовать:
    {docs}
    """

    lk_context = f"""
    Также пользователь может интересоваться своими данными из личного кабинета. Они включают в себя историю потребления горячей воды, электроэнергии и отопления, баланс, номер лицевого счёта (для физических лиц) или ИНН (для юридических лиц). Если баланс отрицательный — это долг. Данные:
    {acc_data}
    """

    history_block = f"""
    История предыдущих обращений:
    {history}
    Учитывай взаимосвязь между предыдущими и текущим запросом. Например, если пользователь спрашивает: "Сколько стоит куб воды?", а затем: "А электроэнергии?", то второй ответ должен учитывать первый.
    """

    postfix = """
    Сформулируй краткий, точный и полезный ответ. Если требуется — перечисли шаги. Если пользователь расстроен — прояви эмпатию, но оставайся деловым.

    Отвечай на русском языке. Не добавляй ничего, что не подтверждено в документах.
    Формулы передавай в читаемом виде, например:
    Расход = Объём / Время * Тариф

    Вопрос пользователя:
    {query}

    Ответ:
    """

    template = prefix + context + lk_context + history_block + postfix
    return ChatPromptTemplate.from_template(template)




def classifier(key, query):
  classificantion_prompt = f'''
  Ты - специализированный классификатор запросов для сервиса тепловой электростанции. Твоя задача - точно определить категорию каждого запроса пользователя согласно строгим критериям.

  Доступные классы (использовать строго в этой формулировке):
  1. Жалоба пользователя
  2. Запрос на выдачу информации из личного кабинета
  3. Запрос на отправку информации в личный кабинет
  4. Вопрос, требующий контекста из правовых документов
  5. Вызов оператора
  6. Бессмысленный вопрос

  Критерии классификации:
  1. "Жалоба пользователя" - если запрос содержит:
    - выражения недовольства ("почему такие высокие тарифы?")
    - претензии ("у меня неправильно начисляют платежи")
    - жалобы ("плохо работает личный кабинет")
    - "негативные вопросы" ("Почему у меня не работает электроснабжение")

  2. "Запрос на выдачу информации из личного кабинета" - если запрашивается:
    - данные о долгах/платежах
    - история потребления (горячей воды, электроэнергии, отопления)
    - текущие тарифы и начисления
    - персональные данные из профиля
    - пользователь спрашивает про личную информацию о себе

  3. "Запрос на отправку информации в личный кабинет" - если требуется:
    - передать показания счетчиков
    - загрузить документы
    - обновить персональные данные

  4. "Вопрос, требующий контекста из правовых документов" - ВСЕ вопросы, которые:
    - не относятся к классам 1-3 и 5
    - касаются нормативов, тарифообразования
    - требуют ссылок на законодательство
    - относятся к общим правилам оказания услуг

  5. "Вызов оператора" - только при явных просьбах:
    - "соедините с оператором"
    - "хочу поговорить с живым человеком"
    - "переведите на специалиста"

  6. "Бессмысленный вопрос" - все вопросы, не имеющие отношения к предыдущим темам:
    - Не относятся к классам 1-5
    - Состоят из одного слова
    - Не относятся к тематике классов 2-4
  Важно:
  - По умолчанию неясные запросы относить к классу 4
  - Не добавлять никаких пояснений к ответу
  - Использовать только точные формулировки классов как указано выше

  Формат ответа:
  Только номер и точное название класса, например: "2. Запрос на выдачу информации из личного кабинета"

  Запрос пользователя: {query}
    '''



  client = OpenAI(api_key=key)

  response = client.chat.completions.create(
      model="gpt-4o-mini",
      messages=[
          {"role": "system", "content": classificantion_prompt},
          {"role": "user", "content": query}
      ]
  )
  return response.choices[0].message.content


def human_query_to_gpt_prompt(key, query):
    system_prompt = '''
    Ты - профессиональный оптимизатор пользовательских запросов. Твоя задача - принимать необработанные запросы пользователей и преобразовывать их в четкие, структурированные и максимально понятные формулировки.

    Правила работы:
    1. Сохраняй исходный смысл запроса
    2. Улучшай формулировку, делая ее:
      - Грамотной и литературной
      - Конкретной и однозначной
      - Логически структурированной
    3. Раскрывай подразумеваемую суть запроса
    4. Устраняй все неоднозначности
    5. Сохраняй вежливый тон
    6. Ни в коем случае не придумывай ничего своего, не добавляй дополнительной информации к запросу.
    7. Текст ответа должен быть в юридическом стиле
    8. Не выводи ничего, кроме улучшенного запроса, не приводи никаких пояснений.


    Теперь обработай этот запрос:
    [Здесь будет запрос пользователя]
    '''
    client = OpenAI(api_key=key)

    response = client.chat.completions.create(
          model="gpt-4o-mini",
          messages=[
              {"role": "system", "content": system_prompt},
              {"role": "user", "content": query}
              ]
      )
    return response.choices[0].message.content