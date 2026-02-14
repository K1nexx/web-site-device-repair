from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from .models import get_connection


def manager(request):
    """Дашборд менеджера - главная страница"""
    user_data = request.session['user']
    if not user_data:
        return redirect('login')
    conn = get_connection(user_data)
    
    try:
        with conn:
            with conn.cursor() as cur:
                # 1. Последние 10 заказов
                cur.execute("""
                    SELECT 
                        o.Client_FIO,
                        o.Detail_ID,
                        o.Order_date,
                        o.Order_Status,
                        o.Order_Price,
                        w.Worker_FIO as Master
                    FROM Orders o
                    LEFT JOIN Workers w ON o.Worker_FIO = w.Worker_FIO
                    ORDER BY o.Order_date DESC
                """)
                recent_orders = cur.fetchall()
                recent_columns = [desc.name for desc in cur.description]
                
                # 2. Получаем список мастеров для быстрого доступа
                cur.execute("SELECT Worker_FIO FROM Workers")
                masters = [row[0] for row in cur.fetchall()]
                
                context = {
                    'user': user_data,
                    'recent_orders': recent_orders,
                    'recent_columns': recent_columns,
                    'masters': masters, 
                }
                return render(request, 'manager/MGhomepage.html', context)
                
    except Exception as e:
        messages.error(request, f'Ошибка загрузки данных: {e}')
        return render(request, 'manager/MGhomepage.html', {
            'user': user_data,
            'recent_orders': [],
            'recent_columns': [],
            'masters': [],
        })
    finally:
        conn.close()

def create_order(request):
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
                    client_fio = request.POST.get('client_fio', '').strip()
                    client_phone = request.POST.get('client_phone', '').strip()
                    client_email = request.POST.get('client_email', '').strip()
                    device_detail = request.POST.get('device_detail', '').strip()
                    worker_fio = request.POST.get('worker_fio', '').strip()
                    order_date = request.POST.get('order_date', '')
                    order_text = request.POST.get('order_text', '').strip()
                    order_price = request.POST.get('order_price', '0')
                    warranty_period = request.POST.get('warranty_period', '12')
                    author_phone = request.POST.get('author_phone', '')
                    
                    # Валидация
                    if not client_fio or not device_detail or not worker_fio:
                        messages.error(request, 'Заполните обязательные поля: ФИО клиента, телефон, деталь устройства и выберите мастера')
                        return redirect('create_order')
                    
                    # 1. Проверяем/создаем клиента
                    cur.execute("SELECT Client_FIO FROM Clients WHERE Client_FIO = %s", [client_fio])
                    existing_client = cur.fetchone()
                    
                    if not existing_client:
                        cur.execute("""
                            INSERT INTO Clients (Client_FIO, Client_Telefon, Client_Email)
                            VALUES (%s, %s, %s)
                        """, [client_fio, client_phone, client_email])
                        messages.info(request, 'Создан новый клиент')
                    else:
                        cur.execute("""
                            UPDATE Clients 
                            SET Client_Telefon = %s, Client_Email = %s
                            WHERE Client_FIO = %s
                        """, [client_phone, client_email, client_fio])
                        messages.info(request, 'Данные клиента обновлены')
                    
                    # 2. Создаем заказ
                    cur.execute("""
                        INSERT INTO Orders (
                            Client_FIO, Detail_ID, Worker_FIO, Order_date, 
                            Order_text, Order_Price, Order_Status, Warranty_Period,
                            Author_FIO, Author_Position, Author_Phone
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, [
                        client_fio,
                        device_detail,
                        worker_fio,
                        order_date,
                        order_text,
                        order_price,
                        'new',
                        warranty_period,
                        user_data['user_fio'],
                        'Менеджер',
                        author_phone,
                    ])
                    
                    messages.success(request, f'Заказ успешно создан!')
                    return redirect('create_order')
                    
        except Exception as e:
            messages.error(request, f'Ошибка создания заказа: {e}')
            return redirect('create_order')
        finally:
            conn.close()
    
    # GET запрос - показываем форму
    try:
        with conn:
            with conn.cursor() as cur:
                # Получаем список устройств
                cur.execute("SELECT Device_Detail, Device_Model FROM Device ORDER BY Device_Model")
                devices = cur.fetchall()
                
                # Получаем список мастеров
                cur.execute("SELECT Worker_FIO, Worker_Position FROM Workers")
                workers = cur.fetchall()
                
                # Получаем список клиентов для автодополнения
                cur.execute("SELECT Client_FIO, Client_Telefon FROM Clients ORDER BY Client_FIO")
                clients = cur.fetchall()
                
                context = {
                    'user': user_data,
                    'devices': devices,
                    'workers': workers,
                    'clients': clients,
                    'today': '2024-01-15',  # Можно заменить на timezone.now().date()
                }
                
                return render(request, 'manager/create_order.html', context)
                
    except Exception as e:
        messages.error(request, f'Ошибка загрузки данных: {e}')
        return render(request, 'manager/create_order.html', {
            'user': user_data,
            'devices': [],
            'workers': [],
            'clients': [],
            'today': '2024-01-15',
        })
    finally:
        conn.close()

def order_history(request):
    """История заказов с фильтрами"""
    user_data = request.session['user']
    if not user_data:
        return redirect('login')
    
    conn = get_connection(user_data)
    if not conn:
        return render(request, 'homepage/access_denied.html', {
            'user': user_data,
            'error_message': 'Не удалось подключиться к базе данных'
        })
    
    # Получаем параметры фильтрации
    client_filter = request.GET.get('client', '')
    status_filter = request.GET.get('status', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    try:
        with conn:
            with conn.cursor() as cur:
                # Формируем запрос с фильтрами
                query = """
                    SELECT 
                        o.Client_FIO,
                        c.Client_Telefon,
                        o.Detail_ID,
                        d.Device_Model,
                        o.Order_date,
                        o.Order_Status,
                        o.Order_Price,
                        o.Warranty_Period,
                        w.Worker_FIO as Master,
                        o.Author_FIO as Manager
                    FROM Orders o
                    LEFT JOIN Clients c ON o.Client_FIO = c.Client_FIO
                    LEFT JOIN Device d ON o.Detail_ID = d.Device_Detail
                    LEFT JOIN Workers w ON o.Worker_FIO = w.Worker_FIO
                """
                cur.execute(query)
                orders = cur.fetchall()
                columns = [desc.name for desc in cur.description]
                context = {
                    'user': user_data,
                    'orders': orders,
                    'columns': columns,
                }
                return render(request, 'manager/order_history.html', context)
                
    except Exception as e:
        messages.error(request, f'Ошибка загрузки истории заказов: {e}')
        return render(request, 'manager/order_history.html', {
            'user': user_data,
            'orders': [],
            'columns': [],
            'statuses': [],
            'clients': [],
        })
    finally:
        conn.close()