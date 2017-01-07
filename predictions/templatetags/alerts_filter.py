from django import template
from predictions.models import Game
from datetime import datetime

register = template.Library()


@register.filter(name='alerts_tag')
def apply_color_if_all(value):
    if value != 'ended_games_without_score':
        today = datetime.today()
        finished_games_without_score = Game.objects.filter(date__lt=today, homegoals__isnull=True).count()
        games_to_refresh_formulas = Game.objects.filter(flag='Refresh').count()
        total_alerts = finished_games_without_score + games_to_refresh_formulas
        return total_alerts
    else:
        return 0
