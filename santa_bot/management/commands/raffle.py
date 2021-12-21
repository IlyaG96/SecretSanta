from .tg_bot import perform_raffle
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    def handle(self, *args, **options):
        perform_raffle()
