from django.db import models
from django.db import models
from tinymce.models import HTMLField


# Create your models here.
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