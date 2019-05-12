from django.core.management.base import BaseCommand, CommandError
from predictions.models import FixtureSM, SeasonSM, Game, Season, Team
from SMcalls import SMcall_LeagueFixturesByDaterange_paginated
from django.db.models import Q


class Command(BaseCommand):
    help = 'Gets all the fixtures for the selected league, season and daterange from the sportmonks API,' \
        ' it checks one by one. The fixtures that are already in the db'\
        ' are updated. The ones that are not in the FixtureSM table' \
        ' are created. Then it creates or updated the relevant Game table instances' \
        'as per the FixtureSM table'

    def add_arguments(self, parser):
        parser.add_argument('smSeasonId', type=int)
        parser.add_argument('startDate', type=str)
        parser.add_argument('endDate', type=str)

    def handle(self, *args, **options):
        smSeasonId = options['smSeasonId']
        startDate = options['startDate']
        endDate = options['endDate']
        smLeagueId = SeasonSM.objects.get(season_id=smSeasonId).league.league_id
        allFixtures = SMcall_LeagueFixturesByDaterange_paginated(smLeagueId, smSeasonId, startDate, endDate)
        cntUpdated = 0
        cntCreated = 0

        for x in allFixtures:
            if FixtureSM.objects.filter(fixture_id=x['fixture_id']).exists():
                FixtureSM.objects.filter(fixture_id=x['fixture_id']).update(**x)
                # self.stdout.write(self.style.WARNING('"%s" has been updated' % x['fixture_id']))
                self.stdout.write(self.style.SUCCESS('"\r%%%s" updating FixtureSM instances from API ' % (100 * float(cntUpdated) / float(len(allFixtures)))), ending='\r')
                self.stdout.flush()
                cntUpdated += 1
                # current_obj = FixtureSM.objects.get(pk=x['fixture_id'])
                # for i in x:
                #     setattr(current_obj, i, d[i])
                #     current_obj.save()
            else:
                FixtureSM.objects.create(**x)
                cntCreated += 1
                # self.stdout.write(self.style.SUCCESS('"%s" has been created' % x['fixture_id']))
                self.stdout.write(self.style.SUCCESS('"\r%%%s" creating FxitureSM instances from API ' % (100 * float(cntCreated) / float(len(allFixtures)))), ending='\r')
                self.stdout.flush()
        self.stdout.write(self.style.SUCCESS('FixtureSM instances created: "%i". FixtureSM instances Updated: "%i"' % (cntCreated, cntUpdated)))

        # start updaing game instances
        allFixtures_sm = FixtureSM.objects.filter(Q(season=smSeasonId, match_date__gte=startDate) & Q(season=smSeasonId, match_date__lte=endDate)).order_by('match_date')
        gameseason = Season.objects.get(season_sm__season_id=smSeasonId)

        cntUpdated = 0
        cntCreated = 0

        for sm_obj in allFixtures_sm:
            # self.stdout.write(self.style.WARNING('"%s"' % sm_obj.pk))
            seasonobj = Season.objects.get(season_sm=smSeasonId)
            hm_obj = Team.objects.get(team_sm=sm_obj.hometeam)
            aw_obj = Team.objects.get(team_sm=sm_obj.awayteam)
            if Game.objects.filter(pk=sm_obj.pk).exists():
                current_obj = Game.objects.get(pk=sm_obj.pk)
                current_obj.date = sm_obj.match_date

                if sm_obj.match_status in {'FT', 'AET', 'FT_PEN'}:
                    current_obj.homegoals = sm_obj.home_goals
                    current_obj.awaygoals = sm_obj.away_goals
                else:
                    current_obj.homegoals = None
                    current_obj.awaygoals = None

                if sm_obj.match_status in {'NS', 'LIVE', 'HT', 'FT', 'PEN_LIVE', 'AET', 'BREAK', 'FT_PEN'}:
                    current_obj.game_status = 'OK'
                elif sm_obj.match_status in {'POSTP', 'INT', 'ABAN', 'SUSP', 'DELAYED', 'TBA', 'AU', 'DELETED'}:
                    current_obj.game_status = 'PST'
                else:
                    current_obj.game_status = 'CNC'

                if sm_obj.stage == 'Regular Season':
                    current_obj.type = 'RS'
                    current_obj.gameweek = sm_obj.gameweek
                else:
                    current_obj.type = 'PO'
                    lastgw = FixtureSM.objects.filter(season=sm_obj.season).order_by('-gameweek')[0]
                    if sm_obj.game_status == None:
                        current_obj.gameweek = lastgw.gameweek + 1
                    else:
                        current_obj.gameweek = lastgw.gameweek + sm_obj.gameweek

                current_obj.save()
                cntUpdated += 1
                # self.stdout.write(self.style.WARNING('"%s" has been updated' % sm_obj.pk), ending='\r')
                self.stdout.write(self.style.SUCCESS('"\r%%%s" updating Game instances ' % (100 * float(cntUpdated) / float(allFixtures_sm.count()))), ending='\r')
                self.stdout.flush()
            else:
                if sm_obj.match_status in {'NS', 'LIVE', 'HT', 'FT', 'PEN_LIVE', 'AET', 'BREAK', 'FT_PEN'}:
                    mstatus = 'OK'
                elif sm_obj.match_status in {'POSTP', 'INT', 'ABAN', 'SUSP', 'DELAYED', 'TBA', 'AU', 'DELETED'}:
                    mstatus = 'PST'
                else:
                    mstatus = 'CNC'

                if sm_obj.stage == 'Regular Season':
                    mstage = 'RS'
                    gw = sm_obj.gameweek
                else:
                    mstage = 'PO'
                    lastgw = FixtureSM.objects.filter(season=sm_obj.season).order_by('-gameweek')[0]
                    gw = lastgw.gameweek + sm_obj.gameweek

                # Here I'm making sure the score will be entered only for the first games when
                # they are first created
                # If you ever get an error on the below, it's probably bon situations where it's the first season game
                # for one team and not the first for the other. Try and handle that manuylly for now however it's
                # unlikely it will happen
                if (Game.objects.is_first_game(hm_obj, gameseason.id, sm_obj.match_date) == 'Yes' or Game.objects.is_first_game(aw_obj, gameseason.id, sm_obj.match_date) == 'Yes')\
                        and sm_obj.stage == 'Regular Season':
                    hg = sm_obj.home_goals
                    ag = sm_obj.away_goals
                else:
                    hg = None
                    ag = None

                current_obj = Game.objects.create(
                    pk=sm_obj.pk,
                    date=sm_obj.match_date,
                    gameweek=gw,
                    fixture_sm=sm_obj,
                    season=seasonobj,
                    hometeam=hm_obj,
                    awayteam=aw_obj,
                    homegoals=hg,
                    awaygoals=ag,
                    game_status=mstatus,
                    type=mstage,
                    flag='No flag')

                # Above, I'm creating a db record without a score (for games after gmwk 1)
                # as this creates an issue when a team has less than 6 games.
                # So below I'm requesting the same object, adding the score and saving it again.

                recatched = Game.objects.get(pk=sm_obj.pk)
                if sm_obj.match_status in {'FT', 'AET', 'FT_PEN'}:
                    recatched.homegoals = sm_obj.home_goals
                    recatched.awaygoals = sm_obj.away_goals
                else:
                    recatched.homegoals = None
                    recatched.awaygoals = None
                recatched.save()

                # current_obj.save()
                cntCreated += 1
                self.stdout.write(self.style.SUCCESS('"\r%%%s" Creating Game instances ' % (100 * float(cntCreated) / float(allFixtures_sm.count()))), ending='\r')
                self.stdout.flush()

        self.stdout.write(self.style.SUCCESS('Game instances created: "%i". Game instances Updated: "%i"' % (cntCreated, cntUpdated)))
