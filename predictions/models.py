from __future__ import unicode_literals
from django.db import models
from django.utils import timezone
from django.db.models import Q, Max, Sum, F
# from decimal import Decimal, ROUND_HALF_UP, ROUND_HALF_DOWN
import django_filters
# from django.conf import settings
from datetime import datetime
from predictions_project import elosettings
from operator import itemgetter
from django.utils.text import slugify
import itertools
from django.utils.encoding import python_2_unicode_compatible


class Leagues(models.Model):
    league_sm = models.ForeignKey('LeagueSM', blank=True, null=True)
    country = models.CharField(max_length=200, verbose_name='Country', unique=False, null=False)
    division = models.IntegerField()
    league_name = models.CharField(max_length=200)
    country_code = models.CharField(max_length=20)
    short_name = models.CharField(max_length=50, unique=True)
    # the below fields (teamstotal, gwtotal) are redundant and will not be used in the future as they should have been
    #  included in the
    # season table and not here. I will remove them in the future or transfer them in the season table. They are only
    # used in the save function of this model for now.
    teamstotal = models.IntegerField(default=0, verbose_name='No. of teams')
    gwtotal = models.IntegerField(default=0, verbose_name="No. Gameweeks", editable=False)

    def save(self, *args, **kwargs):
        self.gwtotal = (self.teamstotal - 1) * 2
        super(Leagues, self).save(*args, **kwargs)

    class Meta:
        ordering = ["short_name"]
        verbose_name = "League"
        verbose_name_plural = "Leagues"

    def __str__(self):
        return self.short_name


class SeasonManager(models.Manager):
    # Returns a set of all seasons related to the given country
    def get_seasons(self, cntry):
        sn_lst = []
        # testing line
        # sn_lst.append([str('CYP2 2014/2015'), 4])
        qset = self.filter(league__country=cntry).order_by('-end_date')
        for item in qset:
            sn_lst.append([str(item), item.id])
        return sn_lst

    def get_seasons_full(self, cntry):
        sn_lst = []
        # testing line
        # sn_lst.append([str('CYP2 2014/2015'), 4])
        qset = self.filter(league__country=cntry).order_by('-end_date')
        for item in qset:
            sn_lst.append([str(item), item.id, str(item.league.league_name), str(item.get_start_year()), str(item.get_end_year()), str(item.end_date), str(item.league.short_name), item.league.country_code])
        return sn_lst

    def get_distinct_season_ends(self):
        dlist = []
        qset = self.all().order_by('-end_date')
        for itm in qset:
            dlist.append(str(itm.get_end_year()))
        # converting my list to a set and then back to a list, leave me only with distinct values as sets only allow distinct values
        dlist = list(set(dlist))
        return dlist


class Season(models.Model):
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    season_sm = models.ForeignKey('SeasonSM', blank=True, null=True)
    league = models.ForeignKey('Leagues', to_field='short_name', null=True, related_name='league')
    teamstotal = models.IntegerField(default=0, verbose_name='No. of teams', blank=True, null=True)
    objects = SeasonManager()

    def get_start_year(self):
        return self.start_date.year

    def get_end_year(self):
        return self.end_date.year

    def __str__(self):
        return str(self.league) + " " + str(self.get_start_year()) + "/" + str(self.get_end_year())


class Team(models.Model):
    team_sm = models.ForeignKey('TeamSM', blank=True, null=True)
    name = models.CharField(max_length=250, unique=True, primary_key=True)
    # points = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class GameManager(models.Manager):
    def team_points(self, team):
        xhome = self.filter(hometeam=team, result='HOME').count()
        xaway = self.filter(awayteam=team, result='AWAY').count()
        xdrawhome = self.filter(hometeam=team, result='DRAW').count()
        xdrawaway = self.filter(awayteam=team, result='DRAW').count()
        return (xhome + xaway) * 3 + xdrawhome + xdrawaway

    def team_points_optimized(self, sn, tm, dt):
        homepts = self.filter(hometeam=tm, season=sn, date__lte=dt).aggregate(Sum('hm_points'))
        awaypts = self.filter(awayteam=tm, season=sn, date__lte=dt).aggregate(Sum('aw_points'))
        total_points = homepts['hm_points__sum'] + awaypts['aw_points__sum']
        return total_points

    def team_playoff_points(self, sn, tm, dt):
        homepts = self.filter(hometeam=tm, season=sn, date__lte=dt, type='PO', homegoals__gte=0).aggregate(Sum('hm_points'))
        awaypts = self.filter(awayteam=tm, season=sn, date__lte=dt, type='PO', homegoals__gte=0).aggregate(Sum('aw_points'))
        if homepts['hm_points__sum'] is None:
            homepts['hm_points__sum'] = 0
        if awaypts['aw_points__sum'] is None:
            awaypts['aw_points__sum'] = 0

        total_points = homepts['hm_points__sum'] + awaypts['aw_points__sum']
        return total_points

    # total games played by a team up to the given gameweek (not used)
    # def get_total_games(self, team, seasn, gmweek):
    #     tmgames = self.filter(Q(hometeam=team, season=seasn, gameweek__lte=gmweek) | Q(awayteam=team, season=seasn, gameweek__lte=gmweek))
    #     tmgames_cnt = tmgames.count()
    #     return tmgames_cnt

    # returns the team's previous elo rating based on gameweek. So it returns the previous gameweek's rating
    # def get_previous_elo(self, tm, seasn, gmwk):
    #     out = 0
    #     prevgmwk = gmwk - 1
    #     if gmwk == 1:
    #         out = elosettings.STARTING_POINTS
    #     elif gmwk > 1:
    #         iprevgame = self.filter(Q(hometeam=tm, season=seasn, gameweek=prevgmwk) | Q(awayteam=tm, season=seasn, gameweek=prevgmwk))
    #         prevgame = iprevgame.get(Q(hometeam=tm) | Q(awayteam=tm))
    #         if prevgame.hometeam == tm:
    #             out = prevgame.elo_rating_home
    #         elif prevgame.awayteam == tm:
    #             out = prevgame.elo_rating_away
    #     return out

    # returns the team's previous elo rating based on date. So it returns the team's previous game's rating. This is
    # useful when a team's game has been postponed and you want to retrieve the real form
    # def get_previous_elo_by_date(self, tm, seasn, gmwk):
    #     try:
    #         date_threshold = self.filter(Q(hometeam=tm, season=seasn, gameweek__lte=gmwk) | Q(awayteam=tm, season=seasn, gameweek__lte=gmwk)).order_by('-date')[0].date
    #         qs = self.filter(Q(hometeam=tm, season=seasn, date__lt=date_threshold) | Q(awayteam=tm, season=seasn, date__lt=date_threshold)).order_by('-date')
    #         # identify the first gameweek by reversing the queryset and getting the first gameweek of the first object
    #         firstgw = qs.reverse()[0].gameweek
    #         out = 0
    #         if gmwk == firstgw:
    #             out = elosettings.STARTING_POINTS
    #         else:
    #             # get the second object of qs as the first one is the current game
    #             prevgame = qs[0]
    #             if prevgame.hometeam == tm:
    #                 out = prevgame.elo_rating_home
    #             elif prevgame.awayteam == tm:
    #                 out = prevgame.elo_rating_away
    #     except IndexError:
    #         out = elosettings.STARTING_POINTS
    #     return out

    def get_previous_elo_by_date(self, tm, seasn, gmwk):
        try:
            date_threshold = self.filter(Q(hometeam=tm, season=seasn, gameweek=gmwk) | Q(awayteam=tm, season=seasn, gameweek=gmwk)).order_by('-date')[0].date
            qs = self.filter(Q(hometeam=tm, season=seasn, date__lt=date_threshold) | Q(awayteam=tm, season=seasn, date__lt=date_threshold)).order_by('-date')
        except IndexError:
            date_threshold = self.filter(Q(hometeam=tm, season=seasn, gameweek__lte=gmwk) | Q(awayteam=tm, season=seasn, gameweek__lte=gmwk)).order_by('-date')[0].date
            qs = self.filter(Q(hometeam=tm, season=seasn, date__lte=date_threshold) | Q(awayteam=tm, season=seasn, date__lte=date_threshold)).order_by('-date')
        # identify the first gameweek by reversing the queryset and getting the first gameweek of the first object
        out = 0
        if self.is_first_game(tm, seasn, date_threshold) == 'Yes':
            out = elosettings.STARTING_POINTS
        else:
            # get the second object of qs as the first one is the current game
            prevgame = qs[0]
            if prevgame.hometeam == tm:
                out = prevgame.elo_rating_home
            elif prevgame.awayteam == tm:
                out = prevgame.elo_rating_away
        return out

    # this version of get previous elo understands if this is the first time an elo is being queried for a team
    def get_previous_elo_by_actual_date_for_initial(self, tm, seasn, dt):
        try:
            qs = self.filter(Q(hometeam=tm, season=seasn, date__lt=dt) | Q(awayteam=tm, season=seasn, date__lt=dt)).order_by('-date')
        except IndexError:
            qs = self.filter(Q(hometeam=tm, season=seasn, date__lte=dt) | Q(awayteam=tm, season=seasn, date__lte=dt)).order_by('-date')
        out = 0
        if self.is_first_game(tm, seasn, dt) == 'Yes':
            out = elosettings.STARTING_POINTS
        else:
            # get the second object of qs as the first one is the current game
            prevgame = qs[0]
            if prevgame.hometeam == tm:
                out = prevgame.elo_rating_home
            elif prevgame.awayteam == tm:
                out = prevgame.elo_rating_away
        return out

    def get_previous_elo_by_actual_date(self, tm, seasn, dt, gw):
        qs = self.filter(Q(hometeam=tm, season=seasn, date__lte=dt) | Q(awayteam=tm, season=seasn, date__lte=dt)).order_by('-date')
        gmwk = qs[0].gameweek
        prevgame = qs[0]
        # identify the first gameweek by reversing the queryset and getting the first gameweek of the first object
        firstgw = qs.reverse()[0].gameweek
        out = 0
        if gmwk == firstgw:
            out = elosettings.STARTING_POINTS
        elif gmwk == gw:
            prevgame = qs[1]
        else:
            # get the second object of qs as the first one is the current game
            prevgame = qs[0]
        if prevgame.hometeam == tm:
            out = prevgame.elo_rating_home
        elif prevgame.awayteam == tm:
            out = prevgame.elo_rating_away
        return out

    # returns the elo rating of as far back as you tell it. i.e if I'm on gameweek 10 and want the elo rating of 4
    # games back (not necessarily 4 gameweeks back), I give the following variables: tm, season, 10, 4
    def get_previous_elo_from_lookback(self, tm, seasn, gmwk, lookback):
        # identify the date of the current game and set as threshold
        date_threshold = self.filter(Q(hometeam=tm, season=seasn, gameweek__lt=gmwk) | Q(awayteam=tm, season=seasn, gameweek__lt=gmwk)).order_by('-date')[0].date
        qs = self.filter(Q(hometeam=tm, season=seasn, date__lte=date_threshold) | Q(awayteam=tm, season=seasn, date__lte=date_threshold)).order_by('-date')
        # identify the first gameweek by reversing the queryset and getting the first gameweek of the first object
        firstgw = qs.reverse()[0].gameweek
        out = 0
        if gmwk == firstgw:
            out = elosettings.STARTING_POINTS
        else:
            prevgame = qs[lookback - 1]
            if prevgame.hometeam == tm:
                out = prevgame.elo_rating_home
            elif prevgame.awayteam == tm:
                out = prevgame.elo_rating_away
        return out

    # returns the elo rating of as far back as you tell it. i.e if I'm on gameweek 10 and want the elo rating of 4
    # games back (not necessarily 4 gameweeks back), I give the following variables: tm, season, 10, 4
    def get_previous_elo_from_lookback_by_date(self, tm, seasn, dt, lookback):
        # identify the date of the current game and set as threshold
        qs = self.filter(Q(hometeam=tm, season=seasn, date__lt=dt) | Q(awayteam=tm, season=seasn, date__lt=dt)).order_by('-date')
        # date_threshold = qs[0].date
        # qs = self.filter(Q(hometeam=tm, season=seasn, date__lte=date_threshold) | Q(awayteam=tm, season=seasn, date__lte=date_threshold)).order_by('-date')
        # identify the first gameweek by reversing the queryset and getting the first gameweek of the first object
        # firstgw = qs.reverse()[0].gameweek
        out = 0
        if qs.count() <= 5:
            pass
        else:
            prevgame = qs[lookback - 1]
            if prevgame.hometeam == tm:
                out = prevgame.elo_rating_home
            elif prevgame.awayteam == tm:
                out = prevgame.elo_rating_away
        return out

    def last_gameweek(self, seasn):
        # season_games = self.filter(season=seasn).order_by('-gameweek')
        season_games = self.filter(season=seasn).exclude(result__exact='').exclude(result__isnull=True).order_by('-gameweek')
        # retrieves the most recent gameweek
        max_gw = season_games[0].gameweek
        # retrieves all the games in the most recent gameweek for the given season
        ldrbrd_list = self.filter(season=seasn, gameweek=max_gw)
        return ldrbrd_list

    # def modified_hga(self, teamm, seasonn, gmwk):
    #     total_home_wins = self.filter(season=seasonn, hometeam=teamm, gameweek__lte=gmwk - 1, result='HOME').count()
    #     total_home_draws = self.filter(season=seasonn, hometeam=teamm, gameweek__lte=gmwk - 1, result='DRAW').count()
    #     win_points = total_home_wins * 1
    #     draw_points = total_home_draws * 0.5
    #     total_games = self.filter(hometeam=teamm, season=seasonn, gameweek__lte=gmwk - 1).count()
    #     if total_games == 0 or gmwk == 1:
    #         mhga = elosettings.ELO_HGA
    #     else:
    #         strike_rate = (win_points + draw_points) / total_games
    #         mhga = strike_rate * float(elosettings.ELO_HGA)
    #     return mhga

    def modified_hga_from_date(self, teamm, seasonn, dt):
        total_home_wins = self.filter(season=seasonn, hometeam=teamm, date__lt=dt, result='HOME').count()
        total_home_draws = self.filter(season=seasonn, hometeam=teamm, date__lt=dt, result='DRAW').count()
        win_points = total_home_wins * 1
        draw_points = total_home_draws * 0.5
        total_games = self.filter(hometeam=teamm, season=seasonn, date__lt=dt).count()
        if total_games == 0:
            mhga = elosettings.ELO_HGA
        else:
            strike_rate = (win_points + draw_points) / total_games
            mhga = strike_rate * float(elosettings.ELO_HGA)
        return mhga

    # def elo_draw_threshold(self, seasonn, gamewk):
    #     if gamewk == 1:
    #         out = 0
    #     else:
    #         games_lst = self.filter(season=seasonn, gameweek__lte=gamewk - 1).order_by('-date')
    #         szn = Season.objects.get(id=seasonn)
    #         # I used to use teamstotal from the leagues model (instead of num_of_teams_in_season) but it was wrong because year by year the number of teams in a league might change
    #         # So the teamstotal in leagues is actually redundant
    #         # num_of_teams_in_season = Team.objects.filter(Q(hometeam__season__id=szn) | Q(awayteam__season__id=szn)).distinct().count()
    #         num_of_teams_in_season = szn.teamstotal
    #         multiplier = -num_of_teams_in_season / 2
    #         x = []
    #         for gm in games_lst:
    #             # h_r_old = self.get_previous_elo(tm=gm.hometeam, seasn=seasonn, gmwk=gm.gameweek)
    #             # a_r_old = self.get_previous_elo(tm=gm.awayteam, seasn=seasonn, gmwk=gm.gameweek)
    #             # rdiff = round(h_r_old - a_r_old, 0)
    #             # x.append(rdiff)
    #             x.append(gm.rdiff)
    #         out = abs(sum(x) / games_lst.count()) * multiplier
    #         # print x
    #     return out

    def elo_draw_threshold_by_id(self, gameid):
        g = self.get(id=gameid)
        qs = self.set_of_games_played_before_game_date_optimized(gameid, 'No')
        if qs.count() <= 1:
            out = 0
        else:
            games_lst = qs.order_by('-date')
            szn = Season.objects.get(id=g.season.id)
            num_of_teams_in_season = szn.teamstotal
            multiplier = -num_of_teams_in_season / 2
            x = []
            for gm in games_lst:
                x.append(gm.rdiff)
            out = abs(sum(x) / float(games_lst.count())) * multiplier
        return out

    def elo_draw_threshold_by_date(self, season, dt):
        qs = self.set_of_games_played_before_game_date_by_date_optimized(season, dt, 'No')
        if qs.count() <= 1:
            out = 0
        else:
            games_lst = qs.order_by('-date')
            szn = Season.objects.get(id=season)
            num_of_teams_in_season = szn.teamstotal
            multiplier = -num_of_teams_in_season / 2
            x = []
            for gm in games_lst:
                x.append(gm.rdiff)
            out = abs(sum(x) / float(games_lst.count())) * multiplier
        return out

    # def elol6_draw_threshold(self, seasonn, gamewk):
    #     x = []
    #     if gamewk <= 7:
    #         out = 0
    #     else:
    #         games_lst = self.filter(season=seasonn, gameweek__lte=gamewk - 1, gameweek__gte=7).order_by('-date')
    #         szn = Season.objects.get(id=seasonn)
    #         # I used to use teamstotal from the leagues model (instead of num_of_teams_in_season) but it was wrong because year by year the number of teams in a league might change
    #         # So the teamstotal in leagues is actually redundant
    #         # num_of_teams_in_season = Team.objects.filter(Q(hometeam__season__id=szn) | Q(awayteam__season__id=szn)).distinct().count()
    #         num_of_teams_in_season = szn.teamstotal
    #         multiplier = -num_of_teams_in_season / 2
    #         x = []
    #         for gm in games_lst:
    #             # h_r_old = self.get_previous_elo(tm=gm.hometeam, seasn=seasonn, gmwk=gm.gameweek) - self.get_previous_elo(tm=gm.hometeam, seasn=seasonn, gmwk=gm.gameweek - 5)
    #             # a_r_old = self.get_previous_elo(tm=gm.awayteam, seasn=seasonn, gmwk=gm.gameweek) - self.get_previous_elo(tm=gm.awayteam, seasn=seasonn, gmwk=gm.gameweek - 5)
    #             h_r_old = gm.elo_rating_home_previous_week - self.get_previous_elo(tm=gm.hometeam, seasn=seasonn, gmwk=gm.gameweek - 5)
    #             a_r_old = gm.elo_rating_away_previous_week - self.get_previous_elo(tm=gm.awayteam, seasn=seasonn, gmwk=gm.gameweek - 5)
    #             rdiff = round(h_r_old - a_r_old, 0)
    #             x.append(rdiff)
    #         out = abs(sum(x) / float(games_lst.count())) * multiplier
    #     return out

    def elol6_draw_threshold_by_id(self, gameid):
        g = self.get(id=gameid)
        qs_wout_first_6 = self.set_of_games_played_before_game_date_optimized(gameid, 'Yes')
        if qs_wout_first_6.count() <= 1:
            out = 0
        else:
            games_lst = qs_wout_first_6.order_by('-date')
            szn = Season.objects.get(id=g.season.id)
            num_of_teams_in_season = szn.teamstotal
            multiplier = -num_of_teams_in_season / 2
            x = []
            for gm in games_lst:
                # h_r_old = gm.elo_rating_home_previous_week - self.get_previous_elo_from_lookback_by_date(gm.hometeam, szn, gm.date, 6)
                # a_r_old = gm.elo_rating_away_previous_week - self.get_previous_elo_from_lookback_by_date(gm.awayteam, szn, gm.date, 6)
                # rdiff = round(h_r_old - a_r_old, 0)
                # x.append(rdiff)
                rdiff = gm.r_difference_6_games_back()
                x.append(rdiff)
            out = abs(sum(x) / float(games_lst.count())) * multiplier
        return out

    def elol6_draw_threshold_by_date(self, season, dt):
        qs_wout_first_6 = self.set_of_games_played_before_game_date_by_date_optimized(season, dt, 'Yes')
        if qs_wout_first_6.count() <= 1:
            out = 0
        else:
            games_lst = qs_wout_first_6.order_by('-date')
            szn = Season.objects.get(id=season)
            num_of_teams_in_season = szn.teamstotal
            multiplier = -num_of_teams_in_season / 2
            x = []
            for gm in games_lst:
                # h_r_old = gm.elo_rating_home_previous_week - self.get_previous_elo_from_lookback_by_date(gm.hometeam, szn, dt, 6)
                # a_r_old = gm.elo_rating_away_previous_week - self.get_previous_elo_from_lookback_by_date(gm.awayteam, szn, dt, 6)
                # rdiff = round(h_r_old - a_r_old, 0)
                rdiff = gm.r_difference_6_games_back()
                x.append(rdiff)
            out = abs(sum(x) / float(games_lst.count())) * multiplier
        return out

    # def total_goal_diff(self, tm, seasn, gw):
    #     if gw <= 6:
    #         out = 0
    #     else:
    #         lst_hm = self.filter(hometeam=tm, season=seasn, gameweek__lte=gw - 1, gameweek__gte=gw - 6)
    #         lst_aw = self.filter(awayteam=tm, season=seasn, gameweek__lte=gw - 1, gameweek__gte=gw - 6)
    #         scored_hm = lst_hm.aggregate(Sum('homegoals'))
    #         scored_aw = lst_aw.aggregate(Sum('awaygoals'))
    #         scored = scored_hm.get('homegoals__sum') + scored_aw.get('awaygoals__sum')
    #         conceded_hm = lst_hm.aggregate(Sum('awaygoals'))
    #         conceded_aw = lst_aw.aggregate(Sum('homegoals'))
    #         conceded = conceded_hm.get('awaygoals__sum') + conceded_aw.get('homegoals__sum')
    #         out = scored - conceded
    #     return out

    def total_goal_diff_from_date(self, tm, seasn, dt):
        team_games = self.set_of_team_games_played_before_game_date_2(tm, seasn, dt, 'No').order_by('-date')

        cnt_of_all_games = team_games.count()
        if cnt_of_all_games < 6:
            out = 0
        else:
            team_games_6th_date = team_games[5].date
            lst_hm = team_games.filter(hometeam=tm, date__gte=team_games_6th_date)
            lst_aw = team_games.filter(awayteam=tm, date__gte=team_games_6th_date)
            scored_hm = lst_hm.aggregate(Sum('homegoals'))
            scored_aw = lst_aw.aggregate(Sum('awaygoals'))
            scored = scored_hm.get('homegoals__sum') + scored_aw.get('awaygoals__sum')
            conceded_hm = lst_hm.aggregate(Sum('awaygoals'))
            conceded_aw = lst_aw.aggregate(Sum('homegoals'))
            conceded = conceded_hm.get('awaygoals__sum') + conceded_aw.get('homegoals__sum')
            out = scored - conceded
        return out

    def gsrs_draw_threshold(self, seasonn, gamewk):
        x = []
        if gamewk <= 7:
            out = 0
        else:
            games_lst = self.filter(season=seasonn, gameweek__lte=gamewk - 1, gameweek__gte=7)
            szn = Season.objects.get(id=seasonn)
            # multiplier = -szn.league.teamstotal / 2
            num_of_teams_in_season = szn.teamstotal
            multiplier = -num_of_teams_in_season / 2
            for gm in games_lst:
                # hm_goal_diff = self.total_goal_diff(tm=gm.hometeam, seasn=gm.season.id, gw=gm.gameweek)
                # aw_goal_diff = self.total_goal_diff(tm=gm.awayteam, seasn=gm.season.id, gw=gm.gameweek)
                # gm_goal_diff = hm_goal_diff - aw_goal_diff
                # x.append(gm_goal_diff)
                x.append(gm.gsrs_goaldiff())
            out = abs(sum(x) / float(len(x))) * multiplier
        return out

    def gsrs_draw_threshold_by_id(self, gameid):
        g = self.get(id=gameid)
        qs_wout_first_6 = self.set_of_games_played_before_game_date_optimized(gameid, 'Yes')
        if qs_wout_first_6.count() <= 1:
            out = 0
        else:
            games_lst = qs_wout_first_6.order_by('-date')
            szn = Season.objects.get(id=g.season.id)
            num_of_teams_in_season = szn.teamstotal
            multiplier = -num_of_teams_in_season / 2
            x = []
            for gm in games_lst:
                x.append(gm.gsrs_goaldiff())
            out = abs(sum(x) / float(games_lst.count())) * multiplier
        return out

    def gsrs_draw_threshold_by_date(self, season, dt):
        qs_wout_first_6 = self.set_of_games_played_before_game_date_by_date_optimized(season, dt, 'Yes')
        if qs_wout_first_6.count() <= 1:
            out = 0
        else:
            games_lst = qs_wout_first_6.order_by('-date')
            szn = Season.objects.get(id=season)
            num_of_teams_in_season = szn.teamstotal
            multiplier = -num_of_teams_in_season / 2
            x = []
            for gm in games_lst:
                x.append(gm.gsrs_goaldiff())
            out = abs(sum(x) / float(games_lst.count())) * multiplier
        return out

    # def elo_hist_prediction(self, hometm, awaytm, szn, gweek):
    #     date_threshold = self.filter(hometeam=hometm, awayteam=awaytm, season=szn, gameweek=gweek)[0].date
    #     max_gw = self.filter(season=szn, date__lte=date_threshold).order_by('-gameweek')[0].gameweek
    #
    #     if max_gw <= gweek:
    #         gweek = gweek
    #     else:
    #         gweek = 'current'
    #
    #     if gweek == 'current':
    #         current_gw = self.last_gameweek(seasn=szn)[0].gameweek
    #         home_r = self.get_previous_elo_by_date(tm=hometm, seasn=szn, gmwk=current_gw)
    #         away_r = self.get_previous_elo_by_date(tm=awaytm, seasn=szn, gmwk=current_gw)
    #         rdiff = home_r - away_r
    #         draw_threshold = self.elo_draw_threshold(seasonn=szn, gamewk=current_gw)
    #         if rdiff > draw_threshold:
    #             prediction = "HOME"
    #         elif rdiff < (draw_threshold * 2):
    #             prediction = "AWAY"
    #         else:
    #             prediction = "DRAW"
    #     elif gweek > 6:
    #         home_r = self.get_previous_elo_by_date(tm=hometm, seasn=szn, gmwk=gweek)
    #         away_r = self.get_previous_elo_by_date(tm=awaytm, seasn=szn, gmwk=gweek)
    #         rdiff = home_r - away_r
    #         # print("{}: about to run elo_draw_threshold".format(datetime.now()))
    #         draw_threshold = self.elo_draw_threshold(seasonn=szn, gamewk=gweek)
    #         # print("{}: ran elo_draw_threshold".format(datetime.now()))
    #         if rdiff > draw_threshold:
    #             prediction = "HOME"
    #         elif rdiff < (draw_threshold * 2):
    #             prediction = "AWAY"
    #         else:
    #             prediction = "DRAW"
    #     else:
    #         prediction = "Not enough games to calculate prediction (the model needs at least 6 gameweeks)"
    #     return prediction

    def elo_hist_prediction_by_id(self, gameid):
        g = self.get(id=gameid)
        qshome = self.set_of_team_games_played_before_game_date_2(g.hometeam, g.season, g.date, 'No')
        qsaway = self.set_of_team_games_played_before_game_date_2(g.awayteam, g.season, g.date, 'No')
        cnt_home = qshome.count()
        cnt_away = qsaway.count()
        # if any of the teams has played less then 6 games
        if cnt_home < 6 or cnt_away < 6:
            prediction = "Not enough games to calculate prediction (the model needs at least 6 gameweeks)"
        else:
            home_r = self.get_previous_elo_by_date(tm=g.hometeam, seasn=g.season, gmwk=g.gameweek)
            away_r = self.get_previous_elo_by_date(tm=g.awayteam, seasn=g.season, gmwk=g.gameweek)
            rdiff = home_r - away_r
            draw_threshold = self.elo_draw_threshold_by_id(gameid)
            if rdiff > draw_threshold:
                prediction = "HOME"
            elif rdiff < (draw_threshold * 2):
                prediction = "AWAY"
            else:
                prediction = "DRAW"
        return prediction

    def elo_hist_prediction_by_date(self, home, away, season, dt, gw):
        qshome = self.set_of_team_games_played_before_game_date_2(home, season, dt, 'No')
        qsaway = self.set_of_team_games_played_before_game_date_2(away, season, dt, 'No')
        cnt_home = qshome.count()
        cnt_away = qsaway.count()
        # if any of the teams has played less then 6 games
        if cnt_home < 6 or cnt_away < 6:
            prediction = "Not enough games to calculate prediction (the model needs at least 6 gameweeks)"
        else:
            home_r = self.get_previous_elo_by_date(tm=home, seasn=season, gmwk=gw)
            away_r = self.get_previous_elo_by_date(tm=away, seasn=season, gmwk=gw)
            rdiff = home_r - away_r
            draw_threshold = self.elo_draw_threshold_by_date(season, dt)
            if rdiff > draw_threshold:
                prediction = "HOME"
            elif rdiff < (draw_threshold * 2):
                prediction = "AWAY"
            else:
                prediction = "DRAW"
        return prediction

    # def elo_l6_prediction(self, hometm, awaytm, szn, gweek):
    #     date_threshold = self.filter(hometeam=hometm, awayteam=awaytm, season=szn, gameweek=gweek)[0].date
    #     max_gw = self.filter(season=szn, date__lte=date_threshold).order_by('-gameweek')[0].gameweek
    #
    #     if max_gw <= gweek:
    #         gweek = gweek
    #     else:
    #         gweek = 'current'
    #
    #     if gweek == 'current':
    #         current_gw = self.last_gameweek(seasn=szn)[0].gameweek
    #         home_r = self.get_previous_elo_by_date(tm=hometm, seasn=szn, gmwk=current_gw) - self.get_previous_elo_by_date(tm=hometm, seasn=szn, gmwk=current_gw - 5)
    #         away_r = self.get_previous_elo_by_date(tm=awaytm, seasn=szn, gmwk=current_gw) - self.get_previous_elo_by_date(tm=awaytm, seasn=szn, gmwk=current_gw - 5)
    #         rdiff = home_r - away_r
    #         draw_threshold = self.elol6_draw_threshold(seasonn=szn, gamewk=current_gw)
    #         if rdiff > draw_threshold:
    #             prediction = "HOME"
    #         elif rdiff < (draw_threshold * 2):
    #             prediction = "AWAY"
    #         else:
    #             prediction = "DRAW"
    #     elif gweek > 6:
    #         home_r = self.get_previous_elo_by_date(tm=hometm, seasn=szn, gmwk=gweek) - self.get_previous_elo_by_date(tm=hometm, seasn=szn, gmwk=gweek - 5)
    #         away_r = self.get_previous_elo_by_date(tm=awaytm, seasn=szn, gmwk=gweek) - self.get_previous_elo_by_date(tm=awaytm, seasn=szn, gmwk=gweek - 5)
    #         rdiff = home_r - away_r
    #         draw_threshold = self.elol6_draw_threshold(seasonn=szn, gamewk=gweek)
    #         if rdiff > draw_threshold:
    #             prediction = "HOME"
    #         elif rdiff < (draw_threshold * 2):
    #             prediction = "AWAY"
    #         else:
    #             prediction = "DRAW"
    #     else:
    #         prediction = "Not enough games to calculate prediction (the model needs at least 6 gameweeks)"
    #     return prediction

    def elo_l6_prediction_by_id(self, gameid):
        g = self.get(id=gameid)
        # qshome = self.filter(Q(hometeam=g.hometeam, season=g.season, date__lt=g.date) | Q(awayteam=g.hometeam, season=g.season, date__lt=g.date)).order_by('-date')
        qshome = self.set_of_team_games_played_before_game_date_2(g.hometeam, g.season, g.date, 'No')
        qsaway = self.set_of_team_games_played_before_game_date_2(g.awayteam, g.season, g.date, 'No')
        # qs = self.set_of_games_played_before_game_date(gameid, 'No')
        # finds the max gameweek from qs so it can use that for draw threshold
        # gw_for_draw_threshold = qs.order_by('-gameweek')[0].gameweek
        cnt_home = qshome.count()
        cnt_away = qsaway.count()
        # if any of the teams has played less then 6 games
        if cnt_home < 6 or cnt_away < 6:
            prediction = "Not enough games to calculate prediction (the model needs at least 6 gameweeks)"
        else:
            home_r = self.get_previous_elo_by_date(tm=g.hometeam, seasn=g.season, gmwk=g.gameweek) - self.get_previous_elo_from_lookback_by_date(g.hometeam, g.season, g.date, 6)
            away_r = self.get_previous_elo_by_date(tm=g.awayteam, seasn=g.season, gmwk=g.gameweek) - self.get_previous_elo_from_lookback_by_date(g.awayteam, g.season, g.date, 6)
            rdiff = home_r - away_r
            draw_threshold = self.elol6_draw_threshold_by_id(gameid)
            if rdiff > draw_threshold:
                prediction = "HOME"
            elif rdiff < (draw_threshold * 2):
                prediction = "AWAY"
            else:
                prediction = "DRAW"
        return prediction

    def elo_l6_prediction_by_date(self, home, away, season, dt, gw):
        # qshome = self.filter(Q(hometeam=g.hometeam, season=g.season, date__lt=g.date) | Q(awayteam=g.hometeam, season=g.season, date__lt=g.date)).order_by('-date')
        # t1 = datetime.now()
        qshome = self.set_of_team_games_played_before_game_date_2(home, season, dt, 'No')
        qsaway = self.set_of_team_games_played_before_game_date_2(away, season, dt, 'No')
        # t2 = datetime.now()
        # t3 = (t2 - t1).total_seconds()
        # print('qshome and qsaway:', t3)
        # qs = self.set_of_games_played_before_game_date(gameid, 'No')
        # finds the max gameweek from qs so it can use that for draw threshold
        # gw_for_draw_threshold = qs.order_by('-gameweek')[0].gameweek
        cnt_home = qshome.count()
        cnt_away = qsaway.count()
        # if any of the teams has played less then 6 games
        if cnt_home < 6 or cnt_away < 6:
            prediction = "Not enough games to calculate prediction (the model needs at least 6 gameweeks)"
        else:
            # t1 = datetime.now()
            home_r = self.get_previous_elo_by_date(tm=home, seasn=season, gmwk=gw) - self.get_previous_elo_from_lookback_by_date(home, season, dt, 6)
            away_r = self.get_previous_elo_by_date(tm=away, seasn=season, gmwk=gw) - self.get_previous_elo_from_lookback_by_date(away, season, dt, 6)
            # t2 = datetime.now()
            # t3 = (t2 - t1).total_seconds()
            # print('get previous elo and from lookback:', t3)
            rdiff = home_r - away_r
            # t1 = datetime.now()
            draw_threshold = self.elol6_draw_threshold_by_date(season, dt)
            # t2 = datetime.now()
            # t3 = (t2 - t1).total_seconds()
            # print('elol6_draw_threshold:', t3)
            if rdiff > draw_threshold:
                prediction = "HOME"
            elif rdiff < (draw_threshold * 2):
                prediction = "AWAY"
            else:
                prediction = "DRAW"
        return prediction

    def gsrs_prediction(self, hm, aw, sn, gmwkk):
        if gmwkk == 'current':
            current_gw = self.last_gameweek(seasn=sn)[0].gameweek
            hm_hmdiff = self.filter(hometeam=hm, season=sn, gameweek__lt=current_gw, gameweek__gte=current_gw - 6).aggregate(hm_hmdiffsum=Sum(F('homegoals') - F('awaygoals')))
            hm_awdiff = self.filter(awayteam=hm, season=sn, gameweek__lt=current_gw, gameweek__gte=current_gw - 6).aggregate(hm_awdiffsum=Sum(F('awaygoals') - F('homegoals')))
            aw_hmdiff = self.filter(hometeam=aw, season=sn, gameweek__lt=current_gw, gameweek__gte=current_gw - 6).aggregate(aw_hmdiffsum=Sum(F('homegoals') - F('awaygoals')))
            aw_awdiff = self.filter(awayteam=aw, season=sn, gameweek__lt=current_gw, gameweek__gte=current_gw - 6).aggregate(aw_awdiffsum=Sum(F('awaygoals') - F('homegoals')))
            home_rating = hm_hmdiff.get('hm_hmdiffsum') + hm_awdiff.get('hm_awdiffsum')
            away_rating = aw_hmdiff.get('aw_hmdiffsum') + aw_awdiff.get('aw_awdiffsum')
            match_rating = home_rating - away_rating
            draw_threshold = self.gsrs_draw_threshold(seasonn=sn, gamewk=current_gw)
            if match_rating > draw_threshold:
                prediction = "HOME"
            elif match_rating < (draw_threshold * 2):
                prediction = "AWAY"
            else:
                prediction = "DRAW"
        elif gmwkk > 6:
            hm_hmdiff = self.filter(hometeam=hm, season=sn, gameweek__lt=gmwkk, gameweek__gte=gmwkk - 6).aggregate(hm_hmdiffsum=Sum(F('homegoals') - F('awaygoals')))
            hm_awdiff = self.filter(awayteam=hm, season=sn, gameweek__lt=gmwkk, gameweek__gte=gmwkk - 6).aggregate(hm_awdiffsum=Sum(F('awaygoals') - F('homegoals')))
            aw_hmdiff = self.filter(hometeam=aw, season=sn, gameweek__lt=gmwkk, gameweek__gte=gmwkk - 6).aggregate(aw_hmdiffsum=Sum(F('homegoals') - F('awaygoals')))
            aw_awdiff = self.filter(awayteam=aw, season=sn, gameweek__lt=gmwkk, gameweek__gte=gmwkk - 6).aggregate(aw_awdiffsum=Sum(F('awaygoals') - F('homegoals')))
            home_rating = hm_hmdiff.get('hm_hmdiffsum') + hm_awdiff.get('hm_awdiffsum')
            away_rating = aw_hmdiff.get('aw_hmdiffsum') + aw_awdiff.get('aw_awdiffsum')
            match_rating = home_rating - away_rating
            draw_threshold = self.gsrs_draw_threshold(seasonn=sn, gamewk=gmwkk)
            if match_rating > draw_threshold:
                prediction = "HOME"
            elif match_rating < (draw_threshold * 2):
                prediction = "AWAY"
            else:
                prediction = "DRAW"
        else:
            prediction = "Not enough games to calculate prediction (the model needs at least 6 gameweeks)"
        return prediction

    def gsrs_prediction_by_id(self, gameid):
        g = self.get(id=gameid)
        # qshome = self.filter(Q(hometeam=g.hometeam, season=g.season, date__lt=g.date) | Q(awayteam=g.hometeam, season=g.season, date__lt=g.date)).order_by('-date')
        qshome = self.set_of_team_games_played_before_game_date_2(g.hometeam, g.season, g.date, 'No')
        qsaway = self.set_of_team_games_played_before_game_date_2(g.awayteam, g.season, g.date, 'No')
        cnt_home = qshome.count()
        cnt_away = qsaway.count()
        # if any of the teams has played less then 6 games
        if cnt_home < 6 or cnt_away < 6:
            prediction = "Not enough games to calculate prediction (the model needs at least 6 gameweeks)"
        else:
            # hm_hmdiff = self.filter(hometeam=g.hometeam, season=g.season, date__lt=g.date).order_by('-date')[0:6].aggregate(hm_hmdiffsum=Sum(F('homegoals') - F('awaygoals')))
            # hm_awdiff = self.filter(awayteam=g.hometeam, season=g.season, date__lt=g.date).order_by('-date')[0:6].aggregate(hm_awdiffsum=Sum(F('awaygoals') - F('homegoals')))
            # aw_hmdiff = self.filter(hometeam=g.awayteam, season=g.season, date__lt=g.date).order_by('-date')[0:6].aggregate(aw_hmdiffsum=Sum(F('homegoals') - F('awaygoals')))
            # aw_awdiff = self.filter(awayteam=g.awayteam, season=g.season, date__lt=g.date).order_by('-date')[0:6].aggregate(aw_awdiffsum=Sum(F('awaygoals') - F('homegoals')))
            hometm_6thgame = qshome.order_by('-date')[5].date
            awaytmtm_6thgame = qsaway.order_by('-date')[5].date
            hm_hmdiff = self.filter(hometeam=g.hometeam, season=g.season, date__lt=g.date, date__gte=hometm_6thgame).order_by('-date').aggregate(hm_hmdiffsum=Sum(F('homegoals') - F('awaygoals')))
            hm_awdiff = self.filter(awayteam=g.hometeam, season=g.season, date__lt=g.date, date__gte=hometm_6thgame).order_by('-date').aggregate(hm_awdiffsum=Sum(F('awaygoals') - F('homegoals')))
            aw_hmdiff = self.filter(hometeam=g.awayteam, season=g.season, date__lt=g.date, date__gte=awaytmtm_6thgame).order_by('-date').aggregate(aw_hmdiffsum=Sum(F('homegoals') - F('awaygoals')))
            aw_awdiff = self.filter(awayteam=g.awayteam, season=g.season, date__lt=g.date, date__gte=awaytmtm_6thgame).order_by('-date').aggregate(aw_awdiffsum=Sum(F('awaygoals') - F('homegoals')))
            home_rating = hm_hmdiff.get('hm_hmdiffsum') + hm_awdiff.get('hm_awdiffsum')
            away_rating = aw_hmdiff.get('aw_hmdiffsum') + aw_awdiff.get('aw_awdiffsum')
            match_rating = home_rating - away_rating
            draw_threshold = self.gsrs_draw_threshold_by_id(gameid)
            if match_rating > draw_threshold:
                prediction = "HOME"
            elif match_rating < (draw_threshold * 2):
                prediction = "AWAY"
            else:
                prediction = "DRAW"
        return prediction

    def gsrs_prediction_by_date(self, home, away, season, dt):
        # qshome = self.filter(Q(hometeam=g.hometeam, season=g.season, date__lt=g.date) | Q(awayteam=g.hometeam, season=g.season, date__lt=g.date)).order_by('-date')
        qshome = self.set_of_team_games_played_before_game_date_2(home, season, dt, 'No')
        qsaway = self.set_of_team_games_played_before_game_date_2(away, season, dt, 'No')
        cnt_home = qshome.count()
        cnt_away = qsaway.count()
        # if any of the teams has played less then 6 games
        if cnt_home < 6 or cnt_away < 6:
            prediction = "Not enough games to calculate prediction (the model needs at least 6 gameweeks)"
        else:
            hometm_6thgame = qshome.order_by('-date')[5].date
            awaytmtm_6thgame = qsaway.order_by('-date')[5].date
            hm_hmdiff = self.filter(hometeam=home, season=season, date__lt=dt, date__gte=hometm_6thgame).order_by('-date').aggregate(hm_hmdiffsum=Sum(F('homegoals') - F('awaygoals')))
            hm_awdiff = self.filter(awayteam=home, season=season, date__lt=dt, date__gte=hometm_6thgame).order_by('-date').aggregate(hm_awdiffsum=Sum(F('awaygoals') - F('homegoals')))
            aw_hmdiff = self.filter(hometeam=away, season=season, date__lt=dt, date__gte=awaytmtm_6thgame).order_by('-date').aggregate(aw_hmdiffsum=Sum(F('homegoals') - F('awaygoals')))
            aw_awdiff = self.filter(awayteam=away, season=season, date__lt=dt, date__gte=awaytmtm_6thgame).order_by('-date').aggregate(aw_awdiffsum=Sum(F('awaygoals') - F('homegoals')))
            # hm_hmdiff = self.filter(hometeam=home, season=season, date__lt=dt).order_by('-date')[0:6].aggregate(hm_hmdiffsum=Sum(F('homegoals') - F('awaygoals')))
            # hm_awdiff = self.filter(awayteam=home, season=season, date__lt=dt).order_by('-date')[0:6].aggregate(hm_awdiffsum=Sum(F('awaygoals') - F('homegoals')))
            # aw_hmdiff = self.filter(hometeam=away, season=season, date__lt=dt).order_by('-date')[0:6].aggregate(aw_hmdiffsum=Sum(F('homegoals') - F('awaygoals')))
            # aw_awdiff = self.filter(awayteam=away, season=season, date__lt=dt).order_by('-date')[0:6].aggregate(aw_awdiffsum=Sum(F('awaygoals') - F('homegoals')))
            home_rating = hm_hmdiff.get('hm_hmdiffsum') + hm_awdiff.get('hm_awdiffsum')
            away_rating = aw_hmdiff.get('aw_hmdiffsum') + aw_awdiff.get('aw_awdiffsum')
            match_rating = home_rating - away_rating
            draw_threshold = self.gsrs_draw_threshold_by_date(season, dt)
            if match_rating > draw_threshold:
                prediction = "HOME"
            elif match_rating < (draw_threshold * 2):
                prediction = "AWAY"
            else:
                prediction = "DRAW"
        return prediction

    # def team_form(self, team, szn, gmwk):
    #     x = ""
    #     if gmwk < 1:
    #         return x
    #     else:
    #         lst = self.get(Q(hometeam=team, season=szn, gameweek=gmwk) | Q(awayteam=team, season=szn, gameweek=gmwk))
    #         if lst.hometeam == team:
    #             if lst.result == 'HOME':
    #                 x = "W"
    #             elif lst.result == 'AWAY':
    #                 x = "L"
    #             elif lst.result == 'DRAW':
    #                 x = "D"
    #             else:
    #                 x = lst.game_status
    #         elif lst.awayteam == team:
    #             if lst.result == 'HOME':
    #                 x = "L"
    #             elif lst.result == 'AWAY':
    #                 x = "W"
    #             elif lst.result == 'DRAW':
    #                 x = "D"
    #             else:
    #                 x = lst.game_status
    #         else:
    #             x = ""
    #     return x

    def team_form_by_date(self, team, szn, gmwk):
        x = ""
        lst = self.get(Q(hometeam=team, season=szn, gameweek=gmwk) | Q(awayteam=team, season=szn, gameweek=gmwk))
        lstdate = lst.date
        gid = self.filter(Q(hometeam=team, season=szn, date__lte=lstdate, game_status='OK') | Q(awayteam=team, season=szn, date__lte=lstdate, game_status='OK')).order_by('-date')[0].id
        gm = self.get(id=gid)
        # gid = lst.id
        cnt = self.set_of_team_games_played_upto_game_date(team, gid, 'No').count()
        if cnt < 1:
            return x
        else:

            if gm.hometeam == team:
                if gm.result == 'HOME':
                    x = "W"
                elif gm.result == 'AWAY':
                    x = "L"
                elif gm.result == 'DRAW':
                    x = "D"
                else:
                    x = gm.game_status
            elif gm.awayteam == team:
                if gm.result == 'HOME':
                    x = "L"
                elif gm.result == 'AWAY':
                    x = "W"
                elif gm.result == 'DRAW':
                    x = "D"
                else:
                    x = gm.game_status
            else:
                x = ""
        return x

    # returns a dictionary with the last 6 games form (ordered by the date of the games not the gameweek)
    def team_form_list_by_date(self, team, sid, dt):
        x = []
        tmgames = (self
                   .select_related('hometeam', 'awayteam')
                   .filter(Q(hometeam=team, season=sid, date__lte=dt, game_status='OK', homegoals__gte=0) | Q(awayteam=team, season=sid, date__lte=dt, game_status='OK', awaygoals__gte=0))
                   .order_by('-date'))[0:6]
        if tmgames.count() < 1:
            pass
        else:
            for gm in tmgames:
                if gm.hometeam == team:
                    x.append(gm.hm_result)
                else:
                    x.append(gm.aw_result)
        return x

    def team_form_tooltip_by_date(self, team, sid, dt):
        x = []
        tmgames = (self
                   .select_related('hometeam', 'awayteam')
                   .filter(Q(hometeam=team, season=sid, date__lte=dt, game_status='OK', homegoals__gte=0) | Q(awayteam=team, season=sid, date__lte=dt, game_status='OK', awaygoals__gte=0))
                   .order_by('-date'))[0:6]
        if tmgames.count() < 1:
            pass
        else:
            for gm in tmgames:
                x.append(str(gm.hometeam) + ' - ' + str(gm.awayteam) + ' (' + str(gm.homegoals) + '-' + str(gm.awaygoals) + ')')
        return x

    # returns a list of pairs of form and tooltip
    def team_form_tooltip_joined_by_date(self, team, sid, dt):
        x = [['', ''], ['', ''], ['', ''], ['', ''], ['', ''], ['', '']]
        frm = self.team_form_list_by_date(team, sid, dt)
        tltp = self.team_form_tooltip_by_date(team, sid, dt)
        cnt = 0
        for pair in frm:
            x[cnt] = [pair, tltp[cnt]]
            cnt += 1
        return x

    def last_gameweek_played(self, team, seazn):
        qry = self.filter(Q(hometeam=team, season=seazn) | Q(awayteam=team, season=seazn)).exclude(result__exact='').exclude(result__isnull=True).order_by('-date')
        last_gameweek = qry[0].gameweek
        return last_gameweek

    # def last_gameweek_played(self, team, seazn):
    #     if self.filter(Q(hometeam=team, season=seazn) | Q(awayteam=team, season=seazn)).exclude(result__exact='').exclude(result__isnull=True).order_by('-date').exists():
    #         qry = self.filter(Q(hometeam=team, season=seazn) | Q(awayteam=team, season=seazn)).exclude(result__exact='').exclude(result__isnull=True).order_by('-date')
    #         last_gameweek = qry[0].gameweek
    #     else:
    #         last_gameweek = 1
    #     return last_gameweek

    # returns the date of the most recent match played for the given team
    def last_date_played(self, team, seazn):
        qry = self.filter(Q(hometeam=team, season=seazn) | Q(awayteam=team, season=seazn)).exclude(result__exact='').exclude(result__isnull=True).order_by('-date')
        last_gameweek = qry[0].date
        return last_gameweek

    # returns a queryset of all games played before the given date and excluding the current gameweek if it's the last
    def set_of_games_played_before_game_date(self, gameid, exclude_first_6_games):
        g = Game.objects.get(id=gameid)
        lastgw = Game.objects.last_gameweek(g.season)[0].gameweek
        if g.gameweek == lastgw:
            if exclude_first_6_games == 'No':
                qry = self.filter(season=g.season, date__lt=g.date).exclude(gameweek=g.gameweek).order_by('-date')
            else:
                qry = self.filter(season=g.season, date__lt=g.date).exclude(gameweek=g.gameweek).exclude(prediction_status_elohist__exact='').exclude(prediction_status_elohist__isnull=True).order_by('-date')
        # if the game is postponed and has been played later
        else:
            if exclude_first_6_games == 'No':
                qry = self.filter(season=g.season, date__lt=g.date).order_by('-date')
            else:
                qry = self.filter(season=g.season, date__lt=g.date).exclude(prediction_status_elohist__exact='').exclude(prediction_status_elohist__isnull=True).order_by('-date')
        return qry

    # returns a queryset of all games played before the given date and excluding the current gameweek
    def set_of_games_played_before_game_date_optimized(self, gameid, exclude_first_6_games):
        g = Game.objects.get(id=gameid)
        if exclude_first_6_games == 'No':
            qry = self.filter(season=g.season, date__lt=g.date).exclude(gameweek=g.gameweek).order_by('-date')
        else:
            qry = self.filter(season=g.season, date__lt=g.date).exclude(gameweek=g.gameweek).exclude(prediction_status_elohist__exact='').exclude(prediction_status_elohist__isnull=True).order_by('-date')
        return qry

    # same as above but given more arguments
    def set_of_games_played_before_game_date_by_date(self, season, dt, exclude_first_6_games):
        lastgw = Game.objects.last_gameweek(season)[0].gameweek
        gw = Game.objects.filter(season=season, date__lte=dt).order_by('-date')[0].gameweek
        if gw == lastgw:
            if exclude_first_6_games == 'No':
                qry = self.filter(season=season, date__lt=dt).exclude(gameweek=gw).order_by('-date')
            else:
                qry = self.filter(season=season, date__lt=dt).exclude(gameweek=gw).exclude(prediction_status_elohist__exact='').exclude(prediction_status_elohist__isnull=True).order_by('-date')
        # if the game is postponed and has been played later
        else:
            if exclude_first_6_games == 'No':
                qry = self.filter(season=season, date__lt=dt).order_by('-date')
            else:
                qry = self.filter(season=season, date__lt=dt).exclude(prediction_status_elohist__exact='').exclude(prediction_status_elohist__isnull=True).order_by('-date')
        return qry

    def set_of_games_played_before_game_date_by_date_optimized(self, season, dt, exclude_first_6_games):
        gw = Game.objects.filter(season=season, date__lte=dt).order_by('-date')[0].gameweek
        if exclude_first_6_games == 'No':
            qry = self.filter(season=season, date__lt=dt).exclude(gameweek=gw).order_by('-date')
        else:
            qry = self.filter(season=season, date__lt=dt).exclude(gameweek=gw).exclude(prediction_status_elohist__exact='').exclude(prediction_status_elohist__isnull=True).order_by('-date')
        return qry

    # returns a queryset of all games played by the given team before the given date
    def set_of_team_games_played_before_game_date(self, team, gameid, exclude_first_6_games):
        g = Game.objects.get(id=gameid)
        if exclude_first_6_games == 'No':
            qry = self.filter(Q(hometeam=team, season=g.season, date__lt=g.date, result__gte=0) | Q(awayteam=team, season=g.season, date__lt=g.date, result__gte=0)).order_by('-date')
        else:
            qry = self.filter(Q(hometeam=team, season=g.season, date__lt=g.date, result__gte=0) | Q(awayteam=team, season=g.season, date__lt=g.date, result__gte=0)).exclude(prediction_status_elohist__exact='')\
                .exclude(prediction_status_elohist__isnull=True).order_by('-date')
        return qry

    # same as above but accepts more variables
    def set_of_team_games_played_before_game_date_2(self, team, season, dt, exclude_first_6_games):
        if exclude_first_6_games == 'No':
            qry = self.filter(Q(hometeam=team, season=season, date__lt=dt, result__gte=0) | Q(awayteam=team, season=season, date__lt=dt, result__gte=0)).order_by('-date')
        else:
            qry = self.filter(Q(hometeam=team, season=season, date__lt=dt, result__gte=0) | Q(awayteam=team, season=season, date__lt=dt, result__gte=0)).exclude(prediction_status_elohist__exact='')\
                .exclude(prediction_status_elohist__isnull=True).order_by('-date')
        return qry

    # returns a queryset of all games played by the given team up to and including the given date
    def set_of_team_games_played_upto_game_date(self, team, gameid, exclude_first_6_games):
        g = Game.objects.get(id=gameid)
        if exclude_first_6_games == 'No':
            qry = self.filter(Q(hometeam=team, season=g.season, date__lte=g.date, result__gte=0) | Q(awayteam=team, season=g.season, date__lte=g.date, result__gte=0)).order_by('-date')
        else:
            qry = self.filter(Q(hometeam=team, season=g.season, date__lte=g.date, result__gte=0) | Q(awayteam=team, season=g.season, date__lte=g.date, result__gte=0)).exclude(prediction_status_elohist__exact='')\
                .exclude(prediction_status_elohist__isnull=True).order_by('-date')
        return qry

    # returns the total number of games played by the team in the given season
    def team_total_season_matches(self, tm, sn):
        qry = self.filter(Q(season=sn, hometeam=tm, result__gte=0) | Q(season=sn, awayteam=tm, result__gte=0))
        gms = qry.count()
        return gms

    # returns Yes if this is the first game of the given team and No if it's not
    def is_first_game(self, tm, sn, dt):
        qry = self.filter(Q(season=sn, hometeam=tm, date__lt=dt) | Q(season=sn, awayteam=tm, date__lt=dt))
        gms = qry.count()
        if gms < 1:
            is_first = 'Yes'
        else:
            is_first = 'No'
        return is_first

    # def team_total_wins(self, team, seazn, gw):
    #     qryset = self.filter(Q(hometeam=team, season=seazn, gameweek__lte=gw) | Q(awayteam=team, season=seazn, gameweek__lte=gw))
    #     total_wins = 0
    #     for g in qryset:
    #         if g.hometeam == team:
    #             if g.result == 'HOME':
    #                 total_wins += 1
    #         elif g.awayteam == team:
    #             if g.result == 'AWAY':
    #                 total_wins += 1
    #     return total_wins

    def team_total_wins_by_date(self, team, seazn, gw):
        gm = self.filter(Q(hometeam=team, season=seazn, gameweek=gw) | Q(awayteam=team, season=seazn, gameweek=gw))[0].id
        qryset = self.set_of_team_games_played_upto_game_date(team, gm, 'No')
        total_wins = 0
        for g in qryset:
            if g.hometeam == team:
                if g.result == 'HOME':
                    total_wins += 1
            elif g.awayteam == team:
                if g.result == 'AWAY':
                    total_wins += 1
        return total_wins

    def team_total_wins_by_date_optimized(self, team, sid, dt):
        wins_total = self.filter(Q(hometeam=team, season=sid, date__lte=dt, hm_result='W') | Q(awayteam=team, season=sid, date__lte=dt, aw_result='W')).count()
        return wins_total

    def team_total_wins_by_date_ex_current(self, team, seazn, gw):
        gm = self.filter(Q(hometeam=team, season=seazn, gameweek=gw) | Q(awayteam=team, season=seazn, gameweek=gw))[0].id
        qryset = self.set_of_team_games_played_before_game_date(team, gm, 'No')
        total_wins = 0
        for g in qryset:
            if g.hometeam == team:
                if g.result == 'HOME':
                    total_wins += 1
            elif g.awayteam == team:
                if g.result == 'AWAY':
                    total_wins += 1
        return total_wins

    def team_total_wins_home(self, team, sid, dt):
        wins_at_home = self.select_related('season').filter(hometeam=team, season=sid, date__lt=dt, hm_result='W').count()
        return wins_at_home

    def team_total_wins_away(self, team, sid, dt):
        wins_away = self.select_related('season').filter(awayteam=team, season=sid, date__lt=dt, aw_result='W').count()
        return wins_away

    def team_total_losses_home(self, team, sid, dt):
        losses_at_home = self.select_related('season').filter(hometeam=team, season=sid, date__lt=dt, hm_result='L').count()
        return losses_at_home

    def team_total_losses_away(self, team, sid, dt):
        losses_away = self.select_related('season').filter(awayteam=team, season=sid, date__lt=dt, aw_result='L').count()
        return losses_away

    def team_total_draws_home(self, team, sid, dt):
        draws_at_home = self.select_related('season').filter(hometeam=team, season=sid, date__lt=dt, hm_result='D').count()
        return draws_at_home

    def team_total_draws_away(self, team, sid, dt):
        draws_away = self.select_related('season').filter(awayteam=team, season=sid, date__lt=dt, aw_result='D').count()
        return draws_away

    # def team_total_losses(self, team, seazn, gw):
    #     qryset = self.filter(Q(hometeam=team, season=seazn, gameweek__lte=gw) | Q(awayteam=team, season=seazn, gameweek__lte=gw))
    #     total_losses = 0
    #     for g in qryset:
    #         if g.hometeam == team:
    #             if g.result == 'AWAY':
    #                 total_losses += 1
    #         elif g.awayteam == team:
    #             if g.result == 'HOME':
    #                 total_losses += 1
    #     return total_losses

    def team_total_losses_by_date(self, team, seazn, gw):
        gm = self.filter(Q(hometeam=team, season=seazn, gameweek=gw) | Q(awayteam=team, season=seazn, gameweek=gw))[0].id
        qryset = self.set_of_team_games_played_upto_game_date(team, gm, 'No')
        total_losses = 0
        for g in qryset:
            if g.hometeam == team:
                if g.result == 'AWAY':
                    total_losses += 1
            elif g.awayteam == team:
                if g.result == 'HOME':
                    total_losses += 1
        return total_losses

    def team_total_losses_by_date_optimized(self, team, sid, dt):
        losses_at_home = self.filter(Q(hometeam=team, season=sid, date__lte=dt, hm_result='L') | Q(awayteam=team, season=sid, date__lte=dt, aw_result='L')).count()
        return losses_at_home

    def team_total_losses_by_date_ex_current(self, team, seazn, gw):
        gm = self.filter(Q(hometeam=team, season=seazn, gameweek=gw) | Q(awayteam=team, season=seazn, gameweek=gw))[0].id
        qryset = self.set_of_team_games_played_before_game_date(team, gm, 'No')
        total_losses = 0
        for g in qryset:
            if g.hometeam == team:
                if g.result == 'AWAY':
                    total_losses += 1
            elif g.awayteam == team:
                if g.result == 'HOME':
                    total_losses += 1
        return total_losses

    # def team_total_draws(self, team, seazn, gw):
    #     qryset = self.filter(Q(hometeam=team, season=seazn, gameweek__lte=gw) | Q(awayteam=team, season=seazn, gameweek__lte=gw))
    #     total_draws = 0
    #     for g in qryset:
    #         if g.result == 'DRAW':
    #             total_draws += 1
    #     return total_draws

    def team_total_draws_by_date(self, team, seazn, gw):
        gm = self.filter(Q(hometeam=team, season=seazn, gameweek=gw) | Q(awayteam=team, season=seazn, gameweek=gw))[0].id
        qryset = self.set_of_team_games_played_upto_game_date(team, gm, 'No')
        total_draws = 0
        for g in qryset:
            if g.result == 'DRAW':
                total_draws += 1
        return total_draws

    def team_total_draws_by_date_optimized(self, team, sid, dt):
        draws_at_home = self.filter(Q(hometeam=team, season=sid, date__lte=dt, hm_result='D') | Q(awayteam=team, season=sid, date__lte=dt, aw_result='D')).count()
        return draws_at_home

    def team_total_draws_by_date_ex_current(self, team, seazn, gw):
        gm = self.filter(Q(hometeam=team, season=seazn, gameweek=gw) | Q(awayteam=team, season=seazn, gameweek=gw))[0].id
        qryset = self.set_of_team_games_played_before_game_date(team, gm, 'No')
        total_draws = 0
        for g in qryset:
            if g.result == 'DRAW':
                total_draws += 1
        return total_draws

    # def team_total_goals_scored(self, team, seazn, gw):
    #     qryset = self.filter(Q(hometeam=team, season=seazn, gameweek__lte=gw) | Q(awayteam=team, season=seazn, gameweek__lte=gw)).exclude(result__exact='').exclude(result__isnull=True)
    #     total_homegoals = 0
    #     total_awaygoals = 0
    #     for g in qryset:
    #         if g.hometeam == team:
    #             total_homegoals += g.homegoals
    #         elif g.awayteam == team:
    #             total_awaygoals += g.awaygoals
    #     return total_homegoals + total_awaygoals

    def team_total_goals_scored_by_date(self, team, seazn, gw):
        # qryset = self.filter(Q(hometeam=team, season=seazn, gameweek__lte=gw) | Q(awayteam=team, season=seazn, gameweek__lte=gw)).exclude(result__exact='').exclude(result__isnull=True)
        gm = self.filter(Q(hometeam=team, season=seazn, gameweek__lte=gw) | Q(awayteam=team, season=seazn, gameweek__lte=gw)).order_by('-date')[0].id
        qryset = self.set_of_team_games_played_upto_game_date(team, gm, 'No').exclude(result__exact='').exclude(result__isnull=True)
        total_homegoals = 0
        total_awaygoals = 0
        for g in qryset:
            if g.hometeam == team:
                total_homegoals += g.homegoals
            elif g.awayteam == team:
                total_awaygoals += g.awaygoals
        return total_homegoals + total_awaygoals

    def team_total_goals_scored_by_date_ex_current(self, team, seazn, gw):
        # qryset = self.filter(Q(hometeam=team, season=seazn, gameweek__lte=gw) | Q(awayteam=team, season=seazn, gameweek__lte=gw)).exclude(result__exact='').exclude(result__isnull=True)
        gm = self.filter(Q(hometeam=team, season=seazn, gameweek=gw) | Q(awayteam=team, season=seazn, gameweek=gw))[0].id
        qryset = self.set_of_team_games_played_before_game_date(team, gm, 'No').exclude(result__exact='').exclude(result__isnull=True)
        total_homegoals = 0
        total_awaygoals = 0
        for g in qryset:
            if g.hometeam == team:
                total_homegoals += g.homegoals
            elif g.awayteam == team:
                total_awaygoals += g.awaygoals
        return total_homegoals + total_awaygoals

    # def team_total_goals_conceded(self, team, seazn, gw):
    #     qryset = self.filter(Q(hometeam=team, season=seazn, gameweek__lte=gw) | Q(awayteam=team, season=seazn, gameweek__lte=gw)).exclude(result__exact='').exclude(result__isnull=True)
    #     total_homegoals = 0
    #     total_awaygoals = 0
    #     for g in qryset:
    #         if g.hometeam == team:
    #             total_homegoals += g.awaygoals
    #         elif g.awayteam == team:
    #             total_awaygoals += g.homegoals
    #     return total_homegoals + total_awaygoals

    def team_total_goals_conceded_by_date(self, team, seazn, gw):
        gm = self.filter(Q(hometeam=team, season=seazn, gameweek__lte=gw) | Q(awayteam=team, season=seazn, gameweek__lte=gw)).order_by('-date')[0].id
        qryset = self.set_of_team_games_played_upto_game_date(team, gm, 'No').exclude(result__exact='').exclude(result__isnull=True)
        total_homegoals = 0
        total_awaygoals = 0
        for g in qryset:
            if g.hometeam == team:
                total_homegoals += g.awaygoals
            elif g.awayteam == team:
                total_awaygoals += g.homegoals
        return total_homegoals + total_awaygoals

    def team_total_goals_conceded_by_date_ex_current(self, team, seazn, gw):
        gm = self.filter(Q(hometeam=team, season=seazn, gameweek=gw) | Q(awayteam=team, season=seazn, gameweek=gw))[0].id
        qryset = self.set_of_team_games_played_before_game_date(team, gm, 'No').exclude(result__exact='').exclude(result__isnull=True)
        total_homegoals = 0
        total_awaygoals = 0
        for g in qryset:
            if g.hometeam == team:
                total_homegoals += g.awaygoals
            elif g.awayteam == team:
                total_awaygoals += g.homegoals
        return total_homegoals + total_awaygoals

    # total points won/lost by a team at home
    # def team_total_home_points(self, team, sz, gmwk):
    #     qset = self.filter(hometeam=team, season=sz, gameweek__lt=gmwk).order_by('gameweek')
    #     points = 0.0
    #     if gmwk == 1:
    #             points = elosettings.STARTING_POINTS - self.get_previous_elo_by_date(team, sz, gmwk)
    #     else:
    #         for gm in qset:
    #             if gm.gameweek == 1:
    #                 points += gm.elo_rating_home - elosettings.STARTING_POINTS
    #             else:
    #                 points += gm.elo_rating_home - gm.elo_rating_home_previous_week
    #     return points

    # total points won/lost by a team at home
    def team_total_home_points_by_date(self, team, sz, gmwk):
        gmdate = self.filter(Q(hometeam=team, season=sz, gameweek=gmwk) | Q(awayteam=team, season=sz, gameweek=gmwk))[0].date
        qset = self.filter(hometeam=team, season=sz, date__lt=gmdate).order_by('date')
        points = 0.0
        for gm in qset:
                points += gm.elo_rating_home - gm.elo_rating_home_previous_week
        return points

    # total points won/lost by a team away
    # def team_total_away_points(self, team, sz, gmwk):
    #     qset = self.filter(awayteam=team, season=sz, gameweek__lt=gmwk).order_by('gameweek')
    #     points = 0.0
    #     if gmwk == 1:
    #             points = elosettings.STARTING_POINTS - self.get_previous_elo_by_date(team, sz, gmwk)
    #     else:
    #         for gm in qset:
    #             if gm.gameweek == 1:
    #                 points += gm.elo_rating_away - elosettings.STARTING_POINTS
    #             else:
    #                 points += gm.elo_rating_away - gm.elo_rating_away_previous_week
    #     return points

    def team_total_away_points_by_date(self, team, sz, gmwk):
        gmdate = self.filter(Q(hometeam=team, season=sz, gameweek=gmwk) | Q(awayteam=team, season=sz, gameweek=gmwk))[0].date
        qset = self.filter(awayteam=team, season=sz, date__lt=gmdate).order_by('date')
        points = 0.0
        for gm in qset:
                points += gm.elo_rating_away - gm.elo_rating_away_previous_week
        return points

    # total Regular Season (excluding playoffs) games played for the given season
    def total_season_games_played(self, sznn):
        qrset = self.filter(season=sznn, type='RS').exclude(homegoals__isnull=True).count()
        return qrset

    # total games that will be played for the given season
    def total_season_games(self, seasonn):
        # games_per_gameweek = self.filter(season=seasonn, gameweek=1).count()
        games_per_gameweek = Season.objects.get(id=seasonn).teamstotal / 2
        ttl_teams = games_per_gameweek * 2
        ttl_gameweeks = (ttl_teams - 1) * 2
        ttl_games = ttl_gameweeks * games_per_gameweek
        return ttl_games

    def total_season_home_wins(self, szn):
        ttl_home = self.filter(season=szn, result='HOME').count()
        return ttl_home

    def total_season_away_wins(self, szn):
        ttl_away = self.filter(season=szn, result='AWAY').count()
        return ttl_away

    def total_season_draws(self, szn):
        ttl_draws = self.filter(season=szn, result='DRAW').count()
        return ttl_draws

    def total_season_goals(self, seasonn):
        hmgoals = self.filter(season=seasonn).aggregate(Sum('homegoals'))
        awgoals = self.filter(season=seasonn).aggregate(Sum('awaygoals'))
        totl = hmgoals['homegoals__sum'] + awgoals['awaygoals__sum']
        return totl

    # Returns the number of games where both teams have scored in the provided season
    def season_both_teams_scored(self, seazn):
        totall = self.filter(season=seazn, homegoals__gt=0, awaygoals__gt=0).count()
        return totall

    # Returns the number of games that finished over1.5 for the given season
    def over_one_half(self, seasonn):
        qrset = self.filter(season=seasonn).exclude(result__exact='').exclude(result__isnull=True).annotate(diff=Sum(F('homegoals') + F('awaygoals')))
        cntr = 0
        for itemm in qrset:
            if itemm.diff > 1:
                cntr += 1
        return cntr

    def over_one_half_optimized(self, seasonn):
        cnt = (self
               .filter(season=seasonn)
               .exclude(result__exact='').exclude(result__isnull=True)
               .annotate(diff=Sum(F('homegoals') + F('awaygoals')))
               .filter(diff__gte=1.5)
               .count())
        return cnt

    def over_two_half(self, seasonn):
        qrset = self.filter(season=seasonn).exclude(result__exact='').exclude(result__isnull=True).annotate(diff=Sum(F('homegoals') + F('awaygoals')))
        cntr = 0
        for itemm in qrset:
            if itemm.diff > 2:
                cntr += 1
        return cntr

    def over_two_half_optimized(self, seasonn):
        cnt = (self
               .filter(season=seasonn)
               .exclude(result__exact='').exclude(result__isnull=True)
               .annotate(diff=Sum(F('homegoals') + F('awaygoals')))
               .filter(diff__gte=2.5)
               .count())
        return cnt

    def over_three_half(self, seasonn):
        qrset = self.filter(season=seasonn).exclude(result__exact='').exclude(result__isnull=True).annotate(diff=Sum(F('homegoals') + F('awaygoals')))
        cntr = 0
        for itemm in qrset:
            if itemm.diff > 3:
                cntr += 1
        return cntr

    def over_three_half_optimized(self, seasonn):
        cnt = (self
               .filter(season=seasonn)
               .exclude(result__exact='').exclude(result__isnull=True)
               .annotate(diff=Sum(F('homegoals') + F('awaygoals')))
               .filter(diff__gte=3.5)
               .count())
        return cnt

    # def team_total_cleansheets(self, team, seasonn, gwk):
    #     qrst = self.filter(Q(hometeam=team, season=seasonn, gameweek__lt=gwk) | Q(awayteam=team, season=seasonn, gameweek__lt=gwk))
    #     qrst_clean = qrst.exclude(result__exact='').exclude(result__isnull=True)
    #     cnt = 0
    #     for gm in qrst_clean:
    #         if gm.hometeam == team and gm.awaygoals == 0:
    #             cnt += 1
    #         if gm.awayteam == team and gm.homegoals == 0:
    #             cnt += 1
    #     return cnt

    def team_total_cleansheets_by_date(self, team, seasonn, dt):
        qrst = self.filter(Q(hometeam=team, season=seasonn, date__lt=dt) | Q(awayteam=team, season=seasonn, date__lt=dt))
        qrst_clean = qrst.exclude(result__exact='').exclude(result__isnull=True)
        cnt = 0
        for gm in qrst_clean:
            if gm.hometeam == team and gm.awaygoals == 0:
                cnt += 1
            if gm.awayteam == team and gm.homegoals == 0:
                cnt += 1
        return cnt

    # def team_total_failedtoscore(self, team, seasonn, gwk):
    #     qrst = self.filter(Q(hometeam=team, season=seasonn, gameweek__lt=gwk) | Q(awayteam=team, season=seasonn, gameweek__lt=gwk))
    #     qrst_clean = qrst.exclude(result__exact='').exclude(result__isnull=True)
    #     cnt = 0
    #     for gm in qrst_clean:
    #         if gm.hometeam == team and gm.homegoals == 0:
    #             cnt += 1
    #         if gm.awayteam == team and gm.awaygoals == 0:
    #             cnt += 1
    #     return cnt

    def team_total_failedtoscore_by_date(self, team, seasonn, dt):
        qrst = self.filter(Q(hometeam=team, season=seasonn, date__lt=dt) | Q(awayteam=team, season=seasonn, date__lt=dt))
        qrst_clean = qrst.exclude(result__exact='').exclude(result__isnull=True)
        cnt = 0
        for gm in qrst_clean:
            if gm.hometeam == team and gm.homegoals == 0:
                cnt += 1
            if gm.awayteam == team and gm.awaygoals == 0:
                cnt += 1
        return cnt

    # returns number of predictions for the given model and season. The choices are: elohist, elol6, gsrs
    def total_model_predictions(self, model, seasonidd, prediction):
        if seasonidd != 'all':
            if model == 'elohist':
                qs = self.filter(season=seasonidd, prediction_elohist=prediction).exclude(prediction_status_elohist__exact='').exclude(prediction_status_elohist__isnull=True)
            elif model == 'elol6':
                qs = self.filter(season=seasonidd, prediction_elol6=prediction).exclude(prediction_status_elol6__exact='').exclude(prediction_status_elol6__isnull=True)
            elif model == 'gsrs':
                qs = self.filter(season=seasonidd, prediction_gsrs=prediction).exclude(prediction_status_gsrs__exact='').exclude(prediction_status_gsrs__isnull=True)
            else:
                qs = ""
        else:
            if model == 'elohist':
                qs = self.filter(prediction_elohist=prediction).exclude(prediction_status_elohist__exact='').exclude(prediction_status_elohist__isnull=True)
            elif model == 'elol6':
                qs = self.filter(prediction_elol6=prediction).exclude(prediction_status_elol6__exact='').exclude(prediction_status_elol6__isnull=True)
            elif model == 'gsrs':
                qs = self.filter(prediction_gsrs=prediction).exclude(prediction_status_gsrs__exact='').exclude(prediction_status_gsrs__isnull=True)
            else:
                qs = ""
        total_predictions = qs.count()
        return total_predictions

    # same as above if the input variables come from the filters (hence the ifpost at the end)
    def total_model_predictions_ifpost(self, model, country, division, period, prediction):
        filtered_qs = Game.objects.all()
        if country == 'All' and division == 'All' and period == 'All':
            filtered_qs = Game.objects.all()
        elif country != 'All' and division == 'All' and period == 'All':
            filtered_qs = self.filter(season__league__country=country)
        elif country != 'All' and division != 'All' and period == 'All':
            filtered_qs = self.filter(season__league__country=country, season__league__league_name=division)
        elif country != 'All' and division != 'All' and period != 'All':
            qsitem = self.filter(season__league__country=country, season__league__league_name=division, season__end_date=period)[0]
            seasonidd = qsitem.season.id
            filtered_qs = self.filter(season=seasonidd)
        # in this case, period will be provided as year(i.e 2017) instead of an actual date
        elif country == 'All' and division == 'All' and period != 'All':
            filtered_qs = self.filter(season__end_date__year=period)

        if model == 'elohist':
            qs = filtered_qs.filter(prediction_elohist=prediction).exclude(prediction_status_elohist__exact='').exclude(prediction_status_elohist__isnull=True)
        elif model == 'elol6':
            qs = filtered_qs.filter(prediction_elol6=prediction).exclude(prediction_status_elol6__exact='').exclude(prediction_status_elol6__isnull=True)
        elif model == 'gsrs':
            qs = filtered_qs.filter(prediction_gsrs=prediction).exclude(prediction_status_gsrs__exact='').exclude(prediction_status_gsrs__isnull=True)
        else:
            qs = ""
        total_predictions = qs.count()
        return total_predictions

    # returns number of successful predictions for the given model and season. The choices are: elohist, elol6, gsrs
    def total_model_successful_predictions(self, model, seasonidd, prediction):
        if seasonidd != 'all':
            if model == 'elohist':
                qs = self.filter(season=seasonidd, prediction_elohist=prediction, prediction_status_elohist='Success')
            elif model == 'elol6':
                qs = self.filter(season=seasonidd, prediction_elol6=prediction, prediction_status_elol6='Success')
            elif model == 'gsrs':
                qs = self.filter(season=seasonidd, prediction_gsrs=prediction, prediction_status_gsrs='Success')
            else:
                qs = ""
        else:
            if model == 'elohist':
                qs = self.filter(prediction_elohist=prediction, prediction_status_elohist='Success')
            elif model == 'elol6':
                qs = self.filter(prediction_elol6=prediction, prediction_status_elol6='Success')
            elif model == 'gsrs':
                qs = self.filter(prediction_gsrs=prediction, prediction_status_gsrs='Success')
            else:
                qs = ""
        total_successful_predictions = qs.count()
        return total_successful_predictions

     # same as above if the input variables come from the filters (hence the ifpost at the end)
    def total_model_successful_predictions_ifpost(self, model, country, division, period, prediction):
        filtered_qs = Game.objects.all()
        if country == 'All' and division == 'All' and period == 'All':
            filtered_qs = Game.objects.all()
        elif country != 'All' and division == 'All' and period == 'All':
            filtered_qs = self.filter(season__league__country=country)
        elif country != 'All' and division != 'All' and period == 'All':
            filtered_qs = self.filter(season__league__country=country, season__league__league_name=division)
        elif country != 'All' and division != 'All' and period != 'All':
            qsitem = self.filter(season__league__country=country, season__league__league_name=division, season__end_date=period)[0]
            seasonidd = qsitem.season.id
            filtered_qs = self.filter(season=seasonidd)
        # in this case, period will be provided as year(i.e 2017) instead of an actual date
        elif country == 'All' and division == 'All' and period != 'All':
            filtered_qs = self.filter(season__end_date__year=period)

        if model == 'elohist':
            qs = filtered_qs.filter(prediction_elohist=prediction, prediction_status_elohist='Success')
        elif model == 'elol6':
            qs = filtered_qs.filter(prediction_elol6=prediction, prediction_status_elol6='Success')
        elif model == 'gsrs':
            qs = filtered_qs.filter(prediction_gsrs=prediction, prediction_status_gsrs='Success')
        else:
            qs = ""
        total_successful_predictions = qs.count()
        return total_successful_predictions

    # model winning streaks
    def total_model_streaks(self, model, seasonidd):
        if seasonidd != 'all':
            if model == 'elohist':
                qs = self.filter(season=seasonidd).exclude(prediction_status_elohist__exact='').exclude(prediction_status_elohist__isnull=True).values('prediction_status_elohist').order_by('date')
            elif model == 'elol6':
                qs = self.filter(season=seasonidd).exclude(prediction_status_elol6__exact='').exclude(prediction_status_elol6__isnull=True).values('prediction_status_elol6').order_by('date')
            elif model == 'gsrs':
                qs = self.filter(season=seasonidd).exclude(prediction_status_gsrs__exact='').exclude(prediction_status_gsrs__isnull=True).values('prediction_status_gsrs').order_by('date')
            else:
                qs = ""
        else:
            if model == 'elohist':
                qs = self.exclude(prediction_status_elohist__exact='').exclude(prediction_status_elohist__isnull=True).values('prediction_status_elohist').order_by('date')
            elif model == 'elol6':
                qs = self.exclude(prediction_status_elol6__exact='').exclude(prediction_status_elol6__isnull=True).values('prediction_status_elol6').order_by('date')
            elif model == 'gsrs':
                qs = self.exclude(prediction_status_gsrs__exact='').exclude(prediction_status_gsrs__isnull=True).values('prediction_status_gsrs').order_by('date')
            else:
                qs = ""
        results = []
        # qs gives me a list of dictionaries i.e [{'prediction_status_elohist': 'fail'}, {'prediction_status_elohist': 'fail'}] etc.
        # The loop below gives me a list of all the dict values for the given model i.e ['fail', 'fail', 'success'] etc.
        for val in qs:
            results.append(str(list(val.values())[0]))
        streaks = []
        streak_cnt = 0
        lstindex = -1
        for r in results:
            lstindex += 1
            if r == 'Success':
                streak_cnt += 1
            elif r == 'Fail' and streak_cnt > 0:
                streaks.append(streak_cnt)
                streak_cnt = 0

            if lstindex == len(results) - 1 and streak_cnt > 0:
                streaks.append(streak_cnt)
        # checks if the streaks is empty otherwise gives the maximum
        if not streaks:
            output = 'NA'
        else:
            output = max(streaks)
        return output

    # same as above if the input variables come from the filters (hence the ifpost at the end)
    def total_model_streaks_ifpost(self, model, country, division, period):
        filtered_qs = Game.objects.all()
        if country == 'All' and division == 'All' and period == 'All':
            filtered_qs = Game.objects.all()
        elif country != 'All' and division == 'All' and period == 'All':
            filtered_qs = self.filter(season__league__country=country)
        elif country != 'All' and division != 'All' and period == 'All':
            filtered_qs = self.filter(season__league__country=country, season__league__league_name=division)
        elif country != 'All' and division != 'All' and period != 'All':
            qsitem = self.filter(season__league__country=country, season__league__league_name=division, season__end_date=period)[0]
            seasonidd = qsitem.season.id
            filtered_qs = self.filter(season=seasonidd)
        # in this case, period will be provided as year(i.e 2017) instead of an actual date
        elif country == 'All' and division == 'All' and period != 'All':
            filtered_qs = self.filter(season__end_date__year=period)

        if model == 'elohist':
            qs = filtered_qs .exclude(prediction_status_elohist__exact='').exclude(prediction_status_elohist__isnull=True).values('prediction_status_elohist').order_by('date')
        elif model == 'elol6':
            qs = filtered_qs .exclude(prediction_status_elol6__exact='').exclude(prediction_status_elol6__isnull=True).values('prediction_status_elol6').order_by('date')
        elif model == 'gsrs':
            qs = filtered_qs .exclude(prediction_status_gsrs__exact='').exclude(prediction_status_gsrs__isnull=True).values('prediction_status_gsrs').order_by('date')
        else:
            qs = ""
        results = []
        # qs gives me a list of dictionaries i.e [{'prediction_status_elohist': 'fail'}, {'prediction_status_elohist': 'fail'}] etc.
        # The loop below gives me a list of all the dict values for the given model i.e ['fail', 'fail', 'success'] etc.
        for val in qs:
            results.append(str(list(val.values())[0]))
        streaks = []
        streak_cnt = 0
        lstindex = -1
        for r in results:
            lstindex += 1
            if r == 'Success':
                streak_cnt += 1
            elif r == 'Fail' and streak_cnt > 0:
                streaks.append(streak_cnt)
                streak_cnt = 0

            if lstindex == len(results) - 1 and streak_cnt > 0:
                streaks.append(streak_cnt)
        # checks if the streaks is empty otherwise gives the maximum
        if not streaks:
            output = 'NA'
        else:
            output = max(streaks)
        return output

    # model losing streaks
    def total_model_losing_streaks(self, model, seasonidd):
        if seasonidd != 'all':
            if model == 'elohist':
                qs = self.filter(season=seasonidd).exclude(prediction_status_elohist__exact='').exclude(prediction_status_elohist__isnull=True).values('prediction_status_elohist').order_by('date')
            elif model == 'elol6':
                qs = self.filter(season=seasonidd).exclude(prediction_status_elol6__exact='').exclude(prediction_status_elol6__isnull=True).values('prediction_status_elol6').order_by('date')
            elif model == 'gsrs':
                qs = self.filter(season=seasonidd).exclude(prediction_status_gsrs__exact='').exclude(prediction_status_gsrs__isnull=True).values('prediction_status_gsrs').order_by('date')
            else:
                qs = ""
        else:
            if model == 'elohist':
                qs = self.exclude(prediction_status_elohist__exact='').exclude(prediction_status_elohist__isnull=True).values('prediction_status_elohist').order_by('date')
            elif model == 'elol6':
                qs = self.exclude(prediction_status_elol6__exact='').exclude(prediction_status_elol6__isnull=True).values('prediction_status_elol6').order_by('date')
            elif model == 'gsrs':
                qs = self.exclude(prediction_status_gsrs__exact='').exclude(prediction_status_gsrs__isnull=True).values('prediction_status_gsrs').order_by('date')
            else:
                qs = ""
        results = []
        # qs gives me a list of dictionaries i.e [{'prediction_status_elohist': 'fail'}, {'prediction_status_elohist': 'fail'}] etc.
        # The loop below gives me a list of all the dict values for the given model i.e ['fail', 'fail', 'success'] etc.
        for val in qs:
            results.append(str(list(val.values())[0]))
        streaks = []
        streak_cnt = 0
        lstindex = -1
        for r in results:
            lstindex += 1
            if r == 'Fail':
                streak_cnt += 1
            elif r == 'Success' and streak_cnt > 0:
                streaks.append(streak_cnt)
                streak_cnt = 0

            if lstindex == len(results) - 1 and streak_cnt > 0:
                streaks.append(streak_cnt)
        # checks if the streaks is empty otherwise gives the maximum
        if not streaks:
            output = 'NA'
        else:
            output = max(streaks)
        return output

    # same as above if the input variables come from the filters (hence the ifpost at the end)
    def total_model_losing_streaks_ifpost(self, model, country, division, period):
        filtered_qs = Game.objects.all()
        if country == 'All' and division == 'All' and period == 'All':
            filtered_qs = Game.objects.all()
        elif country != 'All' and division == 'All' and period == 'All':
            filtered_qs = self.filter(season__league__country=country)
        elif country != 'All' and division != 'All' and period == 'All':
            filtered_qs = self.filter(season__league__country=country, season__league__league_name=division)
        elif country != 'All' and division != 'All' and period != 'All':
            qsitem = self.filter(season__league__country=country, season__league__league_name=division, season__end_date=period)[0]
            seasonidd = qsitem.season.id
            filtered_qs = self.filter(season=seasonidd)
        # in this case, period will be provided as year(i.e 2017) instead of an actual date
        elif country == 'All' and division == 'All' and period != 'All':
            filtered_qs = self.filter(season__end_date__year=period)

        if model == 'elohist':
            qs = filtered_qs .exclude(prediction_status_elohist__exact='').exclude(prediction_status_elohist__isnull=True).values('prediction_status_elohist').order_by('date')
        elif model == 'elol6':
            qs = filtered_qs .exclude(prediction_status_elol6__exact='').exclude(prediction_status_elol6__isnull=True).values('prediction_status_elol6').order_by('date')
        elif model == 'gsrs':
            qs = filtered_qs .exclude(prediction_status_gsrs__exact='').exclude(prediction_status_gsrs__isnull=True).values('prediction_status_gsrs').order_by('date')
        else:
            qs = ""
        results = []
        # qs gives me a list of dictionaries i.e [{'prediction_status_elohist': 'fail'}, {'prediction_status_elohist': 'fail'}] etc.
        # The loop below gives me a list of all the dict values for the given model i.e ['fail', 'fail', 'success'] etc.
        for val in qs:
            results.append(str(list(val.values())[0]))
        streaks = []
        streak_cnt = 0
        lstindex = -1
        for r in results:
            lstindex += 1
            if r == 'Fail':
                streak_cnt += 1
            elif r == 'Success' and streak_cnt > 0:
                streaks.append(streak_cnt)
                streak_cnt = 0

            if lstindex == len(results) - 1 and streak_cnt > 0:
                streaks.append(streak_cnt)
        # checks if the streaks is empty otherwise gives the maximum
        if not streaks:
            output = 'NA'
        else:
            output = max(streaks)
        return output

    def model_strike_rate(self, model, seasonid, prediction):
        successful_preds = self.total_model_successful_predictions(model, seasonid, prediction)
        total_preds = self.total_model_predictions(model, seasonid, prediction)
        if total_preds == 0:
            strikerate = 0
        else:
            strikerate = (float(successful_preds) / total_preds) * 100
        return strikerate

    # model strike rate if the request comes from the dashboard filters (haven't created one without filters yet)
    def model_strike_rate_ifpost(self, model, country, division, period, prediction):
        successful_preds = self.total_model_successful_predictions_ifpost(model, country, division, period, prediction)
        total_preds = self.total_model_predictions_ifpost(model, country, division, period, prediction)
        if total_preds == 0:
            strikerate = 0
        else:
            strikerate = (float(successful_preds) / total_preds) * 100
        return strikerate

    # returns a list of leagues for the selected country, division and period
    def leagues_list(self, country, division, period):
        lglist = []
        lglist_final = []
        filtered_qs = Game.objects.all().values('season_id').distinct()
        if country == 'All' and division == 'All' and period == 'All':
            filtered_qs = Game.objects.all().values('season_id').distinct()
        elif country != 'All' and division == 'All' and period == 'All':
            filtered_qs = self.filter(season__league__country=country).values('season_id').distinct()
        elif country != 'All' and division != 'All' and period == 'All':
            filtered_qs = self.filter(season__league__country=country, season__league__league_name=division).values('season_id').distinct()
        elif country != 'All' and division != 'All' and period != 'All':
            qsitem = self.filter(season__league__country=country, season__league__league_name=division, season__end_date=period)[0]
            seasonidd = qsitem.season.id
            filtered_qs = self.filter(season=seasonidd).values('season_id').distinct()
        # in this case, period will be provided as year(i.e 2017) instead of an actual date
        elif country == 'All' and division == 'All' and period != 'All':
            filtered_qs = self.filter(season__end_date__year=period).values('season_id').distinct()

        for itemm in filtered_qs:
            lglist.append(str(itemm.get('season_id')))

        for lstitem in lglist:
            season_object = Season.objects.get(id=lstitem)
            lglist_final.append(str(season_object))

        return lglist_final

    # returns a list of strike rates for the given selections
    def strike_rate_list(self, model, country, division, period, prediction):
        srlist = []
        seasonlist = []
        filtered_qs = Game.objects.all().values('season_id').distinct()
        if country == 'All' and division == 'All' and period == 'All':
            filtered_qs = Game.objects.all().values('season_id').distinct()
        elif country != 'All' and division == 'All' and period == 'All':
            filtered_qs = self.filter(season__league__country=country).values('season_id').distinct()
        elif country != 'All' and division != 'All' and period == 'All':
            filtered_qs = self.filter(season__league__country=country, season__league__league_name=division).values('season_id').distinct()
        elif country != 'All' and division != 'All' and period != 'All':
            qsitem = self.filter(season__league__country=country, season__league__league_name=division, season__end_date=period)[0]
            seasonidd = qsitem.season.id
            filtered_qs = self.filter(season=seasonidd).values('season_id').distinct()
        # in this case, period will be provided as year(i.e 2017) instead of an actual date
        elif country == 'All' and division == 'All' and period != 'All':
            filtered_qs = self.filter(season__end_date__year=period).values('season_id').distinct()

        for val in filtered_qs:
            seasonlist.append(val.get('season_id'))

        for lstitem in seasonlist:
            srlist.append(self.model_strike_rate(model, lstitem, prediction))
        return srlist

    def total_model_strike_rate_for_short_name(self, model, short_name, period, prediction):
        filtered_qs = Game.objects.all()
        qs_successful = ''
        if period == 'All':
            filtered_qs = Game.objects.filter(season__league__short_name=short_name)
        elif period != 'All':
            filtered_qs = Game.objects.filter(season__league__short_name=short_name, season__end_date__year=period)

        if model == 'elohist':
            qs_total = filtered_qs.filter(prediction_elohist=prediction).exclude(prediction_status_elohist__exact='').exclude(prediction_status_elohist__isnull=True)
            qs_successful = filtered_qs.filter(prediction_elohist=prediction, prediction_status_elohist='Success')
        elif model == 'elol6':
            qs_total = filtered_qs.filter(prediction_elol6=prediction).exclude(prediction_status_elol6__exact='').exclude(prediction_status_elol6__isnull=True)
            qs_successful = filtered_qs.filter(prediction_elol6=prediction, prediction_status_elol6='Success')
        elif model == 'gsrs':
            qs_total = filtered_qs.filter(prediction_gsrs=prediction).exclude(prediction_status_gsrs__exact='').exclude(prediction_status_gsrs__isnull=True)
            qs_successful = filtered_qs.filter(prediction_gsrs=prediction, prediction_status_gsrs='Success')
        else:
            qs_total = ""
        total_predictions = qs_total.count()
        successful_predictions = qs_successful.count()
        if total_predictions == 0:
            strikerate = 0
        else:
            strikerate = round((float(successful_predictions) / total_predictions) * 100)
        return strikerate

    # Don't worry about gameweek being less than 7 as this is only used by strike_rate_list_pergmwk_for_canvas which filters out the gameweeks less than 7 in the
    # qrst parameter
    def total_model_strike_rate_for_gameweek(self, qrst, gamewk, model):
        if model == 'elohist':
            qs_total = qrst.filter(gameweek=gamewk).exclude(prediction_status_elohist__exact='').exclude(prediction_status_elohist__isnull=True)
            qs_successful = qrst.filter(gameweek=gamewk, prediction_status_elohist='Success')
        elif model == 'elol6':
            qs_total = qrst.filter(gameweek=gamewk).exclude(prediction_status_elol6__exact='').exclude(prediction_status_elol6__isnull=True)
            qs_successful = qrst.filter(gameweek=gamewk, prediction_status_elol6='Success')
        elif model == 'gsrs':
            qs_total = qrst.filter(gameweek=gamewk).exclude(prediction_status_gsrs__exact='').exclude(prediction_status_gsrs__isnull=True)
            qs_successful = qrst.filter(gameweek=gamewk, prediction_status_gsrs='Success')
        else:
            qs_total = ""
            qs_successful = ""
        total_predictions = qs_total.count()
        successful_predictions = qs_successful.count()
        if total_predictions == 0:
            strikerate = 0
        else:
            strikerate = round((float(successful_predictions) / total_predictions) * 100)
        return strikerate

    # returns a list of dictionaries containing league short name and strike rate (used for canvas charts)
    def strike_rate_list_for_canvas(self, model, country, division, period, prediction):
        lglist = []
        srlist = []
        filtered_qs = Game.objects.all()
        if country == 'All' and division == 'All' and period == 'All':
            filtered_qs = Game.objects.all()
        elif country != 'All' and division == 'All' and period == 'All':
            filtered_qs = self.filter(season__league__country=country)
        elif country != 'All' and division != 'All' and period == 'All':
            filtered_qs = self.filter(season__league__country=country, season__league__league_name=division)
        elif country != 'All' and division != 'All' and period != 'All':
            qsitem = self.filter(season__league__country=country, season__league__league_name=division, season__end_date__year=period)[0]
            seasonidd = qsitem.season.id
            filtered_qs = self.filter(season=seasonidd)
        elif country == 'All' and division == 'All' and period != 'All':
            filtered_qs = self.filter(season__end_date__year=period)
        # list of distinct league short names
        filtered_qs_vals = list(set(filtered_qs.values_list('season__league', flat=True)))
        for itm in filtered_qs_vals:
            lglist.append(str(itm))
        lglist.sort()

        for lg in lglist:
            srlist.append({str('label'): lg, str('y'): self.total_model_strike_rate_for_short_name(model, lg, period, prediction)})
        return srlist

    # returns a list of dictionaries containing gameweek and strike rate (used for canvas charts)
    def strike_rate_list_pergmwk_for_canvas(self, model, country, division, period):
        gwlist = []
        srlist = []
        filtered_qs = Game.objects.all()
        # since the list is showing strike rate per gameweek i'm excluding the null or empty values of any of the models
        # which I don't need to do in the previous functions for canvas
        if country == 'All' and division == 'All' and period == 'All':
            filtered_qs = Game.objects.filter(gameweek__gte=7).exclude(prediction_status_elohist__exact='').exclude(prediction_status_elohist__isnull=True)
        elif country != 'All' and division == 'All' and period == 'All':
            filtered_qs = self.filter(season__league__country=country, gameweek__gte=7).exclude(prediction_status_elohist__exact='').exclude(prediction_status_elohist__isnull=True)
        elif country != 'All' and division != 'All' and period == 'All':
            filtered_qs = self.filter(season__league__country=country, season__league__league_name=division, gameweek__gte=7).exclude(prediction_status_elohist__exact='').exclude(prediction_status_elohist__isnull=True)
        elif country != 'All' and division != 'All' and period != 'All':
            qsitem = self.filter(season__league__country=country, season__league__league_name=division, season__end_date__year=period)[0]
            seasonidd = qsitem.season.id
            filtered_qs = self.filter(season=seasonidd, gameweek__gte=7).exclude(prediction_status_elohist__exact='').exclude(prediction_status_elohist__isnull=True)
        elif country == 'All' and division == 'All' and period != 'All':
            filtered_qs = self.filter(season__end_date__year=period, gameweek__gte=7).exclude(prediction_status_elohist__exact='').exclude(prediction_status_elohist__isnull=True)
        # list of distinct gameweeks. When using set instead of list you ensure only distinct items will be in the list. So I use a set that's
        # converted back to a list hence list(set())
        filtered_qs_vals = list(set(filtered_qs.values_list('gameweek', flat=True)))
        for itm in filtered_qs_vals:
            gwlist.append(int(itm))
        gwlist.sort()

        for gw in gwlist:
            srlist.append({str('x'): gw, str('y'): self.total_model_strike_rate_for_gameweek(filtered_qs, gw, model)})
        return srlist

    # returns a list of dictionaries with the distribution of strike rate for the same number of gameweeks (i.e if user chooses 'All', 'All', 'All
    # they will get the same number of gameweeks as they would if they chose a country, league and season
    def strike_rate_distribution_for_canvas(self, model, country, division, period):
        gwlist = []
        srlist = []
        zero_to_thirty = 0
        thirty_to_fifty = 0
        fifty_to_seventy = 0
        seventy_to_ninenty = 0
        ninenty_and_above = 0
        filtered_qs = Game.objects.all()
        # since the list is showing strike rate per gameweek i'm excluding the null or empty values of any of the models
        # which I don't need to do in the previous functions for canvas
        if country == 'All' and division == 'All' and period == 'All':
            filtered_qs = Game.objects.filter(gameweek__gte=7).exclude(prediction_status_elohist__exact='').exclude(prediction_status_elohist__isnull=True)
        elif country != 'All' and division == 'All' and period == 'All':
            filtered_qs = self.filter(season__league__country=country, gameweek__gte=7).exclude(prediction_status_elohist__exact='').exclude(prediction_status_elohist__isnull=True)
        elif country != 'All' and division != 'All' and period == 'All':
            filtered_qs = self.filter(season__league__country=country, season__league__league_name=division, gameweek__gte=7).exclude(prediction_status_elohist__exact='').exclude(prediction_status_elohist__isnull=True)
        elif country != 'All' and division != 'All' and period != 'All':
            qsitem = self.filter(season__league__country=country, season__league__league_name=division, season__end_date__year=period)[0]
            seasonidd = qsitem.season.id
            filtered_qs = self.filter(season=seasonidd, gameweek__gte=7).exclude(prediction_status_elohist__exact='').exclude(prediction_status_elohist__isnull=True)
        elif country == 'All' and division == 'All' and period != 'All':
            filtered_qs = self.filter(season__end_date__year=period, gameweek__gte=7).exclude(prediction_status_elohist__exact='').exclude(prediction_status_elohist__isnull=True)
        # list of distinct gameweeks. When using set instead of list you ensure only distinct items will be in the list. So I use a set that's
        # converted back to a list hence list(set())
        filtered_qs_vals = list(set(filtered_qs.values_list('gameweek', flat=True)))
        for itm in filtered_qs_vals:
            gwlist.append(int(itm))
        gwlist.sort()
        for gw in gwlist:
            x = self.total_model_strike_rate_for_gameweek(filtered_qs, gw, model)
            if 0 <= x <= 29.49:
                zero_to_thirty += 1
            elif 29.50 <= x <= 49.49:
                thirty_to_fifty += 1
            elif 49.50 <= x <= 69.49:
                fifty_to_seventy += 1
            elif 69.50 <= x <= 89.49:
                seventy_to_ninenty += 1
            elif 89.50 <= x:
                ninenty_and_above += 1

        srlist.append({str('label'): '0% to 29%', str('y'): zero_to_thirty})
        srlist.append({str('label'): '30% to 49%', str('y'): thirty_to_fifty})
        srlist.append({str('label'): '50% to 69%', str('y'): fifty_to_seventy})
        srlist.append({str('label'): '70% to 89%', str('y'): seventy_to_ninenty})
        srlist.append({str('label'): '90% & above', str('y'): ninenty_and_above})
        return srlist

    # returns a list of dictionaries with the distribution of strike rate for as many gameweeks there are in the underlying seasons of filtered_qs
    def strike_rate_distribution_for_season(self, model, country, division, period):
        gwlist = []
        srlist = []
        zero_to_thirty = 0
        thirty_to_fifty = 0
        fifty_to_seventy = 0
        seventy_to_ninenty = 0
        ninenty_and_above = 0
        filtered_qs = Game.objects.all()
        # since the list is showing strike rate per gameweek i'm excluding the null or empty values of any of the models
        # which I don't need to do in the previous functions for canvas
        if country == 'All' and division == 'All' and period == 'All':
            filtered_qs = Game.objects.filter(gameweek__gte=7).exclude(prediction_status_elohist__exact='').exclude(prediction_status_elohist__isnull=True)
        elif country != 'All' and division == 'All' and period == 'All':
            filtered_qs = self.filter(season__league__country=country, gameweek__gte=7).exclude(prediction_status_elohist__exact='').exclude(prediction_status_elohist__isnull=True)
        elif country != 'All' and division != 'All' and period == 'All':
            filtered_qs = self.filter(season__league__country=country, season__league__league_name=division, gameweek__gte=7).exclude(prediction_status_elohist__exact='').exclude(prediction_status_elohist__isnull=True)
        elif country != 'All' and division != 'All' and period != 'All':
            qsitem = self.filter(season__league__country=country, season__league__league_name=division, season__end_date__year=period)[0]
            seasonidd = qsitem.season.id
            filtered_qs = self.filter(season=seasonidd, gameweek__gte=7).exclude(prediction_status_elohist__exact='').exclude(prediction_status_elohist__isnull=True)
        elif country == 'All' and division == 'All' and period != 'All':
            filtered_qs = self.filter(season__end_date__year=period, gameweek__gte=7).exclude(prediction_status_elohist__exact='').exclude(prediction_status_elohist__isnull=True)
        # list of distinct seasons. When using set instead of list you ensure only distinct items will be in the list. So I use a set that's
        # converted back to a list hence list(set())
        distinct_seasons = list(set(filtered_qs.values_list('season__id', flat=True)))
        for s in distinct_seasons:
            current_set = filtered_qs.filter(season__id=s)
            distinct_gameweeks = list(set(current_set.values_list('gameweek', flat=True)))
            distinct_gameweeks.sort()
            for gw in distinct_gameweeks:
                x = self.total_model_strike_rate_for_gameweek(current_set, gw, model)
                if 0 <= x <= 30.44:
                    zero_to_thirty += 1
                elif 30.45 <= x <= 50.44:
                    thirty_to_fifty += 1
                elif 50.45 <= x <= 70.44:
                    fifty_to_seventy += 1
                elif 70.45 <= x <= 90.44:
                    seventy_to_ninenty += 1
                elif 90.45 <= x:
                    ninenty_and_above += 1
        srlist.append({str('label'): '0% - 30%', str('y'): zero_to_thirty})
        srlist.append({str('label'): '31% - 50%', str('y'): thirty_to_fifty})
        srlist.append({str('label'): '51% - 70%', str('y'): fifty_to_seventy})
        srlist.append({str('label'): '71% - 90%', str('y'): seventy_to_ninenty})
        srlist.append({str('label'): '91% & above', str('y'): ninenty_and_above})
        return srlist

    # returns the strike rate for the selected season. The strike rate represents all the successful predictions divided
    # by all the predictions made for all models
    def total_season_strike_rate(self, seasonid):
        qs = self.filter(season__id=seasonid).exclude(prediction_status_elohist__exact='').exclude(prediction_status_elohist__isnull=True)
        total_preds = qs.count()
        total_preds_final = float(total_preds) * 3
        elohist = qs.filter(prediction_status_elohist='Success').count()
        elol6 = qs.filter(prediction_status_elol6='Success').count()
        gsrs = qs.filter(prediction_status_gsrs='Success').count()
        successful_preds = elohist + elol6 + gsrs

        if total_preds == 0:
            strikerate = 0
        else:
            strikerate = (float(successful_preds) / total_preds_final) * 100
        return strikerate

    # returns a list of seasonid/ total strikerate dictionaries for the selected year, sorted by strike rate, i.e
    # [{'id': 1, 'strike_rate': 75}, {'id': 3, 'strike_rate': 48}, {'id': 2, 'strike_rate': 38}]
    def rank_seasons_by_strike_rate(self, year):
        allseasons = Season.objects.filter(end_date__year=year).values_list('id', flat=True)
        strike_rates_list = []
        for season in allseasons:
            strike_rates_list.append({'id': season, 'strike_rate': self.total_season_strike_rate(season)})
        sorted_list = sorted(strike_rates_list, key=itemgetter('strike_rate'), reverse=True)
        return sorted_list

    # returns a list of dicts containing seasonid, country, country code, league name, strike rate for all seasons for
    # the given year, model and prediction
    def rank_seasons_by_strike_rate_for_model(self, year, model, prediction):
        # allseasons = Season.objects.filter(end_date__year=year).values_list('id', flat=True)
        allseasons = Season.objects.filter(end_date__year=year).values_list('id', flat=True)
        strike_rates_list = []
        for season in allseasons:
            strike_rates_list.append({
                'id': season,
                # 'strike_rate': self.model_strike_rate(model, season, prediction),
                # 'country': Season.objects.get(id=season).league.country,
                # 'country_code': Season.objects.get(id=season).league.country_code,
                # 'league_name': Season.objects.get(id=season).league.league_name
                'strike_rate': self.model_strike_rate(model, season, prediction),
                'country': Season.objects.select_related('league').get(id=season).league.country,
                'country_code': Season.objects.select_related('league').get(id=season).league.country_code,
                'league_name': Season.objects.select_related('league').get(id=season).league.league_name
            })
        sorted_list = sorted(strike_rates_list, key=itemgetter('strike_rate'), reverse=True)
        return sorted_list


class Game(models.Model):
    ok = 'OK'
    postponed = 'PST'
    cancelled = 'CNC'
    GAME_STATUS_CHOICES = (
        (ok, 'OK'),
        (postponed, 'Postponed'),
        (cancelled, 'Cancelled'),
    )
    FLAG_CHOICES = (
        ('No flag', 'No flag'),
        ('Refresh', 'Refresh'),
    )

    TYPE_CHOICES = (
        ('RS', 'RS'),
        ('PO', 'PO'),
    )

    date = models.DateField()
    gameweek = models.PositiveIntegerField()
    fixture_sm = models.ForeignKey('FixtureSM', blank=True, null=True)
    season = models.ForeignKey('Season')
    game_status = models.CharField(max_length=10, choices=GAME_STATUS_CHOICES, default=ok,)
    flag = models.CharField(max_length=10, choices=FLAG_CHOICES, default='No flag',)
    type = models.CharField(max_length=5, choices=TYPE_CHOICES, default='RS', )
    hometeam = models.ForeignKey(Team, related_name='hometeam')
    awayteam = models.ForeignKey(Team, related_name='awayteam')
    homegoals = models.IntegerField(null=True, blank=True)
    awaygoals = models.IntegerField(null=True, blank=True)
    result = models.CharField(max_length=5, null=True, blank=True)
    hm_result = models.CharField(max_length=5, null=True, blank=True)
    aw_result = models.CharField(max_length=5, null=True, blank=True)
    hm_points = models.IntegerField(null=True, blank=True)
    aw_points = models.IntegerField(null=True, blank=True)
    elo_rating_home = models.FloatField(null=True, blank=True)
    elo_rating_home_previous_week = models.FloatField(null=True, blank=True)
    elo_rating_home_6_weeks_ago = models.FloatField(null=True, blank=True)
    elo_rating_away = models.FloatField(null=True, blank=True)
    elo_rating_away_previous_week = models.FloatField(null=True, blank=True)
    elo_rating_away_6_weeks_ago = models.FloatField(null=True, blank=True)
    rdiff = models.FloatField(null=True, blank=True)
    goaldiff_hm = models.IntegerField(null=True, blank=True)
    goaldiff_aw = models.IntegerField(null=True, blank=True)
    prediction_elohist = models.CharField(max_length=80, null=True, blank=True)
    prediction_status_elohist = models.CharField(max_length=80, null=True, blank=True)
    prediction_elol6 = models.CharField(max_length=80, null=True, blank=True)
    prediction_status_elol6 = models.CharField(max_length=80, null=True, blank=True)
    prediction_gsrs = models.CharField(max_length=80, null=True, blank=True)
    prediction_status_gsrs = models.CharField(max_length=80, null=True, blank=True)
    objects = GameManager()

    def get_k_factor(self):
        k = elosettings.ELO_K
        scaling = {10: 2.99, 9: 2.88, 8: 2.77, 7: 2.64, 6: 2.49, 5: 2.32, 4: 2.11, 3: 1.85, 2: 1.51, 1: 1.00}
        if self.homegoals >= 0:
            goaldiff = abs(self.homegoals - self.awaygoals)
            if goaldiff == 0:
                k += 0
            elif goaldiff > 10:
                k += 2.99
            else:
                k += scaling[goaldiff]
            return k
        else:
            k = ''
            return k

    def home_sa(self):
        # this means if self.homegoals is not empty or null
        if self.homegoals >= 0:
            goaldiff = self.homegoals - self.awaygoals
            if goaldiff > 0:
                actual_score = 1
            elif goaldiff == 0:
                actual_score = 0.5
            elif goaldiff < 0:
                actual_score = 0
            else:
                actual_score = 'na'
            return actual_score
        else:
            return ''

    def away_sa(self):
        # this means if self.awaygoals is not empty or null
        if self.awaygoals >= 0:
            goaldiff = self.awaygoals - self.homegoals
            if goaldiff > 0:
                actual_score = 1
            elif goaldiff == 0:
                actual_score = 0.5
            elif goaldiff < 0:
                actual_score = 0
            else:
                actual_score = 'na'
            return actual_score
        else:
            return ''

    def home_se(self):
        away_r_old = self._default_manager.get_previous_elo_by_actual_date_for_initial(tm=self.awayteam, seasn=self.season, dt=self.date)
        home_r_old = self._default_manager.get_previous_elo_by_actual_date_for_initial(tm=self.hometeam, seasn=self.season, dt=self.date)
        home_ground_adv = self._default_manager.modified_hga_from_date(teamm=self.hometeam, seasonn=self.season, dt=self.date)
        home_sa = 1 / (1 + 10 ** ((away_r_old - home_r_old - home_ground_adv) / float(elosettings.ELO_S)))
        return home_sa

    def away_se(self):
        hmscore = self.home_se()
        away_sa = 1 - hmscore
        return away_sa

    def r_new_home(self):
        if self.homegoals >= 0:
            r_old = self._default_manager.get_previous_elo_by_actual_date_for_initial(tm=self.hometeam, seasn=self.season, dt=self.date)
            k = self.get_k_factor()
            sa = self.home_sa()
            se = self.home_se()
            rating = r_old + k * (sa - se)
            return rating
        else:
            gmwkk = self._default_manager.last_gameweek_played(self.hometeam, self.season.id)
            last_gwk_qrset = Game.objects.filter(Q(season=self.season.id, gameweek=gmwkk, hometeam=self.hometeam) | Q(season=self.season.id, gameweek=gmwkk, awayteam=self.hometeam))
            tms = last_gwk_qrset.get(Q(hometeam=self.hometeam) | Q(awayteam=self.hometeam))
            if self.hometeam == tms.hometeam:
                rating = tms.elo_rating_home
            else:
                rating = tms.elo_rating_away
            return rating

    def r_new_away(self):
        if self.awaygoals >= 0:
            r_old = self._default_manager.get_previous_elo_by_actual_date_for_initial(tm=self.awayteam, seasn=self.season, dt=self.date)
            k = self.get_k_factor()
            sa = self.away_sa()
            se = self.away_se()
            rating = r_old + k * (sa - se)
            return rating
        else:
            gmwkk = self._default_manager.last_gameweek_played(self.awayteam, self.season.id)
            last_gwk_qrset = Game.objects.filter(Q(season=self.season.id, gameweek=gmwkk, hometeam=self.awayteam) | Q(season=self.season.id, gameweek=gmwkk, awayteam=self.awayteam))
            tms = last_gwk_qrset.get(Q(hometeam=self.awayteam) | Q(awayteam=self.awayteam))
            if self.awayteam == tms.awayteam:
                rating = tms.elo_rating_away
            else:
                rating = tms.elo_rating_home
            return rating

    # def elo_hist_prediction_status(self):
    #     if self.homegoals >= 0:
    #         prediction = self._default_manager.elo_hist_prediction_by_id(self.id)
    #         actual_result = self.result
    #         if prediction == 'Not enough games to calculate prediction (the model needs at least 6 gameweeks)':
    #             out = ''
    #         elif prediction == actual_result:
    #             out = 'Success'
    #         else:
    #             out = 'Fail'
    #         return out
    #     return ''

    def elo_hist_prediction_status(self):
        if self.homegoals >= 0:
            prediction = self._default_manager.elo_hist_prediction_by_id(self.id)
            actual_result = self.result
            if prediction == 'Not enough games to calculate prediction (the model needs at least 6 gameweeks)':
                out = ''
            elif prediction == actual_result:
                out = 'Success'
            else:
                out = 'Fail'
            return out
        return ''

    def elo_l6_prediction_status(self):
        if self.homegoals >= 0:
            prediction = self._default_manager.elo_l6_prediction_by_id(self.id)
            actual_result = self.result
            if prediction == 'Not enough games to calculate prediction (the model needs at least 6 gameweeks)':
                out = ''
            elif prediction == actual_result:
                out = 'Success'
            else:
                out = 'Fail'
            return out
        return ''

    def gsrs_prediction_status(self):
        if self.homegoals >= 0:
            prediction = self._default_manager.gsrs_prediction_by_id(self.id)
            actual_result = self.result
            if prediction == 'Not enough games to calculate prediction (the model needs at least 6 gameweeks)':
                out = ''
            elif prediction == actual_result:
                out = 'Success'
            else:
                out = 'Fail'
            return out
        else:
            return ''

    def r_difference(self):
        # this means if self.elo_rating_home is not empty or null
        if self.elo_rating_home:
            rdiff = round(self.elo_rating_home_previous_week - self.elo_rating_away_previous_week, 0)
            return rdiff
        else:
            return ''

    def r_difference_6_games_back(self):
        # this means if self.elo_rating_home_6_weeks_ago is not empty or null
        if self.elo_rating_home_6_weeks_ago:
            hmdiff = self.elo_rating_home_previous_week - self.elo_rating_home_6_weeks_ago
            awdiff = self.elo_rating_away_previous_week - self.elo_rating_away_6_weeks_ago
            rdiff = round(hmdiff - awdiff, 0)
            return rdiff
        else:
            return ''

    def gsrs_goaldiff(self):
        # if self.goaldiff_hm:
        #     return self.goaldiff_hm - self.goaldiff_aw
        # else:
        #     return 0
        return self.goaldiff_hm - self.goaldiff_aw

    def save(self, *args, **kwargs):
        if self.homegoals >= 0:
            if self.homegoals > self.awaygoals:
                self.result = "HOME"
                # self.hometeam.points += 3
            elif self.homegoals < self.awaygoals:
                self.result = "AWAY"
            else:
                self.result = "DRAW"
        else:
            self.result = ''

        # t1 = datetime.now()
        self.elo_rating_home = self.r_new_home()
        self.elo_rating_away = self.r_new_away()
        # t2 = datetime.now()
        # t3 = (t2 - t1).total_seconds()
        # print('elo_rating_home and elo_rating_away ran in: ', t3)

        # t1 = datetime.now()
        self.elo_rating_home_previous_week = self._default_manager.get_previous_elo_by_actual_date_for_initial(self.hometeam, self.season, self.date)
        self.elo_rating_away_previous_week = self._default_manager.get_previous_elo_by_actual_date_for_initial(self.awayteam, self.season, self.date)
        # t2 = datetime.now()
        # t3 = (t2 - t1).total_seconds()
        # print('elo_rating_home_previous_week and elo_rating_away_previous_week ran in: ', t3)

        self.elo_rating_home_6_weeks_ago = self._default_manager.get_previous_elo_from_lookback_by_date(self.hometeam, self.season, self.date, 6)
        self.elo_rating_away_6_weeks_ago = self._default_manager.get_previous_elo_from_lookback_by_date(self.awayteam, self.season, self.date, 6)
        # t1 = datetime.now()
        self.rdiff = self.r_difference()
        self.goaldiff_hm = self._default_manager.total_goal_diff_from_date(self.hometeam, self.season.id, self.date)
        self.goaldiff_aw = self._default_manager.total_goal_diff_from_date(self.awayteam, self.season.id, self.date)
        # t2 = datetime.now()
        # t3 = (t2 - t1).total_seconds()
        # print('rdiff, goaldiff_hm and goaldiff_aw:', t3)

        # t1 = datetime.now()
        self.prediction_elohist = self._default_manager.elo_hist_prediction_by_date(self.hometeam, self.awayteam, self.season.id, self.date, self.gameweek)
        if self._default_manager.is_first_game(self.hometeam, self.season.id, self.date) == 'Yes' or self._default_manager.is_first_game(self.awayteam, self.season.id, self.date) == 'Yes':
            self.prediction_status_elohist = ''
        else:
            self.prediction_status_elohist = self.elo_hist_prediction_status()
        # t2 = datetime.now()
        # t3 = (t2 - t1).total_seconds()
        # print('prediction_elohist and prediction_status_elohist:', t3)

        # t1 = datetime.now()
        self.prediction_elol6 = self._default_manager.elo_l6_prediction_by_date(self.hometeam, self.awayteam, self.season.id, self.date, self.gameweek)
        # t2 = datetime.now()
        # t3 = (t2 - t1).total_seconds()
        # print('prediction_elol6', t3)
        # t1 = datetime.now()
        if self._default_manager.is_first_game(self.hometeam, self.season.id, self.date) == 'Yes' or self._default_manager.is_first_game(self.awayteam, self.season.id, self.date) == 'Yes':
            self.prediction_status_elol6 = ''
        else:
            self.prediction_status_elol6 = self.elo_l6_prediction_status()
        # t2 = datetime.now()
        # t3 = (t2 - t1).total_seconds()
        # print('prediction_status_elol6:', t3)

        # t1 = datetime.now()
        self.prediction_gsrs = self._default_manager.gsrs_prediction_by_date(self.hometeam, self.awayteam, self.season.id, self.date)
        if self._default_manager.is_first_game(self.hometeam, self.season.id, self.date) == 'Yes' or self._default_manager.is_first_game(self.awayteam, self.season.id, self.date) == 'Yes':
            self.prediction_status_gsrs = ''
        else:
            self.prediction_status_gsrs = self.gsrs_prediction_status()
        # t2 = datetime.now()
        # t3 = (t2 - t1).total_seconds()
        # print('prediction_gsrs and prediction_status_gsrs:', t3)

        # hometeam result and points
        if self.homegoals >= 0:
            if self.homegoals > self.awaygoals:
                self.hm_result = 'W'
                self.hm_points = 3
            elif self.homegoals < self.awaygoals:
                self.hm_result = 'L'
                self.hm_points = 0
            elif self.homegoals == self.awaygoals:
                self.hm_result = 'D'
                self.hm_points = 1
            else:
                pass
        else:
            pass

        # awayteam result and points
        if self.awaygoals >= 0:
            if self.awaygoals > self.homegoals:
                self.aw_result = 'W'
                self.aw_points = 3
            elif self.awaygoals < self.homegoals:
                self.aw_result = 'L'
                self.aw_points = 0
            elif self.awaygoals == self.homegoals:
                self.aw_result = 'D'
                self.aw_points = 1
            else:
                pass
        else:
            pass
        super(Game, self).save(*args, **kwargs)

    def __str__(self):
        return str(self.date) + " " + str(self.hometeam) + " vs " + str(self.awayteam)


class GameFilter(django_filters.FilterSet):

    class Meta:
        model = Game
        fields = ['gameweek']


class GameSeasonFilter(django_filters.FilterSet):

    class Meta:
        model = Game
        fields = ['season']


class Post(models.Model):
    author = models.ForeignKey('auth.User')
    home_team = models.ForeignKey('Team', null=True, related_name='home_team', verbose_name='Home Team')
    away_team = models.ForeignKey('Team', null=True, related_name='away_team', verbose_name='Away Team')
    title = models.CharField(max_length=200)
    text = models.TextField()
    created_date = models.DateTimeField(
        default=timezone.now)
    published_date = models.DateTimeField(
        blank=True, null=True)

    def publish(self):
        self.published_date = timezone.now()
        self.save()

    def __str__(self):
        return self.title


class Tip(models.Model):
    TIPSTER_CHOICES = (
        ('Alesantro', 'Alesantro'),
        ('Krok', 'Krok'),
        ('Mr X', 'Mr X'),
        ('The Bomber', 'The Bomber'),
        ('Mr Combo', 'Mr Combo'),
        ('GG', 'GG'),
        ('---', '---'),
    )

    TIPTYPE_CHOICES = (
        ('1', '1'),
        ('X', 'X'),
        ('2', '2'),
        ('DC 1X', 'DC 1X'),
        ('DC X2', 'DC X2'),
        ('DC 12', 'DC 12'),
        ('Over 2.5', 'Over 2.5'),
        ('Under 2.5', 'Under 2.5'),
        ('Over 3.5', 'Over 3.5'),
        ('Under 3.5', 'Under 3.5'),
        ('Over 4.5', 'Over 4.5'),
        ('Under 4.5', 'Under 4.5'),
        ('GG Yes', 'GG Yes'),
        ('GG No', 'GG No'),
        ('1 & Over 2.5', '1 & Over 2.5'),
        ('1 & Under 2.5', '1 & Under 2.5'),
        ('1 & Over 3.5', '1 & Over 3.5'),
        ('1 & Under 3.5', '1 & Under 3.5'),
        ('1 & Over 4.5', '1 & Over 4.5'),
        ('1 & Under 4.5', '1 & Under 4.5'),
        ('1 & GG Yes', '1 & GG Yes'),
        ('1 & GG No', '1 & GG No'),
        ('2 & Over 2.5', '2 & Over 2.5'),
        ('2 & Under 2.5', '2 & Under 2.5'),
        ('2 & Over 3.5', '2 & Over 3.5'),
        ('2 & Under 3.5', '2 & Under 3.5'),
        ('2 & Over 4.5', '2 & Over 4.5'),
        ('2 & Under 4.5', '2 & Under 4.5'),
        ('2 & GG Yes', '2 & GG Yes'),
        ('2 & GG No', '2 & GG No'),
        ('X & Over 2.5', 'X & Over 2.5'),
        ('X & Under 2.5', 'X & Under 2.5'),
        ('X & Over 3.5', 'X & Over 3.5'),
        ('X & Under 3.5', 'X & Under 3.5'),
        ('X & Over 4.5', 'X & Over 4.5'),
        ('X & Under 4.5', 'X & Under 4.5'),
        ('X & GG Yes', 'X & GG Yes'),
        ('X & GG No', 'X & GG No'),
        ('---', '---'),
    )
    tipster = models.CharField(max_length=15, choices=TIPSTER_CHOICES, default='---', )
    game = models.ForeignKey('Game')
    time = models.TimeField(auto_now=False, auto_now_add=False, null=True, blank=True)
    tip_type = models.CharField(max_length=15, choices=TIPTYPE_CHOICES, default='---', )
    tip_odds = models.FloatField(null=True, blank=True)
    tip_status = models.CharField(max_length=15, null=True, blank=True)

    # Returns Success and Fail depending on the tip_type. Returns N/A if tip_type='---' and Pending if game has no score
    # Remember to add to this code every time you add new TIP_TYPE choices!!!
    def tipstatus(self):
        if self.game.homegoals >= 0:
            if self.tip_type == '1':
                if self.game.homegoals > self.game.awaygoals:
                    return 'Success'
                else:
                    return 'Fail'
            elif self.tip_type == 'X':
                if self.game.homegoals == self.game.awaygoals:
                    return 'Success'
                else:
                    return 'Fail'
            elif self.tip_type == '2':
                if self.game.homegoals < self.game.awaygoals:
                    return 'Success'
                else:
                    return 'Fail'
            elif self.tip_type == 'DC 1X':
                if self.game.homegoals > self.game.awaygoals or self.game.homegoals == self.game.awaygoals:
                    return 'Success'
                else:
                    return 'Fail'
            elif self.tip_type == 'DC X2':
                if self.game.homegoals < self.game.awaygoals or self.game.homegoals == self.game.awaygoals:
                    return 'Success'
                else:
                    return 'Fail'
            elif self.tip_type == 'DC 12':
                if self.game.homegoals < self.game.awaygoals or self.game.homegoals > self.game.awaygoals:
                    return 'Success'
                else:
                    return 'Fail'
            elif self.tip_type == 'Over 2.5':
                if self.game.homegoals + self.game.awaygoals > 2.5:
                    return 'Success'
                else:
                    return 'Fail'
            elif self.tip_type == 'Under 2.5':
                if self.game.homegoals + self.game.awaygoals < 2.5:
                    return 'Success'
                else:
                    return 'Fail'
            elif self.tip_type == 'Over 3.5':
                if self.game.homegoals + self.game.awaygoals > 3.5:
                    return 'Success'
                else:
                    return 'Fail'
            elif self.tip_type == 'Under 3.5':
                if self.game.homegoals + self.game.awaygoals < 3.5:
                    return 'Success'
                else:
                    return 'Fail'
            elif self.tip_type == 'Over 4.5':
                if self.game.homegoals + self.game.awaygoals > 4.5:
                    return 'Success'
                else:
                    return 'Fail'
            elif self.tip_type == 'Under 4.5':
                if self.game.homegoals + self.game.awaygoals < 4.5:
                    return 'Success'
                else:
                    return 'Fail'
            elif self.tip_type == 'GG Yes':
                if self.game.homegoals > 0 and self.game.awaygoals > 0:
                    return 'Success'
                else:
                    return 'Fail'
            elif self.tip_type == 'GG No':
                if (self.game.homegoals > 0 and self.game.awaygoals == 0)\
                        or (self.game.homegoals == 0 and self.game.awaygoals > 0):
                    return 'Success'
                else:
                    return 'Fail'
            elif self.tip_type == '1 & Over 2.5':
                if self.game.homegoals > self.game.awaygoals and self.game.homegoals + self.game.awaygoals > 2.5:
                    return 'Success'
                else:
                    return 'Fail'
            elif self.tip_type == '1 & Under 2.5':
                if self.game.homegoals > self.game.awaygoals and self.game.homegoals + self.game.awaygoals < 2.5:
                    return 'Success'
                else:
                    return 'Fail'
            elif self.tip_type == '1 & Over 3.5':
                if self.game.homegoals > self.game.awaygoals and self.game.homegoals + self.game.awaygoals > 3.5:
                    return 'Success'
                else:
                    return 'Fail'
            elif self.tip_type == '1 & Under 3.5':
                if self.game.homegoals > self.game.awaygoals and self.game.homegoals + self.game.awaygoals < 3.5:
                    return 'Success'
                else:
                    return 'Fail'
            elif self.tip_type == '1 & Over 4.5':
                if self.game.homegoals > self.game.awaygoals and self.game.homegoals + self.game.awaygoals > 4.5:
                    return 'Success'
                else:
                    return 'Fail'
            elif self.tip_type == '1 & Under 4.5':
                if self.game.homegoals > self.game.awaygoals and self.game.homegoals + self.game.awaygoals < 4.5:
                    return 'Success'
                else:
                    return 'Fail'
            elif self.tip_type == '1 & GG Yes':
                if (self.game.homegoals > self.game.awaygoals) and (self.game.homegoals > 0 and self.game.awaygoals > 0):
                    return 'Success'
                else:
                    return 'Fail'
            elif self.tip_type == '1 & GG No':
                if (self.game.homegoals > self.game.awaygoals) and\
                        ((self.game.homegoals > 0 and self.game.awaygoals == 0) or (self.game.homegoals == 0 and self.game.awaygoals > 0)):
                    return 'Success'
                else:
                    return 'Fail'
            elif self.tip_type == '2 & Over 2.5':
                if self.game.homegoals < self.game.awaygoals and self.game.homegoals + self.game.awaygoals > 2.5:
                    return 'Success'
                else:
                    return 'Fail'
            elif self.tip_type == '2 & Under 2.5':
                if self.game.homegoals < self.game.awaygoals and self.game.homegoals + self.game.awaygoals < 2.5:
                    return 'Success'
                else:
                    return 'Fail'
            elif self.tip_type == '2 & Over 3.5':
                if self.game.homegoals < self.game.awaygoals and self.game.homegoals + self.game.awaygoals > 3.5:
                    return 'Success'
                else:
                    return 'Fail'
            elif self.tip_type == '2 & Under 3.5':
                if self.game.homegoals < self.game.awaygoals and self.game.homegoals + self.game.awaygoals < 3.5:
                    return 'Success'
                else:
                    return 'Fail'
            elif self.tip_type == '2 & Over 4.5':
                if self.game.homegoals < self.game.awaygoals and self.game.homegoals + self.game.awaygoals > 4.5:
                    return 'Success'
                else:
                    return 'Fail'
            elif self.tip_type == '2 & Under 4.5':
                if self.game.homegoals < self.game.awaygoals and self.game.homegoals + self.game.awaygoals < 4.5:
                    return 'Success'
                else:
                    return 'Fail'
            elif self.tip_type == '2 & GG Yes':
                if (self.game.homegoals < self.game.awaygoals) and (self.game.homegoals > 0 and self.game.awaygoals > 0):
                    return 'Success'
                else:
                    return 'Fail'
            elif self.tip_type == '2 & GG No':
                if (self.game.homegoals < self.game.awaygoals) and\
                        ((self.game.homegoals > 0 and self.game.awaygoals == 0) or (self.game.homegoals == 0 and self.game.awaygoals > 0)):
                    return 'Success'
                else:
                    return 'Fail'
            elif self.tip_type == 'X & Over 2.5':
                if self.game.homegoals == self.game.awaygoals and self.game.homegoals + self.game.awaygoals > 2.5:
                    return 'Success'
                else:
                    return 'Fail'
            elif self.tip_type == 'X & Under 2.5':
                if self.game.homegoals == self.game.awaygoals and self.game.homegoals + self.game.awaygoals < 2.5:
                    return 'Success'
                else:
                    return 'Fail'
            elif self.tip_type == 'X & Over 3.5':
                if self.game.homegoals == self.game.awaygoals and self.game.homegoals + self.game.awaygoals > 3.5:
                    return 'Success'
                else:
                    return 'Fail'
            elif self.tip_type == 'X & Under 3.5':
                if self.game.homegoals == self.game.awaygoals and self.game.homegoals + self.game.awaygoals < 3.5:
                    return 'Success'
                else:
                    return 'Fail'
            elif self.tip_type == 'X & Over 4.5':
                if self.game.homegoals == self.game.awaygoals and self.game.homegoals + self.game.awaygoals > 4.5:
                    return 'Success'
                else:
                    return 'Fail'
            elif self.tip_type == 'X & Under 4.5':
                if self.game.homegoals == self.game.awaygoals and self.game.homegoals + self.game.awaygoals < 4.5:
                    return 'Success'
                else:
                    return 'Fail'
            elif self.tip_type == 'X & GG Yes':
                if (self.game.homegoals == self.game.awaygoals) and (self.game.homegoals > 0 and self.game.awaygoals > 0):
                    return 'Success'
                else:
                    return 'Fail'
            elif self.tip_type == 'X & GG No':
                if (self.game.homegoals == self.game.awaygoals) and\
                        ((self.game.homegoals > 0 and self.game.awaygoals == 0) or (self.game.homegoals == 0 and self.game.awaygoals > 0)):
                    return 'Success'
                else:
                    return 'Fail'
            elif self.tip_type == '---':
                return 'N/A'
        else:
            return 'Pending'
        return 'NA'

    def __str__(self):
        return str(self.tipster) + " " + str(self.game) + " (" + str(self.tip_type) + ")"

    def save(self, *args, **kwargs):
        self.tip_status = self.tipstatus()
        super(Tip, self).save(*args, **kwargs)


class BetslipManager(models.Manager):
    # Returns the number of betslips given by a tipster
    # ~Q means not equal
    def tipster_total_betslips(self, tipster, end_year):
        cnt = self.filter(betslip_tipster=tipster).exclude(tips__game__season__end_date__year__lt=end_year).exclude(tips__game__season__end_date__year__gt=end_year).count()
        return cnt

    # Returns the number of non pending betslips given by a tipster
    def tipster_total_nonpending_betslips(self, tipster, end_year):
        cnt = self.filter(betslip_tipster=tipster).exclude(tips__game__season__end_date__year__lt=end_year).exclude(tips__game__season__end_date__year__gt=end_year).exclude(betslip_status='Pending').count()
        return cnt

    # Returns the number of active betslips given by a tipster
    def tipster_total_active_betslips(self, tipster, end_year):
        cnt = self.filter(betslip_tipster=tipster, betslip_status='Pending').exclude(tips__game__season__end_date__year__lt=end_year).exclude(tips__game__season__end_date__year__gt=end_year).count()
        return cnt

    # Returns the number of successful betslips given by a tipster
    def tipster_successful_betslips(self, tipster, end_year):
        cnt = self.filter(betslip_tipster=tipster, betslip_status='Success').exclude(tips__game__season__end_date__year__lt=end_year).exclude(tips__game__season__end_date__year__gt=end_year).count()
        return cnt

    # Returns the number of lost betslips given by a tipster
    def tipster_lost_betslips(self, tipster, end_year):
        cnt = self.filter(betslip_tipster=tipster, betslip_status='Fail').exclude(tips__game__season__end_date__year__lt=end_year).exclude(tips__game__season__end_date__year__gt=end_year).count()
        return cnt

    # Returns the sum of stakes played by a tipster
    def tipster_sum_of_stakes(self, tipster, end_year):
        stakes_sum = self.filter(betslip_tipster=tipster).exclude(tips__game__season__end_date__year__lt=end_year).exclude(tips__game__season__end_date__year__gt=end_year).exclude(betslip_status='Pending').aggregate(Sum('stake'))
        if stakes_sum['stake__sum']:
            return stakes_sum['stake__sum']
        else:
            return 0

    # Returns the sum of active stakes by a tipster
    def tipster_sum_of_active_stakes(self, tipster, end_year):
        stakes_sum = self.filter(betslip_tipster=tipster, betslip_status='Pending').exclude(tips__game__season__end_date__year__lt=end_year).exclude(tips__game__season__end_date__year__gt=end_year).aggregate(Sum('stake'))
        if stakes_sum['stake__sum']:
            return stakes_sum['stake__sum']
        else:
            return 0

    # Returns the sum of profits or losses for a tipster
    def tipster_sum_of_profits(self, tipster, end_year):
        profits_sum = self.filter(betslip_tipster=tipster).exclude(tips__game__season__end_date__year__lt=end_year).exclude(tips__game__season__end_date__year__gt=end_year).exclude(betslip_status='Pending').aggregate(Sum('profit'))
        if profits_sum['profit__sum']:
            return profits_sum['profit__sum']
        else:
            return 0


class Betslip(models.Model):
    BETSLIP_TIPSTER_CHOICES = (
        ('Alesantro', 'Alesantro'),
        ('Krok', 'Krok'),
        ('Mr X', 'Mr X'),
        ('The Bomber', 'The Bomber'),
        ('Mr Combo', 'Mr Combo'),
        ('---', '---'),
    )
    BETSLIP_TYPES = (
        ('Singles', 'Singles'),
        ('Any 2', 'Any 2'),
        ('Any 3', 'Any 3'),
        ('Any 4', 'Any 4'),
        ('Any 2 or 3', 'Any 2 or 3'),
        ('Any 3 or 4', 'Any 3 or 4'),
        ('Any 4 or 5', 'Any 4 or 5'),
        ('All', 'All'),
        ('---', '---'),
    )
    betslip_tipster = models.CharField(max_length=15, choices=BETSLIP_TIPSTER_CHOICES, default='---', )
    slug = models.SlugField(unique=False, blank=True, null=True)
    tips = models.ManyToManyField(Tip)
    bet_type = models.CharField(max_length=15, choices=BETSLIP_TYPES, default='---', )
    created_date = models.DateTimeField(default=timezone.now)
    betslip_status = models.CharField(max_length=15, null=True, blank=True)
    stake = models.FloatField(null=True, blank=True)
    profit = models.FloatField(null=True, blank=True)
    objects = BetslipManager()

    def betslipstatus(self):
        pending_cnt = 0
        for g in self.tips.all():
            if g.tip_status == 'Pending':
                pending_cnt += 1
        if pending_cnt > 0:
            return 'Pending'
        else:
            succ_cnt = 0
            if self.bet_type == 'All' or self.bet_type == 'Singles':
                tps_cnt = self.tips.count()
                for t in self.tips.all():
                    if t.tip_status == 'Success':
                        succ_cnt += 1
                if succ_cnt == tps_cnt:
                    return 'Success'
                else:
                    return 'Fail'
            elif self.bet_type == 'Any 2' or self.bet_type == 'Any 2 or 3':
                for t in self.tips.all():
                    if t.tip_status == 'Success':
                        succ_cnt += 1
                if succ_cnt >= 2:
                    return 'Success'
                else:
                    return 'Fail'
            elif self.bet_type == 'Any 3' or self.bet_type == 'Any 3 or 4':
                for t in self.tips.all():
                    if t.tip_status == 'Success':
                        succ_cnt += 1
                if succ_cnt >= 3:
                    return 'Success'
                else:
                    return 'Fail'
            elif self.bet_type == 'Any 4' or self.bet_type == 'Any 4 or 5':
                for t in self.tips.all():
                    if t.tip_status == 'Success':
                        succ_cnt += 1
                if succ_cnt >= 4:
                    return 'Success'
                else:
                    return 'Fail'
        return 'NA'

    # Returns a list of accumulated odds in case of a successful betslip. Note that in case the bet type is any 2, 3 or 4
    # the function returns more than one accumulated odds
    # This assumes that Singles are entered one by one in betslips. DO NOT ENTER more than
    # one single bet in a betslip.
    # Additionally, accum only does calculations if the betslip type is either success or failed, otherwise it returns
    # an empty list.
    # Remember to add to this code every time you add a new BETSLIP_TYPE!!!
    def accum(self):
        # itertools.combinations returns all possible combinations of a list as a list of tuples
        # i.e [1,2,3] returns [(1,2), (1,3), (2,3)]
        x = []
        a = 1.0
        if self.bet_type == 'All' or self.bet_type == 'Singles':
            if self.betslip_status == 'Success':
                for tp in self.tips.all():
                    a *= tp.tip_odds
                x.append(a)
                return x
            elif self.betslip_status == 'Fail':
                x.append(-1)
                return x
            else:
                return x
        elif self.bet_type == 'Any 2':
            if self.betslip_status == 'Success' or self.betslip_status == 'Fail':
                combos = list(itertools.combinations(self.tips.all(), 2))
                for tpl in combos:
                    if tpl[0].tip_status == 'Success' and tpl[1].tip_status == 'Success':
                        x.append(tpl[0].tip_odds * tpl[1].tip_odds)
                    else:
                        x.append(-1)
                return x
            else:
                return x
        elif self.bet_type == 'Any 3':
            if self.betslip_status == 'Success' or self.betslip_status == 'Fail':
                combos = list(itertools.combinations(self.tips.all(), 3))
                for tpl in combos:
                    if tpl[0].tip_status == 'Success' and tpl[1].tip_status == 'Success' and tpl[2].tip_status == 'Success':
                        x.append(tpl[0].tip_odds * tpl[1].tip_odds * tpl[2].tip_odds)
                    else:
                        x.append(-1)
                return x
            else:
                return x
        elif self.bet_type == 'Any 4':
            if self.betslip_status == 'Success' or self.betslip_status == 'Fail':
                combos = list(itertools.combinations(self.tips.all(), 4))
                for tpl in combos:
                    if tpl[0].tip_status == 'Success' and tpl[1].tip_status == 'Success' and tpl[2].tip_status == 'Success' and tpl[3].tip_status == 'Success':
                        x.append(tpl[0].tip_odds * tpl[1].tip_odds * tpl[2].tip_odds * tpl[3].tip_odds)
                    else:
                        x.append(-1)
                return x
            else:
                return x
        elif self.bet_type == 'Any 2 or 3':
            expected_tips = 3
            if self.tips.count() == expected_tips:
                if self.betslip_status == 'Success' or self.betslip_status == 'Fail':
                    cnt_succ = 0
                    for tp in self.tips.all():
                        if tp.tip_status == 'Success':
                            cnt_succ += 1
                    if cnt_succ == expected_tips:
                        for tpp in self.tips.all():
                            a *= tpp.tip_odds
                        x.append(a)
                    else:
                        x.append(-1)
                    combos = list(itertools.combinations(self.tips.all(), 2))
                    for tpl in combos:
                        if tpl[0].tip_status == 'Success' and tpl[1].tip_status == 'Success':
                            x.append(tpl[0].tip_odds * tpl[1].tip_odds)
                        else:
                            x.append(-1)
                    return x
                else:
                    return x
        elif self.bet_type == 'Any 3 or 4':
            expected_tips = 4
            if self.tips.count() == expected_tips:
                if self.betslip_status == 'Success' or self.betslip_status == 'Fail':
                    cnt_succ = 0
                    for tp in self.tips.all():
                        if tp.tip_status == 'Success':
                            cnt_succ += 1
                    if cnt_succ == expected_tips:
                        for tpp in self.tips.all():
                            a *= tpp.tip_odds
                        x.append(a)
                    else:
                        x.append(-1)
                    combos = list(itertools.combinations(self.tips.all(), 3))
                    for tpl in combos:
                        if tpl[0].tip_status == 'Success' and tpl[1].tip_status == 'Success' and tpl[2].tip_status == 'Success':
                            x.append(tpl[0].tip_odds * tpl[1].tip_odds * tpl[2].tip_odds)
                        else:
                            x.append(-1)
                    return x
                else:
                    return x
        elif self.bet_type == 'Any 4 or 5':
            expected_tips = 5
            if self.tips.count() == expected_tips:
                if self.betslip_status == 'Success' or self.betslip_status == 'Fail':
                    cnt_succ = 0
                    for tp in self.tips.all():
                        if tp.tip_status == 'Success':
                            cnt_succ += 1
                    if cnt_succ == expected_tips:
                        for tpp in self.tips.all():
                            a *= tpp.tip_odds
                        x.append(a)
                    else:
                        x.append(-1)
                    combos = list(itertools.combinations(self.tips.all(), 4))
                    for tpl in combos:
                        if tpl[0].tip_status == 'Success' and tpl[1].tip_status == 'Success' and tpl[2].tip_status == 'Success' and tpl[3].tip_status == 'Success':
                            x.append(tpl[0].tip_odds * tpl[1].tip_odds * tpl[2].tip_odds * tpl[3].tip_odds)
                        else:
                            x.append(-1)
                    return x
                else:
                    return x
        return x

    # Returns the number of sub slips that are created according to bet type
    # i.e when a betslip has 3 games and the type is Any 2, this should return 3
    def subslips(self):
        combos = 1
        if self.bet_type == 'Any 2':
            combo_list = list(itertools.combinations(self.tips.all(), 2))
            combos = len(combo_list)
        if self.bet_type == 'Any 3':
            combo_list = list(itertools.combinations(self.tips.all(), 3))
            combos = len(combo_list)
        if self.bet_type == 'Any 4':
            combo_list = list(itertools.combinations(self.tips.all(), 4))
            combos = len(combo_list)
        if self.bet_type == 'Any 2 or 3':
            combo_list = list(itertools.combinations(self.tips.all(), 2))
            combos = len(combo_list) + 1
        if self.bet_type == 'Any 3 or 4':
            combo_list = list(itertools.combinations(self.tips.all(), 3))
            combos = len(combo_list) + 1
        if self.bet_type == 'Any 4 or 5':
            combo_list = list(itertools.combinations(self.tips.all(), 4))
            combos = len(combo_list) + 1
        return combos

    # Returns the accumulated profit or loss of the betslip. This returns the net profit or loss meaning that in case
    # of a succesful betslip, it deducts the original stake amount from the profit.
    # Remember to add to this code every time you add a new BETSLIP_TYPE!!!
    def betslip_profit(self):
        p = 0
        l = 0
        if self.stake:
            if self.betslip_status == 'Pending':
                pass
            elif self.betslip_status == 'NA':
                pass
            else:
                stk = float(self.stake)
                if self.bet_type == 'All' or self.bet_type == 'Singles':
                    if self.betslip_status == 'Success':
                        for accm in self.accum():
                            p += (stk * accm) - stk
                        return p
                    elif self.betslip_status == 'Fail':
                        l = -stk
                        return l
                elif self.bet_type == 'Any 2' or self.bet_type == 'Any 3' or self.bet_type == 'Any 4' or self.bet_type == 'Any 2 or 3' or self.bet_type == 'Any 3 or 4' or self.bet_type == 'Any 4 or 5':
                    for accm in self.accum():
                        if accm > 0:
                            p += ((stk / self.subslips()) * accm) - (stk / self.subslips())
                        else:
                            l += stk / self.subslips()
                    return p - l
                else:
                    pass
        else:
            pass

    # Returns the gross profit or loss of the betslip.
    # Remember to add to this code every time you add a new BETSLIP_TYPE!!!
    def betslip_gross_profit(self):
        p = 0
        l = 0
        if self.stake:
            if self.betslip_status == 'Pending':
                pass
            elif self.betslip_status == 'NA':
                pass
            else:
                stk = float(self.stake)
                if self.bet_type == 'All' or self.bet_type == 'Singles':
                    if self.betslip_status == 'Success':
                        for accm in self.accum():
                            p += (stk * accm)
                        return p
                    elif self.betslip_status == 'Fail':
                        l = -stk
                        return l
                elif self.bet_type == 'Any 2' or self.bet_type == 'Any 3' or self.bet_type == 'Any 4' or self.bet_type == 'Any 2 or 3' or self.bet_type == 'Any 3 or 4' or self.bet_type == 'Any 4 or 5':
                    for accm in self.accum():
                        if accm > 0:
                            p += ((stk / self.subslips()) * accm)
                        else:
                            l += stk / self.subslips()
                    if self.betslip_status == 'Success':
                        return p
                    elif self.betslip_status == 'Fail':
                        return p - l
                else:
                    pass
        else:
            pass

    def __str__(self):
        return str(self.betslip_tipster) + " " + str(self.created_date)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.betslip_tipster)
        if self.betslip_status:
            self.betslip_status = self.betslipstatus()
        else:
            self.betslip_status = 'Pending'
        self.profit = self.betslip_profit()
        super(Betslip, self).save(*args, **kwargs)


# SportMonks tables
@python_2_unicode_compatible
class CountrySM(models.Model):
    country_id = models.IntegerField(unique=True, primary_key=True)
    name = models.CharField(max_length=200)
    continent = models.CharField(max_length=200, null=True, blank=True)
    fifa_code = models.CharField(max_length=200, null=True, blank=True)
    iso_code = models.CharField(max_length=200, null=True, blank=True)
    flag = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "SM Country"
        verbose_name_plural = "SM Countries"

    def __str__(self):
        return self.name


class LeagueSM(models.Model):
    league_id = models.IntegerField(unique=True, primary_key=True)
    name = models.CharField(max_length=100)
    country = models.ForeignKey('CountrySM', null=True)
    is_cup = models.CharField(max_length=200, null=True, blank=True)
    live_standings = models.CharField(max_length=200, null=True, blank=True)
    topscorer_goals = models.CharField(max_length=200, null=True, blank=True)
    topscorer_assists = models.CharField(max_length=200, null=True, blank=True)
    topscorer_cards = models.CharField(max_length=200, null=True, blank=True)

    class Meta:
        ordering = ["country__name"]
        verbose_name = "SM League"
        verbose_name_plural = "SM Leagues"

    def __str__(self):
        return self.country.name + ' ' + self.name                


class SeasonSM(models.Model):
    season_id = models.IntegerField(unique=True, primary_key=True)
    name = models.CharField(max_length=100)
    league = models.ForeignKey('LeagueSM', null=True)

    class Meta:
        ordering = ["league__country__name"]
        verbose_name = "SM Season"
        verbose_name_plural = "SM Seasons"

    def __str__(self):
        # return "(id: " + str(self.season_id) + ") " + str(self.name)
        return self.league.country.name + ' ' + self.league.name + " " + self.name


class TeamSM(models.Model):
    team_id = models.IntegerField(unique=True, primary_key=True)
    name = models.CharField(max_length=100)
    short_code = models.CharField(max_length=200, null=True, blank=True)
    country = models.ForeignKey('CountrySM', null=True)
    founded = models.IntegerField(null=True)
    logo_path = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "SM Team"
        verbose_name_plural = "SM Teams"

    def __str__(self):
        return self.name           


class FixtureSM(models.Model):
    fixture_id = models.IntegerField(unique=True, primary_key=True)
    season = models.ForeignKey('SeasonSM', null=True)
    hometeam = models.ForeignKey('TeamSM', null=True, related_name='hometeam')
    awayteam = models.ForeignKey('TeamSM', null=True, related_name='awayteam')
    weather_code = models.CharField(max_length=200, null=True, blank=True)
    weather_type = models.CharField(max_length=200, null=True, blank=True)
    weather_icon = models.TextField(null=True, blank=True)
    attendance = models.IntegerField(null=True)
    pitch_status = models.CharField(max_length=200, null=True, blank=True)
    home_formation = models.CharField(max_length=200, null=True, blank=True)
    away_formation = models.CharField(max_length=200, null=True, blank=True)
    home_goals = models.IntegerField(null=True)
    away_goals = models.IntegerField(null=True)
    ht_score = models.CharField(max_length=200, null=True, blank=True)
    ft_score = models.CharField(max_length=200, null=True, blank=True)
    match_status = models.CharField(max_length=200, null=True, blank=True)
    match_date = models.DateField(null=True, blank=True)
    match_time = models.TimeField(null=True, blank=True)
    gameweek = models.IntegerField(null=True)
    stage = models.CharField(max_length=200, null=True, blank=True)
    venue_name = models.CharField(max_length=200, null=True, blank=True)
    venue_surface = models.CharField(max_length=200, null=True, blank=True)
    venue_city = models.CharField(max_length=200, null=True, blank=True)
    venue_capacity = models.IntegerField(null=True)
    venue_image = models.TextField(null=True)
    odds_1 = models.FloatField(null=True, blank=True)
    odds_x = models.FloatField(null=True, blank=True)
    odds_2 = models.FloatField(null=True, blank=True)
    home_coach = models.CharField(max_length=200, null=True, blank=True)
    home_coach_nationality = models.CharField(max_length=200, null=True, blank=True)
    home_coach_image = models.TextField(null=True, blank=True)
    away_coach = models.CharField(max_length=200, null=True, blank=True)
    away_coach_nationality = models.CharField(max_length=200, null=True, blank=True)
    away_coach_image = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ["match_date"]
        verbose_name = "SM Fixture"
        verbose_name_plural = "SM Fixtures"

    def __str__(self):
        return str(self.match_date) + " " + str(self.hometeam) + " vs " + str(self.awayteam)           
