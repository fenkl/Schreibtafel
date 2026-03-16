#!/usr/bin/python3
# Author                   : Francisco Fenkl
# Datum 1. Version         : 04.02.2025
# Grundsaetzliche Funktion : Logger-Setup

import logging
import sys
from logging.handlers import SysLogHandler  # , SMTPHandler

class OnlyWarningFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        """
        # Nur Logeinträge mit dem Level WARNING durchlassen
        :param record: logging.LogRecord
        :return: True, wenn record.levelno dem Loglevel Warning (level 30) entspricht. False, wenn nicht
        """
        return record.levelno == logging.WARNING


def handler_exists(logger: logging.Logger, handler_type: type, level: int) -> bool:
    """
    Überprüft, ob im Logger bereits ein Handler vom Typ handler_type existiert,
    dessen Level mit dem gewünschten Level übereinstimmt.
    """
    return any(isinstance(h, handler_type) and h.level == level for h in logger.handlers)


def setup_logging(logger_name: str = "wohnungssuche_bot",
                  log_level: str = "INFO",
                  log_to_stdout: bool = False,
                  unique_logger: bool = False,
                  overwrite_old_logger_name: bool = False) -> logging.Logger:
    """
    Konfiguriert und gibt ein Logger-Objekt zurück.
    Wird der Logger bereits konfiguriert, so erfolgt keine erneute Konfiguration (außer bei unique_logger
    oder overwrite_old_logger_name).
    :param logger_name: Logname des Loggers
    :param log_level: Loglevel des Loggers (z.B. "DEBUG", "INFO", "ERROR")
    :param log_to_stdout: Wenn True, loggt der Logger nach stdout, statt syslog zu verwenden
    :param unique_logger: Wenn True, wird ein einzigartiger Logger erstellt, egal ob schon einer vorhanden ist
    :param overwrite_old_logger_name: Wenn True, wird der Logger zurückgesetzt (alle Handler entfernt)
    :return: Konfiguriertes Logger-Objekt
    """
    logger = logging.getLogger(logger_name)

    # Falls der Logger bereits konfiguriert wurde, direkt zurückgeben, außer overwrite ist aktiv
    if getattr(logger, '_configured', False) and not unique_logger:
        if not overwrite_old_logger_name:
            return logger

    # Wenn overwrite_old_logger_name gesetzt ist, alle bestehenden Handler entfernen
    if overwrite_old_logger_name:
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        logger.handlers.clear()

    # Logger-Level setzen
    logger.setLevel(log_level)

    # Handler konfigurieren, abhängig davon, ob ins stdout oder Syslog geschrieben werden soll
    # Auf Windows gibt es kein /dev/log, daher dort immer stdout als Fallback
    if log_to_stdout or sys.platform == "win32":
        log_handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            f"%(asctime)s - {logger_name} - %(levelname)s - [%(filename)s.%(funcName)s:%(lineno)s] - %(message)s"
        )
    else:
        # Konfiguration für Syslog
        log_handler = SysLogHandler(address="/dev/log")
        formatter = logging.Formatter(
            f"{logger_name} - %(levelname)s - [%(filename)s.%(funcName)s:%(lineno)s] - %(message)s"
        )
        log_handler.setLevel(log_level)
        log_handler.setFormatter(formatter)

        # Überprüfen, ob bereits ein Handler desselben Typs im Logger vorhanden ist.
        # Falls nicht, wird der aktuelle Handler hinzugefügt, um doppelte Handler zu vermeiden.
        if not any(isinstance(h, type(log_handler)) for h in logger.handlers):
            logger.addHandler(log_handler)

        # Gemeinsamer Formatter für beide SMTPHandler
        smtp_formatter = logging.Formatter(
            fmt="%(asctime)s - %(levelname)-8s - %(filename)s - %(funcName)s - Zeile %(lineno)s - %(message)s",
            datefmt='%d.%m.%Y %H:%M:%S'
        )
        """
        # SMTPHandler für Warnungen hinzufügen (sofern nicht schon vorhanden)
        if not handler_exists(logger, SMTPHandler, logging.WARNING):
            warning_smtp_handler = SMTPHandler(
                mailhost="mail.kikxxl.corp",
                fromaddr="noreply@kikxxl.de",
                toaddrs=LST_EMPFAENGER_DEV_LOG_WARNING,
                subject="Warnung in wikiexport_to_vectordb"
            )
            warning_smtp_handler.setLevel(logging.WARNING)
            warning_smtp_handler.setFormatter(smtp_formatter)
            # Filter hinzufügen, der nur Warnungen (und nichts darüber z.B. Error) durchlässt
            warning_smtp_handler.addFilter(OnlyWarningFilter())
            logger.addHandler(warning_smtp_handler)

        # SMTPHandler für Fehler hinzufügen (sofern nicht schon vorhanden)
        if not handler_exists(logger, SMTPHandler, logging.ERROR):
            error_smtp_handler = SMTPHandler(
                mailhost="mail.kikxxl.corp",
                fromaddr="noreply@kikxxl.de",
                toaddrs=LST_EMPFAENGER_DEV_LOG_ERROR,
                subject="Fehler in wikiexport_to_vectordb"
            )
            error_smtp_handler.setLevel(logging.ERROR)
            error_smtp_handler.setFormatter(smtp_formatter)
            logger.addHandler(error_smtp_handler)
        """

    log_handler.setLevel(log_level)
    log_handler.setFormatter(formatter)
    logger.addHandler(log_handler)

    # Flag, um in Zukunft die erneute Konfiguration zu vermeiden.
    if not unique_logger:
        logger._configured = True

    return logger


if __name__ == "__main__":
    log = setup_logging(log_to_stdout=True)
    log.info("Dies ist eine Testmeldung.")
