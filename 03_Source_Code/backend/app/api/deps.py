from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from app.cores.database import get_db
from app.cores.config import settings
from app.models.user import User
from app.schemas.user import TokenData

security = HTTPBearer(auto_error=False)

def get_current_user(credentials = Depends(security), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if credentials is None:
        raise credentials_exception
        
    token = credentials.credentials
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
        
    user = db.query(User).filter(User.email == token_data.email).first()
    if user is None:
        raise credentials_exception
    return user

def get_current_active_admin(current_user: User = Depends(get_current_user)):
    if current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return current_user
