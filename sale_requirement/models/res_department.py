# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo import exceptions 
from odoo.http import request


class res_department(models.Model):
    _name = 'res.department'
    _description = 'Department Management'

    name = fields.Char(string='Name')
    description = fields.Text('Description', translate=True)

class ProductAttributeLine(models.Model):
    _name = 'res.department.line'
    
    product_quot_id = fields.Many2one('product.quotation', 'Quotation', ondelete='cascade', required=True)
    department_id = fields.Many2many('res.department', 'Department Request', ondelete='restrict', related='user_id.department')
    values = fields.Float(string='Request Number')
    user_id = fields.Many2one('res.users',string='Submitter')