from django.urls import path
from . import views

app_name = 'backups'

urlpatterns = [
    path('', views.index, name='index'),
    path('task/<int:task_id>/command', views.get_task_command, name='command'),
]
