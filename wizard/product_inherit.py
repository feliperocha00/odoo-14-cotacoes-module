from datetime import date

from odoo import fields, models, api, _
from odoo.exceptions import UserError


class ProductInherit(models.Model):
    _inherit = 'product.product'

    quoted_stock = fields.Boolean(
        string='Não tem estoque',
        compute='instock',
        store=True
    )

    will_quote = fields.Boolean(
        string="Vai cotar",
        default=True
    )

    fipe_ano = fields.Integer(
        related='fipe_ids.ano'
    )

    wish_qty = fields.Float()

    pre_wish_qty = fields.Float()

    codigo_fipe = fields.Char(
        related='fipe_ids.codigo_fipe'
    )

    concorrente_prices = fields.One2many(
        comodel_name='preco.concorrente',
        inverse_name='product_id'
    )

    # campos relacionados a feaure de checkbox autor:Thiago Francelino Santos
    stk_ins = fields.Boolean(
        default=False,
        string="Estoque insuficiente?",
    )

    def write(self, vals):
        if 'wish_qty' in vals:
            if vals['wish_qty'] > self.qty_available:
                raise UserError(
                    _('Quantidade inserida do produto ' + self.name + ' maior do que a disponível do estoque'))
        return super(ProductInherit, self).write(vals=vals)

    @api.depends("qty_available")
    def instock(self):
        for rec in self:
            if rec.qty_available > 0:
                rec.quoted_stock = True
            else:
                rec.quoted_stock = False

    # COPIEI DO MILA https://github.com/mikunatic/cotacao/blob/main/models/product_extension.py
    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        name_split = name.split()
        array = []
        for palavra in name_split:
            array.append('|')
            array.append('|')
            array.append('|')
            array.append('|')
            array.append(('name', operator, palavra))
            array.append(('product_template_attribute_value_ids', operator, palavra))
            array.append(('fipe_ids', operator, palavra))
            array.append(('codigo_fipe', operator, palavra))
            array.append(('fipe_ano', operator, palavra))
        if name:
            pesquisa = self.search(array)
            return pesquisa.name_get()
        return self.search([('name', operator, name)] + args, limit=limit).name_get()


class PrecoConcorrente(models.Model):
    _name = 'preco.concorrente'

    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Produto'
    )

    name = fields.Many2one(
        comodel_name='res.partner',
        string='Concorrente'
    )

    value = fields.Float()

    data = fields.Date(default=date.today())
