"""Emails to members.

outbox.txt stands in for a mail server. Only send_email knows that, so
switching to real email means changing this one function.
"""
from policy import money

OUTBOX_PATH = "outbox.txt"


def send_email(to, subject, body):
    with open(OUTBOX_PATH, "a") as f:
        f.write("TO: " + to + " | SUBJECT: " + subject + " | BODY: " + body + "\n")


def checkout_confirmation(email, title):
    send_email(email, "Book checked out", "You checked out " + title)


def renewal_confirmation(email, title):
    send_email(email, "Loan renewed", "You renewed " + title)


def return_receipt(email, title, fine):
    send_email(email, "Book returned", "You returned " + title + ". Fine: $" + str(money(fine)))


def payment_receipt(email, amount):
    send_email(email, "Fine paid", "We received $" + str(money(amount)))
