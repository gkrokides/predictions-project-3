from django import template

register = template.Library()


@register.filter(name='strike_rate_colors')
def strike_rate_colors(value):
    if value >= 0.79:
        return 'srslot1'
    elif 0.59 <= value < 0.79:
        return 'srslot2'
    elif 0.49 <= value < 0.59:
        return 'srslot3'
    elif 0.29 <= value < 0.49:
        return 'srslot4'
    elif 0.09 <= value < 0.29:
        return 'srslot5'
    elif 0.00 <= value < 0.09:
        return 'srslot6'
    else:
        return ''


