from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Q
from .models import Room, Topic, Message
from .forms import RoomForm
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm

# it's gonna be called when calling an URL

# rooms = [
#     {'id': 1, 'name':'Lets learn Python'},
#     {'id': 2, 'name':'Design with me'},
#     {'id': 3, 'name':'Backend dev'},
# ]

def loginPage(request):
    # check to consider that page is login or register
    page = 'login'

    # to allow user haven't relogged in page
    if request.user.is_authenticated:
        return redirect('home')
    
    # checking valid account
    if request.method == 'POST':
        username = request.POST.get('username').lower()
        password = request.POST.get('password')

        try:
            user = User.objects.get(username=username)
        except:
            messages.error(request, 'User does not exist')
        
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, 'login was successfull')
            return redirect('home')
        else:
            messages.error(request, 'Username or password was incorrect!')
    context = {'page':page}
    return render(request, 'base/login_register.html', context)

def registerPage(request):
    form = UserCreationForm()

    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'an error occured druing registration')
    context = {'form':form}
    return render(request, 'base/login_register.html', context)

def logoutUser(request):
    # deleteing session of request
    logout(request)
    return redirect('home')

def home(request):
    q= request.GET.get('q') if request.GET.get('q') != None else ''

    rooms = Room.objects.filter(Q(topic__name__icontains=q) |
                                Q(name__icontains=q) |
                                Q(description__icontains=q)
                                )
    room_number = rooms.count()
    topics = Topic.objects.all()
    room_messages = Message.objects.filter(Q(room__topic__name__icontains=q)).order_by('-created')
    context = {'rooms':rooms, 'topics': topics, 'room_number':room_number, 'room_messages':room_messages}
    return render(request, 'base/home.html', context)

# Read
def room(request, pk):
    room = Room.objects.get(id=pk)
    room_messages = room.message_set.all().order_by('-created')
    # message_set : automatically created by django for reverse relation (n-1)
    # meaning: take all message in the room have id=pk
    # you can rename it in Message model by adding 'related_name' attribute in 'room' attribute
    
    room_participants = room.participants.all()

    # new comment was added recently by users
    if request.method == 'POST':
        message = Message.objects.create(
            user = request.user,
            room = room,
            body = request.POST.get('body')
        )
        # adding new member when they comment
        room.participants.add(request.user)
        # reload page to make sure that changes will be done
        return redirect('room', pk=room.id)
    context = {'room' : room, 'room_messages':room_messages, 'room_participants':room_participants}
    return render(request, 'base/room.html', context)
    
def userProfile(request, pk):
    user = User.objects.get(id=pk)
    rooms = user.room_set.filter(host__isnull=False)
    room_messages = user.message_set.all().order_by('-created')
    topics = Topic.objects.all()
    context = {'user':user, 'rooms':rooms, 'room_messages':room_messages,'topics':topics}
    return render(request, 'base/profile.html', context)

@login_required(login_url='login') 
def createRoom(request):
    form = RoomForm()
    topics = Topic.objects.all()
    
    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)
        
        Room.objects.create(
            host = request.user,
            topic = topic,
            name = request.POST.get('name'),
            description = request.POST.get('description'),
        )
        return redirect('home')

    context = {'form': form, 'topics': topics}
    return render(request, 'base/room_form.html', context)


@login_required(login_url='login')
def updateRoom(request, pk): 
    # pk : primary key : what was item changed ?
    room = Room.objects.get(id=pk)
    form = RoomForm(instance=room)
    topics = Topic.objects.all()

    if request.user != room.host:
        return HttpResponse('You are not allowed here!')

    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get(name=topic_name)
        room.name = request.POST.get('name')
        room.topic = topic
        room.description = request.POST.get('description')
        room.save()
    context = {'form':form, 'topics':topics, 'room': room}
    return render(request, 'base/room_form.html', context)

@login_required(login_url='login')
def deleteRoom(request, pk):
    room = Room.objects.get(id=pk) 

    if request.user != room.host:
        return HttpResponse('You are not allowed here!')
    
    if request.method == 'POST':
        room.delete()
        return redirect('home')
    context = {'obj': room}
    return render(request, 'base/delete.html', context)

@login_required(login_url='login')
def deleteMessage(request, pk):
    message = Message.objects.get(id=pk)

    if request.user != message.user:
        return HttpResponse('You are not allowed!')
    
    if request.method == 'POST':
        message.delete()
        return redirect('home')
    
    return render(request, 'base/delete.html', {'obj': message})
