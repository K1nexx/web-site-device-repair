from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('', views.manager, name='manager'),
    path('create-order/', views.create_order, name='create_order'),
    path('order-history/', views.order_history, name='order_history')
]