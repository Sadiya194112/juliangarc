from django.contrib import admin
from unfold.admin import ModelAdmin
from apps.common.models import HelpSupport, PrivacyPolicy, TermsConditions, Notification


# ----------------------------
# Help & Support Admin
# ----------------------------
@admin.register(HelpSupport)
class HelpSupportAdmin(ModelAdmin):
    list_display = ["id", "name", "email", "subject", "message"]
    search_fields = ["name", "email", "subject"]
    list_per_page = 20

    unfold_config = {
        "list_display": {
            "columns": [
                {"name": "ID", "sortable": True},
                {"name": "Name", "sortable": True},
                {"name": "Email", "sortable": True},
                {"name": "Subject", "sortable": True},
                {"name": "Message", "sortable": False},
            ],
            "search_enabled": True,
        },
        "edit_form": {
            "title": "Help & Support Ticket",
            "layout": [
                ("name", "email"),
                ("subject",),
                ("message",),
            ],
            "save_button": "Save Ticket",
        },
        "buttons": [
            {"name": "Add New Ticket", "icon": "plus", "url": "helpsupport:add"},
        ],
    }

    def unfold_ui_config(self):
        return self.unfold_config


# ----------------------------
# Privacy Policy Admin
# ----------------------------
@admin.register(PrivacyPolicy)
class PrivacyPolicyAdmin(ModelAdmin):
    list_display = ["id", "short_content"]
    search_fields = ["content"]

    def short_content(self, obj):
        return f"{obj.content[:70]}..." if len(obj.content) > 70 else obj.content
    short_content.short_description = "Preview"

    unfold_config = {
        "list_display": {
            "columns": [
                {"name": "ID", "sortable": True},
                {"name": "Content Preview", "sortable": False},
            ],
            "search_enabled": True,
        },
        "edit_form": {
            "title": "Privacy Policy",
            "layout": [
                ("content",),
            ],
            "save_button": "Update Policy",
        },
    }

    def unfold_ui_config(self):
        return self.unfold_config


# ----------------------------
# Terms & Conditions Admin
# ----------------------------
@admin.register(TermsConditions)
class TermsConditionsAdmin(ModelAdmin):
    list_display = ["id", "short_content"]
    search_fields = ["content"]

    def short_content(self, obj):
        return f"{obj.content[:70]}..." if len(obj.content) > 70 else obj.content
    short_content.short_description = "Preview"

    unfold_config = {
        "list_display": {
            "columns": [
                {"name": "ID", "sortable": True},
                {"name": "Content Preview", "sortable": False},
            ],
            "search_enabled": True,
        },
        "edit_form": {
            "title": "Terms & Conditions",
            "layout": [
                ("content",),
            ],
            "save_button": "Update Terms",
        },
    }

    def unfold_ui_config(self):
        return self.unfold_config


# ----------------------------
# Notification Admin
# ----------------------------
@admin.register(Notification)
class NotificationAdmin(ModelAdmin):
    list_display = ["id", "user", "short_message", "is_read", "created_at"]
    list_filter = ["is_read", "created_at"]
    search_fields = ["user__email", "message"]
    readonly_fields = ["created_at"]
    list_per_page = 25

    def short_message(self, obj):
        return f"{obj.message[:50]}..." if len(obj.message) > 50 else obj.message
    short_message.short_description = "Message Preview"

    unfold_config = {
        "list_display": {
            "columns": [
                {"name": "ID", "sortable": True},
                {"name": "User", "sortable": True},
                {"name": "Message Preview", "sortable": False},
                {"name": "Read", "sortable": True},
                {"name": "Created At", "sortable": True},
            ],
            "search_enabled": True,
        },
        "edit_form": {
            "title": "Notification Details",
            "layout": [
                ("user", "is_read"),
                ("message",),
                ("created_at",),
            ],
            "save_button": "Save Notification",
        },
        "buttons": [
            {"name": "Create Notification", "icon": "plus", "url": "notification:add"},
            {"name": "Mark All as Read", "icon": "check-circle"},
        ],
    }

    def unfold_ui_config(self):
        return self.unfold_config
