import json
import base64
from odoo.addons.http_routing.models.ir_http import slug
from odoo.tools import file_open
from scratching.app import run


def execute(env):
    items = env['product.template'].search([])
    # items = env['product.template'].search([('default_code', '=', '15416')])

    products = []

    for product in items:
        try:
            sku = int(product.default_code)
            if (1 <= sku <= 500_000) or (600_000 <= sku < 900_000):
                products.append(product)
        except:
            ...

    jsonobjs = []
    for product in products:
        item = process(product)
        jsonobjs.append(item)

    print(json.dumps(jsonobjs, indent=4))


def process(product):
    attributes = _get_stuff(product)
    category_name = _get_category_name(product)

    # print(
    #     f"""
    #     {product.name} [{product.default_code}]
    #     \t{category_name}
    #     \t{attributes}
    #     """.strip()
    # )

    for key, value in attributes.items():
        attributes.update({key: ";".join(value)})


    return {
        'id': product.id,
        'name': product.name,
        'category': category_name,
        'attributes': attributes
    }


def _get_category_name(product):
    if product.categ_id:
        if product.categ_id.alternative_name:
            return product.categ_id.alternative_name
        else:
            return product.categ_id.display_name


def _get_stuff(product):
    attributes = dict()

    for attribute_line in product.attribute_line_ids:
        key = attribute_line.attribute_id.with_context(lang='de_DE').name
        values = set(value.name for value in attribute_line.value_ids)

        if key in attributes:
            attributes[key].update(values)  # Use update instead of +
        else:
            attributes[key] = values

    return attributes


if __name__ == '__main__':
    run(execute, commit_changes=False)
