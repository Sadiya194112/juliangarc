from django import forms
from django.contrib import admin
from apps.accounts.models import User, Profile
from django.core.exceptions import ValidationError
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField


class UserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(
        label="Password confirmation", widget=forms.PasswordInput
    )

    class Meta:
        model = User
        fields = ["full_name", "email"]

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = User
        fields = ["full_name", "email", "password", "is_active", "is_staff", "is_superuser"]


class UserAdmin(BaseUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm

    list_display = ["id", "full_name", "email", "role", "phone", "picture", "stripe_account_id", "stripe_customer_id", "terms_privacy", "is_active", "is_staff", "is_superuser"]
    list_filter = ["is_active", "is_staff", "is_superuser"]
    fieldsets = [
        (None, {"fields": ["email", "password"]}),
        ("Personal info", {"fields": ["full_name", "role", "phone", "stripe_account_id"]}),
        ("Permissions", {"fields": [ "is_active", "is_staff", "is_superuser", "groups", "user_permissions"]}),
    ]
    add_fieldsets = [
        (
            None,
            {
                "classes": ["wide"],
                "fields": ["name", "email", "password1", "password2"],
            },
        ),
    ]
    search_fields = ["email"]
    ordering = ["email"]
    filter_horizontal = []



admin.site.register(User, UserAdmin)





@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ["id", "get_full_name", "get_email", "get_phone"]

    def get_full_name(self, obj):
        return obj.user.full_name
    get_full_name.admin_order_field = "user__full_name"
    get_full_name.short_description = "Full Name"

    def get_email(self, obj):
        return obj.user.email
    get_email.admin_order_field = "user__email"
    get_email.short_description = "Email"

    def get_phone(self, obj):
        return obj.user.phone
    get_phone.admin_order_field = "user__phone"
    get_phone.short_description = "Phone"


# @admin.register(HostProfile)
# class HostAdmin(admin.ModelAdmin):
#     list_display = [
#         "id",
#         "get_full_name",
#         "get_email",
#         "get_phone",
#         "address",
#         "city",
#         "state",
#         "zip_code"
#     ]

#     def get_full_name(self, obj):
#         return obj.user.full_name
#     get_full_name.admin_order_field = "user__full_name"
#     get_full_name.short_description = "Full Name"

#     def get_email(self, obj):
#         return obj.user.email
#     get_email.admin_order_field = "user__email"
#     get_email.short_description = "Email"

#     def get_phone(self, obj):
#         return obj.user.phone
#     get_phone.admin_order_field = "user__phone"
#     get_phone.short_description = "Phone"