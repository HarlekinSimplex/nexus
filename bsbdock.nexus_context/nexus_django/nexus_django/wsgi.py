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

env_dict = dict(os.environ)
print(env_dict["USER"], env_dict["NAME"])


def on_starting(server):
    # Pull up Reticulum stack as configured
    configpath = env_dict["RNS_CONFIG"]
    RNS.Reticulum(configpath)

    # Startup log with used parameter
    RNS.log("NX: ____   _____ ____   _   _                      _____", RNS.LOG_INFO)
    RNS.log("NX:|  _ \\ / ____|  _ \\ | \\ | |                    / ____|", RNS.LOG_INFO)
    RNS.log("NX:| |_) | (___ | |_) ||  \\| | _____  ___   _ ___| (___   ___ _ ____   _____ _ __", RNS.LOG_INFO)
    RNS.log("NX:|  _ < \\___ \\|  _ < | . ` |/ _ \\ \\/ / | | / __|\\___ \\ / _ \\ '__\\ \\ / / _ \\ '__|",
            RNS.LOG_INFO)
    RNS.log("NX:| |_) |____) | |_) || |\\  |  __/>  <| |_| \\__ \\____) |  __/ |   \\ V /  __/ |", RNS.LOG_INFO)
    RNS.log("NX:|____/|_____/|____(_)_| \\_|\\___/_/\\_\\\\__,_|___/_____/ \\___|_|    \\_/ \\___|_|", RNS.LOG_INFO)
    RNS.log("NX:", RNS.LOG_INFO)
    RNS.log("NX:Copyright (c) 2022 Stephan Becker / Becker-Systemberatung, MIT License", RNS.LOG_INFO)
    RNS.log("NX:...............................................................................", RNS.LOG_INFO)

    if configpath is not None:
        RNS.log("NX: Used RNS Config   " + configpath, RNS.LOG_INFO)
    else:
        RNS.log("NX: Used RNS Config   " + "RNS Default Location", RNS.LOG_INFO)

    RNS.log("NX:...............................................................................", RNS.LOG_INFO)
