from django.urls import path
from .views import *
from rest_framework_simplejwt.views import (
    TokenRefreshView,
)
urlpatterns = [
    path('AdminRegistration',AdminRegistration.as_view(),name='AdminRegistration'),
    path('AdminLogin',AdminLogin.as_view(),name='AdminLogin'),
    path('GetUpdateApproveEWARequest',GetUpdateApproveEWARequest.as_view(),name='GetUpdateApproveEWARequest'),]