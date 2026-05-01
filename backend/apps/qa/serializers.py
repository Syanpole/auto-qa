from rest_framework import serializers
from .models import QAStation, ProductProfile, StationThreshold, DefectEvent


class QAStationSerializer(serializers.ModelSerializer):
    class Meta:
        model = QAStation
        fields = "__all__"


class ProductProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductProfile
        fields = "__all__"


class StationThresholdSerializer(serializers.ModelSerializer):
    class Meta:
        model = StationThreshold
        fields = "__all__"


class DefectEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = DefectEvent
        fields = "__all__"
