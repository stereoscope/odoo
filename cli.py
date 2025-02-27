#!/usr/bin/env python3
import argparse
from scratching.app import run

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="CLI to reset Odoo user passwords and optionally disable 2FA."
    )
    parser.add_argument(
        "-u", "--username",
        help="Email (or partial match) of the user for whom the password is being reset",
        required=True
    )
    parser.add_argument(
        "-p", "--password",
        help="New password to set for the user",
        required=True
    )
    parser.add_argument(
        "--disable-2fa",
        action="store_true",
        help="Whether to disable 2FA (TOTP) for the user."
    )
    return parser.parse_args()


def change_password(user, new_password, disable_2fa=False):
    """Internal function that changes a user's password and optionally disables 2FA."""
    if user.has_group('base.group_user'):
        user._change_password(new_password)

        if disable_2fa:
            user.totp_secret = None  # This should remove 2FA (TOTP) for the user
    else:
        raise Exception(f"User {user.name} is not an internal user. Aborting.")


def execute(env, args):
    """Main execute function called by run() to do the work inside Odoo's environment."""
    email = args.username
    new_password = args.password
    disable_2fa = args.disable_2fa

    # Search for users by login that "ilike" the provided email string
    users = env["res.users"].search([("login", "ilike", email)])
    if not users:
        raise Exception(f"No user found with email matching '{email}'")

    for user in users:
        print(f"Changing password for user: {user.login} (ID: {user.id})")
        change_password(user, new_password, disable_2fa=disable_2fa)
        print(f"  -> Password updated. 2FA disabled = {disable_2fa}")

def main():
    """CLI entry point."""
    args = parse_args()

    # We define a wrapper function so that we can pass `args` into `execute`.
    def runner(env):
        execute(env, args)

    # The `run` function sets up the Odoo environment,
    # calls `runner`, and optionally commits changes.
    run(runner, path_to_config='.', commit_changes=True)


if __name__ == "__main__":
    main()
