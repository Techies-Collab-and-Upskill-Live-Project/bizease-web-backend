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
        read_only_fields = ['email']

    def validate(self, data):
        """ Checks for any unwanted fields """
        expected_validated_data = {} # will be used to hold only values from Meta.fields
        good = True

        for field in self.Meta.fields:
            field_value = self.initial_data.get(field)
            if field_value and field not in self.Meta.read_only_fields:
                expected_validated_data[field] = field_value
                del self.initial_data[field]

        for key in self.initial_data:
            self.initial_data[key] = ["Unexpected field"]
            good = False

        if not good:
            return {"field_errors": self.initial_data}
        return data
        
class SignUpDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['business_name', 'full_name', 'email', 'password', 'business_type', 'country', 'currency', 'state']

    def create(self, validated_data):
        """
        Create, Saves and return a new `CustomUser` instance, given the validated data.
        """
        if (validated_data.get("country")):
            validated_data["country"] = validated_data["country"].title()
        if (validated_data.get("currency")):
            validated_data["currency"] = validated_data["currency"].title()
        unhashed_password = validated_data["password"]
        del validated_data["password"]
        new_user = CustomUser(**validated_data)
        new_user.set_password(unhashed_password)
        new_user.save()
        return new_user
    
class LoginDataSerializer(serializers.Serializer):
    email = serializers.CharField(max_length=150)
    password = serializers.CharField(max_length=50)






