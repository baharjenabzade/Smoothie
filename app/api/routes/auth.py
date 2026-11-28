from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.api.deps import CurrentUser, DbSession
from app.core.errors import ConflictError
from app.core.security import (
    create_access_token,
    dummy_hash,
    hash_password,
    verify_password,
)
from app.models import User
from app.schemas.user import Token, UserCreate, UserRead, UserUpdate

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: DbSession):
    email = payload.email.lower()
    if db.scalar(select(User).where(User.email == email)) is not None:
        raise ConflictError("This e-mail address is already registered")
    user = User(
        email=email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        target_band=payload.target_band,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:  # lost a race with a concurrent registration
        db.rollback()
        raise ConflictError("This e-mail address is already registered") from None
    return UserRead.model_validate(user)


@router.post("/login", response_model=Token)
def login(form: Annotated[OAuth2PasswordRequestForm, Depends()], db: DbSession):
    """OAuth2 password flow. Send the e-mail address in the `username` field."""
    user = db.scalar(select(User).where(User.email == form.username.strip().lower()))
    # Always run a bcrypt check so response time does not reveal whether the e-mail exists.
    password_ok = verify_password(form.password, user.hashed_password if user else dummy_hash())
    if user is None or not password_ok or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect e-mail or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Token(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserRead)
def read_me(user: CurrentUser):
    return UserRead.model_validate(user)


@router.patch("/me", response_model=UserRead)
def update_me(payload: UserUpdate, db: DbSession, user: CurrentUser):
    changes = payload.model_dump(exclude_unset=True)
    for field, value in changes.items():
        if value is not None:
            setattr(user, field, value)
    db.commit()
    return UserRead.model_validate(user)
