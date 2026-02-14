from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from .forms import LoginForm, PREDEFINED_USERS


def loginform(request):
    """Страница входа"""
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user_fio = form.cleaned_data['user_fio']
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            
            # Проверяем credentials в предустановленных пользователях
            if username in PREDEFINED_USERS and PREDEFINED_USERS[username]['password'] == password:
                # Сохраняем в сессии
                request.session['user'] = {
                    "user_fio" : user_fio,
                    'username': username,
                    'email': PREDEFINED_USERS[username]['email'],
                    'password': PREDEFINED_USERS[username]['password'],
                    'role': PREDEFINED_USERS[username]['role']
                }
                if username == "director":
                    return redirect('director_dashboard')
                elif username == "manager":
                    return redirect('manager')
                elif username == "technician":
                    return redirect('technician')
                elif username == "accountant":
                    return redirect('accountant')
                else:
                    return redirect('customer') 
            else:
                messages.error(request, 'Неверный логин или пароль')
    
    else:
        form = LoginForm()
    return render(request, 'registration/LogInForm.html', {'form': form})

def logout(request):
    """Выход из системы"""
    if 'user' in request.session:
        # Очищаем все данные сессии
        request.session.flush()
    
    messages.success(request, 'Вы успешно вышли из системы')
    
    # Перенаправляем на страницу логина
    return redirect('login')
