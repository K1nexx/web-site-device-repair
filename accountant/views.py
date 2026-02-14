from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
import psycopg
from .models import get_connection

def accountant(request):
    """Главный дашборд бухгалтера"""
    user_data = user_data = request.session.get('user')
    if 'user' not in request.session or user_data.get('role') != 'accountant':
        messages.warning(request, 'Для доступа необходимо войти в систему')
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
                
                # 1. Статистика по работникам
                cur.execute("""
                    SELECT COUNT(*) FROM Workers;
                """)
                workers_count = cur.fetchone()
                
                # 2. Недавние заказы ожидающие оплаты
                cur.execute("""
                    SELECT 
                        o.Order_date,
                        o.Order_Price,
                        d.Detail_Price,
                        w.One_work_price,
                        w.Worker_FIO,
                        o.Order_Price - w.One_work_price - d.Detail_Price,
                        o.Order_Status
                    FROM Orders o
                    LEFT JOIN Workers w ON o.Worker_FIO = w.Worker_FIO
                    LEFT JOIN Device d ON o.Detail_id = d.Device_Detail        
                    ORDER BY o.Order_date DESC
                """)
                orders = cur.fetchall()
                
                context = {
                    'user': user_data,
                    'orders': orders,
                    'workers_count': workers_count[0]
                }
                
                return render(request, 'accountant/accountant.html', context)
                
    except Exception as e:
        messages.error(request, f'Ошибка загрузки данных: {e}')
        return render(request, 'accountant/accountant.html', {
            'user': user_data,
            'orders': [],
            'workers_count': 0
        })
    finally:
        conn.close()

def accountant_orders(request):
    """Управление заказами и изменение статуса оплаты"""
    if 'user' not in request.session:
        messages.warning(request, 'Для доступа необходимо войти в систему')
        return redirect('login')
    
    user_data = request.session['user']
    
    # Обработка изменения статуса
    if request.method == 'POST' and 'change_status' in request.POST:
        conn = get_connection(user_data)
        if not conn:
            messages.error(request, 'Не удалось подключиться к базе данных')
            return redirect('accountant_orders')
        
        try:
            client_fio = request.POST.get('client_fio', '')
            detail_id = request.POST.get('detail_id', '')
            order_date = request.POST.get('order_date', '')
            new_status = request.POST.get('new_status', '')
            
            with conn:
                with conn.cursor() as cur:
                    # Проверяем существование заказа
                    cur.execute("""
                        SELECT Order_Status FROM Orders 
                        WHERE Client_FIO = %s AND Detail_ID = %s AND Order_date = %s
                    """, [client_fio, detail_id, order_date])
                    
                    if not cur.fetchone():
                        messages.error(request, 'Заказ не найден')
                        return redirect('accountant_orders')
                    
                    # Обновляем статус
                    cur.execute("""
                        UPDATE Orders 
                        SET Order_Status = %s 
                        WHERE Client_FIO = %s AND Detail_ID = %s AND Order_date = %s
                    """, [new_status, client_fio, detail_id, order_date])                  
                    messages.success(request, f'Статус заказа успешно изменен на "{new_status}"')
                    
        except Exception as e:
            messages.error(request, f'Ошибка изменения статуса: {e}')
        finally:
            conn.close()
        
        return redirect('accountant_orders')
    
    # Получаем параметры фильтрации
    status_filter = request.GET.get('status', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    conn = get_connection(user_data)
    if not conn:
        return render(request, 'homepage/access_denied.html', {
            'user': user_data,
            'error_message': 'Не удалось подключиться к базе данных'
        })
    return render(request, 'accountant/accountant_orders.html')

def manage_salaries(request):
    """Управление зарплатами сотрудников"""
    if 'user' not in request.session:
        messages.warning(request, 'Для доступа необходимо войти в систему')
        return redirect('login')
    
    user_data = request.session['user']
    
    # Обработка изменения зарплаты
    if request.method == 'POST' and 'update_salary' in request.POST:
        conn = get_connection(user_data)
        if not conn:
            messages.error(request, 'Не удалось подключиться к базе данных')
            return redirect('manage_salaries')
        
        try:
            worker_fio = request.POST.get('worker_fio', '').strip()
            new_salary = request.POST.get('new_salary', '').strip()
            
            if not worker_fio or not new_salary:
                messages.error(request, 'Заполните все поля')
                return redirect('manage_salaries')
            
            with conn:
                with conn.cursor() as cur:
                    # Получаем текущую зарплату
                    cur.execute("SELECT One_Work_Price FROM Workers WHERE Worker_FIO = %s", [worker_fio])
                    old_salary_result = cur.fetchone()
                    
                    if not old_salary_result:
                        messages.error(request, 'Сотрудник не найден')
                        return redirect('manage_salaries')
                                                         
                    # Обновляем зарплату
                    cur.execute("""
                        UPDATE Workers 
                        SET One_Work_Price = %s 
                        WHERE Worker_FIO = %s
                    """, [new_salary, worker_fio])
                    
                    
        except Exception as e:
            messages.error(request, f'Ошибка обновления зарплаты: {e}')
        finally:
            conn.close()
        
        return redirect('manage_salaries')
    
    # GET запрос - показываем список сотрудников
    conn = get_connection(user_data)
    if not conn:
        return render(request, 'accountant/access_denied.html', {
            'user': user_data,
            'error_message': 'Не удалось подключиться к базе данных'
        })
    
    try:
        with conn:
            with conn.cursor() as cur:
                # Получаем список сотрудников
                cur.execute("""
                    SELECT 
                        Worker_FIO,
                        Worker_Position,
                        One_Work_Price,
                        Worker_Telefon
                    FROM Workers 
                    ORDER BY Worker_FIO
                """)
                workers = cur.fetchall()
                
                context = {
                    'user': user_data,
                    'workers': workers,
                }
                
                return render(request, 'accountant/manage_salaries.html', context)
                
    except Exception as e:
        messages.error(request, f'Ошибка загрузки данных: {e}')
        return render(request, 'accountant/manage_salaries.html', {
            'user': user_data,
            'workers': []
        })
    finally:
        conn.close()