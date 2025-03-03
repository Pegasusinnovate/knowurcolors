from flask import current_app
from .firebase_utils import list_files, delete_file
from datetime import datetime, timedelta

def delete_old_files():
    with current_app.app_context():
        for blob in list_files():
            # Delete files older than 24 hours
            if blob.time_created < datetime.utcnow() - timedelta(hours=24):
                try:
                    delete_file(blob.name)
                except Exception as e:
                    current_app.logger.error(f"Error deleting file {blob.name}: {e}")

def init_scheduler(app):
    from apscheduler.schedulers.background import BackgroundScheduler
    scheduler = BackgroundScheduler()
    # Run deletion job every hour
    scheduler.add_job(func=delete_old_files, trigger="interval", hours=1)
    scheduler.start()
    app.logger.info("Scheduler started for auto deletion of old files.")