from django.core.management.base import BaseCommand, CommandError
from predictions.models import Game


class Command(BaseCommand):
    help = 'Applies ELO settings to all games above the date threshold'

    def add_arguments(self, parser):
        parser.add_argument('seasonid', type=int)
        parser.add_argument('gameweek', type=int)

    def handle(self, *args, **options):
        seasonid = options['seasonid']
        gw = options['gameweek']
        # find the earliest date of the gameweek to set as threshold
        date_threshold = Game.objects.filter(season=seasonid, gameweek=gw).order_by('date')[0].date
        all_games = Game.objects.filter(season=seasonid, date__gte=date_threshold).order_by('date')
        for game in all_games:
            game.flag = 'No flag'
            game.save()
            # self.stdout.write(self.style.SUCCESS('Successfully saved game "%s"' % game.id))
            self.stdout.write('Successfully saved game on gameweek "%s"' % game.gameweek)
