# -*- coding: utf-8 -*-
{
    'name': "Customer Requirement",

    'summary': """Bussiness Requirement""",

    'description': """
        将客户，CRM提交的报价单快速转化为供应链的工作表，并快速转化为报价单。
    """,

    'author': "COMESOON",
    'website': "http://www.comesoon.hk",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Bussiness Requirement',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale','mail','project','crm','website','website_sale','sale_management','product'],

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/res_brand.xml',
        'views/res_department.xml',
        'views/quotation_product_line.xml',
        'views/product_quotation.xml',
        'views/sale_requirement.xml',
        'views/inherit_views.xml',
        'views/product_append_requirement.xml',
    ],
    'application': True,
}

