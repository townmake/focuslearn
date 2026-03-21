
from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Reset all migrations by deleting records from django_migrations table'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM django_migrations;")
            self.stdout.write(self.style.SUCCESS('Successfully reset migrations'))
