from babel.messages.extract import check_and_call_extract_file

from odoo.exceptions import UserError
from scratching.app import run


def execute(env):
    # Create the user
    error = UserError("TEST")
    error


if __name__ == '__main__':
    run(execute, commit_changes=False)