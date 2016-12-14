from django.core.management.base import BaseCommand, CommandError
from predictions.models import Game


class Command(BaseCommand):
    help = 'Applies ELO settings to all games in provided season id by saving them one by one'

    def add_arguments(self, parser):
        parser.add_argument('seasonid', type=int)
        parser.add_argument('gameweek', type=int)

    def handle(self, *args, **options):
        seasonid = options['seasonid']
        gw = options['gameweek']
        all_games = Game.objects.filter(season=seasonid, gameweek__gte=gw)
        for game in all_games:
            game.save()
            # self.stdout.write(self.style.SUCCESS('Successfully saved game "%s"' % game.id))
            self.stdout.write('Successfully saved game on gameweek "%s"' % game.gameweek)