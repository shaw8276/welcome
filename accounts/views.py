import re
from accounts.models import Profile
from django.shortcuts import render,redirect
import razorpay
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseBadRequest
from django.contrib.auth.models import User
from django.contrib import messages
from .models import *
import uuid
from django.conf import settings
from django.core.mail import message, send_mail
from django.contrib.auth import authenticate, login ,logout
from django.contrib.auth.decorators import login_required

# authorize razor pay client
razorpay_client = razorpay.Client(
    auth=(settings.RAZOR_KEY_ID, settings.RAZOR_KEY_SECRET))
# Create your views here.

@login_required(login_url="/accounts/user")
def home(request):
    currency = 'INR'
    amount = 20000  # Rs. 200
    # Create a Razorpay Order
    razorpay_order = razorpay_client.order.create(dict(amount=amount,currency=currency, payment_capture='0'))
    # order id of newly created order.
    razorpay_order_id = razorpay_order['id']
    callback_url = 'paymenthandler/'
    # we need to pass these details to frontend.
    context = {}
    context['razorpay_order_id'] = razorpay_order_id
    context['razorpay_merchant_key'] = settings.RAZOR_KEY_ID
    context['razorpay_amount'] = amount
    context['currency'] = currency
    context['callback_url'] = callback_url

    return render(request, 'home.html', context=context)  

# we need to csrf_exempt this url as
# POST request will be made by Razorpay
# and it won't have the csrf token.
@csrf_exempt
def paymenthandler(request):
 

    # only accept POST request.

    if request.method == "POST":

        try:

           

            # get the required parameters from post request.

            payment_id = request.POST.get('razorpay_payment_id', '')

            razorpay_order_id = request.POST.get('razorpay_order_id', '')

            signature = request.POST.get('razorpay_signature', '')

            params_dict = {

                'razorpay_order_id': razorpay_order_id,

                'razorpay_payment_id': payment_id,

                'razorpay_signature': signature

            }
 

            # verify the payment signature.

            result = razorpay_client.utility.verify_payment_signature(

                params_dict)

            if result is None:

                amount = 20000  # Rs. 200

                try:
 

                    # capture the payemt

                    razorpay_client.payment.capture(payment_id, amount)
 

                    # render success page on successful caputre of payment

                    return render(request, 'paymentsuccess.html')

                except:
 

                    # if there is an error while capturing payment.

                    return render(request, 'paymentfail.html')

            else:
 

                # if signature verification fails.

                return render(request, 'paymentfail.html')

        except:
 

            # if we don't find the required parameters in POST data

            return HttpResponseBadRequest()

    else:

       # if other than POST request is made.

        return HttpResponseBadRequest()

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