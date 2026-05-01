from django.contrib.auth.models import Group
from rest_framework.permissions import BasePermission


def user_in_group(user, group_name: str) -> bool:
    return bool(user and user.is_authenticated and user.groups.filter(name=group_name).exists())


class RolePermission(BasePermission):
    required_group = ""

    def has_permission(self, request, view):
        return user_in_group(request.user, self.required_group)


class IsSuperAdmin(RolePermission):
    required_group = "super_admin"


class IsAdmin(RolePermission):
    required_group = "admin"

    def has_permission(self, request, view):
        return user_in_group(request.user, "admin") or user_in_group(request.user, "super_admin")


class IsQaOperator(RolePermission):
    required_group = "qa_operator"


class CanViewLiveScreen(IsSuperAdmin):
    pass
