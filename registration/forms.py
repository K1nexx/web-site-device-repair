from django import forms

class LoginForm(forms.Form):
    user_fio = forms.CharField(
        label='ФИО Пользователя',
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите ваше ФИО'
        })
    )
    username = forms.CharField(
        label='Логин',
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите ваш логин'
        })
    )
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите ваш пароль'
        })
    )

PREDEFINED_USERS = {
    'director': {
        'password': 'director123',
        'email': 'director@company.com',
        'role': 'director'
    },
    'manager': {
        'password': 'manager123', 
        'email': 'manager@company.com',
        'role': 'manager'
    },
    'technician': {
        'password': 'technician123',
        'email': 'tech@company.com', 
        'role': 'technician'
    },
    'accountant': {
        'password': 'accountant123',
        'email': 'accountant@company.com',
        'role': 'accountant'
    },
    'customer': {
        'password': 'customer123',
        'email': 'customer@company.com',
        'role': 'customer'
    }
}