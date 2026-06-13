"""Disposable email domain blocking for abuse prevention."""

from disposable_email_domains import blocklist


def is_disposable_email(email: str) -> bool:
    """Check if email is from a disposable domain.

    Checks all parent domains to handle subdomains like foo.tempmail.com.

    Args:
        email: Email address to check

    Returns:
        True if disposable (should block), False if legitimate
    """
    try:
        domain = email.split("@")[1].lower()
    except IndexError:
        return True  # Invalid email format - treat as disposable

    parts = domain.split(".")
    # Check each possible parent domain
    for i in range(len(parts)):
        check_domain = ".".join(parts[i:])
        if check_domain in blocklist:
            return True
    return False
