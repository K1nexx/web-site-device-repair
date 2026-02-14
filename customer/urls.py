# urls.py
from django.urls import path
from . import views

urlpatterns = [

    path('', views.customer, name='customer'),
    path('update-info/', views.update, name='update_customer_info'),
]