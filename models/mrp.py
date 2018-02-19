# -*- encoding: utf-8 -*-
'''
Created on 6 december. 2010

@author: tarik Lallouch
'''

from datetime import datetime
from dateutil.relativedelta import relativedelta
import math

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_round
from odoo.addons import decimal_precision as dp

def rounding(f, r):
    if not r:
        return f
    return round(f / r) * r

def ceiling(f, r):
    if not r:
        return f
    return math.ceil(f / r) * r

# class mrp_bom_line(models.Model):
#     _inherit = 'mrp.bom.line'
#
#     constante = fields.Float('product_id','constante', relation="product.product", string="constante"),
#     desc_tech = fields.Text('description technique')

class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    # constante = fields.Float(related='product_id', string="constante")
    calculer = fields.Boolean('Calculer cout')
    prix_interne = fields.Float('Prix de revient')
    desc_tech = fields.Text('description technique')

    @api.model
    def _explode_constant(self, product, quantity, picking_type=False):
        """
            Explodes the BoM and creates two lists with all the information you need: bom_done and line_done
            Quantity describes the number of times you need the BoM: so the quantity divided by the number created by the BoM
            and converted into its UoM
        """
        boms_done = [(self, {'qty': quantity, 'product': product, 'original_qty': quantity, 'parent_line': False})]
        lines_done = []
        templates_done = product.product_tmpl_id

        bom_lines = [(bom_line, product, quantity, False) for bom_line in self.bom_line_ids]
        while bom_lines:
            current_line, current_product, current_qty, parent_line = bom_lines[0]
            bom_lines = bom_lines[1:]
            constante = current_line.constante
            if current_line._skip_bom_line(current_product):
                continue
            if current_line.product_id.product_tmpl_id in templates_done:
                raise UserError(_('Recursion error!  A product with a Bill of Material should not have itself in its BoM or child BoMs!'))
            if constante==0:
                line_quantity = current_qty * current_line.product_qty
            else:
                line_quantity = current_line.product_qty
                
            bom = self._bom_find(product=current_line.product_id, picking_type=picking_type or self.picking_type_id, company_id=self.company_id.id)
            if bom.type == 'phantom':
                converted_line_quantity = current_line.product_uom_id._compute_quantity(line_quantity / bom.product_qty, bom.product_uom_id)
                bom_lines = [(line, current_line.product_id, converted_line_quantity, current_line) for line in bom.bom_line_ids] + bom_lines
                templates_done |= current_line.product_id.product_tmpl_id
                boms_done.append((bom, {'qty': converted_line_quantity, 'product': current_product, 'original_qty': quantity, 'parent_line': current_line}))
            else:
                # We round up here because the user expects that if he has to consume a little more, the whole UOM unit
                # should be consumed.
                rounding = current_line.product_uom_id.rounding
                line_quantity = float_round(line_quantity, precision_rounding=rounding, rounding_method='UP')
                lines_done.append((current_line, {'qty': line_quantity, 'product': current_product, 'original_qty': quantity, 'parent_line': parent_line}))

        return boms_done, lines_done
    
    explode = _explode_constant
    
    
    def compute_qty(self):
        print 22
        return True


    def compute_price(self):
        for bom in self:
            price=0
            for sbom in bom.bom_lines:
                if sbom.prix_interne :
                    price+=sbom.prix_interne * sbom.product_qty
                else :
                    price+=sbom.product_id.prix_interne * sbom.product_qty
            self.write({'prix_interne' : price/bom.product_qty})
        return True


class mrp_production(models.Model):
    _inherit = 'mrp.production'

    def _get_ids_order_and_parent_from_origin(self, origin):
        order_id = False
        parent_id = False
        if origin:
            origin = origin.split(':')
            order = origin[0]
            parent = len(origin) > 1 and origin[1] or ''
            if order and order != '':
                self._cr.execute('select id from sale_order where name=%s order by id desc', (order,))
                res = self._cr.fetchone()
                order_id = res and res[0] or False
            if parent and parent != '':
                self._cr.execute('select id from mrp_production where name=%s order by id desc', (parent,))
                res = self._cr.fetchone()
                parent_id = res and res[0] or False
        return order_id, parent_id

    def get_partner(self):
        result = {}
        for line in self:
            sale_obj = self._cr.dbname.get('sale.order')
            sale_ref = sale_obj.search([('name', '=', line.origin)])
            if sale_ref == []:
                result[line.id] = ''
            else:
                sale = sale_obj.browse(sale_ref)[0]
                result[line.id] = sale.partner_id.name
        return result

    def get_cout_total_matieres(self):
        result = {}
        for line in self:
            total_1=0
            for sub in line.move_raw_ids:
                total_1 += sub.product_id.standard_price*sub.product_qty
            result[line.id] = total_1
        return result

    def get_cout_total_machines(self):
        result = {}
        for line in self:
            total_2=0
            for sub2 in line.workorder_ids:
                total_2 += sub2.product_id.standard_price
            result[line.id] = total_2
        return result

    def get_cout_total_charge(self):
        result = {}
        for line in self:
            total_3 = 0
         #   for sub3 in line.charge_fixe:
          #      total_3 += sub3.amount
            result[line.id] = total_3
        return result

    def get_cout_total_cout(self):
        result = {}
        for line in self:
            total=0
            total+=(line.cout_total_machines + line.cout_total_charge + line.cout_total_matieres)*1.2
            result[line.id] = total
        return result

    def get_cout_unitaire(self):
        result = {}
        for line in self:
            total=0
            total+=(line.cout_total_machines + line.cout_total_charge + line.cout_total_matieres)*1.2/line.product_qty
            result[line.id] = total
        return result

    order_id = fields.Many2one('sale.order', 'Sales Order', required=False, readonly=False, states={'draft': [('readonly', False)]})
    parent_id = fields.Many2one('mrp.production', 'Parent', required=False, readonly=True, change_default=True)
    #partner_id = fields.function(get_partner, method=True, type='char', string='Client', store=False)
    partner_id = fields.Many2one('res.partner', 'Client', required=False, states={'draft':[('readonly',False)]})
    invoice_id = fields.Many2one('account.invoice', 'Facture', required=False, states={'draft':[('readonly',False)]})
    etat_prod = fields.Selection([
        ('1','attente BAT'),('2','CTP'), ('3','en impression'),('4','pelliculage'), ('5','finition'),('6','livraison partielle'), ('7','attente liv'),('8','solder'),('9','litige'),
    ],    'etat prod',  states={'draft':[('readonly',False)]})
    type_prod = fields.Selection([
        ('1','offset'),('2','numerique'), ('3','Grand Format'),('4','PLV')
    ],    'type production',  states={'draft':[('readonly',False)]})
    cout_total_matieres = fields.Float(compute=get_cout_total_matieres, method=True, string='cout matieres', store=False)
    cout_total_machines = fields.Float(compute=get_cout_total_machines, method=True, string='cout machines', store=False)
    cout_total_charge = fields.Float(compute=get_cout_total_charge, method=True, string='cout charge en +', store=False, default=10)
    cout_total_cout = fields.Float(compute=get_cout_total_cout, method=True, string='cout Total', store=False)
    cout_unitaire = fields.Float(compute=get_cout_unitaire, method=True, string='cout unitaire', store=False)
    #charge_fixe = fields.One2many('mrp.production.charge.fixe', 'production_id', 'Production charge fixe')
    # description = fields.related('product_id','description_sale',type='char', relation="product.product", string="description", store=False)

    def init(self):
        # This is a helper to guess "old" Relations
        self._cr.execute('select id, origin from mrp_production where length(origin) > 0')
        origins = self._cr.dictfetchall()
        for origin in origins:
            production_id = origin['id']
            order_id, parent_id = self._get_ids_order_and_parent_from_origin(origin['origin'])
            if order_id:
                self._cr.execute('update mrp_production set order_id = %s where id = %s', (order_id, production_id,))
            if parent_id:
                self._cr.execute('update mrp_production set parent_id = %s where id = %s', (parent_id, production_id,))

    @api.model
    def create(self, vals):
        origin = vals.get('origin', False)
        order_id = vals.get('order_id', False)
        if origin: # If origin has SO# or MO#,
            order_id, parent_id = self._get_ids_order_and_parent_from_origin(origin)
            vals.update({'order_id': order_id, 'parent_id': parent_id})
        elif order_id: # No origin, if order_id is specified, update it back to origin.
            so_number = self.env['sale.order'].browse(order_id).name
            vals.update({'origin': so_number})
        res = super(mrp_production, self).create(vals)
        return res

    def _workorders_create_printshop(self, bom, bom_data):
        """
        :param bom: in case of recursive boms: we could create work orders for child
                    BoMs
        """
        workorders = self.env['mrp.workorder']
        bom_qty = bom_data['qty']

        # Initial qty producing
        if self.product_id.tracking == 'serial':
            quantity = 1.0
        else:
            quantity = self.product_qty - sum(self.move_finished_ids.mapped('quantity_done'))
            quantity = quantity if (quantity > 0) else 0

        for operation in bom.routing_id.operation_ids:
            # create workorder
            cycle_number = math.ceil(bom_qty / operation.workcenter_id.capacity)  # TODO: float_round UP
            duration_expected = (operation.workcenter_id.time_start +
                                 operation.workcenter_id.time_stop +
                                 cycle_number * operation.time_cycle * 100.0 / operation.workcenter_id.time_efficiency)
            workorder = workorders.create({
                'name': operation.name,
                'production_id': self.id,
                'workcenter_id': operation.workcenter_id.id,
                'operation_id': operation.id,
                'duration_expected': duration_expected,
                'state': len(workorders) == 0 and 'ready' or 'pending',
                'qty_producing': 1000,
                'capacity': operation.workcenter_id.capacity,
            })
            if workorders:
                workorders[-1].next_work_order_id = workorder.id
            workorders += workorder

            # assign moves; last operation receive all unassigned moves (which case ?)
            moves_raw = self.move_raw_ids.filtered(lambda move: move.operation_id == operation)
            if len(workorders) == len(bom.routing_id.operation_ids):
                moves_raw |= self.move_raw_ids.filtered(lambda move: not move.operation_id)
            moves_finished = self.move_finished_ids.filtered(lambda move: move.operation_id == operation) #TODO: code does nothing, unless maybe by_products?
            moves_raw.mapped('move_lot_ids').write({'workorder_id': workorder.id})
            (moves_finished + moves_raw).write({'workorder_id': workorder.id})

            workorder._generate_lot_ids()
        return workorders
    
    _workorders_create = _workorders_create_printshop

mrp_production()

class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    constante = fields.Selection([
        (1, 'Constant'),
        (0, 'Variable')], string='Product constant')
    calculer = fields.Boolean('Calculer cout')
    prix_interne = fields.Float('Prix de revient')
    desc_tech = fields.Char('description technique')



# class mrp_production_product_line(models.Model):
#     _inherit = 'mrp.production.product.line'
#     _description = 'Production Scheduled Product'

    # desc_tech = fields.Text('mrp.bom.line', related='desc_tech', string='desc_tech')


class stock_production_lot(models.Model):
    _inherit = 'stock.production.lot'

    cost_price_unit = fields.Float('Cost Price Unit', required=True, readonly=True,  help="Cost of one UoM of the product of this lot in the company's currency.")
    uom_id = fields.Many2one('product.uom', 'UoM', required=True, readonly=True, help='Unit of measure used to calculate the cost price of this lot.')

stock_production_lot()

#class mrp_production_charge_fixe(models.Model):
 #   """
  #      Class that represents a production fixed costs
   # """
   # _name = 'mrp.production.charge.fixe'

 #   name = fields.Char('Description', size=128, required=True)
  #  amount = fields.Float('montant', digits_compute=dp.get_precision('Account'))
   # production_id = fields.Many2one('mrp.production', 'Production', required=True)

    #  _defaults = {
    #    'production_id': lambda self, cr, uid, context: context.get('parent_id') and context['parent_id'] or False,
    # }


class MrpWorkorder(models.Model):
    #_name = 'mrp.workorder'
    _description = 'Work Order'
    _inherit = ['mrp.workorder']
    
    qty_printshop = fields.Float(
        'Quantity', default=0.0,
        readonly=True,
        digits=dp.get_precision('Product Unit of Measure'),
        help="Quantity of work center")

class MrpWorkcebter_printshop(models.Model):
    #_name = 'mrp.workorder'
    _description = 'Work Order printshop'
    _inherit = ['mrp.routing.workcenter']
    
    qty_printshop = fields.Float(
        'Quantity', default=0.0,
        readonly=True,
        digits=dp.get_precision('Product Unit of Measure'),
        help="Quantity of work center")

    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

