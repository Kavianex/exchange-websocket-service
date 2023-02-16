from __future__ import absolute_import
from celery_config import celery_app
import app.tasks as tasks
__all__ = ('celery_app', 'tasks')
