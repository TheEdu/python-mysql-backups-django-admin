from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from .models import Task


# Create your views here.
def index(request):
    return HttpResponse("Hello, world. You're at the backups index.")


def get_task_command(request, task_id):
    task = get_object_or_404(Task, pk=task_id)

    if (task.data_source.data_source_type.codigo == "mysql"):
        pass
    else:
        pass

    return HttpResponse("Comando")
