from scratching.app import run
import barcode

def execute(env):
    EAN = barcode.get_barcode_class('ean13')

    products = env["product.template"].search([('qty_available', '>', 0)])

    for product in products:
        if product.barcode:
            ean = EAN(product.barcode)
            ean.save(f"barcodes/{product.display_name}")


if __name__ == '__main__':
    run(execute, commit_changes=False)