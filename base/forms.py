# Model Form
from django.forms import ModelForm
from django import forms
from .models import Room


class RoomForm(ModelForm):
    class Meta: # config the form
        model = Room # connect RoomForm to Room model
        fields = '__all__' # to add automatically the fields in Room model

