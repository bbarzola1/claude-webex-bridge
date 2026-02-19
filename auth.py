import logging

from config import WEBEX_USER_EMAIL

logger = logging.getLogger(__name__)


def is_authorized(person_email: str) -> bool:
    """Check if the sender's email matches the authorized user."""
    if person_email.lower() == WEBEX_USER_EMAIL.lower():
        return True
    logger.warning("Unauthorized message from: %s", person_email)
    return False
