from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='homepage'),
    #path('view/<str:table_name>/', views.view_table, name='view_table'),
    #path('add/<str:table_name>/', views.add_record, name='add_record'),
    #path('edit/<str:table_name>/<str:record_id>/', views.edit_record, name='edit_record'),
    #path('delete/<str:table_name>/<str:record_id>/', views.delete_record, name='delete_record'),

]