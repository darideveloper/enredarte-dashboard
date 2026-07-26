from django.contrib.auth.models import User


def is_user_admin(user: User):
    user_groups = user.groups.all()
    user_in_admin_group = False
    for group in user_groups:
        if group.name in ["admins", "supports"]:
            user_in_admin_group = True
            break
    return user_in_admin_group or user.is_superuser
