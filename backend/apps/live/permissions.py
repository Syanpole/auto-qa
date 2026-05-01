from rest_framework.permissions import BasePermission
from apps.common.permissions import IsSuperAdmin, IsQaOperator, user_in_group


class CanViewLiveScreen(IsSuperAdmin):
    pass


class CanRequestLiveScreen(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (request.user.is_superuser or user_in_group(request.user, "qa_operator") or user_in_group(request.user, "admin"))
