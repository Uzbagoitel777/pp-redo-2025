from pydantic import BaseModel, field_validator
import db_handler as db

class User(BaseModel):
    id: int = None
    fname: str
    lname: str
    pname: str = None
    email: str
    password: str

    def to_db(self):
        db_user = db.User(
            id=self.id,
            fname=self.fname,
            lname=self.lname,
            pname=self.pname,
            email=self.email,
            password=self.password
        )
        return db_user

    @classmethod
    def from_db(cls, db_user: db.User):
        user = cls(
            id = db_user.id,
            fname = db_user.fname,
            lname = db_user.lname,
            pname = db_user.pname,
            email = db_user.email,
            password = db_user.password
        )
        return user


class Vacancy(BaseModel):
    id: int = None
    employer: str
    title: str
    brief: str = None
    icon_path: str
    salary: (float, float) = (0, 0)

    def to_db(self):
        db_vacancy = db.Vacancy(
            id=self.id,
            employer=self.employer,
            title=self.title,
            brief=self.brief,
            icon_path=self.icon_path,
            salary_top=self.salary[0]
        )
        return db_vacancy

    @classmethod
    def from_db(cls, db_vacancy: db.Vacancy):
        vacancy = cls(
            id = db_vacancy.id,
            employer = db_vacancy.employer,
            title = db_vacancy.title,
            brief = db_vacancy.brief,
            icon_path = db_vacancy.icon_path,
            salary = (db_vacancy.salary_top,db_vacancy.salary_bottom)
        )
        return vacancy