# -*- coding: utf-8 -*-
import sys, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','running_project.settings')

import django
django.setup()

from random import choice, randint
from datetime import datetime
from django.contrib.auth.models import User

# Disable printing
def blockPrint():
    sys.stdout = open(os.devnull, 'w')

# Restore printing
def enablePrint():
    sys.stdout = sys.__stdout__

def populate():
    u = User.objects.get_or_create(username="admin")[0]
    u.password = "argon2$argon2i$v=19$m=512,t=2,p=2$dXNNempMWE02T2p4$amQEn7mi4LjQ6WVal8sDtQ"
    u.is_superuser = 1
    u.first_name = "John"
    u.last_name = "Admin"
    u.email = "admin@got-the-runs.co.uk"
    u.is_staff = 1
    u.is_active = 1
    u.save()

# Known as the populate function
if __name__ == '__main__':
	print("Starting Policy Tracker population script...")
	if len(sys.argv) > 1:
		if str(sys.argv[1]) == '-debug':
			populate()
			print("Populating complete...")
	else:
		blockPrint()
		populate()
		enablePrint()
		print("Populating complete...")
		print("Completed with all messages hidden. Add '-debug' to view all logging.")
