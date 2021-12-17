from django.utils.safestring import mark_safe

from .models import Profile
from .models import Game
from django.contrib import admin




@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'external_id', 'name', 'email', 'wishlist', 'message_for_Santa')


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ('profile', 'name', 'price_limit_status', 'price_limit', 'registration_date', 'gift_dispatch_date', 'raffle')

    def raffle(self, obj):
        return mark_safe( f'<a role="button"><button class="btn btn-primary"> Жеребьевка </button></a>' )
# Register your models here.
