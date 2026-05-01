from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from apps.audit.models import AuditLog
from apps.qa.models import QAStation, ProductProfile, StationThreshold, DefectEvent
from apps.training.models import DatasetVersion, TrainingJob, ModelRegistry, ModelAccess, StationModelAssignment
from apps.live.models import LiveScreenSession, LiveScreenAccessEvent


class Command(BaseCommand):
    help = "Seed enterprise RBAC groups and baseline permissions."

    def handle(self, *args, **options):
        super_admin, _ = Group.objects.get_or_create(name="super_admin")
        admin, _ = Group.objects.get_or_create(name="admin")
        qa_operator, _ = Group.objects.get_or_create(name="qa_operator")

        model_permissions = [
            "add_modelregistry", "change_modelregistry", "view_modelregistry",
            "add_modelaccess", "change_modelaccess", "view_modelaccess",
            "add_stationmodelassignment", "change_stationmodelassignment", "view_stationmodelassignment",
            "add_datasetversion", "change_datasetversion", "view_datasetversion",
            "add_trainingjob", "change_trainingjob", "view_trainingjob",
            "add_livescreensession", "change_livescreensession", "view_livescreensession",
            "view_livescreenaccessevent", "view_auditlog",
        ]
        admin_permissions = [
            "add_qastation", "change_qastation", "view_qastation",
            "add_productprofile", "change_productprofile", "view_productprofile",
            "add_stationthreshold", "change_stationthreshold", "view_stationthreshold",
            "add_defectevent", "change_defectevent", "view_defectevent",
            "view_livescreensession",
        ]
        qa_permissions = [
            "view_qastation",
            "view_productprofile",
            "view_defectevent",
            "view_livescreensession",
            "request_live_screen",
        ]

        super_admin.permissions.set(Permission.objects.all())
        admin.permissions.set(Permission.objects.filter(codename__in=model_permissions + admin_permissions + ["export_audit_log", "deploy_model", "grant_model_access", "assign_station_model", "view_live_screen", "request_live_screen"]))
        qa_operator.permissions.set(Permission.objects.filter(codename__in=qa_permissions))

        self.stdout.write(self.style.SUCCESS("RBAC groups seeded successfully."))
