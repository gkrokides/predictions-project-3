from django.core.management.base import BaseCommand, CommandError
from predictions.models import Game


class Command(BaseCommand):
    help = 'Applies ELO settings to all games by saving them one by one'

    def handle(self, *args, **options):
        all_games = Game.objects.all().order_by('date')
        for game in all_games:
            game.save()
            # self.stdout.write(self.style.SUCCESS('Successfully saved game "%s"' % game.id))
            self.stdout.write('Successfully saved game "%s"' % game.id)
