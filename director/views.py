from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from .models import get_connection
import json

def director_dashboard(request):
    """Дашборд директора с управлением всеми таблицами"""
    user_data = request.session.get('user')
    if not user_data or user_data.get('role') != 'director':
        messages.error(request, 'Доступ только для директора')
        return redirect('login')
    
    # Получаем выбранную таблицу из GET параметра или по умолчанию
    table_name = request.GET.get('table', 'Orders')
    
    # Список доступных таблиц
    tables = ['Orders', 'Clients', 'Workers', 'Device', 'Providers']
    
    conn = get_connection(user_data)
    if not conn:
        return render(request, 'homepage/access_denied.html', {
            'user': user_data,
            'error_message': 'Не удалось подключиться к базе данных'
        })
    
    try:
        with conn:
            with conn.cursor() as cur:
                # Получаем данные из выбранной таблицы
                cur.execute(f"SELECT * FROM {table_name} LIMIT 100")
                data = cur.fetchall()
                
                # Получаем названия колонок
                columns = [desc.name for desc in cur.description]
                
                # Получаем первичные ключи таблицы
                cur.execute("""
                    SELECT kcu.column_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu
                    ON tc.constraint_name = kcu.constraint_name
                    WHERE tc.table_name = %s AND tc.constraint_type = 'PRIMARY KEY'
                """, [table_name])
                
                primary_keys = [row[0] for row in cur.fetchall()]
                
                context = {
                    'user': user_data,
                    'table_name': table_name,
                    'tables': tables,
                    'data': data,
                    'columns': columns,
                    'primary_keys': primary_keys,
                    'row_count': len(data),
                }
                
                return render(request, 'director/dashboard.html', context)
                
    except Exception as e:
        messages.error(request, f'Ошибка загрузки данных: {str(e)}')
        return render(request, 'director/dashboard.html', {
            'user': user_data,
            'table_name': table_name,
            'tables': tables,
            'data': [],
            'columns': [],
            'primary_keys': [],
            'row_count': 0,
        })
    finally:
        if conn:
            conn.close()

def director_action(request):
    """Обработка действий CRUD для всех таблиц"""
    user_data = request.session.get('user')
    if not user_data or user_data.get('role') != 'director':
        return JsonResponse({'success': False, 'error': 'Доступ запрещен'})
    
    if request.method == 'POST':
        conn = get_connection(user_data)
        if not conn:
            return JsonResponse({'success': False, 'error': 'Нет подключения к БД'})
        
        try:
            action = request.POST.get('action')
            table_name = request.POST.get('table_name')
            
            with conn:
                with conn.cursor() as cur:
                    if action == 'delete':
                        # Удаление записи
                        primary_key = request.POST.get('primary_key')
                        primary_value = request.POST.get('primary_value')
                        
                        # Проверяем, что это действительно primary key
                        cur.execute("""
                            SELECT kcu.column_name
                            FROM information_schema.table_constraints tc
                            JOIN information_schema.key_column_usage kcu
                            ON tc.constraint_name = kcu.constraint_name
                            WHERE tc.table_name = %s AND tc.constraint_type = 'PRIMARY KEY'
                            AND kcu.column_name = %s
                        """, [table_name, primary_key])
                        
                        if not cur.fetchone():
                            return JsonResponse({'success': False, 'error': 'Неверный первичный ключ'})
                        
                        # Удаляем запись
                        cur.execute(f"DELETE FROM {table_name} WHERE {primary_key} = %s", [primary_value])
                        
                        return JsonResponse({'success': True, 'message': 'Запись удалена'})
                    
                    elif action == 'edit':
                        # Редактирование записи
                        data = json.loads(request.POST.get('data', '{}'))
                        primary_key = request.POST.get('primary_key')
                        primary_value = request.POST.get('primary_value')
                        
                        if not data:
                            return JsonResponse({'success': False, 'error': 'Нет данных для обновления'})
                        
                        # Формируем SQL запрос для UPDATE
                        set_clause = ', '.join([f"{key} = %s" for key in data.keys()])
                        values = list(data.values()) + [primary_value]
                        
                        sql = f"UPDATE {table_name} SET {set_clause} WHERE {primary_key} = %s"
                        cur.execute(sql, values)
                        
                        return JsonResponse({'success': True, 'message': 'Запись обновлена'})
                    
                    elif action == 'add':
                        # Добавление новой записи
                        data = json.loads(request.POST.get('data', '{}'))
                        
                        if not data:
                            return JsonResponse({'success': False, 'error': 'Нет данных для добавления'})
                        
                        # Формируем SQL запрос для INSERT
                        columns = ', '.join(data.keys())
                        placeholders = ', '.join(['%s'] * len(data))
                        values = list(data.values())
                        
                        sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
                        cur.execute(sql, values)
                        
                        return JsonResponse({'success': True, 'message': 'Запись добавлена'})
                    
                    else:
                        return JsonResponse({'success': False, 'error': 'Неизвестное действие'})
                        
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
        finally:
            if conn:
                conn.close()
    
    return JsonResponse({'success': False, 'error': 'Неверный метод запроса'})

def get_table_columns(request):
    """Получение информации о колонках таблицы"""
    user_data = request.session.get('user')
    if not user_data or user_data.get('role') != 'director':
        return JsonResponse({'success': False, 'error': 'Доступ запрещен'})
    
    table_name = request.GET.get('table_name')
    if not table_name:
        return JsonResponse({'success': False, 'error': 'Не указана таблица'})
    
    conn = get_connection(user_data)
    if not conn:
        return JsonResponse({'success': False, 'error': 'Нет подключения к БД'})
    
    try:
        with conn:
            with conn.cursor() as cur:
                # Получаем информацию о колонках
                cur.execute("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_name = %s
                    ORDER BY ordinal_position
                """, [table_name])
                
                columns = []
                for row in cur.fetchall():
                    columns.append({
                        'name': row[0],
                        'type': row[1],
                        'nullable': row[2] == 'YES',
                        'default': row[3]
                    })
                
                return JsonResponse({'success': True, 'columns': columns})
                
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
    finally:
        if conn:
            conn.close()