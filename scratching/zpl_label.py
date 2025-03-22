from scratching.app import run
from zpl import TCPPrinter
from odoo.addons.product_label_print.services.custom_label import PriceLabel

def execute(env):
    default_code = "13584"
    product = env['product.template'].search([('default_code', '=', default_code)])

    wizard = env['product.label.print.wizard']
    data = wizard._get_data(product)

    PriceLabel().create(data).preview()

    # label = PriceLabel().create(data).dumpZPL()
    # TCPPrinter('192.168.82.119', 9100).send_job(label)




run(execute)
