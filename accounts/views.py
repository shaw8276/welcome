import re
from accounts.models import Profile
from django.shortcuts import render,redirect
from django.contrib.auth.models import User
from django.contrib import messages
from .models import *
import uuid
from django.conf import settings
from django.core.mail import message, send_mail
from django.contrib.auth import authenticate, login ,logout
from django.contrib.auth.decorators import login_required

# Create your views here.

@login_required(login_url="/accounts/user")
def home(request):
    return render(request,'home.html')

def login_attempt(request):
    if request.method=='POST':
        username=request.POST.get('username')
        password=request.POST.get('password')

        user_obj=User.objects.filter(username=username).first()
        if user_obj is None:
            messages.success(request,'username not found')
            return redirect('/login')
        
        profile_obj=Profile.objects.filter(user = user_obj).first()

        if not profile_obj.is_verified:
            messages.success(request,'Profile is not verifed check your mail.')
            return redirect('/login')

        user = authenticate(username=username , password=password)
        if user is None:
            messages.success(request,'Wrong password')
            return redirect('/login')
        
        login(request, user)
        return redirect('/accounts/user')




    return render(request,'login.html')

def register_attempt(request):
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            if User.objects.filter(username = username).first():
                messages.success(request,'Username is taken')
                return redirect('/register')

            if User.objects.filter(email=email).first():
                messages.success(request,'Email is taken.')
                return redirect('/register')

            user_obj = User.objects.create(username=username , email=email)
            user_obj.set_password(password)
            user_obj.save()
            auth_token=str(uuid.uuid4())
            Profile_obj=Profile.objects.create(user=user_obj,auth_token= auth_token)
            Profile_obj.save()
            send_mail_registration(email,auth_token,username)
            return redirect('/token_send')
            
        except Exception as e:
            print(e)

    return render(request,'register.html')

def success(request):
    return render(request,'success.html')

def token_send(request):
    return render(request,'token_send.html')


def verify(request,auth_token):
    try:
        Profile_obj=Profile.objects.filter(auth_token=auth_token).first()
        if Profile_obj:
            if Profile_obj.is_verified:
                messages.success(request,'Your account is already verified.')
                return redirect('/login')

            Profile_obj.is_verified = True
            Profile_obj.save()
            messages.success(request, 'Your account has been verified.')
            return redirect('/success')
        else:
            return redirect('/error')
    except Exception as e:
        print(e)

def Redirect(request):
    return redirect('login_attempt')

def error_page(request):
    return render(request, 'error.html')

def logout_request(request):
    logout(request)
    messages.info(request,"You Logged out succesfully!.")
    return redirect('/')

def send_mail_registration(email,token,name):
    subject = 'Your accounts need to be verified'
    message = f'Hi { name } paste the link to verify your account http://127.0.0.1:8000/verify/{ token }'
    email_from = settings.EMAIL_HOST_USER
    recipient_list = [email ]
    send_mail(subject,message,email_from,recipient_list)