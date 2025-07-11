from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class MockedUserData(Base):
    __tablename__ = "user_data"

    id = Column(Integer, primary_key=True)  # face_number from DB1
    name = Column(String)
    phone_number = Column(String)
    date_of_birth = Column(String)
    
    light_bill = Column(Integer, default=0)
    heat_bill = Column(Integer, default=0)
    electricity_bill = Column(Integer, default=0)
    debt = Column(Integer, default=0)