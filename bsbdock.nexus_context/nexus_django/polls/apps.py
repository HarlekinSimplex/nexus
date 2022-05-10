import RNS
from django.apps import AppConfig

import logging
logger = logging.getLogger(__name__)


class PollsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'polls'

    def ready(self):
        # Pull up Reticulum stack as configured
        RNS.Reticulum()

        # Startup log with used parameter
        RNS.log(" ____   _____ ____   _   _                      _____", RNS.LOG_INFO)
        RNS.log("|  _ \\ / ____|  _ \\ | \\ | |                    / ____|", RNS.LOG_INFO)
        RNS.log("| |_) | (___ | |_) ||  \\| | _____  ___   _ ___| (___   ___ _ ____   _____ _ __", RNS.LOG_INFO)
        RNS.log("|  _ < \\___ \\|  _ < | . ` |/ _ \\ \\/ / | | / __|\\___ \\ / _ \\ '__\\ \\ / / _ \\ '__|", RNS.LOG_INFO)
        RNS.log("| |_) |____) | |_) || |\\  |  __/>  <| |_| \\__ \\____) |  __/ |   \\ V /  __/ |", RNS.LOG_INFO)
        RNS.log("|____/|_____/|____(_)_| \\_|\\___/_/\\_\\\\__,_|___/_____/ \\___|_|    \\_/ \\___|_|", RNS.LOG_INFO)
        RNS.log("", RNS.LOG_INFO)
        RNS.log("Copyright (c) 2022 Stephan Becker / Becker-Systemberatung, MIT License", RNS.LOG_INFO)
        RNS.log("...............................................................................", RNS.LOG_INFO)
