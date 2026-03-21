from django import template
from django.utils.safestring import mark_safe
from datetime import datetime, timedelta

register = template.Library()

@register.filter
def date_range(start_date, end_date):
    delta = end_date - start_date
    return [start_date + timedelta(days=i) for i in range(delta.days + 1)]

@register.filter
def split(value, delimiter=','):
    return value.split(delimiter)

@register.filter
def period_name(period):
    period_names = {
        'morning': '上午',
        'noon': '中午',
        'afternoon': '下午',
        'evening': '晚上'
    }
    return period_names.get(period, period)

@register.simple_tag
def get_plan(daily_plans, date, period):
    for plan in daily_plans:
        if plan.date == date and plan.period == period:
            return plan.content
    return ''

@register.filter
def get_plan(period_name, args):
    daily_plans, date = args.split(':')
    for plan in daily_plans:
        if str(plan.date) == date and plan.period == period_name:
            return plan.content
    return ''

@register.filter
def get_summary(summaries, date):
    for summary in summaries:
        if summary.date == date:
            return summary.content
    return ''

@register.filter
def get_weekday_name(day_number):
    weekdays = ['一', '二', '三', '四', '五', '六', '日']
    return weekdays[int(day_number)]

@register.filter
def date_offset(date, offset):
    return date + timedelta(days=int(offset))