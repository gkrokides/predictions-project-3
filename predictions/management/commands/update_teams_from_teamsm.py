from django.core.management.base import BaseCommand, CommandError
from predictions.models import TeamSM, Team
from SMcalls import SMcall_teamsBySeason


class Command(BaseCommand):
    help = 'given the sm season id it gets all the teams for the selected season from the sportmonks API,' \
        ' it checks one by one. The teams that are already in the Team table (not TeamSM)'\
        ' are skipped. The ones that are not in the Team table are created'

    def add_arguments(self, parser):
        parser.add_argument('smSeasonId', type=int)

    def handle(self, *args, **options):
        smSeasonId = options['smSeasonId']
        d = SMcall_teamsBySeason(smSeasonId)
        cnt = 0
        dlen = len(d)
        for x in d:
            current_team_obj = TeamSM.objects.get(team_id=x['team_id'])
            if not Team.objects.filter(team_sm=current_team_obj).exists():
                t = Team.objects.create(name=current_team_obj.name, team_sm=current_team_obj)
                t.save()
                cnt += 1
                self.stdout.write('"%s" has been created in the Team table' % x['name'])
        self.stdout.write('No. of teams already in the Team table: "%i". Created "%i"' % (dlen - cnt, cnt))
