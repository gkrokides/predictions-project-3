from django import template

register = template.Library()


@register.filter(name='apply_color_if_all')
def apply_color_if_all(value):
    if value != 'All':
        return 'dash-filter'
