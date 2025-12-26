from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from passlib.context import CryptContext
import models


# ===== USER CRUD =====

def get_user(db: Session, user_id: int) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[models.User]:
    return db.query(models.User).offset(skip).limit(limit).all()


def create_user(db: Session, user_data: dict) -> models.User:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    user_data['password'] = pwd_context.hash(user_data['password'])

    db_user = models.User(**user_data)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user(db: Session, user_id: int, user_data: dict) -> Optional[models.User]:
    db_user = get_user(db, user_id)
    if not db_user:
        return None

    for field, value in user_data.items():
        setattr(db_user, field, value)

    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user(db: Session, user_id: int) -> bool:
    db_user = get_user(db, user_id)
    if not db_user:
        return False
    db.delete(db_user)
    db.commit()
    return True


def get_organisation(db: Session, org_id: int) -> Optional[models.Organisation]:
    return db.query(models.Organisation).filter(models.Organisation.id == org_id).first()


def get_organisations(db: Session, skip: int = 0, limit: int = 100) -> List[models.Organisation]:
    return db.query(models.Organisation).offset(skip).limit(limit).all()


def create_organisation(db: Session, org_data: dict) -> models.Organisation:
    db_org = models.Organisation(**org_data)
    db.add(db_org)
    db.commit()
    db.refresh(db_org)
    return db_org


def update_organisation(db: Session, org_id: int, org_data: dict) -> Optional[models.Organisation]:
    db_org = get_organisation(db, org_id)
    if not db_org:
        return None

    for field, value in org_data.items():
        setattr(db_org, field, value)

    db.commit()
    db.refresh(db_org)
    return db_org


def delete_organisation(db: Session, org_id: int) -> bool:
    db_org = get_organisation(db, org_id)
    if not db_org:
        return False
    db.delete(db_org)
    db.commit()
    return True


def get_vacancy(db: Session, vacancy_id: int) -> Optional[models.Vacancy]:
    return db.query(models.Vacancy).filter(models.Vacancy.id == vacancy_id).first()


def get_vacancies(db: Session, skip: int = 0, limit: int = 100, employer_id: Optional[int] = None) -> List[
    models.Vacancy]:
    query = db.query(models.Vacancy)
    if employer_id:
        query = query.filter(models.Vacancy.employer_id == employer_id)
    return query.offset(skip).limit(limit).all()


def create_vacancy(db: Session, vacancy_data: dict) -> models.Vacancy:
    db_vacancy = models.Vacancy(**vacancy_data)
    db.add(db_vacancy)
    db.commit()
    db.refresh(db_vacancy)
    return db_vacancy


def update_vacancy(db: Session, vacancy_id: int, vacancy_data: dict) -> Optional[models.Vacancy]:
    db_vacancy = get_vacancy(db, vacancy_id)
    if not db_vacancy:
        return None

    for field, value in vacancy_data.items():
        setattr(db_vacancy, field, value)

    db.commit()
    db.refresh(db_vacancy)
    return db_vacancy


def delete_vacancy(db: Session, vacancy_id: int) -> bool:
    db_vacancy = get_vacancy(db, vacancy_id)
    if not db_vacancy:
        return False
    db.delete(db_vacancy)
    db.commit()
    return True


def get_message(db: Session, message_id: int) -> Optional[models.Message]:
    return db.query(models.Message).filter(models.Message.id == message_id).first()


def get_user_messages(db: Session, user_id: int, sent: bool = True) -> List[models.Message]:
    if sent:
        return db.query(models.Message).filter(models.Message.sender_id == user_id).all()
    else:
        return db.query(models.Message).filter(models.Message.recipient_id == user_id).all()


def create_message(db: Session, sender_id: int, message_data: dict) -> models.Message:
    db_message = models.Message(sender_id=sender_id, **message_data)
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message


def update_message(db: Session, message_id: int, content: str) -> Optional[models.Message]:
    db_message = get_message(db, message_id)
    if not db_message:
        return None

    db_message.content = content
    db_message.last_edit = datetime.utcnow()
    db.commit()
    db.refresh(db_message)
    return db_message


def delete_message(db: Session, message_id: int) -> bool:
    db_message = get_message(db, message_id)
    if not db_message:
        return False
    db.delete(db_message)
    db.commit()
    return True


def get_application(db: Session, application_id: int) -> Optional[models.Application]:
    return db.query(models.Application).filter(models.Application.id == application_id).first()


def get_user_applications(db: Session, user_id: int) -> List[models.Application]:
    return db.query(models.Application).filter(models.Application.user_id == user_id).all()


def get_vacancy_applications(db: Session, vacancy_id: int) -> List[models.Application]:
    return db.query(models.Application).filter(models.Application.vacancy_id == vacancy_id).all()


def create_application(db: Session, user_id: int, application_data: dict) -> models.Application:
    db_application = models.Application(user_id=user_id, **application_data)
    db.add(db_application)
    db.commit()
    db.refresh(db_application)
    return db_application


def update_application(db: Session, application_id: int, application_data: dict) -> Optional[models.Application]:
    db_application = get_application(db, application_id)
    if not db_application:
        return None

    for field, value in application_data.items():
        setattr(db_application, field, value)

    db.commit()
    db.refresh(db_application)
    return db_application


def delete_application(db: Session, application_id: int) -> bool:
    db_application = get_application(db, application_id)
    if not db_application:
        return False
    db.delete(db_application)
    db.commit()
    return True


def get_user_bookmarks(db: Session, user_id: int) -> List[models.Bookmark]:
    return db.query(models.Bookmark).filter(models.Bookmark.user_id == user_id).all()


def create_bookmark(db: Session, user_id: int, vacancy_id: int) -> models.Bookmark:
    # Check if bookmark already exists
    existing = db.query(models.Bookmark).filter(
        models.Bookmark.user_id == user_id,
        models.Bookmark.vacancy_id == vacancy_id
    ).first()

    if existing:
        return existing

    db_bookmark = models.Bookmark(user_id=user_id, vacancy_id=vacancy_id)
    db.add(db_bookmark)
    db.commit()
    db.refresh(db_bookmark)
    return db_bookmark


def delete_bookmark(db: Session, user_id: int, vacancy_id: int) -> bool:
    db_bookmark = db.query(models.Bookmark).filter(
        models.Bookmark.user_id == user_id,
        models.Bookmark.vacancy_id == vacancy_id
    ).first()

    if not db_bookmark:
        return False

    db.delete(db_bookmark)
    db.commit()
    return True


def get_media(db: Session, media_id: int) -> Optional[models.Media]:
    return db.query(models.Media).filter(models.Media.id == media_id).first()


def create_media(db: Session, media_data: dict) -> models.Media:
    db_media = models.Media(**media_data)
    db.add(db_media)
    db.commit()
    db.refresh(db_media)
    return db_media


def delete_media(db: Session, media_id: int) -> bool:
    db_media = get_media(db, media_id)
    if not db_media:
        return False
    db.delete(db_media)
    db.commit()
    return True


def add_message_media(db: Session, message_id: int, media_id: int) -> models.MessageMedia:
    db_mm = models.MessageMedia(message_id=message_id, media_id=media_id)
    db.add(db_mm)
    db.commit()
    db.refresh(db_mm)
    return db_mm


def add_vacancy_media(db: Session, vacancy_id: int, media_id: int) -> models.VacancyMedia:
    db_vm = models.VacancyMedia(vacancy_id=vacancy_id, media_id=media_id)
    db.add(db_vm)
    db.commit()
    db.refresh(db_vm)
    return db_vm


def add_application_media(db: Session, application_id: int, media_id: int) -> models.ApplicationMedia:
    db_am = models.ApplicationMedia(application_id=application_id, media_id=media_id)
    db.add(db_am)
    db.commit()
    db.refresh(db_am)
    return db_am