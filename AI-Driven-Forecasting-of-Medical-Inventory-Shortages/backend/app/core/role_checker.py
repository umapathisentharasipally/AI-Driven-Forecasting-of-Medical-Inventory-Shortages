from typing import List

from fastapi import Depends

from app.config.security import get_current_active_user
from app.core.exception_handler import ForbiddenException
from app.core.permissions import ADMIN_ALL, ROLE_PERMISSIONS


class RoleChecker:
    def __init__(self, required_permissions: List[str]):
        self.required_permissions = required_permissions

    async def __call__(self, current_user=Depends(get_current_active_user)):
        role_name = current_user.get("role") or current_user.get("role_name")
        user_permissions = ROLE_PERMISSIONS.get(role_name, [])

        if ADMIN_ALL in user_permissions:
            return current_user

        for permission in self.required_permissions:
            if permission not in user_permissions:
                raise ForbiddenException(
                    message="Insufficient permissions",
                    details={"missing_permission": permission},
                )

        return current_user