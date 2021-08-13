from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path
from . import views

urlpatterns = [
    path('',views.Redirect),
    path('accounts/user', views.home,name="home"),
    path('register',views.register_attempt,name="register_attempt"),
    path('login',views.login_attempt,name="login_attempt"),
    path('success',views.success,name="success"),
    path('token_send',views.token_send,name="token_send"),
    path('verify/<auth_token>',views.verify,name="verify"),
    path('error',views.error_page,name="error"),
    path("logout", views.logout_request, name="logout"),
]
