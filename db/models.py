import sys

try:
    from django.db import models
except Exception:
    print('Exception: Django Not Found, please install it with "pip install django".')
    sys.exit()


# Sample User model
class Profile(models.Model):
    first_name = models.CharField(max_length=64)
    last_name = models.CharField(max_length=64, null=True, blank=True)
    score = models.PositiveIntegerField(default=0, null=True, blank=True)
    user_id = models.PositiveIntegerField(unique=True)
    level = models.PositiveSmallIntegerField(default=1)

    def __str__(self):
        return self.first_name
