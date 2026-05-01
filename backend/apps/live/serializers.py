from rest_framework import serializers
from .models import LiveScreenSession, LiveScreenAccessEvent


class LiveScreenSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = LiveScreenSession
        fields = "__all__"


class LiveScreenAccessEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = LiveScreenAccessEvent
        fields = "__all__"
