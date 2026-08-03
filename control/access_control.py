# control/access_control.py
# AKUFIN - Intelligence for Wealth Accrual
# Admin Access Control System
# YOU control who sees your platform. Always.
import hashlib
import json
import os
from datetime import datetime, timedelta
from monitoring.logger import get_logger

logger = get_logger(__name__)

# ── AKUFIN ACCESS CONTROL DATABASE ───────────────────
# This file stores user access data locally
ACCESS_DB_FILE = "control/akufin_access.json"


def _load_db() -> dict:
    """Load the access control database"""
    os.makedirs("control", exist_ok=True)
    if not os.path.exists(ACCESS_DB_FILE):
        # Create fresh database with admin only
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
    """Save the access control database"""
    os.makedirs("control", exist_ok=True)
    with open(ACCESS_DB_FILE, "w") as f:
        json.dump(db, f, indent=2)


def _hash_key(key: str) -> str:
    """Hash a key for secure storage"""
    return hashlib.sha256(key.encode()).hexdigest()


class AKUFINAccessControl:
    """
    AKUFIN Admin Access Control System.

    YOU are the only admin.
    YOU approve who sees your platform.
    YOU can revoke access instantly.
    No one can bypass this system.
    """

    def __init__(self):
        self.db = _load_db()

    def setup_admin(self, admin_key: str) -> bool:
        """
        First time setup: Set your admin key.
        Call this ONCE when you first deploy.
        Keep your admin key secret and safe.
        """
        self.db["admin_key_hash"] = _hash_key(admin_key)
        _save_db(self.db)
        logger.info("AKUFIN admin key configured")
        return True

    def is_admin(self, key: str) -> bool:
        """Check if provided key is the admin key"""
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
        """
        ADMIN ONLY: Approve a new user.
        Roles:
          viewer → Can view dashboard only
          analyst → Can generate predictions
          trader → Can approve trades
        """
        if not self.is_admin(admin_key):
            logger.warning(
                f"Unauthorized approve attempt "
                f"for {username}"
            )
            return {
                "success": False,
                "error": "Invalid admin key"
            }

        expires = (
            datetime.now() + timedelta(days=expires_days)
        ).isoformat()

        self.db["users"][username] = {
            "username": username,
            "role": role,
            "approved": True,
            "approved_by": "AKUFIN_ADMIN",
            "approved_at": datetime.now().isoformat(),
            "expires": expires,
            "active": True,
            "last_login": None
        }
        _save_db(self.db)

        logger.info(
            f"AKUFIN: User approved: {username} "
            f"| Role: {role} | Expires: {expires}"
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
        """
        ADMIN ONLY: Instantly revoke user access.
        They will be logged out immediately.
        """
        if not self.is_admin(admin_key):
            return {
                "success": False,
                "error": "Invalid admin key"
            }

        if username in self.db["users"]:
            self.db["users"][username]["active"] = False
            self.db["users"][username]["revoked_at"] = (
                datetime.now().isoformat()
            )
            _save_db(self.db)
            logger.info(
                f"AKUFIN: Access REVOKED: {username}"
            )
            return {
                "success": True,
                "message": f"{username} access revoked"
            }
        return {
            "success": False,
            "error": "User not found"
        }

    def check_access(
        self, username: str, password: str
    ) -> dict:
        """
        Check if a user has valid AKUFIN access.
        Called every time someone tries to login.
        """
        if username not in self.db["users"]:
            logger.warning(
                f"AKUFIN: Unknown user login: {username}"
            )
            return {
                "allowed": False,
                "reason": "User not found. "
                          "Contact AKUFIN admin for access."
            }

        user = self.db["users"][username]

        if not user.get("active", False):
            logger.warning(
                f"AKUFIN: Revoked user attempt: {username}"
            )
            return {
                "allowed": False,
                "reason": "Your AKUFIN access has been revoked."
            }

        # Check expiry
        expires = datetime.fromisoformat(
            user.get("expires", "2000-01-01")
        )
        if datetime.now() > expires:
            logger.warning(
                f"AKUFIN: Expired access: {username}"
            )
            return {
                "allowed": False,
                "reason": "Your AKUFIN access has expired."
            }

        # Check password hash
        if _hash_key(password) != user.get(
            "password_hash", ""
        ):
            logger.warning(
                f"AKUFIN: Wrong password: {username}"
            )
            return {
                "allowed": False,
                "reason": "Incorrect password."
            }

        # Update last login
        self.db["users"][username]["last_login"] = (
            datetime.now().isoformat()
        )
        _save_db(self.db)

        logger.info(
            f"AKUFIN: Login success: {username} "
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
        """ADMIN ONLY: Set or reset a user's password"""
        if not self.is_admin(admin_key):
            return {
                "success": False,
                "error": "Invalid admin key"
            }

        if username not in self.db["users"]:
            return {
                "success": False,
                "error": "User not found"
            }

        self.db["users"][username][
            "password_hash"
        ] = _hash_key(password)
        _save_db(self.db)

        logger.info(
            f"AKUFIN: Password set for: {username}"
        )
        return {
            "success": True,
            "message": f"Password set for {username}"
        }

    def get_all_users(self, admin_key: str) -> list:
        """ADMIN ONLY: See all users and their status"""
        if not self.is_admin(admin_key):
            return []

        users = []
        for username, data in self.db["users"].items():
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
        """ADMIN ONLY: Extend a user's access period"""
        if not self.is_admin(admin_key):
            return {
                "success": False,
                "error": "Invalid admin key"
            }

        if username not in self.db["users"]:
            return {
                "success": False,
                "error": "User not found"
            }

        current_expires = datetime.fromisoformat(
            self.db["users"][username].get(
                "expires",
                datetime.now().isoformat()
            )
        )
        new_expires = (
            current_expires + timedelta(days=extra_days)
        ).isoformat()

        self.db["users"][username]["expires"] = new_expires
        _save_db(self.db)

        logger.info(
            f"AKUFIN: Access extended: {username} "
            f"→ {new_expires}"
        )
        return {
            "success": True,
            "username": username,
            "new_expiry": new_expires
        }