from rest_framework import serializers
from .managers import *
from .models import *


class EmployeeRegistrationSerializer(serializers.ModelSerializer):
    employee_id = serializers.CharField(max_length=100, required=False)
    name = serializers.CharField(required=False)
    mobile = serializers.CharField()
    user_type = serializers.ChoiceField(choices=['gigaff', 'nongigaff'])
    class Meta:
        model = CustomUser
        fields = ['mobile', 'user_type','employee_id','name']

    def __init__(self, *args, **kwargs):
        self.user_type = kwargs.pop('user_type', None)
        super().__init__(*args, **kwargs)

    def create(self, validated_data):
        if self.user_type is None:
            raise ValueError("user_type must be provided")
        employee_id = validated_data.pop('employee_id', None)
        name = validated_data.pop('name', None)

        user = CustomUser.objects.create_user(
            mobile=validated_data.get('mobile'),
            user_type=self.user_type
        )

        if self.user_type == 'gigaff':
            Employee.objects.create(user=user, mobile=user.mobile,employee_id=employee_id,name=name)
        else:
            raise ValueError("Invalid user type")

        print(f"Created {self.user_type} user: {user} with Mobile: {user.mobile}")
        return user
    

############---------------------------Employee VERIFICATIONS
class EmployeeVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeVerification
        fields = ['pan_number', 'aadhar_number', 'selfie', 'video_kyc', 'is_verified']