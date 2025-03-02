from django.shortcuts import render
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser,JSONParser
import random
from .managers import *
from django.shortcuts import get_object_or_404
from .models import *
from .utils import *
from .serializers import *
from django.conf import settings
# Create your views here.
TEST_MOBILE = 1239956739
STATIC_OTP = 612743

class UserSendOTP(APIView):
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        user_type = request.data.get('user_type')
        mobile = request.data.get('mobile')
        if mobile == TEST_MOBILE:
            otp = STATIC_OTP
            print(f"Test user login: Mobile {mobile}, using static OTP {otp}")
        else:
            otp = random.randint(100000, 999999)
            print(f"Generated OTP: {otp}")

        try:
                user = CustomUser.objects.filter(mobile=mobile, user_type=user_type).first()
                is_existing_user = Employee.objects.filter(user=user).exists() if user else False
                if user:
                    sendmobile_otp(mobile, otp)
                    store_otp(mobile, otp)
                    return Response({
                        'message': f"OTP sent successfully to {user.mobile}",
                        'otp': otp,
                        'is_existing_user': is_existing_user
                    }, status=status.HTTP_200_OK)
                else:
                    sendmobile_otp(mobile, otp)
                    store_otp(mobile, otp)
                    return Response({
                        'message': f"OTP sent successfully to {mobile}",
                        'otp': otp,
                        'is_existing_user': False
                    }, status=status.HTTP_200_OK)

        except Exception as e:
            return handle_exception(e,"An error occurred while Sending OTP")

#################------------------------------------------Verify Otp-------------------###############
class VerifyOTP(APIView):
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        mobile = request.data.get("mobile")
        otp = request.data.get("otp")
        user_type = request.data.get("user_type")

        if not mobile or not otp or not user_type:
            return Response({"error": "Mobile number, OTP, and user type are required"}, status=status.HTTP_400_BAD_REQUEST)

        if mobile == TEST_MOBILE and otp == STATIC_OTP:
            print(f"Test user verified with static OTP {STATIC_OTP}")

            user, created = CustomUser.objects.get_or_create(mobile=TEST_MOBILE, defaults={"user_type": user_type})
            is_existing_user = Employee.objects.filter(user=user).exists()
            
            return Response({
                "message": "Test user OTP verified successfully", 
                "is_existing_user": is_existing_user
            }, status=status.HTTP_200_OK)

        else:
            otp_record = OTPVerification.objects.filter(otp=otp, mobile=mobile).order_by("-expires_at").first()
            if not otp_record or otp_record.expires_at < timezone.now():
                return Response({"error": "Invalid or expired OTP"}, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if user exists and is an onboarded employee
            user = CustomUser.objects.filter(mobile=mobile, user_type=user_type).first()
            is_existing_user = Employee.objects.filter(user=user).exists() if user else False
            otp_record.delete()
            
            # If user exists and is onboarded, generate token immediately
            if user and is_existing_user:
                tokens = create_gig_token(user, user_type)
                return Response({
                    "message": "OTP verified successfully.",
                    "is_existing_user": True,
                    "tokens": tokens
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "message": "OTP verified successfully. Please complete employee details.",
                    "is_existing_user": False,
                }, status=status.HTTP_200_OK)

###################3---------------------------------Employee LOGIN
class EmployeeLogin(APIView):
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        employee_id = request.data.get("employee_id")
        mobile = request.data.get("mobile")
        name=request.data.get("name")
        user_type=request.data.get("user_type")

        if not employee_id or not mobile:
            return Response({"error": "Employee ID and mobile are required"}, status=400)

        employer = Employeer.objects.filter(associated_employee_id=employee_id).first()
        if not employer:
            return Response({"error": "No employer found with this Employee ID"}, status=400)
        try:
            #---Check Existing User
            user=CustomUser.objects.filter(mobile=mobile,user_type=user_type)
            if user:
                tokens=create_gig_token(user,user_type)
                return Response({"message": "Employee Login Successful", "tokens": tokens, "is_existing_user": True}, status=200)
            else:
                ##------------Create User
                serializer = EmployeeRegistrationSerializer(
                data={"mobile": mobile, "user_type": user_type, "employee_id": employee_id, "name": name},
                user_type=user_type
            )
            if serializer.is_valid():
                user = serializer.save()
            else:
                return Response(serializer.errors, status=400)
            tokens = create_gig_token(user, user_type)
            return Response({
                "message": "User created & login successful",
                "tokens": tokens,
                "is_existing_user": False
                }, status=200)
        except Exception as e:
            return handle_exception(e,"An error occurred while logging in")
            
###########################-------------------------------Employee Verification
class EmployeeVerification(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    def post(self, request, format=None):
        user = request.user
        provided_access_token = request.META.get('HTTP_AUTHORIZATION', '').split(' ')[-1]

        if user.access_token!= provided_access_token:
            return Response({'error': 'Access token is invalid or has been replaced.'}, status=status.HTTP_401_UNAUTHORIZED)

        if user.user_type!= "gigaff":
            return Response({'error': 'Only Giugs can view Request'}, status=status.HTTP_403_FORBIDDEN)
        try:
            employee=get_object_or_404(Employee,user=user)
            verification, created = EmployeeVerification.objects.get_or_create(employee=employee)

            serializer = EmployeeVerificationSerializer(verification, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({"message": "Verification details updated successfully."}, status=status.HTTP_200_OK)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return handle_exception(e,"An error occurred while updating verification details")
 
################--------------------------Refersh Token-------------------####################
class EmployeeTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        if response.status_code == status.HTTP_200_OK:
            access_token = response.data.get("access")
            refresh_token = request.data.get("refresh")
            try:
                refresh_token_obj = RefreshToken(refresh_token)
                user_id = refresh_token_obj["user_id"]
                print(f"User ID: {user_id}")

                user = CustomUser.objects.get(id=user_id)
                print(f"User is: {user}")
                if user.id == user_id:  
                    user.access_token = access_token
                    user.token_expires_at = timezone.now() + settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'] 
                    user.save()
                else:
                    return Response({"error": "Invalid user"}, status=status.HTTP_403_FORBIDDEN)

            except CustomUser.DoesNotExist:
                return Response({"error": "Farmer not found"}, status=status.HTTP_404_NOT_FOUND)

        return response
    

#################----------------------Get EWA Balance-------------------#################
class GetEwaBalance(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, format=None):
        user = request.user
        provided_access_token = request.META.get('HTTP_AUTHORIZATION', '').split(' ')[-1]

        if user.access_token!= provided_access_token:
            return Response({'error': 'Access token is invalid or has been replaced.'}, status=status.HTTP_401_UNAUTHORIZED)

        if user.user_type!= "gigaff":
            return Response({'error': 'Only Giugs can view Request'}, status=status.HTTP_403_FORBIDDEN)
        employee_id=request.query_params.get('employee_id')
        if not employee_id:
            return Response({"error": "Employee ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            employee=get_object_or_404(Employee,user=user,employee_id=employee_id)
            salary_details = SalaryDetails.objects.filter(employee=employee).first()

            if not salary_details or salary_details.employment_status != "active":
                return Response({"error": "Employee is not active or has no salary details"}, status=status.HTTP_404_NOT_FOUND)
            earned_wages = salary_details.calculate_earned_wages()
            return Response({'message':'success', 'salary_details':earned_wages},status=status.HTTP_200_OK)
        except Exception as e:
            return handle_exception(e,"An error occurred while fetching EWA balance")