import uvicorn
from fastapi import FastAPI, APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from db_handler import get_db, User as DBUser, Vacancy as DBVacancy
from models import User, Vacancy
from typing import Union, List, Optional

app = FastAPI()

user_router = APIRouter(prefix="/api/user", tags=["user"])

@user_router.get("/{user_id}", response_model=Union[User|List[User]])
async def get_users(user_id: int = None, db:Session=Depends(get_db)):
    if user_id:
        user = db.query(DBUser).filter(DBUser.id == user_id)
        return User.from_db(user)
    else:
        users = db.query(DBUser)
        return [User.from_db(user) for user in users]


@user_router.post("/", response_model=User)
async def create_user(user: User, db: Session=Depends(get_db)):
    if user:
        db.add(user.to_db())
        db.commit()
        db.refresh(user.to_db())
    # try:
    #     user = db.query(DBUser).filter(DBUser.email == user.email)
    # except Exception as e:
    #     print(e)
    return user

app.include_router(user_router)

vacancy_router = APIRouter(prefix="/api/vacancy", tags=["vacancy"])


@vacancy_router.post("/", response_model=Vacancy, status_code=201)
async def create_vacancy(vacancy: Vacancy, db_session: Session = Depends(get_db)):
    """Create a new vacancy"""
    db_vacancy = vacancy.to_db()
    db_session.add(db_vacancy)
    db_session.commit()
    db_session.refresh(db_vacancy)
    return Vacancy.from_db(db_vacancy)


@vacancy_router.get("/{vacancy_id}", response_model=Vacancy)
async def get_vacancy(vacancy_id: int, db_session: Session = Depends(get_db)):
    """Retrieve a specific vacancy by ID"""
    db_vacancy = db_session.query(DBVacancy).filter(DBVacancy.id == vacancy_id).first()
    if not db_vacancy:
        raise HTTPException(status_code=404, detail="Vacancy not found")
    return Vacancy.from_db(db_vacancy)


@vacancy_router.get("/", response_model=List[Vacancy])
async def get_vacancies(
        employer: Optional[str] = Query(None),
        title: Optional[str] = Query(None),
        min_salary: Optional[float] = Query(None),
        max_salary: Optional[float] = Query(None),
        max_required_year: Optional[int] = Query(None),
        db_session: Session = Depends(get_db)
):
    """Retrieve all vacancies matching optional filter parameters"""
    query = db_session.query(DBVacancy)

    if employer:
        query = query.filter(DBVacancy.employer.ilike(f"%{employer}%"))

    if title:
        query = query.filter(DBVacancy.title.ilike(f"%{title}%"))

    if min_salary is not None:
        query = query.filter(DBVacancy.salary_top >= min_salary)

    if max_salary is not None:
        query = query.filter(DBVacancy.salary_bottom <= max_salary)

    if max_required_year is not None:
        query = query.filter(DBVacancy.required_year <= max_required_year)

    vacancies = query.all()
    return [Vacancy.from_db(vacancy) for vacancy in vacancies]

app.include_router(vacancy_router)

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)