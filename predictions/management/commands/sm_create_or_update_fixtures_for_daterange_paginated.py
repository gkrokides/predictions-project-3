from django.core.management.base import BaseCommand, CommandError
from predictions.models import FixtureSM, LeagueSM, SeasonSM, TeamSM
from SMcalls import SMcall_LeagueFixturesByDaterange_paginated


class Command(BaseCommand):
    help = 'Gets all the fixtures for the selected league, season and daterange from the sportmonks API,' \
        ' it checks one by one. The fixtures that are already in the db'\
        ' are updated. The ones that are not in the FixtureSM table' \
        ' are created.'

    def add_arguments(self, parser):
        parser.add_argument('smLeagueId', type=int)
        parser.add_argument('smSeasonId', type=int)
        parser.add_argument('startDate', type=str)
        parser.add_argument('endDate', type=str)

    def handle(self, *args, **options):
        smLeagueId = options['smLeagueId']
        smSeasonId = options['smSeasonId']
        startDate = options['startDate']
        endDate = options['endDate']
        allFixtures = SMcall_LeagueFixturesByDaterange_paginated(smLeagueId, smSeasonId, startDate, endDate)

        cntUpdated = 0
        cntCreated = 0

        for x in allFixtures:
            if FixtureSM.objects.filter(fixture_id=x['fixture_id']).exists():
                FixtureSM.objects.filter(fixture_id=x['fixture_id']).update(**x)
                self.stdout.write(self.style.WARNING('"%s" has been updated' % x['fixture_id']))
                cntUpdated += 1
                # current_obj = FixtureSM.objects.get(pk=x['fixture_id'])
                # for i in x:
                #     setattr(current_obj, i, d[i])
                #     current_obj.save()
            else:
                FixtureSM.objects.create(**x)
                cntCreated += 1
                self.stdout.write(self.style.SUCCESS('"%s" has been created' % x['fixture_id']))

        self.stdout.write('Fixtures created: "%i". Updated: "%i"' % (cntCreated, cntUpdated))
