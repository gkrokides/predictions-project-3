from django import template

register = template.Library()


@register.filter(name='apply_prediction_colors')
def apply_prediction_colors(value):
    if value == 'HOME':
        return 'home-prediction'
    elif value == 'AWAY':
        return 'away-prediction'
    else:
        return 'draw-prediction'

