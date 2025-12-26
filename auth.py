from datetime import datetime, timedelta
from typing import Optional, Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.orm import Session
import models
from models import get_db

# Configuration
SECRET_KEY = "SECRETKEYCHANGELOL"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 900

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")


# ===== Schemas =====

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: Optional[int] = None


class UserLogin(BaseModel):
    email: str
    password: str


# ===== Role Enum for clarity =====

class Role:
    STUDENT = 0
    AGENT = 1
    ADMIN = 2


# ===== Password Hashing =====

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


# ===== JWT Token Functions =====

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def authenticate_user(db: Session, email: str, password: str) -> Optional[models.User]:
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user or not verify_password(password, user.password):
        return None
    return user


# ===== Dependency: Get Current User =====

async def get_current_user(
        token: Annotated[str, Depends(oauth2_scheme)],
        db: Session = Depends(get_db)
) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user


# ===== Authorization Checks =====

def require_role(required_role: int):
    """Dependency that requires a minimum role level"""

    async def role_checker(current_user: models.User = Depends(get_current_user)):
        if current_user.role < required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {required_role}"
            )
        return current_user

    return role_checker


def require_student(current_user: models.User = Depends(get_current_user)):
    """Any authenticated user"""
    return current_user


def require_agent(current_user: models.User = Depends(get_current_user)):
    """Agents and Admins only"""
    if current_user.role < Role.AGENT:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Agent privileges required")
    return current_user


def require_admin(current_user: models.User = Depends(get_current_user)):
    """Admins only"""
    if current_user.role < Role.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")
    return current_user


# ===== Permission Checks (Business Logic) =====

def can_view_user(current_user: models.User, target_user_id: int, db: Session) -> bool:
    """
    Students: Only their own profile
    Agents: Own profile + students who applied to their org's vacancies
    Admins: Everyone
    """
    if current_user.role == Role.ADMIN:
        return True

    if current_user.id == target_user_id:
        return True

    if current_user.role == Role.AGENT:
        # Check if target user is a student who applied to agent's org vacancies
        target_user = db.query(models.User).filter(models.User.id == target_user_id).first()
        if not target_user or target_user.role != Role.STUDENT:
            return False

        # Check if student has applications to this agent's org
        has_application = db.query(models.Application).join(
            models.Vacancy
        ).filter(
            models.Application.user_id == target_user_id,
            models.Vacancy.employer_id == current_user.org_id
        ).first()

        return has_application is not None

    return False


def can_modify_user(current_user: models.User, target_user_id: int) -> bool:
    """Only admins or the user themselves can modify user data"""
    return current_user.role == Role.ADMIN or current_user.id == target_user_id


def can_modify_vacancy(current_user: models.User, vacancy: models.Vacancy) -> bool:
    """Agents can modify their org's vacancies, Admins can modify any"""
    if current_user.role == Role.ADMIN:
        return True
    if current_user.role == Role.AGENT:
        return vacancy.employer_id == current_user.org_id
    return False


def can_modify_application(current_user: models.User, application: models.Application) -> bool:
    """Students can modify their own applications, Admins can modify any"""
    if current_user.role == Role.ADMIN:
        return True
    if current_user.role == Role.STUDENT:
        return application.user_id == current_user.id
    return False


def can_modify_organisation(current_user: models.User, org_id: int) -> bool:
    """Agents can modify their own org, Admins can modify any"""
    if current_user.role == Role.ADMIN:
        return True
    if current_user.role == Role.AGENT:
        return current_user.org_id == org_id
    return False