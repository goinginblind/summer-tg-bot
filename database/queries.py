from sqlalchemy.orm import Session
from models import User, UserLog
from datetime import datetime

def get_user(session: Session, user_id: int) -> User | None:
    return session.query(User).filter_by(user_id=user_id).first()

def create_user(session: Session, user_id: int, face_type: str):
    user = User(user_id=user_id, face_type=face_type)
    session.add(user)
    session.commit()

def update_user_face(session: Session, user_id: int, face_type: str, face_number: int):
    user = session.query(User).filter_by(user_id=user_id).first()
    if user:
        user.face_type = face_type
        user.face_number = face_number
        session.commit()

def set_face_number(session: Session, user_id: int, face_number: int):
    user = session.query(User).filter_by(user_id=user_id).first()
    if user:
        user.face_number = face_number
        session.commit()

def add_log(session: Session, user_id: int, question: str, question_label: str, response: str):
    log = UserLog(
        user_id=user_id,
        question=question,
        question_label=question_label,
        response=response,
        timestamp=datetime.utcnow()
    )
    session.add(log)
    session.commit()

def get_last_n_questions(session: Session, user_id: int, n: int = 10):
    return session.query(UserLog)\
        .filter_by(user_id=user_id)\
        .order_by(UserLog.timestamp.desc())\
        .limit(n)\
        .all()
