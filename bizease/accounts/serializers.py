from rest_framework import serializers
from .models import CustomUser



class ProfileDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            'business_name', 'full_name', 'email', 'business_type', 'country', 'currency', 
            'state', 'rcv_mail_for_new_orders', 'rcv_mail_for_low_stocks', 'phone', 'business_phone',
            'business_address','rcv_mail_notification', 'rcv_msg_notification', 'default_order_status',
            'language', 'low_stock_threshold'
        ]
        
class SignUpDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['business_name', 'full_name', 'email', 'password', 'business_type', 'country', 'currency', 'state']

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


from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

