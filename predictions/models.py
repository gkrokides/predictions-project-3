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


class Leagues(models.Model):
    country = models.CharField(max_length=200, verbose_name='Country', unique=False, null=False)
    division = models.IntegerField()
    league_name = models.CharField(max_length=200)
    country_code = models.CharField(max_length=20)
    short_name = models.CharField(max_length=50, unique=True)
    # the below fields (teamstotal, gwtotal) are redundant and will not be used in the future as they should have been included in the
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
            sn_lst.append([str(item), item.id, str(item.league.league_name), str(item.get_start_year()), str(item.get_end_year()), str(item.end_date), str(item.league.short_name)])
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

    # total games played by a team up to the given gameweek
    def get_total_games(self, team, seasn, gmweek):
        tmgames = self.filter(Q(hometeam=team, season=seasn, gameweek__lte=gmweek) | Q(awayteam=team, season=seasn, gameweek__lte=gmweek))
        tmgames_cnt = tmgames.count()
        return tmgames_cnt

    def get_previous_elo(self, tm, seasn, gmwk):
        out = 0
        prevgmwk = gmwk - 1
        # tmgames = self.filter(Q(hometeam=tm, season=seasn) | Q(awayteam=tm, season=seasn)).order_by('gameweek')
        if gmwk == 1:
            out = elosettings.STARTING_POINTS
        elif gmwk > 1:
            # ix = tmgames.get(gameweek=prevgmwk)
            iprevgame = self.filter(Q(hometeam=tm, season=seasn, gameweek=prevgmwk) | Q(awayteam=tm, season=seasn, gameweek=prevgmwk))
            prevgame = iprevgame.get(Q(hometeam=tm) | Q(awayteam=tm))
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

    def modified_hga(self, teamm, seasonn, gmwk):
        total_home_wins = self.filter(season=seasonn, hometeam=teamm, gameweek__lte=gmwk - 1, result='HOME').count()
        total_home_draws = self.filter(season=seasonn, hometeam=teamm, gameweek__lte=gmwk - 1, result='DRAW').count()
        win_points = total_home_wins * 1
        draw_points = total_home_draws * 0.5
        total_games = self.filter(hometeam=teamm, season=seasonn, gameweek__lte=gmwk - 1).count()
        if total_games == 0 or gmwk == 1:
            mhga = elosettings.ELO_HGA
        else:
            strike_rate = (win_points + draw_points) / total_games
            mhga = strike_rate * float(elosettings.ELO_HGA)
        return mhga

    def elo_draw_threshold(self, seasonn, gamewk):
        if gamewk == 1:
            out = 0
        else:
            games_lst = self.filter(season=seasonn, gameweek__lte=gamewk - 1)
            szn = Season.objects.get(id=seasonn)
            # I used to use teamstotal from the leagues model (instead of num_of_teams_in_season) but it was wrong because year by year the number of teams in a league might change
            # So the teamstotal in leagues is actually redundant
            # num_of_teams_in_season = Team.objects.filter(Q(hometeam__season__id=szn) | Q(awayteam__season__id=szn)).distinct().count()
            num_of_teams_in_season = szn.teamstotal
            multiplier = -num_of_teams_in_season / 2
            x = []
            for gm in games_lst:
                # h_r_old = self.get_previous_elo(tm=gm.hometeam, seasn=seasonn, gmwk=gm.gameweek)
                # a_r_old = self.get_previous_elo(tm=gm.awayteam, seasn=seasonn, gmwk=gm.gameweek)
                # rdiff = round(h_r_old - a_r_old, 0)
                # x.append(rdiff)
                x.append(gm.rdiff)
            out = abs(sum(x) / games_lst.count()) * multiplier
            # print x
        return out

    def elol6_draw_threshold(self, seasonn, gamewk):
        x = []
        if gamewk <= 7:
            out = 0
        else:
            games_lst = self.filter(season=seasonn, gameweek__lte=gamewk - 1, gameweek__gte=7)
            szn = Season.objects.get(id=seasonn)
            # I used to use teamstotal from the leagues model (instead of num_of_teams_in_season) but it was wrong because year by year the number of teams in a league might change
            # So the teamstotal in leagues is actually redundant
            # num_of_teams_in_season = Team.objects.filter(Q(hometeam__season__id=szn) | Q(awayteam__season__id=szn)).distinct().count()
            num_of_teams_in_season = szn.teamstotal
            multiplier = -num_of_teams_in_season / 2
            x = []
            for gm in games_lst:
                # h_r_old = self.get_previous_elo(tm=gm.hometeam, seasn=seasonn, gmwk=gm.gameweek) - self.get_previous_elo(tm=gm.hometeam, seasn=seasonn, gmwk=gm.gameweek - 5)
                # a_r_old = self.get_previous_elo(tm=gm.awayteam, seasn=seasonn, gmwk=gm.gameweek) - self.get_previous_elo(tm=gm.awayteam, seasn=seasonn, gmwk=gm.gameweek - 5)
                h_r_old = gm.elo_rating_home_previous_week - self.get_previous_elo(tm=gm.hometeam, seasn=seasonn, gmwk=gm.gameweek - 5)
                a_r_old = gm.elo_rating_away_previous_week - self.get_previous_elo(tm=gm.awayteam, seasn=seasonn, gmwk=gm.gameweek - 5)
                rdiff = round(h_r_old - a_r_old, 0)
                x.append(rdiff)
            out = abs(sum(x) / float(games_lst.count())) * multiplier
        return out

    def total_goal_diff(self, tm, seasn, gw):
        if gw <= 6:
            out = 0
        else:
            lst_hm = self.filter(hometeam=tm, season=seasn, gameweek__lte=gw - 1, gameweek__gte=gw - 6)
            lst_aw = self.filter(awayteam=tm, season=seasn, gameweek__lte=gw - 1, gameweek__gte=gw - 6)
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

    def elo_hist_prediction(self, hometm, awaytm, szn, gweek):
        if gweek == 'current':
            current_gw = self.last_gameweek(seasn=szn)[0].gameweek
            home_r = self.get_previous_elo(tm=hometm, seasn=szn, gmwk=current_gw)
            away_r = self.get_previous_elo(tm=awaytm, seasn=szn, gmwk=current_gw)
            rdiff = home_r - away_r
            draw_threshold = self.elo_draw_threshold(seasonn=szn, gamewk=current_gw)
            if rdiff > draw_threshold:
                prediction = "HOME"
            elif rdiff < (draw_threshold * 2):
                prediction = "AWAY"
            else:
                prediction = "DRAW"
        elif gweek > 6:
            home_r = self.get_previous_elo(tm=hometm, seasn=szn, gmwk=gweek)
            away_r = self.get_previous_elo(tm=awaytm, seasn=szn, gmwk=gweek)
            rdiff = home_r - away_r
            # print("{}: about to run elo_draw_threshold".format(datetime.now()))
            draw_threshold = self.elo_draw_threshold(seasonn=szn, gamewk=gweek)
            # print("{}: ran elo_draw_threshold".format(datetime.now()))
            if rdiff > draw_threshold:
                prediction = "HOME"
            elif rdiff < (draw_threshold * 2):
                prediction = "AWAY"
            else:
                prediction = "DRAW"
        else:
            prediction = "Not enough games to calculate prediction (the model needs at least 6 gameweeks)"
        return prediction

    def elo_l6_prediction(self, hometm, awaytm, szn, gweek):
        if gweek == 'current':
            current_gw = self.last_gameweek(seasn=szn)[0].gameweek
            home_r = self.get_previous_elo(tm=hometm, seasn=szn, gmwk=current_gw) - self.get_previous_elo(tm=hometm, seasn=szn, gmwk=current_gw - 5)
            away_r = self.get_previous_elo(tm=awaytm, seasn=szn, gmwk=current_gw) - self.get_previous_elo(tm=awaytm, seasn=szn, gmwk=current_gw - 5)
            rdiff = home_r - away_r
            draw_threshold = self.elol6_draw_threshold(seasonn=szn, gamewk=current_gw)
            if rdiff > draw_threshold:
                prediction = "HOME"
            elif rdiff < (draw_threshold * 2):
                prediction = "AWAY"
            else:
                prediction = "DRAW"
        elif gweek > 6:
            home_r = self.get_previous_elo(tm=hometm, seasn=szn, gmwk=gweek) - self.get_previous_elo(tm=hometm, seasn=szn, gmwk=gweek - 5)
            away_r = self.get_previous_elo(tm=awaytm, seasn=szn, gmwk=gweek) - self.get_previous_elo(tm=awaytm, seasn=szn, gmwk=gweek - 5)
            rdiff = home_r - away_r
            draw_threshold = self.elol6_draw_threshold(seasonn=szn, gamewk=gweek)
            if rdiff > draw_threshold:
                prediction = "HOME"
            elif rdiff < (draw_threshold * 2):
                prediction = "AWAY"
            else:
                prediction = "DRAW"
        else:
            prediction = "Not enough games to calculate prediction (the model needs at least 6 gameweeks)"
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

    def team_form(self, team, szn, gmwk):
        x = ""
        if gmwk < 1:
            return x
        else:
            lst = self.get(Q(hometeam=team, season=szn, gameweek=gmwk) | Q(awayteam=team, season=szn, gameweek=gmwk))
            if lst.hometeam == team:
                if lst.result == 'HOME':
                    x = "W"
                elif lst.result == 'AWAY':
                    x = "L"
                elif lst.result == 'DRAW':
                    x = "D"
                else:
                    x = lst.game_status
            elif lst.awayteam == team:
                if lst.result == 'HOME':
                    x = "L"
                elif lst.result == 'AWAY':
                    x = "W"
                elif lst.result == 'DRAW':
                    x = "D"
                else:
                    x = lst.game_status
            else:
                x = ""
        return x

    def last_gameweek_played(self, team, seazn):
        qry = self.filter(Q(hometeam=team, season=seazn) | Q(awayteam=team, season=seazn)).exclude(result__exact='').exclude(result__isnull=True).order_by('-gameweek')
        last_gameweek = qry[0].gameweek
        return last_gameweek

    def team_total_wins(self, team, seazn, gw):
        qryset = self.filter(Q(hometeam=team, season=seazn, gameweek__lte=gw) | Q(awayteam=team, season=seazn, gameweek__lte=gw))
        total_wins = 0
        for g in qryset:
            if g.hometeam == team:
                if g.result == 'HOME':
                    total_wins += 1
            elif g.awayteam == team:
                if g.result == 'AWAY':
                    total_wins += 1
        return total_wins

    def team_total_losses(self, team, seazn, gw):
        qryset = self.filter(Q(hometeam=team, season=seazn, gameweek__lte=gw) | Q(awayteam=team, season=seazn, gameweek__lte=gw))
        total_losses = 0
        for g in qryset:
            if g.hometeam == team:
                if g.result == 'AWAY':
                    total_losses += 1
            elif g.awayteam == team:
                if g.result == 'HOME':
                    total_losses += 1
        return total_losses

    def team_total_draws(self, team, seazn, gw):
        qryset = self.filter(Q(hometeam=team, season=seazn, gameweek__lte=gw) | Q(awayteam=team, season=seazn, gameweek__lte=gw))
        total_draws = 0
        for g in qryset:
            if g.result == 'DRAW':
                total_draws += 1
        return total_draws

    def team_total_goals_scored(self, team, seazn, gw):
        qryset = self.filter(Q(hometeam=team, season=seazn, gameweek__lte=gw) | Q(awayteam=team, season=seazn, gameweek__lte=gw)).exclude(result__exact='').exclude(result__isnull=True)
        total_homegoals = 0
        total_awaygoals = 0
        for g in qryset:
            if g.hometeam == team:
                total_homegoals += g.homegoals
            elif g.awayteam == team:
                total_awaygoals += g.awaygoals
        return total_homegoals + total_awaygoals

    def team_total_goals_conceded(self, team, seazn, gw):
        qryset = self.filter(Q(hometeam=team, season=seazn, gameweek__lte=gw) | Q(awayteam=team, season=seazn, gameweek__lte=gw)).exclude(result__exact='').exclude(result__isnull=True)
        total_homegoals = 0
        total_awaygoals = 0
        for g in qryset:
            if g.hometeam == team:
                total_homegoals += g.awaygoals
            elif g.awayteam == team:
                total_awaygoals += g.homegoals
        return total_homegoals + total_awaygoals

    # total points won/lost by a team at home
    def team_total_home_points(self, team, sz, gmwk):
        qset = self.filter(hometeam=team, season=sz, gameweek__lt=gmwk).order_by('gameweek')
        points = 0.0
        if gmwk == 1:
                points = elosettings.STARTING_POINTS - self.get_previous_elo(team, sz, gmwk)
        else:
            for gm in qset:
                if gm.gameweek == 1:
                    points += gm.elo_rating_home - elosettings.STARTING_POINTS
                else:
                    points += gm.elo_rating_home - self.get_previous_elo(team, sz, gm.gameweek)
        return points

    # total points won/lost by a team away
    def team_total_away_points(self, team, sz, gmwk):
        qset = self.filter(awayteam=team, season=sz, gameweek__lt=gmwk).order_by('gameweek')
        points = 0.0
        if gmwk == 1:
                points = elosettings.STARTING_POINTS - self.get_previous_elo(team, sz, gmwk)
        else:
            for gm in qset:
                if gm.gameweek == 1:
                    points += gm.elo_rating_away - elosettings.STARTING_POINTS
                else:
                    points += gm.elo_rating_away - self.get_previous_elo(team, sz, gm.gameweek)
        return points

    # total games played for the given season
    def total_season_games_played(self, sznn):
        qrset = self.filter(season=sznn).exclude(homegoals__isnull=True).count()
        return qrset

    # total games that will be played for the given season
    def total_season_games(self, seasonn):
        games_per_gameweek = self.filter(season=seasonn, gameweek=1).count()
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

    def over_two_half(self, seasonn):
        qrset = self.filter(season=seasonn).exclude(result__exact='').exclude(result__isnull=True).annotate(diff=Sum(F('homegoals') + F('awaygoals')))
        cntr = 0
        for itemm in qrset:
            if itemm.diff > 2:
                cntr += 1
        return cntr

    def over_three_half(self, seasonn):
        qrset = self.filter(season=seasonn).exclude(result__exact='').exclude(result__isnull=True).annotate(diff=Sum(F('homegoals') + F('awaygoals')))
        cntr = 0
        for itemm in qrset:
            if itemm.diff > 3:
                cntr += 1
        return cntr

    def team_total_cleansheets(self, team, seasonn, gwk):
        qrst = self.filter(Q(hometeam=team, season=seasonn, gameweek__lt=gwk) | Q(awayteam=team, season=seasonn, gameweek__lt=gwk))
        qrst_clean = qrst.exclude(result__exact='').exclude(result__isnull=True)
        cnt = 0
        for gm in qrst_clean:
            if gm.hometeam == team and gm.awaygoals == 0:
                cnt += 1
            if gm.awayteam == team and gm.homegoals == 0:
                cnt += 1
        return cnt

    def team_total_failedtoscore(self, team, seasonn, gwk):
        qrst = self.filter(Q(hometeam=team, season=seasonn, gameweek__lt=gwk) | Q(awayteam=team, season=seasonn, gameweek__lt=gwk))
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
        qs_total = ''
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
        qs = self.filter(season__id=seasonid, gameweek__gte=7).exclude(prediction_status_elohist__exact='').exclude(prediction_status_elohist__isnull=True)
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
        allseasons = Season.objects.filter(end_date__year=year).values_list('id', flat=True)
        strike_rates_list = []
        for season in allseasons:
            strike_rates_list.append({
                'id': season,
                'strike_rate': self.model_strike_rate(model, season, prediction),
                'country': Season.objects.get(id=season).league.country,
                'country_code': Season.objects.get(id=season).league.country_code,
                'league_name': Season.objects.get(id=season).league.league_name
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

    date = models.DateField()
    gameweek = models.PositiveIntegerField()
    season = models.ForeignKey('Season')
    game_status = models.CharField(max_length=10, choices=GAME_STATUS_CHOICES, default=ok,)
    hometeam = models.ForeignKey(Team, related_name='hometeam')
    awayteam = models.ForeignKey(Team, related_name='awayteam')
    homegoals = models.IntegerField(null=True, blank=True)
    awaygoals = models.IntegerField(null=True, blank=True)
    result = models.CharField(max_length=5, null=True, blank=True)
    elo_rating_home = models.FloatField(null=True, blank=True)
    elo_rating_away = models.FloatField(null=True, blank=True)
    elo_rating_home_previous_week = models.FloatField(null=True, blank=True)
    elo_rating_away_previous_week = models.FloatField(null=True, blank=True)
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
        home_sa = 0.00
        if self.gameweek == 1:
            away_r_old = elosettings.STARTING_POINTS
            home_r_old = elosettings.STARTING_POINTS
            home_sa = 1 / (1 + 10 ** ((away_r_old - home_r_old - elosettings.ELO_HGA) / float(elosettings.ELO_S)))
        elif self.gameweek > 1:
            away_r_old = self._default_manager.get_previous_elo(tm=self.awayteam, seasn=self.season, gmwk=self.gameweek)
            home_r_old = self._default_manager.get_previous_elo(tm=self.hometeam, seasn=self.season, gmwk=self.gameweek)
            previous_gw = self.gameweek - 1
            home_ground_adv = self._default_manager.modified_hga(teamm=self.hometeam, seasonn=self.season, gmwk=self.gameweek)
            home_sa = 1 / (1 + 10 ** ((away_r_old - home_r_old - home_ground_adv) / float(elosettings.ELO_S)))
        return home_sa

    def away_se(self):
        hmscore = self.home_se()
        away_sa = 1 - hmscore
        return away_sa

    def r_new_home(self):
        if self.homegoals >= 0:
            r_old = self._default_manager.get_previous_elo(tm=self.hometeam, seasn=self.season, gmwk=self.gameweek)
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
            r_old = self._default_manager.get_previous_elo(tm=self.awayteam, seasn=self.season, gmwk=self.gameweek)
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

    def elo_hist_prediction_status(self):
        if self.homegoals >= 0:
            prediction = self._default_manager.elo_hist_prediction(hometm=self.hometeam, awaytm=self.awayteam, szn=self.season.id, gweek=self.gameweek)
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
            prediction = self._default_manager.elo_l6_prediction(hometm=self.hometeam, awaytm=self.awayteam, szn=self.season.id, gweek=self.gameweek)
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
            prediction = self._default_manager.gsrs_prediction(hm=self.hometeam, aw=self.awayteam, sn=self.season.id, gmwkk=self.gameweek)
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

        self.elo_rating_home = self.r_new_home()
        self.elo_rating_away = self.r_new_away()

        self.elo_rating_home_previous_week = self._default_manager.get_previous_elo(self.hometeam, self.season, self.gameweek)
        self.elo_rating_away_previous_week = self._default_manager.get_previous_elo(self.awayteam, self.season, self.gameweek)

        self.rdiff = self.r_difference()
        self.goaldiff_hm = self._default_manager.total_goal_diff(self.hometeam, self.season.id, self.gameweek)
        self.goaldiff_aw = self._default_manager.total_goal_diff(self.awayteam, self.season.id, self.gameweek)

        self.prediction_elohist = self._default_manager.elo_hist_prediction(hometm=self.hometeam, awaytm=self.awayteam, szn=self.season.id, gweek=self.gameweek)
        self.prediction_status_elohist = self.elo_hist_prediction_status()

        self.prediction_elol6 = self._default_manager.elo_l6_prediction(hometm=self.hometeam, awaytm=self.awayteam, szn=self.season.id, gweek=self.gameweek)
        self.prediction_status_elol6 = self.elo_l6_prediction_status()

        self.prediction_gsrs = self._default_manager.gsrs_prediction(hm=self.hometeam, aw=self.awayteam, sn=self.season.id, gmwkk=self.gameweek)
        self.prediction_status_gsrs = self.gsrs_prediction_status()
        super(Game, self).save(*args, **kwargs)

    def __str__(self):
        return str(self.date) + " " + str(self.hometeam) + " vs " + str(self.awayteam)


class GameFilter(django_filters.FilterSet):

    class Meta:
        model = Game
        fields = ['gameweek']


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
