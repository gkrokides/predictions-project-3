from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from .models import Post, Team, Game, Season, GameFilter, Leagues, GameSeasonFilter, Tip, Betslip
from .forms import PostForm, GameForm, ContactForm, TipForm, BetslipForm
from dicts.sorteddict import ValueSortedDict
from decimal import Decimal
from django.db.models import Q, F, Sum, Max
from operator import itemgetter
from django.conf import settings
from datetime import datetime, timedelta
import json
from django.forms import modelformset_factory
from django import forms
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.core.mail import send_mail, BadHeaderError
from django.http import HttpResponse, HttpResponseRedirect

# from django.db.models import Count

# from itertools import  chain
# from django.db.models import Q, Max


def post_list(request):
    posts = Post.objects.filter(published_date__lte=timezone.now()).order_by('-published_date')
    return render(request, 'predictions/post_list.html', {'posts': posts})


def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    return render(request, 'predictions/post_detail.html', {'post': post})


def post_new(request):
    if request.method == "POST":
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.published_date = timezone.now()
            post.save()
            return redirect('post_detail', pk=post.pk)
    else:
        form = PostForm()
    return render(request, 'predictions/post_new.html', {'form': form})


def post_edit(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.method == "POST":
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.published_date = timezone.now()
            post.save()
            return redirect('post_detail', pk=post.pk)
    else:
        form = PostForm(instance=post)
    return render(request, 'predictions/post_edit.html', {'form': form})


def predictions_filter(request):
    gfilter = GameFilter(request.GET, queryset=Game.objects.all().exclude(prediction_status_elohist__isnull=True).exclude(prediction_status_elohist__exact='').order_by('date'))
    return render(request, 'predictions/predictions_filtered.html', {'gfilter': gfilter})


def past_predictions(request, seasonid):
    gfilter = GameFilter(request.GET, queryset=Game.objects.filter(season=seasonid).exclude(prediction_status_elohist__isnull=True).exclude(prediction_status_elohist__exact='').order_by('-gameweek'))
    predicted_games = gfilter.count()
    return render(request, 'predictions/past_predictions.html', {'gfilter': gfilter, 'predicted_games': predicted_games})


def h2h(request, pk):
    gm = get_object_or_404(Game, pk=pk)
    # season = Season.objects.get(id=2)
    gmscount = 0
    season = gm.season
    gamewk = gm.gameweek + 1
    gamewk_for_title = gamewk - 2
    hometm = gm.hometeam
    awaytm = gm.awayteam
    leaderboard = Game.objects.last_gameweek(seasn=season)
    # gamewk = leaderboard[0].gameweek
    x = {}
    for tm in leaderboard:
        h = tm.hometeam
        a = tm.awayteam
        x.update({h: round(Decimal(Game.objects.get_previous_elo_by_actual_date(tm=tm.hometeam, seasn=season, dt=gm.date, gw=gm.gameweek)), 2)})
        x.update({a: round(Decimal(Game.objects.get_previous_elo_by_actual_date(tm=tm.awayteam, seasn=season, dt=gm.date, gw=gm.gameweek)), 2)})
    sorted_x = ValueSortedDict(x, reverse=True)
    hmteam_all = Game.objects.filter(Q(hometeam=gm.hometeam, date__lt=gm.date, season=gm.season) | Q(awayteam=gm.hometeam, date__lt=gm.date, season=gm.season)).order_by('date')
    awteam_all = Game.objects.filter(Q(hometeam=gm.awayteam, date__lt=gm.date, season=gm.season) | Q(awayteam=gm.awayteam, date__lt=gm.date, season=gm.season)).order_by('date')
    # last 6 games of each team--------------------------------------------
    # formstart = gm.gameweek - 6
    # formend = gm.gameweek
    hm_formstart = hmteam_all.reverse()[5].date
    hm_formend = hmteam_all.reverse()[0].date
    aw_formstart = awteam_all.reverse()[5].date
    aw_formend = awteam_all.reverse()[0].date
    homeform = []
    awayform = []
    home_iterset = hmteam_all.filter(date__gte=hm_formstart, date__lte=hm_formend).order_by('date')
    away_iterset = awteam_all.filter(date__gte=aw_formstart, date__lte=aw_formend).order_by('date')
    for mtch in home_iterset:
        homeform.append(Game.objects.team_form_by_date(hometm, season.id, mtch.gameweek))
    for mtchh in away_iterset:
        awayform.append(Game.objects.team_form_by_date(awaytm, season.id, mtchh.gameweek))
    # for i in range(formstart, formend):
    #     homeform.append(Game.objects.team_form(hometm, season.id, i))
    # for i in range(formstart, formend):
    #     awayform.append(Game.objects.team_form(awaytm, season.id, i))
    # Line chart data ------------------------------------------
    homename = str(gm.hometeam)
    awayname = str(gm.awayteam)
    # hmteam_all = Game.objects.filter(Q(hometeam=gm.hometeam, date__lt=gm.date, season=gm.season) | Q(awayteam=gm.hometeam, date__lt=gm.date, season=gm.season)).order_by('date')
    # awteam_all = Game.objects.filter(Q(hometeam=gm.awayteam, date__lt=gm.date, season=gm.season) | Q(awayteam=gm.awayteam, date__lt=gm.date, season=gm.season)).order_by('date')
    # hmteam_all = Game.objects.filter(Q(hometeam=gm.hometeam, gameweek__lt=gm.gameweek, season=gm.season) | Q(awayteam=gm.hometeam, gameweek__lt=gm.gameweek, season=gm.season)).order_by('gameweek')
    # awteam_all = Game.objects.filter(Q(hometeam=gm.awayteam, gameweek__lt=gm.gameweek, season=gm.season) | Q(awayteam=gm.awayteam, gameweek__lt=gm.gameweek, season=gm.season)).order_by('gameweek')
    gweeks = []
    home_elos = []
    away_elos = []
    chart_data = [
        ['Gameweek', homename, awayname],
        [0, settings.STARTING_POINTS, settings.STARTING_POINTS]
    ]
    for g in hmteam_all:
        gmscount += 1
        gweeks.append(gmscount)
    for h in hmteam_all:
        if h.hometeam == gm.hometeam:
            home_elos.append(h.elo_rating_home)
        else:
            home_elos.append(h.elo_rating_away)
    for a in awteam_all:
        if a.hometeam == gm.awayteam:
            away_elos.append(a.elo_rating_home)
        else:
            away_elos.append(a.elo_rating_away)
    # if gm.gameweek < 2:
    #     chart_data = chart_data
    # else:
    #     for g in range(0, gm.gameweek - 1):
    #         templist = [gweeks[g], home_elos[g], away_elos[g]]
    #         chart_data.append(templist)
    for g in range(0, hmteam_all.count()):
        # since I chose to go with the hometeam's data, and since gameweeks are built according to hometeam
        # i need to handle the list index out of range for the away team in case it has less games
        try:
            aelos = away_elos[g]
        except IndexError:
            aelos = away_elos[-1] #return the last value of the list
        templist = [gweeks[g], home_elos[g], aelos]
        chart_data.append(templist)
    # gweeks = []
    # home_elos = []
    # away_elos = []
    # chart_data = [
    #     ['Gameweek', homename, awayname],
    #     [0, settings.STARTING_POINTS, settings.STARTING_POINTS]
    # ]
    # for g in hmteam_all:
    #     gweeks.append(g.gameweek)
    # for h in hmteam_all:
    #     if h.hometeam == gm.hometeam:
    #         home_elos.append(h.elo_rating_home)
    #     else:
    #         home_elos.append(h.elo_rating_away)
    # for a in awteam_all:
    #     if a.hometeam == gm.awayteam:
    #         away_elos.append(a.elo_rating_home)
    #     else:
    #         away_elos.append(a.elo_rating_away)
    # if gm.gameweek < 2:
    #     chart_data = chart_data
    # else:
    #     for g in range(0, gm.gameweek - 1):
    #         templist = [gweeks[g], home_elos[g], away_elos[g]]
    #         chart_data.append(templist)
    # donut charts data ------------------------------------------
    homewins = Game.objects.team_total_wins_by_date_ex_current(hometm, season.id, gm.gameweek)
    homewins_at_home = Game.objects.team_total_wins_home(hometm, season.id, gm.date)
    homewins_at_away = Game.objects.team_total_wins_away(hometm, season.id, gm.date)

    awaywins = Game.objects.team_total_wins_by_date_ex_current(awaytm, season.id, gm.gameweek)
    awaywins_at_home = Game.objects.team_total_wins_home(awaytm, season.id, gm.date)
    awaywins_at_away = Game.objects.team_total_wins_away(awaytm, season.id, gm.date)

    homelosses = Game.objects.team_total_losses_by_date_ex_current(hometm, season.id, gm.gameweek)
    homelosses_at_home = Game.objects.team_total_losses_home(hometm, season.id, gm.date)
    homelosses_at_away = Game.objects.team_total_losses_away(hometm, season.id, gm.date)

    awaylosses = Game.objects.team_total_losses_by_date_ex_current(awaytm, season.id, gm.gameweek)
    awaylosses_at_home = Game.objects.team_total_losses_home(awaytm, season.id, gm.date)
    awaylosses_at_away = Game.objects.team_total_losses_away(awaytm, season.id, gm.date)

    homedraws = Game.objects.team_total_draws_by_date_ex_current(hometm, season.id, gm.gameweek)
    homedraws_at_home = Game.objects.team_total_draws_home(hometm, season.id, gm.date)
    homedraws_at_away = Game.objects.team_total_draws_away(hometm, season.id, gm.date)

    awaydraws = Game.objects.team_total_draws_by_date_ex_current(awaytm, season.id, gm.gameweek)
    awaydraws_at_home = Game.objects.team_total_draws_home(awaytm, season.id, gm.date)
    awaydraws_at_away = Game.objects.team_total_draws_away(awaytm, season.id, gm.date)
    # SCORING TABLE DATA ------------------------------------------
    # HOME TEAM ALL GAMES -------------------------
    homeset = Game.objects.filter(Q(hometeam=gm.hometeam, season=gm.season.id, date__lt=gm.date) |
                                  Q(awayteam=gm.hometeam, season=gm.season.id, date__lt=gm.date))
    homefor = Game.objects.team_total_goals_scored_by_date_ex_current(hometm, season.id, gm.gameweek)
    homeagainst = Game.objects.team_total_goals_conceded_by_date_ex_current(hometm, season.id, gm.gameweek)
    home_total_games = homeset.exclude(result__exact='').exclude(result__isnull=True).count()
    try:
        home_scored_p_game = homefor / float(home_total_games)
    except ZeroDivisionError:
        home_scored_p_game = 0
    try:
        home_conceded_p_game = homeagainst / float(home_total_games)
    except ZeroDivisionError:
        home_conceded_p_game = 0
    homeset_with_results = homeset.exclude(result__exact='').exclude(result__isnull=True).annotate(diff=Sum(F('homegoals') + F('awaygoals')))
    home_over2p5_all = 0
    home_over2p5_all_pcnt = 0.0
    home_over3p5_all = 0
    home_over3p5_all_pcnt = 0.0
    home_over4p5_all = 0
    home_over4p5_all_pcnt = 0.0
    home_gg_all = 0
    home_gg_all_pcnt = 0.0
    home_cleansheets_all = Game.objects.team_total_cleansheets_by_date(gm.hometeam, gm.season.id, gm.date)
    home_cleansheets_all_pcnt = 0.0
    home_failedtoscore_all = Game.objects.team_total_failedtoscore_by_date(gm.hometeam, gm.season.id, gm.date)
    home_failedtoscore_all_pcnt = 0.0
    for gmm in homeset_with_results:
        if gmm.diff > 2.5:
            home_over2p5_all += 1
        if gmm.diff > 3.5:
            home_over3p5_all += 1
        if gmm.diff > 4.5:
            home_over4p5_all += 1
        if gmm.homegoals > 0 and gmm.awaygoals > 0:
            home_gg_all += 1
        # if gmm.awaygoals == 0:
        #     home_cleansheets_all += 1
        # if gmm.homegoals == 0:
        #     home_failedtoscore_all += 1
    try:
        home_over2p5_all_pcnt = home_over2p5_all / float(home_total_games) * 100
    except ZeroDivisionError:
        home_over2p5_all_pcnt = 0
    try:
        home_over3p5_all_pcnt = home_over3p5_all / float(home_total_games) * 100
    except ZeroDivisionError:
        home_over3p5_all_pcnt = 0
    try:
        home_over4p5_all_pcnt = home_over4p5_all / float(home_total_games) * 100
    except ZeroDivisionError:
        home_over4p5_all_pcnt = 0
    try:
        home_gg_all_pcnt = home_gg_all / float(home_total_games) * 100
    except ZeroDivisionError:
        home_gg_all_pcnt = 0
    try:
        home_cleansheets_all_pcnt = home_cleansheets_all / float(home_total_games) * 100
    except ZeroDivisionError:
        home_cleansheets_all_pcnt = 0
    try:
        home_failedtoscore_all_pcnt = home_failedtoscore_all / float(home_total_games) * 100
    except ZeroDivisionError:
        home_failedtoscore_all_pcnt = 0
    # HOME TEAM HOME GAMES ----------------------------------------------------------
    homeset_hm = Game.objects.filter(hometeam=gm.hometeam, season=gm.season.id, date__lt=gm.date)
    # because the aggregation function returns a dictionary, the last part ['homefor_home'] is used to retrieve only the number
    homefor_hm = homeset_hm.aggregate(homefor_home=Sum('homegoals'))['homefor_home']
    homeagainst_hm = homeset_hm.aggregate(homeagainst_home=Sum('awaygoals'))['homeagainst_home']
    home_total_games_hm = homeset_hm.exclude(result__exact='').exclude(result__isnull=True).count()
    try:
        home_scored_p_game_hm = homefor_hm / float(home_total_games_hm)
    except ZeroDivisionError:
        home_scored_p_game_hm = 0
    try:
        home_conceded_p_game_hm = homeagainst_hm / float(home_total_games_hm)
    except ZeroDivisionError:
        home_conceded_p_game_hm = 0
    homeset_with_results_hm = homeset_hm.exclude(result__exact='').exclude(result__isnull=True).annotate(diff=Sum(F('homegoals') + F('awaygoals')))
    home_over2p5_all_hm = 0
    home_over2p5_all_pcnt_hm = 0.0
    home_over3p5_all_hm = 0
    home_over3p5_all_pcnt_hm = 0.0
    home_over4p5_all_hm = 0
    home_over4p5_all_pcnt_hm = 0.0
    home_gg_all_hm = 0
    home_gg_all_pcnt_hm = 0.0
    home_cleansheets_all_hm = 0
    home_cleansheets_all_pcnt_hm = 0.0
    home_failedtoscore_all_hm = 0
    home_failedtoscore_all_pcnt_hm = 0.0
    for gmmm in homeset_with_results_hm:
        if gmmm.diff > 2.5:
            home_over2p5_all_hm += 1
        if gmmm.diff > 3.5:
            home_over3p5_all_hm += 1
        if gmmm.diff > 4.5:
            home_over4p5_all_hm += 1
        if gmmm.homegoals > 0 and gmmm.awaygoals > 0:
            home_gg_all_hm += 1
        if gmmm.awaygoals == 0:
            home_cleansheets_all_hm += 1
        if gmmm.homegoals == 0:
            home_failedtoscore_all_hm += 1
    try:
        home_over2p5_all_pcnt_hm = home_over2p5_all_hm / float(home_total_games_hm) * 100
    except ZeroDivisionError:
        home_over2p5_all_pcnt_hm = 0
    try:
        home_over3p5_all_pcnt_hm = home_over3p5_all_hm / float(home_total_games_hm) * 100
    except ZeroDivisionError:
        home_over3p5_all_pcnt_hm = 0
    try:
        home_over4p5_all_pcnt_hm = home_over4p5_all_hm / float(home_total_games_hm) * 100
    except ZeroDivisionError:
        home_over4p5_all_pcnt_hm = 0
    try:
        home_gg_all_pcnt_hm = home_gg_all_hm / float(home_total_games_hm) * 100
    except ZeroDivisionError:
        home_gg_all_pcnt_hm = 0
    try:
        home_cleansheets_all_pcnt_hm = home_cleansheets_all_hm / float(home_total_games_hm) * 100
    except ZeroDivisionError:
        home_cleansheets_all_pcnt_hm = 0
    try:
        home_failedtoscore_all_pcnt_hm = home_failedtoscore_all_hm / float(home_total_games_hm) * 100
    except ZeroDivisionError:
        home_failedtoscore_all_pcnt_hm = 0
    # HOME TEAM AWAY GAMES ----------------------------------------------------------
    homeset_aw = Game.objects.filter(awayteam=gm.hometeam, season=gm.season.id, date__lt=gm.date)
    # because the aggregation function returns a dictionary, the last part ['homefor_home'] is used to retrieve only the number
    homefor_aw = homeset_aw.aggregate(homefor_away=Sum('awaygoals'))['homefor_away']
    homeagainst_aw = homeset_aw.aggregate(homeagainst_away=Sum('homegoals'))['homeagainst_away']
    home_total_games_aw = homeset_aw.exclude(result__exact='').exclude(result__isnull=True).count()
    home_scored_p_game_aw = homefor_aw / float(home_total_games_aw)
    home_conceded_p_game_aw = homeagainst_aw / float(home_total_games_aw)
    homeset_with_results_aw = homeset_aw.exclude(result__exact='').exclude(result__isnull=True).annotate(diff=Sum(F('homegoals') + F('awaygoals')))
    home_over2p5_all_aw = 0
    home_over2p5_all_pcnt_aw = 0.0
    home_over3p5_all_aw = 0
    home_over3p5_all_pcnt_aw = 0.0
    home_over4p5_all_aw = 0
    home_over4p5_all_pcnt_aw = 0.0
    home_gg_all_aw = 0
    home_gg_all_pcnt_aw = 0.0
    home_cleansheets_all_aw = 0
    home_cleansheets_all_pcnt_aw = 0.0
    home_failedtoscore_all_aw = 0
    home_failedtoscore_all_pcnt_aw = 0.0
    for gammm in homeset_with_results_aw:
        if gammm.diff > 2.5:
            home_over2p5_all_aw += 1
        if gammm.diff > 3.5:
            home_over3p5_all_aw += 1
        if gammm.diff > 4.5:
            home_over4p5_all_aw += 1
        if gammm.homegoals > 0 and gammm.awaygoals > 0:
            home_gg_all_aw += 1
        if gammm.homegoals == 0:
            home_cleansheets_all_aw += 1
        if gammm.awaygoals == 0:
            home_failedtoscore_all_aw += 1
    try:
        home_over2p5_all_pcnt_aw = home_over2p5_all_aw / float(home_total_games_aw) * 100
    except ZeroDivisionError:
        home_over2p5_all_pcnt_aw = 0
    try:
        home_over3p5_all_pcnt_aw = home_over3p5_all_aw / float(home_total_games_aw) * 100
    except ZeroDivisionError:
        home_over3p5_all_pcnt_aw = 0
    try:
        home_over4p5_all_pcnt_aw = home_over4p5_all_aw / float(home_total_games_aw) * 100
    except ZeroDivisionError:
        home_over4p5_all_pcnt_aw = 0
    try:
        home_gg_all_pcnt_aw = home_gg_all_aw / float(home_total_games_aw) * 100
    except ZeroDivisionError:
        home_gg_all_pcnt_aw = 0
    try:
        home_cleansheets_all_pcnt_aw = home_cleansheets_all_aw / float(home_total_games_aw) * 100
    except ZeroDivisionError:
        home_cleansheets_all_pcnt_aw = 0
    try:
        home_failedtoscore_all_pcnt_aw = home_failedtoscore_all_aw / float(home_total_games_aw) * 100
    except ZeroDivisionError:
        home_failedtoscore_all_pcnt_aw = 0
    # AWAY TEAM ALL GAMES -------------------------
    awayset = Game.objects.filter(Q(hometeam=gm.awayteam, season=gm.season.id, date__lt=gm.date) |
                                  Q(awayteam=gm.awayteam, season=gm.season.id, date__lt=gm.date))
    awayfor = Game.objects.team_total_goals_scored_by_date_ex_current(awaytm, season.id, gm.gameweek)
    awayagainst = Game.objects.team_total_goals_conceded_by_date_ex_current(awaytm, season.id, gm.gameweek)
    away_total_games = awayset.exclude(result__exact='').exclude(result__isnull=True).count()
    try:
        away_scored_p_game = awayfor / float(away_total_games)
    except ZeroDivisionError:
        away_scored_p_game = 0
    try:
        away_conceded_p_game = awayagainst / float(away_total_games)
    except ZeroDivisionError:
        away_conceded_p_game = 0
    awayset_with_results = awayset.exclude(result__exact='').exclude(result__isnull=True).annotate(diff=Sum(F('homegoals') + F('awaygoals')))
    away_over2p5_all = 0
    away_over2p5_all_pcnt = 0.0
    away_over3p5_all = 0
    away_over3p5_all_pcnt = 0.0
    away_over4p5_all = 0
    away_over4p5_all_pcnt = 0.0
    away_gg_all = 0
    away_gg_all_pcnt = 0.0
    away_cleansheets_all = Game.objects.team_total_cleansheets_by_date(gm.awayteam, gm.season.id, gm.date)
    away_cleansheets_all_pcnt = 0.0
    away_failedtoscore_all = Game.objects.team_total_failedtoscore_by_date(gm.awayteam, gm.season.id, gm.date)
    away_failedtoscore_all_pcnt = 0.0
    for gmm in awayset_with_results:
        if gmm.diff > 2.5:
            away_over2p5_all += 1
        if gmm.diff > 3.5:
            away_over3p5_all += 1
        if gmm.diff > 4.5:
            away_over4p5_all += 1
        if gmm.homegoals > 0 and gmm.awaygoals > 0:
            away_gg_all += 1
    try:
        away_over2p5_all_pcnt = away_over2p5_all / float(away_total_games) * 100
    except ZeroDivisionError:
        away_over2p5_all_pcnt = 0
    try:
        away_over3p5_all_pcnt = away_over3p5_all / float(away_total_games) * 100
    except ZeroDivisionError:
        away_over3p5_all_pcnt = 0
    try:
        away_over4p5_all_pcnt = away_over4p5_all / float(away_total_games) * 100
    except ZeroDivisionError:
        away_over4p5_all_pcnt = 0
    try:
        away_gg_all_pcnt = away_gg_all / float(away_total_games) * 100
    except ZeroDivisionError:
        away_gg_all_pcnt = 0
    try:
        away_cleansheets_all_pcnt = away_cleansheets_all / float(away_total_games) * 100
    except ZeroDivisionError:
        away_cleansheets_all_pcnt = 0
    try:
        away_failedtoscore_all_pcnt = away_failedtoscore_all / float(away_total_games) * 100
    except ZeroDivisionError:
        away_failedtoscore_all_pcnt = 0
    # AWAY TEAM HOME GAMES ----------------------------------------------------------
    awayset_hm = Game.objects.filter(hometeam=gm.awayteam, season=gm.season.id, date__lt=gm.date)
    # because the aggregation function returns a dictionary, the last part ['homefor_home'] is used to retrieve only the number
    awayfor_hm = awayset_hm.aggregate(awayfor_home=Sum('homegoals'))['awayfor_home']
    awayagainst_hm = awayset_hm.aggregate(awayagainst_home=Sum('awaygoals'))['awayagainst_home']
    away_total_games_hm = awayset_hm.exclude(result__exact='').exclude(result__isnull=True).count()
    try:
        away_scored_p_game_hm = awayfor_hm / float(away_total_games_hm)
    except ZeroDivisionError:
        away_scored_p_game_hm = 0
    try:
        away_conceded_p_game_hm = awayagainst_hm / float(away_total_games_hm)
    except ZeroDivisionError:
        away_conceded_p_game_hm = 0
    awayset_with_results_hm = awayset_hm.exclude(result__exact='').exclude(result__isnull=True).annotate(diff=Sum(F('homegoals') + F('awaygoals')))
    away_over2p5_all_hm = 0
    away_over2p5_all_pcnt_hm = 0.0
    away_over3p5_all_hm = 0
    away_over3p5_all_pcnt_hm = 0.0
    away_over4p5_all_hm = 0
    away_over4p5_all_pcnt_hm = 0.0
    away_gg_all_hm = 0
    away_gg_all_pcnt_hm = 0.0
    away_cleansheets_all_hm = 0
    away_cleansheets_all_pcnt_hm = 0.0
    away_failedtoscore_all_hm = 0
    away_failedtoscore_all_pcnt_hm = 0.0
    for gmmm in awayset_with_results_hm:
        if gmmm.diff > 2.5:
            away_over2p5_all_hm += 1
        if gmmm.diff > 3.5:
            away_over3p5_all_hm += 1
        if gmmm.diff > 4.5:
            away_over4p5_all_hm += 1
        if gmmm.homegoals > 0 and gmmm.awaygoals > 0:
            away_gg_all_hm += 1
        if gmmm.awaygoals == 0:
            away_cleansheets_all_hm += 1
        if gmmm.homegoals == 0:
            away_failedtoscore_all_hm += 1
    try:
        away_over2p5_all_pcnt_hm = away_over2p5_all_hm / float(away_total_games_hm) * 100
    except ZeroDivisionError:
        away_over2p5_all_pcnt_hm = 0
    try:
        away_over3p5_all_pcnt_hm = away_over3p5_all_hm / float(away_total_games_hm) * 100
    except ZeroDivisionError:
        away_over3p5_all_pcnt_hm = 0
    try:
        away_over4p5_all_pcnt_hm = away_over4p5_all_hm / float(away_total_games_hm) * 100
    except ZeroDivisionError:
        away_over4p5_all_pcnt_hm = 0
    try:
        away_gg_all_pcnt_hm = away_gg_all_hm / float(away_total_games_hm) * 100
    except ZeroDivisionError:
        away_gg_all_pcnt_hm = 0
    try:
        away_cleansheets_all_pcnt_hm = away_cleansheets_all_hm / float(away_total_games_hm) * 100
    except ZeroDivisionError:
        away_cleansheets_all_pcnt_hm = 0
    try:
        away_failedtoscore_all_pcnt_hm = away_failedtoscore_all_hm / float(away_total_games_hm) * 100
    except ZeroDivisionError:
        away_failedtoscore_all_pcnt_hm = 0
    # AWAY TEAM AWAY GAMES ----------------------------------------------------------
    awayset_aw = Game.objects.filter(awayteam=gm.awayteam, season=gm.season.id, date__lt=gm.date)
    # because the aggregation function returns a dictionary, the last part ['homefor_home'] is used to retrieve only the number
    awayfor_aw = awayset_aw.aggregate(awayfor_away=Sum('awaygoals'))['awayfor_away']
    awayagainst_aw = awayset_aw.aggregate(awayagainst_away=Sum('homegoals'))['awayagainst_away']
    away_total_games_aw = awayset_aw.exclude(result__exact='').exclude(result__isnull=True).count()
    try:
        away_scored_p_game_aw = awayfor_aw / float(away_total_games_aw)
    except ZeroDivisionError:
        away_scored_p_game_aw = 0
    try:
        away_conceded_p_game_aw = awayagainst_aw / float(away_total_games_aw)
    except ZeroDivisionError:
        away_conceded_p_game_aw = 0
    awayset_with_results_aw = awayset_aw.exclude(result__exact='').exclude(result__isnull=True).annotate(diff=Sum(F('homegoals') + F('awaygoals')))
    away_over2p5_all_aw = 0
    away_over2p5_all_pcnt_aw = 0.0
    away_over3p5_all_aw = 0
    away_over3p5_all_pcnt_aw = 0.0
    away_over4p5_all_aw = 0
    away_over4p5_all_pcnt_aw = 0.0
    away_gg_all_aw = 0
    away_gg_all_pcnt_aw = 0.0
    away_cleansheets_all_aw = 0
    away_cleansheets_all_pcnt_aw = 0.0
    away_failedtoscore_all_aw = 0
    away_failedtoscore_all_pcnt_aw = 0.0
    for gammm in awayset_with_results_aw:
        if gammm.diff > 2.5:
            away_over2p5_all_aw += 1
        if gammm.diff > 3.5:
            away_over3p5_all_aw += 1
        if gammm.diff > 4.5:
            away_over4p5_all_aw += 1
        if gammm.homegoals > 0 and gammm.awaygoals > 0:
            away_gg_all_aw += 1
        if gammm.homegoals == 0:
            away_cleansheets_all_aw += 1
        if gammm.awaygoals == 0:
            away_failedtoscore_all_aw += 1
    try:
        away_over2p5_all_pcnt_aw = away_over2p5_all_aw / float(away_total_games_aw) * 100
    except ZeroDivisionError:
        away_over2p5_all_pcnt_aw = 0
    try:
        away_over3p5_all_pcnt_aw = away_over3p5_all_aw / float(away_total_games_aw) * 100
    except ZeroDivisionError:
        away_over3p5_all_pcnt_aw = 0
    try:
        away_over4p5_all_pcnt_aw = away_over4p5_all_aw / float(away_total_games_aw) * 100
    except ZeroDivisionError:
        away_over4p5_all_pcnt_aw = 0
    try:
        away_gg_all_pcnt_aw = away_gg_all_aw / float(away_total_games_aw) * 100
    except ZeroDivisionError:
        away_gg_all_pcnt_aw = 0
    try:
        away_cleansheets_all_pcnt_aw = away_cleansheets_all_aw / float(away_total_games_aw) * 100
    except ZeroDivisionError:
        away_cleansheets_all_pcnt_aw = 0
    try:
        away_failedtoscore_all_pcnt_aw = away_failedtoscore_all_aw / float(away_total_games_aw) * 100
    except ZeroDivisionError:
        away_failedtoscore_all_pcnt_aw = 0
    # HOME/AWAY ADVANTAGE
    home_points_at_home = Game.objects.team_total_home_points_by_date(hometm, gm.season.id, gm.gameweek)
    home_points_away = Game.objects.team_total_away_points_by_date(hometm, gm.season.id, gm.gameweek)
    try:
        home_goals_at_home_pcnt = (float(homefor_hm) / homefor) * 100
    except ZeroDivisionError:
        home_goals_at_home_pcnt = 0
    try:
        home_goals_away_pcnt = (float(homefor_aw) / homefor) * 100
    except ZeroDivisionError:
        home_goals_away_pcnt = 0
    try:
        home_against_at_home_pcnt = (float(homeagainst_hm) / homeagainst) * 100
    except ZeroDivisionError:
        home_against_at_home_pcnt = 0
    try:
        home_against_away_pcnt = (float(homeagainst_aw) / homeagainst) * 100
    except ZeroDivisionError:
        home_against_away_pcnt = 0
    away_points_at_home = Game.objects.team_total_home_points_by_date(awaytm, gm.season.id, gm.gameweek)
    away_points_away = Game.objects.team_total_away_points_by_date(awaytm, gm.season.id, gm.gameweek)
    try:
        away_goals_at_home_pcnt = (float(awayfor_hm) / awayfor) * 100
    except ZeroDivisionError:
        away_goals_at_home_pcnt = 0
    try:
        away_goals_away_pcnt = (float(awayfor_aw) / awayfor) * 100
    except ZeroDivisionError:
        away_goals_away_pcnt = 0
    try:
        away_against_at_home_pcnt = (float(awayagainst_hm) / awayagainst) * 100
    except ZeroDivisionError:
        away_against_at_home_pcnt = 0
    try:
        away_against_away_pcnt = (float(awayagainst_aw) / awayagainst) * 100
    except ZeroDivisionError:
        away_against_away_pcnt = 0
   # BAR CHART data Team vs Average
    # home team
    homeset_cleaned = homeset.exclude(result__exact='').exclude(result__isnull=True)
    homeset_annotated = homeset_cleaned.annotate(result_total=Sum(F('homegoals') + F('awaygoals')))
    home0to1 = homeset_annotated.filter(result_total__lt=2).count() / float(home_total_games)
    home2to3 = homeset_annotated.filter(Q(result_total=2) | Q(result_total=3)).count() / float(home_total_games)
    home4to6 = homeset_annotated.filter(Q(result_total=4) | Q(result_total=5) | Q(result_total=6)).count() / float(home_total_games)
    home7plus = homeset_annotated.filter(result_total__gt=6).count() / float(home_total_games)
    # away team
    awayset_cleaned = awayset.exclude(result__exact='').exclude(result__isnull=True)
    awayset_annotated = awayset_cleaned.annotate(result_total=Sum(F('homegoals') + F('awaygoals')))
    away0to1 = awayset_annotated.filter(result_total__lt=2).count() / float(away_total_games)
    away2to3 = awayset_annotated.filter(Q(result_total=2) | Q(result_total=3)).count() / float(away_total_games)
    away4to6 = awayset_annotated.filter(Q(result_total=4) | Q(result_total=5) | Q(result_total=6)).count() / float(away_total_games)
    away7plus = awayset_annotated.filter(result_total__gt=6).count() / float(away_total_games)
    # league
    all_matches = Game.objects.filter(season=gm.season.id, date__lt=gm.date).exclude(result__exact='').exclude(result__isnull=True)
    all_matches_cnt = all_matches.count()
    all_matches_annotated = all_matches.annotate(result_total=Sum(F('homegoals') + F('awaygoals')))
    lg0to1 = all_matches_annotated.filter(result_total__lt=2).count() / float(all_matches_cnt)
    lg2to3 = all_matches_annotated.filter(Q(result_total=2) | Q(result_total=3)).count() / float(all_matches_cnt)
    lg4to6 = all_matches_annotated.filter(Q(result_total=4) | Q(result_total=5) | Q(result_total=6)).count() / float(all_matches_cnt)
    lg7plus = all_matches_annotated.filter(result_total__gt=6).count() / float(all_matches_cnt)
    chart_data_json = json.dumps(chart_data)
    return render(request, 'predictions/h2h.html',
                  {'hometm': hometm, 'awaytm': awaytm, 'gm': gm, 'leaderboard': leaderboard, 'x': sorted_x,
                   'season': season, 'gamewk': gamewk, 'title': gamewk_for_title, 'chart_data': chart_data_json,
                   'homewins': homewins, 'homelosses': homelosses, 'homedraws': homedraws,
                   'awaywins': awaywins, 'awaylosses': awaylosses, 'awaydraws': awaydraws, 'homeform': homeform, 'awayform': awayform,
                   'homefor': homefor, 'homeagainst': homeagainst, 'home_total_games': home_total_games, 'home_scored_p_game': home_scored_p_game,
                   'home_conceded_p_game': home_conceded_p_game, 'home_over2p5_all_pcnt': home_over2p5_all_pcnt,
                   'home_over3p5_all_pcnt': home_over3p5_all_pcnt, 'home_over4p5_all_pcnt': home_over4p5_all_pcnt, 'home_gg_all_pcnt': home_gg_all_pcnt,
                   'home_cleansheets_all_pcnt': home_cleansheets_all_pcnt, 'home_failedtoscore_all_pcnt': home_failedtoscore_all_pcnt, 'homefor_hm': homefor_hm,
                   'homeagainst_hm': homeagainst_hm, 'home_scored_p_game_hm': home_scored_p_game_hm, 'home_conceded_p_game_hm': home_conceded_p_game_hm,
                   'home_over2p5_all_pcnt_hm': home_over2p5_all_pcnt_hm, 'home_over3p5_all_pcnt_hm': home_over3p5_all_pcnt_hm, 'home_over4p5_all_pcnt_hm': home_over4p5_all_pcnt_hm,
                   'home_gg_all_pcnt_hm': home_gg_all_pcnt_hm, 'home_cleansheets_all_pcnt_hm': home_cleansheets_all_pcnt_hm, 'home_failedtoscore_all_pcnt_hm': home_failedtoscore_all_pcnt_hm,
                   'homefor_aw': homefor_aw, 'homeagainst_aw': homeagainst_aw, 'home_scored_p_game_aw': home_scored_p_game_aw, 'home_conceded_p_game_aw': home_conceded_p_game_aw,
                   'home_over2p5_all_pcnt_aw': home_over2p5_all_pcnt_aw, 'home_over3p5_all_pcnt_aw': home_over3p5_all_pcnt_aw, 'home_over4p5_all_pcnt_aw': home_over4p5_all_pcnt_aw,
                   'home_gg_all_pcnt_aw': home_gg_all_pcnt_aw, 'home_cleansheets_all_pcnt_aw': home_cleansheets_all_pcnt_aw, 'home_failedtoscore_all_pcnt_aw': home_failedtoscore_all_pcnt_aw,
                   'awayfor': awayfor, 'awayagainst': awayagainst, 'away_total_games': away_total_games, 'away_scored_p_game': away_scored_p_game,
                   'away_conceded_p_game': away_conceded_p_game, 'away_over2p5_all_pcnt': away_over2p5_all_pcnt,
                   'away_over3p5_all_pcnt': away_over3p5_all_pcnt, 'away_over4p5_all_pcnt': away_over4p5_all_pcnt, 'away_gg_all_pcnt': away_gg_all_pcnt,
                   'away_cleansheets_all_pcnt': away_cleansheets_all_pcnt, 'away_failedtoscore_all_pcnt': away_failedtoscore_all_pcnt,
                   'awayfor_hm': awayfor_hm, 'awayagainst_hm': awayagainst_hm, 'away_scored_p_game_hm': away_scored_p_game_hm, 'away_conceded_p_game_hm': away_conceded_p_game_hm,
                   'away_over2p5_all_pcnt_hm': away_over2p5_all_pcnt_hm, 'away_over3p5_all_pcnt_hm': away_over3p5_all_pcnt_hm, 'away_over4p5_all_pcnt_hm': away_over4p5_all_pcnt_hm,
                   'away_gg_all_pcnt_hm': away_gg_all_pcnt_hm, 'away_cleansheets_all_pcnt_hm': away_cleansheets_all_pcnt_hm, 'away_failedtoscore_all_pcnt_hm': away_failedtoscore_all_pcnt_hm,
                   'awayfor_aw': awayfor_aw, 'awayagainst_aw': awayagainst_aw, 'away_scored_p_game_aw': away_scored_p_game_aw, 'away_conceded_p_game_aw': away_conceded_p_game_aw,
                   'away_over2p5_all_pcnt_aw': away_over2p5_all_pcnt_aw, 'away_over3p5_all_pcnt_aw': away_over3p5_all_pcnt_aw, 'away_over4p5_all_pcnt_aw': away_over4p5_all_pcnt_aw,
                   'away_gg_all_pcnt_aw': away_gg_all_pcnt_aw, 'away_cleansheets_all_pcnt_aw': away_cleansheets_all_pcnt_aw, 'away_failedtoscore_all_pcnt_aw': away_failedtoscore_all_pcnt_aw,
                   'home_points_at_home': home_points_at_home, 'home_points_away': home_points_away, 'away_points_at_home': away_points_at_home, 'away_points_away': away_points_away,
                   'home_goals_at_home_pcnt': home_goals_at_home_pcnt, 'home_goals_away_pcnt': home_goals_away_pcnt, 'home_against_at_home_pcnt': home_against_at_home_pcnt,
                   'home_against_away_pcnt': home_against_away_pcnt, 'away_goals_at_home_pcnt': away_goals_at_home_pcnt, 'away_goals_away_pcnt': away_goals_away_pcnt,
                   'away_against_at_home_pcnt': away_against_at_home_pcnt, 'away_against_away_pcnt': away_against_away_pcnt, 'home0to1': home0to1, 'home2to3': home2to3,
                   'home4to6': home4to6, 'home7plus': home7plus, 'away0to1': away0to1, 'away2to3': away2to3, 'away4to6': away4to6, 'away7plus': away7plus, 'lg0to1': lg0to1,
                   'lg2to3': lg2to3, 'lg4to6': lg4to6, 'lg7plus': lg7plus, 'all_matches_cnt': all_matches_cnt, 'homewins_at_home': homewins_at_home, 'homewins_at_away': homewins_at_away,
                   'awaywins_at_home': awaywins_at_home, 'awaywins_at_away': awaywins_at_away, 'homelosses_at_home': homelosses_at_home, 'homelosses_at_away': homelosses_at_away,
                   'awaylosses_at_home': awaylosses_at_home, 'awaylosses_at_away': awaylosses_at_away, 'homedraws_at_home': homedraws_at_home, 'homedraws_at_away': homedraws_at_away,
                   'awaydraws_at_home': awaydraws_at_home, 'awaydraws_at_away': awaydraws_at_away})


def metrics(request):
    myset = Game.objects.all()
    x = {}
    for gm in myset:
        h = gm.hometeam
        a = gm.awayteam
        x.update({h: Game.objects.modified_hga_from_date(teamm=gm.hometeam, seasonn=gm.season, dt=gm.date)})
        x.update({a: Game.objects.modified_hga_from_date(teamm=gm.awayteam, seasonn=gm.season, dt=gm.date)})
    return render(request, 'predictions/metrics.html', {'x': x})


def predictions(request):
    flag = ''
    seasonid = 0
    games_selected = ''
    games_played = 0
    games_total = 0
    games_played_perc = 0
    home_wins_total = 0
    home_wins_total_perc = 0
    away_wins_total = 0
    away_wins_total_perc = 0
    draws_total = 0
    draws_total_perc = 0
    season_goals = 0
    goals_p_game = 0
    bts = 0
    bts_perc = 0
    over_1p5 = 0
    over_2p5 = 0
    over_3p5 = 0
    p = []
    any_postponed = False
    new_predictions_cnt = 0
    past_predictions_cnt = 0
    seasons = Season.objects.all()
    # identifying all distinct countries
    countries = Leagues.objects.order_by('country').values_list('country', flat=True).distinct()
    szns_drpdown = {}
    # filling in a dictionary of leagues for each country
    for cntr in countries:
        szns_drpdown.update({str(cntr): Season.objects.get_seasons_full(cntr)})
    x = []
    szns_drpdown = json.dumps(szns_drpdown)
    gamewk_out = ""
    lstout = "no league selected"
    ssnout = ""
    user_made_selection = False
    if request.method == "POST":
        lg_name = request.POST.get('country_leagues')
        period_end = str(request.POST.get('league_period'))
        if lg_name == "select_league" or lg_name == '' or not lg_name or lg_name is None or period_end == 'None' or period_end == '':
            return redirect('predictions')
        else:
            games_selected = Game.objects.filter(season__league__league_name=lg_name, season__end_date=period_end)[0]
            seasonid = games_selected.season.id
            playoff_cnt = Game.objects.filter(season=seasonid, type='PO').count()
            if playoff_cnt > 0:
                playoffs_started = True
            else:
                playoffs_started = False
            games_played = Game.objects.total_season_games_played(seasonid)
            games_total = Game.objects.total_season_games(seasonid)
            games_played_perc = float(games_played) / games_total
            home_wins_total = Game.objects.total_season_home_wins(seasonid)
            home_wins_total_perc = format(float(home_wins_total) / games_played, "0.00%")
            away_wins_total = Game.objects.total_season_away_wins(seasonid)
            away_wins_total_perc = format(float(away_wins_total) / games_played, "0.00%")
            draws_total = Game.objects.total_season_draws(seasonid)
            draws_total_perc = format(float(draws_total) / games_played, "0.00%")
            season_goals = Game.objects.total_season_goals(seasonid)
            goals_p_game = float(season_goals) / games_played
            bts = Game.objects.season_both_teams_scored(seasonid)
            bts_perc = format(float(bts) / games_played, "0.00%")
            over_1p5 = format(float(Game.objects.over_one_half_optimized(seasonid)) / games_played, "0.00%")
            over_2p5 = format(float(Game.objects.over_two_half_optimized(seasonid)) / games_played, "0.00%")
            over_3p5 = format(float(Game.objects.over_three_half_optimized(seasonid)) / games_played, "0.00%")
            lst = Season.objects.get(id=seasonid)
            lstout = lst.league.league_name
            ssnout = str(lst.get_start_year()) + "/" + str(lst.get_end_year())
            leaderboard = Game.objects.last_gameweek(seasn=lst).select_related('season', 'hometeam', 'awayteam')
            datte = leaderboard.order_by('-date')[0].date
            gamewk = leaderboard[0].gameweek + 1
            lastgw = leaderboard[0].gameweek
            last_gamewk_no_scores_cnt = Game.objects.filter(season=seasonid, gameweek=lastgw).exclude(homegoals__gte=0).count()

            if last_gamewk_no_scores_cnt > 0:
                predictions_exist = True
                try:
                    last_date = Game.objects.filter(season=seasonid, gameweek=gamewk).order_by('-date')[0].date
                except IndexError:
                    last_date = Game.objects.last_gameweek(seasonid).order_by('-date')[0].date
            else:
                try:
                    last_date = Game.objects.filter(season=seasonid, gameweek=gamewk).order_by('-date')[0].date
                    predictions_exist = True
                except IndexError:
                    last_date = Game.objects.last_gameweek(lst).order_by('-gameweek')[0].date
                    predictions_exist = False

            # try:
            #     last_date = Game.objects.filter(season=seasonid, gameweek=gamewk).order_by('-date')[0].date
            #     predictions_exist = True
            # except IndexError:
            #     last_date = Game.objects.last_gameweek(lst).order_by('-gameweek')[0].date
            #     predictions_exist = False
            gamewk_out = gamewk - 1
            user_made_selection = True
            past_predictions_cnt = Game.objects.filter(season=seasonid, gameweek__lte=gamewk_out).exclude(prediction_status_elohist__exact='').exclude(prediction_status_elohist__isnull=True).count()
            # new_predictions_cnt = Game.objects.filter(season=seasonid, gameweek__gt=6).count() - past_predictions_cnt
            # new_predictions_cnt = Game.objects.filter(season=seasonid, gameweek=gamewk).count()
            if predictions_exist:
                new_predictions_cnt = Game.objects.filter(season=seasonid, date__lte=last_date, game_status='OK') \
                    .exclude(prediction_elohist__exact='Not enough games to calculate prediction (the model needs at least 6 gameweeks)') \
                    .exclude(homegoals__gte=0) \
                    .count()
                # new_predictions_cnt = Game.objects.filter(season=seasonid, date__lte=last_date, game_status='OK').exclude(prediction_elohist__exact='Not enough games to calculate prediction (the model needs at least 6 gameweeks)').count()
                # new_predictions_cnt = new_predictions_cnt - past_predictions_cnt
            else:
                new_predictions_cnt = 0
            # teams_total = Game.objects.filter(season=seasonid, gameweek=1).count() * 2
            dateof_last_game = Game.objects.select_related('season').filter(season=seasonid).exclude(result__exact='').exclude(result__isnull=True).order_by('-date')[0].date
            for tm in leaderboard:
                h = tm.hometeam
                a = tm.awayteam
                homeform = Game.objects.team_form_list_by_date(h, seasonid, datte)
                awayform = Game.objects.team_form_list_by_date(a, seasonid, datte)
                hometooltips = Game.objects.team_form_tooltip_by_date(h, seasonid, datte)
                awaytooltips = Game.objects.team_form_tooltip_by_date(a, seasonid, datte)
                hmform_and_tooltip = Game.objects.team_form_tooltip_joined_by_date(h, seasonid, datte)
                awform_and_tooltip = Game.objects.team_form_tooltip_joined_by_date(a, seasonid, datte)
                x.append(
                    {'team': h,
                     'played': Game.objects.team_total_season_matches(h, seasonid),
                     'wins': Game.objects.team_total_wins_by_date_optimized(h, seasonid, datte),
                     'draws': Game.objects.team_total_draws_by_date_optimized(h, seasonid, datte),
                     'losses': Game.objects.team_total_losses_by_date_optimized(h, seasonid, datte),
                     'gf': Game.objects.team_total_goals_scored_by_date(h, seasonid, gamewk),
                     'ga': Game.objects.team_total_goals_conceded_by_date(h, seasonid, gamewk),
                     'f1': hmform_and_tooltip[5][0],
                     'f2': hmform_and_tooltip[4][0],
                     'f3': hmform_and_tooltip[3][0],
                     'f4': hmform_and_tooltip[2][0],
                     'f5': hmform_and_tooltip[1][0],
                     'f6': hmform_and_tooltip[0][0],
                     'tltp1': hmform_and_tooltip[5][1],
                     'tltp2': hmform_and_tooltip[4][1],
                     'tltp3': hmform_and_tooltip[3][1],
                     'tltp4': hmform_and_tooltip[2][1],
                     'tltp5': hmform_and_tooltip[1][1],
                     'tltp6': hmform_and_tooltip[0][1],
                     # 'points': round(Decimal(Game.objects.get_previous_elo_by_date(tm=tm.hometeam, seasn=lst, gmwk=gamewk)), 2)
                     'points': round(Decimal(tm.elo_rating_home), 2),
                     'normal_points': Game.objects.team_points_optimized(seasonid, h, datte),
                     'po_points': Game.objects.team_playoff_points(seasonid, h, datte),
                     })
                x.append(
                    {'team': a,
                     'played': Game.objects.team_total_season_matches(a, seasonid),
                     'wins': Game.objects.team_total_wins_by_date_optimized(a, seasonid, datte),
                     'draws': Game.objects.team_total_draws_by_date_optimized(a, seasonid, datte),
                     'losses': Game.objects.team_total_losses_by_date_optimized(a, seasonid, datte),
                     'gf': Game.objects.team_total_goals_scored_by_date(a, seasonid, gamewk),
                     'ga': Game.objects.team_total_goals_conceded_by_date(a, seasonid, gamewk),
                     'f1': awform_and_tooltip[5][0],
                     'f2': awform_and_tooltip[4][0],
                     'f3': awform_and_tooltip[3][0],
                     'f4': awform_and_tooltip[2][0],
                     'f5': awform_and_tooltip[1][0],
                     'f6': awform_and_tooltip[0][0],
                     'tltp1': awform_and_tooltip[5][1],
                     'tltp2': awform_and_tooltip[4][1],
                     'tltp3': awform_and_tooltip[3][1],
                     'tltp4': awform_and_tooltip[2][1],
                     'tltp5': awform_and_tooltip[1][1],
                     'tltp6': awform_and_tooltip[0][1],
                     # 'points': round(Decimal(Game.objects.get_previous_elo_by_date(tm=tm.awayteam, seasn=lst, gmwk=gamewk)), 2)
                     'points': round(Decimal(tm.elo_rating_away), 2),
                     'normal_points': Game.objects.team_points_optimized(seasonid, a, datte),
                     'po_points': Game.objects.team_playoff_points(seasonid, a, datte),
                     })
            country_code = Season.objects.select_related('league').get(id=seasonid).league.country_code
            if country_code == 'England':
                flag = 'gb-eng'
            else:
                flag = country_code
            p = []
            postponed_games = Game.objects.filter(season=seasonid).exclude(game_status='OK')
            if postponed_games.count() > 0:
                any_postponed = True
            for pgm in postponed_games:
                p.append(
                    {'phome': pgm.hometeam,
                     'paway': pgm.awayteam,
                     'pgw': pgm.gameweek,
                     'pstatus': pgm.game_status,
                     }
                )
    sorted_x = sorted(x, key=itemgetter('points'), reverse=True)
    return render(request, 'predictions/predictions.html',
                  {'x': sorted_x, 'seasonid': seasonid, 'gamewkout': gamewk_out, 'seasons': seasons,
                   'season': lstout, 'ssnout': ssnout, 'user_made_selection': user_made_selection,
                   'countries': countries, 'szns_drpdown': szns_drpdown, 'games_played': games_played,
                   'games_total': games_total, 'games_played_perc': games_played_perc,
                   'games_played_perc_string': format(games_played_perc, "0.00%"), 'home_wins_total_perc': home_wins_total_perc,
                   'away_wins_total_perc': away_wins_total_perc, 'draws_total_perc': draws_total_perc, 'season_goals': season_goals,
                   'goals_p_game': goals_p_game, 'bts_perc': bts_perc, 'over_1p5': over_1p5, 'over_2p5': over_2p5, 'over_3p5': over_3p5,
                   'new_predictions_cnt': new_predictions_cnt, 'past_predictions_cnt': past_predictions_cnt, 'flag': flag, 'p': p, 'any_postponed': any_postponed,
                   'playoffs_started': playoffs_started})


def testview(request):
    active_sessions = Session.objects.filter(expire_date__gte=timezone.now())
    user_id_list = []
    for session in active_sessions:
        data = session.get_decoded()
        user_id_list.append(data.get('_auth_user_id', None))
    userslist = User.objects.filter(id__in=user_id_list)
    return render(request, 'predictions/test.html', {'userslist': userslist})


def active_users(request):
    active_sessions = Session.objects.filter(expire_date__gte=timezone.now())
    user_id_list = []
    for session in active_sessions:
        data = session.get_decoded()
        user_id_list.append(data.get('_auth_user_id', None))
    userslist = User.objects.filter(id__in=user_id_list)
    return render(request, 'predictions/activeusers.html', {'userslist': userslist})


def new_predictions(request, seasonid, gamewk):
    seasonn = Season.objects.get(id=seasonid)
    season_name = seasonn.league.league_name
    season_year = str(seasonn.get_start_year()) + "/" + str(seasonn.get_end_year())
    lastgw = Game.objects.last_gameweek(seasn=seasonid)
    prediction_gamewk = lastgw[0].gameweek + 1
    last_gamewk = lastgw[0].gameweek
    # count of games in the last gmwk where no scores have been entered
    last_gamewk_no_scores_cnt = Game.objects.filter(season=seasonid, gameweek=last_gamewk).exclude(homegoals__gte=0).count()

    if last_gamewk_no_scores_cnt > 0:
        predictions_exist = True
        try:
            last_date = Game.objects.filter(season=seasonid, gameweek=prediction_gamewk).order_by('-date')[0].date
        except IndexError:
            last_date = Game.objects.last_gameweek(seasonn).order_by('-date')[0].date
            prediction_gamewk = last_gamewk
    else:
        try:
            last_date = Game.objects.filter(season=seasonid, gameweek=prediction_gamewk).order_by('-date')[0].date
            predictions_exist = True
        except IndexError:
            last_date = Game.objects.last_gameweek(seasonn).order_by('-gameweek')[0].date
            predictions_exist = False

    # try:
    #     last_date = Game.objects.filter(season=seasonid, gameweek=prediction_gamewk).order_by('-date')[0].date
    #     predictions_exist = True
    # except IndexError:
    #     last_date = Game.objects.last_gameweek(seasonn).order_by('-gameweek')[0].date
    #     predictions_exist = False

    new_predictions_set = Game.objects\
        .filter(season=seasonid, date__lte=last_date, game_status='OK')\
        .exclude(homegoals__gte=0)
    past_predictions_cnt = Game.objects\
        .filter(season=seasonid, gameweek__lte=prediction_gamewk - 1)\
        .exclude(prediction_status_elohist__exact='')\
        .exclude(prediction_status_elohist__isnull=True)\
        .count()

    if predictions_exist:
        new_predictions_cnt = Game.objects.filter(season=seasonid, date__lte=last_date, game_status='OK')\
            .exclude(prediction_elohist__exact='Not enough games to calculate prediction (the model needs at least 6 gameweeks)')\
            .count()
        new_predictions_cnt = new_predictions_cnt - past_predictions_cnt
    else:
        new_predictions_cnt = 0

    x = []
    for gm in new_predictions_set:
        matchh = str(gm.hometeam) + " - " + str(gm.awayteam)
        x.append({
            'gameweek': gm.gameweek,
            'match': matchh,
            'elohist': gm.prediction_elohist,
            'elol6': gm.prediction_elol6,
            'gsrs': gm.prediction_gsrs,
            'date': gm.date,
            'pk': gm.pk
        })
    sorted_x = sorted(x, key=itemgetter('date'), reverse=False)
    # progress bars variables
    home_elohist_total_preds = Game.objects.total_model_predictions('elohist', seasonid, 'HOME')
    home_elohist_succ_preds = Game.objects.total_model_successful_predictions('elohist', seasonid, 'HOME')
    if home_elohist_total_preds == 0:
        home_elohist_strikerate = 0
    else:
        home_elohist_strikerate = (float(home_elohist_succ_preds) / home_elohist_total_preds) * 100

    home_elo6_total_preds = Game.objects.total_model_predictions('elol6', seasonid, 'HOME')
    home_elo6_succ_preds = Game.objects.total_model_successful_predictions('elol6', seasonid, 'HOME')
    if home_elo6_total_preds == 0:
        home_elo6_strikerate = 0
    else:
        home_elo6_strikerate = (float(home_elo6_succ_preds) / home_elo6_total_preds) * 100

    home_gsrs_total_preds = Game.objects.total_model_predictions('gsrs', seasonid, 'HOME')
    home_gsrs_succ_preds = Game.objects.total_model_successful_predictions('gsrs', seasonid, 'HOME')
    if home_gsrs_total_preds == 0:
        home_gsrs_strikerate = 0
    else:
        home_gsrs_strikerate = (float(home_gsrs_succ_preds) / home_gsrs_total_preds) * 100

    away_elohist_total_preds = Game.objects.total_model_predictions('elohist', seasonid, 'AWAY')
    away_elohist_succ_preds = Game.objects.total_model_successful_predictions('elohist', seasonid, 'AWAY')
    if away_elohist_total_preds == 0:
        away_elohist_strikerate = 0
    else:
        away_elohist_strikerate = (float(away_elohist_succ_preds) / away_elohist_total_preds) * 100

    away_elo6_total_preds = Game.objects.total_model_predictions('elol6', seasonid, 'AWAY')
    away_elo6_succ_preds = Game.objects.total_model_successful_predictions('elol6', seasonid, 'AWAY')
    if away_elo6_total_preds == 0:
        away_elo6_strikerate = 0
    else:
        away_elo6_strikerate = (float(away_elo6_succ_preds) / away_elo6_total_preds) * 100

    away_gsrs_total_preds = Game.objects.total_model_predictions('gsrs', seasonid, 'AWAY')
    away_gsrs_succ_preds = Game.objects.total_model_successful_predictions('gsrs', seasonid, 'AWAY')
    if away_gsrs_total_preds == 0:
        away_gsrs_strikerate = 0
    else:
        away_gsrs_strikerate = (float(away_gsrs_succ_preds) / away_gsrs_total_preds) * 100

    draw_elohist_total_preds = Game.objects.total_model_predictions('elohist', seasonid, 'DRAW')
    draw_elohist_succ_preds = Game.objects.total_model_successful_predictions('elohist', seasonid, 'DRAW')
    if draw_elohist_total_preds == 0:
        draw_elohist_strikerate = 0
    else:
        draw_elohist_strikerate = (float(draw_elohist_succ_preds) / draw_elohist_total_preds) * 100

    draw_elo6_total_preds = Game.objects.total_model_predictions('elol6', seasonid, 'DRAW')
    draw_elo6_succ_preds = Game.objects.total_model_successful_predictions('elol6', seasonid, 'DRAW')
    if draw_elo6_total_preds == 0:
        draw_elo6_strikerate = 0
    else:
        draw_elo6_strikerate = (float(draw_elo6_succ_preds) / draw_elo6_total_preds) * 100

    draw_gsrs_total_preds = Game.objects.total_model_predictions('gsrs', seasonid, 'DRAW')
    draw_gsrs_succ_preds = Game.objects.total_model_successful_predictions('gsrs', seasonid, 'DRAW')
    if draw_gsrs_total_preds == 0:
        draw_gsrs_strikerate = 0
    else:
        draw_gsrs_strikerate = (float(draw_gsrs_succ_preds) / draw_gsrs_total_preds) * 100
    return render(request, 'predictions/new_predictions.html', {'szname': season_name, 'szyear': season_year, 'gw': prediction_gamewk, 'new_predictions_set': new_predictions_set,
                                                                'sorted_x': sorted_x, 'new_predictions_cnt': new_predictions_cnt, 'home_elohist_total_preds': home_elohist_total_preds,
                                                                'home_elohist_succ_preds': home_elohist_succ_preds, 'home_elohist_strikerate': home_elohist_strikerate,
                                                                'home_elo6_total_preds': home_elo6_total_preds, 'home_elo6_succ_preds': home_elo6_succ_preds, 'home_elo6_strikerate': home_elo6_strikerate,
                                                                'home_gsrs_total_preds': home_gsrs_total_preds, 'home_gsrs_succ_preds': home_gsrs_succ_preds, 'home_gsrs_strikerate': home_gsrs_strikerate,
                                                                'away_elohist_total_preds': away_elohist_total_preds, 'away_elohist_succ_preds': away_elohist_succ_preds,
                                                                'away_elohist_strikerate': away_elohist_strikerate, 'away_elo6_total_preds': away_elo6_total_preds, 'away_elo6_succ_preds': away_elo6_succ_preds,
                                                                'away_elo6_strikerate': away_elo6_strikerate, 'away_gsrs_total_preds': away_gsrs_total_preds,
                                                                'away_gsrs_succ_preds': away_gsrs_succ_preds, 'away_gsrs_strikerate': away_gsrs_strikerate, 'draw_elohist_total_preds': draw_elohist_total_preds,
                                                                'draw_elohist_succ_preds': draw_elohist_succ_preds, 'draw_elohist_strikerate': draw_elohist_strikerate,
                                                                'draw_elo6_total_preds': draw_elo6_total_preds, 'draw_elo6_succ_preds': draw_elo6_succ_preds,
                                                                'draw_elo6_strikerate': draw_elo6_strikerate, 'draw_gsrs_total_preds': draw_gsrs_total_preds,
                                                                'draw_gsrs_succ_preds': draw_gsrs_succ_preds, 'draw_gsrs_strikerate': draw_gsrs_strikerate})


def dashboard(request):
    # find current year and assign it to period_end_out so when the page loads for the first time, it shows
    # data for the current year's top league
    allgames = Game.objects.all().order_by('-date')
    current_start_year = allgames[0].season.start_date.year
    current_end_year = allgames[0].season.end_date.year
    current_period = str(current_start_year) + "/" + str(current_end_year)
    # period_end_out = 'All'
    period_end_out = current_period
    period_end_canvas = 'All'
    # find top season in terms of strike rate and assign the country and division to the cntry and divisionn
    # variables respectively
    sorted_seasons = Game.objects.rank_seasons_by_strike_rate(current_end_year)
    top_season_id = sorted_seasons[0]['id']
    top_season = Season.objects.get(id=top_season_id)
    cntry = top_season.league.country
    # cntry = 'All'
    divisionn = top_season.league.league_name
    # divisionn = 'All'
    # create a list of dicts that contain the top 3 leagues by league name, and strike rate
    ranked1 = sorted_seasons[0]['id']
    ranked2 = sorted_seasons[1]['id']
    ranked3 = sorted_seasons[2]['id']
    top3srs = [
        {'name': Season.objects.get(id=ranked1).league.league_name, 'strike_rate': sorted_seasons[0]['strike_rate']},
        {'name': Season.objects.get(id=ranked2).league.league_name, 'strike_rate': sorted_seasons[1]['strike_rate']},
        {'name': Season.objects.get(id=ranked3).league.league_name, 'strike_rate': sorted_seasons[2]['strike_rate']}
    ]
    cntry_class = ''
    divisionn_class = ''
    period_end_out_class = ''
    strongest_home_list = [0.0]
    strongest_away_list = [0.0]
    strongest_draw_list = [0.0]
    # dropdown list data
    countries = Leagues.objects.order_by('country').values_list('country', flat=True).distinct()
    allseasons = Season.objects.get_distinct_season_ends()
    szns_drpdown = {}
    # filling in a dictionary of lists of leagues for each country. Each list will contain more info (look at get_seasons_full() in models)
    for cntr in countries:
        szns_drpdown.update({str(cntr): Season.objects.get_seasons_full(cntr)})
    if request.method == "POST":
        cntry = request.POST.get('cntries')
        divisionn = request.POST.get('country_leagues')
        period_end = str(request.POST.get('league_period'))
        if period_end == 'All':
            period_end_out = 'All'
        else:
            try:
                period_end_out = str(datetime.strptime(request.POST.get('league_period'), '%Y-%m-%d').year - 1) + "/" + str(datetime.strptime(request.POST.get('league_period'), '%Y-%m-%d').year)
            except ValueError:
                period_end_out = str(int(request.POST.get('league_period')) - 1) + "/" + str(request.POST.get('league_period'))
            try:
                period_end_canvas = str(datetime.strptime(request.POST.get('league_period'), '%Y-%m-%d').year)
            except ValueError:
                period_end_canvas = str(request.POST.get('league_period'))
        # variables all predictions if request.post
        elohist_total_preds_home = Game.objects.total_model_predictions_ifpost('elohist', cntry, divisionn, period_end, 'HOME')
        elohist_total_preds_away = Game.objects.total_model_predictions_ifpost('elohist', cntry, divisionn, period_end, 'AWAY')
        elohist_total_preds_draw = Game.objects.total_model_predictions_ifpost('elohist', cntry, divisionn, period_end, 'DRAW')
        elol6_total_preds_home = Game.objects.total_model_predictions_ifpost('elol6', cntry, divisionn, period_end, 'HOME')
        elol6_total_preds_away = Game.objects.total_model_predictions_ifpost('elol6', cntry, divisionn, period_end, 'AWAY')
        elol6_total_preds_draw = Game.objects.total_model_predictions_ifpost('elol6', cntry, divisionn, period_end, 'DRAW')
        gsrs_total_preds_home = Game.objects.total_model_predictions_ifpost('gsrs', cntry, divisionn, period_end, 'HOME')
        gsrs_total_preds_away = Game.objects.total_model_predictions_ifpost('gsrs', cntry, divisionn, period_end, 'AWAY')
        gsrs_total_preds_draw = Game.objects.total_model_predictions_ifpost('gsrs', cntry, divisionn, period_end, 'DRAW')
        # variables all successful predictions if request.post
        elohist_total_succ_home = Game.objects.total_model_successful_predictions_ifpost('elohist', cntry, divisionn, period_end, 'HOME')
        elohist_total_succ_away = Game.objects.total_model_successful_predictions_ifpost('elohist', cntry, divisionn, period_end, 'AWAY')
        elohist_total_succ_draw = Game.objects.total_model_successful_predictions_ifpost('elohist', cntry, divisionn, period_end, 'DRAW')
        elol6_total_succ_home = Game.objects.total_model_successful_predictions_ifpost('elol6', cntry, divisionn, period_end, 'HOME')
        elol6_total_succ_away = Game.objects.total_model_successful_predictions_ifpost('elol6', cntry, divisionn, period_end, 'AWAY')
        elol6_total_succ_draw = Game.objects.total_model_successful_predictions_ifpost('elol6', cntry, divisionn, period_end, 'DRAW')
        gsrs_total_succ_home = Game.objects.total_model_successful_predictions_ifpost('gsrs', cntry, divisionn, period_end, 'HOME')
        gsrs_total_succ_away = Game.objects.total_model_successful_predictions_ifpost('gsrs', cntry, divisionn, period_end, 'AWAY')
        gsrs_total_succ_draw = Game.objects.total_model_successful_predictions_ifpost('gsrs', cntry, divisionn, period_end, 'DRAW')
        # variables all winning streaks if request.post
        elohist_winning_streaks = Game.objects.total_model_streaks_ifpost('elohist', cntry, divisionn, period_end)
        elol6_winning_streaks = Game.objects.total_model_streaks_ifpost('elol6', cntry, divisionn, period_end)
        gsrs_winning_streaks = Game.objects.total_model_streaks_ifpost('gsrs', cntry, divisionn, period_end)
        # variables all losing streaks if request.post
        elohist_losing_streaks = Game.objects.total_model_losing_streaks_ifpost('elohist', cntry, divisionn, period_end)
        elol6_losing_streaks = Game.objects.total_model_losing_streaks_ifpost('elol6', cntry, divisionn, period_end)
        gsrs_losing_streaks = Game.objects.total_model_losing_streaks_ifpost('gsrs', cntry, divisionn, period_end)
    else:
        # variables all predictions if not request.post
        elohist_total_preds_home = Game.objects.total_model_predictions('elohist', top_season_id, 'HOME')
        elohist_total_preds_away = Game.objects.total_model_predictions('elohist', top_season_id, 'AWAY')
        elohist_total_preds_draw = Game.objects.total_model_predictions('elohist', top_season_id, 'DRAW')
        elol6_total_preds_home = Game.objects.total_model_predictions('elol6', top_season_id, 'HOME')
        elol6_total_preds_away = Game.objects.total_model_predictions('elol6', top_season_id, 'AWAY')
        elol6_total_preds_draw = Game.objects.total_model_predictions('elol6', top_season_id, 'DRAW')
        gsrs_total_preds_home = Game.objects.total_model_predictions('gsrs', top_season_id, 'HOME')
        gsrs_total_preds_away = Game.objects.total_model_predictions('gsrs', top_season_id, 'AWAY')
        gsrs_total_preds_draw = Game.objects.total_model_predictions('gsrs', top_season_id, 'DRAW')
        # variables all successful predictions if not request.post
        elohist_total_succ_home = Game.objects.total_model_successful_predictions('elohist', top_season_id, 'HOME')
        elohist_total_succ_away = Game.objects.total_model_successful_predictions('elohist', top_season_id, 'AWAY')
        elohist_total_succ_draw = Game.objects.total_model_successful_predictions('elohist', top_season_id, 'DRAW')
        elol6_total_succ_home = Game.objects.total_model_successful_predictions('elol6', top_season_id, 'HOME')
        elol6_total_succ_away = Game.objects.total_model_successful_predictions('elol6', top_season_id, 'AWAY')
        elol6_total_succ_draw = Game.objects.total_model_successful_predictions('elol6', top_season_id, 'DRAW')
        gsrs_total_succ_home = Game.objects.total_model_successful_predictions('gsrs', top_season_id, 'HOME')
        gsrs_total_succ_away = Game.objects.total_model_successful_predictions('gsrs', top_season_id, 'AWAY')
        gsrs_total_succ_draw = Game.objects.total_model_successful_predictions('gsrs', top_season_id, 'DRAW')
        # variables all winning streaks if not request.post
        elohist_winning_streaks = Game.objects.total_model_streaks('elohist', top_season_id)
        elol6_winning_streaks = Game.objects.total_model_streaks('elol6', top_season_id)
        gsrs_winning_streaks = Game.objects.total_model_streaks('gsrs', top_season_id)
        # variables all losing streaks if not request.post
        elohist_losing_streaks = Game.objects.total_model_losing_streaks('elohist', top_season_id)
        elol6_losing_streaks = Game.objects.total_model_losing_streaks('elol6', top_season_id)
        gsrs_losing_streaks = Game.objects.total_model_losing_streaks('gsrs', top_season_id)

    # variables all failed predictions
    elohist_total_fail_home = elohist_total_preds_home - elohist_total_succ_home
    elohist_total_fail_away = elohist_total_preds_away - elohist_total_succ_away
    elohist_total_fail_draw = elohist_total_preds_draw - elohist_total_succ_draw
    elol6_total_fail_home = elol6_total_preds_home - elol6_total_succ_home
    elol6_total_fail_away = elol6_total_preds_away - elol6_total_succ_away
    elol6_total_fail_draw = elol6_total_preds_draw - elol6_total_succ_draw
    gsrs_total_fail_home = gsrs_total_preds_home - gsrs_total_succ_home
    gsrs_total_fail_away = gsrs_total_preds_away - gsrs_total_succ_away
    gsrs_total_fail_draw = gsrs_total_preds_draw - gsrs_total_succ_draw
    # variables strike rate
    if elohist_total_preds_home == 0:
        elohist_strike_rate_home = "NA*"
        elohist_strike_rate_home_tltp = 'NA'
    else:
        elohist_strike_rate_home = (float(elohist_total_succ_home) / elohist_total_preds_home) * 100
        strongest_home_list.append(elohist_strike_rate_home)
        elohist_strike_rate_home_tltp = str(elohist_total_succ_home) + ' / ' + str(elohist_total_preds_home)

    if elohist_total_preds_away == 0:
        elohist_strike_rate_away = "NA*"
        elohist_strike_rate_away_tltp = 'NA'
    else:
        elohist_strike_rate_away = (float(elohist_total_succ_away) / elohist_total_preds_away) * 100
        strongest_away_list.append(elohist_strike_rate_away)
        elohist_strike_rate_away_tltp = str(elohist_total_succ_away) + ' / ' + str(elohist_total_preds_away)

    if elohist_total_preds_draw == 0:
        elohist_strike_rate_draw = "NA*"
        elohist_strike_rate_draw_tltp = 'NA'
    else:
        elohist_strike_rate_draw = (float(elohist_total_succ_draw) / elohist_total_preds_draw) * 100
        strongest_draw_list.append(elohist_strike_rate_draw)
        elohist_strike_rate_draw_tltp = str(elohist_total_succ_draw) + ' / ' + str(elohist_total_preds_draw)

    if elol6_total_preds_home == 0:
        elol6_strike_rate_home = "NA*"
        elol6_strike_rate_home_tltp = 'NA'
    else:
        elol6_strike_rate_home = (float(elol6_total_succ_home) / elol6_total_preds_home) * 100
        strongest_home_list.append(elol6_strike_rate_home)
        elol6_strike_rate_home_tltp = str(elol6_total_succ_home) + ' / ' + str(elol6_total_preds_home)

    if elol6_total_preds_away == 0:
        elol6_strike_rate_away = "NA*"
        elol6_strike_rate_away_tltp = 'NA'
    else:
        elol6_strike_rate_away = (float(elol6_total_succ_away) / elol6_total_preds_away) * 100
        strongest_away_list.append(elol6_strike_rate_away)
        elol6_strike_rate_away_tltp = str(elol6_total_succ_away) + ' / ' + str(elol6_total_preds_away)

    if elol6_total_preds_draw == 0:
        elol6_strike_rate_draw = "NA*"
        elol6_strike_rate_draw_tltp = 'NA'
    else:
        elol6_strike_rate_draw = (float(elol6_total_succ_draw) / elol6_total_preds_draw) * 100
        strongest_draw_list.append(elol6_strike_rate_draw)
        elol6_strike_rate_draw_tltp = str(elol6_total_succ_draw) + ' / ' + str(elol6_total_preds_draw)

    if gsrs_total_preds_home == 0:
        gsrs_strike_rate_home = "NA*"
        gsrs_strike_rate_home_tltp = 'NA'
    else:
        gsrs_strike_rate_home = (float(gsrs_total_succ_home) / gsrs_total_preds_home) * 100
        strongest_home_list.append(gsrs_strike_rate_home)
        gsrs_strike_rate_home_tltp = str(gsrs_total_succ_home) + ' / ' + str(gsrs_total_preds_home)

    if gsrs_total_preds_away == 0:
        gsrs_strike_rate_away = "NA*"
        gsrs_strike_rate_away_tltp = 'NA'
    else:
        gsrs_strike_rate_away = (float(gsrs_total_succ_away) / gsrs_total_preds_away) * 100
        strongest_away_list.append(gsrs_strike_rate_away)
        gsrs_strike_rate_away_tltp = str(gsrs_total_succ_away) + ' / ' + str(gsrs_total_preds_away)

    if gsrs_total_preds_draw == 0:
        gsrs_strike_rate_draw = "NA*"
        gsrs_strike_rate_draw_tltp = 'NA'
    else:
        gsrs_strike_rate_draw = (float(gsrs_total_succ_draw) / gsrs_total_preds_draw) * 100
        strongest_draw_list.append(gsrs_strike_rate_draw)
        gsrs_strike_rate_draw_tltp = str(gsrs_total_succ_draw) + ' / ' + str(gsrs_total_preds_draw)
    # variable model strengths
    strongest_home = max(strongest_home_list)
    strongest_away = max(strongest_away_list)
    strongest_draw = max(strongest_draw_list)
    if strongest_home == elohist_strike_rate_home:
        strongest_home_model = 'Black Predictor'
        strongest_home_value = elohist_strike_rate_home
        barclass_home = "elo_hist_chart"
    elif strongest_home == elol6_strike_rate_home:
        strongest_home_model = 'Maroon Predictor'
        strongest_home_value = elol6_strike_rate_home
        barclass_home = "elo_l6_chart"
    elif strongest_home == gsrs_strike_rate_home:
        strongest_home_model = 'Yellow Predictor'
        strongest_home_value = gsrs_strike_rate_home
        barclass_home = "gsrs_chart"
    else:
        strongest_home_model = 'None yet'
        strongest_home_value = 0
        barclass_home = ""

    if strongest_away == elohist_strike_rate_away:
        strongest_away_model = 'Black Predictor'
        strongest_away_value = elohist_strike_rate_away
        barclass_away = "elo_hist_chart"
    elif strongest_away == elol6_strike_rate_away:
        strongest_away_model = 'Maroon Predictor'
        strongest_away_value = elol6_strike_rate_away
        barclass_away = "elo_l6_chart"
    elif strongest_away == gsrs_strike_rate_away:
        strongest_away_model = 'Yellow Predictor'
        strongest_away_value = gsrs_strike_rate_away
        barclass_away = "gsrs_chart"
    else:
        strongest_away_model = 'None yet'
        strongest_away_value = 0
        barclass_away = ""

    if strongest_draw == elohist_strike_rate_draw:
        strongest_draw_model = 'Black Predictor'
        strongest_draw_value = elohist_strike_rate_draw
        barclass_draw = "elo_hist_chart"
    elif strongest_draw == elol6_strike_rate_draw:
        strongest_draw_model = 'Maroon Predictor'
        strongest_draw_value = elol6_strike_rate_draw
        barclass_draw = "elo_l6_chart"
    elif strongest_draw == gsrs_strike_rate_draw:
        strongest_draw_model = 'Yellow Predictor'
        strongest_draw_value = gsrs_strike_rate_draw
        barclass_draw = "gsrs_chart"
    else:
        strongest_draw_model = 'None yet'
        strongest_draw_value = 0
        barclass_draw = ""
    # variables that return classes
    if elohist_total_preds_home == 0:
        elohist_strike_rate_home_out = -0.1
    else:
        elohist_strike_rate_home_out = float(elohist_total_succ_home) / elohist_total_preds_home

    if elohist_total_preds_away == 0:
        elohist_strike_rate_away_out = -0.1
    else:
        elohist_strike_rate_away_out = float(elohist_total_succ_away) / elohist_total_preds_away

    if elohist_total_preds_draw == 0:
        elohist_strike_rate_draw_out = -0.1
    else:
        elohist_strike_rate_draw_out = float(elohist_total_succ_draw) / elohist_total_preds_draw

    if elol6_total_preds_home == 0:
        elol6_strike_rate_home_out = -0.1
    else:
        elol6_strike_rate_home_out = float(elol6_total_succ_home) / elol6_total_preds_home

    if elol6_total_preds_away == 0:
        elol6_strike_rate_away_out = -0.1
    else:
        elol6_strike_rate_away_out = float(elol6_total_succ_away) / elol6_total_preds_away

    if elol6_total_preds_draw == 0:
        elol6_strike_rate_draw_out = -0.1
    else:
        elol6_strike_rate_draw_out = float(elol6_total_succ_draw) / elol6_total_preds_draw

    if gsrs_total_preds_home == 0:
        gsrs_strike_rate_home_out = -0.1
    else:
        gsrs_strike_rate_home_out = float(gsrs_total_succ_home) / gsrs_total_preds_home

    if gsrs_total_preds_away == 0:
        gsrs_strike_rate_away_out = -0.1
    else:
        gsrs_strike_rate_away_out = float(gsrs_total_succ_away) / gsrs_total_preds_away

    if gsrs_total_preds_draw == 0:
        gsrs_strike_rate_draw_out = -0.1
    else:
        gsrs_strike_rate_draw_out = float(gsrs_total_succ_draw) / gsrs_total_preds_draw

    szns_drpdown_json = json.dumps(szns_drpdown)
    allseasons_json = json.dumps(allseasons)

    elohist_distribution_strike_rate = Game.objects.strike_rate_distribution_for_season('elohist', cntry, divisionn, period_end_canvas)
    elol6_distribution_strike_rate = Game.objects.strike_rate_distribution_for_season('elol6', cntry, divisionn, period_end_canvas)
    gsrs_distribution_strike_rate = Game.objects.strike_rate_distribution_for_season('gsrs', cntry, divisionn, period_end_canvas)

    elohist_distribution_strike_rate = json.dumps(elohist_distribution_strike_rate)
    elol6_distribution_strike_rate = json.dumps(elol6_distribution_strike_rate)
    gsrs_distribution_strike_rate = json.dumps(gsrs_distribution_strike_rate)
    return render(request, 'predictions/dashboard.html',
                  {'szns_drpdown': szns_drpdown_json, 'countries': countries, 'elohist_strike_rate_home': elohist_strike_rate_home,
                   'elohist_strike_rate_away': elohist_strike_rate_away, 'elohist_strike_rate_draw': elohist_strike_rate_draw,
                   'elol6_strike_rate_home': elol6_strike_rate_home, 'elol6_strike_rate_away': elol6_strike_rate_away,
                   'elol6_strike_rate_draw': elol6_strike_rate_draw, 'gsrs_strike_rate_home': gsrs_strike_rate_home,
                   'gsrs_strike_rate_away': gsrs_strike_rate_away, 'gsrs_strike_rate_draw': gsrs_strike_rate_draw,
                   'elohist_total_succ_home': elohist_total_succ_home, 'elohist_total_succ_away': elohist_total_succ_away,
                   'elohist_total_succ_draw': elohist_total_succ_draw, 'elol6_total_succ_home': elol6_total_succ_home,
                   'elol6_total_succ_away': elol6_total_succ_away, 'elol6_total_succ_draw': elol6_total_succ_draw,
                   'gsrs_total_succ_home': gsrs_total_succ_home, 'gsrs_total_succ_away': gsrs_total_succ_away,
                   'gsrs_total_succ_draw': gsrs_total_succ_draw, 'elohist_total_preds_home': elohist_total_preds_home,
                   'elohist_total_preds_away': elohist_total_preds_away, 'elohist_total_preds_draw': elohist_total_preds_draw,
                   'elol6_total_preds_home': elol6_total_preds_home, 'elol6_total_preds_away': elol6_total_preds_away,
                   'elol6_total_preds_draw': elol6_total_preds_draw, 'gsrs_total_preds_home': gsrs_total_preds_home,
                   'gsrs_total_preds_away': gsrs_total_preds_away, 'gsrs_total_preds_draw': gsrs_total_preds_draw,
                   'elohist_total_fail_home': elohist_total_fail_home, 'elohist_total_fail_away': elohist_total_fail_away,
                   'elohist_total_fail_draw': elohist_total_fail_draw, 'elol6_total_fail_home': elol6_total_fail_home,
                   'elol6_total_fail_away': elol6_total_fail_away, 'elol6_total_fail_draw': elol6_total_fail_draw,
                   'gsrs_total_fail_home': gsrs_total_fail_home, 'gsrs_total_fail_away': gsrs_total_fail_away,
                   'gsrs_total_fail_draw': gsrs_total_fail_draw, 'strongest_home_model': strongest_home_model,
                   'strongest_home_value': strongest_home_value, 'strongest_away_model': strongest_away_model,
                   'strongest_away_value': strongest_away_value, 'strongest_draw_model': strongest_draw_model,
                   'strongest_draw_value': strongest_draw_value, 'barclass_home': barclass_home, 'barclass_away': barclass_away,
                   'barclass_draw': barclass_draw, 'cntry': cntry, 'divisionn': divisionn, 'period_end_out': period_end_out,
                   'elohist_winning_streaks': elohist_winning_streaks, 'elol6_winning_streaks': elol6_winning_streaks,
                   'gsrs_winning_streaks': gsrs_winning_streaks, 'elohist_losing_streaks': elohist_losing_streaks,
                   'elol6_losing_streaks': elol6_losing_streaks, 'gsrs_losing_streaks': gsrs_losing_streaks,
                   'gsrs_strike_rate_away_out': gsrs_strike_rate_away_out, 'elol6_strike_rate_home_out': elol6_strike_rate_home_out,
                   'elohist_strike_rate_home_out': elohist_strike_rate_home_out, 'elohist_strike_rate_away_out': elohist_strike_rate_away_out,
                   'elohist_strike_rate_draw_out': elohist_strike_rate_draw_out, 'elol6_strike_rate_away_out': elol6_strike_rate_away_out,
                   'elol6_strike_rate_draw_out': elol6_strike_rate_draw_out, 'gsrs_strike_rate_home_out': gsrs_strike_rate_home_out,
                   'gsrs_strike_rate_draw_out': gsrs_strike_rate_draw_out, 'allseasons': allseasons_json, 'allseasons_notjson': allseasons,
                   'period_end_canvas': period_end_canvas, 'elohist_distribution_strike_rate': elohist_distribution_strike_rate,
                   'elol6_distribution_strike_rate': elol6_distribution_strike_rate, 'gsrs_distribution_strike_rate': gsrs_distribution_strike_rate,
                   'top3': top3srs, 'elohist_strike_rate_home_tltp': elohist_strike_rate_home_tltp, 'elohist_strike_rate_away_tltp': elohist_strike_rate_away_tltp,
                   'elohist_strike_rate_draw_tltp': elohist_strike_rate_draw_tltp, 'elol6_strike_rate_home_tltp': elol6_strike_rate_home_tltp,
                   'elol6_strike_rate_away_tltp': elol6_strike_rate_away_tltp, 'elol6_strike_rate_draw_tltp': elol6_strike_rate_draw_tltp,
                   'gsrs_strike_rate_home_tltp': gsrs_strike_rate_home_tltp, 'gsrs_strike_rate_away_tltp': gsrs_strike_rate_away_tltp,
                   'gsrs_strike_rate_draw_tltp': gsrs_strike_rate_draw_tltp})


def addscore(request):
    formset_to_save = ''
    msg = ''
    msg_class = ''
    GameFormSet = modelformset_factory(Game, fields=('gameweek', 'hometeam', 'homegoals', 'awaygoals', 'awayteam', 'game_status', 'type', 'flag'), extra=0)
    formset = GameFormSet(queryset=Game.objects.all())
    countries = Leagues.objects.order_by('country').values_list('country', flat=True).distinct()
    szns_drpdown = {}
    # filling in a dictionary of leagues for each country
    for cntr in countries:
        szns_drpdown.update({str(cntr): Season.objects.get_seasons_full(cntr)})
    szns_drpdown = json.dumps(szns_drpdown)
    gamewk = ""
    lstout = "no league selected"
    ssnout = ""
    user_made_selection = False
    if request.method == "POST":
        if 'jsform' in request.POST:
            lg_name = request.POST.get('country_leagues')
            period_end = str(request.POST.get('league_period'))
            if lg_name == "select_league" or lg_name == '' or not lg_name or lg_name is None or period_end == 'None' or period_end == '':
                return redirect('add_score')
            else:
                games_selected = Game.objects.filter(season__league__league_name=lg_name, season__end_date=period_end)[0]
                seasonid = games_selected.season.id
                user_made_selection = True
                lst = Season.objects.get(id=seasonid)
                lstout = lst.league.league_name
                ssnout = str(lst.get_start_year()) + "/" + str(lst.get_end_year())
                leaderboard = Game.objects.last_gameweek(seasn=lst)
                gamewk = leaderboard[0].gameweek + 1
                formset = GameFormSet(queryset=Game.objects.filter(season=seasonid, homegoals__isnull=True, game_status='OK'))
        elif 'djform' in request.POST:
            formset_to_save = GameFormSet(request.POST, request.FILES)
            if formset_to_save.is_valid():
                formset_to_save.save()
                msg = "Success! All games saved!"
                msg_class = 'bg-success'
            else:
                formset_to_save = GameFormSet()
                msg = "Something went wrong. Call krok"
                msg_class = 'bg-danger'
    return render(request, 'predictions/addscore.html', {'formset': formset, 'user_made_selection': user_made_selection,
                                                         'szns_drpdown': szns_drpdown, 'gamewk': gamewk, 'lstout': lstout,
                                                         'ssnout': ssnout, 'countries': countries,
                                                         'formset_to_save': formset_to_save, 'msg': msg,
                                                         'msg_class': msg_class})


def addgames(request):
    formset_to_save = ''
    msg = ''
    msg_class = ''
    GameFormSet = modelformset_factory(
        Game,
        form=GameForm,
        extra=40,
        widgets={
            'homegoals': forms.Textarea(attrs={'cols': 8, 'rows': 1}),
            'awaygoals': forms.Textarea(attrs={'cols': 8, 'rows': 1}),
            'date': forms.DateInput()
        },
        fields=('date', 'gameweek', 'hometeam', 'homegoals', 'awaygoals', 'awayteam', 'season', 'game_status', 'type'))
    formset = GameFormSet(queryset=Game.objects.none())
    countries = Leagues.objects.order_by('country').values_list('country', flat=True).distinct()
    szns_drpdown = {}
    # filling in a dictionary of leagues for each country
    for cntr in countries:
        szns_drpdown.update({str(cntr): Season.objects.get_seasons_full(cntr)})
    szns_drpdown = json.dumps(szns_drpdown)
    gamewk = ""
    lstout = "no league selected"
    ssnout = ""
    user_made_selection = False
    if request.method == "POST":
        if 'jsform' in request.POST:
            lg_name = request.POST.get('country_leagues')
            period_end = str(request.POST.get('league_period'))
            if lg_name == "select_league" or lg_name == '' or not lg_name or lg_name is None or period_end == 'None' or period_end == '':
                return redirect('add_games')
            else:
                seasonid = Season.objects.filter(league__league_name=lg_name, end_date=period_end)[0].id
                user_made_selection = True
                lst = Season.objects.get(id=seasonid)
                lstout = lst.league.league_name
                ssnout = str(lst.get_start_year()) + "/" + str(lst.get_end_year())
                # leaderboard = Game.objects.last_gameweek(seasn=lst)
                # gamewk = leaderboard[0].gameweek + 1
                # override the hometeam, awayteam and season querysets (of each form in the formset) to only show the teams and season related to the selected season
                for form in formset:
                    form.fields['hometeam'].queryset = Team.objects.filter(Q(hometeam__season__id=seasonid) | Q(awayteam__season__id=seasonid)).distinct()
                    form.fields['awayteam'].queryset = Team.objects.filter(Q(hometeam__season__id=seasonid) | Q(awayteam__season__id=seasonid)).distinct()
                    form.fields['season'].queryset = Season.objects.filter(id=seasonid).distinct()
                # formset = GameFormSet(queryset=Game.objects.filter(season=seasonid, gameweek=gamewk))
        elif 'djform' in request.POST:
            formset_to_save = GameFormSet(request.POST, request.FILES)
            if formset_to_save.is_valid():
                # for frm in formset:
                #     frm.fields['hometeam'] = frm.fields['homefield']
                #     frm.fields['awayteam'] = frm.fields['awayfield']
                # formset_to_save.save(commit=False)
                formset_to_save.save()
                msg = "Success! All games saved!"
                msg_class = 'bg-success'
            else:
                formset_to_save = GameFormSet()
                msg = "Something went wrong. Call krok"
                msg_class = 'bg-danger'
    return render(request, 'predictions/addgame.html', {'formset': formset, 'user_made_selection': user_made_selection,
                                                        'szns_drpdown': szns_drpdown, 'lstout': lstout,
                                                        'ssnout': ssnout, 'countries': countries,
                                                        'formset_to_save': formset_to_save, 'msg': msg, 'msg_class': msg_class})


def all_games(request):
    tableset = Game.objects.select_related('season')
    return render(request, 'predictions/all_games.html', {'tableset': tableset})


def dashboard_byleague(request):
    cntry = 'All'
    divisionn = 'All'
    allgames = Game.objects.all().order_by('-date')
    current_start_year = allgames[0].season.start_date.year
    current_end_year = allgames[0].season.end_date.year
    current_period = str(current_start_year) + "/" + str(current_end_year)
    sorted_seasons = Game.objects.rank_seasons_by_strike_rate(current_end_year)
    top_season_id = sorted_seasons[0]['id']
    # create a list of dicts that contain the top 3 leagues by league name, and strike rate
    ranked1 = sorted_seasons[0]['id']
    ranked2 = sorted_seasons[1]['id']
    ranked3 = sorted_seasons[2]['id']
    top3srs = [
        {'name': Season.objects.get(id=ranked1).league.league_name, 'strike_rate': sorted_seasons[0]['strike_rate']},
        {'name': Season.objects.get(id=ranked2).league.league_name, 'strike_rate': sorted_seasons[1]['strike_rate']},
        {'name': Season.objects.get(id=ranked3).league.league_name, 'strike_rate': sorted_seasons[2]['strike_rate']}
    ]
    period_end_out = current_period
    period_end_canvas = current_end_year
    allseasons = Season.objects.get_distinct_season_ends()
    # dropdown list data
    countries = Leagues.objects.order_by('country').values_list('country', flat=True).distinct()
    szns_drpdown = {}
    # filling in a dictionary of lists of leagues for each country. Each list will contain more info (look at get_seasons_full() in models)
    for cntr in countries:
        szns_drpdown.update({str(cntr): Season.objects.get_seasons_full(cntr)})
    if request.method == "POST":
        cntry = request.POST.get('cntries')
        divisionn = request.POST.get('country_leagues')
        period_end = str(request.POST.get('league_period'))
        if period_end == 'All':
            period_end_out = 'All'
            period_end_canvas = 'All'
        else:
            try:
                period_end_out = str(datetime.strptime(request.POST.get('league_period'), '%Y-%m-%d').year - 1) + "/" + str(datetime.strptime(request.POST.get('league_period'), '%Y-%m-%d').year)
            except ValueError:
                period_end_out = str(int(request.POST.get('league_period')) - 1) + "/" + str(request.POST.get('league_period'))
            try:
                period_end_canvas = str(datetime.strptime(request.POST.get('league_period'), '%Y-%m-%d').year)
            except ValueError:
                period_end_canvas = str(request.POST.get('league_period'))
    elohist_canvas_home = Game.objects.strike_rate_list_for_canvas('elohist', cntry, divisionn, period_end_canvas, 'HOME')
    elol6_canvas_home = Game.objects.strike_rate_list_for_canvas('elol6', cntry, divisionn, period_end_canvas, 'HOME')
    gsrs_canvas_home = Game.objects.strike_rate_list_for_canvas('gsrs', cntry, divisionn, period_end_canvas, 'HOME')
    elohist_canvas_away = Game.objects.strike_rate_list_for_canvas('elohist', cntry, divisionn, period_end_canvas, 'AWAY')
    elol6_canvas_away = Game.objects.strike_rate_list_for_canvas('elol6', cntry, divisionn, period_end_canvas, 'AWAY')
    gsrs_canvas_away = Game.objects.strike_rate_list_for_canvas('gsrs', cntry, divisionn, period_end_canvas, 'AWAY')
    elohist_canvas_draw = Game.objects.strike_rate_list_for_canvas('elohist', cntry, divisionn, period_end_canvas, 'DRAW')
    elol6_canvas_draw = Game.objects.strike_rate_list_for_canvas('elol6', cntry, divisionn, period_end_canvas, 'DRAW')
    gsrs_canvas_draw = Game.objects.strike_rate_list_for_canvas('gsrs', cntry, divisionn, period_end_canvas, 'DRAW')

    elohist_canvas_home = json.dumps(elohist_canvas_home)
    elol6_canvas_home = json.dumps(elol6_canvas_home)
    gsrs_canvas_home = json.dumps(gsrs_canvas_home)
    elohist_canvas_away = json.dumps(elohist_canvas_away)
    elol6_canvas_away = json.dumps(elol6_canvas_away)
    gsrs_canvas_away = json.dumps(gsrs_canvas_away)
    elohist_canvas_draw = json.dumps(elohist_canvas_draw)
    elol6_canvas_draw = json.dumps(elol6_canvas_draw)
    gsrs_canvas_draw = json.dumps(gsrs_canvas_draw)
    szns_drpdown_json = json.dumps(szns_drpdown)
    allseasons_json = json.dumps(allseasons)
    return render(request, 'predictions/byleague.html', {'szns_drpdown': szns_drpdown_json, 'countries': countries, 'allseasons': allseasons_json, 'allseasons_notjson': allseasons,
                                                         'elohist_canvas_home': elohist_canvas_home, 'elol6_canvas_home': elol6_canvas_home, 'gsrs_canvas_home': gsrs_canvas_home,
                                                         'cntry': cntry, 'divisionn': divisionn, 'period_end_out': period_end_out, 'elohist_canvas_away': elohist_canvas_away,
                                                         'elol6_canvas_away': elol6_canvas_away, 'gsrs_canvas_away': gsrs_canvas_away, 'elohist_canvas_draw': elohist_canvas_draw,
                                                         'elol6_canvas_draw': elol6_canvas_draw, 'gsrs_canvas_draw': gsrs_canvas_draw, 'top3': top3srs, 'current_period': current_period})


def dashboard_bygameweek(request):
    # find current year and assign it to period_end_out so when the page loads for the first time, it shows
    # data for the current year's top league
    allgames = Game.objects.all().order_by('-date')
    current_start_year = allgames[0].season.start_date.year
    current_end_year = allgames[0].season.end_date.year
    current_period = str(current_start_year) + "/" + str(current_end_year)
    # period_end_out = 'All'
    period_end_out = current_period
    # period_end_canvas = 'All'
    # find top season in terms of strike rate and assign the country and division to the cntry and divisionn
    # variables respectively
    sorted_seasons = Game.objects.rank_seasons_by_strike_rate(current_end_year)
    top_season_id = sorted_seasons[0]['id']
    top_season = Season.objects.get(id=top_season_id)
    cntry = top_season.league.country
    # cntry = 'All'
    divisionn = top_season.league.league_name
    # divisionn = 'All'
    period_end_canvas = 'All'
    # create a list of dicts that contain the top 3 leagues by league name, and strike rate
    ranked1 = sorted_seasons[0]['id']
    ranked2 = sorted_seasons[1]['id']
    ranked3 = sorted_seasons[2]['id']
    top3srs = [
        {'name': Season.objects.get(id=ranked1).league.league_name, 'strike_rate': sorted_seasons[0]['strike_rate']},
        {'name': Season.objects.get(id=ranked2).league.league_name, 'strike_rate': sorted_seasons[1]['strike_rate']},
        {'name': Season.objects.get(id=ranked3).league.league_name, 'strike_rate': sorted_seasons[2]['strike_rate']}
    ]
    allseasons = Season.objects.get_distinct_season_ends()
    # dropdown list data
    countries = Leagues.objects.order_by('country').values_list('country', flat=True).distinct()
    szns_drpdown = {}
    # filling in a dictionary of lists of leagues for each country. Each list will contain more info (look at get_seasons_full() in models)
    for cntr in countries:
        szns_drpdown.update({str(cntr): Season.objects.get_seasons_full(cntr)})
    if request.method == "POST":
        cntry = request.POST.get('cntries')
        divisionn = request.POST.get('country_leagues')
        period_end = str(request.POST.get('league_period'))
        if period_end == 'All':
            period_end_out = 'All'
        else:
            try:
                period_end_out = str(datetime.strptime(request.POST.get('league_period'), '%Y-%m-%d').year - 1) + "/" + str(datetime.strptime(request.POST.get('league_period'), '%Y-%m-%d').year)
            except ValueError:
                period_end_out = str(int(request.POST.get('league_period')) - 1) + "/" + str(request.POST.get('league_period'))
            try:
                period_end_canvas = str(datetime.strptime(request.POST.get('league_period'), '%Y-%m-%d').year)
            except ValueError:
                period_end_canvas = str(request.POST.get('league_period'))
    szns_drpdown_json = json.dumps(szns_drpdown)
    allseasons_json = json.dumps(allseasons)

    elohist_canvas = Game.objects.strike_rate_list_pergmwk_for_canvas('elohist', cntry, divisionn, period_end_canvas)
    elohist_avg_canvas = Game.objects.strike_rate_list_pergmwk_for_canvas('elohist', 'All', 'All', 'All')
    elol6_canvas = Game.objects.strike_rate_list_pergmwk_for_canvas('elol6', cntry, divisionn, period_end_canvas)
    elol6_avg_canvas = Game.objects.strike_rate_list_pergmwk_for_canvas('elol6', 'All', 'All', 'All')
    gsrs_canvas = Game.objects.strike_rate_list_pergmwk_for_canvas('gsrs', cntry, divisionn, period_end_canvas)
    gsrs_avg_canvas = Game.objects.strike_rate_list_pergmwk_for_canvas('gsrs', 'All', 'All', 'All')

    elohist_canvas = json.dumps(elohist_canvas)
    elohist_avg_canvas = json.dumps(elohist_avg_canvas)
    elol6_canvas = json.dumps(elol6_canvas)
    elol6_avg_canvas = json.dumps(elol6_avg_canvas)
    gsrs_canvas = json.dumps(gsrs_canvas)
    gsrs_avg_canvas = json.dumps(gsrs_avg_canvas)
    return render(request, 'predictions/bygameweek.html', {'szns_drpdown': szns_drpdown_json, 'countries': countries, 'cntry': cntry, 'divisionn': divisionn, 'period_end_out': period_end_out,
                                                           'allseasons': allseasons_json, 'allseasons_notjson': allseasons, 'period_end_canvas': period_end_canvas,
                                                           'elohist_canvas': elohist_canvas, 'elohist_avg_canvas': elohist_avg_canvas, 'elol6_canvas': elol6_canvas,
                                                           'elol6_avg_canvas': elol6_avg_canvas, 'gsrs_canvas': gsrs_canvas, 'gsrs_avg_canvas': gsrs_avg_canvas,
                                                           'sorted_seasons': sorted_seasons, 'top3': top3srs})


def email(request):
    if request.method == 'GET':
        form = ContactForm()
    else:
        form = ContactForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            subject = form.cleaned_data['subject']
            from_email = form.cleaned_data['email']
            message = form.cleaned_data['message']
            message = message + '\n ' + '\n Sent from: ' + name + '\n email: ' + from_email
            try:
                send_mail(subject, message, from_email, ['georgekrokides@gmail.com'])
            except BadHeaderError:
                return HttpResponse('Invalid header found.')
            return redirect('success')
    return render(request, 'predictions/contact_us.html', {'form': form})


def success(request):
    return render(request, 'predictions/success.html')


def success_postponed_cancelled(request):
    return render(request, 'predictions/success_postponed_cancelled.html')


def faq(request):
    return render(request, 'predictions/faq.html')


def top3(request):
    # allgames = Game.objects.all().order_by('-date')
    # current_start_year = allgames[0].season.start_date.year
    # current_end_year = allgames[0].season.end_date.year
    allseasons = Season.objects.all().order_by('-end_date')
    current_start_year = allseasons[0].start_date.year
    current_end_year = allseasons[0].end_date.year
    current_period = str(current_start_year) + "/" + str(current_end_year)

    # get the dicts
    home_elohist = Game.objects.rank_seasons_by_strike_rate_for_model(current_end_year, 'elohist', 'HOME')
    away_elohist = Game.objects.rank_seasons_by_strike_rate_for_model(current_end_year, 'elohist', 'AWAY')
    draw_elohist = Game.objects.rank_seasons_by_strike_rate_for_model(current_end_year, 'elohist', 'DRAW')
    home_elol6 = Game.objects.rank_seasons_by_strike_rate_for_model(current_end_year, 'elol6', 'HOME')
    away_elol6 = Game.objects.rank_seasons_by_strike_rate_for_model(current_end_year, 'elol6', 'AWAY')
    draw_elol6 = Game.objects.rank_seasons_by_strike_rate_for_model(current_end_year, 'elol6', 'DRAW')
    home_gsrs = Game.objects.rank_seasons_by_strike_rate_for_model(current_end_year, 'gsrs', 'HOME')
    away_gsrs = Game.objects.rank_seasons_by_strike_rate_for_model(current_end_year, 'gsrs', 'AWAY')
    draw_gsrs = Game.objects.rank_seasons_by_strike_rate_for_model(current_end_year, 'gsrs', 'DRAW')

    home_elohist_top3 = [
        {'sid': home_elohist[0]['id'], 'code': home_elohist[0]['country_code'], 'country': home_elohist[0]['country'], 'league_name': home_elohist[0]['league_name'], 'strike_rate': home_elohist[0]['strike_rate']},
        {'sid': home_elohist[1]['id'], 'code': home_elohist[1]['country_code'], 'country': home_elohist[1]['country'], 'league_name': home_elohist[1]['league_name'], 'strike_rate': home_elohist[1]['strike_rate']},
        {'sid': home_elohist[2]['id'], 'code': home_elohist[2]['country_code'], 'country': home_elohist[2]['country'], 'league_name': home_elohist[2]['league_name'], 'strike_rate': home_elohist[2]['strike_rate']}
    ]

    away_elohist_top3 = [
        {'sid': away_elohist[0]['id'], 'code': away_elohist[0]['country_code'], 'country': away_elohist[0]['country'], 'league_name': away_elohist[0]['league_name'], 'strike_rate': away_elohist[0]['strike_rate']},
        {'sid': away_elohist[1]['id'], 'code': away_elohist[1]['country_code'], 'country': away_elohist[1]['country'], 'league_name': away_elohist[1]['league_name'], 'strike_rate': away_elohist[1]['strike_rate']},
        {'sid': away_elohist[2]['id'], 'code': away_elohist[2]['country_code'], 'country': away_elohist[2]['country'], 'league_name': away_elohist[2]['league_name'], 'strike_rate': away_elohist[2]['strike_rate']}
    ]

    draw_elohist_top3 = [
        {'sid': draw_elohist[0]['id'], 'code': draw_elohist[0]['country_code'], 'country': draw_elohist[0]['country'], 'league_name': draw_elohist[0]['league_name'], 'strike_rate': draw_elohist[0]['strike_rate']},
        {'sid': draw_elohist[1]['id'], 'code': draw_elohist[1]['country_code'], 'country': draw_elohist[1]['country'], 'league_name': draw_elohist[1]['league_name'], 'strike_rate': draw_elohist[1]['strike_rate']},
        {'sid': draw_elohist[2]['id'], 'code': draw_elohist[2]['country_code'], 'country': draw_elohist[2]['country'], 'league_name': draw_elohist[2]['league_name'], 'strike_rate': draw_elohist[2]['strike_rate']}
    ]

    home_elol6_top3 = [
        {'sid': home_elol6[0]['id'], 'code': home_elol6[0]['country_code'], 'country': home_elol6[0]['country'], 'league_name': home_elol6[0]['league_name'], 'strike_rate': home_elol6[0]['strike_rate']},
        {'sid': home_elol6[1]['id'], 'code': home_elol6[1]['country_code'], 'country': home_elol6[1]['country'], 'league_name': home_elol6[1]['league_name'], 'strike_rate': home_elol6[1]['strike_rate']},
        {'sid': home_elol6[2]['id'], 'code': home_elol6[2]['country_code'], 'country': home_elol6[2]['country'], 'league_name': home_elol6[2]['league_name'], 'strike_rate': home_elol6[2]['strike_rate']}
    ]

    away_elol6_top3 = [
        {'sid': away_elol6[0]['id'], 'code': away_elol6[0]['country_code'], 'country': away_elol6[0]['country'], 'league_name': away_elol6[0]['league_name'], 'strike_rate': away_elol6[0]['strike_rate']},
        {'sid': away_elol6[1]['id'], 'code': away_elol6[1]['country_code'], 'country': away_elol6[1]['country'], 'league_name': away_elol6[1]['league_name'], 'strike_rate': away_elol6[1]['strike_rate']},
        {'sid': away_elol6[2]['id'], 'code': away_elol6[2]['country_code'], 'country': away_elol6[2]['country'], 'league_name': away_elol6[2]['league_name'], 'strike_rate': away_elol6[2]['strike_rate']}
    ]

    draw_elol6_top3 = [
        {'sid': draw_elol6[0]['id'], 'code': draw_elol6[0]['country_code'], 'country': draw_elol6[0]['country'], 'league_name': draw_elol6[0]['league_name'], 'strike_rate': draw_elol6[0]['strike_rate']},
        {'sid': draw_elol6[1]['id'], 'code': draw_elol6[1]['country_code'], 'country': draw_elol6[1]['country'], 'league_name': draw_elol6[1]['league_name'], 'strike_rate': draw_elol6[1]['strike_rate']},
        {'sid': draw_elol6[2]['id'], 'code': draw_elol6[2]['country_code'], 'country': draw_elol6[2]['country'], 'league_name': draw_elol6[2]['league_name'], 'strike_rate': draw_elol6[2]['strike_rate']}
    ]

    home_gsrs_top3 = [
        {'sid': home_gsrs[0]['id'], 'code': home_gsrs[0]['country_code'], 'country': home_gsrs[0]['country'], 'league_name': home_gsrs[0]['league_name'], 'strike_rate': home_gsrs[0]['strike_rate']},
        {'sid': home_gsrs[1]['id'], 'code': home_gsrs[1]['country_code'], 'country': home_gsrs[1]['country'], 'league_name': home_gsrs[1]['league_name'], 'strike_rate': home_gsrs[1]['strike_rate']},
        {'sid': home_gsrs[2]['id'], 'code': home_gsrs[2]['country_code'], 'country': home_gsrs[2]['country'], 'league_name': home_gsrs[2]['league_name'], 'strike_rate': home_gsrs[2]['strike_rate']}
    ]

    away_gsrs_top3 = [
        {'sid': away_gsrs[0]['id'], 'code': away_gsrs[0]['country_code'], 'country': away_gsrs[0]['country'], 'league_name': away_gsrs[0]['league_name'], 'strike_rate': away_gsrs[0]['strike_rate']},
        {'sid': away_gsrs[1]['id'], 'code': away_gsrs[1]['country_code'], 'country': away_gsrs[1]['country'], 'league_name': away_gsrs[1]['league_name'], 'strike_rate': away_gsrs[1]['strike_rate']},
        {'sid': away_gsrs[2]['id'], 'code': away_gsrs[2]['country_code'], 'country': away_gsrs[2]['country'], 'league_name': away_gsrs[2]['league_name'], 'strike_rate': away_gsrs[2]['strike_rate']}
    ]

    draw_gsrs_top3 = [
        {'sid': draw_gsrs[0]['id'], 'code': draw_gsrs[0]['country_code'], 'country': draw_gsrs[0]['country'], 'league_name': draw_gsrs[0]['league_name'], 'strike_rate': draw_gsrs[0]['strike_rate']},
        {'sid': draw_gsrs[1]['id'], 'code': draw_gsrs[1]['country_code'], 'country': draw_gsrs[1]['country'], 'league_name': draw_gsrs[1]['league_name'], 'strike_rate': draw_gsrs[1]['strike_rate']},
        {'sid': draw_gsrs[2]['id'], 'code': draw_gsrs[2]['country_code'], 'country': draw_gsrs[2]['country'], 'league_name': draw_gsrs[2]['league_name'], 'strike_rate': draw_gsrs[2]['strike_rate']}
    ]
    return render(request, 'predictions/top3.html', {'home_elohist_top3': home_elohist_top3, 'away_elohist_top3': away_elohist_top3, 'draw_elohist_top3': draw_elohist_top3,
                                                     'home_elol6_top3': home_elol6_top3, 'away_elol6_top3': away_elol6_top3, 'draw_elol6_top3': draw_elol6_top3,
                                                     'home_gsrs_top3': home_gsrs_top3, 'away_gsrs_top3': away_gsrs_top3, 'draw_gsrs_top3': draw_gsrs_top3, 'current_period': current_period})


def cancelled_postponed_list(request):
    postponed_cancelled = Game.objects.filter(Q(game_status='PST') | Q(game_status='CNC'))
    return render(request, 'predictions/cancelled_postponed_list.html', {'postponed_cancelled': postponed_cancelled})


def cancelled_postponed_detail(request, pk):
    match = get_object_or_404(Game, pk=pk)
    return render(request, 'predictions/cancelled_postponed_detail.html', {'match': match})


def edit_match(request, pk):
    match = get_object_or_404(Game, pk=pk)
    if request.method == "POST":
        form = GameForm(request.POST, instance=match)
        if form.is_valid():
            match.save()
            return redirect('success_postponed_cancelled')
    else:
        form = GameForm(instance=match)
    return render(request, 'predictions/edit_match.html', {'form': form})


def game_details(request, pk):
    match = get_object_or_404(Game, pk=pk)
    return render(request, 'predictions/game_details.html', {'match': match})


def alerts(request):
    today = datetime.today()
    threshold = datetime.now() + timedelta(days=7)
    upcoming_games = Game.objects.filter(date__gte=today).exclude(homegoals__gte=0).count()
    finished_games_without_score = Game.objects.filter(date__lt=today, homegoals__isnull=True).count()
    games_to_refresh_formulas = Game.objects.filter(flag='Refresh').count()
    upcoming_pst_games = Game.objects \
        .filter(date__gte=today, date__lte=threshold, game_status='PST') \
        .exclude(homegoals__gte=0) \
        .count()
    return render(request, 'predictions/alerts.html', {'upcoming_games': upcoming_games, 'finished_games_without_score': finished_games_without_score,
                                                       'games_to_refresh_formulas': games_to_refresh_formulas, 'upcoming_pst_games': upcoming_pst_games})


def alerts_upcoming_games(request):
    today = datetime.today()
    upcoming_games = Game.objects.filter(date__gte=today).exclude(homegoals__gte=0).order_by('date')
    return render(request, 'predictions/alerts_upcoming_games.html', {'upcoming_games': upcoming_games})


def alerts_upcoming_pst_games(request):
    today = datetime.today()
    threshold = datetime.now() + timedelta(days=7)
    upcoming_games = Game.objects\
        .filter(date__gte=today, date__lte=threshold, game_status='PST')\
        .exclude(homegoals__gte=0)\
        .order_by('date')
    return render(request, 'predictions/alerts_upcoming_pst_games.html', {'upcoming_games': upcoming_games})


def alerts_finished_games(request):
    today = datetime.today()
    finished_games_without_score = GameSeasonFilter(request.GET, queryset=Game.objects.filter(date__lt=today, homegoals__isnull=True).order_by('season'))
    x = []
    for g in finished_games_without_score:
        x.append({
            'season': g.season,
            'gameweek': g.gameweek,
            'date': g.date,
            'hometeam': g.hometeam,
            'awayteam': g.awayteam,
            'command': "python manage.py update_games_boilerplate " + 
                str(g.season.season_sm.season_id) + " " + 
                str(g.date) + " " + 
                str(g.date + timedelta(days=15))
            })

    return render(request, 'predictions/alerts_finished_games_without_score.html', {'finished_games_without_score': finished_games_without_score, 'x': x})


def alerts_refresh_formulas(request):
    games_to_refresh_formulas = GameSeasonFilter(request.GET, queryset=Game.objects.filter(flag='Refresh').order_by('season'))
    return render(request, 'predictions/games_to_refresh.html', {'games_to_refresh_formulas': games_to_refresh_formulas})


def predictions_by_day(request):
    today = datetime.today()
    threshold = datetime.now() + timedelta(days=3)
    upcoming_predictions = Game.objects.select_related('season').filter(date__gte=today, date__lte=threshold, game_status='OK').exclude(homegoals__gte=0).order_by('date')
    countries = Leagues.objects.order_by('country').values_list('country', flat=True).distinct()
    # country_codes = Leagues.objects.order_by('country').values_list('country_code', flat=True).distinct()
    x = []
    # i = 0
    # for c in countries:
    #     x.append([c, country_codes[i]])
    #     i += 1
    szns_drpdown = {}
    # filling in a dictionary of leagues for each country
    for cntr in countries:
        szns_drpdown.update({str(cntr): Season.objects.get_seasons_full(cntr)})

    for key, value in szns_drpdown.items():
        x.append([key, szns_drpdown[key][0][1], szns_drpdown[key][0][7]])
    # szns_drpdown = json.dumps(szns_drpdown)
    sorted_x = sorted(x, key=itemgetter(0), reverse=False)
    return render(request, 'predictions/predictions_by_day.html', {'x': x, 'sorted_x': sorted_x, 'upcoming_predictions': upcoming_predictions, 'threshold': threshold})


def league_overview(request, sid):
    seasonid = sid
    playoff_cnt = Game.objects.filter(season=seasonid, type='PO').count()
    if playoff_cnt > 0:
        playoffs_started = True
    else:
        playoffs_started = False
    selected_country = Season.objects.select_related('league').filter(id=sid)[0].league.country
    countries = Leagues.objects.order_by('country').values_list('country', flat=True).distinct()
    szns_drpdown = {}
    # filling in a dictionary of leagues for each country
    for cntr in countries:
        szns_drpdown.update({str(cntr): Season.objects.get_seasons_full(cntr)})
    x = []
    szns_drpdown = json.dumps(szns_drpdown)
    gamewk_out = ""
    lstout = "no league selected"
    ssnout = ""
    any_postponed = False
    games_played = Game.objects.total_season_games_played(seasonid)
    games_total = Game.objects.total_season_games(seasonid)
    games_played_perc = float(games_played) / games_total
    home_wins_total = Game.objects.total_season_home_wins(seasonid)
    home_wins_total_perc = format(float(home_wins_total) / games_played, "0.00%")
    away_wins_total = Game.objects.total_season_away_wins(seasonid)
    away_wins_total_perc = format(float(away_wins_total) / games_played, "0.00%")
    draws_total = Game.objects.total_season_draws(seasonid)
    draws_total_perc = format(float(draws_total) / games_played, "0.00%")
    season_goals = Game.objects.total_season_goals(seasonid)
    goals_p_game = float(season_goals) / games_played
    bts = Game.objects.season_both_teams_scored(seasonid)
    bts_perc = format(float(bts) / games_played, "0.00%")
    over_1p5 = format(float(Game.objects.over_one_half_optimized(seasonid)) / games_played, "0.00%")
    over_2p5 = format(float(Game.objects.over_two_half_optimized(seasonid)) / games_played, "0.00%")
    over_3p5 = format(float(Game.objects.over_three_half_optimized(seasonid)) / games_played, "0.00%")
    lst = Season.objects.get(id=seasonid)
    lstout = lst.league.league_name
    ssnout = str(lst.get_start_year()) + "/" + str(lst.get_end_year())
    leaderboard = Game.objects.last_gameweek(seasn=lst).select_related('season', 'hometeam', 'awayteam')
    datte = leaderboard.order_by('-date')[0].date
    gamewk = leaderboard[0].gameweek + 1
    lastgw = leaderboard[0].gameweek
    last_gamewk_no_scores_cnt = Game.objects.filter(season=seasonid, gameweek=lastgw).exclude(homegoals__gte=0).count()

    if last_gamewk_no_scores_cnt > 0:
        predictions_exist = True
        try:
            last_date = Game.objects.filter(season=seasonid, gameweek=gamewk).order_by('-date')[0].date
        except IndexError:
            last_date = Game.objects.last_gameweek(seasonid).order_by('-date')[0].date
    else:
        try:
            last_date = Game.objects.filter(season=seasonid, gameweek=gamewk).order_by('-date')[0].date
            predictions_exist = True
        except IndexError:
            last_date = Game.objects.last_gameweek(lst).order_by('-gameweek')[0].date
            predictions_exist = False

    # try:
    #     last_date = Game.objects.filter(season=seasonid, gameweek=gamewk).order_by('-date')[0].date
    #     predictions_exist = True
    # except IndexError:
    #     last_date = Game.objects.last_gameweek(lst).order_by('-gameweek')[0].date
    #     predictions_exist = False
    gamewk_out = gamewk - 1
    user_made_selection = True
    past_predictions_cnt = Game.objects.filter(season=seasonid, gameweek__lte=gamewk_out).exclude(prediction_status_elohist__exact='').exclude(prediction_status_elohist__isnull=True).count()
    # new_predictions_cnt = Game.objects.filter(season=seasonid, gameweek__gt=6).count() - past_predictions_cnt
    # new_predictions_cnt = Game.objects.filter(season=seasonid, gameweek=gamewk).count()
    if predictions_exist:
        new_predictions_cnt = Game.objects.filter(season=seasonid, date__lte=last_date, game_status='OK')\
            .exclude(prediction_elohist__exact='Not enough games to calculate prediction (the model needs at least 6 gameweeks)')\
            .exclude(homegoals__gte=0)\
            .count()
        # new_predictions_cnt = new_predictions_cnt - past_predictions_cnt
    else:
        new_predictions_cnt = 0
    # teams_total = Game.objects.filter(season=seasonid, gameweek=1).count() * 2
    dateof_last_game = Game.objects.select_related('season').filter(season=seasonid).exclude(result__exact='').exclude(result__isnull=True).order_by('-date')[0].date
    for tm in leaderboard:
        h = tm.hometeam
        a = tm.awayteam
        homeform = Game.objects.team_form_list_by_date(h, seasonid, datte)
        awayform = Game.objects.team_form_list_by_date(a, seasonid, datte)
        hometooltips = Game.objects.team_form_tooltip_by_date(h, seasonid, datte)
        awaytooltips = Game.objects.team_form_tooltip_by_date(a, seasonid, datte)
        hmform_and_tooltip = Game.objects.team_form_tooltip_joined_by_date(h, seasonid, datte)
        awform_and_tooltip = Game.objects.team_form_tooltip_joined_by_date(a, seasonid, datte)
        x.append(
            {'team': h,
             'played': Game.objects.team_total_season_matches(h, seasonid),
             'wins': Game.objects.team_total_wins_by_date_optimized(h, seasonid, datte),
             'draws': Game.objects.team_total_draws_by_date_optimized(h, seasonid, datte),
             'losses': Game.objects.team_total_losses_by_date_optimized(h, seasonid, datte),
             'gf': Game.objects.team_total_goals_scored_by_date(h, seasonid, gamewk),
             'ga': Game.objects.team_total_goals_conceded_by_date(h, seasonid, gamewk),
             'f1': hmform_and_tooltip[5][0],
             'f2': hmform_and_tooltip[4][0],
             'f3': hmform_and_tooltip[3][0],
             'f4': hmform_and_tooltip[2][0],
             'f5': hmform_and_tooltip[1][0],
             'f6': hmform_and_tooltip[0][0],
             'tltp1': hmform_and_tooltip[5][1],
             'tltp2': hmform_and_tooltip[4][1],
             'tltp3': hmform_and_tooltip[3][1],
             'tltp4': hmform_and_tooltip[2][1],
             'tltp5': hmform_and_tooltip[1][1],
             'tltp6': hmform_and_tooltip[0][1],
             # 'points': round(Decimal(Game.objects.get_previous_elo_by_date(tm=tm.hometeam, seasn=lst, gmwk=gamewk)), 2)
             'points': round(Decimal(tm.elo_rating_home), 2),
             'normal_points': Game.objects.team_points_optimized(seasonid, h, datte),
             'po_points': Game.objects.team_playoff_points(seasonid, h, datte),
             })
        x.append(
            {'team': a,
             'played': Game.objects.team_total_season_matches(a, seasonid),
             'wins': Game.objects.team_total_wins_by_date_optimized(a, seasonid, datte),
             'draws': Game.objects.team_total_draws_by_date_optimized(a, seasonid, datte),
             'losses': Game.objects.team_total_losses_by_date_optimized(a, seasonid, datte),
             'gf': Game.objects.team_total_goals_scored_by_date(a, seasonid, gamewk),
             'ga': Game.objects.team_total_goals_conceded_by_date(a, seasonid, gamewk),
             'f1': awform_and_tooltip[5][0],
             'f2': awform_and_tooltip[4][0],
             'f3': awform_and_tooltip[3][0],
             'f4': awform_and_tooltip[2][0],
             'f5': awform_and_tooltip[1][0],
             'f6': awform_and_tooltip[0][0],
             'tltp1': awform_and_tooltip[5][1],
             'tltp2': awform_and_tooltip[4][1],
             'tltp3': awform_and_tooltip[3][1],
             'tltp4': awform_and_tooltip[2][1],
             'tltp5': awform_and_tooltip[1][1],
             'tltp6': awform_and_tooltip[0][1],
             # 'points': round(Decimal(Game.objects.get_previous_elo_by_date(tm=tm.awayteam, seasn=lst, gmwk=gamewk)), 2)
             'points': round(Decimal(tm.elo_rating_away), 2),
             'normal_points': Game.objects.team_points_optimized(seasonid, a, datte),
             'po_points': Game.objects.team_playoff_points(seasonid, a, datte),
             })
    country_code = Season.objects.select_related('league').get(id=seasonid).league.country_code
    if country_code == 'England':
        flag = 'gb-eng'
    else:
        flag = country_code
    p = []
    postponed_games = Game.objects.filter(season=seasonid).exclude(game_status='OK')
    if postponed_games.count() > 0:
        any_postponed = True
    for pgm in postponed_games:
        p.append(
            {'phome': pgm.hometeam,
             'paway': pgm.awayteam,
             'pgw': pgm.gameweek,
             'pstatus': pgm.game_status,
             }
        )
    sorted_x = sorted(x, key=itemgetter('points'), reverse=True)
    return render(request, 'predictions/league_overview.html',
                  {'x': sorted_x, 'seasonid': seasonid, 'gamewkout': gamewk_out,
                   'season': lstout, 'ssnout': ssnout, 'user_made_selection': user_made_selection,
                   'countries': countries, 'szns_drpdown': szns_drpdown, 'games_played': games_played,
                   'games_total': games_total, 'games_played_perc': games_played_perc,
                   'games_played_perc_string': format(games_played_perc, "0.00%"), 'home_wins_total_perc': home_wins_total_perc,
                   'away_wins_total_perc': away_wins_total_perc, 'draws_total_perc': draws_total_perc, 'season_goals': season_goals,
                   'goals_p_game': goals_p_game, 'bts_perc': bts_perc, 'over_1p5': over_1p5, 'over_2p5': over_2p5, 'over_3p5': over_3p5,
                   'new_predictions_cnt': new_predictions_cnt, 'past_predictions_cnt': past_predictions_cnt, 'flag': flag, 'p': p, 'any_postponed': any_postponed,
                   'selected_country': selected_country, 'playoffs_started': playoffs_started,
                   'last_gamewk_no_scores_cnt': last_gamewk_no_scores_cnt, 'predictions_exist': predictions_exist})


def livescore(request):
    return render(request, 'predictions/livescore.html')


def addtip(request):
    if request.method == "POST":
        form = TipForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('tip_list')
    else:
        form = TipForm()
    return render(request, 'predictions/addtips.html', {'form': form})


def add_tip_from_pk(request, pk):

    if request.method == "POST":
        form = TipForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('predictions_by_day')
    else:
        form = TipForm()
        form.fields['game'].queryset = Game.objects.filter(id=pk)
    return render(request, 'predictions/add_tip_from_pk.html', {'form': form})


def tip_list(request):
    tips = Tip.objects.all().order_by('tipster')
    return render(request, 'predictions/tip_list.html', {'tips': tips})


def tip_detail(request, pk):
    tip = get_object_or_404(Tip, pk=pk)
    return render(request, 'predictions/tip_detail.html', {'tip': tip})


def tip_edit(request, pk):
    tip = get_object_or_404(Tip, pk=pk)
    if request.method == "POST":
        form = TipForm(request.POST, instance=tip)
        if form.is_valid():
            tip = form.save(commit=False)
            tip.save()
            return redirect('tip_list')
    else:
        form = TipForm(instance=tip)
    return render(request, 'predictions/tip_edit.html', {'form': form})


def addbetslip(request):
    user_made_selection = False
    tipsters = Tip.objects.order_by('tipster').values_list('tipster', flat=True).distinct()
    if request.method == "POST":
        if 'jsform' in request.POST:
            user_made_selection = True
            selected_tipster = request.POST.get('tpster')
            form = BetslipForm(request.POST)
            if selected_tipster == 'All':
                form.fields['tips'].queryset = Tip.objects.filter(game__date__gte=timezone.now())
            else:
                form.fields['tips'].queryset = Tip.objects.filter(tipster=selected_tipster, game__date__gte=timezone.now())
        else:
            form = BetslipForm(request.POST)
        if 'djform' in request.POST:
            if form.is_valid():
                form.save()
            return redirect('betslip_list')
    else:
        form = BetslipForm()
    return render(request, 'predictions/addbetslip.html', {'form': form, 'tipsters': tipsters,
                                                           'user_made_selection': user_made_selection})


def betslip_list(request):
    # list of distinct season ends that will be used in the dropdown
    season_ends = []
    season_ends_full = {}
    for s in Season.objects.all():
        season_ends.append(s.get_end_year())
    season_ends = list(set(season_ends))
    season_ends.sort(reverse=True)
    for endy in season_ends:
        season_ends_full.update({endy: str(endy-1) + "/" + str(endy)})
    season_ends_full = ValueSortedDict(season_ends_full, reverse=True)
    current_end_year = season_ends[0]
    betslips = Betslip.objects.exclude(tips__game__season__end_date__year__lt=current_end_year).exclude(tips__game__season__end_date__year__gt=current_end_year).order_by('-created_date')
    betslips_cnt = betslips.count()
    tipsters = Betslip.objects.order_by('betslip_tipster').values_list('betslip_tipster', flat=True).distinct()
    if request.method == "POST":
        if request.POST.get('seasonends') == 'no selection':
            current_end_year = current_end_year
        else:
            current_end_year = int(request.POST.get('seasonends'))
            betslips = Betslip.objects.exclude(tips__game__season__end_date__year__lt=current_end_year).exclude(tips__game__season__end_date__year__gt=current_end_year).order_by('-created_date')
            betslips_cnt = betslips.count()
    x = {}
    y = []
    for t in tipsters:
        x.update({t: Betslip.objects.tipster_total_betslips(t, current_end_year)})
        y.append([t,
                  Betslip.objects.tipster_total_betslips(t, current_end_year),
                  Betslip.objects.tipster_successful_betslips(t, current_end_year),
                  Betslip.objects.tipster_lost_betslips(t, current_end_year),
                  Betslip.objects.tipster_total_active_betslips(t, current_end_year),
                  Betslip.objects.tipster_sum_of_stakes(t, current_end_year) + Betslip.objects.tipster_sum_of_active_stakes(t, current_end_year),
                  Betslip.objects.tipster_sum_of_stakes(t, current_end_year),
                  Betslip.objects.tipster_sum_of_active_stakes(t, current_end_year),
                  Betslip.objects.tipster_sum_of_stakes(t, current_end_year) + Betslip.objects.tipster_sum_of_profits(t, current_end_year),
                  Betslip.objects.tipster_sum_of_profits(t, current_end_year)])
    current_end_year_for_title = str(int(current_end_year)-1) + "/" + str(current_end_year)
    return render(request, 'predictions/betslip_list.html', {'betslips': betslips, 'x': x, 'betslips_cnt': betslips_cnt, 'y': y,
                                                             'season_ends': season_ends, 'season_ends_full': season_ends_full,
                                                             'current_end_year_for_title': current_end_year_for_title})


def betslip_detail(request, pk):
    betslip = get_object_or_404(Betslip, pk=pk)
    return render(request, 'predictions/betslip_detail.html', {'betslip': betslip})


def betslip_edit(request, pk):
    betslip = get_object_or_404(Betslip, pk=pk)
    if request.method == "POST":
        form = BetslipForm(request.POST, instance=betslip)
        if form.is_valid():
            betslip = form.save(commit=False)
            betslip.save()
            return redirect('betslip_list')
    else:
        form = BetslipForm(instance=betslip)
    return render(request, 'predictions/betslip_edit.html', {'form': form})


def betslips_by_tipster(request, tipster):
    # list of distinct season ends that will be used in the dropdown
    season_ends = []
    season_ends_full = {}
    for s in Season.objects.all():
        season_ends.append(s.get_end_year())
    season_ends = list(set(season_ends))
    season_ends.sort(reverse=True)
    for endy in season_ends:
        season_ends_full.update({endy: str(endy - 1) + "/" + str(endy)})
    season_ends_full = ValueSortedDict(season_ends_full, reverse=True)
    current_end_year = season_ends[0]
    betslips = Betslip.objects.filter(slug=tipster).exclude(tips__game__season__end_date__year__lt=current_end_year).exclude(tips__game__season__end_date__year__gt=current_end_year).order_by('-created_date')
    # betslips_cnt = Betslip.objects.all().count()
    betslips_cnt = Betslip.objects.exclude(tips__game__season__end_date__year__lt=current_end_year).exclude(tips__game__season__end_date__year__gt=current_end_year).order_by('-created_date').count()
    selected_tipster = Betslip.objects.filter(slug=tipster)[0].betslip_tipster
    tipsters = Betslip.objects.order_by('betslip_tipster').values_list('betslip_tipster', flat=True).distinct()
    if request.method == "POST":
        if request.POST.get('seasonends') == 'no selection':
            current_end_year = current_end_year

        else:
            current_end_year = request.POST.get('seasonends')
            # betslips = Betslip.objects.filter(slug=tipster).exclude(tips__game__season__end_date__year__lt=current_end_year).exclude(tips__game__season__end_date__year__gt=current_end_year).order_by('-created_date')
            # betslips_cnt = betslips.count()
            betslips_cnt = Betslip.objects.exclude(tips__game__season__end_date__year__lt=current_end_year).exclude(tips__game__season__end_date__year__gt=current_end_year).order_by('-created_date').count()
    x = {}
    y = []
    for t in tipsters:
        x.update({t: Betslip.objects.tipster_total_betslips(t, current_end_year)})
        y.append([t,
                  Betslip.objects.tipster_total_betslips(t, current_end_year),
                  Betslip.objects.tipster_successful_betslips(t, current_end_year),
                  Betslip.objects.tipster_lost_betslips(t, current_end_year),
                  Betslip.objects.tipster_total_active_betslips(t, current_end_year),
                  Betslip.objects.tipster_sum_of_stakes(t, current_end_year) + Betslip.objects.tipster_sum_of_active_stakes(t, current_end_year),
                  Betslip.objects.tipster_sum_of_stakes(t, current_end_year),
                  Betslip.objects.tipster_sum_of_active_stakes(t, current_end_year),
                  Betslip.objects.tipster_sum_of_stakes(t, current_end_year) + Betslip.objects.tipster_sum_of_profits(t, current_end_year),
                  Betslip.objects.tipster_sum_of_profits(t, current_end_year)])
    current_end_year_for_title = str(int(current_end_year) - 1) + "/" + str(current_end_year)
    return render(request, 'predictions/betslips_by_tipster.html', {'betslips': betslips, 'x': x,
                                                                    'betslips_cnt': betslips_cnt,
                                                                    'selected_tipster': selected_tipster, 'y': y,
                                                                    'season_ends': season_ends, 'season_ends_full': season_ends_full,
                                                                    'current_end_year': current_end_year,
                                                                    'current_end_year_for_title': current_end_year_for_title, 'tipster': tipster})

def smleaguedata(request):
    # API call to get data for selected league (by Id) from sportmonks

    import requests
    import json
    from predictions_project.settings import production
    #from django.conf import settings
    

    http1 = 'https://soccer.sportmonks.com/api/v2.0/leagues/'
    leagueID = str(181)
    http2 = '?api_token='
    if production.sm_API == '':
        from predictions_project.settings import local
        api_token = local.sm_API
    else:
        api_token = production.sm_API    
    http3 = '&include=country,season'

    requestString = http1+leagueID+http2+api_token+http3

    # response = requests.get("https://soccer.sportmonks.com/api/v2.0/leagues/181?api_token=UtfTQXmWeltdNWnWsL53IbP3t7YDyezdR0fMuVbAl9gk9ErXbJOyxQJAEVGB&include=country,season")
    response = requests.get(requestString)

    smleague = response.json()
    leaguesJson = json.dumps(smleague, sort_keys=True, indent=4)
    leaguesDict = json.loads(leaguesJson)
    smleague_data = {}
    # populate the dict to be used to update the sm_League database table
    smleague_data['league_id'] = leaguesDict['data']['id']
    smleague_data['legacy_id'] = leaguesDict['data']['legacy_id']
    smleague_data['name'] = leaguesDict['data']['name']
    smleague_data['country_id'] = leaguesDict['data']['country_id']
    smleague_data['is_cup'] = leaguesDict['data']['is_cup']
    smleague_data['live_standings'] = leaguesDict['data']['live_standings']
    smleague_data['topscorer_goals'] = leaguesDict['data']['coverage']['topscorer_goals']
    smleague_data['topscorer_assists'] = leaguesDict['data']['coverage']['topscorer_assists']
    smleague_data['topscorer_cards'] = leaguesDict['data']['coverage']['topscorer_cards']

    return render(request, 'predictions/smleaguedata.html', {'leaguesDict': leaguesDict,
        'response': response, 'smleague_data': smleague_data})



