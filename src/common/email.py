from django.conf import settings
from django.core.mail import send_mail


def email_noreply(address, subject, message, **kwargs):
    email(settings.DEFAULT_FROM_EMAIL, [address], subject, message, **kwargs)


def email(sender, addresses, subject, message, **kwargs):

    for address in addresses:

        if settings.DEBUG_EMAIL:
            print("FROM", sender)
            print("TO", address)
            print("SUBJ", subject)
            print("--------------")
            print(message)
            print("--------------")
            continue

        send_mail(f"{subject}", f"{message}", sender, [address], **kwargs)
