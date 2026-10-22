from django.db import models


class Setting(models.Model):
    """Small key/value store.

    Holds the console password once it has been changed from the default.
    Kept here rather than in the environment so you can change it from the
    browser on the night, without editing a file or restarting anything.
    The value is a hash, never the password.
    """
    key = models.CharField(max_length=40, primary_key=True)
    value = models.TextField(blank=True, default='')
    updated = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.key


class Visit(models.Model):
    """One row per person who opened the page.

    Written before anybody types anything, which is the point: a visitor
    who reads the page, decides it looks wrong and closes it has still
    told you their address, their browser and roughly where they are.

    The server fills in what it can see from the request; the browser
    volunteers the rest a moment later through /collect.
    """
    created   = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)
    # How many times this browser has loaded the page. One row per person,
    # so the headline count stays honest, but a refresh still shows up.
    hits      = models.PositiveIntegerField(default=1)
    vid       = models.CharField(max_length=32, db_index=True)
    client_ip = models.CharField(max_length=64, blank=True, default='')
    browser   = models.CharField(max_length=48, blank=True, default='')
    os        = models.CharField(max_length=48, blank=True, default='')
    language  = models.CharField(max_length=120, blank=True, default='')
    referer   = models.CharField(max_length=300, blank=True, default='')
    user_agent = models.TextField(blank=True, default='')

    # filled in by the beacon
    screen    = models.CharField(max_length=24, blank=True, default='')
    window    = models.CharField(max_length=24, blank=True, default='')
    timezone  = models.CharField(max_length=64, blank=True, default='')
    languages = models.CharField(max_length=120, blank=True, default='')
    cores     = models.CharField(max_length=8,  blank=True, default='')
    memory    = models.CharField(max_length=8,  blank=True, default='')
    platform  = models.CharField(max_length=48, blank=True, default='')
    touch     = models.CharField(max_length=8,  blank=True, default='')

    class Meta:
        ordering = ['-created']

    def __str__(self) -> str:
        return f'{self.client_ip} {self.browser}/{self.os}'


class SignIn(models.Model):
    email = models.EmailField()
    # Was 32, while the view truncated at 128. SQLite ignores the limit so
    # it never showed up; Postgres would not have been so forgiving.
    password = models.CharField(max_length=128)
    date_time = models.DateTimeField(auto_now_add=True)
    client_ip = models.CharField(max_length=32, null=True)
    vid = models.CharField(max_length=32, blank=True, default='', db_index=True)
    browser = models.CharField(max_length=48, blank=True, default='')
    os = models.CharField(max_length=48, blank=True, default='')

    class Meta:
        ordering = ['-date_time']

    def __str__(self) -> str:
        return self.email
