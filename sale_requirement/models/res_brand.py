# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo import exceptions 
from odoo.http import request


class res_brand(models.Model):
    _name = 'res.brand'
    _description = 'Brand'

    name = fields.Char(string='Name')
    partner_ids = fields.One2many(
        'res.partner',
        'partner_brand_id',
        string='Subsidiarie')
    product_ids = fields.One2many(
        'product.template',
        'product_brand_id',
        string='Brand Products',
    )
    description = fields.Text('Description', translate=True)
    logo = fields.Binary('Logo File')
    partner_count = fields.Integer('Partner',compute='_get_partner_count')
    product_count = fields.Integer('Product',compute='_get_product_count')

    @api.one
    @api.depends('partner_ids')
    def _get_partner_count(self):
        self.partner_count = len(self.partner_ids)

    @api.one
    @api.depends('product_ids')
    def _get_product_count(self):
        self.product_count = len(self.product_ids)