# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http
from odoo.http import request


class ProductConfiguratorController(http.Controller):
    @http.route(['/sale_product_configurator/configure'], type='json', auth="user", methods=['POST'])
    def configure(self, product_template_id, pricelist_id, **kw):
        add_qty = float(kw.get('quantity', 1))
        product_template = request.env['product.template'].browse(int(product_template_id))
        pricelist = self._get_pricelist(pricelist_id)

        product_combination = False
        attribute_value_ids = set(kw.get('product_template_attribute_value_ids', []))
        attribute_value_ids |= set(kw.get('product_no_variant_attribute_value_ids', []))
        if attribute_value_ids:
            product_combination = request.env['product.template.attribute.value'].browse(
                attribute_value_ids
            ).filtered(
                lambda ptav: ptav.product_tmpl_id == product_template
            )  # Filter out ptavs not belonging to the given template
            # It happens when you change the template on an already configured line
            # receiving the configured attributes data from the previous template configuration.

        if pricelist:
            product_template = product_template.with_context(pricelist=pricelist.id, partner=request.env.user.partner_id)

        return request.env['ir.ui.view']._render_template(
            "sale_product_configurator.configure",
            {
                'product': product_template,
                'pricelist': pricelist,
                'add_qty': add_qty,
                'product_combination': product_combination
            },
        )

    @http.route(['/sale_product_configurator/show_advanced_configurator'], type='json', auth="user", methods=['POST'])
    def show_advanced_configurator(self, product_id, variant_values, pricelist_id, **kw):
        pricelist = self._get_pricelist(pricelist_id)
        return self._show_advanced_configurator(product_id, variant_values, pricelist, False, **kw)

    @http.route(['/sale_product_configurator/optional_product_items'], type='json', auth="user", methods=['POST'])
    def optional_product_items(self, product_id, pricelist_id, **kw):
        pricelist = self._get_pricelist(pricelist_id)
        return self._optional_product_items(product_id, pricelist, **kw)

    def _optional_product_items(self, product_id, pricelist, **kw):
        add_qty = float(kw.get('add_qty', 1))
        product = request.env['product.product'].browse(int(product_id))

        parent_combination = product.product_template_attribute_value_ids
        if product.env.context.get('no_variant_attribute_values'):
            # Add "no_variant" attribute values' exclusions
            # They are kept in the context since they are not linked to this product variant
            parent_combination |= product.env.context.get('no_variant_attribute_values')

        exclude_product_tmpl_ids = kw.get('exclude_product_tmpl_ids')
        if exclude_product_tmpl_ids:
            # Temporarily exclude products from being in `optional_product_ids`
            # to avoid issues with mutually recursive/cyclic optional products
            optional_products = product.optional_product_ids
            exclude_products = request.env['product.template'].browse(exclude_product_tmpl_ids)
            request.env.cache.update(
                product,
                product._fields['optional_product_ids'],
                [(optional_products - exclude_products).ids],
            )
        res = request.env['ir.ui.view']._render_template("sale_product_configurator.optional_product_items", {
            'product': product,
            'parent_name': product.name,
            'parent_combination': parent_combination,
            'pricelist': pricelist,
            'add_qty': add_qty,
        })
        if exclude_product_tmpl_ids:
            # Re-add the excluded products after rendering the configurator template
            request.env.cache.update(
                product,
                product._fields['optional_product_ids'],
                [optional_products.ids],
            )
        return res

    def _show_advanced_configurator(self, product_id, variant_values, pricelist, handle_stock, **kw):
        product = request.env['product.product'].browse(int(product_id))
        combination = request.env['product.template.attribute.value'].browse(variant_values)
        add_qty = float(kw.get('add_qty', 1))

        no_variant_attribute_values = combination.filtered(
            lambda product_template_attribute_value: product_template_attribute_value.attribute_id.create_variant == 'no_variant'
        )
        if no_variant_attribute_values:
            product = product.with_context(no_variant_attribute_values=no_variant_attribute_values)

        return request.env['ir.ui.view']._render_template("sale_product_configurator.optional_products_modal", {
            'product': product,
            'combination': combination,
            'add_qty': add_qty,
            'parent_name': product.name,
            'variant_values': variant_values,
            'pricelist': pricelist,
            'handle_stock': handle_stock,
            'already_configured': kw.get("already_configured", False),
            'mode': kw.get('mode', 'add'),
            'product_custom_attribute_values': kw.get('product_custom_attribute_values', None),
            'no_attribute': kw.get('no_attribute', False),
            'custom_attribute': kw.get('custom_attribute', False)
        })

    def _get_pricelist(self, pricelist_id, pricelist_fallback=False):
        return request.env['product.pricelist'].browse(int(pricelist_id or 0))
