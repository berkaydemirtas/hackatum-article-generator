from django_celery_beat.models import PeriodicTask, IntervalSchedule

# 1. Create an Interval Schedule (e.g., execute every 10 seconds)
schedule, created = IntervalSchedule.objects.get_or_create(
    every=10,
    period=IntervalSchedule.SECONDS,  # Options: SECONDS, MINUTES, HOURS, DAYS, WEEKS
)

# 2. Create the Periodic Task
PeriodicTask.objects.create(
    interval=schedule,               # Set the interval schedule
    name='My Scheduled Task',        # Unique name
    task='article_generator.tasks.sum',  # The task to run
    args='[2, 3]',                   # Arguments to pass to the task
)