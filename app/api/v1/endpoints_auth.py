from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import AsyncGenerator
from datetime import timedelta

from app.db.session import AsyncSessionLocal
from app.schemas.user import UserCreate, UserPublic
from app.schemas.token import Token
from app.models.user import User
from app.core.security import create_access_token, get_password_hash, verify_password
from app.config import settings

router = APIRouter()

def get_db():
  db = SessionLocal()
  try:
    yield db
  finally:
    db.close()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
  async with AsyncSessionLocal() as session:
    yield session

@router.post("/register", response_model=UserPublic)
async def register_user(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
  result = await db.execute(select(User).filter(User.email == user_in.email))
  db_user = result.scalar_one_or_none()
  
  if db_user:
    raise HTTPException(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail="Email already registered",
    )
  
  hashed_password = get_password_hash(user_in.password)
  db_user = User(email=user_in.email, hashed_password=hashed_password)
  db.add(db_user)
  await db.commit()
  await db.refresh(db_user)

  return db_user

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
      
  access_token_expires = timedelta(settings.ACCESS_TOKEN_EXPIRE_MINUTES)
  access_token = create_access_token(
      data={"sub": user.email}, expires_delta=access_token_expires
  )

  return {"access_token": access_token, "token_type": "bearer"}