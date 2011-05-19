# custom scheduler

import datetime
import logging
from celery.schedules import schedule

class EveryFourDays(schedule):
    """Provide an instance of this class as a task's schedule
    to schedule it every four days."""

    # We do this by scheduling on each day whose proleptic
    # Gregorian ordinal is divisible by 4.  (the proleptic
    # Gregorian ordinal just assigns each day in history a
    # number, and otherwise isn't significant here)

    def __init__(self, hour=12, *args, **kwargs):
        """Specify hour to make task scheduled at that hour of the day
        (default is noon)"""
        super(EveryFourDays,self).__init__(run_every=datetime.timedelta(days=4))
        self.hour = hour

    def remaining_estimate(self, last_run_at):
        """Returns when the periodic task should run next as a timedelta."""
        # last_run_at is a datetime.datetime
        # could have just been set to 'now' when the task was created,
        # so not necessarily at the right hour

        logging.debug("remaining_estimate(last_run_at=%s)" % last_run_at)

        # add four days to last run
        next_run = last_run_at + datetime.timedelta(days=4)
        # then adjust to the right hour
        next_run = next_run.replace(hour=self.hour)
        # how long til then?
        result = next_run - datetime.datetime.now()
        logging.debug("remaing_estimate -> %s" % result)
        return result
