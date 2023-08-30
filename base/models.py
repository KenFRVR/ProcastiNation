from django.contrib.auth.models import User
from django.db import models


class Topic(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class Room(models.Model):
    host = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='rooms', null=True)
    topic = models.ForeignKey(Topic, on_delete=models.SET_NULL, related_name='rooms', null=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    participants = models.ManyToManyField(User, related_name='participants', blank=True)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    type = models.CharField(max_length=8, default='public', choices=[
        ('public', 'Public'),
        ('private', 'Private'),
    ])
    access_code = models.CharField(max_length=6, blank=True)

    class Meta:
        ordering = ['-updated', '-created']

    def __str__(self):
        return self.name


class Message(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='messages')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='messages')
    body = models.TextField()
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-updated', '-created']

    def __str__(self):
        return self.body


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(default='avatar.svg')
    bio = models.TextField(blank=True, default='This my boring bio :v')
    full_name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True, unique=True, null=True)

    def __str__(self):
        return self.user.username
