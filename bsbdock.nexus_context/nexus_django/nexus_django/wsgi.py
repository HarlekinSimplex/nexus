"""
WSGI config for nexus_django project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/howto/deployment/wsgi/
"""

import os

import RNS
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nexus_django.settings')

application = get_wsgi_application()


def on_starting(server):
    # Pull up Reticulum stack as configured
    RNS.Reticulum()

    # Startup log with used parameter
    RNS.log(" ____   _____ ____   _   _                      _____", RNS.LOG_INFO)
    RNS.log("|  _ \\ / ____|  _ \\ | \\ | |                    / ____|", RNS.LOG_INFO)
    RNS.log("| |_) | (___ | |_) ||  \\| | _____  ___   _ ___| (___   ___ _ ____   _____ _ __", RNS.LOG_INFO)
    RNS.log("|  _ < \\___ \\|  _ < | . ` |/ _ \\ \\/ / | | / __|\\___ \\ / _ \\ '__\\ \\ / / _ \\ '__|",
            RNS.LOG_INFO)
    RNS.log("| |_) |____) | |_) || |\\  |  __/>  <| |_| \\__ \\____) |  __/ |   \\ V /  __/ |", RNS.LOG_INFO)
    RNS.log("|____/|_____/|____(_)_| \\_|\\___/_/\\_\\\\__,_|___/_____/ \\___|_|    \\_/ \\___|_|", RNS.LOG_INFO)
    RNS.log("", RNS.LOG_INFO)
    RNS.log("Copyright (c) 2022 Stephan Becker / Becker-Systemberatung, MIT License", RNS.LOG_INFO)
    RNS.log("...............................................................................", RNS.LOG_INFO)
