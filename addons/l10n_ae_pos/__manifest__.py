# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'United Arab Emirates - Point of Sale',
    'author': 'Odoo S.A.',
    'category': 'Accounting/Localizations/Point of Sale',
    'icon': '/l10n_ae/static/description/icon.png',
    'description': """
United Arab Emirates POS Localization
=======================================================
    """,
    'depends': ['l10n_ae', 'point_of_sale'],
    'auto_install': True,
    'license': 'LGPL-3',
    'assets': {
        'point_of_sale.assets': [
            'l10n_ae_pos/static/src/xml/Screens/ReceiptScreen/OrderReceipt.xml',
        ],
    },
}
