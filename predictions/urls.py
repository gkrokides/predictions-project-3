from django.conf.urls import url
from . import views
from django.views.generic import TemplateView

urlpatterns = [
    url(r'^posts$', views.post_list, name='post_list'),
    url(r'^post/(?P<pk>[0-9]+)/$', views.post_detail, name='post_detail'),
    url(r'^post/new/$', views.post_new, name='post_new'),
    url(r'^post/(?P<pk>[0-9]+)/edit/$', views.post_edit, name='post_edit'),
    url(r'^league-overview/$', views.predictions, name='predictions'),
    url(r'^predictions-by-day/$', views.predictions_by_day, name='predictions_by_day'),
    url(r'^league-overview/(?P<sid>[0-9]+)/$', views.league_overview, name='league_overview'),
    url(r'^predictions/history/$', views.predictions_filter, name='predictions_history'),
    url(r'^$', views.top3, name='top3'),
    url(r'^contact-us/$', views.email, name='contactus'),
    url(r'^headtohead/(?P<pk>[0-9]+)/$', views.h2h, name='h2h'),
    url(r'^metrics/$', views.metrics, name='metrics'),
    url(r'^pastpredictions/(?P<seasonid>[0-9]+)/$', views.past_predictions, name='past_predictions'),
    url(r'^newpredictions/(?P<seasonid>[0-9]+)/(?P<gamewk>[0-9]+)/$', views.new_predictions, name='new_predictions'),
    url(r'^test/$', views.testview, name='test'),
    url(r'^dashboard/$', views.dashboard, name='dashboard'),
    url(r'^add-score/$', views.addscore, name='add_score'),
    url(r'^add-game/$', views.addgames, name='add_games'),
    url(r'^all-games/$', views.all_games, name='all_games'),
    url(r'^byleague/$', views.dashboard_byleague, name='byleague'),
    url(r'^bygameweek/$', views.dashboard_bygameweek, name='bygameweek'),
    url(r'^activeusers/$', views.active_users, name='activeusers'),
    # url(r'^email/$', views.email, name='email'),
    url(r'^success/$', views.success, name='success'),
    url(r'^faq/$', views.faq, name='faq'),
    url(r'^cancelled-postponed-list/$', views.cancelled_postponed_list, name='cancelled_postponed_list'),
    url(r'^cancelled-postponed-detail/(?P<pk>[0-9]+)/$', views.cancelled_postponed_detail, name='cancelled_postponed_detail'),
    url(r'^edit-match/(?P<pk>[0-9]+)/edit/$', views.edit_match, name='edit_match'),
    url(r'^success-postponed-cancelled/$', views.success_postponed_cancelled, name='success_postponed_cancelled'),
    url(r'^game-details/(?P<pk>[0-9]+)/$', views.game_details, name='game_details'),
    url(r'^alerts/$', views.alerts, name='alerts'),
    url(r'^alerts/upcoming-games/$', views.alerts_upcoming_games, name='alerts_upcoming_games'),
    url(r'^alerts/finished-games-without-score/$', views.alerts_finished_games, name='alerts_finished_games'),
    url(r'^alerts/games-to-refresh/$', views.alerts_refresh_formulas, name='alerts_refresh'),
    url(r'^livescore/$', views.livescore, name='livescore'),

]
