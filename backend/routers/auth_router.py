from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from config.database import get_db
from repository.user_repository import UserRepository
from services.auth_service import authenticate_user, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login")
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(UserRepository(db), form.username, form.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contrasenia incorrectos",
            headers={"WWW-Authenticate": "Bearer"}
        )

    token = create_access_token(
        {"username": user.username,
         "rol": user.rol.value,
         "supplier_id": user.supplier_id}
    )

    return {"access_token": token, "token_type": "bearer"}