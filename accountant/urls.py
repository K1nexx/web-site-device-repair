from django.urls import path
from . import views

urlpatterns = [

    path('', views.accountant, name='accountant'),
    path('orders/', views.accountant_orders, name='accountant_orders'),
    path('salaries/', views.manage_salaries, name='manage_salaries')
]