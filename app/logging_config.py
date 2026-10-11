import logging

logger = logging.getLogger("event-desk")
handler = logging.FileHandler("event-desk.log")
handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
logger.addHandler(handler)
logger.setLevel(logging.INFO)
