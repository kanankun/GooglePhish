"""Write what was collected to CSV, for the write-up afterwards.

    docker exec week1-c2 sh -c 'cd /GooglePhish && \
        poetry run python manage.py export_captures' > class.csv

Passwords are left out unless you ask for them. The numbers are what the
write-up needs; the passwords are somebody's actual secret and do not
belong in a file that gets emailed around.
"""
import csv
import sys

from django.core.management.base import BaseCommand

from Phisher.models import SignIn, Visit


class Command(BaseCommand):
    help = 'Export visits and submissions as CSV.'

    def add_arguments(self, parser):
        parser.add_argument('--what', choices=['visits', 'submissions'],
                            default='visits')
        parser.add_argument('--with-passwords', action='store_true',
                            help='include the passwords. Think first.')

    def handle(self, *args, **options):
        out = csv.writer(sys.stdout)

        if options['what'] == 'visits':
            out.writerow(['when', 'ip', 'browser', 'os', 'screen',
                          'timezone', 'languages', 'cores', 'memory'])
            for v in Visit.objects.all():
                out.writerow([v.created.isoformat(), v.client_ip, v.browser, v.os,
                              v.screen, v.timezone, v.languages, v.cores, v.memory])
            return

        header = ['when', 'ip', 'email']
        if options['with_passwords']:
            header.append('password')
        out.writerow(header)
        for s in SignIn.objects.all():
            row = [s.date_time.isoformat(), s.client_ip, s.email]
            if options['with_passwords']:
                row.append(s.password)
            out.writerow(row)
