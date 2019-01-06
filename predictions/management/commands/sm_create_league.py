from django.core.management.base import BaseCommand, CommandError
from predictions.models import LeagueSM
from SMcalls import SMcall_LeagueById


class Command(BaseCommand):
    help = 'Given a league ID from the sportmonks API,' \
    'it checks if it is already included in the LeagueSM table.' \
    'If it is not, it creates it, otherwise it skips it.'

    def add_arguments(self, parser):
        parser.add_argument('smLeagueId', type=int)

    def handle(self, *args, **options):
        smLeagueId = options['smLeagueId']
        d = SMcall_LeagueById(smLeagueId)

        if LeagueSM.objects.filter(pk=smLeagueId).exists():
            self.stdout.write('"%s" already exists in the database' % d['name'])
        else:
            LeagueSM.objects.create(**d)
            self.stdout.write('Successfully created "%s"' % d['name'])     
