from django.db import models
from .managers import *
from django.utils import timezone

#------------------------------EMPLOYERR MODELS
class Employeer(models.Model):
    name = models.CharField(max_length=100,null=True, blank=True)
    associated_employee_id= models.CharField(max_length=100, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    is_partnership = models.BooleanField(default=False)

####---------------------------OTP Verification
class OTPVerification(models.Model):
    mobile = models.CharField(null=True, blank=True, max_length=10, validators=[validate_mobile_no], unique=True)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def is_valid(self):
        return timezone.now() < self.expires_at
###############-------------------Employee Model
class Employee(models.Model):
    user=models.OneToOneField(CustomUser,on_delete=models.CASCADE,null=True,blank=True,related_name='gig_withemoployer')
    employeer = models.ForeignKey(Employeer, on_delete=models.CASCADE,null=True, blank=True)
    employee_id= models.CharField(max_length=100, null=True, blank=True)
    name = models.CharField(max_length=100, null=True, blank=True)
    mobile = models.CharField(max_length=10, validators=[validate_mobile_no])
    gender=models.CharField(null=True, blank=True, max_length=100)
    created = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)


class EmployeeVerification(models.Model):
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE,null=True,blank=True, related_name='verification')
    pan_number = models.CharField(max_length=10, unique=True, null=True, blank=True)
    aadhar_number = models.CharField(max_length=12, unique=True, null=True, blank=True)
    selfie = models.ImageField(upload_to='selfies/', null=True, blank=True)
    video_kyc = models.FileField(upload_to='video_kyc/', null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

###############-----------------------Employee Salary History
class SalaryHistory(models.Model):
    """Tracks past salaries and payments for employees"""
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="salary_history")
    salary_amount = models.DecimalField(max_digits=10, decimal_places=2) 
    start_date = models.DateField()  
    end_date = models.DateField()  
    days_paid = models.IntegerField()  
    created_at = models.DateTimeField(auto_now_add=True)  

    def __str__(self):
        return f"{self.employee.name} - {self.start_date} to {self.end_date}"
# ------------------------------ Salary Details Model
class SalaryDetails(models.Model):
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name="salary_details")
    salary_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    employment_status = models.CharField(max_length=50, choices=[("active", "Active"), ("inactive", "Inactive")])
    last_salary_date = models.DateField(null=True, blank=True)  # Last salary paid date
    daily_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Salary per day
    earned_wages = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Wages earned till now
    ewa_limit = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    last_updated = models.DateTimeField(auto_now=True)

    def calculate_earned_wages(self):
        """Calculate earned wages based on the days worked since last salary."""
        if not self.last_salary_date:
            return 0  # No earnings if no salary has been paid before

        days_worked = (timezone.now().date() - self.last_salary_date).days
        self.earned_wages = self.daily_salary * days_worked
        self.ewa_limit = self.earned_wages  
        self.save()
        return self.earned_wages

    def __str__(self):
        return f"Salary for {self.employee.name} - {self.salary_amount}"