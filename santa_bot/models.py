import jsonfield
from django.db import models

class Profile(models.Model):
    external_id = models.PositiveIntegerField(
        verbose_name='Внешний ID пользователя',
        unique=True,
    )
    name = models.TextField(
        verbose_name='Имя пользователя',
    )
    email = models.EmailField(max_length=254, verbose_name='email',)
    wishlist = models.CharField(max_length = 256, verbose_name='Интересы')
    message_for_Santa = models.TextField(
        verbose_name='Письмо Санте',
    )
    def __str__(self):
        return f'{self.name}'

    class Meta:
        verbose_name = 'Профиль'
        verbose_name_plural = 'Профили'


class Game(models.Model):
    name = models.CharField(max_length = 256)
    game_hash = models.CharField(max_length = 256, default=None)
    participants = jsonfield.JSONField(default={})
    price_limit_status = models.BooleanField(default=False,
        verbose_name='Безлимит'
    )
    price_limit = models.CharField(max_length = 256, default = 'Золотая карта')
    creator_chat_id = models.CharField(max_length = 256, default=None)
    registration_date = models.DateField()
    gift_dispatch_date = models.DateField()
    class Meta:
        verbose_name = 'Игра'
        verbose_name_plural = 'Игры'

class Raffle(models.Model):
    raffle = models.CharField(max_length = 256)
    class Meta:
        verbose_name = 'Провести жеребьевку'
# Create your models here.
