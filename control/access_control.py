# control/access_control.py
# AKUFIN - Intelligence for Wealth Accrual
# Admin Access Control System
# Works on both localhost AND Streamlit Cloud
import hashlib
import json
import os
from datetime import datetime, timedelta
from monitoring.logger import get_logger

logger = get_logger(__name__)

ACCESS_DB_FILE = "control/akufin_access.json"


def _load_db() -> dict:
    """Load access control database"""
    os.makedirs("control", exist_ok=True)
    if not os.path.exists(ACCESS_DB_FILE):
        db = {
            "users": {},
            "admin_key_hash": "",
            "created": datetime.now().isoformat()
        }
        _save_db(db)
        return db
    with open(ACCESS_DB_FILE, "r") as f:
        return json.load(f)


def _save_db(db: dict):
    """Save access control database"""
    os.makedirs("control", exist_ok=True)
    with open(ACCESS_DB_FILE, "w") as f:
        json.dump(db, f, indent=2)


def _hash_key(key: str) -> str:
    """Hash a key for secure storage"""
    return hashlib.sha256(key.encode()).hexdigest()


def _load_db_from_secrets() -> dict:
    """
    Load users from Streamlit Secrets on cloud.
    Falls back to local file on localhost.
    """
    try:
        import streamlit as st
        if hasattr(st, 'secrets'):
            # Try to get from secrets
            admin_hash = st.secrets.get(
                "AKUFIN_ADMIN_HASH", ""
            )
            users_json = st.secrets.get(
                "AKUFIN_USERS", ""
            )
            
            if admin_hash and users_json:
                return {
                    "users": json.loads(users_json),
                    "admin_key_hash": admin_hash,
                    "source": "streamlit_secrets"
                }
    except Exception as e:
        pass

    # Fall back to local file
    return _load_db()


class AKUFINAccessControl:
    """
    AKUFIN Admin Access Control.
    Works on localhost and Streamlit Cloud.
    YOU control all access.
    """

    def __init__(self):
        self.db = _load_db_from_secrets()

    def _reload(self):
        """Reload database"""
        self.db = _load_db_from_secrets()

    def setup_admin(self, admin_key: str) -> bool:
        """Set admin key"""
        db = _load_db()
        db["admin_key_hash"] = _hash_key(admin_key)
        _save_db(db)
        self.db = db
        logger.info("AKUFIN admin key configured")
        return True

    def is_admin(self, key: str) -> bool:
    """Check if key is admin key"""
    # Check from loaded db (works for both local and cloud)
    stored_hash = self.db.get("admin_key_hash", "")
    if stored_hash and stored_hash == _hash_key(key):
        return True
    
    # Also check directly from secrets if on cloud
    try:
        import streamlit as st
        if hasattr(st, 'secrets'):
            cloud_hash = st.secrets.get(
                "AKUFIN_ADMIN_HASH", ""
            )
            if cloud_hash and cloud_hash == _hash_key(key):
                return True
    except Exception:
        pass
    
    return False
        """Check if key is admin key"""
        return (
            self.db.get("admin_key_hash") ==
            _hash_key(key)
        )

    def approve_user(
        self,
        username: str,
        admin_key: str,
        role: str = "viewer",
        expires_days: int = 30
    ) -> dict:
        """ADMIN ONLY: Approve a new user"""
        if not self.is_admin(admin_key):
            return {
                "success": False,
                "error": "Invalid admin key"
            }

        expires = (
            datetime.now() + timedelta(days=expires_days)
        ).isoformat()

        db = _load_db()
        db["users"][username] = {
            "username": username,
            "role": role,
            "approved": True,
            "approved_by": "AKUFIN_ADMIN",
            "approved_at": datetime.now().isoformat(),
            "expires": expires,
            "active": True,
            "last_login": None,
            "password_hash": ""
        }
        _save_db(db)
        self.db = db

        logger.info(
            f"AKUFIN user approved: {username} "
            f"| Role: {role}"
        )
        return {
            "success": True,
            "username": username,
            "role": role,
            "expires": expires
        }

    def revoke_user(
        self, username: str, admin_key: str
    ) -> dict:
        """ADMIN ONLY: Revoke user access instantly"""
        if not self.is_admin(admin_key):
            return {
                "success": False,
                "error": "Invalid admin key"
            }

        db = _load_db()
        if username in db["users"]:
            db["users"][username]["active"] = False
            db["users"][username]["revoked_at"] = (
                datetime.now().isoformat()
            )
            _save_db(db)
            self.db = db
            logger.info(
                f"AKUFIN access REVOKED: {username}"
            )
            return {
                "success": True,
                "message": f"{username} revoked"
            }
        return {
            "success": False,
            "error": "User not found"
        }

    def check_access(
        self, username: str, password: str
    ) -> dict:
        """Check if user has valid AKUFIN access"""
        self._reload()
        users = self.db.get("users", {})

        if username not in users:
            logger.warning(
                f"AKUFIN: Unknown user: {username}"
            )
            return {
                "allowed": False,
                "reason": (
                    "User not found. "
                    "Contact AKUFIN admin for access."
                )
            }

        user = users[username]

        if not user.get("active", False):
            return {
                "allowed": False,
                "reason": (
                    "Your AKUFIN access has been revoked."
                )
            }

        expires = datetime.fromisoformat(
            user.get("expires", "2000-01-01")
        )
        if datetime.now() > expires:
            return {
                "allowed": False,
                "reason": (
                    "Your AKUFIN access has expired. "
                    "Contact admin to renew."
                )
            }

        stored_hash = user.get("password_hash", "")
        if not stored_hash:
            return {
                "allowed": False,
                "reason": (
                    "Password not set. "
                    "Contact AKUFIN admin."
                )
            }

        if _hash_key(password) != stored_hash:
            logger.warning(
                f"AKUFIN: Wrong password: {username}"
            )
            return {
                "allowed": False,
                "reason": "Incorrect password."
            }

        # Update last login in local file
        try:
            db = _load_db()
            if username in db["users"]:
                db["users"][username][
                    "last_login"
                ] = datetime.now().isoformat()
                _save_db(db)
        except Exception:
            pass

        logger.info(
            f"AKUFIN login success: {username} "
            f"| Role: {user.get('role')}"
        )
        return {
            "allowed": True,
            "username": username,
            "role": user.get("role"),
            "expires": user.get("expires")
        }

    def set_user_password(
        self,
        username: str,
        password: str,
        admin_key: str
    ) -> dict:
        """ADMIN ONLY: Set user password"""
        if not self.is_admin(admin_key):
            return {
                "success": False,
                "error": "Invalid admin key"
            }

        db = _load_db()
        if username not in db["users"]:
            return {
                "success": False,
                "error": "User not found"
            }

        db["users"][username][
            "password_hash"
        ] = _hash_key(password)
        _save_db(db)
        self.db = db

        logger.info(
            f"AKUFIN password set: {username}"
        )
        return {
            "success": True,
            "message": f"Password set for {username}"
        }

    def get_all_users(self, admin_key: str) -> list:
        """ADMIN ONLY: Get all users"""
        if not self.is_admin(admin_key):
            return []

        self._reload()
        users = []
        for username, data in self.db.get(
            "users", {}
        ).items():
            expires = datetime.fromisoformat(
                data.get("expires", "2000-01-01")
            )
            users.append({
                "username": username,
                "role": data.get("role"),
                "active": data.get("active"),
                "approved_at": data.get("approved_at"),
                "expires": data.get("expires"),
                "last_login": data.get("last_login"),
                "expired": datetime.now() > expires
            })
        return users

    def extend_access(
        self,
        username: str,
        admin_key: str,
        extra_days: int = 30
    ) -> dict:
        """ADMIN ONLY: Extend user access"""
        if not self.is_admin(admin_key):
            return {
                "success": False,
                "error": "Invalid admin key"
            }

        db = _load_db()
        if username not in db["users"]:
            return {
                "success": False,
                "error": "User not found"
            }

        current = datetime.fromisoformat(
            db["users"][username].get(
                "expires",
                datetime.now().isoformat()
            )
        )
        new_expires = (
            current + timedelta(days=extra_days)
        ).isoformat()

        db["users"][username]["expires"] = new_expires
        _save_db(db)
        self.db = db

        return {
            "success": True,
            "username": username,
            "new_expiry": new_expires
        }