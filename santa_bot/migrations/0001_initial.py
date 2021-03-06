# Generated by Django 3.2.7 on 2021-12-21 23:00

from django.db import migrations, models
import jsonfield.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Game',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=256)),
                ('game_hash', models.CharField(default=None, max_length=256)),
                ('participants', jsonfield.fields.JSONField(default={})),
                ('price_limit_status', models.BooleanField(default=False, verbose_name='Безлимит')),
                ('price_limit', models.CharField(default='Золотая карта', max_length=256)),
                ('creator_chat_id', models.CharField(default=None, max_length=256)),
                ('registration_date', models.DateField()),
                ('gift_dispatch_date', models.DateField()),
            ],
            options={
                'verbose_name': 'Игра',
                'verbose_name_plural': 'Игры',
            },
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('external_id', models.PositiveIntegerField(unique=True, verbose_name='Внешний ID пользователя')),
                ('name', models.TextField(verbose_name='Имя пользователя')),
                ('email', models.EmailField(max_length=254, verbose_name='email')),
                ('wishlist', models.CharField(max_length=256, verbose_name='Интересы')),
                ('message_for_Santa', models.TextField(verbose_name='Письмо Санте')),
            ],
            options={
                'verbose_name': 'Профиль',
                'verbose_name_plural': 'Профили',
            },
        ),
        migrations.CreateModel(
            name='Raffle',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('raffle', models.CharField(max_length=256)),
            ],
            options={
                'verbose_name': 'Провести жеребьевку',
            },
        ),
    ]
