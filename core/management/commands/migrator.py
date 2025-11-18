from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = "Performs initial setup: collectstatic, migrate, create superuser, and populate initial data."

    def handle(self, *args, **options):
        self.stdout.write("Starting initial setup...")

        # Collect static files
        self.stdout.write("Collecting static files...")
        call_command('collectstatic', '--noinput', '--clear')

        # Make migrations for all apps
        self.stdout.write("Making migrations...")
        call_command('makemigrations', 'users', 'core', 'storage', 'finance', 'salary', 'treasury')

        # Run migrations
        self.stdout.write("Running migrations...")
        call_command('migrate', '--noinput')

        # Create superuser if it doesn't exist
        User = get_user_model()
        username = 'admin'
        email = 'admin@example.com'
        password = 'db123123'
        if not User.objects.filter(username=username).exists():
            self.stdout.write("Superuser not found. Creating superuser...")
            User.objects.create_superuser(username=username, email=email, password=password)
            self.stdout.write(self.style.SUCCESS(f'Successfully created superuser: {username}'))
        else:
            self.stdout.write(self.style.WARNING(f'Superuser {username} already exists.'))

        self.stdout.write(self.style.SUCCESS("Initial setup complete."))
