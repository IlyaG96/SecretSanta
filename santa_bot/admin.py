from django.utils.safestring import mark_safe

from .models import Profile, Game, Raffle
from django.contrib import admin
from santa_bot.management.commands.tg_bot import perform_raffle

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'external_id', 'name', 'email', 'wishlist', 'message_for_Santa')


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ('creator_chat_id', 'name', 'price_limit_status', 'price_limit', 'registration_date', 'gift_dispatch_date', 'participants')


@admin.register(Raffle)
class RaffleAdmin(admin.ModelAdmin):
    list_display = ('raffle', 'raffles')

    def raffles(self, obj):
        perform_raffle()
        return mark_safe( f'<a role="button"><button class="btn btn-primary"> Жеребьевка </button></a>' )
# Register your models here.
