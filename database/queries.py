from sqlalchemy.orm import Session
from database.models import Log

def add_log(session: Session, user_id: int, question: str, response: str, question_label: str):
    log = Log(user_id=user_id, question=question, response=response, question_label=question_label)
    session.add(log)
    session.commit()
    session.refresh(log)
    return log

def get_last_question(session: Session, user_id: int):
    return session.query(Log)\
        .filter(Log.user_id == user_id)\
        .order_by(Log.timestamp.desc())\
        .first()

def get_last_n_questions(session: Session, user_id: int, n=10):
    return session.query(Log)\
        .filter(Log.user_id == user_id)\
        .order_by(Log.timestamp.desc())\
        .limit(n)\
        .all()

# Пример использования результатов:
# session = Session()
# 
# latest = get_last_question(session, user_id=123)
# print(latest.question)
# 
# recent = get_last_n_questions(session, user_id=123, n=5)
# for log in recent:
#     print(log.question)