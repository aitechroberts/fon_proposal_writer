# logging_config.py
import logging
from logging.config import dictConfig

NOISY_LIBS = [
    "streamlit", "tornado", "urllib3", "httpx", "watchdog",
    "asyncio", "litellm", "openai", "azure",
    "azure.core.pipeline.policies.http_logging_policy",
    "numexpr.utils",
]

def setup_logging(app_level="INFO", lib_level="ERROR"):
    root = logging.getLogger()

    # If we already configured, bail
    if getattr(root, "_configured_by_us", False):
        return

    # 🔨 HARD RESET any prior handlers/filters Streamlit may have added
    for h in list(root.handlers):
        root.removeHandler(h)
    root.filters.clear()

    dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "std": {"format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s"},
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "std",
                "level": "DEBUG",
                "stream": "ext://sys.stderr",
            },
        },
        # Keep root high so random libs don't spam
        "root": {"level": "WARNING", "handlers": ["console"]},

        # Attach console directly to our namespaces, no propagation
        "loggers": {
            "app":      {"level": app_level, "handlers": ["console"], "propagate": False},
            "main": {"level": app_level, "handlers": ["console"], "propagate": False},

            # Silence noisy libs early
            **{lib: {"level": lib_level, "propagate": False} for lib in NOISY_LIBS},
        },
    })

    root._configured_by_us = True
