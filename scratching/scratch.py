import json

from odoo.addons.http_routing.models.ir_http import slug
from scratching.app import run


def get_breadcrumbs_structured_data(product):
    base_url = product.get_base_url()
    breadcrumbs = []

    count = 1
    for categ in product.public_categ_ids.parents_and_self:
        item = {
            "@type": "ListItem",
            "position": count,
            "name": categ.name,
            "item": base_url + f"/shop/category/{slug(categ)}"
        }
        breadcrumbs.append(item)

        count += 1

    structured_data = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": breadcrumbs,
    }

    return structured_data


def get_quantities_for_stores(env, product):
    stores = env["store.store"].sudo().search([])
    free_quantities = []

    for store in stores:
        quantities = (
            product.product_variant_id.with_context(location=store.stock_location_id.id)
            .sudo()
            ._compute_quantities_dict(
                lot_id=False,
                owner_id=False,
                package_id=False,
                from_date=False,
                to_date=False
            )
        )

        free_qty = quantities[product.product_variant_id.id].get('free_qty', 0)
        free_quantities.append(free_qty)

    return free_quantities


def get_brand(env, product):
    default_brand = env.ref('product_brand.default_brand')
    if product.brand_id == default_brand:
        return

    return {
        "brand": {
            "@type": "Brand",
            "name": product.name
        }
    }


def get_product_structured_data(env, product, website):
    base_url = product.get_base_url()
    url = base_url + product.website_url
    image_url = base_url + website.image_url(product, 'image_1920')

    free_quantities = get_quantities_for_stores(env, product)

    if sum(free_quantities) > 0:
        availability = "https://schema.org/InStock"
    else:
        availability = "https://schema.org/OutOfStock"

    structured_data = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": product.name,
        "image": image_url,
        "description": product.description,
        "sku": product.default_code,
        "gtin13": product.barcode,
        "url": url,
        "offers": {
            "@type": "Offer",
            "url": url,
            "priceCurrency": product.currency_id.name,
            "price": product.list_price,
            "itemCondition": "https://schema.org/NewCondition",
            "availability": availability,
        }
    }

    if brand := get_brand(env, product):
        structured_data.update(brand)

    return structured_data


def execute(env):
    product = env['product.template'].search([('default_code', '=', '13992')])
    website = env.ref('website.default_website')

    data = get_product_structured_data(env, product, website)
    print('<script data-rh="true" type="application/ld+json">')
    print(json.dumps(data, indent=4))

    data = get_breadcrumbs_structured_data(product)
    print('<script data-rh="true" type="application/ld+json">')
    print(json.dumps(data, indent=4))


run(execute)
