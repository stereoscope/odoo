from odoo import Command
from scratching.app import run

def execute(env):
    user = env['res.users'].browse(7)
    message = "Hello <strong>man</strong>"

    post_message(env, user, message, message_type="auto_comment")

def post_message(env, recipient, message, message_type='notification'):
    """
    Sends a direct chat message to the current user's Discuss channel in Odoo 16.
    receipient is a user

    """
    user = recipient
    current_user = user
    current_partner = user.partner_id

    # 2) Find an existing private 'chat' channel that contains ONLY this user
    channels = env['mail.channel'].search([
        ('channel_type', '=', 'chat'),
        ('channel_partner_ids', 'in', [current_partner.id]),
    ])

    # We only want the channel if it has exactly this one partner (the user).
    # That is, a 1-person "private chat" channel with themselves.
    channels = channels.filtered(lambda ch: ch.member_count == 1)

    # 3) If no channel exists, create a new one
    if not channels:
        channel = env['mail.channel'].create({
            'channel_partner_ids': [Command.link(current_partner.id)],
            'channel_type': 'chat',
            'name': "Private Channel for %s" % current_user.name,
        })
    else:
        channel = channels[0]

    # 4) Post the message in that channel.
    #    'author_id' controls who appears as the sender.
    #    If you want the message to appear as coming from the user themselves:
    author_partner_id = None # show odoo_bot as sender

    channel.message_post(
        body=message,
        message_type=message_type,
        subtype_xmlid='mail.mt_comment',
        author_id=author_partner_id
    )

if __name__ == '__main__':
    run(execute)