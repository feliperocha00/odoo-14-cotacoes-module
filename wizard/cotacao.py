from odoo import models, fields, api, _
from datetime import date
import datetime


class CotacoesVendas(models.TransientModel):
    _name = 'cotacoes'

    # CONSULTA DE CLIENTE
    partner_id = fields.Many2one(comodel_name='res.partner', string='Cliente')
    partner_credit_limit = fields.Float(string='Limite de crédito', readonly=1)
    partner_phone = fields.Char(string='Telefone', readonly=1)
    partner_route_id = fields.Many2one(comodel_name='routes', string='Rota', readonly=1)
    partner_street = fields.Char(string='Rua', readonly=1)
    partner_city = fields.Char(string='Cidade', readonly=1)
    partner_email = fields.Char(string='E-mail', readonly=1)
    partner_fantasy_name = fields.Char(string='Nome fantasia', readonly=1)
    date = fields.Date(string='Data de Emissão', default=date.today(), readonly=True)
    expire_date = fields.Date(string='Data de Vencimento', default=date.today())
    payment_conditions = fields.Many2one(comodel_name='account.payment.term')


    # LISTA DE COTAÇÃO
    quote_list = fields.Many2many(
        comodel_name="product.product",
        relation="cotacao_product_rel",
    )

    partner_quotes = fields.Many2many(
        comodel_name='sale.order',
    )

    @api.onchange('partner_route_id')
    def calcula_vencimento(self):
        today = datetime.date.today()
        weekday = today.weekday()

        days_of_week = ["Segunda-feira",
                        "Terça-feira",
                        "Quarta-feira",
                        "Quinta-feira",
                        "Sexta-feira",
                        "Sábado",
                        "Domingo"]
        dia_rota = []
        for rec in self.partner_route_id.dia_rota:
            dia_rota.append(rec.dia)
        if self.partner_route_id:
            while days_of_week[today.weekday()] != dia_rota[-1]:
                today += datetime.timedelta(days=1)
            self.expire_date = today






    @api.onchange('partner_id')
    def part_quotes(self):
        if self.partner_id:
            sales = self.env['sale.order'].search([('partner_id.id', '=', self.partner_id.id)])
            self.partner_quotes = sales
        else:
            self.partner_quotes = False

    @api.onchange('partner_id')
    def costumerinform(self):
        if self.partner_id:
            for name in self.partner_id:
                self.partner_phone = name.phone
                self.partner_route_id = name.route_id
                self.partner_street = name.street
                self.partner_city = name.city
                self.partner_email = name.email
                self.partner_fantasy_name = name.name_fantasy
                self.partner_credit_limit = name.credit_limit_compute
        else:
            for name in self.partner_id:
                self.partner_phone = False
                self.partner_route_id = False
                self.partner_street = False
                self.partner_city = False
                self.partner_email = False
                self.partner_fantasy_name = False
                self.partner_credit_limit = False

    # @api.onchange('partner_route_id')
    # def routesearch(self):
    #     if self.partner_route_id:
    #         id = self.partner_route_id.id
    #         return {"domain": {'partner_id': [('route_id', '=', id)]}}
    #     else:
    #         return {'domain': {'partner_id': []}}

    def productsearch(self):
        quotelist = []
        for quote in self.quote_list.ids:
            quotelist.append(quote)
        ctx = dict()
        ctx.update({
            'default_partner_id': self.partner_id.id,
            'default_expire_date': self.expire_date,
            'default_payment_conditions': self.payment_conditions.id,
            'default_quote_list': quotelist
        })
        return {
            'type': 'ir.actions.act_window',
            'name': 'Pesquisa de Produto',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'product.search',
            'views': [[self.env.ref("cotacoes.pesquisa_de_produto_form_view").id, 'form']],
            'context': ctx,
            'target': 'new'
        }

    @api.onchange('quote_list')
    def will(self):
        if self.quote_list:
            for prods in self.quote_list:
                if not prods.quoted_stock or not prods.wish_qty > 0:
                    prods.write({'will_quote': False})
                else:
                    prods.write({'will_quote': True})

    def quotecreate(self):
        ctx = dict()
        vals_list = {
            'partner_id': self.partner_id.id,
            'validity_date': self.expire_date,
            'payment_term_id': self.payment_conditions.id,
        }

        vals_cotacao_bi = {
            'partner_id': self.partner_id.id,
            'expire_date': self.expire_date,
            'payment_conditions': self.payment_conditions.id
        }

        quote = self.env['sale.order'].create(vals_list)

        quote_bi = self.env['cotacao.b.i'].create(vals_cotacao_bi)

        for prods in self.quote_list:
            name = prods.name + '(' + str(prods.product_template_attribute_value_ids.name) + ')'

            if prods.quoted_stock and prods.wish_qty and prods.will_quote:
                vals_lines = ({
                    'order_line': [(0, 0, {'product_id': prods.id,
                                           'product_template_id': prods.product_tmpl_id.id,
                                           'name': name,
                                           'product_uom_qty': prods.wish_qty})]
                })
                quote.write(vals_lines)

            vals_lines_bi = {'wish_qty': prods.wish_qty,
                             'pre_wish_qty': prods.pre_wish_qty,
                             'product_id': prods.id,
                             'cotacao_id': quote_bi.id,
                             'quoted_stock': prods.quoted_stock,
                             'will_quote': prods.will_quote,
                             'stk_ins': prods.stk_ins}

            self.env['cotacao.b.i.list'].create(vals_lines_bi)



        qtys = self.env['product.product'].search([])

        for prods in qtys:
            prods.write({'wish_qty': 0})
            prods.write({'pre_wish_qty': 0})
            prods.write({'quoted_stock': True})
            prods.write({'will_quote': True})
            prods.write({'stk_ins': False})

        return {
            'type': "ir.actions.act_window",
            'view_type': "form",
            'view_mode': "form",
            'res_id': quote.id,
            'res_model': "sale.order",
            'views': [[self.env.ref("sale.view_order_form").id, 'form']],
            'target': 'current',
            'context': ctx
        }

    def cancel(self):

        vals_cotacao_bi = {
            'partner_id': self.partner_id.id,
            'expire_date': self.expire_date,
            'payment_conditions': self.payment_conditions.id
        }

        quote_bi = self.env['cotacao.b.i'].create(vals_cotacao_bi)

        for prods in self.quote_list:

            vals_lines_bi = {'wish_qty': prods.wish_qty,
                             'product_id': prods.id,
                             'cotacao_id': quote_bi.id,
                             'quoted_stock': prods.quoted_stock}

            self.env['cotacao.b.i.list'].create(vals_lines_bi)

        qtys = self.env['product.product'].search([])

        for prods in qtys:
            prods.write({'wish_qty': 0})
