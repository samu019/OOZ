from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Establecer la configuración predeterminada del Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tu_proyecto.settings')

app = Celery('tu_proyecto')

# Usar el backend de Django
app.config_from_object('django.conf:settings', namespace='CELERY')

# Cargar tareas de todas las aplicaciones Django registradas
app.autodiscover_tasks()
