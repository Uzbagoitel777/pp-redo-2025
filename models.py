from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

DATABASE_URL = 'sqlite:///./database.db'
engine = create_engine(DATABASE_URL, connect_args={'check_same_thread': False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


@event.listens_for(engine, "connect")
def enable_sqlite_foreign_keys(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    fname = Column(String)
    lname = Column(String)
    pname = Column(String, nullable=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    role = Column(Boolean)
    icon_id = Column(Integer, ForeignKey('media.id', ondelete='SET NULL'), nullable=True)
    registred = Column(DateTime, default=datetime.utcnow)
    org_id = Column(Integer, ForeignKey('organisations.id', ondelete='SET NULL'), nullable=True)

    # Relationships
    sent_messages = relationship('Message', foreign_keys='Message.sender_id', back_populates='sender')
    received_messages = relationship('Message', foreign_keys='Message.recipient_id', back_populates='recipient')
    bookmarks = relationship('Bookmark', back_populates='user', cascade='all, delete-orphan')
    applications = relationship('Application', back_populates='user', cascade='all, delete-orphan')
    icon = relationship('Media', foreign_keys=[icon_id])
    organisation = relationship('Organisation', foreign_keys=[org_id], back_populates='members')


class Vacancy(Base):
    __tablename__ = "vacancies"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    employer_id = Column(Integer, ForeignKey('organisations.id', ondelete='CASCADE'))
    title = Column(String, unique=True)
    brief = Column(String, nullable=True)
    description = Column(Text)
    icon_id = Column(Integer, ForeignKey('media.id', ondelete='SET NULL'))
    salary_top = Column(Float, nullable=True)
    salary_bottom = Column(Float, nullable=True)
    required_year = Column(Integer, nullable=True)
    created = Column(DateTime, default=datetime.utcnow)
    status = Column(Integer)

    # Relationships
    employer = relationship('Organisation', back_populates='vacancies')
    bookmarks = relationship('Bookmark', back_populates='vacancy', cascade='all, delete-orphan')
    vacancy_media = relationship('VacancyMedia', back_populates='vacancy', cascade='all, delete-orphan')
    applications = relationship('Application', back_populates='vacancy', cascade='all, delete-orphan')
    icon = relationship('Media', foreign_keys=[icon_id])

class Organisation(Base):
    __tablename__ = 'organisations'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String)
    description = Column(Text)
    icon_id = Column(Integer, ForeignKey('media.id', ondelete='SET NULL'), nullable=True)

    vacancies = relationship('Vacancy', back_populates='employer')
    members = relationship('User', back_populates='organisation')
    icon = relationship('Media', foreign_keys=[icon_id])


class Media(Base):
    __tablename__ = 'media'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String)
    path = Column(String)
    added = Column(DateTime, default=datetime.utcnow)

    message_media = relationship('MessageMedia', back_populates='media', cascade='all, delete-orphan')
    vacancy_media = relationship('VacancyMedia', back_populates='media', cascade='all, delete-orphan')
    application_media = relationship('ApplicationMedia', back_populates='media', cascade='all, delete-orphan')


class Message(Base):
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    content = Column(String)
    sent = Column(DateTime, default=datetime.utcnow)
    last_edit = Column(DateTime, nullable=True)
    sender_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    recipient_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))

    sender = relationship('User', foreign_keys=[sender_id], back_populates='sent_messages')
    recipient = relationship('User', foreign_keys=[recipient_id], back_populates='received_messages')
    message_media = relationship('MessageMedia', back_populates='message', cascade='all, delete-orphan')


class Bookmark(Base):
    __tablename__ = 'bookmarks'

    vacancy_id = Column(Integer, ForeignKey('vacancies.id', ondelete='CASCADE'), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)

    user = relationship('User', back_populates='bookmarks')
    vacancy = relationship('Vacancy', back_populates='bookmarks')


class MessageMedia(Base):
    __tablename__ = 'messagemedia'

    media_id = Column(Integer, ForeignKey('media.id', ondelete='CASCADE'), primary_key=True)
    message_id = Column(Integer, ForeignKey('messages.id', ondelete='CASCADE'), primary_key=True)

    media = relationship('Media', back_populates='message_media')
    message = relationship('Message', back_populates='message_media')


class VacancyMedia(Base):
    __tablename__ = 'vacancymedia'

    vacancy_id = Column(Integer, ForeignKey('vacancies.id', ondelete='CASCADE'), primary_key=True)
    media_id = Column(Integer, ForeignKey('media.id', ondelete='CASCADE'), primary_key=True)

    vacancy = relationship('Vacancy', back_populates='vacancy_media')
    media = relationship('Media', back_populates='vacancy_media')


class Application(Base):
    __tablename__ = 'applications'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    vacancy_id = Column(Integer, ForeignKey('vacancies.id', ondelete='CASCADE'))
    title = Column(String)
    content = Column(String)

    user = relationship('User', back_populates='applications')
    vacancy = relationship('Vacancy', foreign_keys=[vacancy_id], back_populates='applications')
    application_media = relationship('ApplicationMedia', back_populates='application')


class ApplicationMedia(Base):
    __tablename__ = 'applicationmedia'

    media_id = Column(Integer, ForeignKey('media.id', ondelete='CASCADE'), primary_key=True)
    application_id = Column(Integer, ForeignKey('applications.id', ondelete='CASCADE'), primary_key=True)

    media = relationship('Media', back_populates='application_media')
    application = relationship('Application', back_populates='application_media')


Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
