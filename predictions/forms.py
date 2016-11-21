from django import forms

from .models import Post, Game, Team, Season


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('home_team', 'away_team', 'title', 'text',)


class GameForm(forms.ModelForm):
    # here I'm declaring the fields of hometeam, awayteam and season so I can override the queryset in the addgames view to
    # only show the teams and season related to the selected season
    hometeam = forms.ModelChoiceField(queryset=Team.objects.all())
    awayteam = forms.ModelChoiceField(queryset=Team.objects.all())
    season = forms.ModelChoiceField(queryset=Season.objects.all())

    class Meta:
        model = Game
        fields = ('date', 'gameweek', 'hometeam', 'homegoals', 'awaygoals', 'awayteam', 'season',)


class ContactForm(forms.Form):
    name = forms.CharField(required=True)
    email = forms.EmailField(required=True)
    subject = forms.CharField(required=True)
    message = forms.CharField(widget=forms.Textarea, required=True)
