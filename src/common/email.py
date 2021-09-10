from django.conf import settings
from django.core.mail import send_mail


import logging

logger = logging.getLogger("django")


def email_noreply(address, subject, message, **kwargs):
    email(settings.DEFAULT_FROM_EMAIL, [address], subject, message, **kwargs)


def email(sender, addresses, subject, message, **kwargs):

    for address in addresses:

        if settings.DEBUG_EMAIL:
            logger.info("FROM: " + sender)
            logger.info("TO: " + address)
            logger.info("SUBJ: " + subject)
            logger.info("--------------")
            logger.info(message)
            logger.info("--------------")
            continue

        send_mail(f"{subject}", f"{message}", sender, [address], **kwargs)
