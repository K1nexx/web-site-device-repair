from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import get_connection
from datetime import datetime
from django.contrib import messages

def customer(request):
    """Дашборд клиента"""
    user_data = request.session.get('user')
    if not user_data or user_data['role'] != 'customer':
        return redirect('login')
    
    conn = get_connection(user_data)
    if not conn:
        return render(request, 'homepage/access_denied.html', {
            'user': user_data,
            'error_message': 'Не удалось подключиться к базе данных'
        })
    
    try:
        with conn:
            with conn.cursor() as cur:
                # 1. Получаем все заказы клиента
                cur.execute("""
                    SELECT * FROM get_client_orders(%s);
                """, [user_data.get('user_fio')])
                
                orders = cur.fetchall()
                order_columns = [desc.name for desc in cur.description]
                
                # 2. Получаем информацию о клиенте
                cur.execute("""
                    SELECT * FROM get_client_info(%s);
                """, [user_data.get('user_fio')])
                
                customer_info = cur.fetchone()
                
                context = {
                    'user': user_data,
                    'orders': orders,
                    'order_columns': order_columns,
                    'customer_info': {
                        'fio': customer_info[0] if customer_info else 'Не известно',
                        'phone': customer_info[1] if customer_info else 'Не известно',
                        'email': customer_info[2] if customer_info else 'Не известно',
                    } if customer_info else None,
                }
                
                return render(request, 'customer/customer.html', context)
                
    except Exception as e:
        return render(request, 'customer/customer.html', {
            'user': user_data,
            'orders': [],
            'order_columns': [],
            'stats': {'total': 0, 'completed': 0, 'active': 0, 'total_spent': 0},
            'customer_info': None,
        })
    finally:
        if conn:
            conn.close()

def update(request):
    """Страница создания нового заказа"""
    user_data = request.session['user']
    if not user_data:
        return redirect('login')
    
    conn = get_connection(user_data)
    if not conn:
        return render(request, 'homepage/access_denied.html', {
            'user': user_data,
            'error_message': 'Не удалось подключиться к базе данных'
        })
    
    if request.method == 'POST':
        # Обработка формы создания заказа
        try:
            with conn:
                with conn.cursor() as cur:
                    # Получаем данные из формы
                    client_phone = request.POST.get('client_phone', '').strip()
                    client_email = request.POST.get('client_email', '').strip()
                    
                    # Валидация
                    if not client_phone or not client_email:
                        messages.error(request, 'Заполните обязательные поля')
                        return redirect('update_customer_info')
                    
                    # 1. Проверяем/создаем клиента
                    cur.execute("""
                    SELECT * FROM get_client_info(%s);
                    """, [user_data.get('user_fio')])
                    existing_client = cur.fetchone()
                    
                    if not existing_client:
                        cur.execute("""
                            INSERT INTO Clients (Client_FIO, Client_Telefon, Client_Email)
                            VALUES (%s, %s, %s)
                        """, [user_data["user_fio"], client_phone, client_email])
                        messages.info(request, 'Создан новый клиент')
                    else:
                        cur.execute("""
                            UPDATE Clients 
                            SET Client_Telefon = %s, Client_Email = %s
                            WHERE Client_FIO = %s
                        """, [client_phone, client_email, user_data["user_fio"]])
                        messages.info(request, 'Данные клиента обновлены')                    
        except Exception as e:
            messages.error(request, f'Ошибка создания заказа: {e}')
            return redirect('update_customer_info')
        finally:
            conn.close()
    
    # GET запрос - показываем форму
    return render(request, 'customer/update.html')
