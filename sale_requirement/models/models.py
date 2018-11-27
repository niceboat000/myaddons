# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo import exceptions 
from datetime import datetime, timedelta,date
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.http import request

class CyclePurchaseOrder(models.Model):
    _name = 'quotation.cycle'

    requirement_id = fields.Many2one('sale.requirement',string='Requirement')
    company_id = fields.Many2one('res.partner',related='partner_id.parent_id',string='Company')
    partner_id = fields.Many2one('res.partner',string='Submitter')
    state = fields.Selection(
        [(1,'Pending'),
        (2,'Approved'),
        (3,'Done')],
        string='State',
        default=1)
    cycle_line = fields.One2many('quotation.cycle.line','order_id',string='Product List')

class CyclePurchaseOrder(models.Model):
    _name = 'quotation.cycle.line'

    product_id = fields.Many2one('product.product',string='Product')
    uom_qty = fields.Float(string='Quantity')
    uom_id = fields.Many2one('product.uom',string='Unit')
    order_id = fields.Many2one('quotation.cycle',string='Order')
    description = fields.Text(string='Department')

class ProductProductAppendSo(models.TransientModel):
    _name = 'product.product.append.br'

    quotation_id = fields.Many2one('product.quotation')
    requirement_id = fields.Many2one('sale.requirement',related='quotation_id.requirement_id')
    barcode = fields.Char(related="product_id.barcode")
    partner_id = fields.Many2one('res.partner')
    image = fields.Binary(related="product_id.image")
    price_unit = fields.Float('Cost')
    min_qty = fields.Float(string="MOQ")
    vaild_length = fields.Integer(string="Vaild Length")
    so_currency_id = fields.Many2one('res.currency',related='product_id.currency_id',readonly=True)
    product_uom_qty = fields.Float(string='Quantity', default=1.0)
    product_id = fields.Many2one('product.product', string='Product', readonly=True)
    tax_ids = fields.Many2many('account.tax', string='Taxes')
    product_uom_qty = fields.Float(string='Offer Quantity')
    name = fields.Char(string='Product Name')
    request = fields.Text(string='Customer Request')

   # 供应链用
    def apply_insert(self):
        self.quotation_id.write({
            'product_line': [
                (0, 0, {
                    'pdt_quote': self.quotation_id,
                    'pdt_requirement':self.requirement_id,
                    'product_uom_qty': self.product_uom_qty,
                    'product_id': self.product_id.id,
                    'tax_id': self.tax_ids and [(6, 0, self.tax_ids.ids)],
                    'name': self.name,
                    'min_qty': self.min_qty,
                    'pricing_currency_id': self.so_currency_id.id,
                    'vaild_length': self.vaild_length,
                })]
        })            
        view_id = self.env.ref('sale_requirement.product_quotation_form')
        quotation_id = self.quotation_id
        return {
                'type': 'ir.actions.act_window',
                'res_model': 'product.quotation',
                'view_type': 'form',
                'view_mode': 'form',
                'target': 'current',
                'res_id': quotation_id.id,
                'view_id': view_id.id,
            }

class Quotation_Product_Line(models.Model):
    _name = 'quotation.product.line'

    product_id = fields.Many2one('product.product', string="Product",
                                 change_default=True, ondelete='restrict', required=True)
    name = fields.Text(string='Description')
    pdt_quote = fields.Many2one('product.quotation',string='Quote Product')
    product_uom_qty = fields.Float(string='Quantity', default=1.0)
    price_unit = fields.Float(string='Cost',related='product_id.list_price')
    application = fields.Many2many('product.application',string='Application',related='product_id.application')
    market_price = fields.Float(string='Price',compute='_compute_unit')
    price_tax = fields.Float(string='Tax',compute='_compute_unit')
    no_duty_price = fields.Float(string='Price without tax',compute='_compute_unit')
    price_total_currency = fields.Float(string='Price',compute='_compute')
    market_price_currency = fields.Float(string='Unit Price',compute='_compute')
    price_total = fields.Float(string='Price',compute='_compute_total')
    cost_total = fields.Float(string='Cost',compute='_compute_cost')
    tax_total = fields.Float(string='Tax',compute='_compute_total')
    margin = fields.Float(string='Margin',compute='_compute_cost')
    uom_id = fields.Many2one('product.uom', 'Unit of Measure')
    image = fields.Binary(string='Image',related='product_id.image')
    min_qty = fields.Float(string='MOQ')
    product_image_ids = fields.One2many(related='product_id.product_image_ids')
    price_rate = fields.Float(string='Price Rate', default=0.0)
    currency_id = fields.Many2one('res.currency',string='Currency',related='pdt_quote.currency_id')
    pricing_currency_id = fields.Many2one('res.currency',string='Currency')
    valid_length = fields.Integer(string='Valid Length')
    create_date = fields.Datetime(string='Date',default=fields.Datetime.now)
    valid_date = fields.Date(string='VALID',compute="onchange_day")
    tax_id = fields.Many2many('account.tax',string='Taxes')
    pdt_requirement = fields.Many2one('sale.requirement',string='Requirement')
    hotel_style_id = fields.Many2many('requirement.tags',string='Hotel Style',related='pdt_requirement.hotel_style')
    customer_images = fields.One2many('quotation.image','product_quot_id',string='Quote Image',related='pdt_quote.customer_images')

    @api.depends('price_total','market_price','pricing_currency_id','currency_id','price_rate')
    def _compute(self):
        for order in self:
            if order.currency_id and order.pricing_currency_id and order.price_rate:
                order.price_total_currency =  self.env['res.currency']._compute(order.pricing_currency_id,order.currency_id,order.price_total)
                order.market_price_currency = self.env['res.currency']._compute(order.pricing_currency_id,order.currency_id,order.market_price)

    @api.depends('product_uom_qty')
    def _compute_cost(self):

        for line in self:
            line.cost_total =  line.price_unit  * line.product_uom_qty
            line.margin = line.price_total - line.cost_total - line.tax_total

    @api.depends('product_uom_qty','price_unit', 'tax_id','price_rate','product_id')
    def _compute_total(self):

        for line in self:
            price = line.price_unit * (1 / (1 - line.price_rate))
            taxes = line.tax_id.compute_all(price, line.currency_id, line.product_uom_qty, product=line.product_id, partner=line.pdt_requirement.partner_id)
            line.update({
                'tax_total': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
            })

    @api.depends('price_unit', 'tax_id','price_rate','product_id')
    def _compute_unit(self):

        for line in self:
            price = line.price_unit * (1 / (1 - line.price_rate))
            taxes = line.tax_id.compute_all(price, line.currency_id)
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'market_price': taxes['total_included'],
                'no_duty_price': taxes['total_excluded'],
            })

    @api.onchange('create_date','valid_length')
    def onchange_day(self):
        for s in self:
            s.valid_date = datetime.strptime(s.create_date,DEFAULT_SERVER_DATETIME_FORMAT) + timedelta(days=s.valid_length)

    # 产品信息自动更新    
    @api.onchange('product_id')
    def product_line(self):
        line = self.env['product.product'].search([('name', '=', self.product_id.name)])
        self.name = line.name
        self.price_unit = line.list_price
        self.uom_id = line.uom_id
        self.pricing_currency_id = line.currency_id
                
class quotation_tags(models.Model):
    _name = 'quotation.tags'
    _description = 'Tags for quotation'

    name = fields.Char('Stage Name', required=True, translate=True)
    sequence = fields.Integer('Sequence', default=1, help="Used to order stages. Lower is better.")
    requirements = fields.Text('Requirements', help="Enter here the internal requirements for this stage (ex: Offer sent to customer). It will appear as a tooltip over the stage's name.")

class application_tags(models.Model):
    _name = 'product.application'
    _description = 'Tags for Product'
    _parent_name = "parent_id"
    _parent_store = True
    _parent_order = 'name'
    _rec_name = 'complete_name'
    _order = 'parent_left'

    name = fields.Char(string='Application')
    color = fields.Integer(string='Color Index', default=10)
    description = fields.Text(string='Description')
    parent_id = fields.Many2one('product.application', 'Parent Category', index=True, ondelete='cascade')
    child_id = fields.One2many('product.application', 'parent_id', 'Child Categories')
    parent_left = fields.Integer('Left Parent', index=1)
    parent_right = fields.Integer('Right Parent', index=1)
    complete_name = fields.Char(
        'Complete Name', compute='_compute_complete_name',
        store=True)

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Tag name already exists !"),
    ]

    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for category in self:
            if category.parent_id:
                category.complete_name = '%s / %s' % (category.parent_id.complete_name, category.name)
            else:
                category.complete_name = category.name

    @api.model
    def name_create(self, name):
        return self.create({'name': name}).name_get()[0]


class product_quotation(models.Model):
    _name = 'product.quotation'
    _description = 'Quotation Product'
    _inherit = ['mail.thread','mail.activity.mixin']

    name = fields.Char(string='Name', required=True)
    name_cn = fields.Char(string='Chinese Name')                             
    default_code = fields.Char(string='Inquiry Code')
    application = fields.Many2many('product.application',string='Application')
    function = fields.Char(string='Function')
    create_date = fields.Date(string='Date', default=fields.Date.today())
    requirement_id =fields.Many2one('sale.requirement',string='Quotation',ondeldete='cascade')
    description = fields.Text(string='Department Requirement',compute='_compute_require_description')
    customer_description = fields.Text(string='Customer Description')
    hotel_style = fields.Many2many('requirement.tags',string='Hotel Style',related='requirement_id.hotel_style')
    categ_id = fields.Many2one('product.category',string='Category')
    customer_image = fields.Binary(string='Image')
    customer_images = fields.One2many('quotation.image','product_quot_id',string='Quote Image')
    uom_qty = fields.Float(string='Order Quantity',track_visibility='onchange',compute='_compute_qty_quotation_')
    uom_id = fields.Many2one('product.uom',string='Unit')
    user_id = fields.Many2one('res.users',string='负责人')
    price_max = fields.Float(string='Max Price')
    price_min = fields.Float(string='Min Price')
    country_policy = fields.Text(string='Country Policy')
    tag_ids = fields.Many2many('quotation.tags',string='Tags')
    fuction_standard = fields.Text(string='Fuction Standard')
    delivery_time = fields.Date(string='Delivery Time',track_visibility='onchange')
    monthly_cost = fields.Float(string='Monthly Cost')
    next_cycle_time = fields.Date(string='Next Purchase Time',compute='next_cycle_day')
    cycle_uom_qty = fields.Float(string='Cycle Quantity')
    is_customized = fields.Boolean(string='Customized')
    customized_description = fields.Text(string='Description for Customized')
    product_line = fields.One2many('quotation.product.line','pdt_quote',string='Product')
    customer_id = fields.Many2one('res.partner',string='Submitter',default=lambda self: self.env.user.partner_id)
    parent_id = fields.Many2one('res.partner',string='Company',related='requirement_id.partner_id')
    customer_barcode = fields.Char(string='Customer Ref')
    department = fields.Many2many('res.department',string='Department',related='customer_id.department')
    is_accept = fields.Boolean(string='Accept')
    subtotal = fields.Float(string='Subtotal',compute='compute_subtotal')
    price_rate = fields.Float(string='费率')
    currency_id = fields.Many2one('res.currency',related='parent_id.property_product_pricelist.currency_id')
    department_line_ids = fields.One2many('res.department.line', 'product_quot_id', 'Department')
    state = fields.Selection([
        ('black','Normal'),
        ('green','Approved'),
        ('red','Reject')], string='State',
        copy=False, default='black', required=True)


    @api.onchange('monthly_cost','delivery_time')
    def next_cycle_day(self):
        for s in self:
            if s.delivery_time:
                s.next_cycle_time = datetime.strptime(s.delivery_time,DEFAULT_SERVER_DATETIME_FORMAT) + timedelta(mouths=(s.uom_qty / s.monthly_cost))

    @api.multi
    def btn_claim(self):
        self.user_id = self.env.uid

    @api.multi
    def btn_refuse_claim(self):
        for s in self:
            s.user_id = 0

    @api.depends('department_line_ids')
    def _compute_qty_quotation_(self):
        for q in self:
            q.uom_qty = 0
            if q.department_line_ids:
                for value in self.department_line_ids:
                    q.uom_qty += value.values

    # 计算单需求预算
    @api.one
    def compute_subtotal(self): 
        for product in self: 
            product.subtotal = 0
            for line in product.product_line:
                product.subtotal += line.price_total_currency

    @api.multi
    def btn_accept(self):
        for s in self:
            s.is_accept = not s.is_accept
            return True

    @api.depends('department_line_ids')
    def _compute_require_description(self):
        for required in self:
            variant = ''
            for item in required.department_line_ids:
                name = ''
                for dept in item.department_id:
                    name += (str(dept.name)+',')
                variant += (str(name) + ' : ' + str(item.values) + '\n')
            required.description = variant or required.name
                
    # @api.depends('attribute_line_ids')
    # def _compute_require_description(self):
    #     for required in self:
    #             variant = ''
    #             for item in required.attribute_line_ids:
    #                 value = ''
    #                 for attribute in item.value_ids:
    #                     value += (str(attribute.name)+',')
    #                 variant += (' - ' + str(item.attribute_id.name) + ' : ' + str(value) + '\n')
    #             required.description = variant or required.name

    def action_create_order_new(self):
        vals = {'partner_id': self.customer_id.id,
                'user_id': self.user_id.id,
                }
        sale_order = self.env['sale.order'].create(vals)
        order_line = self.env['sale.order.line']
        for line in self.product_line:
            pdt_value = {
                        'order_id': sale_order.id,
                        'product_id': line.product_id.id,
                        # 产品解释，客户需求
                        'product_uom_qty': line.product_uom_qty,
                        'uom_id': line.uom_id.id,
                        'price_unit':line.market_price,
                        'quotation_id':line.pdt_quote.id,

                }
            order_line.create(pdt_value)
            view_id = self.env.ref('sale.view_order_form')
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'sale.order',
                'view_type': 'form',
                'view_mode': 'form',
                'target': 'current',
                'res_id': sale_order.id,
                'view_id': view_id.id,
            }

class product_quotation_image(models.Model):
    _name = 'quotation.image'
    _description = 'Customer Quotation Image'

    image = fields.Binary(string='IMAGE',attachment=True)
    name = fields.Char(string='Name')
    product_quot_id = fields.Many2one('product.quotation',string='Related Quote')

class requirement_tags(models.Model):
    _name = 'requirement.tags'
    _description = 'Tags for requirement'

    name = fields.Char(string='Style')
    color = fields.Integer(string='Color Index', default=10)
    description = fields.Text(string='Description')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Tag name already exists !"),
    ]
class quotation_tags(models.Model):
    _name = 'scenario.tags'
    _description = 'Tags for scenario'

    name = fields.Char(string='State')
    color = fields.Integer(string='Color Index', default=10)
    description = fields.Text(string='Description')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Tag name already exists !"),
    ]

class sale_quotation(models.Model):
    _name = 'sale.requirement'
    _description = 'Requirement Order'
    _inherit = ['mail.thread','mail.activity.mixin']

    name = fields.Char(string='Project Name', required=True)
    image = fields.Binary(string='Image',related='partner_id.image')
    order_id = fields.Char(string='Inquiry NO.',default=lambda self: self.env['ir.sequence'].next_by_code('requirement.inquiry'))
    quote_line = fields.One2many('product.quotation', 'requirement_id', string='Quote Product')
    number_of_quote = fields.Integer(string='Requirement Number', compute='_number_of_quote')
    number_of_unsure = fields.Integer(string='Unconfirm Requirement',compute='_number_of_unsure')
    number_of_product = fields.Integer(string='All Product',compute='_number_of_product')
    project_manager = fields.Many2one('res.users', string='Project Manager', ondelete='cascade',index=True)
    lead_id = fields.One2many('crm.lead','requirement_id','线索')
    task_id = fields.One2many('project.task','requirement_id','任务')
    scenario_id = fields.Many2many('scenario.tags',string='Scenario')
    is_accept = fields.Boolean(string='产品已确认')
    partner_id = fields.Many2one('res.partner',string='Company',index=True,related="staff_id.parent_id")
    barcode = fields.Char(string='Customer Code',related='partner_id.barcode')
    description = fields.Text(string='Project Description')
    total_budget = fields.Float(string='Total Budget',compute='_total_budget')
    product_line = fields.One2many('quotation.product.line','pdt_requirement',string='Product List')
    street = fields.Char('Street')
    street2 = fields.Char('Street2')
    currency_id = fields.Many2one('res.currency',related='partner_id.property_product_pricelist.currency_id')
    zip = fields.Char('Zip', change_default=True)
    city = fields.Char('City')
    state_id = fields.Many2one("res.country.state", string='State')
    country_id = fields.Many2one('res.country', string='Country')
    start_schedule = fields.Date(string='Estimated opening time')
    hotel_style = fields.Many2many('requirement.tags',string='Hotel Style')
    response_schedule = fields.Date(string='Expected quotation time',track_visibility='onchange')
    build_area = fields.Float(string='Building Area')
    brand = fields.Many2one('res.brand',string='Brand')
    department = fields.Many2many('res.department',string='Department',related='staff_id.department')
    staff_id = fields.Many2one('res.partner',track_visibility='onchange',string='Initiator',default=lambda self: self.env.user.partner_id)
    attachment_filename = fields.Char(string="Attachment Filename")
    attachment_ids = fields.One2many('ir.attachment', 'res_id', domain=[('res_model', '=', 'website.support.ticket')],
                                     string="Attachments")

    # 计算询盘数量
    @api.depends()
    def _number_of_quote(self):
        for s in self:
            domain = [('requirement_id','=', s.id)]
            count = len(s.env['product.quotation'].search(domain).ids)
            s.number_of_quote = count

    # 计算未确认数量
    @api.depends()
    def _number_of_unsure(self):
        for s in self:
            domain = [('is_accept','!=',True),('requirement_id', '=', s.id)]
            count = len(s.env['product.quotation'].search(domain).ids)
            s.number_of_unsure = count

    # 总产品数量
    @api.depends()
    def _number_of_product(self):
        for s in self:
            domain = [('pdt_requirement', '=', s.id)]
            count = len(s.env['quotation.product.line'].search(domain).ids)
            s.number_of_product = count

    # 计算总预算
    @api.multi
    def _total_budget(self):
        for sale in self:
            sale.total_budget = 0
            for line in sale.quote_line:
                sale.total_budget += line.subtotal 

    # 客户确定所有产品
    @api.multi
    def btn_accept(self):
        count = self.number_of_unsure
        for s in self.quote_line:
            if s.is_accept == False:
                raise exceptions.Warning('There are %d product not accepted.' %count)
                break
            else :
                self.is_accept = True


    # 创建订单
    def action_create_order_new(self):
        vals = {'partner_id': self.partner_id.id,
                'user_id': self.project_manager.id,
                }
        sale_order = self.env['sale.order'].create(vals)
        order_line = self.env['sale.order.line']
        for line in self.quote_line:
            for line in line.product_line:
                pdt_value = {
                            'order_id': sale_order.id,
                            'product_id': line.product_id.id,
                            # 产品解释，客户需求
                            'product_uom_qty': line.product_uom_qty,
                            'uom_id': line.uom_id.id,
                            'price_unit':line.market_price,
                            'quotation_id':line.pdt_quote.id,

                    }
                order_line.create(pdt_value)
            view_id = self.env.ref('sale.view_order_form')
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'sale.order',
                'view_type': 'form',
                'view_mode': 'form',
                'target': 'current',
                'res_id': sale_order.id,
                'view_id': view_id.id,
            }