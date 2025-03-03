from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken,TokenError
from gigworkers.managers import *
from .models import *
from gigworkers.models import *

######----------------------Admin Reigistration
class AdminRegistrationSerializer(serializers.Serializer):
    mobile = serializers.CharField()
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    user_type = serializers.ChoiceField(choices=['admin'])
    name = serializers.CharField(required=False)

    def create(self, validated_data):
        user_type = validated_data['user_type']
        name = validated_data.pop('name', None)
        user = CustomUser.objects.create_user(
            mobile=validated_data['mobile'],
            password=validated_data['password'],
            user_type=user_type,
            name=name,
            email=validated_data['email']
        )
        if user_type == 'admin':
            if not name:
                raise serializers.ValidationError({"name": "Name is required for Admin users."})
            LoanAdmin.objects.create(user=user, mobile=user.mobile,name=name,password=user.password,
                                    email=user.email)
        else:
            user.delete()  
            raise serializers.ValidationError({"user_type": "Invalid user type."})
        
        

        print(f"Created {user_type} user: {user}")
        return user

    def validate(self, data):
        user_type = data.get('user_type')
        name = data.get('name')
        print(f"Validating {user_type} Validation Name: {name}")

        if user_type in ['admin'] and not name:
            raise serializers.ValidationError({"name": f"Name is required for {user_type.upper()} users."})

        return data
    
class AdminLoginSerializer(serializers.Serializer):
    email = serializers.CharField()
    password = serializers.CharField(write_only=True)
    user_type = serializers.ChoiceField(choices=['admin'])
    
    
#########################--------------------------EWA Request Serializers-------------------------########
class EWARequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = EWARequest
        fields = '__all__'