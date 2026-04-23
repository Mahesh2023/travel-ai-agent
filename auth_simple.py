"""
Authentication Module - Simplified (In-Memory)
Following teloscopy pattern: No external databases, in-memory storage only
"""

from jose import jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uuid

# Configuration
JWT_SECRET = "your-super-secret-jwt-key-change-in-production"
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security scheme
security = HTTPBearer()

# In-memory storage (following teloscopy pattern)
_users_db: Dict[str, Dict[str, Any]] = {}  # email -> user data
_sessions_db: Dict[str, Dict[str, Any]] = {}  # session_id -> session data

class User:
    """User model"""
    def __init__(self, user_id: str, email: str, username: str, is_active: bool = True):
        self.user_id = user_id
        self.email = email
        self.username = username
        self.is_active = is_active

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: Dict[str, Any]) -> str:
    """Create JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def verify_token(token: str, token_type: str = "access") -> Dict[str, Any]:
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != token_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get current user from JWT token"""
    token = credentials.credentials
    payload = verify_token(token, "access")
    user_id = payload.get("sub")
    
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    # Check if user exists in in-memory database
    user_data = None
    for email, data in _users_db.items():
        if data.get("user_id") == user_id:
            user_data = data
            break
    
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return User(
        user_id=user_id,
        email=user_data.get("email"),
        username=user_data.get("username"),
        is_active=user_data.get("is_active", True)
    )

def create_session(user_id: str, user_data: Dict[str, Any]) -> str:
    """Create session in memory"""
    session_id = str(uuid.uuid4())
    
    _sessions_db[session_id] = {
        "user_id": user_id,
        "created_at": datetime.utcnow().isoformat(),
        **user_data
    }
    
    return session_id

def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    """Get session from memory"""
    return _sessions_db.get(session_id)

def delete_session(session_id: str) -> bool:
    """Delete session from memory"""
    if session_id in _sessions_db:
        del _sessions_db[session_id]
        return True
    return False

def delete_user_sessions(user_id: str) -> int:
    """Delete all sessions for a user"""
    deleted = 0
    to_delete = []
    
    for session_id, session_data in _sessions_db.items():
        if session_data.get("user_id") == user_id:
            to_delete.append(session_id)
    
    for session_id in to_delete:
        del _sessions_db[session_id]
        deleted += 1
    
    return deleted

def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Get user by email from in-memory database"""
    return _users_db.get(email)

def save_user(email: str, user_data: Dict[str, Any]) -> None:
    """Save user to in-memory database"""
    _users_db[email] = user_data
