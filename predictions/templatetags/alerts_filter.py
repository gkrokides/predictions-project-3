from django import template
from predictions.models import Game
from datetime import datetime, timedelta

register = template.Library()


@register.filter(name='alerts_tag')
def apply_color_if_all(value):
    if value != 'all_alerts':
        today = datetime.today()
        threshold = datetime.now() + timedelta(days=7)
        finished_games_without_score = Game.objects.filter(date__lt=today, homegoals__isnull=True).count()
        games_to_refresh_formulas = Game.objects.filter(flag='Refresh').count()
        upcoming_pst_games = Game.objects \
            .filter(date__gte=today, date__lte=threshold, game_status='PST') \
            .exclude(homegoals__gte=0) \
            .count()
        total_alerts = finished_games_without_score + games_to_refresh_formulas + upcoming_pst_games
        return total_alerts
    else:
        return 0
