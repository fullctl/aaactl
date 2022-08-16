from fullctl.django.models import Task
from fullctl.django.tasks import register

import account.models

__all__ = ["UpdatePermissions"]


@register
class UpdatePermissions(Task):
    class Meta:
        proxy = True

    class HandleRef:
        tag = "task_update_permissions"

    def run(self, *args, **kwargs):
        account.models.ManagedPermission.apply_roles_all()
