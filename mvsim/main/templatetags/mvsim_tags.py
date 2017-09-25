from django import template
from django.utils.safestring import mark_safe
import locale
import math
from engine.simple_controller import money_report as _money_report

register = template.Library()


def money_report(num):
    num = _money_report(num)
    return mark_safe(num)  # nosec


def format_float(number, decimals=1):
    return locale.format('%.' + str(decimals) + 'f', number, True)


def format_int(number):
    return locale.format('%i', round(number), True)


def div(a, b):
    return float(a) / float(b)


def times(a, b):
    return float(a) * float(b)


def minus(a, b):
    return float(a) - float(b)


def _sum(a):
    return sum(a)


def gt(a, b):
    a = a or 0
    return float(a) > float(b)


def gte(a, b):
    return float(a) >= float(b)


def lt(a, b):
    return float(a) < float(b)


def startswith(a, b):
    return a.startswith(b)


def plus(a, b):
    return float(a) + float(b)


def neq(a, b):
    return a != b


def _or(a, b):
    return a or b


def get_attr(a, b):
    return getattr(a, b)


def get_item(a, b):
    try:
        return a[b]
    except (IndexError, KeyError):
        return ''


def get_item_or_0(a, b,):
    try:
        return a[b]
    except (IndexError, KeyError):
        return 0

# reverse engineering the year and season this way is ugly, but saves us
# from having to instantiate the state and variable objects for every turn
# of the game


def reverse_engineer_year(turn_number):
    return int(math.ceil(turn_number / 2.0))


def reverse_engineer_season(turn_number):
    return "%s / 2" % str(((turn_number - 1) % 2) + 1)


register.filter("neq", neq)
register.filter("format_float", format_float)
register.filter("money_report", money_report)
register.filter("format_int", format_int)
register.filter("div", div)
register.filter("plus", plus)
register.filter("times", times)
register.filter("minus", minus)
register.filter("sum", _sum)
register.filter("gt", gt)
register.filter("gte", gte)
register.filter("lt", lt)
register.filter("startswith", startswith)
register.filter("or", _or)
register.filter("get_attr", get_attr)
register.filter("get_item", get_item)
register.filter("get_item_or_0", get_item_or_0)
register.filter("reverse_engineer_year", reverse_engineer_year)
register.filter("reverse_engineer_season", reverse_engineer_season)
