from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.contrib.auth.models import User
from django.contrib.auth.models import Group
from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from apps.audit.services import log_event


@receiver(user_logged_in)
def on_user_logged_in(sender, request, user, **kwargs):
    log_event(user=user, action_type="user_login", target_object=user.username, request=request)


@receiver(user_logged_out)
def on_user_logged_out(sender, request, user, **kwargs):
    log_event(user=user, action_type="user_logout", target_object=getattr(user, "username", ""), request=request)


@receiver(user_login_failed)
def on_user_login_failed(sender, credentials, request, **kwargs):
    username = credentials.get("username", "") if credentials else ""
    log_event(action_type="failed_login", target_object=username, metadata={"credentials": "masked"}, request=request)


@receiver(m2m_changed, sender=User.groups.through)
def on_user_role_changed(sender, instance, action, reverse, model, pk_set, **kwargs):
    if action not in {"post_add", "post_remove", "post_clear"}:
        return
    change_action = "role_grant" if action == "post_add" else "role_revoke"
    log_event(
        user=instance,
        action_type=change_action,
        target_object=instance.username,
        metadata={"group_ids": list(pk_set or [])},
    )


@receiver(m2m_changed, sender=User.user_permissions.through)
def on_user_permission_changed(sender, instance, action, reverse, model, pk_set, **kwargs):
    if action not in {"post_add", "post_remove", "post_clear"}:
        return
    change_action = "permission_grant" if action == "post_add" else "permission_revoke"
    log_event(
        user=instance,
        action_type=change_action,
        target_object=instance.username,
        metadata={"permission_ids": list(pk_set or [])},
    )
