import uvicorn
from fastapi import FastAPI, APIRouter, Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from models import get_db
from auth import Role
import schemas
import models
import crud
import auth
import logging
from typing import Union, List, Optional
from datetime import timedelta

app = FastAPI(
    title="Stageровка API",
    description="API для сервиса публикации и поиска студенческих стажировок",
    version="0.2.1"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.DEBUG,       # show debug and above
    format="[%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

auth_router = APIRouter(prefix="/api/auth", tags=["authentication"])

@auth_router.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Register a new user (defaults to Student role)"""
    # Check if email already exists
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Hash password
    user_data = user.model_dump()
    logger.debug(user_data['password'])
    user_data['password'] = auth.get_password_hash(user_data['password'])

    # Create user
    db_user = models.User(**user_data)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@auth_router.post("/login", response_model=auth.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login and get access token"""
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@auth_router.get("/me", response_model=schemas.UserResponse)
def get_current_user_info(current_user: models.User = Depends(auth.get_current_user)):
    """Get current authenticated user info"""
    return current_user

app.include_router(auth_router)


user_router = APIRouter(prefix="/api/users", tags=["users"])


@user_router.get("/", response_model=List[schemas.UserResponse])
def list_users(
        skip: int = 0,
        limit: int = 100,
        current_user: models.User = Depends(auth.get_current_user),
        db: Session = Depends(get_db)
):
    """
    List users based on role:
    - Students: Only themselves
    - Agents: Themselves + students who applied to their org
    - Admins: Everyone
    """
    if current_user.role == Role.ADMIN:
        return crud.get_users(db, skip=skip, limit=limit)

    elif current_user.role == Role.AGENT:
        # Get agent themselves + students who applied to their org
        students_with_applications = db.query(models.User).join(
            models.Application
        ).join(
            models.Vacancy
        ).filter(
            models.Vacancy.employer_id == current_user.org_id,
            models.User.role == Role.STUDENT
        ).distinct().all()

        # Include the agent themselves
        result = [current_user] + students_with_applications
        return result[skip:skip + limit]

    else:  # Student
        return [current_user]


@user_router.get("/{user_id}", response_model=schemas.UserDetailed)
def get_user(
        user_id: int,
        current_user: models.User = Depends(auth.get_current_user),
        db: Session = Depends(get_db)
):
    """Get a specific user (with permission check)"""
    if not auth.can_view_user(current_user, user_id, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this user")

    db_user = crud.get_user(db, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@user_router.patch("/{user_id}", response_model=schemas.UserResponse)
def update_user(
        user_id: int,
        user: schemas.UserUpdate,
        current_user: models.User = Depends(auth.get_current_user),
        db: Session = Depends(get_db)
):
    """Update user (self or admin only)"""
    if not auth.can_modify_user(current_user, user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to modify this user")

    update_data = user.model_dump(exclude_unset=True)

    # Hash password if it's being updated
    if 'password' in update_data:
        update_data['password'] = auth.get_password_hash(update_data['password'])

    db_user = crud.update_user(db, user_id, update_data)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@user_router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
        user_id: int,
        current_user: models.User = Depends(auth.require_admin),
        db: Session = Depends(get_db)
):
    """Delete user (admin only)"""
    if not crud.delete_user(db, user_id):
        raise HTTPException(status_code=404, detail="User not found")


app.include_router(user_router)

vacancy_router = APIRouter(prefix="/api/vacancies", tags=["vacancies"])


@vacancy_router.get("/", response_model=List[schemas.VacancyResponse])
def list_vacancies(
        skip: int = 0,
        limit: int = 100,
        employer_id: Optional[int] = None,
        db: Session = Depends(get_db)
):
    """List all vacancies (public endpoint)"""
    return crud.get_vacancies(db, skip=skip, limit=limit, employer_id=employer_id)


@vacancy_router.get("/{vacancy_id}", response_model=schemas.VacancyDetailed)
def get_vacancy(vacancy_id: int, db: Session = Depends(get_db)):
    """Get a specific vacancy (public endpoint)"""
    db_vacancy = crud.get_vacancy(db, vacancy_id)
    if not db_vacancy:
        raise HTTPException(status_code=404, detail="Vacancy not found")
    return db_vacancy


@vacancy_router.post("/", response_model=schemas.VacancyResponse, status_code=status.HTTP_201_CREATED)
def create_vacancy(
        vacancy: schemas.VacancyCreate,
        current_user: models.User = Depends(auth.require_agent),
        db: Session = Depends(get_db)
):
    """Create a vacancy (agents and admins only)"""
    # Agents can only create vacancies for their own org
    if current_user.role == Role.AGENT and vacancy.employer_id != current_user.org_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Can only create vacancies for your organization")

    vacancy_data = vacancy.model_dump()
    return crud.create_vacancy(db, vacancy_data)


@vacancy_router.patch("/{vacancy_id}", response_model=schemas.VacancyResponse)
def update_vacancy(
        vacancy_id: int,
        vacancy: schemas.VacancyUpdate,
        current_user: models.User = Depends(auth.require_agent),
        db: Session = Depends(get_db)
):
    """Update a vacancy (agents for their org, admins for any)"""
    db_vacancy = crud.get_vacancy(db, vacancy_id)
    if not db_vacancy:
        raise HTTPException(status_code=404, detail="Vacancy not found")

    if not auth.can_modify_vacancy(current_user, db_vacancy):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to modify this vacancy")

    update_data = vacancy.model_dump(exclude_unset=True)
    return crud.update_vacancy(db, vacancy_id, update_data)


@vacancy_router.delete("/{vacancy_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vacancy(
        vacancy_id: int,
        current_user: models.User = Depends(auth.require_agent),
        db: Session = Depends(get_db)
):
    """Delete a vacancy (agents for their org, admins for any)"""
    db_vacancy = crud.get_vacancy(db, vacancy_id)
    if not db_vacancy:
        raise HTTPException(status_code=404, detail="Vacancy not found")

    if not auth.can_modify_vacancy(current_user, db_vacancy):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this vacancy")

    if not crud.delete_vacancy(db, vacancy_id):
        raise HTTPException(status_code=404, detail="Vacancy not found")


app.include_router(vacancy_router)

application_router = APIRouter(prefix="/api/applications", tags=["applications"])


@application_router.get("/", response_model=List[schemas.ApplicationResponse])
def list_applications(
        skip: int = 0,
        limit: int = 100,
        current_user: models.User = Depends(auth.get_current_user),
        db: Session = Depends(get_db)
):
    """
    List applications based on role:
    - Students: Only their own applications
    - Agents: Applications to their org's vacancies
    - Admins: All applications
    """
    if current_user.role == Role.ADMIN:
        return db.query(models.Application).offset(skip).limit(limit).all()

    elif current_user.role == Role.AGENT:
        # Applications to this agent's organization vacancies
        return db.query(models.Application).join(
            models.Vacancy
        ).filter(
            models.Vacancy.employer_id == current_user.org_id
        ).offset(skip).limit(limit).all()

    else:  # Student
        return crud.get_user_applications(db, current_user.id)


@application_router.get("/{application_id}", response_model=schemas.ApplicationDetailed)
def get_application(
        application_id: int,
        current_user: models.User = Depends(auth.get_current_user),
        db: Session = Depends(get_db)
):
    """Get a specific application (with permission check)"""
    db_application = crud.get_application(db, application_id)
    if not db_application:
        raise HTTPException(status_code=404, detail="Application not found")

    # Check permissions
    if current_user.role == Role.STUDENT and db_application.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    if current_user.role == Role.AGENT:
        vacancy = db_application.vacancy
        if vacancy.employer_id != current_user.org_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    return db_application


@application_router.post("/", response_model=schemas.ApplicationResponse, status_code=status.HTTP_201_CREATED)
def create_application(
        application: schemas.ApplicationCreate,
        current_user: models.User = Depends(auth.get_current_user),
        db: Session = Depends(get_db)
):
    """Create an application (any authenticated user can apply)"""
    application_data = application.model_dump()
    return crud.create_application(db, current_user.id, application_data)


@application_router.patch("/{application_id}", response_model=schemas.ApplicationResponse)
def update_application(
        application_id: int,
        application: schemas.ApplicationUpdate,
        current_user: models.User = Depends(auth.get_current_user),
        db: Session = Depends(get_db)
):
    """Update an application (students for their own, admins for any)"""
    db_application = crud.get_application(db, application_id)
    if not db_application:
        raise HTTPException(status_code=404, detail="Application not found")

    if not auth.can_modify_application(current_user, db_application):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to modify this application")

    update_data = application.model_dump(exclude_unset=True)
    return crud.update_application(db, application_id, update_data)


@application_router.delete("/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_application(
        application_id: int,
        current_user: models.User = Depends(auth.get_current_user),
        db: Session = Depends(get_db)
):
    """Delete an application (students for their own, admins for any)"""
    db_application = crud.get_application(db, application_id)
    if not db_application:
        raise HTTPException(status_code=404, detail="Application not found")

    if not auth.can_modify_application(current_user, db_application):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this application")

    if not crud.delete_application(db, application_id):
        raise HTTPException(status_code=404, detail="Application not found")


app.include_router(application_router)

organisation_router = APIRouter(prefix="/api/organisations", tags=["organisations"])


@organisation_router.get("/", response_model=List[schemas.OrganisationResponse])
def list_organisations(
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db)
):
    """List all organisations (public endpoint)"""
    return crud.get_organisations(db, skip=skip, limit=limit)


@organisation_router.get("/{org_id}", response_model=schemas.OrganisationDetailed)
def get_organisation(org_id: int, db: Session = Depends(get_db)):
    """Get a specific organisation (public endpoint)"""
    db_org = crud.get_organisation(db, org_id)
    if not db_org:
        raise HTTPException(status_code=404, detail="Organisation not found")
    return db_org


@organisation_router.post("/", response_model=schemas.OrganisationResponse, status_code=status.HTTP_201_CREATED)
def create_organisation(
        organisation: schemas.OrganisationCreate,
        current_user: models.User = Depends(auth.require_admin),
        db: Session = Depends(get_db)
):
    """Create an organisation (admin only)"""
    org_data = organisation.model_dump()
    return crud.create_organisation(db, org_data)


@organisation_router.patch("/{org_id}", response_model=schemas.OrganisationResponse)
def update_organisation(
        org_id: int,
        organisation: schemas.OrganisationUpdate,
        current_user: models.User = Depends(auth.require_agent),
        db: Session = Depends(get_db)
):
    """Update an organisation (agents for their own, admins for any)"""
    if not auth.can_modify_organisation(current_user, org_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to modify this organisation")

    update_data = organisation.model_dump(exclude_unset=True)
    db_org = crud.update_organisation(db, org_id, update_data)
    if not db_org:
        raise HTTPException(status_code=404, detail="Organisation not found")
    return db_org


@organisation_router.delete("/{org_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_organisation(
        org_id: int,
        current_user: models.User = Depends(auth.require_admin),
        db: Session = Depends(get_db)
):
    """Delete an organisation (admin only)"""
    if not crud.delete_organisation(db, org_id):
        raise HTTPException(status_code=404, detail="Organisation not found")


app.include_router(organisation_router)


media_router = APIRouter(prefix="/api/media", tags=["media"])


@media_router.get("/{media_id}", response_model=schemas.MediaResponse)
def get_media(
    media_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Get media info (authenticated users only)"""
    db_media = crud.get_media(db, media_id)
    if not db_media:
        raise HTTPException(status_code=404, detail="Media not found")
    return db_media


@media_router.post("/", response_model=schemas.MediaResponse, status_code=status.HTTP_201_CREATED)
def upload_media(
    media: schemas.MediaCreate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Upload media (any authenticated user)"""
    media_data = media.model_dump()
    return crud.create_media(db, media_data)


@media_router.delete("/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_media(
    media_id: int,
    current_user: models.User = Depends(auth.require_admin),
    db: Session = Depends(get_db)
):
    """Delete media (admin only)"""
    if not crud.delete_media(db, media_id):
        raise HTTPException(status_code=404, detail="Media not found")


app.include_router(media_router)

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)