from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = 'sqlite:///./database.db'
engine = create_engine(DATABASE_URL, connect_args={'check_same_thread': False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class User(Base):
    __tablename__ = "Users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    fname = Column(String, index=True)
    lname = Column(String, index=True)
    pname = Column(String, nullable=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)


class Vacancy(Base):
    __tablename__ = "Vacancies"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    employer = Column(String, index=True)
    title = Column(String, index=True)
    brief = Column(String, nullable=True)
    description = Column(String, index=True)
    icon_path = Column(String, index=True)
    salary_top = Column(Float)
    salary_bottom = Column(Float)
    required_year = Column(Integer)

Base.metadata.create_all(bind=engine)

