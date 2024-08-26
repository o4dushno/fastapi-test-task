from src.auth.schemas import MailTaskSchema
from src.core.logging import logger


def user_mail_event(payload: MailTaskSchema):
    # Send mail to user here
    # Now printing only token
    logger.info(f"[ Mail Schecma ]: {payload}")
