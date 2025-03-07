from babel.messages.extract import check_and_call_extract_file

from scratching.app import run


def execute(env):
    # Create the user
    user_vals = {
        'name': 'Test User',
        'login': 'test_user',
        'password': 'test_password',
    }
    new_user = env['res.users'].create(user_vals)

    # Ensure the user has been created
    assert new_user, "User creation failed; no user record returned."

    # Check that we can authenticate using the password
    # _check_credentials will raise an exception if the credentials are invalid
    new_user._check_credentials('test_password', env)

    # If the function completes without exceptions, we assume the login works
    assert(True, "User can successfully log in with the set password.")


if __name__ == '__main__':
    run(execute, commit_changes=False)