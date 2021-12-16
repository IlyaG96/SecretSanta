from django.contrib import admin

from .models import Profile
from .models import Game


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'external_id', 'name', 'email', 'wishlist', 'message_for_Santa')


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ('profile', 'name', 'price_limit_status', 'price_limit', 'registration_date', 'gift_dispatch_date')

# Register your models here.
