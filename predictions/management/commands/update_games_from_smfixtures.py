from django.core.management.base import BaseCommand, CommandError
from predictions.models import FixtureSM, Game, Team, Season
from django.db.models import Q


class Command(BaseCommand):
    help = 'Updates the Games table using the FixtureSM table.' \
        ' it checks one by one. The fixtures that are already in the Games table'\
        ' are updated. The ones that are not, are created.' \


    def add_arguments(self, parser):
        parser.add_argument('smSeasonId', type=int)
        parser.add_argument('startDate', type=str)
        parser.add_argument('endDate', type=str)

    def handle(self, *args, **options):
        smSeasonId = options['smSeasonId']
        startDate = options['startDate']
        endDate = options['endDate']
        allFixtures_sm = FixtureSM.objects.filter(Q(season=smSeasonId, match_date__gte=startDate) & Q(season=smSeasonId, match_date__lte=endDate))

        cntUpdated = 0
        cntCreated = 0

        for sm_obj in allFixtures_sm:
            seasonobj = Season.objects.get(season_sm=smSeasonId)
            hm_obj = Team.objects.get(team_sm=sm_obj.hometeam)
            aw_obj = Team.objects.get(team_sm=sm_obj.awayteam)
            if Game.objects.filter(pk=sm_obj.pk).exists():
                current_obj = Game.objects.get(pk=sm_obj.pk)
                current_obj.date = sm_obj.match_date
                current_obj.gameweek = sm_obj.gameweek
                current_obj.homegoals = sm_obj.home_goals
                current_obj.awaygoals = sm_obj.away_goals

                if sm_obj.match_status in {'NS', 'LIVE', 'HT', 'FT', 'PEN_LIVE', 'AET', 'BREAK', 'FT_PEN'}:
                    current_obj.game_status = 'OK'
                elif sm_obj.match_status in {'POSTP', 'INT', 'ABAN', 'SUSP', 'DELAYED', 'TBA', 'AU', 'DELETED'}:
                    current_obj.game_status = 'Postponed'
                else:
                    current_obj.game_status = 'Cancelled'

                if sm_obj.stage == 'Regular Season':
                    current_obj.type = 'RS'
                else:
                    current_obj.type = 'PO'

                current_obj.save()
                cntUpdated += 1
                self.stdout.write(self.style.WARNING('"%s" has been updated' % sm_obj.pk))
            else:
                if sm_obj.match_status in {'NS', 'LIVE', 'HT', 'FT', 'PEN_LIVE', 'AET', 'BREAK', 'FT_PEN'}:
                    mstatus = 'OK'
                elif sm_obj.match_status in {'POSTP', 'INT', 'ABAN', 'SUSP', 'DELAYED', 'TBA', 'AU', 'DELETED'}:
                    mstatus = 'Postponed'
                else:
                    mstatus = 'Cancelled'

                if sm_obj.stage == 'Regular Season':
                    mstage = 'RS'
                else:
                    mstage = 'PO'

                current_obj = Game.objects.create(
                    date=sm_obj.match_date,
                    gameweek=sm_obj.gameweek,
                    fixture_sm=sm_obj,
                    season=seasonobj,
                    hometeam=hm_obj,
                    awayteam=aw_obj,
                    homegoals=sm_obj.home_goals,
                    awaygoals=sm_obj.away_goals,
                    game_status=mstatus,
                    type=mstage,
                    flag='No flag')

                current_obj.save()
                cntCreated += 1
                self.stdout.write(self.style.SUCCESS('"%s" has been created' % sm_obj.pk))

        self.stdout.write('Fixtures created: "%i". Updated: "%i"' % (cntCreated, cntUpdated))
