from django.conf.urls import url
from . import views
from django.views.generic import TemplateView

urlpatterns = [
    url(r'^$', views.post_list, name='post_list'),
    url(r'^post/(?P<pk>[0-9]+)/$', views.post_detail, name='post_detail'),
    url(r'^post/new/$', views.post_new, name='post_new'),
    url(r'^post/(?P<pk>[0-9]+)/edit/$', views.post_edit, name='post_edit'),
    url(r'^predictions/$', views.predictions, name='predictions'),
    url(r'^predictions/history/$', views.predictions_filter, name='predictions_history'),
    url(r'^about/$', TemplateView.as_view(template_name='predictions/about.html'), name='about'),
    url(r'^contact-us/$', TemplateView.as_view(template_name='predictions/contact_us.html'), name='contactus'),
    url(r'^game/(?P<pk>[0-9]+)/$', views.game_detail, name='game_detail'),
    url(r'^metrics/$', views.metrics, name='metrics'),
    url(r'^pastpredictions/(?P<seasonid>[0-9]+)/$', views.past_predictions, name='past_predictions'),
    url(r'^newpredictions/(?P<seasonid>[0-9]+)/(?P<gamewk>[0-9]+)/$', views.new_predictions, name='new_predictions'),
    url(r'^test/$', views.testview, name='test'),
    url(r'^dashboard/$', views.dashboard, name='dashboard')
    # url(r'^games_filtered/$', views.games_filter, name='games_filtered'),
]
