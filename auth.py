"""
Authentication Module for Travel AI Agent
JWT + OAuth + Session Management for millions of users
"""

import jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import redis
import json
import uuid

# Configuration
JWT_SECRET = "your-super-secret-jwt-key-change-in-production"
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Redis for session management
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

# Security scheme
security = HTTPBearer()

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
    
    # Check if user is active (from Redis)
    user_data = redis_client.get(f"user:{user_id}")
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    user_dict = json.loads(user_data)
    return User(
        user_id=user_id,
        email=user_dict.get("email"),
        username=user_dict.get("username"),
        is_active=user_dict.get("is_active", True)
    )

def create_session(user_id: str, user_data: Dict[str, Any]) -> str:
    """Create session in Redis"""
    session_id = str(uuid.uuid4())
    session_key = f"session:{session_id}"
    
    # Store session data
    redis_client.setex(
        session_key,
        timedelta(hours=24).total_seconds(),
        json.dumps({
            "user_id": user_id,
            "created_at": datetime.utcnow().isoformat(),
            **user_data
        })
    )
    
    # Store user data
    redis_client.setex(
        f"user:{user_id}",
        timedelta(days=30).total_seconds(),
        json.dumps(user_data)
    )
    
    return session_id

def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    """Get session from Redis"""
    session_data = redis_client.get(f"session:{session_id}")
    if session_data:
        return json.loads(session_data)
    return None

def delete_session(session_id: str) -> bool:
    """Delete session from Redis"""
    return redis_client.delete(f"session:{session_id}") > 0

def delete_user_sessions(user_id: str) -> int:
    """Delete all sessions for a user"""
    # Get all session keys for this user
    pattern = f"session:*"
    deleted = 0
    
    for key in redis_client.scan_iter(match=pattern):
        session_data = redis_client.get(key)
        if session_data:
            session_dict = json.loads(session_data)
            if session_dict.get("user_id") == user_id:
                redis_client.delete(key)
                deleted += 1
    
    return deleted
