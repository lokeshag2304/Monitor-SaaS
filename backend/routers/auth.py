from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.schemas.user import UserCreate, UserResponse, UserLogin
from backend.schemas.token import Token
from backend.services.auth_service import create_user, authenticate_user
from backend.utils.security import create_access_token
from backend.utils.dependencies import get_current_user
from backend.models.user import User
from backend.config import ACCESS_TOKEN_EXPIRE_MINUTES
from backend.utils.url import get_full_url

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse, status_code=201)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    return create_user(db, user_data)

@router.post("/login", response_model=Token)
def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    user = authenticate_user(db, user_credentials.email, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
def get_current_user_info(request: Request, current_user: User = Depends(get_current_user)):
    user_data = UserResponse.from_orm(current_user).dict()
    user_data["profile_image"] = get_full_url(request, current_user.profile_image)
    return user_data

@router.post("/logout")
def logout():
    return {"message": "Successfully logged out. Please delete your access token."}