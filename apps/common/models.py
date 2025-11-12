from django.db import models
from tinymce.models import HTMLField
from apps.accounts.models import User


class HelpSupport(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField()
    subject = models.CharField(max_length=255)
    message = models.TextField()

    class Meta:
        verbose_name_plural = "Help & Support"

    def __str__(self):
        return self.name
    

class PrivacyPolicy(models.Model):
    content = HTMLField()

    class Meta:
        verbose_name_plural = 'Privacy Policy'

    def __str__(self):
        return "Privacy Policy"
    

class TermsConditions(models.Model):
    content = HTMLField()

    class Meta:
        verbose_name_plural = 'Terms & Conditions'

    def __str__(self):
        return "Terms & Conditions"
    



class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.email}"