from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import AsyncGenerator
from datetime import timedelta

from app.db.session import AsyncSessionLocal
from app.schemas.user import UserCreate, UserPublic
from app.schemas.token import Token
from app.models.user import User
from app.core.security import create_access_token, get_password_hash, verify_password, create_email_token, verify_email_token
from app.core.email import send_activation_email
from app.config import settings

router = APIRouter()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
  async with AsyncSessionLocal() as session:
    yield session


@router.post("/register", response_model=UserPublic)
async def register_user(
    user_in: UserCreate, 
    background_tasks: BackgroundTasks, 
    db: AsyncSession = Depends(get_db)
):
  result = await db.execute(select(User).filter(User.email == user_in.email))
  db_user = result.scalar_one_or_none()

  if db_user:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Email already registered",
    )

  hashed_password = get_password_hash(user_in.password)
  # Create user as inactive
  db_user = User(email=user_in.email, hashed_password=hashed_password, is_active=False)
  db.add(db_user)
  await db.commit()
  await db.refresh(db_user)

  # Send activation email
  token = create_email_token({"sub": user_in.email})
  background_tasks.add_task(send_activation_email, user_in.email, token)

  return db_user


@router.get("/verify-email")
async def verify_email(token: str, db: AsyncSession = Depends(get_db)):
    email = verify_email_token(token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )
    
    result = await db.execute(select(User).filter(User.email == email))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
        
    if user.is_active:
        return {"message": "Account already active"}
        
    user.is_active = True
    db.add(user)
    await db.commit()
    
    return {"message": "Account activated successfully"}


@router.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
  result = await db.execute(select(User).filter(User.email == form_data.username))
  user = result.scalar_one_or_none()

  if not user or not verify_password(form_data.password, user.hashed_password):
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect email or password",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
  if not user.is_active:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Account not activated. Please check your email.",
        headers={"WWW-Authenticate": "Bearer"},
    )

  access_token_expires = timedelta(settings.ACCESS_TOKEN_EXPIRE_MINUTES)
  access_token = create_access_token(
      data={"sub": user.email}, expires_delta=access_token_expires
  )

  return {"access_token": access_token, "token_type": "bearer"}