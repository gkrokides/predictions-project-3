from django.core.management.base import BaseCommand, CommandError
from predictions.models import TeamSM
from SMcalls import SMcall_teamsBySeason


class Command(BaseCommand):
    help = 'Gets all the teams for the selected season from the sportmonks API,' \
    ' it checks one by one. The teams that are already in the db'\
    ' are skipped. The ones that are not in the TeamSM table' \
    ' are created.'

    def add_arguments(self, parser):
        parser.add_argument('smSeasonId', type=int)

    def handle(self, *args, **options):
        smSeasonId = options['smSeasonId']
        d = SMcall_teamsBySeason(smSeasonId)
        cnt = 0
        dlen = len(d)
        for x in d:
            if TeamSM.objects.filter(team_id=x['team_id']).exists():
                self.stdout.write('"%s" already exists in the database' % x['name'])
                cnt += 1
            else:
                 TeamSM.objects.create(**x)
                 # self.stdout.write('Successfully created "%s" in the database' % x['name'])
        self.stdout.write('No. of teams already in the database "%i". Created "%i"' % (cnt, dlen-cnt))
