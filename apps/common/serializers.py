from rest_framework import serializers
from apps.common.models import PrivacyPolicy, TermsConditions, HelpSupport


# Create your serializers here.
class PrivacyPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = PrivacyPolicy
        fields = ['id', 'content']


class TermsConditionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TermsConditions
        fields = ['id', 'content']

class SupportSerializer(serializers.ModelSerializer):
    class Meta:
        model = HelpSupport
        fields = ['name', 'email', 'subject', 'message']