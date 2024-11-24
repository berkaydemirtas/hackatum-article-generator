from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'articlegenerator.settings')

# Create the Celery app
app = Celery('articlegenerator')

# Load task settings from Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks(['article_generator'])


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
