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
from django.contrib.auth.hashers import check_password,make_password
from gigworkers.managers import *
from django.db.models import Q
from django.shortcuts import get_object_or_404
from .models import *
from gigworkers.utils import *
from .serializers import *
from django.conf import settings
##----------1.User Registration
class AdminRegistration(APIView):
    permission_classes = [AllowAny]
    def post(self, request, format=None):
        user_type = request.data.get('user_type')
        mobile = request.data.get('mobile')
        email = request.data.get('email')
        password = request.data.get('password')
        name = request.data.get('name')
        role=request.data.get('role')
        user_language=request.data.get('user_language',2)
        ip_address = request.META.get('REMOTE_ADDR')
        print(f"Registration attempt with mobile: {mobile}, user_type: {user_type}, password: {password}, IP address: {ip_address} ,Role is :{role} Lang is :{user_language}")
        try:
            user = CustomUser.objects.filter(
            Q(email=email, user_type=user_type) | Q(mobile=mobile, user_type=user_type)
            ).exists()

            print(f"User is :{user}")
            if user:
                return Response({'error': 'User with this mobile number or email already exists for the same user type'}, 
                            status=status.HTTP_400_BAD_REQUEST)
            serializer = AdminRegistrationSerializer(data=request.data)
            #print(f"Serialized Data :{serializer.data}")
            if serializer.is_valid():
                user = serializer.save()
                subject = 'Welcome to Our Platform!'
                content = f"""
                Dear {name},

                Welcome to our platform! Your registration was successful.

                Here are your login details:

                Email: {email}

                Password: {password}

                Please log in to start using our services.

                Best regards,
                Agrisarthi
                """
                send_email(subject,content,email)
                return Response({'message': 'User registered successfully'}, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error_message = str(e)
            trace = traceback.format_exc()
            return Response(
                {
                    "status": "error",
                    "message": "An unexpected error occurred",
                    "error_message": error_message,
                    "traceback": trace
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
                
####################-------------------------------------REST API's Login----------------###############
class AdminLogin(APIView):
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        serializer = AdminLoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        user_type = serializer.validated_data['user_type']
        ip_address = request.META.get('REMOTE_ADDR')

        print(f"Login attempt with email: {email}, user_type: {user_type}, IP address: {ip_address}")

        try:
            user = CustomUser.objects.filter(email=email, user_type=user_type).first()
            if not user:
                return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

            if check_password(password, user.password):
                tokens = create_gig_token(user, user_type)
                return Response({
                    'message': "User logged in successfully",
                    'tokens': tokens
                }, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Invalid Credentials'}, status=status.HTTP_401_UNAUTHORIZED)

        except Exception as e:
            error_message = str(e)
            trace = traceback.format_exc()
            return Response(
                {
                    "status": "error",
                    "message": "An unexpected error occurred during login",
                    "error_message": error_message,
                    "traceback": trace
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
            
#################----------------------Approve EWA Request By Loan Admin
class GetUpdateApproveEWARequest(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, format=None):
        user = request.user
        provided_access_token = request.META.get('HTTP_AUTHORIZATION', '').split(' ')[-1]
        if user.access_token!= provided_access_token:
            return Response({'error': 'Access token is invalid or has been replaced.'}, status=status.HTTP_401_UNAUTHORIZED)
        if user.user_type!= "admin":
            return Response({'error': 'Only Admin can view Request'}, status=status.HTTP_403_FORBIDDEN)
        request_id=request.data.get('request_id')
        if not request_id:
            return Response({'error': 'Request ID is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            admin=get_object_or_404(LoanAdmin,user=user)
            ewa_request = get_object_or_404(EWARequest, id=request_id,processed_by=admin)
            ewa_request.status = "approved"
            ewa_request.save()
            return Response({'message': 'EWA Request approved successfully'}, status=status.HTTP_200_OK)
        except Exception as e:
            return handle_exception(e,"An error Ocuured while Updating EWA Request")
        
    def get(self,request,format=None):
        user = request.user
        provided_access_token = request.META.get('HTTP_AUTHORIZATION', '').split(' ')[-1]
        if user.access_token!= provided_access_token:
            return Response({'error': 'Access token is invalid or has been replaced.'}, status=status.HTTP_401_UNAUTHORIZED)
        if user.user_type!= "admin":
            return Response({'error': 'Only Admin can view Request'}, status=status.HTTP_403_FORBIDDEN)
        try:
            admin=get_object_or_404(LoanAdmin,user=user)
            ewa_requests = EWARequest.objects.filter(processed_by=admin,status="pending")
            paginator=CurrentNewsPagination()
            result_page=paginator.paginate_queryset(ewa_requests, request)
            serializer = EWARequestSerializer(result_page, many=True)
            return paginator.get_paginated_response({
                        'status': 'success',
                        'data': serializer.data,
                    })
        except Exception as e:
            return handle_exception(e,"An error Ocuured while fetching EWA Requests")
            
        
