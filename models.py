from pydantic import BaseModel, field_validator, EmailStr, ConfigDict
from typing import List, Optional
from datetime import datetime
import db_handler as db


class UserBase(BaseModel):
    fname: str
    lname: str
    email: EmailStr
    role: bool


class UserCreate(UserBase):
    password: str
    pname: Optional[str] = None
    org_id: Optional[int] = None

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v


class UserUpdate(BaseModel):
    fname: Optional[str] = None
    lname: Optional[str] = None
    pname: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    role: Optional[bool] = None
    icon_id: Optional[int] = None
    org_id: Optional[int] = None

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if v is not None and len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v


class UserResponse(UserBase):
    id: int
    pname: Optional[str] = None
    icon_id: Optional[int] = None
    registred: datetime
    org_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class UserDetailed(UserResponse):
    applications: List['ApplicationResponse'] = []
    bookmarks: List['BookmarkResponse'] = []
    sent_messages: List['MessageResponse'] = []

    model_config = ConfigDict(from_attributes=True)


class OrganisationBase(BaseModel):
    title: str
    description: str


class OrganisationCreate(OrganisationBase):
    icon_id: Optional[int] = None


class OrganisationUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    icon_id: Optional[int] = None


class OrganisationResponse(OrganisationBase):
    id: int
    icon_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class OrganisationDetailed(OrganisationResponse):
    vacancies: List['VacancyResponse'] = []
    members: List[UserResponse] = []

    model_config = ConfigDict(from_attributes=True)


class VacancyBase(BaseModel):
    title: str
    description: str
    status: int


class VacancyCreate(VacancyBase):
    employer_id: int
    brief: Optional[str] = None
    salary_top: Optional[float] = None
    salary_bottom: Optional[float] = None
    required_year: Optional[int] = None
    icon_id: Optional[int] = None


class VacancyUpdate(BaseModel):
    title: Optional[str] = None
    brief: Optional[str] = None
    description: Optional[str] = None
    salary_top: Optional[float] = None
    salary_bottom: Optional[float] = None
    required_year: Optional[int] = None
    status: Optional[int] = None
    icon_id: Optional[int] = None


class VacancyResponse(VacancyBase):
    id: int
    employer_id: int
    brief: Optional[str] = None
    salary_top: Optional[float] = None
    salary_bottom: Optional[float] = None
    required_year: Optional[int] = None
    icon_id: Optional[int] = None
    created: datetime

    model_config = ConfigDict(from_attributes=True)


class VacancyDetailed(VacancyResponse):
    employer: Optional[OrganisationResponse] = None
    applications: List['ApplicationResponse'] = []

    model_config = ConfigDict(from_attributes=True)


class MediaBase(BaseModel):
    name: str
    path: str


class MediaCreate(MediaBase):
    pass


class MediaUpdate(BaseModel):
    name: Optional[str] = None
    path: Optional[str] = None


class MediaResponse(MediaBase):
    id: int
    added: datetime

    model_config = ConfigDict(from_attributes=True)


class MessageBase(BaseModel):
    content: str


class MessageCreate(MessageBase):
    recepient_id: int


class MessageUpdate(BaseModel):
    content: Optional[str] = None


class MessageResponse(MessageBase):
    id: int
    sent: datetime
    last_edit: Optional[datetime] = None
    sender_id: int
    recepient_id: int

    model_config = ConfigDict(from_attributes=True)


class MessageDetailed(MessageResponse):
    sender: Optional[UserResponse] = None
    recipient: Optional[UserResponse] = None

    model_config = ConfigDict(from_attributes=True)


class ApplicationBase(BaseModel):
    title: str
    content: str


class ApplicationCreate(ApplicationBase):
    vacancy_id: int


class ApplicationUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None


class ApplicationResponse(ApplicationBase):
    id: int
    user_id: int
    vacancy_id: int

    model_config = ConfigDict(from_attributes=True)


class ApplicationDetailed(ApplicationResponse):
    user: Optional[UserResponse] = None
    vacancy: Optional[VacancyResponse] = None

    model_config = ConfigDict(from_attributes=True)


class BookmarkCreate(BaseModel):
    vacancy_id: int


class BookmarkResponse(BaseModel):
    vacancy_id: int
    user_id: int

    model_config = ConfigDict(from_attributes=True)


class BookmarkDetailed(BookmarkResponse):
    vacancy: Optional[VacancyResponse] = None

    model_config = ConfigDict(from_attributes=True)


class MessageMediaCreate(BaseModel):
    media_id: int


class VacancyMediaCreate(BaseModel):
    media_id: int


class ApplicationMediaCreate(BaseModel):
    media_id: int
