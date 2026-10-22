"""Reset the console password from the command line.

For the night you cannot get in. Beats editing the database by hand.

    docker exec week1-c2 sh -c 'cd /GooglePhish && \
        poetry run python manage.py c2password --reset'
"""
from django.core.management.base import BaseCommand

from Phisher.collector_views import PASSWORD_KEY, default_password, set_password, using_default
from Phisher.models import Setting


class Command(BaseCommand):
    help = 'Set or clear the console password.'

    def add_arguments(self, parser):
        parser.add_argument('--set', metavar='PASSWORD',
                            help='set a new password')
        parser.add_argument('--reset', action='store_true',
                            help='forget the stored one and fall back to C2_PASSWORD')

    def handle(self, *args, **options):
        if options['reset']:
            Setting.objects.filter(key=PASSWORD_KEY).delete()
            self.stdout.write(self.style.SUCCESS(
                f'Cleared. Sign in with the default: {default_password()}'))
            return

        new = options['set']
        if new:
            if len(new) < 8:
                self.stderr.write('Use at least 8 characters.')
                return
            set_password(new)
            self.stdout.write(self.style.SUCCESS('Password set.'))
            return

        self.stdout.write(
            'Still on the default.' if using_default() else 'A password has been set.')
        self.stdout.write('Use --set PASSWORD or --reset.')
