from django.core.management.base import BaseCommand, CommandError
from predictions.models import LeagueSMforLive
from SMcalls import SMcall_allLeagues


class Command(BaseCommand):
    help = 'Gets all the leagues from the sportmonks API,' \
        ' it checks one by one. The leagues that are already in the LeagueSMforLive db table'\
        ' are skipped. The ones that are not, are created.'

    def handle(self, *args, **options):
        d = SMcall_allLeagues()
        cnt = 0
        dlen = len(d)
        for x in d:
            if LeagueSMforLive.objects.filter(league_id=x['league_id']).exists():
                self.stdout.write('"%s" already exists in the database' % x['name'])
                cnt += 1
            else:
                LeagueSMforLive.objects.create(**x)
                # self.stdout.write('Successfully created "%s" in the database' % x['name'])
        self.stdout.write('already in the database "%i". Created "%i"' % (cnt, dlen - cnt))
