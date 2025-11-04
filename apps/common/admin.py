from django.contrib import admin
from apps.common.models import HelpSupport, PrivacyPolicy, TermsConditions, Notification


# Register your models here.
admin.site.register(HelpSupport)
admin.site.register(PrivacyPolicy)
admin.site.register(TermsConditions)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'message', 'is_read']