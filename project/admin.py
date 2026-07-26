from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group, User
from rest_framework.authtoken.admin import TokenAdmin as BaseTokenAdmin
from rest_framework.authtoken.models import TokenProxy

from project.admin_base import ModelAdminUnfoldBase
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

admin.site.unregister(User)
admin.site.unregister(Group)
admin.site.unregister(TokenProxy)


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdminUnfoldBase):
    sidebar_icon = "person"
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm
    list_display = ("username", "email", "first_name", "is_staff")
    list_display_links = ("username", "email")


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdminUnfoldBase):
    sidebar_icon = "group"


@admin.register(TokenProxy)
class TokenAdmin(BaseTokenAdmin):
    sidebar_icon = "key"
