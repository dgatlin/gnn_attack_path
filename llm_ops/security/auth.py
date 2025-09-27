"""
LLM Authentication and Access Management
======================================

Provides secure authentication and access control for LLM operations including:
- API key management and rotation
- Multi-provider support
- Access control and permissions
- Session management
- Audit logging
"""

import os
import time
import hashlib
import secrets
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
import structlog
from enum import Enum

logger = structlog.get_logger(__name__)

class Provider(Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    COHERE = "cohere"
    GOOGLE = "google"
    AZURE = "azure"

class AccessLevel(Enum):
    """Access levels for LLM operations."""
    READ_ONLY = "read_only"
    STANDARD = "standard"
    PREMIUM = "premium"
    ADMIN = "admin"

@dataclass
class APIKey:
    """API key configuration."""
    key_id: str
    provider: Provider
    key_value: str
    access_level: AccessLevel
    created_at: datetime
    expires_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
    usage_count: int = 0
    is_active: bool = True
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    @property
    def is_expired(self) -> bool:
        """Check if the API key is expired."""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at
    
    def touch(self):
        """Update last used timestamp and usage count."""
        self.last_used = datetime.now()
        self.usage_count += 1

@dataclass
class User:
    """User configuration."""
    user_id: str
    name: str
    email: str
    access_level: AccessLevel
    created_at: datetime
    last_active: Optional[datetime] = None
    is_active: bool = True
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class LLMAuth:
    """LLM authentication and access management."""
    
    def __init__(self, 
                 key_rotation_days: int = 90,
                 session_timeout_hours: int = 24,
                 max_failed_attempts: int = 5):
        self.key_rotation_days = key_rotation_days
        self.session_timeout_hours = session_timeout_hours
        self.max_failed_attempts = max_failed_attempts
        
        # Storage
        self.api_keys: Dict[str, APIKey] = {}
        self.users: Dict[str, User] = {}
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.failed_attempts: Dict[str, List[datetime]] = {}
        
        # Load environment variables
        self._load_env_keys()
        
        logger.info("LLM Auth initialized", 
                   key_rotation_days=key_rotation_days,
                   session_timeout_hours=session_timeout_hours)
    
    def _load_env_keys(self):
        """Load API keys from environment variables."""
        env_mappings = {
            Provider.OPENAI: ["OPENAI_API_KEY"],
            Provider.ANTHROPIC: ["ANTHROPIC_API_KEY"],
            Provider.COHERE: ["COHERE_API_KEY"],
            Provider.GOOGLE: ["GOOGLE_API_KEY"],
            Provider.AZURE: ["AZURE_OPENAI_API_KEY"]
        }
        
        for provider, env_vars in env_mappings.items():
            for env_var in env_vars:
                key_value = os.getenv(env_var)
                if key_value:
                    key_id = f"{provider.value}_{env_var.lower()}"
                    self.api_keys[key_id] = APIKey(
                        key_id=key_id,
                        provider=provider,
                        key_value=key_value,
                        access_level=AccessLevel.STANDARD,
                        created_at=datetime.now(),
                        metadata={"source": "environment", "env_var": env_var}
                    )
                    logger.info("Loaded API key from environment", 
                               provider=provider.value,
                               key_id=key_id)
    
    def create_api_key(self, 
                      provider: Provider,
                      access_level: AccessLevel = AccessLevel.STANDARD,
                      expires_days: Optional[int] = None,
                      metadata: Optional[Dict[str, Any]] = None) -> str:
        """Create a new API key."""
        key_id = f"{provider.value}_{secrets.token_hex(8)}"
        key_value = secrets.token_urlsafe(32)
        
        expires_at = None
        if expires_days:
            expires_at = datetime.now() + timedelta(days=expires_days)
        
        api_key = APIKey(
            key_id=key_id,
            provider=provider,
            key_value=key_value,
            access_level=access_level,
            created_at=datetime.now(),
            expires_at=expires_at,
            metadata=metadata or {}
        )
        
        self.api_keys[key_id] = api_key
        
        logger.info("Created API key", 
                   key_id=key_id,
                   provider=provider.value,
                   access_level=access_level.value)
        
        return key_value  # Return the actual key value for the user
    
    def validate_api_key(self, 
                        key_value: str,
                        provider: Provider,
                        required_access_level: AccessLevel = AccessLevel.STANDARD) -> Optional[APIKey]:
        """Validate an API key."""
        # Find the key
        api_key = None
        for key in self.api_keys.values():
            if key.key_value == key_value and key.provider == provider:
                api_key = key
                break
        
        if not api_key:
            logger.warning("Invalid API key", provider=provider.value)
            return None
        
        # Check if key is active and not expired
        if not api_key.is_active or api_key.is_expired:
            logger.warning("API key inactive or expired", 
                          key_id=api_key.key_id,
                          is_active=api_key.is_active,
                          is_expired=api_key.is_expired)
            return None
        
        # Check access level
        if not self._check_access_level(api_key.access_level, required_access_level):
            logger.warning("Insufficient access level", 
                          key_id=api_key.key_id,
                          required=required_access_level.value,
                          actual=api_key.access_level.value)
            return None
        
        # Update usage
        api_key.touch()
        
        logger.debug("API key validated", 
                    key_id=api_key.key_id,
                    provider=provider.value,
                    access_level=api_key.access_level.value)
        
        return api_key
    
    def _check_access_level(self, user_level: AccessLevel, required_level: AccessLevel) -> bool:
        """Check if user access level meets requirements."""
        level_hierarchy = {
            AccessLevel.READ_ONLY: 1,
            AccessLevel.STANDARD: 2,
            AccessLevel.PREMIUM: 3,
            AccessLevel.ADMIN: 4
        }
        
        return level_hierarchy.get(user_level, 0) >= level_hierarchy.get(required_level, 0)
    
    def rotate_api_key(self, key_id: str) -> Optional[str]:
        """Rotate an API key."""
        if key_id not in self.api_keys:
            logger.warning("API key not found for rotation", key_id=key_id)
            return None
        
        old_key = self.api_keys[key_id]
        
        # Create new key
        new_key_value = secrets.token_urlsafe(32)
        new_key = APIKey(
            key_id=f"{old_key.provider.value}_{secrets.token_hex(8)}",
            provider=old_key.provider,
            key_value=new_key_value,
            access_level=old_key.access_level,
            created_at=datetime.now(),
            expires_at=old_key.expires_at,
            metadata={**old_key.metadata, "rotated_from": key_id}
        )
        
        # Deactivate old key
        old_key.is_active = False
        old_key.metadata["rotated_to"] = new_key.key_id
        
        # Add new key
        self.api_keys[new_key.key_id] = new_key
        
        logger.info("API key rotated", 
                   old_key_id=key_id,
                   new_key_id=new_key.key_id,
                   provider=old_key.provider.value)
        
        return new_key_value
    
    def get_keys_for_rotation(self) -> List[APIKey]:
        """Get API keys that need rotation."""
        cutoff_date = datetime.now() - timedelta(days=self.key_rotation_days)
        
        return [
            key for key in self.api_keys.values()
            if key.is_active and key.created_at < cutoff_date
        ]
    
    def create_user(self, 
                   user_id: str,
                   name: str,
                   email: str,
                   access_level: AccessLevel = AccessLevel.STANDARD,
                   metadata: Optional[Dict[str, Any]] = None) -> User:
        """Create a new user."""
        user = User(
            user_id=user_id,
            name=name,
            email=email,
            access_level=access_level,
            created_at=datetime.now(),
            metadata=metadata or {}
        )
        
        self.users[user_id] = user
        
        logger.info("Created user", 
                   user_id=user_id,
                   name=name,
                   access_level=access_level.value)
        
        return user
    
    def authenticate_user(self, user_id: str, session_token: str) -> Optional[User]:
        """Authenticate a user session."""
        if user_id not in self.users:
            logger.warning("User not found", user_id=user_id)
            return None
        
        user = self.users[user_id]
        
        if not user.is_active:
            logger.warning("User inactive", user_id=user_id)
            return None
        
        # Check session
        if session_token not in self.sessions:
            logger.warning("Invalid session token", user_id=user_id)
            return None
        
        session = self.sessions[session_token]
        
        # Check session timeout
        if datetime.now() - session["created_at"] > timedelta(hours=self.session_timeout_hours):
            logger.warning("Session expired", user_id=user_id)
            del self.sessions[session_token]
            return None
        
        # Update last active
        user.last_active = datetime.now()
        session["last_accessed"] = datetime.now()
        
        logger.debug("User authenticated", 
                    user_id=user_id,
                    access_level=user.access_level.value)
        
        return user
    
    def create_session(self, user_id: str) -> str:
        """Create a new user session."""
        if user_id not in self.users:
            logger.warning("User not found for session creation", user_id=user_id)
            return None
        
        session_token = secrets.token_urlsafe(32)
        
        self.sessions[session_token] = {
            "user_id": user_id,
            "created_at": datetime.now(),
            "last_accessed": datetime.now()
        }
        
        logger.info("Session created", user_id=user_id, session_token=session_token[:8])
        
        return session_token
    
    def revoke_session(self, session_token: str) -> bool:
        """Revoke a user session."""
        if session_token in self.sessions:
            del self.sessions[session_token]
            logger.info("Session revoked", session_token=session_token[:8])
            return True
        
        logger.warning("Session not found for revocation", session_token=session_token[:8])
        return False
    
    def get_user_stats(self) -> Dict[str, Any]:
        """Get user and session statistics."""
        active_sessions = len(self.sessions)
        active_users = len([u for u in self.users.values() if u.is_active])
        active_keys = len([k for k in self.api_keys.values() if k.is_active])
        
        return {
            "total_users": len(self.users),
            "active_users": active_users,
            "active_sessions": active_sessions,
            "total_api_keys": len(self.api_keys),
            "active_api_keys": active_keys,
            "keys_needing_rotation": len(self.get_keys_for_rotation())
        }
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions."""
        cutoff_time = datetime.now() - timedelta(hours=self.session_timeout_hours)
        expired_sessions = []
        
        for token, session in self.sessions.items():
            if session["created_at"] < cutoff_time:
                expired_sessions.append(token)
        
        for token in expired_sessions:
            del self.sessions[token]
        
        if expired_sessions:
            logger.info("Cleaned up expired sessions", count=len(expired_sessions))
    
    def get_audit_log(self, 
                     user_id: Optional[str] = None,
                     action: Optional[str] = None,
                     limit: int = 100) -> List[Dict[str, Any]]:
        """Get audit log entries."""
        # This would typically connect to a proper audit logging system
        # For now, return a placeholder
        return [
            {
                "timestamp": datetime.now(),
                "user_id": user_id or "system",
                "action": action or "access",
                "details": "Audit log entry"
            }
        ]
