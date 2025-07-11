from sqlalchemy import select, insert, update
from database.models import User, UserLog
from datetime import datetime

def get_user(session, user_id):
    return session.query(User).filter_by(user_id=user_id).first()

def create_user(session, user_id, face_type):
    user = User(user_id=user_id, face_type=face_type)
    session.add(user)
    session.commit()

def set_face_number(session, user_id, face_number):
    session.query(User).filter_by(user_id=user_id).update({User.face_number: face_number})
    session.commit()

def add_log(session, user_id, question, question_label, response):
    log = UserLog(
        user_id=user_id,
        question=question,
        question_label=question_label,
        response=response,
        timestamp=datetime.now()
    )
    session.add(log)
    session.commit()

def get_last_n_questions(session, user_id, n=10):
    return (
        session.query(UserLog)
        .filter_by(user_id=user_id)
        .order_by(UserLog.timestamp.desc())
        .limit(n)
        .all()
    )
