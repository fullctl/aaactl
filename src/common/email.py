import logging

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger("django")


def email_noreply(address, subscriptionject, message, **kwargs):
    email(settings.DEFAULT_FROM_EMAIL, [address], subscriptionject, message, **kwargs)


def email(sender, addresses, subscriptionject, message, **kwargs):
    for address in addresses:
        if settings.DEBUG_EMAIL:
            logger.info("FROM: " + sender)
            logger.info("TO: " + address)
            logger.info("SUBJ: " + subscriptionject)
            logger.info("--------------")
            logger.info(message)
            logger.info("--------------")
            continue

        send_mail(f"{subscriptionject}", f"{message}", sender, [address], **kwargs)
