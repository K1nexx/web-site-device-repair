from django.urls import path
from . import views

urlpatterns = [

    path('', views.director_dashboard, name='director_dashboard'),
    path('action/', views.director_action, name='director_action'),
    path('columns/', views.get_table_columns, name='get_table_columns'),
]