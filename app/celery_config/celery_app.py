from celery import Celery
import settings
app = Celery('main',
    broker=f'pyamqp://{settings.RABBITMQ_CRED}@{settings.RABBITMQ_HOST}:5672//',
    include=['tasks'],
)
app.conf.update(
    task_default_queue='PUBLISH',
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_publish_retry=True,
    task_publish_retry_policy={
        'max_retries': 3,
        'interval_start': 0,
        'interval_step': 0.2,
        'interval_max': 0.2,
    },
)
# app.autodiscover_tasks(related_name='')
