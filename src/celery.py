import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.settings')

app = Celery(
    'src',
    broker='redis://localhost:6379/0',     
    backend='redis://localhost:6379/0'    
)

app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'update-charging-stations-monthly': {
        'task': '.apps.host.tasks.update_charging_stations',
        'schedule': crontab(day_of_month=1, hour=3, minute=0), 
    },
}
