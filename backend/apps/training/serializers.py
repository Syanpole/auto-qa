from rest_framework import serializers
from .models import DatasetVersion, TrainingJob, ModelRegistry, ModelAccess, StationModelAssignment


class DatasetVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DatasetVersion
        fields = "__all__"


class TrainingJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainingJob
        fields = "__all__"


class ModelRegistrySerializer(serializers.ModelSerializer):
    class Meta:
        model = ModelRegistry
        fields = "__all__"


class ModelAccessSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModelAccess
        fields = "__all__"


class StationModelAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = StationModelAssignment
        fields = "__all__"
