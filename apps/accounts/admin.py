from django import forms
from django.contrib import admin
from unfold.admin import ModelAdmin
from apps.accounts.models import User, Profile
from django.core.exceptions import ValidationError
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField



# ----------------------------
# Custom Forms
# ----------------------------

class UserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirm Password", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ["full_name", "email"]

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError("Passwords do not match.")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField(label="Hashed Password")

    class Meta:
        model = User
        fields = [
            "full_name", "email", "password",
            "is_active", "is_staff", "is_superuser"
        ]


# ----------------------------
# User Admin
# ----------------------------

@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):  # inherit unfold.ModelAdmin
    form = UserChangeForm
    add_form = UserCreationForm

    list_display = [
        "id", "full_name", "email", "role", "phone",
        "stripe_account_id", "stripe_customer_id",
        "is_active", "is_staff", "is_superuser"
    ]
    list_filter = ["is_active", "is_staff", "is_superuser", "role"]
    search_fields = ["email", "full_name", "phone"]
    ordering = ["email"]
    readonly_fields = ["stripe_account_id", "stripe_customer_id"]

    # --- FIELD GROUPING ---
    fieldsets = [
        ("🧑 Basic Info", {"fields": ["full_name", "email", "password", "role", "phone"]}),
        ("💳 Stripe Integration", {"fields": ["stripe_account_id", "stripe_customer_id"]}),
        ("⚙️ Permissions", {"fields": ["is_active", "is_staff", "is_superuser", "groups", "user_permissions"]}),
    ]

    add_fieldsets = [
        (
            "Create New User",
            {
                "classes": ["wide"],
                "fields": ["full_name", "email", "password1", "password2"],
            },
        ),
    ]

    # --- UNFOLD CUSTOMIZATION ---
    unfold_config = {
        "list_display": {
            "columns": [
                {"name": "ID", "sortable": True},
                {"name": "Full Name", "sortable": True},
                {"name": "Email", "sortable": True},
                {"name": "Role", "sortable": True},
                {"name": "Phone", "sortable": False},
                {"name": "Active", "sortable": True},
                {"name": "Staff", "sortable": True},
            ],
            "search_enabled": True,
        },
        "edit_form": {
            "title": "Edit User",
            "layout": [
                ("full_name", "email"),
                ("role", "phone"),
                ("is_active", "is_staff", "is_superuser"),
                ("stripe_account_id", "stripe_customer_id"),
            ],
            "save_button": "Save Changes",
        },
        "buttons": [
            {"name": "Add User", "icon": "plus", "url": "user:add"},
            {"name": "Export Users", "icon": "download"},
        ],
    }

    def unfold_ui_config(self):
        return self.unfold_config


# ----------------------------
# Profile Admin
# ----------------------------

@admin.register(Profile)
class ProfileAdmin(ModelAdmin):
    list_display = ["id", "get_full_name", "get_email", "get_phone"]
    search_fields = ["user__full_name", "user__email", "user__phone"]

    def get_full_name(self, obj):
        return obj.user.full_name
    get_full_name.short_description = "Full Name"
    get_full_name.admin_order_field = "user__full_name"

    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = "Email"
    get_email.admin_order_field = "user__email"

    def get_phone(self, obj):
        return obj.user.phone
    get_phone.short_description = "Phone"
    get_phone.admin_order_field = "user__phone"

    # --- UNFOLD CONFIGURATION ---
    unfold_config = {
        "list_display": {
            "columns": [
                {"name": "ID", "sortable": True},
                {"name": "Full Name", "sortable": True},
                {"name": "Email", "sortable": True},
                {"name": "Phone", "sortable": True},
            ],
            "search_enabled": True,
        },
        "edit_form": {
            "title": "Edit Profile",
            "layout": [
                ("user",),
                ("profile_picture", "bio"),
            ],
            "save_button": "Save Profile",
        },
    }

    def unfold_ui_config(self):
        return self.unfold_config