import datetime
import itertools

from django import template

from alerts.models import Notification
from alerts.utils import get_alert_generators


register = template.Library()


@register.inclusion_tag("dashboard/alerts.html", takes_context=True)
def alerts(context, request, count=None):
    """
    Renders the user's notifications and alerts.

    If count is given, a maximum of count notifications are returned. All
    alerts will always be returned.
    """
    gens = get_alert_generators('alert', request=request, context=context)
    alerts = list(itertools.chain(*(g for g in gens if g is not None)))
    notifs = Notification.objects.filter(is_open=True, visible_to__user=request.user)
    total = len(alerts) + len(notifs)

    if count:
        notifs = notifs[:count]

    return {
        'alerts': alerts,
        'notifs': notifs,
        'total': total,
        'count': count,
        'program': context.get('program', None),
    }


@register.filter
def days(date):
    """Calculates the number of days between today and the given date."""
    now = datetime.datetime.now()
    today = datetime.datetime(now.year, now.month, now.day)
    then = datetime.datetime(date.year, date.month, date.day)
    diff = (today - then).days

    if diff == 0:
        return 'today'
    elif diff < 0:
        diff = abs(diff)
        phrase = 'in {diff} {interval}{plural}'
    else:
        phrase = '{diff} {interval}{plural} ago'

    interval = 'day' if diff < 7 else 'week'
    diff = diff if diff < 7 else (diff / 7)
    plural = 's' if diff > 1 else ''

    return phrase.format(interval=interval, diff=diff, plural=plural)
