
{
    "name": "Tienda Nube - Odoo Connector",
    "summary": """
        Conector de Tienda Nube con Odoo""",
    "category": "Sale",
    "version": "18.0.1.0.0",
    "website": "https://autodidactati.com",
    "author": "Iván Arriola - Autodidacta TI",
    "license": "LGPL-3",
    "depends": [
        "base",
        "stock",
        "sale",
    ],
    "data": [
        "data/product_discount_tn.xml",
        "data/cron_update_stock_tn.xml",
        "data/product_template_actions.xml",
        "security/ir.model.access.csv",
        "wizards/create_all_products_odoo_views.xml",
        "wizards/create_all_category_odoo_views.xml",
        "wizards/create_all_webhook_odoo_views.xml",
        "wizards/create_all_coupon_odoo_views.xml",
        "wizards/create_all_order_odoo_views.xml",
        "wizards/get_tn_location_wizard_views.xml",
        "views/webhook_tn_view.xml",
        "views/res_company_inherit_view.xml",
        "views/menu_view.xml",
        "views/product_template_inherit_view.xml",
        "views/product_product_inherit_view.xml",
        "views/category_tn_view.xml",
        "views/sale_order_inherit_view.xml",
        "views/tn_log_views.xml",
        "views/coupon_tn_views.xml",
        "views/stock_warehouse_inherit_views.xml",
    ],
    "assets": {
        
    },
    "installable": True,
    "application": True,
    "auto_install": False,
}