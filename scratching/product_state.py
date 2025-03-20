import json
import base64
from odoo.addons.http_routing.models.ir_http import slug
from odoo.addons.product_state.models.product_template import State
from odoo.tools import file_open
from scratching.app import run


def execute(env):
    products = env['product.template'].search([('default_code', '=', '15638')])

    for product in products:
        try:
            # sku = int(product.default_code)
            # if (1 <= sku <= 500_000) or (600_000 <= sku < 900_000):
            #     products.append(product)

            state = product.write({'state': State.APPROVED.key(), 'prev_state': State.UNDEFINED.key(), 'decommission_type': 'eol'})
            print(f" {product.default_code} state: {state}")
        except Exception as e:
            print(e)
            ...

if __name__ == '__main__':
    run(execute, commit_changes=False)
