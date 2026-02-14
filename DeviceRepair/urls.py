from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('', include('registration.urls')),
    path('admin/', admin.site.urls),
    path('homepage/', include('homepage.urls')),
    path('manager/', include('manager.urls')),
    path('director/', include('director.urls')),
    path('customer/', include('customer.urls')),
    path('accountant/', include('accountant.urls')),
    path('technician/', include('technician.urls'))
]