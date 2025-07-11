from database.mocked_models import MockedUserData

def get_mocked_user_data(session, face_number):
    return session.query(MockedUserData).filter_by(id=face_number).first()

def update_mocked_user_field(session, face_number, field, value):
    user = session.query(MockedUserData).filter_by(id=face_number).first()
    if not user:
        return
    setattr(user, field, value)
    session.commit()
