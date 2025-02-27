from babel.messages.extract import check_and_call_extract_file

from scratching.app import run


def execute(env):
    email = '%@gaschler.at%'
    new_password = "test"

    users = env['res.users'].search([('login', 'like', email)])

    if len(users) == 0:
        raise Exception(f'No user found with email {email}')

    for user in users:
        change_password(user, new_password, disable_2fa=True)
    
def change_password(user, new_password, disable_2fa=False):
    if user.has_group('base.group_user'):
        user._change_password(new_password)

    if disable_2fa:
        user.totp_secret = None
    else:
        raise Exception('No internal user! Aborting')



if __name__ == '__main__':
    run(execute, commit_changes=True)