from rest_framework import serializers
from .models import Report


class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = ['id', 'title', 'email', 'created_at', 'updated_at', 'report_type']
        read_only_fields = ['id', 'created_at', 'updated_at']
    def create(self, validated_data):
        report = Report.objects.create(*validated_data)
        return report



