from __future__ import unicode_literals
from django.db import models
from django.utils import timezone
from django.db.models import Q, Max, Sum, F
# from decimal import Decimal, ROUND_HALF_UP, ROUND_HALF_DOWN
import django_filters
from django.conf import settings


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
            sn_lst.append([str(item), item.id, str(item.league.league_name), str(item.get_start_year()), str(item.get_end_year()), str(item.end_date)])
        return sn_lst


class Season(models.Model):
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    league = models.ForeignKey('Leagues', to_field='short_name', null=True, related_name='league')
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
            out = settings.STARTING_POINTS
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
        total_home_wins = self.filter(season=seasonn, hometeam=teamm, gameweek__lte=gmwk-1, result='HOME').count()
        total_home_draws = self.filter(season=seasonn, hometeam=teamm, gameweek__lte=gmwk-1, result='DRAW').count()
        win_points = total_home_wins * 1
        draw_points = total_home_draws * 0.5
        total_games = self.filter(hometeam=teamm, season=seasonn, gameweek__lte=gmwk-1).count()
        if total_games == 0 or gmwk == 1:
            mhga = settings.ELO_HGA
        else:
            strike_rate = (win_points + draw_points)/total_games
            mhga = strike_rate * float(settings.ELO_HGA)
        return mhga

    def elo_draw_threshold(self, seasonn, gamewk):
        if gamewk == 1:
            out = 0
        else:
            games_lst = self.filter(season=seasonn, gameweek__lte=gamewk - 1)
            szn = Season.objects.get(id=seasonn)
            multiplier = -szn.league.teamstotal / 2
            x = []
            for gm in games_lst:
                h_r_old = self.get_previous_elo(tm=gm.hometeam, seasn=seasonn, gmwk=gm.gameweek)
                a_r_old = self.get_previous_elo(tm=gm.awayteam, seasn=seasonn, gmwk=gm.gameweek)
                rdiff = round(h_r_old - a_r_old, 0)
                x.append(rdiff)
            out = abs(sum(x) / games_lst.count()) * multiplier
        return out

    def elol6_draw_threshold(self, seasonn, gamewk):
        x = []
        if gamewk <= 7:
            out = 0
        else:
            games_lst = self.filter(season=seasonn, gameweek__lte=gamewk - 1, gameweek__gte=7)
            szn = Season.objects.get(id=seasonn)
            multiplier = -szn.league.teamstotal / 2
            x = []
            for gm in games_lst:
                h_r_old = self.get_previous_elo(tm=gm.hometeam, seasn=seasonn, gmwk=gm.gameweek) - self.get_previous_elo(tm=gm.hometeam, seasn=seasonn, gmwk=gm.gameweek - 5)
                a_r_old = self.get_previous_elo(tm=gm.awayteam, seasn=seasonn, gmwk=gm.gameweek) - self.get_previous_elo(tm=gm.awayteam, seasn=seasonn, gmwk=gm.gameweek - 5)
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
            multiplier = -szn.league.teamstotal / 2
            for gm in games_lst:
                hm_goal_diff = self.total_goal_diff(tm=gm.hometeam, seasn=gm.season.id, gw=gm.gameweek)
                aw_goal_diff = self.total_goal_diff(tm=gm.awayteam, seasn=gm.season.id, gw=gm.gameweek)
                gm_goal_diff = hm_goal_diff - aw_goal_diff
                x.append(gm_goal_diff)
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
            draw_threshold = self.elo_draw_threshold(seasonn=szn, gamewk=gweek)
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
                    x = ""
            elif lst.awayteam == team:
                if lst.result == 'HOME':
                    x = "L"
                elif lst.result == 'AWAY':
                    x = "W"
                elif lst.result == 'DRAW':
                    x = "D"
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
                points = settings.STARTING_POINTS - self.get_previous_elo(team, sz, gmwk)
        else:
            for gm in qset:
                if gm.gameweek == 1:
                    points += gm.elo_rating_home - settings.STARTING_POINTS
                else:
                    points += gm.elo_rating_home - self.get_previous_elo(team, sz, gm.gameweek)
        return points

    # total points won/lost by a team away
    def team_total_away_points(self, team, sz, gmwk):
        qset = self.filter(awayteam=team, season=sz, gameweek__lt=gmwk).order_by('gameweek')
        points = 0.0
        if gmwk == 1:
                points = settings.STARTING_POINTS - self.get_previous_elo(team, sz, gmwk)
        else:
            for gm in qset:
                if gm.gameweek == 1:
                    points += gm.elo_rating_away - settings.STARTING_POINTS
                else:
                    points += gm.elo_rating_away - self.get_previous_elo(team, sz, gm.gameweek)
        return points

    # total games played for the given season
    def total_season_games_played(self, sznn):
        qrset = self.filter(season=sznn).exclude(homegoals__isnull=True).count()
        return qrset

    # total games that will be played for the given season
    def total_season_games(self,seasonn):
        games_per_gameweek = self.filter(season=seasonn, gameweek=1).count()
        ttl_teams = games_per_gameweek*2
        ttl_gameweeks = (ttl_teams-1)*2
        ttl_games = ttl_gameweeks*games_per_gameweek
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
                qs = self.filter(season=seasonidd).exclude(prediction_status_elohist__exact='').exclude(prediction_status_elohist__isnull=True).values('prediction_status_elohist')
            elif model == 'elol6':
                qs = self.filter(season=seasonidd).exclude(prediction_status_elol6__exact='').exclude(prediction_status_elol6__isnull=True).values('prediction_status_elol6')
            elif model == 'gsrs':
                qs = self.filter(season=seasonidd).exclude(prediction_status_gsrs__exact='').exclude(prediction_status_gsrs__isnull=True).values('prediction_status_gsrs')
            else:
                qs = ""
        else:
            if model == 'elohist':
                qs = self.exclude(prediction_status_elohist__exact='').exclude(prediction_status_elohist__isnull=True).values('prediction_status_elohist')
            elif model == 'elol6':
                qs = self.exclude(prediction_status_elol6__exact='').exclude(prediction_status_elol6__isnull=True).values('prediction_status_elol6')
            elif model == 'gsrs':
                qs = self.exclude(prediction_status_gsrs__exact='').exclude(prediction_status_gsrs__isnull=True).values('prediction_status_gsrs')
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

        if model == 'elohist':
            qs = filtered_qs .exclude(prediction_status_elohist__exact='').exclude(prediction_status_elohist__isnull=True).values('prediction_status_elohist')
        elif model == 'elol6':
            qs = filtered_qs .exclude(prediction_status_elol6__exact='').exclude(prediction_status_elol6__isnull=True).values('prediction_status_elol6')
        elif model == 'gsrs':
            qs = filtered_qs .exclude(prediction_status_gsrs__exact='').exclude(prediction_status_gsrs__isnull=True).values('prediction_status_gsrs')
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
                qs = self.filter(season=seasonidd).exclude(prediction_status_elohist__exact='').exclude(prediction_status_elohist__isnull=True).values('prediction_status_elohist')
            elif model == 'elol6':
                qs = self.filter(season=seasonidd).exclude(prediction_status_elol6__exact='').exclude(prediction_status_elol6__isnull=True).values('prediction_status_elol6')
            elif model == 'gsrs':
                qs = self.filter(season=seasonidd).exclude(prediction_status_gsrs__exact='').exclude(prediction_status_gsrs__isnull=True).values('prediction_status_gsrs')
            else:
                qs = ""
        else:
            if model == 'elohist':
                qs = self.exclude(prediction_status_elohist__exact='').exclude(prediction_status_elohist__isnull=True).values('prediction_status_elohist')
            elif model == 'elol6':
                qs = self.exclude(prediction_status_elol6__exact='').exclude(prediction_status_elol6__isnull=True).values('prediction_status_elol6')
            elif model == 'gsrs':
                qs = self.exclude(prediction_status_gsrs__exact='').exclude(prediction_status_gsrs__isnull=True).values('prediction_status_gsrs')
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

        if model == 'elohist':
            qs = filtered_qs .exclude(prediction_status_elohist__exact='').exclude(prediction_status_elohist__isnull=True).values('prediction_status_elohist')
        elif model == 'elol6':
            qs = filtered_qs .exclude(prediction_status_elol6__exact='').exclude(prediction_status_elol6__isnull=True).values('prediction_status_elol6')
        elif model == 'gsrs':
            qs = filtered_qs .exclude(prediction_status_gsrs__exact='').exclude(prediction_status_gsrs__isnull=True).values('prediction_status_gsrs')
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


class Game(models.Model):
    date = models.DateField()
    gameweek = models.PositiveIntegerField()
    season = models.ForeignKey('Season')
    hometeam = models.ForeignKey(Team, related_name='hometeam')
    awayteam = models.ForeignKey(Team, related_name='awayteam')
    homegoals = models.IntegerField(null=True, blank=True)
    awaygoals = models.IntegerField(null=True, blank=True)
    result = models.CharField(max_length=5, null=True, blank=True)
    elo_rating_home = models.FloatField(null=True, blank=True)
    elo_rating_away = models.FloatField(null=True, blank=True)
    prediction_elohist = models.CharField(max_length=80, null=True, blank=True)
    prediction_status_elohist = models.CharField(max_length=80, null=True, blank=True)
    prediction_elol6 = models.CharField(max_length=80, null=True, blank=True)
    prediction_status_elol6 = models.CharField(max_length=80, null=True, blank=True)
    prediction_gsrs = models.CharField(max_length=80, null=True, blank=True)
    prediction_status_gsrs = models.CharField(max_length=80, null=True, blank=True)
    objects = GameManager()

    # # ELO SETTINGS MOVED TO SETTINGS.PY
    # ELO_HGA = 65  # Home ground advantage factor. You can set it to 0 if you don't want to add it as a factor in the calculations
    # ELO_S = 400  # S is a scaling parameter that controls the extent to which a team's Ratings deficit, net of any
    # # Home Ground Advantage, is translated into expected performance. Larger values of S mean that
    # # a team's Expected share of points scored responds more slowly to any given Ratings deficit or surplus
    # # net of Home Ground Advantage, while smaller values of S mean the opposite.
    # STARTING_POINTS = 1500
    # ELO_K = 20

    def get_k_factor(self):
        k = settings.ELO_K
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
            away_r_old = settings.STARTING_POINTS
            home_r_old = settings.STARTING_POINTS
            home_sa = 1 / (1 + 10 ** ((away_r_old - home_r_old - settings.ELO_HGA) / float(settings.ELO_S)))
        elif self.gameweek > 1:
            away_r_old = self._default_manager.get_previous_elo(tm=self.awayteam, seasn=self.season, gmwk=self.gameweek)
            home_r_old = self._default_manager.get_previous_elo(tm=self.hometeam, seasn=self.season, gmwk=self.gameweek)
            previous_gw = self.gameweek - 1
            home_ground_adv = self._default_manager.modified_hga(teamm=self.hometeam, seasonn=self.season, gmwk=self.gameweek)
            home_sa = 1 / (1 + 10 ** ((away_r_old - home_r_old - home_ground_adv) / float(settings.ELO_S)))
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
            if self.hometeam == tms.awayteam:
                rating = tms.elo_rating_home
            else:
                rating = tms.elo_rating_away
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
