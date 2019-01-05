from django.core.management.base import BaseCommand, CommandError
from predictions.models import CountrySM
from SMcalls import SMcall_allCountries


class Command(BaseCommand):
    help = 'Gets all the countries from the sportmonks API,' \
    ' it checks one by one. The countries that are already in the db'\
    ' are skipped. The ones that are not in the CountrySM table' \
    ' are created.'

    def handle(self, *args, **options):
        d = SMcall_allCountries()
        cnt = 0
        dlen = len(d)
        for x in d:
            if CountrySM.objects.filter(country_id=x['country_id']).exists():
                self.stdout.write('"%s" already exists in the database' % x['name'])
                cnt += 1
            else:
                 CountrySM.objects.create(**x)
                 # self.stdout.write('Successfully created "%s" in the database' % x['name'])
        self.stdout.write('already in the database "%i". Created "%i"' % (cnt, dlen-cnt))
