import json

from odoo.addons.http_routing.models.ir_http import slug
from scratching.app import run

def execute(env):
    user = env['res.users'].search([('name', 'ilike', 'eibel')])
    print(user.name)

    for group in user.groups_id:
        if 'inventory' in group.display_name.lower():
            print(f"{group.display_name} : {group.category_id.name} ")


run(execute)
