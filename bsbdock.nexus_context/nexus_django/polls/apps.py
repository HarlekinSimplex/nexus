from django.apps import AppConfig

# import the logging library
import logging
# Get an instance of a logger
logger = logging.getLogger(__name__)


class PollsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'polls'

    def ready(self):
        # put your startup code here
        # Startup log with used parameter
        logger.info(" ____   _____ ____   _   _                      _____")
        logger.info("|  _ \\ / ____|  _ \\ | \\ | |                    / ____|")
        logger.info("| |_) | (___ | |_) ||  \\| | _____  ___   _ ___| (___   ___ _ ____   _____ _ __")
        logger.info("|  _ < \\___ \\|  _ < | . ` |/ _ \\ \\/ / | | / __|\\___ \\ / _ \\ '__\\ \\ / / _ \\ '__|")
        logger.info("| |_) |____) | |_) || |\\  |  __/>  <| |_| \\__ \\____) |  __/ |   \\ V /  __/ |")
        logger.info("|____/|_____/|____(_)_| \\_|\\___/_/\\_\\\\__,_|___/_____/ \\___|_|    \\_/ \\___|_|")
        logger.info("")
        logger.info("Copyright (c) 2022 Stephan Becker / Becker-Systemberatung, MIT License")
        logger.info("...............................................................................")
