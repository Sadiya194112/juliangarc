from rest_framework import serializers
from .models import *


# Create your serializers here.
class PrivacyPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = PrivacyPolicy
        fields = "__all__"


class TermsConditionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TermsConditions
        fields = "__all__"


class SupportSerializer(serializers.ModelSerializer):
    class Meta:
        model = HelpSupport
        fields = "__all__"