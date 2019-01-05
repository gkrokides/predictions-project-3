from django.core.management.base import BaseCommand, CommandError
from predictions.models import CountrySM
from SMcalls import SMcall_CountryById


class Command(BaseCommand):
    help = 'Given a country ID from the sportmonks API,' \
    'it checks if it is already included in the CountrySM table.' \
    'If it is not, it creates it, otherwise it skips it.'

    def add_arguments(self, parser):
        parser.add_argument('smCountryId', type=int)

    def handle(self, *args, **options):
        smCountryId = options['smCountryId']
        d = SMcall_CountryById(smCountryId)

        if CountrySM.objects.filter(country_id=smCountryId).exists():
            self.stdout.write('"%s" already exists in the database' % d['name'])
        else:
            CountrySM.objects.create(**d)
            self.stdout.write('Successfully created "%s"' % d['name'])     
