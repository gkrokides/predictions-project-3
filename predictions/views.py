from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from .models import Post, Team, Game, Season, GameFilter, Leagues
from .forms import PostForm
from dicts.sorteddict import ValueSortedDict
from decimal import Decimal
from django.db.models import Q, F, Sum
from operator import itemgetter
from django.conf import settings
from datetime import datetime
import json

# from django.db.models import Count
# from itertools import chain
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
    gfilter = GameFilter(request.GET, queryset=Game.objects.filter(season=seasonid).exclude(prediction_status_elohist__isnull=True).exclude(prediction_status_elohist__exact='').order_by('-date'))
    predicted_games = gfilter.count()
    return render(request, 'predictions/past_predictions.html', {'gfilter': gfilter, 'predicted_games': predicted_games})


def game_detail(request, pk):
    gm = get_object_or_404(Game, pk=pk)
    # season = Season.objects.get(id=2)
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
        x.update({h: round(Decimal(Game.objects.get_previous_elo(tm=tm.hometeam, seasn=season, gmwk=gm.gameweek)), 2)})
        x.update({a: round(Decimal(Game.objects.get_previous_elo(tm=tm.awayteam, seasn=season, gmwk=gm.gameweek)), 2)})
    sorted_x = ValueSortedDict(x, reverse=True)
    # last 6 games of each team--------------------------------------------
    formstart = gm.gameweek - 6
    formend = gm.gameweek
    homeform = []
    awayform = []
    for i in range(formstart, formend):
        homeform.append(Game.objects.team_form(hometm, season.id, i))
    for i in range(formstart, formend):
        awayform.append(Game.objects.team_form(awaytm, season.id, i))
    # Line chart data ------------------------------------------
    homename = str(gm.hometeam)
    awayname = str(gm.awayteam)
    hmteam_all = Game.objects.filter(Q(hometeam=gm.hometeam, gameweek__lt=gm.gameweek, season=gm.season) | Q(awayteam=gm.hometeam, gameweek__lt=gm.gameweek, season=gm.season)).order_by('gameweek')
    awteam_all = Game.objects.filter(Q(hometeam=gm.awayteam, gameweek__lt=gm.gameweek, season=gm.season) | Q(awayteam=gm.awayteam, gameweek__lt=gm.gameweek, season=gm.season)).order_by('gameweek')
    gweeks = []
    home_elos = []
    away_elos = []
    chart_data = [
        ['Gameweek', homename, awayname],
        [0, settings.STARTING_POINTS, settings.STARTING_POINTS]
    ]
    for g in hmteam_all:
        gweeks.append(g.gameweek)
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
    if gm.gameweek < 2:
        chart_data = chart_data
    else:
        for g in range(0, gm.gameweek - 1):
            templist = [gweeks[g], home_elos[g], away_elos[g]]
            chart_data.append(templist)
    # donut charts data ------------------------------------------
    homewins = Game.objects.team_total_wins(hometm, season.id, gm.gameweek - 1)
    awaywins = Game.objects.team_total_wins(awaytm, season.id, gm.gameweek - 1)
    homelosses = Game.objects.team_total_losses(hometm, season.id, gm.gameweek - 1)
    awaylosses = Game.objects.team_total_losses(awaytm, season.id, gm.gameweek - 1)
    homedraws = Game.objects.team_total_draws(hometm, season.id, gm.gameweek - 1)
    awaydraws = Game.objects.team_total_draws(awaytm, season.id, gm.gameweek - 1)
    # SCORING TABLE DATA ------------------------------------------
    # HOME TEAM ALL GAMES -------------------------
    homeset = Game.objects.filter(Q(hometeam=gm.hometeam, season=gm.season.id, gameweek__lt=gm.gameweek) |
                                  Q(awayteam=gm.hometeam, season=gm.season.id, gameweek__lt=gm.gameweek))
    homefor = Game.objects.team_total_goals_scored(hometm, season.id, gm.gameweek - 1)
    homeagainst = Game.objects.team_total_goals_conceded(hometm, season.id, gm.gameweek - 1)
    home_total_games = homeset.exclude(result__exact='').exclude(result__isnull=True).count()
    home_scored_p_game = homefor / float(home_total_games)
    home_conceded_p_game = homeagainst / float(home_total_games)
    homeset_with_results = homeset.exclude(result__exact='').exclude(result__isnull=True).annotate(diff=Sum(F('homegoals') + F('awaygoals')))
    home_over2p5_all = 0
    home_over2p5_all_pcnt = 0.0
    home_over3p5_all = 0
    home_over3p5_all_pcnt = 0.0
    home_over4p5_all = 0
    home_over4p5_all_pcnt = 0.0
    home_gg_all = 0
    home_gg_all_pcnt = 0.0
    home_cleansheets_all = Game.objects.team_total_cleansheets(gm.hometeam, gm.season.id, gm.gameweek)
    home_cleansheets_all_pcnt = 0.0
    home_failedtoscore_all = Game.objects.team_total_failedtoscore(gm.hometeam, gm.season.id, gm.gameweek)
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
    home_over2p5_all_pcnt = home_over2p5_all / float(home_total_games) * 100
    home_over3p5_all_pcnt = home_over3p5_all / float(home_total_games) * 100
    home_over4p5_all_pcnt = home_over4p5_all / float(home_total_games) * 100
    home_gg_all_pcnt = home_gg_all / float(home_total_games) * 100
    home_cleansheets_all_pcnt = home_cleansheets_all / float(home_total_games) * 100
    home_failedtoscore_all_pcnt = home_failedtoscore_all / float(home_total_games) * 100
    # HOME TEAM HOME GAMES ----------------------------------------------------------
    homeset_hm = Game.objects.filter(hometeam=gm.hometeam, season=gm.season.id, gameweek__lt=gm.gameweek)
    # because the aggregation function returns a dictionary, the last part ['homefor_home'] is used to retrieve only the number
    homefor_hm = homeset_hm.aggregate(homefor_home=Sum('homegoals'))['homefor_home']
    homeagainst_hm = homeset_hm.aggregate(homeagainst_home=Sum('awaygoals'))['homeagainst_home']
    home_total_games_hm = homeset_hm.exclude(result__exact='').exclude(result__isnull=True).count()
    home_scored_p_game_hm = homefor_hm / float(home_total_games_hm)
    home_conceded_p_game_hm = homeagainst_hm / float(home_total_games_hm)
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
    home_over2p5_all_pcnt_hm = home_over2p5_all_hm / float(home_total_games_hm) * 100
    home_over3p5_all_pcnt_hm = home_over3p5_all_hm / float(home_total_games_hm) * 100
    home_over4p5_all_pcnt_hm = home_over4p5_all_hm / float(home_total_games_hm) * 100
    home_gg_all_pcnt_hm = home_gg_all_hm / float(home_total_games_hm) * 100
    home_cleansheets_all_pcnt_hm = home_cleansheets_all_hm / float(home_total_games_hm) * 100
    home_failedtoscore_all_pcnt_hm = home_failedtoscore_all_hm / float(home_total_games_hm) * 100
    # HOME TEAM AWAY GAMES ----------------------------------------------------------
    homeset_aw = Game.objects.filter(awayteam=gm.hometeam, season=gm.season.id, gameweek__lt=gm.gameweek)
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
    home_over2p5_all_pcnt_aw = home_over2p5_all_aw / float(home_total_games_aw) * 100
    home_over3p5_all_pcnt_aw = home_over3p5_all_aw / float(home_total_games_aw) * 100
    home_over4p5_all_pcnt_aw = home_over4p5_all_aw / float(home_total_games_aw) * 100
    home_gg_all_pcnt_aw = home_gg_all_aw / float(home_total_games_aw) * 100
    home_cleansheets_all_pcnt_aw = home_cleansheets_all_aw / float(home_total_games_aw) * 100
    home_failedtoscore_all_pcnt_aw = home_failedtoscore_all_aw / float(home_total_games_aw) * 100
    # AWAY TEAM ALL GAMES -------------------------
    awayset = Game.objects.filter(Q(hometeam=gm.awayteam, season=gm.season.id, gameweek__lt=gm.gameweek) |
                                  Q(awayteam=gm.awayteam, season=gm.season.id, gameweek__lt=gm.gameweek))
    awayfor = Game.objects.team_total_goals_scored(awaytm, season.id, gm.gameweek - 1)
    awayagainst = Game.objects.team_total_goals_conceded(awaytm, season.id, gm.gameweek - 1)
    away_total_games = awayset.exclude(result__exact='').exclude(result__isnull=True).count()
    away_scored_p_game = awayfor / float(away_total_games)
    away_conceded_p_game = awayagainst / float(away_total_games)
    awayset_with_results = awayset.exclude(result__exact='').exclude(result__isnull=True).annotate(diff=Sum(F('homegoals') + F('awaygoals')))
    away_over2p5_all = 0
    away_over2p5_all_pcnt = 0.0
    away_over3p5_all = 0
    away_over3p5_all_pcnt = 0.0
    away_over4p5_all = 0
    away_over4p5_all_pcnt = 0.0
    away_gg_all = 0
    away_gg_all_pcnt = 0.0
    away_cleansheets_all = Game.objects.team_total_cleansheets(gm.awayteam, gm.season.id, gm.gameweek)
    away_cleansheets_all_pcnt = 0.0
    away_failedtoscore_all = Game.objects.team_total_failedtoscore(gm.awayteam, gm.season.id, gm.gameweek)
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
    away_over2p5_all_pcnt = away_over2p5_all / float(away_total_games) * 100
    away_over3p5_all_pcnt = away_over3p5_all / float(away_total_games) * 100
    away_over4p5_all_pcnt = away_over4p5_all / float(away_total_games) * 100
    away_gg_all_pcnt = away_gg_all / float(away_total_games) * 100
    away_cleansheets_all_pcnt = away_cleansheets_all / float(away_total_games) * 100
    away_failedtoscore_all_pcnt = away_failedtoscore_all / float(away_total_games) * 100
    # AWAY TEAM HOME GAMES ----------------------------------------------------------
    awayset_hm = Game.objects.filter(hometeam=gm.awayteam, season=gm.season.id, gameweek__lt=gm.gameweek)
    # because the aggregation function returns a dictionary, the last part ['homefor_home'] is used to retrieve only the number
    awayfor_hm = awayset_hm.aggregate(awayfor_home=Sum('homegoals'))['awayfor_home']
    awayagainst_hm = awayset_hm.aggregate(awayagainst_home=Sum('awaygoals'))['awayagainst_home']
    away_total_games_hm = awayset_hm.exclude(result__exact='').exclude(result__isnull=True).count()
    away_scored_p_game_hm = awayfor_hm / float(away_total_games_hm)
    away_conceded_p_game_hm = awayagainst_hm / float(away_total_games_hm)
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
    away_over2p5_all_pcnt_hm = away_over2p5_all_hm / float(away_total_games_hm) * 100
    away_over3p5_all_pcnt_hm = away_over3p5_all_hm / float(away_total_games_hm) * 100
    away_over4p5_all_pcnt_hm = away_over4p5_all_hm / float(away_total_games_hm) * 100
    away_gg_all_pcnt_hm = away_gg_all_hm / float(away_total_games_hm) * 100
    away_cleansheets_all_pcnt_hm = away_cleansheets_all_hm / float(away_total_games_hm) * 100
    away_failedtoscore_all_pcnt_hm = away_failedtoscore_all_hm / float(away_total_games_hm) * 100
    # AWAY TEAM AWAY GAMES ----------------------------------------------------------
    awayset_aw = Game.objects.filter(awayteam=gm.awayteam, season=gm.season.id, gameweek__lt=gm.gameweek)
    # because the aggregation function returns a dictionary, the last part ['homefor_home'] is used to retrieve only the number
    awayfor_aw = awayset_aw.aggregate(awayfor_away=Sum('awaygoals'))['awayfor_away']
    awayagainst_aw = awayset_aw.aggregate(awayagainst_away=Sum('homegoals'))['awayagainst_away']
    away_total_games_aw = awayset_aw.exclude(result__exact='').exclude(result__isnull=True).count()
    away_scored_p_game_aw = awayfor_aw / float(away_total_games_aw)
    away_conceded_p_game_aw = awayagainst_aw / float(away_total_games_aw)
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
    away_over2p5_all_pcnt_aw = away_over2p5_all_aw / float(away_total_games_aw) * 100
    away_over3p5_all_pcnt_aw = away_over3p5_all_aw / float(away_total_games_aw) * 100
    away_over4p5_all_pcnt_aw = away_over4p5_all_aw / float(away_total_games_aw) * 100
    away_gg_all_pcnt_aw = away_gg_all_aw / float(away_total_games_aw) * 100
    away_cleansheets_all_pcnt_aw = away_cleansheets_all_aw / float(away_total_games_aw) * 100
    away_failedtoscore_all_pcnt_aw = away_failedtoscore_all_aw / float(away_total_games_aw) * 100
    # HOME/AWAY ADVANTAGE
    home_points_at_home = Game.objects.team_total_home_points(hometm, gm.season.id, gm.gameweek)
    home_points_away = Game.objects.team_total_away_points(hometm, gm.season.id, gm.gameweek)
    home_goals_at_home_pcnt = (float(homefor_hm) / homefor) * 100
    home_goals_away_pcnt = (float(homefor_aw) / homefor) * 100
    home_against_at_home_pcnt = (float(homeagainst_hm) / homeagainst) * 100
    home_against_away_pcnt = (float(homeagainst_aw) / homeagainst) * 100
    away_points_at_home = Game.objects.team_total_home_points(awaytm, gm.season.id, gm.gameweek)
    away_points_away = Game.objects.team_total_away_points(awaytm, gm.season.id, gm.gameweek)
    away_goals_at_home_pcnt = (float(awayfor_hm) / awayfor) * 100
    away_goals_away_pcnt = (float(awayfor_aw) / awayfor) * 100
    away_against_at_home_pcnt = (float(awayagainst_hm) / awayagainst) * 100
    away_against_away_pcnt = (float(awayagainst_aw) / awayagainst) * 100
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
    all_matches = Game.objects.filter(season=gm.season.id, gameweek__lt=gm.gameweek).exclude(result__exact='').exclude(result__isnull=True)
    all_matches_cnt = all_matches.count()
    all_matches_annotated = all_matches.annotate(result_total=Sum(F('homegoals') + F('awaygoals')))
    lg0to1 = all_matches_annotated.filter(result_total__lt=2).count() / float(all_matches_cnt)
    lg2to3 = all_matches_annotated.filter(Q(result_total=2) | Q(result_total=3)).count() / float(all_matches_cnt)
    lg4to6 = all_matches_annotated.filter(Q(result_total=4) | Q(result_total=5) | Q(result_total=6)).count() / float(all_matches_cnt)
    lg7plus = all_matches_annotated.filter(result_total__gt=6).count() / float(all_matches_cnt)
    return render(request, 'predictions/game_detail.html',
                  {'hometm': hometm, 'awaytm': awaytm, 'gm': gm, 'leaderboard': leaderboard, 'x': sorted_x,
                   'season': season, 'gamewk': gamewk, 'title': gamewk_for_title, 'chart_data': chart_data,
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
                   'lg2to3': lg2to3, 'lg4to6': lg4to6, 'lg7plus': lg7plus, 'all_matches_cnt': all_matches_cnt})


def metrics(request):
    myset = Game.objects.all()
    x = {}
    for gm in myset:
        h = gm.hometeam
        a = gm.awayteam
        x.update({h: Game.objects.modified_hga(teamm=gm.hometeam, seasonn=gm.season, gmwk=gm.gameweek)})
        x.update({a: Game.objects.modified_hga(teamm=gm.awayteam, seasonn=gm.season, gmwk=gm.gameweek)})
    return render(request, 'predictions/metrics.html', {'x': x})


def predictions(request):
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
            over_1p5 = format(float(Game.objects.over_one_half(seasonid)) / games_played, "0.00%")
            over_2p5 = format(float(Game.objects.over_two_half(seasonid)) / games_played, "0.00%")
            over_3p5 = format(float(Game.objects.over_three_half(seasonid)) / games_played, "0.00%")
            lst = Season.objects.get(id=seasonid)
            lstout = lst.league.league_name
            ssnout = str(lst.get_start_year()) + "/" + str(lst.get_end_year())
            leaderboard = Game.objects.last_gameweek(seasn=lst)
            gamewk = leaderboard[0].gameweek + 1
            gamewk_out = gamewk - 1
            user_made_selection = True
            new_predictions_cnt = leaderboard.exclude(prediction_status_elohist__exact='').exclude(prediction_status_elohist__isnull=True).count()
            past_predictions_cnt = Game.objects.filter(season=seasonid, gameweek__lte=gamewk_out).exclude(prediction_status_elohist__exact='').exclude(prediction_status_elohist__isnull=True).count()
            # teams_total = Game.objects.filter(season=seasonid, gameweek=1).count() * 2
            for tm in leaderboard:
                h = tm.hometeam
                a = tm.awayteam
                # In order to get this week's game, I have to give next week's gmwk as the function deducts 1 (so I add 1 at gamewk)
                x.append(
                    {'team': h,
                     'played': Game.objects.last_gameweek_played(h, seasonid),
                     'wins': Game.objects.team_total_wins(h, seasonid, gamewk_out),
                     'draws': Game.objects.team_total_draws(h, seasonid, gamewk_out),
                     'losses': Game.objects.team_total_losses(h, seasonid, gamewk_out),
                     'gf': Game.objects.team_total_goals_scored(h, seasonid, gamewk_out),
                     'ga': Game.objects.team_total_goals_conceded(h, seasonid, gamewk_out),
                     'f1': Game.objects.team_form(h, seasonid, gamewk - 6),
                     'f2': Game.objects.team_form(h, seasonid, gamewk - 5),
                     'f3': Game.objects.team_form(h, seasonid, gamewk - 4),
                     'f4': Game.objects.team_form(h, seasonid, gamewk - 3),
                     'f5': Game.objects.team_form(h, seasonid, gamewk - 2),
                     'f6': Game.objects.team_form(h, seasonid, gamewk - 1),
                     'points': round(Decimal(Game.objects.get_previous_elo(tm=tm.hometeam, seasn=lst, gmwk=gamewk)), 2)
                     })
                x.append(
                    {'team': a,
                     'played': Game.objects.last_gameweek_played(a, seasonid),
                     'wins': Game.objects.team_total_wins(a, seasonid, gamewk_out),
                     'draws': Game.objects.team_total_draws(a, seasonid, gamewk_out),
                     'losses': Game.objects.team_total_losses(a, seasonid, gamewk_out),
                     'gf': Game.objects.team_total_goals_scored(a, seasonid, gamewk_out),
                     'ga': Game.objects.team_total_goals_conceded(a, seasonid, gamewk_out),
                     'f1': Game.objects.team_form(a, seasonid, gamewk - 6),
                     'f2': Game.objects.team_form(a, seasonid, gamewk - 5),
                     'f3': Game.objects.team_form(a, seasonid, gamewk - 4),
                     'f4': Game.objects.team_form(a, seasonid, gamewk - 3),
                     'f5': Game.objects.team_form(a, seasonid, gamewk - 2),
                     'f6': Game.objects.team_form(a, seasonid, gamewk - 1),
                     'points': round(Decimal(Game.objects.get_previous_elo(tm=tm.awayteam, seasn=lst, gmwk=gamewk)), 2)
                     })
    sorted_x = sorted(x, key=itemgetter('points'), reverse=True)
    return render(request, 'predictions/predictions.html',
                  {'x': sorted_x, 'seasonid': seasonid, 'gamewkout': gamewk_out, 'seasons': seasons,
                   'season': lstout, 'ssnout': ssnout, 'user_made_selection': user_made_selection,
                   'countries': countries, 'szns_drpdown': szns_drpdown, 'games_played': games_played,
                   'games_total': games_total, 'games_played_perc': games_played_perc,
                   'games_played_perc_string': format(games_played_perc, "0.00%"), 'home_wins_total_perc': home_wins_total_perc,
                   'away_wins_total_perc': away_wins_total_perc, 'draws_total_perc': draws_total_perc, 'season_goals': season_goals,
                   'goals_p_game': goals_p_game, 'bts_perc': bts_perc, 'over_1p5': over_1p5, 'over_2p5': over_2p5, 'over_3p5': over_3p5,
                   'new_predictions_cnt': new_predictions_cnt, 'past_predictions_cnt': past_predictions_cnt})


def testview(request):
    return render(request, 'predictions/test.html')


def new_predictions(request, seasonid, gamewk):
    seasonn = Season.objects.get(id=seasonid)
    season_name = seasonn.league.league_name
    season_year = str(seasonn.get_start_year()) + "/" + str(seasonn.get_end_year())
    lastgw = Game.objects.last_gameweek(seasn=seasonid)
    prediction_gamewk = lastgw[0].gameweek + 1
    # new_predictions_set = Game.objects.filter(season=seasonid, gameweek=prediction_gamewk).exclude(prediction_status_elohist__exact='').exclude(prediction_status_elohist__isnull=False).order_by('date')
    new_predictions_set = Game.objects.filter(season=seasonid, gameweek=prediction_gamewk).order_by('date')
    new_predictions_cnt = new_predictions_set.count()
    x = []
    for gm in new_predictions_set:
        matchh = str(gm.hometeam) + " vs " + str(gm.awayteam)
        x.append({
            'match': matchh,
            'elohist': gm.prediction_elohist,
            'elol6': gm.prediction_elol6,
            'gsrs': gm.prediction_gsrs,
            'date': gm.date,
            'pk': gm.pk
        })
    sorted_x = sorted(x, key=itemgetter('date'), reverse=False)
    return render(request, 'predictions/new_predictions.html', {'szname': season_name, 'szyear': season_year, 'gw': prediction_gamewk, 'new_predictions_set': new_predictions_set,
                                                                'sorted_x': sorted_x, 'new_predictions_cnt': new_predictions_cnt})


def dashboard(request):
    cntry = 'All'
    divisionn = 'All'
    period_end_out = 'All'
    cntry_class = ''
    divisionn_class = ''
    period_end_out_class = ''
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
            period_end_out = str(datetime.strptime(request.POST.get('league_period'), '%Y-%m-%d').year - 1) + "/" + str(datetime.strptime(request.POST.get('league_period'), '%Y-%m-%d').year)
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
        elohist_total_preds_home = Game.objects.total_model_predictions('elohist', 'all', 'HOME')
        elohist_total_preds_away = Game.objects.total_model_predictions('elohist', 'all', 'AWAY')
        elohist_total_preds_draw = Game.objects.total_model_predictions('elohist', 'all', 'DRAW')
        elol6_total_preds_home = Game.objects.total_model_predictions('elol6', 'all', 'HOME')
        elol6_total_preds_away = Game.objects.total_model_predictions('elol6', 'all', 'AWAY')
        elol6_total_preds_draw = Game.objects.total_model_predictions('elol6', 'all', 'DRAW')
        gsrs_total_preds_home = Game.objects.total_model_predictions('gsrs', 'all', 'HOME')
        gsrs_total_preds_away = Game.objects.total_model_predictions('gsrs', 'all', 'AWAY')
        gsrs_total_preds_draw = Game.objects.total_model_predictions('gsrs', 'all', 'DRAW')
        # variables all successful predictions if not request.post
        elohist_total_succ_home = Game.objects.total_model_successful_predictions('elohist', 'all', 'HOME')
        elohist_total_succ_away = Game.objects.total_model_successful_predictions('elohist', 'all', 'AWAY')
        elohist_total_succ_draw = Game.objects.total_model_successful_predictions('elohist', 'all', 'DRAW')
        elol6_total_succ_home = Game.objects.total_model_successful_predictions('elol6', 'all', 'HOME')
        elol6_total_succ_away = Game.objects.total_model_successful_predictions('elol6', 'all', 'AWAY')
        elol6_total_succ_draw = Game.objects.total_model_successful_predictions('elol6', 'all', 'DRAW')
        gsrs_total_succ_home = Game.objects.total_model_successful_predictions('gsrs', 'all', 'HOME')
        gsrs_total_succ_away = Game.objects.total_model_successful_predictions('gsrs', 'all', 'AWAY')
        gsrs_total_succ_draw = Game.objects.total_model_successful_predictions('gsrs', 'all', 'DRAW')
        # variables all winning streaks if not request.post
        elohist_winning_streaks = Game.objects.total_model_streaks('elohist', 'all')
        elol6_winning_streaks = Game.objects.total_model_streaks('elol6', 'all')
        gsrs_winning_streaks = Game.objects.total_model_streaks('gsrs', 'all')
        # variables all losing streaks if not request.post
        elohist_losing_streaks = Game.objects.total_model_losing_streaks('elohist', 'all')
        elol6_losing_streaks = Game.objects.total_model_losing_streaks('elol6', 'all')
        gsrs_losing_streaks = Game.objects.total_model_losing_streaks('gsrs', 'all')

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
    else:
        elohist_strike_rate_home = format(float(elohist_total_succ_home) / elohist_total_preds_home, "0.00%")

    if elohist_total_preds_away == 0:
        elohist_strike_rate_away = "NA*"
    else:
        elohist_strike_rate_away = format(float(elohist_total_succ_away) / elohist_total_preds_away, "0.00%")

    if elohist_total_preds_draw == 0:
        elohist_strike_rate_draw = "NA*"
    else:
        elohist_strike_rate_draw = format(float(elohist_total_succ_draw) / elohist_total_preds_draw, "0.00%")

    if elol6_total_preds_home == 0:
        elol6_strike_rate_home = "NA*"
    else:
        elol6_strike_rate_home = format(float(elol6_total_succ_home) / elol6_total_preds_home, "0.00%")

    if elol6_total_preds_away == 0:
        elol6_strike_rate_away = "NA*"
    else:
        elol6_strike_rate_away = format(float(elol6_total_succ_away) / elol6_total_preds_away, "0.00%")

    if elol6_total_preds_draw == 0:
        elol6_strike_rate_draw = "NA*"
    else:
        elol6_strike_rate_draw = format(float(elol6_total_succ_draw) / elol6_total_preds_draw, "0.00%")

    if gsrs_total_preds_home == 0:
        gsrs_strike_rate_home = "NA*"
    else:
        gsrs_strike_rate_home = format(float(gsrs_total_succ_home) / gsrs_total_preds_home, "0.00%")

    if gsrs_total_preds_away == 0:
        gsrs_strike_rate_away = "NA*"
    else:
        gsrs_strike_rate_away = format(float(gsrs_total_succ_away) / gsrs_total_preds_away, "0.00%")

    if gsrs_total_preds_draw == 0:
        gsrs_strike_rate_draw = "NA*"
    else:
        gsrs_strike_rate_draw = format(float(gsrs_total_succ_draw) / gsrs_total_preds_draw, "0.00%")
    # variable model strengths
    strongest_home = max(elohist_strike_rate_home, elol6_strike_rate_home, gsrs_strike_rate_home)
    strongest_away = max(elohist_strike_rate_away, elol6_strike_rate_away, gsrs_strike_rate_away)
    strongest_draw = max(elohist_strike_rate_draw, elol6_strike_rate_draw, gsrs_strike_rate_draw)
    if strongest_home == elohist_strike_rate_home:
        strongest_home_model = 'ELO(H)'
        strongest_home_value = elohist_strike_rate_home
        barclass_home = "elo_hist_chart"
    elif strongest_home == elol6_strike_rate_home:
        strongest_home_model = 'ELO(6)'
        strongest_home_value = elol6_strike_rate_home
        barclass_home = "elo_l6_chart"
    else:
        strongest_home_model = 'GSRS'
        strongest_home_value = gsrs_strike_rate_home
        barclass_home = "gsrs_chart"

    if strongest_away == elohist_strike_rate_away:
        strongest_away_model = 'ELO(H)'
        strongest_away_value = elohist_strike_rate_away
        barclass_away = "elo_hist_chart"
    elif strongest_away == elol6_strike_rate_home:
        strongest_away_model = 'ELO(6)'
        strongest_away_value = elol6_strike_rate_away
        barclass_away = "elo_l6_chart"
    else:
        strongest_away_model = 'GSRS'
        strongest_away_value = gsrs_strike_rate_away
        barclass_away = "gsrs_chart"

    if strongest_draw == elohist_strike_rate_draw:
        strongest_draw_model = 'ELO(H)'
        strongest_draw_value = elohist_strike_rate_draw
        barclass_draw = "elo_hist_chart"
    elif strongest_draw == elol6_strike_rate_draw:
        strongest_draw_model = 'ELO(6)'
        strongest_draw_value = elol6_strike_rate_draw
        barclass_draw = "elo_l6_chart"
    else:
        strongest_draw_model = 'GSRS'
        strongest_draw_value = gsrs_strike_rate_draw
        barclass_draw = "gsrs_chart"
    # variables that return classes
    if elohist_total_preds_home == 0:
        elohist_strike_rate_home_out = 0
    else:
        elohist_strike_rate_home_out = float(elohist_total_succ_home) / elohist_total_preds_home

    if elohist_total_preds_away == 0:
        elohist_strike_rate_away_out = 0
    else:
        elohist_strike_rate_away_out = float(elohist_total_succ_away) / elohist_total_preds_away

    if elohist_total_preds_draw == 0:
        elohist_strike_rate_draw_out = 0
    else:
        elohist_strike_rate_draw_out = float(elohist_total_succ_draw) / elohist_total_preds_draw

    if elol6_total_preds_home == 0:
        elol6_strike_rate_home_out = 0
    else:
        elol6_strike_rate_home_out = float(elol6_total_succ_home) / elol6_total_preds_home

    if elol6_total_preds_away == 0:
        elol6_strike_rate_away_out = 0
    else:
        elol6_strike_rate_away_out = float(elol6_total_succ_away) / elol6_total_preds_away

    if elol6_total_preds_draw == 0:
        elol6_strike_rate_draw_out = 0
    else:
        elol6_strike_rate_draw_out = float(elol6_total_succ_draw) / elol6_total_preds_draw

    if gsrs_total_preds_home == 0:
        gsrs_strike_rate_home_out = 0
    else:
        gsrs_strike_rate_home_out = float(gsrs_total_succ_home) / gsrs_total_preds_home

    if gsrs_total_preds_away == 0:
        gsrs_strike_rate_away_out = 0
    else:
        gsrs_strike_rate_away_out = float(gsrs_total_succ_away) / gsrs_total_preds_away

    if gsrs_total_preds_draw == 0:
        gsrs_strike_rate_draw_out = 0
    else:
        gsrs_strike_rate_draw_out = float(gsrs_total_succ_draw) / gsrs_total_preds_draw
    return render(request, 'predictions/dashboard.html',
                  {'szns_drpdown': szns_drpdown, 'countries': countries, 'elohist_strike_rate_home': elohist_strike_rate_home,
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
                   'gsrs_strike_rate_draw_out': gsrs_strike_rate_draw_out})
