# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging
_logger = logging.getLogger(__name__)

class ProductProduct(models.Model):
    _inherit = 'product.product'

    quotation_ids = fields.One2many('quotation.product.line','product_id',string='Requirement List') 
    application = fields.Many2many('product.application',string='Application')

    # 添加到Requirement的产品信息
    @api.multi
    def open_br_product_append(self):
        context = {
            'default_product_id': self.id,
            'default_name': self.name,
            'default_price_unit': self.list_price,
        }
        return {'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'view_type': 'form',
                'res_model': 'product.product.append.br',
                'target': 'new',
                'context': context,
                }
    

class partner_quote(models.Model):
    _inherit = 'res.partner'

    product_count = fields.Integer(string='Product Count',compute='_number_of_product')
    requirement_count = fields.Integer(string='Quotation Count',compute='_number_of_quotation')
    partner_brand_id = fields.Many2many('res.brand',string='Brand')
    department = fields.Many2many('res.department',string='Department')

    # 计算产品数量
    @api.depends()
    def _number_of_product(self):
        for s in self:
            domain = [('customer_id', '=', s.id)]
            count = len(s.env['product.quotation'].search(domain).ids)
            s.product_count = count
    
    # 计算产品数量
    @api.depends()
    def _number_of_quotation(self):
        for s in self:
            domain = ['|',('partner_id', '=', s.parent_id.id),('partner_id', '=', s.id)]
            count = len(s.env['sale.requirement'].search(domain).ids)
            s.requirement_count = count

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    product_brand_id = fields.Many2one(
        'res.brand',
        string='Brand',
        help='Select a brand for this product'
    )


class Sale_Order(models.Model):
    _inherit = 'sale.order'

    product_count = fields.Integer(string='Product Count',compute='_number_of_product')
    requirement_id = fields.Many2one('sale.requirement',string='Requirement')
    
    
    # 计算产品数量
    @api.depends()
    def _number_of_product(self):
        for s in self:
            domain = [('order_id', '=', s.id)]
            count = len(s.env['sale.order.line'].search(domain).ids)
            s.product_count = count

class Sale_order_line(models.Model):
    _inherit = 'sale.order.line'

    quotation_id = fields.Many2one('product.quotation',string="Requirement")
    description = fields.Text(string='Customer Description',related='quotation_id.description')

class Project_Task(models.Model):
    _inherit = 'project.task'

    requirement_id = fields.Many2one('sale.requirement')

class Crm_Lead(models.Model):
    _inherit = 'crm.lead'

    requirement_id = fields.Many2one('sale.requirement')

class ProductAttributevalue(models.Model):
    """
    This is a bugfix to Odoo 10.0
    Categories should not be ordered alphabetically.
    Categories should be ordered according to their choosen order (i.e. sequence field).
    """
    _inherit = 'product.attribute.value'

    @api.multi
    def _variant_name(self, variable_attributes):
        return ", ".join([v.name for v in self.sorted(key=lambda r: r.attribute_id.sequence) if v.attribute_id in variable_attributes])

class ProductProductExt(models.Model):
    """
    When the variants are saved, we store the whole description in "var_desc" field.
    When searching for products, e.g. in invoice line, we perform search in that field.
    Moreover, during this search we convert ' '  to '%' (this could be useful in standard search, too).
    WARNING: we lose the "customer" description.
    """
    _inherit = 'product.product'
    var_desc = fields.Char('Variant description', compute='_compute_var_desc', store=True)

    @api.multi
    def name_get(self):
        """
        By default, "display only the attributes with multiple possible values on the template".
        Why?!?
        I want omogeneity.
        """
        def _name_get(d):
            name = d.get('name', '')
            code = self._context.get('display_default_code', True) and d.get('default_code', False) or False
            if code:
                name = '[%s] %s' % (code,name)
            return (d['id'], name)

        partner_id = self._context.get('partner_id')
        if partner_id:
            partner_ids = [partner_id, self.env['res.partner'].browse(partner_id).commercial_partner_id.id]
        else:
            partner_ids = []

        # all user don't have access to seller and partner
        # check access and use superuser
        self.check_access_rights("read")
        self.check_access_rule("read")

        result = []
        for product in self.sudo():
            # display all the attributes 
            variable_attributes = product.attribute_line_ids.mapped('attribute_id')
            variant = product.attribute_value_ids._variant_name(variable_attributes)

            name = variant and "%s (%s)" % (product.name, variant) or product.name
            sellers = []
            if partner_ids:
                sellers = [x for x in product.seller_ids if (x.name.id in partner_ids) and (x.product_id == product)]
                if not sellers:
                    sellers = [x for x in product.seller_ids if (x.name.id in partner_ids) and not x.product_id]
            if sellers:
                for s in sellers:
                    seller_variant = s.product_name and (
                        variant and "%s (%s)" % (s.product_name, variant) or s.product_name
                        ) or False
                    mydict = {
                              'id': product.id,
                              'name': seller_variant or name,
                              'default_code': s.product_code or product.default_code,
                              }
                    temp = _name_get(mydict)
                    if temp not in result:
                        result.append(temp)
            else:
                mydict = {
                          'id': product.id,
                          'name': name,
                          'default_code': product.default_code,
                          }
                result.append(_name_get(mydict))
        return result
        
    @api.model
    def name_search(self, name='', args=[], operator='ilike', limit=100):
        if not args:
            args = []
        products = None
        
        if name:
            if operator in ['like', 'ilike']:
                pieces = name.split(' ')
                search_domains = [('var_desc', operator, piece) for piece in pieces]
            else:
                search_domains = [('var_desc', operator, name)]
            search_domains += args
            _logger.debug('Qui domains=%s ', str(search_domains))
            products = self.search(search_domains)
            _logger.debug('Qui products=%s ', str(products))
            if products:
                return products.name_get()
        
        return super(ProductProductExt, self).name_search(name=name, args=args, operator=operator, limit=limit)
    
    @api.depends('attribute_value_ids', 'name')
    def _compute_var_desc(self):
        #FIXME can avoid loop?
        for rec in self:
            idAndName = rec.name_get()[0]
            rec.var_desc = idAndName[1] if idAndName else None

class ProductAttributeLine(models.Model):
    _inherit = "product.attribute.line"

    product_quot_id = fields.Many2one('product.quotation', 'Product Quotation', ondelete='cascade')
    product_tmpl_id = fields.Many2one('product.template','Product Template',ondelete='cascade',required=False)
