from rest_framework import serializers
from .models import CustomUser


class UserDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['business_name', 'full_name', 'email', 'password', 'business_type', 'country', 'currency', 'state', 'low_stock_threshold']

    def create(self, validated_data):
        """
        Create, Saves and return a new `CustomUser` instance, given the validated data.
        """
        unhashed_password = validated_data["password"]
        del validated_data["password"]
        new_user = CustomUser(**validated_data)
        new_user.set_password(unhashed_password)
        new_user.save()
        return new_user

class LoginDataSerializer(serializers.Serializer):
    email = serializers.CharField(max_length=150)
    password = serializers.CharField(max_length=50)
