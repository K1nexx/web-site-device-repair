import psycopg
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse

def get_connection(user_data):
    """Создание подключения к PostgreSQL 17"""
    try:
        conn = psycopg.connect(
            dbname="rz_gse_a7",
            user=str(user_data['username']),
            password =str(user_data['password']),
            host="localhost",
            port="5433", 
        )
        return conn
    except Exception as e:
        print(f"Ошибка подключения: {e}")
        return None

def index(request):
    if 'user' not in request.session:
        messages.warning(request, 'Для доступа необходимо войти в систему')
        return redirect('login')
    user_data = request.session['user']
    """Главная страница"""
    conn = get_connection(user_data)
    if not conn:
        return HttpResponse("Ошибка подключения к базе данных")
    return render(request, 'homepage/index.html')