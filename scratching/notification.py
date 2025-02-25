from scratching.app import run


def execute(env):
    user = env['res.users'].browse(7)
    type = "success"
    notify(env, user, 'title', 'message', type=type)

def notify(env, recipient, title, message, sticky=False, message_type='simple_notification', type='warning'):

    message = {
        "title": title,
        "message": message,
        "sticky": sticky,
        "type": type,
    }

    env["bus.bus"]._sendone(recipient.partner_id, message_type, message)


if __name__ == '__main__':
    run(execute, commit_changes=False)