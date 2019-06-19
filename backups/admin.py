from django.contrib import admin
from .models import HostType, DataSourceType, Host, DataSource, DataStorage, Task, Log
from crontab import CronTab

# # Register your models here.
# admin.site.register(HostType)
# admin.site.register(DataSourceType)
# admin.site.register(DataStorage)
# admin.site.register(Task)
# admin.site.register(Log)
# admin.site.register(Host)
# admin.site.register(DataSource)

cron_user = "denise"
script_path = "/home/denise/python/django/backups/scripts"
python_path = "/home/denise/.virtualenvs/django_env/bin/python3"


class HostTypeAdmin(admin.ModelAdmin):
    list_display = [field.name for field in HostType._meta.fields]


class DataSourceTypeAdmin(admin.ModelAdmin):
    list_display = [field.name for field in DataSourceType._meta.fields]


class DataStorageAdmin(admin.ModelAdmin):
    list_display = [field.name for field in DataStorage._meta.fields]


class LogAdmin(admin.ModelAdmin):
    list_display = [field.name for field in Log._meta.fields]


class HostAdmin(admin.ModelAdmin):
    list_display = [field.name for field in Host._meta.fields]


class DataSourceAdmin(admin.ModelAdmin):
    list_display = [field.name for field in DataSource._meta.fields]


class TaskAdmin(admin.ModelAdmin):
    # list_display = ('nombre', 'max_quantity', 'data_source', 'data_storage', 'minuto', 'hora', 'dia_mes', 'mes', 'dia_semana')
    list_display = [field.name for field in Task._meta.fields]
    list_filter = ['nombre', 'data_source', 'data_storage']
    search_fields = ['nombre']

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        cron = CronTab(user=cron_user)
        commando = "(cd " + script_path + "; " + python_path + " do_backup.py -taskID " + str(obj.pk) + ")"

        if (change):
            jobs = cron.find_comment(str(obj.pk))

            for job in jobs:
                cron.remove(job)
                cron.write()

        job = cron.new(command=commando, comment=str(obj.pk))
        job.setall(obj.minuto, obj.hora, obj.dia_mes, obj.mes, obj.dia_semana)
        cron.write()

    def delete_model(self, request, obj):
        cron = CronTab(user=cron_user)
        jobs = cron.find_comment(str(obj.pk))

        for job in jobs:
            cron.remove(job)
            cron.write()

        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        cron = CronTab(user=cron_user)

        for obj in queryset:
            jobs = cron.find_comment(str(obj.pk))

            for job in jobs:
                cron.remove(job)
                cron.write()

        super().delete_queryset(request, queryset)

admin.site.register(HostType, HostTypeAdmin)
admin.site.register(DataSourceType, DataSourceTypeAdmin)
admin.site.register(DataSource, DataSourceAdmin)
admin.site.register(DataStorage, DataStorageAdmin)
admin.site.register(Log, LogAdmin)
admin.site.register(Host, HostAdmin)
admin.site.register(Task, TaskAdmin)
