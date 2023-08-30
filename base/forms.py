from django.forms import ModelForm
from .models import Room, UserProfile


class RoomForm(ModelForm):
    class Meta:
        model = Room
        fields = '__all__'
        exclude = ['host', 'participants', 'access_code']


class UserProfileForm(ModelForm):
    class Meta:
        model = UserProfile
        fields = ['avatar', 'full_name', 'email', 'bio']
