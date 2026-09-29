"""Break-glass account recovery, run on the Handoff server.

For the rare case where no one can sign in, for example a sole owner
who lost both their password and their recovery codes. Anyone who can
run commands on the server already controls it, so this adds no new
way in. It unlocks the account and prints a fresh set of recovery
codes; the person then uses "Forgot password?" on the login page.

Usage with Docker:
    docker exec handoff-backend python -m backend.reset_password owner@example.com
"""
import sys

from backend.auth_service import (
    create_recovery_codes,
    get_user_by_email,
    unlock_user,
)


def issue_break_glass_codes(email: str):
    """Unlock the account and return a fresh set of recovery codes,
    or None if no account uses that email."""
    user = get_user_by_email(email.strip().lower())

    if user is None:
        return None

    unlock_user(user.id)

    return create_recovery_codes(user.id)


def main(argv: list) -> int:
    if len(argv) != 2:
        print("Usage: python -m backend.reset_password <email>")
        return 2

    email = argv[1]
    codes = issue_break_glass_codes(email)

    if codes is None:
        print(f"No account uses {email}.")
        return 1

    print(f"New recovery codes for {email} (the old set no longer works):")

    for code in codes:
        print(f"  {code}")

    print('Use one on the login page under "Forgot password?".')

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))