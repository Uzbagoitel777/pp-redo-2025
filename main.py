import uvicorn
from fastapi import FastAPI, APIRouter, Depends
from sqlalchemy.orm import Session
from db_handler import get_db, User as DBUser
from models import User
from typing import Union, List

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


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)