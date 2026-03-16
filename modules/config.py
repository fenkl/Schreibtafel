from modules.Mhandle_log import setup_logging

class Config:
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Config, cls).__new__(cls, *args, **kwargs)
            cls._instance.LOG_NAME = "Schreibtafel"
            cls._instance.LOGGER = None
            cls._instance.LOG_LEVEL = "INFO"
            cls._instance.LOG_TO_STDOUT = False
            # NEU: Zeitgesteuerte Ruhezeiten (24h Format)
            cls._instance.WAKE_HOUR = 7   # 07:00 Uhr an
            cls._instance.SLEEP_HOUR = 1  # 01:00 Uhr aus
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._initialized = True

    def create_logger(self):
        self.LOGGER = setup_logging(
            log_to_stdout=self.LOG_TO_STDOUT,
            log_level=self.LOG_LEVEL,
            logger_name=self.LOG_NAME,
            overwrite_old_logger_name=True
        )

    def get_logger(self):
        if not self.LOGGER:
            self.create_logger()
        return self.LOGGER
