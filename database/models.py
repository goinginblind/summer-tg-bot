from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True)  # Telegram user ID
    face_type = Column(String, nullable=True)
    face_number = Column(Integer, nullable=True)

    logs = relationship("UserLog", back_populates="user")

class UserLog(Base):
    __tablename__ = "user_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    question = Column(Text, nullable=False)
    question_label = Column(String, nullable=False)
    response = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.now)

    user = relationship("User", back_populates="logs")
