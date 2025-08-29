from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from database.database import get_db
from database.models import User

security = HTTPBearer(auto_error=False)

async def get_current_user(token: str = Depends(security), db: Session = Depends(get_db)):
    """
    Get current user from token.
    For demo purposes, we'll return the first user or create one.
    """
    try:
        # In a real app, you'd validate the JWT token here
        # For demo purposes, get or create a demo user
        user = db.query(User).first()
        
        if not user:
            try:
                from passlib.context import CryptContext
                pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
                hashed_password = pwd_context.hash("demo123")
            except:
                # Fallback if bcrypt has issues
                hashed_password = "hashed_demo123"
            
            user = User(
                email="demo@example.com",
                username="demo_user",
                hashed_password=hashed_password,
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        
        return user
        
    except Exception as e:
        # Return a mock user for demo purposes
        return User(
            id=1,
            username="demo_user",
            email="demo@example.com",
            is_active=True
        )
