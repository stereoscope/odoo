import json
import base64
from odoo.addons.http_routing.models.ir_http import slug
from odoo.addons.product_state.models.product_template import State
from odoo.tools import file_open
from scratching.BarcodeGenerator.generate_codes import BarcodeGenerator
from scratching.app import run


def execute(env):
    products = env['product.template'].search([('detailed_type', '=', 'product')])

    generator = BarcodeGenerator()
    generator.genreate(products)

if __name__ == '__main__':
    run(execute, path_to_config='../..', commit_changes=False)
