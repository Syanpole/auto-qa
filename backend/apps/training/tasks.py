from celery import shared_task


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def run_training_job(self, training_job_id: str):
    # Placeholder for pipeline orchestration against Ultralytics/RT-DETR training scripts.
    return {"training_job_id": training_job_id, "status": "queued"}
