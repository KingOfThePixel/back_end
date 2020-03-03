from django.contrib import admin
from django.urls import path, include
from django.conf.urls import include
from adv_project import view


urlpatterns = [
    path('', view.home_view, name='home'),
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('api/adv/', include('adventure.urls')),
    
]
