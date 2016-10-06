from django import forms

from .models import Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('home_team', 'away_team', 'title', 'text',)


#class GameForm(forms.form):
