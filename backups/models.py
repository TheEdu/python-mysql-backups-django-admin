from django.db import models


class HostType(models.Model):
    codigo = models.CharField(max_length=200)
    descripcion = models.CharField(max_length=200)

    def __str__(self):
        return self.codigo + " - " + self.descripcion


class DataSourceType(models.Model):
    codigo = models.CharField(max_length=200)
    descripcion = models.CharField(max_length=200)

    def __str__(self):
        return self.codigo + " - " + self.descripcion


class Host(models.Model):
    nombre = models.CharField(max_length=200)
    descripcion = models.CharField(max_length=200)
    ip = models.CharField(max_length=200)
    user = models.CharField(max_length=200)
    password = models.CharField(max_length=200)
    ssh_port = models.IntegerField(default=22)

    host_type = models.ForeignKey(HostType, on_delete=models.CASCADE)

    def __str__(self):
        return self.nombre


class DataSource(models.Model):
    nombre = models.CharField(max_length=200)
    user = models.CharField(max_length=200)
    password = models.CharField(max_length=200)
    identificador_origen = models.CharField(max_length=200)
    port = models.IntegerField(default=3306)

    data_source_type = models.ForeignKey(DataSourceType, on_delete=models.CASCADE)
    host = models.ForeignKey(Host, on_delete=models.CASCADE)

    def __str__(self):
        return self.nombre


class DataStorage(models.Model):
    nombre = models.CharField(max_length=200)
    boveda_path = models.CharField(max_length=200)
    user = models.CharField(max_length=200, blank=True)
    password = models.CharField(max_length=200, blank=True)

    host = models.ForeignKey(Host, on_delete=models.CASCADE)

    def __str__(self):
        return self.nombre


class Task(models.Model):
    nombre = models.CharField(max_length=200, unique=True)
    minuto = models.CharField(max_length=5, default='*')
    hora = models.CharField(max_length=5, default='*')
    dia_mes = models.CharField(max_length=5, default='*')
    mes = models.CharField(max_length=5, default='*')
    dia_semana = models.CharField(max_length=5, default='*')
    max_quantity = models.IntegerField(default=5)
    max_retry = models.IntegerField(default=5)

    data_source = models.ForeignKey(DataSource, on_delete=models.CASCADE)
    data_storage = models.ForeignKey(DataStorage, on_delete=models.CASCADE)

    def __str__(self):
        return self.nombre


class Log(models.Model):
    exit_code = models.IntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)
    backup_name = models.CharField(max_length=200)
    description = models.CharField(max_length=200)

    task = models.ForeignKey(Task, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.exit_code)
