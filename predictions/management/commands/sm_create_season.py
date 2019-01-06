from django.core.management.base import BaseCommand, CommandError
from predictions.models import SeasonSM
from SMcalls import SMcall_SeasonById


class Command(BaseCommand):
    help = 'Given a season ID from the sportmonks API,' \
    'it checks if it is already included in the SeasonSM table.' \
    'If it is not, it creates it, otherwise it skips it.'

    def add_arguments(self, parser):
        parser.add_argument('smSeasonId', type=int)

    def handle(self, *args, **options):
        smSeasonId = options['smSeasonId']
        d = SMcall_SeasonById(smSeasonId)

        if SeasonSM.objects.filter(pk=smSeasonId).exists():
            self.stdout.write('"%i" already exists in the database' % d['season_id'])
        else:
            SeasonSM.objects.create(**d)
            self.stdout.write('Successfully created "%i"' % d['season_id'])     
