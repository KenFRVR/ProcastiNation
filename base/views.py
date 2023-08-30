from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse

from .models import Room, Topic, Message, UserProfile
from .forms import RoomForm, UserProfileForm
import secrets

code_length = 6


def login_user(request):
    page = 'login'

    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username = request.POST['username'].lower()
        password = request.POST['password']

        try:
            User.objects.get(username=username)
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                messages.error(request, 'Wrong password')
        except User.DoesNotExist:
            messages.error(request, 'The user does not exist')

    context = {
        'page': page
    }

    return render(request, 'base/login_register.html', context)


def logout_user(request):
    logout(request)
    return redirect('home')


def register_user(request):
    form = UserCreationForm()

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            UserProfile.objects.create(user=user)
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Something went wrong during registration')

    context = {
        'form': form
    }

    return render(request, 'base/login_register.html', context)


def home(request):
    q = request.GET.get('q') or ''
    total_rooms = Room.objects.all()
    rooms = total_rooms.filter(
        Q(topic__name__icontains=q) |
        Q(name__icontains=q) |
        Q(description__icontains=q)
    )

    rooms_count = rooms.count()
    topics = Topic.objects.all()[0:5]
    room_messages = Message.objects.filter(Q(room__topic__name__icontains=q))[0:7]

    context = {
        'rooms': rooms,
        'topics': topics,
        'rooms_count': rooms_count,
        'room_messages': room_messages,
        'total_rooms': total_rooms.count()
    }

    return render(request, 'base/home.html', context)


# noinspection PyShadowingNames
@login_required(login_url='login')
def room(request, pk):
    room = get_object_or_404(Room, pk=pk)
    if room.type == 'private':
        return redirect('room-auth', pk=pk)

    room_messages = room.messages.all().order_by('created')
    participants = room.participants.all()

    if request.method == 'POST':
        Message.objects.create(
            user=request.user,
            room=room,
            body=request.POST['body']
        )
        room.participants.add(request.user)
        return redirect('room', pk=room.id)

    context = {
        'room': room,
        'room_messages': room_messages,
        'participants': participants
    }

    return render(request, 'base/room.html', context)


@login_required(login_url='login')
def room_private(request, pk):
    room = get_object_or_404(Room, pk=pk)

    room_messages = room.messages.all().order_by('created')
    participants = room.participants.all()

    if request.method == 'POST':
        Message.objects.create(
            user=request.user,
            room=room,
            body=request.POST['body']
        )
        room.participants.add(request.user)
        return redirect('room-private', pk=room.id)

    context = {
        'room': room,
        'room_messages': room_messages,
        'participants': participants
    }

    return render(request, 'base/room.html', context)


# noinspection PyShadowingNames
@login_required(login_url='login')
def room_auth(request, pk):
    room = get_object_or_404(Room, pk=pk)

    if request.method == 'POST':
        if request.POST['access_code'] == room.access_code:
           return redirect('room-private', pk=pk)
        else:
            messages.error(request, 'Wrong access code')

    context = {
        'room': room
    }

    return render(request, 'base/room-auth.html', context)


def user_profile(request, pk):
    user = User.objects.get(id=pk)
    rooms = user.rooms.all()
    room_messages = user.messages.all()
    total_rooms = Room.objects.all().count()
    topics = Topic.objects.all()[0:5]

    context = {
        'user': user,
        'topics': topics,
        'room_messages': room_messages,
        'rooms': rooms,
        'total_rooms': total_rooms
    }

    return render(request, 'base/profile.html', context)


# noinspection PyShadowingNames
@login_required(login_url='login')
def update_profile(request):
    user_profile = request.user.userprofile
    form = UserProfileForm(instance=user_profile)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            request.user.username = request.POST['username']
            request.user.save()
            form.save()
            return redirect('profile', pk=user_profile.user.id)
    context = {
        'form': form
    }

    return render(request, 'base/update-profile.html', context)


@login_required(login_url='login')
def create_room(request):
    form = RoomForm()
    topics = Topic.objects.all()

    if request.method == 'POST':
        topic_name = request.POST['topic']
        topic, created = Topic.objects.get_or_create(name=topic_name)
        code = ''

        room_type = request.POST['type']
        if room_type == 'private':
            code = secrets.token_urlsafe(code_length)

        Room.objects.create(
            host=request.user,
            name=request.POST['name'],
            topic=topic,
            description=request.POST['description'],
            type=request.POST['type'],
            access_code=code
        )

        return redirect('home')

    context = {
        'form': form,
        'topics': topics,

        'is_create': True
    }

    return render(request, 'base/room_form.html', context)


# noinspection PyShadowingNames
@login_required(login_url='login')
def update_room(request, pk):
    room = Room.objects.get(id=pk)
    form = RoomForm(instance=room)
    topics = Topic.objects.all()

    if request.user != room.host and not request.user.is_superuser:
        return HttpResponse('<p>You are not allowed here!</p>')

    if request.method == 'POST':
        topic_name = request.POST['topic']
        topic, created = Topic.objects.get_or_create(name=topic_name)

        room.name = request.POST['name']
        room.description = request.POST['description']
        room.topic = topic
        room.save()

        return redirect('home')

    context = {
        'form': form,
        'topics': topics,
        'room': room
    }

    return render(request, 'base/room_form.html', context)


# noinspection PyShadowingNames
@login_required(login_url='login')
def delete_room(request, pk):
    room = Room.objects.get(id=pk)

    if request.method == 'POST':
        room.delete()
        return redirect('home')

    return render(request, 'base/delete.html', {'obj': room})


@login_required(login_url='login')
def delete_message(request, pk):
    message = Message.objects.get(id=pk)

    if request.user != message.user and not request.user.is_superuser:
        return HttpResponse('You are not allowed here!')

    if request.method == 'POST':
        message.delete()
        return redirect('room', pk=message.room.id)

    return render(request, 'base/delete.html', {'obj': message})


def topics_page(request):
    q = request.GET.get('q') or ''
    topics = Topic.objects.filter(name__icontains=q)

    context = {
        'topics': topics
    }

    return render(request, 'base/topics.html', context)


def activity_page(request):
    room_messages = Message.objects.all()

    context = {
        'room_messages': room_messages
    }

    return render(request, 'base/activity.html', context)
