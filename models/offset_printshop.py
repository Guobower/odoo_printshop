# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2011 AKENOO All Rights Reserved
#    authors: tariklallouch@gmail.com
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time
from datetime import datetime
import odoo.addons.decimal_precision as dp
from odoo import api, fields, models, _
from dateutil import parser
from odoo.exceptions import UserError
import re

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError
from odoo.osv import expression



# class pour determiner type de machine de production

#  def create(self,  data, context=None):
#     if 'stype' in data:
#        if 'gr' in data:
#           data['line_ids'] = self._compute_factor_inv(data['factor_inv'])
#
#       return super(product_uom, self].create( data, context)



class printshop2_setting(models.Model):
    _name = 'printshop2.setting'
    _description = 'printshop2 admin setting'

    name = fields.Char('Setting Profil', size=64, required=True, readonly=False)
    marge = fields.Float('general marge', digits=(8, 2), help="decimal number: 10%=1,10 ")
    raw_marge = fields.Float('raw maetriel marge', digits=(8, 2), help="decimal number: 10%=1,10 ")
    tolerance = fields.Float('Tolerance of production', digits=(8, 2), help="decimal number: 10%=1,10 ")
    remise_id = fields.Many2one('printshop2.remise', 'Discount', required=False, states={'draft': [('readonly', False)]})
    bleed = fields.Float('Bleed', states={'draft': [('readonly', False)]}, default=0.3, help="in cm : 3mm=0,3 ")
    description = fields.Text('Description')

class printshop2_machine(models.Model):
    _name = 'printshop2.machine'
    _description = 'printshop2 Machine'

    name = fields.Char('Machine name', size=64, required=True, readonly=False)
    print_id = fields.Many2one('product.product', 'Print', required=True)
    larg_mach = fields.Float('Machine width', digits=(8, 2), help="in cm")
    long_mach = fields.Float('Machine length', digits=(8, 2), help="in cm")
    nbr_coul_mach = fields.Float('Nbr color of the machine', digits=(8, 0))
    nbr_passe = fields.Float('Nbr of sup. Quantity for production', digits=(8, 0),
                             help="Nombre of sheet for start the machine in offset shop")
    prise_pince = fields.Float('Machine gripper clamp', digits=(8, 2), help="in cm")
    prix_tirage = fields.Float(related='print_id.list_price', string="Price of the print run")
    insolation_id = fields.Many2one('product.product', 'Plate Insolation', states={'draft': [('readonly', False)]})
    prix_insolation = fields.Float(related='insolation_id.list_price', string="Price Plate Insolation")
    prix_calage = fields.Float(related='calage_id.list_price', string="Price setting machine")
    max_gr_print = fields.Float('maximum Grammage', digits=(8, 0), help="in maximum grammage that machine can print")
    calage_id = fields.Many2one('product.product', 'Setting machine to run', states={'draft': [('readonly', False)]})
    typeprinter = fields.Selection([
        ('offset', 'Offset'), ('digital', 'Digital'),
    ], 'Type of Machine', states={'draft': [('readonly', False)]})
    typeshop = fields.Selection([
        ('offsetprinting', 'OFFSET PRINTING'), ('signroll', 'ROLL SIGN SHOP'), ('signsheet', 'SHEET SIGN SHOP'),
    ], 'Type of business shop', states={'draft': [('readonly', False)]})
    sous_traitance = fields.Boolean('Print subcontracting')
    workcenter_id_print = fields.Many2one('mrp.workcenter', 'Attached workcenter')
    cycle_print = fields.Float('cycle', help="Production cylcle /hour ", digits=(8, 0))
    workcenter_id_callage = fields.Many2one('mrp.workcenter', 'Attached workcenter')
    cycle_callage = fields.Float('cycle', help="Production cylcle /hour ", digits=(8, 0))

    mini_cost_tirage = fields.Float(string="Minimum Price ", help="minimum price for printing", digits=(8, 0))


class printshop2_type_support(models.Model):
    _name = 'printshop2.type_support'
    _description = 'printshop2 Type Support'

    name = fields.Char('Type media', size=64)
    description = fields.Char('Description', size=128)


class printshop2_type_pelliculage(models.Model):
    _name = 'printshop2.type_pelliculage'
    _description = 'printshop2 Type pelliculage'
    _order = 'name'

    name = fields.Char('Type pelliculage', size=64, help='nema type laminate gloss, mat velour..')
    description = fields.Char('Description', size=128)
    line_ids2 = fields.One2many('product.product', 'type_pelliculage', 'Variants coating list')


# class pour determiner les supports pour impression en feuille
class printshop2_support(models.Model):
    _name = 'printshop2.support'
    _description = 'printshop2 Support'
    _order = "typeshop , marque , grammage"

    @api.model
    def _media_get_default(self):
        allpapermedia = self.env['printshop2.support.line'].search([('support_id', '=', id)])
        return allpapermedia

    @api.model
    def _support_get_default_of(self):
        allvariants = self.env['product.product'].search([('marque_support', '=', name)])
        self.write({'line_ids2': allvariants})

        return allvariants

    name = fields.Char('Familly', size=64, readonly=True)
    typeshop = fields.Selection([
        ('offsetprinting', 'OFFSET PRINTING'), ('signroll', 'ROLL SIGN SHOP'), ('signsheet', 'SHEET SIGN SHOP'),
    ], 'Type of business shop', states={'draft': [('readonly', False)]})
    grammage = fields.Float('Grammage', required=False, readonly=False, digits=(8, 0), help="in gramme")
    prix_kg = fields.Float('Kg price', digits=(8, 1))
    marque = fields.Char('Category')
    couleur = fields.Char('Color', default=" ")
    type_id = fields.Many2one('printshop2.type_support', 'Print media type', required=True)
    type = fields.Char(related='type_id.name', string="Print media type", readonly=True)

    line_ids = fields.One2many('printshop2.support.line', 'support_id', 'Variants Print media')
    line_ids2 = fields.One2many('product.product', 'marque_support', 'Variants Print media list')
    marge_support = fields.Float('marge for support', digits=(8, 2), help='10% = 1.10')

    @api.one
    def write_papername(self):
        id_product = self.ids[0]
        support = self.env['printshop2.support'].browse(id_product)
        self.write({'name': str(support.type) + '_' + str(support.marque) + '_' + str(support.couleur) + '_' + str(
            support.grammage)})
        return True

    @api.one
    def Create_paperline(self):
        id_product = self.ids[0]

        support = self.env['printshop2.support'].browse(id_product)
        paper_var = self.env['product.product'].search([('marque_support3', '=', support.name)])
        line_id = self.env['printshop2.support.line'].search([('support_id', '=', id_product)])
        for r in paper_var:
            lines_ids = [(2, 0, {'support_id': support.id, 'product_id': r.id, 'active': True})]

            lines_ids = [(0, 0, {'support_id': support.id, 'product_id': r.id})]

            support.write({"line_ids": lines_ids})


class printshop2_support_line(models.Model):
    _name = 'printshop2.support.line'
    _description = 'PRINTSHOP Support line'
    _order = " marque_support , gr_support"

    support_id = fields.Many2one('printshop2.support', 'Print media', required=False)
    typeshop = fields.Selection(related='support_id.typeshop', string="type printshop")
    product_id = fields.Many2one('product.product', 'Product', required=True)
    longueur_feuille = fields.Float(related='product_id.longueur_support', string="Print media length", help="in cm")
    largeur_feuille = fields.Float(related='product_id.largeur_support', string="Print media width", help="in cm")
    longueur_support = fields.Float(string="Print media length", readonly=True, help="in cm")
    largeur_support = fields.Float(rstring="Print media width", readonly=True, help="in cm")
    marge_support = fields.Float(related='support_id.marge_support', string="Print media grammage")

    gr_support = fields.Float(related='support_id.grammage', string="Print media grammage")
    kg_support = fields.Float(related='support_id.prix_kg', string="Print media kg's price")
    marque_support = fields.Char(related='product_id.marque_support3', string="Print media brand")
    prix_support = fields.Float(related='product_id.prix_feuille', store=False)
    list_price = fields.Float(related='product_id.list_price', string="Price sale of the sheet")
    actif = fields.Boolean('actif for calcul', default=True)
    laize_roll = fields.Float(related='product_id.laize_rouleau', string="Print roll media width", help="in cm")
    longueur_roll = fields.Float(related='product_id.longueur_rouleau', string="Print roll media lenght", help="in cm")

    @api.onchange('typeshop')
    def size_media(self):
        if self.typeshop == 'offsetprinting':
            self.largeur_support = self.largeur_feuille
            self.longueur_support = self.longueur_feuille

        if self.typeshop == 'signroll':
            self.largeur_support = self.laize_roll
            self.longueur_support = self.longueur_roll
        if self.typeshop == 'signsheet':
            self.largeur_support = self.largeur_feuille
            self.longueur_support = self.longueur_feuille


class printshop2_remise(models.Model):
    _name = 'printshop2.remise'
    _description = 'printshop2 remise'

    name = fields.Char('Name', size=64, required=False, readonly=False)
    valeur = fields.Float('Discount', required=False, readonly=False, help="decimal number: 10% = 1,10")


class printshop2_quantite(models.Model):
    _name = 'printshop2.quantite'
    _description = 'printshop2 quantite'
    _order = 'quantites'

    name = fields.Char('Name', size=64, required=False, readonly=False)
    printshop_id = fields.Many2one('offset.printshop', 'Offset Printshop', required=False)
    quantites = fields.Float('quantity', required=False, readonly=False, default=1, digits=(16, 0))
    price_qtes = fields.Float('prices qty', required=False, readonly=False)


class other_product_line(models.Model):
    _name = 'other.product.line'
    _description = 'other_price_product line'

    def get_prix_total(self):
        result = {}
        for line in self:
            total = 0
            total += (line.product_id.list_price * line.quantite)
            result[line.id] = total
        return result

    product_id = fields.Many2one('product.product', 'Produit', required=True, select=1)
    prix = fields.Float(related='product_id.list_price', store=False)
    quantite = fields.Float('quantite', required=False, readonly=False)

    prix_total = fields.Float(compute=get_prix_total, method=True, type='Float', string='cout Total Matieres',
                              store=False)

    other_product_id = fields.Many2one('offset.printshop', 'printshop_id', required=False)


class accessoire_product_line(models.Model):
    _name = 'accessoire.product.line'
    _description = 'accessoire_product line'

    def get_prix_total(self):
        result = {}
        for line in self:
            total = 0
            total += (line.product_id.list_price * line.quantite)
            result[line.id] = total
        return result

    product_id = fields.Many2one('product.product', 'Produit', required=True, select=1)
    prix = fields.Float(related='product_id.list_price', store=False)
    quantite = fields.Float('quantite', required=False, readonly=False)

    prix_total = fields.Float(compute=get_prix_total, method=True, type='Float', string='cout Total Matieres',
                              store=False)

    accessoire_product_id = fields.Many2one('offset.printshop', 'printshop_id', required=False)


class offset_printshop_priceline(models.Model):
    _name = 'offset.printshop.priceline'
    _description = 'Offset PRINTSHOP priceLine'
    _order = 'quantites,prix_qte'

    name = fields.Char('Name', size=64, required=False, readonly=True)
    # quantites = fields.Many2one('printshop2.quantite', 'quantite', required=False)
    quantites = fields.Float('Quantity', readonly=True)
    code_id = fields.Char('code_id', size=64, required=False, readonly=True)
    size = fields.Char('size', size=64, required=False, readonly=True)
    type_paper = fields.Char('type paper', size=64, required=False, readonly=True)
    side = fields.Char('nbr of side', size=64, required=False, readonly=True)
    color = fields.Char('nbr of color', size=64, required=False, readonly=True)
    laminate = fields.Char('type laminate', size=64, required=False, readonly=True)
    description = fields.Text('sale description', size=128, required=False, readonly=False)
    weight = fields.Float('weight', readonly=True)
    prix_qte_cout_mat = fields.Float('unit price of raw materials', readonly=True)
    prix_qte = fields.Float('unit Calculte price', readonly=True)
    prix_qte_sale = fields.Float('unit Sale Price')
    total_prix_qte = fields.Float('total prix vente', readonly=True)

    product_id = fields.Many2one('offset.printshop', 'produit', readonly=True)
    printshop_id = fields.Many2one('offset.printshop', 'Offset Printshop', readonly=True)


# nombre de combinaisons possible pour la realisation du travail
class offset_printshop_line(models.Model):
    _name = 'offset.printshop.line'
    _description = 'Offset PRINTSHOP Line'

    @api.multi
    def get_optimal(self):
        for line in self:
            try:
                if line.id == line.printshop_id.line_id.id:
                    self[line.id] = 'yes'
                else:
                    self[line.id] = 'no'
            except:
                pass
            return self

    name = fields.Char('Name', size=64, required=False, readonly=False)
    machine_id = fields.Many2one('printshop2.machine', 'machine', required=False)
    support_id = fields.Many2one('product.product', 'Print media', required=True)
    support_name = fields.Char(related='support_id.name')
    support_uom = fields.Float('uom')
    support_list_price = fields.Float(related='support_id.list_price')

    poses_machine = fields.Float('Poses machine')
    poses_support = fields.Float('Poses support')
    nbr_feuille = fields.Float('Nbr sheet')
    nbr_callage = fields.Float('nbr calage machine')
    nbr_insolation = fields.Float('nbr plate insolation')
    nbr_tirage = fields.Float('print')
    cout = fields.Float('Cost')
    cout_pelliculage = fields.Float('Cost')
    qte_impression = fields.Float('qte sheet printing')

    largeur_imp = fields.Float('Print width')
    longueur_imp = fields.Float('Print length')
    compute = fields.Boolean('Force')
    printshop_id = fields.Many2one('offset.printshop', 'Offset Printshop', required=True)
    nbr_m2 = fields.Float('Nbr m2')
    nbr_ml = fields.Float('Nbr Ml')
    pelliculage2_id = fields.Many2one('product.product', 'coating media')
    laize_pel = fields.Float('laize coating')
    ml_pelliculage = fields.Float('qty metre lianeaire coating')
    pelliculage_list_price = fields.Float(related='pelliculage2_id.list_price')
    pelliculage_name = fields.Char(related='pelliculage2_id.name')
    pelliculage_uom = fields.Float('uom coating')
    nbr_pose_pel = fields.Float('nbr_pose_pel')


class offset_printshop(models.Model):
    _order = "parent_id , date"
    _name = 'offset.printshop'
    _description = 'Offset PRINTSHOP'
    _order = 'name desc,partner_id,date'

    # def get_quantite_prod(self):
    #   for line in self:
    #      record.quantite_prod = record.quantite + (record.quantite*float(record.tolerance))

    def get_quantite_prod(self):
        result = {}
        for line in self.browse(ids[0]):
            result[line.id] = line.quantite + line.quantite * float(line.tolerance)
        return result

    # mise àjour des champs
    def _name_get_default(self):

        return self.env['ir.sequence'].next_by_code('offset.printshop')

    @api.model
    def _setting_get_default(self):
        profil_setting = self.env['printshop2.setting'].search([('name', '=', 'Standard')])
        return profil_setting

    @api.model
    def _machine_get_default_of(self):
        allmachines = self.env['printshop2.machine'].search(
            [('sous_traitance', '=', False), ('typeshop', '=', 'offsetprinting')])
        allmachines_inter = self.env['printshop2.machine'].search(
            [('sous_traitance', '=', False), ('typeshop', '=', 'offsetprinting')])

        self.write({'machine_ids': allmachines})
        self.write({'machine_ids2_inter': allmachines_inter})

        return allmachines
        return allmachines_inter

    @api.model
    def _machine_get_default_of_inter(self):

        allmachines_inter = self.env['printshop2.machine'].search(
            [('sous_traitance', '=', False), ('typeshop', '=', 'offsetprinting')])

        self.write({'machine_ids2_inter': allmachines_inter})

        return allmachines_inter

    @api.model
    def _machine_get_default_sh(self):
        allmachines = self.env['printshop2.machine'].search([('typeshop', '=', 'signsheet')])
        self.write({'machine_ids_signsheet': allmachines})
        return allmachines

    @api.model
    def _machine_get_default_rol(self):
        allmachines_sh = self.env['printshop2.machine'].search([('typeshop', '=', 'signroll')])
        self.write({'machine_ids_roll': allmachines_sh})
        return allmachines_sh

    name = fields.Char('Reference', size=64, required=True, readonly=True, default=_name_get_default)
    profil_setting = fields.Many2one('printshop2.setting', 'name', required=True, default=_setting_get_default)
    typeshop = fields.Selection([
        ('offsetprinting', 'OFFSET PRINTING'), ('signroll', 'ROLL SIGN SHOP'), ('signsheet', 'SHEET SIGN SHOP'),
    ], 'Type of business shop', states={'draft': [('readonly', False)]})
    child_ids = fields.One2many('offset.printshop', 'parent_id', 'Chils product', required=False,
                                states={'draft': [('readonly', False)]})
    parent_id = fields.Many2one('offset.printshop', 'Parent', required=False, index=True,
                                states={'draft': [('readonly', False)]})
    parent_is = fields.Boolean('Article compose', help='Check if the item is composed of several items')

    date = fields.Date('Date', states={'draft': [('readonly', False)]}, default=lambda *a: time.strftime('%Y-%m-%d'))

    partner_id = fields.Many2one('res.partner', 'Partner', required=False, states={'draft': [('readonly', False)]})
    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env['res.company']._company_default_get('sale.order'))

    imprime = fields.Char('Print Product', size=64, required=True, readonly=False,
                          states={'draft': [('readonly', False)]})
    largeur = fields.Float('width ', states={'draft': [('readonly', False)]}, help="in cm")
    longueur = fields.Float('Length', states={'draft': [('readonly', False)]}, help="in cm")
    fond_perdu = fields.Float(related='profil_setting.bleed', string="bleed", readonly=True, help="in cm")

    nbr_pages = fields.Selection([('1', 'Front'), ('2', 'Front/Back'), ],
                                 'Nbr printing face', default='2', states={'draft': [('readonly', False)]})
    nbr_coul_recto = fields.Selection(
        [('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ],
        'nbr color Front', required=False, default='4',
        states={'draft': [('readonly', False)]})
    nbr_coul_verso = fields.Selection(
        [('0', '0'), ('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ],
        'nbr color Back', required=False, default='4',
        states={'draft': [('readonly', False)]})

    product_id = fields.Many2one('product.product', 'Product', required=False, states={'draft': [('readonly', False)]})
    product_categorie = fields.Many2one('product.category', related='product_tmpl_id.categ_id',
                                        string="Product category")

    product_tmpl_id = fields.Many2one('product.template', 'Product created', required=False)
    product_tmpl2_id = fields.Char('Product created', required=False)

    quantite = fields.Float('Quantity ordered', states={'draft': [('readonly', False)]}, required=False, digits=(16, 0))

    tolerance = fields.Float(related='profil_setting.tolerance', string="Production Tolerance", readonly=True)
    marge = fields.Float(related='profil_setting.marge', string="general marge", readonly=True)
    raw_marge = fields.Float(related='profil_setting.raw_marge', string="raw materiels marge", readonly=True)

    quantite_prod = fields.Float(string='Production Quantity', digits=(16, 0))
    remise_id = fields.Many2one('printshop2.remise', 'Discount', required=False,
                                states={'draft': [('readonly', False)]})

    machine_ids = fields.Many2many('printshop2.machine', 'printshop_machine_rel', 'printshop_id', 'machine_id',
                                   string='machines', states={'draft': [('readonly', False)]}, required=False,
                                   help="Add machines to calculate printing", default=_machine_get_default_of
                                   )

    machine_ids_roll = fields.Many2many('printshop2.machine', 'printshop_machine_rel', 'printshop_id', 'machine_id',
                                        string='machines', states={'draft': [('readonly', False)]}, required=False,
                                        help="Add machines to calculate printing", default=_machine_get_default_rol
                                        )
    machine_ids_signsheet = fields.Many2many('printshop2.machine', 'printshop_machine_rel', 'printshop_id',
                                             'machine_id',
                                             string='machines', states={'draft': [('readonly', False)]}, required=False,
                                             help="Add machines to calculate printing", default=_machine_get_default_sh
                                             )
    support_id = fields.Many2one('printshop2.support', 'Print Media', required=False,
                                 states={'draft': [('readonly', False)]})
    support_fournis = fields.Boolean('Print media Supplied',
                                     help='Check whether the print media is supplied by the client')
    support_line_id = fields.Many2one('printshop2.support.line', 'Prints Media variants', required=False,
                                      states={'draft': [('readonly', False)]})

    support_line_id_2 = fields.One2many(related='support_id.line_ids2', required=False,
                                        states={'draft': [('readonly', False)]})

    support_ids = fields.Many2many('printshop2.support.line', 'printshop_support_line_rel', 'printshop_id',
                                   'support_id',
                                   string='Print Media', states={'draft': [('readonly', False)]}, required=False,
                                   help="Add Print Media to calculate printing")
    nbr_calage = fields.Float('Nbr Machine setting', readonly=True)

    Multiqty = fields.One2many('printshop2.quantite', 'printshop_id', 'Multiquantity', readonly=False)

    # 'prix_Multiqty' : fields.many2many('printshop2.quantite','printshop2_quantite_rel','printshop_id','name', 'quantite',readonly=False),
    priceline_ids = fields.One2many('offset.printshop.priceline', 'printshop_id', 'Calculs', required=False,
                                    states={'draft': [('readonly', False)]})

    # qte_1 = fields.Float('Qte 1', readonly=False,digits_compute=dp.get_precision('prix_vente_unitaire'),)
    # qte_2 = fields.Float('Qte 2', readonly=False,digits_compute=dp.get_precision('prix_vente_unitaire'),)
    # qte_3 = fields.Float('Qte 3', readonly=False,digits_compute=dp.get_precision('prix_vente_unitaire'),)
    # prix_qte_1 = fields.Float('Prix qte 1', readonly=False,)
    # prix_qte_2 = fields.Float('Prix qte 2', readonly=False,)
    # prix_qte_3 = fields.Float('Prix qte 3', readonly=False,)
    nbr_insolation = fields.Float('Nbr plate insolation', readonly=True)
    type_offset = fields.Selection([('applat', 'Card & flyer'),
                                    ('depliant', 'Leaflet folder'),
                                    ('brochure', 'Book & Booket'),
                                    ('blocnote', 'Notebook'),
                                    ('sac', 'Bag'),
                                    ('boite', 'Box'),
                                    ('Compose', 'Compound products')], 'Type', index=True)
    # champs finition
    # traitement de surface:
    pelliculage_id = fields.Many2one('product.product', 'Type Coating', required=False)
    type_pelliculage = fields.Many2one('printshop2.type_pelliculage', 'Type Coating')
    type_pelliculage_inter = fields.Many2one('printshop2.type_pelliculage', 'Type Coating inside')

    pelliculage_ids = fields.One2many(related='type_pelliculage.line_ids2', required=False)
    pelliculage_ids_inter = fields.One2many(related='type_pelliculage.line_ids2', required=False)

    nbr_pelliculage = fields.Selection([('0', 'without'),
                                        ('1', 'Front'),
                                        ('2', 'Front/Back')], 'Face coating', index=True, default='0',
                                       readonly=False, states={'draft': [('readonly', False)]})
    qte_pelliculage = fields.Float('Quantity of film coatings', readonly=True)
    serigraphie_id = fields.Many2one('product.product', 'varnish', required=False,
                                     states={'draft': [('readonly', False)]})
    nbr_serigraphie = fields.Selection([('0', 'without'),
                                        ('1', 'Front'),
                                        ('2', 'Front/Back')], 'Varnish faces', index=True, readonly=False,
                                       states={'draft': [('readonly', False)]})
    serigraphie_id_inter = fields.Many2one('product.product', 'varnish', required=False,
                                           states={'draft': [('readonly', False)]})
    nbr_serigraphie_inter = fields.Selection([('0', 'without'),
                                              ('1', 'Front'),
                                              ('2', 'Front/Back')], 'Varnish faces', index=True, readonly=False,
                                             states={'draft': [('readonly', False)]})
    qte_serigraphie_inter = fields.Float('Quantity of interior varnish', readonly=True)
    decoupe_id = fields.Many2one('product.product', 'Cutting', required=False, states={'draft': [('readonly', False)]})
    form_decoupe_id = fields.Many2one('product.product', 'Shape', required=False,
                                      states={'draft': [('readonly', False)]})
    poses_forme = fields.Float('Number of Poses per Cutting Form', required=False,
                               states={'draft': [('readonly', False)]}, digits=(8, 0))
    pliage_id = fields.Many2one('product.product', 'Folding', required=False, states={'draft': [('readonly', False)]})

    decoupe_id_inter = fields.Many2one('product.product', 'Cutting', required=False,
                                       states={'draft': [('readonly', False)]})
    form_decoupe_id_inter = fields.Many2one('product.product', 'Shape', required=False,
                                            states={'draft': [('readonly', False)]})
    poses_forme_inter = fields.Float('Number of Poses per Cutting Form', required=False,
                                     states={'draft': [('readonly', False)]}, digits=(8, 0))
    pliage_id_inter = fields.Many2one('product.product', 'Folding', required=False,
                                      states={'draft': [('readonly', False)]})

    qte_pliage = fields.Float('Qte Folding', readonly=False)

    accessoires_id = fields.Many2one('product.product', 'Accessory', required=False,
                                     states={'draft': [('readonly', False)]})

    accessoires_ids = fields.One2many('accessoire.product.line', 'accessoire_product_id', 'Accessoiry products',
                                      required=False,
                                      states={'draft': [('readonly', False)]})

    qte_accessoires = fields.Float('Qty Accessory', readonly=False)
    nbr_clichet = fields.Float('Number of Slices', states={'draft': [('readonly', False)]})
    clichet_vernis = fields.Many2one('product.product', 'Slices', required=False,
                                     states={'draft': [('readonly', False)]})
    clichet_vernis_inter = fields.Many2one('product.product', 'Slices', required=False,
                                           states={'draft': [('readonly', False)]})
    emballage_id = fields.Many2one('product.product', 'packaging', required=False,
                                   states={'draft': [('readonly', False)]})
    qte_emballage = fields.Float('Packet quantity', readonly=False, digits=(8, 0))
    qte_emballage_carton = fields.Float('Quantity of packages per carton', readonly=False, digits=(8, 0))

    emballage_carton_id = fields.Many2one('product.product', 'Cardboard packaging', required=False,
                                          states={'draft': [('readonly', False)]})

    nbr_clichet_gauffrage = fields.Float('Number of embossed pictures', states={'draft': [('readonly', False)]},
                                         digits=(8, 0))
    clichet_gauffarge = fields.Float('Embossed pictures', states={'draft': [('readonly', False)]})
    finition_pel = fields.Char('finition 1', size=64, states={'draft': [('readonly', False)]})
    finition_dec = fields.Char('finition 2', size=64, states={'draft': [('readonly', False)]})
    finition_pliage = fields.Char('finition 3', size=64, states={'draft': [('readonly', False)]})
    finition_piquage = fields.Char('finition 4', size=64, states={'draft': [('readonly', False)]})
    finition_collage = fields.Char('finition 5', size=64, states={'draft': [('readonly', False)]})
    finition_vernis = fields.Char('finition 6', size=64, states={'draft': [('readonly', False)]})

    # assembalge et relieure
    spirale_id = fields.Many2one('product.product', 'spirale', required=False, states={'draft': [('readonly', False)]})
    nbr_spirale = fields.Float('Number of loops per print', states={'draft': [('readonly', False)]}, digits=(8, 0))
    qte_spirale = fields.Float('Qte spirale', readonly=True, digits=(8, 0))
    piquage_id = fields.Many2one('product.product', 'Stitching', required=False,
                                 states={'draft': [('readonly', False)]})
    qte_piquage = fields.Float('Qty Stitchinge', readonly=True)
    collage_id = fields.Many2one('product.product', 'collage', required=False, states={'draft': [('readonly', False)]})

    ass_sac_id = fields.Many2one('product.product', 'assemblage sac', required=False,
                                 states={'draft': [('readonly', False)]})
    qte_ass_sac = fields.Float('Bag assembly', readonly=True)
    # note
    description = fields.Text('Description')
    desc_ventes = fields.Text('Sale description')
    bom_id = fields.Many2one('mrp.bom', 'BOM', states={'draft': [('readonly', False)]})
    line_ids = fields.One2many('offset.printshop.line', 'printshop_id', 'Calculs', required=False,
                               states={'draft': [('readonly', False)]})
    line_id = fields.Many2one('offset.printshop.line', 'optimal line', required=False,
                              states={'draft': [('readonly', False)]})
    user_id = fields.Many2one('res.users', 'user calculator', required=True, readonly=True,
                              states={'draft': [('readonly', False)]},
                              default=lambda self: self.env.uid)
    subproduct_ids = fields.One2many('offset.printshop.subproduct', 'printshop_id', 'Sub-products', required=False,
                                     states={'draft': [('readonly', False)]})
    cout_total = fields.Float(compute='get_cout_total_price', string='Total cost')
    cout_total_mat = fields.Float(compute='get_cout_total_mat', type='Float', string='Total cost of materials')

    prix_vente_unitaire = fields.Float(compute='get_cout_total_price', string='Unit selling price')
    prix_vente_total = fields.Float(compute='get_cout_total_price', string='Total selling price')
    state = fields.Selection([('draft', 'Draft'),
                              ('done', 'Done')], 'State', default='draft', index=True, readonly=True)
    # 'largeur_ouvert': fields.float('Largeur Ouvert', states={'draft':[('readonly',False)]}),
    # 'longueur_ouvert': fields.float('Longeur Ouvert', states={'draft':[('readonly',False)]}),
    #####champ pour couverture blocnote ou brochures
    largeur_inter = fields.Float('Interior open width', states={'draft': [('readonly', False)]}, help="in cm")
    longueur_inter = fields.Float('Inside length', states={'draft': [('readonly', False)]}, help="in cm")
    largeur_inter_bloc = fields.Float('width notebook sheet', states={'draft': [('readonly', False)]}, help="in cm")
    longueur_inter_bloc = fields.Float('length notebook sheet', states={'draft': [('readonly', False)]}, help="in cm")
    fond_perdu_inter = fields.Float('Bled inside sheet', states={'draft': [('readonly', False)]})
    nbr_pages_inter = fields.Selection([('1', 'Front'), ('2', 'Front/Back')],
                                       'Nbr face printing', states={'draft': [('readonly', False)]})
    nbr_coul_recto_inter = fields.Selection([('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5')],
                                            'Color Front interior', required=False,
                                            states={'draft': [('readonly', False)]})
    nbr_coul_verso_inter = fields.Selection([('0', '0'), ('1', '1'), ('2', '2'),
                                             ('3', '3'), ('4', '4'), ('5', '5')],
                                            'Color Back interior', required=False,
                                            states={'draft': [('readonly', False)]})

    machine_ids_inter = fields.Many2many('printshop2.machine', 'printshop_machine_rel', 'printshop_id',
                                         'machine_id', 'machines',
                                         states={'draft': [('readonly', False)]}, required=False,
                                         help="rajouter les machines pour calculer l'impression")

    machine_ids2_inter = fields.Many2many('printshop2.machine', 'printshop_machine_inter_rel', 'printshop_id',
                                          'machine_id',
                                          string='machines', states={'draft': [('readonly', False)]}, required=False,
                                          help="Add machines to calculate printing",
                                          default=_machine_get_default_of_inter
                                          )

    support_id_inter = fields.Many2one('printshop2.support', 'print media inside', required=False,
                                       states={'draft': [('readonly', False)]})
    support_inter = fields.Boolean('Print media Supplied',
                                   help='Check whether the print media is supplied by the client')
    support_line_id_inter = fields.Many2one('printshop2.support.line', 'Print Media', required=False,
                                            states={'draft': [('readonly', False)]})
    support_line_id_inter_2 = fields.One2many(related='support_id_inter.line_ids2', required=False,
                                              states={'draft': [('readonly', False)]})

    support_ids_inter = fields.Many2many('printshop2.support.line', 'printshop_support_line2_rel', 'printshop_id',
                                         'support_id',
                                         string='Print Media Inside', states={'draft': [('readonly', False)]},
                                         required=False,
                                         help="Add Print Media to calculate printing")
    pelliculage_id_inter = fields.Many2one('product.product', 'Inside lamination type', required=False,
                                           states={'draft': [('readonly', False)]})
    nbr_pelliculage_inter = fields.Selection([('0', 'Without'), ('1', 'Front'), ('2', 'Front/Back')],
                                             'Number of face', index=True, readonly=False,
                                             states={'draft': [('readonly', False)]})
    qte_pelliculage_inter = fields.Float('Qty laminate', readonly=True)
    ##########################
    contrecollage_id = fields.Many2one('product.product', ' service Sheet lamination', required=False,
                                       states={'draft': [('readonly', False)]})
    qte_contrecollage = fields.Selection([('1', 'Front'), ('2', 'Double side')],
                                         'Nbr faces Sheet lamination  ', readonly=False,
                                         states={'draft': [('readonly', False)]})
    support_id_contrecollage = fields.Many2one('printshop2.support', 'Media Sheet lamination ', required=False,
                                               states={'draft': [('readonly', False)]})
    support_id_rigide = fields.Many2one('printshop2.rigide', 'Media Sheet lamination ', required=False,
                                        states={'draft': [('readonly', False)]})

    # 'support_collage = fields.function (compute_contre_collage, method=True, type='Boolean', help='Cocher si le support d\'impression est fournit par le client',store=False),
    contrecollage = fields.Boolean('With lamination in sheet')
    largeur_contrecollage = fields.Float('width Sheet lamination', states={'draft': [('readonly', False)]},
                                         help="in cm")
    longueur_contrecollage = fields.Float('lenght Sheet lamination ', states={'draft': [('readonly', False)]},
                                          help="in cm")
    support_line_id_contrecollage = fields.Many2one('printshop2.support.line', 'Media laminate variants sheet',
                                                    required=False,
                                                    states={'draft': [('readonly', False)]})
    support_line_id_rigide = fields.Many2one('printshop2.rigide.line', 'Media laminate variants sheet', required=False,
                                             states={'draft': [('readonly', False)]})

    ###################
    largeur_ferme = fields.Float('Width Closed', states={'draft': [('readonly', False)]}, help="in cm")
    longueur_ferme = fields.Float('lenght closed', states={'draft': [('readonly', False)]}, help="in cm")
    largeur_ferme_inter = fields.Float('Width Closed interior', states={'draft': [('readonly', False)]}, help="in cm")
    longueur_ferme_inter = fields.Float('lenght Closed interior', states={'draft': [('readonly', False)]}, help="in cm")
    nbr_composants = fields.Float('Nbr of component not covered', states={'draft': [('readonly', False)]})
    # Champs Offset Brochure
    nbr_coul_r_v = fields.Selection([('0', '0'), ('1', '1'), ('2', '2'),
                                     ('3', '3'), ('4', '4'), ('5', '5')],
                                    'Nbr of color', required=False, default='4',
                                    states={'draft': [('readonly', False)]})
    nbr_pages_brochure = fields.Float('Number of pages', states={'draft': [('readonly', False)]}, digits=(8, 0))
    # Champs Offset Sac
    hauteur = fields.Float('Bag height', states={'draft': [('readonly', False)]})
    largeur_sac = fields.Float('Width Bag', states={'draft': [('readonly', False)]})
    soufflet = fields.Float('Bellows bag', states={'draft': [('readonly', False)]})
    # Champs boite etuis
    hauteur_boite = fields.Float('Box height', states={'draft': [('readonly', False)]})
    largeur_boite = fields.Float('Width box', states={'draft': [('readonly', False)]})
    profondeur_boite = fields.Float('Box depth', states={'draft': [('readonly', False)]})
    # Bloc Note
    nbr_feuille_bloc = fields.Float('Nbr of sheet', states={'draft': [('readonly', False)]}, digits=(8, 0),
                                    help="for notebook, give the nuber of sheet not of page")
    # Carnet avec souches
    souches = fields.Float('Nbr Strains', states={'draft': [('readonly', False)]}, digits=(8, 0))
    nbr_souches_carnet = fields.Float('Nbr Strains per book', states={'draft': [('readonly', False)]}, digits=(8, 0))
    parent = fields.Boolean('Parent', required=False, default=False)
    # constante = fields.Boolean('produit constant', readonly=False)
    ok_prod = fields.Boolean('Produced for production', readonly=False)
    size = fields.Float('size', states={'draft': [('readonly', False)]})
    paper = fields.Char('paper', states={'draft': [('readonly', False)]})
    color = fields.Char('color', states={'draft': [('readonly', False)]})
    embossing = fields.Char('embossing', states={'draft': [('readonly', False)]})

    dos_livre = fields.Float('book tickness', readonly=True)
    ref_spiral = fields.Char('ref spirale', readonly=True)
    # workcenter_id = fields.Many2one('mrp.workcenter', 'workcenter')

    # sign fields

    oeillet_id = fields.Many2one('product.product', 'Oeillet', required=False)
    oeillets = fields.Float('oeillets par m')
    nbr_oeillets_produit = fields.Float(type='Float', string='Oeillets par produit', store=False)
    couture_id = fields.Many2one('product.product', 'Couture', required=False)
    qte_couture = fields.Float('Qte Couture', readonly=True)
    baguette_id = fields.Many2one('product.product', 'Baguette', required=False)
    qte_baguettes = fields.Float('Qte Baguettes', readonly=True)
    raclage_id = fields.Many2one('product.product', 'Raclage', required=False)

    @api.depends('quantite')
    def get_cout_total_price(self):
        for record in self:
            total = 0
            total_mat = 0
            for sub in record.subproduct_ids:
                total += sub.subtotal
                # if record.subproduct_ids.matieres==True:
                # total_mat+=sub.subtotal

            record.cout_total = total
            # record.cout_total_mat = total_mat
            marge = record.marge

            record.prix_vente_unitaire = ((total * marge) / record.quantite)
            record.prix_vente_total = ((total * marge / record.quantite) + (
                total * (float(record.remise_id.valeur) / 100)) / record.quantite) * record.quantite

    @api.depends('quantite')
    def get_cout_total_mat(self):
        for line in self:
            total = 0
            for sub in line.subproduct_ids:
                if not sub.matieres:
                    continue
                total += sub.subtotal
            self.cout_total_mat = total

    @api.multi
    def compute_price(self, force=False):
        # pool = pooler.get_pool(cr.dbname)
        # id_printshop = self[0].id
        printshop = self.env['offset.printshop'].browse(self.id)
        return True

    @api.multi  # here
    def compute_parent(self):

        sql = '''
        DELETE from offset_printshop_subproduct where printshop_id = %s
        '''
        self.env.cr.execute(sql, (self.id,))
        for child in self.child_ids:
            for line in child.subproduct_ids:
                l = {'name': line.name,
                     'product_id': line.product_id.id,
                     'product_qty': line.product_qty,
                     'unit_price': line.unit_price,
                     'product_uom': line.product_uom.id,
                     'printshop_id': self.id}
                self.env['offset.printshop.subproduct'].create(l)
        return True

    # calcul aplat et couverture
    def compute(self, force=False):
        # printshop = self
        # id_printshop = ids[0]
        printshop = self.env['offset.printshop'].browse(self.ids)
        fond_perdu = printshop.fond_perdu
        longueur = printshop.longueur + fond_perdu

        largeur = printshop.largeur + fond_perdu

        quantite = printshop.quantite * printshop.tolerance

        # ajout ligne en bas
        nbr_face = float(printshop.nbr_pages)
        nbr_coul_recto = float(printshop.nbr_coul_recto)
        nbr_coul_verso = float(printshop.nbr_coul_verso)
        nbr_pelliculage = float(printshop.nbr_pelliculage)
        line = {}
        sql = '''
        DELETE from offset_printshop_subproduct where printshop_id = %s
        '''
        self.env.cr.execute(sql, (printshop.id,))
        if not force:
            sql = '''
            DELETE from offset_printshop_line where printshop_id = %s
            '''
            self.env.cr.execute(sql, (printshop.id,))
            cout_minimal = 0
            # self.compute_contre_collage ( ids, context={'support_collage':True},force=False): False

            for m in printshop.machine_ids:
                if nbr_coul_recto > m.nbr_coul_mach * 2:
                    continue

                nbr_pose_machine = 0
                largeur_imp = 0
                longueur_imp = 0
                largeur_imp_pince = 0
                longueur_imp_pince = 0
                qte_impression = 0
                if int(m.larg_mach / largeur) * int(m.long_mach / longueur) >= int(m.long_mach / largeur) * int(
                                m.larg_mach / longueur):
                    nbr_pose_machine = int(m.larg_mach / largeur) * int(m.long_mach / longueur)
                    largeur_imp = largeur * int(m.larg_mach / largeur)
                    longueur_imp = longueur * int(m.long_mach / longueur)
                    if largeur_imp < longueur_imp:
                        largeur_imp_pince = largeur_imp + m.prise_pince
                        longueur_imp_pince = longueur_imp
                    else:
                        largeur_imp_pince = largeur_imp
                        longueur_imp_pince = longueur_imp + m.prise_pince
                else:
                    nbr_pose_machine = int(m.long_mach / largeur) * int(m.larg_mach / longueur)
                    largeur_imp = largeur * int(m.long_mach / largeur)
                    longueur_imp = longueur * int(m.larg_mach / longueur)
                    if largeur_imp < longueur_imp:
                        largeur_imp_pince = largeur_imp + m.prise_pince
                        longueur_imp_pince = longueur_imp
                    else:
                        largeur_imp_pince = largeur_imp
                        longueur_imp_pince = longueur_imp + m.prise_pince
                if not nbr_pose_machine: continue
                qte_impression = (quantite / nbr_pose_machine) * nbr_face

                npm = []
                while nbr_pose_machine >= 1:
                    npm.append(nbr_pose_machine)
                    nbr_pose_machine -= 1
                for nbr_pose_machine in npm:
                    if nbr_pose_machine == int(m.larg_mach / largeur) * int(m.long_mach / longueur):
                        largeur_imp = largeur * int(m.larg_mach / largeur)
                        longueur_imp = longueur * int(m.long_mach / longueur)
                        if largeur_imp < longueur_imp:
                            largeur_imp_pince = largeur_imp + m.prise_pince
                            longueur_imp_pince = longueur_imp
                        else:
                            largeur_imp_pince = largeur_imp
                            longueur_imp_pince = longueur_imp + m.prise_pince
                    elif nbr_pose_machine == int(m.long_mach / largeur) * int(m.larg_mach / longueur):
                        largeur_imp = largeur * int(m.long_mach / largeur)
                        longueur_imp = longueur * int(m.larg_mach / longueur)
                        if largeur_imp < longueur_imp:
                            largeur_imp_pince = largeur_imp + m.prise_pince
                            longueur_imp_pince = longueur_imp
                        else:
                            longueur_imp_pince = largeur_imp
                            largeur_imp_pince = longueur_imp + m.prise_pince
                            # largeur_imp_pince = largeur_imp
                            # longueur_imp_pince = longueur_imp + m.prise_pince
                    # if not nbr_pose_machine == int(m.larg_mach / largeur) * int(m.long_mach / longueur) : continue


                    for s in printshop.support_id.line_ids2:

                        nbr_pose_support = 0
                        nbr_feuille = 0
                        nbr_callage = 0
                        nbr_insolation = 0
                        nbr_tirage = 0
                        if int(s.largeur_support / largeur_imp_pince) * int(
                                        s.longueur_support / longueur_imp_pince) > int(
                                    s.largeur_support / longueur_imp_pince) * int(
                                    s.longueur_support / largeur_imp_pince):
                            nbr_pose_support = int(s.largeur_support / largeur_imp_pince) * int(
                                s.longueur_support / longueur_imp_pince)
                        else:
                            nbr_pose_support = int(s.largeur_support / longueur_imp_pince) * int(
                                s.longueur_support / largeur_imp_pince)
                        if nbr_pose_support:
                            if nbr_pose_machine % 2 == 0:

                                nbr_callage = int((((nbr_coul_recto) / m.nbr_coul_mach)) + 0.75)
                                nbr_insolation = nbr_coul_recto
                            else:
                                nbr_callage = int(((nbr_coul_recto + nbr_coul_verso) / m.nbr_coul_mach) + 0.75)
                                nbr_insolation = (nbr_coul_recto + nbr_coul_verso)

                            nbr_tirage = int(((quantite / nbr_pose_machine) * nbr_face) * nbr_callage) + 1

                            # nbr_feuille = int((quantite / nbr_pose_machine) / nbr_pose_support) + int(m.nbr_passe)
                            nbr_feuille = int((quantite / nbr_pose_machine) / nbr_pose_support)
                            cout_papier = nbr_feuille * s.list_price

                            cout_tirage = nbr_tirage * m.print_id.list_price
                            if cout_tirage < m.mini_cost_tirage:
                                cout_tirage = m.mini_cost_tirage
                            cout_insolation = nbr_insolation * m.insolation_id.list_price
                            cout_calage = nbr_callage * m.calage_id.list_price
                            # cout = cout_papier + cout_tirage + cout_insolation + cout_calage


                            if not printshop.type_pelliculage:
                                cout = cout_papier + cout_tirage + cout_insolation + cout_calage
                                line = {'name': m.name + ' ' + s.name,
                                        'machine_id': m.id,
                                        'support_id': s.id,
                                        'support_name': s.name,
                                        'support_uom': s.uom_id.id,
                                        'support_list_price': s.list_price,
                                        'poses_machine': nbr_pose_machine,
                                        'poses_support': nbr_pose_support,
                                        'cout': cout,
                                        'nbr_feuille': nbr_feuille,
                                        'nbr_callage': nbr_callage,
                                        'nbr_insolation': nbr_insolation,
                                        'nbr_tirage': nbr_tirage,
                                        'compute': False,
                                        'printshop_id': self.id,
                                        'largeur_imp': largeur_imp_pince,
                                        'longueur_imp': longueur_imp_pince
                                        }
                                # cout = cout_papier + cout_tirage + cout_insolation + cout_calage
                                # self.env['offset.printshop.line'].create(line)
                                line = self.env['offset.printshop.line'].create(line)
                                if cout_minimal == 0: cout_minimal = cout
                                if cout <= cout_minimal:
                                    cout_minimal = cout
                                    largeur_impression = largeur_imp
                                    longueur_impression = 0
                                    printshop.line_id = line.id



                            else:
                                for pel in printshop.type_pelliculage.line_ids2:
                                    nbr_ml_pelliuclage = 0
                                    if pel.laize_rouleau > largeur_imp_pince or pel.laize_rouleau > longueur_imp_pince:
                                        nbr_pose_pel = (pel.laize_rouleau) / largeur_imp

                                        nbr_ml_pelliuclage_1 = (int((qte_impression/ nbr_face))) * (
                                            largeur_imp_pince / 100) * float(printshop.nbr_pelliculage) * (
                                                                   pel.laize_rouleau / 100)
                                        nbr_ml_pelliuclage_2 = (int((qte_impression / nbr_face))) * (
                                            longueur_imp_pince / 100) * float(printshop.nbr_pelliculage) * (
                                                                   pel.laize_rouleau / 100)
                                        if nbr_ml_pelliuclage_1 >= nbr_ml_pelliuclage_2:
                                            nbr_ml_pelliuclage = nbr_ml_pelliuclage_1
                                        else:
                                            nbr_ml_pelliuclage = nbr_ml_pelliuclage_2
                                        cout_pelliuclage = nbr_ml_pelliuclage * pel.list_price

                                    else:
                                        nbr_pose_pel = 0
                                        nbr_ml_pelliuclage = 9999999 * quantite
                                        cout_pelliuclage = 9999999 * quantite








                                        # if printshop.type_pelliculage:
                                    cout = cout_papier + cout_tirage + cout_insolation + cout_calage + cout_pelliuclage
                                    line = {'name': m.name + ' ' + s.name,
                                            'machine_id': m.id,
                                            'support_id': s.id,
                                            'support_name': s.name,
                                            'support_uom': s.uom_id.id,
                                            'support_list_price': s.list_price,
                                            'pelliculage2_id': pel.id,
                                            'nbr_pose_pel': nbr_pose_pel,
                                            'qte_impression' : qte_impression,

                                            'laize_pel': pel.laize_rouleau,
                                            'ml_pelliculage': nbr_ml_pelliuclage,
                                            'pelliculage_list_price': pel.list_price,
                                            'pelliculage_name': pel.name,
                                            'pelliculage_uom': pel.uom_id.id,
                                            'cout_pelliculage': cout_pelliuclage,
                                            'poses_machine': nbr_pose_machine,
                                            'poses_support': nbr_pose_support,
                                            'cout': cout,
                                            'nbr_feuille': nbr_feuille,
                                            'nbr_callage': nbr_callage,
                                            'nbr_insolation': nbr_insolation,
                                            'nbr_tirage': nbr_tirage,
                                            'compute': False,
                                            'printshop_id': self.id,
                                            'largeur_imp': largeur_imp_pince,
                                            'longueur_imp': longueur_imp_pince
                                            }
                                    cout = cout_papier + cout_tirage + cout_insolation + cout_calage + cout_pelliuclage
                                    line = self.env['offset.printshop.line'].create(line)

                                    if cout_minimal == 0: cout_minimal = cout
                                    if cout <= cout_minimal:
                                        cout_minimal = cout
                                        largeur_impression = largeur_imp
                                        longueur_impression = 0
                                        printshop.line_id = line.id

        self.generate_subproducts(quantite, qte_impression)
        if printshop.contrecollage == 1:
                self.compute_contre_collage()
        return True

    def compute_signsheet(self, force=False):
        # printshop = self
        # id_printshop = ids[0]
        printshop = self.env['offset.printshop'].browse(self.ids)
        longueur = printshop.longueur + printshop.fond_perdu
        largeur = printshop.largeur + printshop.fond_perdu
        fond_perdu = printshop.fond_perdu
        quantite = printshop.quantite * printshop.tolerance
        print 'quantitecompute'
        print quantite
        # ajout ligne en bas
        nbr_face = float(printshop.nbr_pages)
        nbr_coul_recto = float(printshop.nbr_coul_recto)
        nbr_coul_verso = float(printshop.nbr_coul_verso)
        nbr_pelliculage = float(printshop.nbr_pelliculage)
        line = {}
        sql = '''
        DELETE from offset_printshop_subproduct where printshop_id = %s
        '''
        self.env.cr.execute(sql, (printshop.id,))
        if not force:
            sql = '''
            DELETE from offset_printshop_line where printshop_id = %s
            '''
            self.env.cr.execute(sql, (printshop.id,))
            cout_minimal = 0
            # self.compute_contre_collage ( ids, context={'support_collage':True},force=False): False
            if printshop.contrecollage == 1:
                self.compute_contre_collage()
            for m in printshop.machine_ids:
                nbr_pose_machine = 0
                largeur_imp = 0
                longueur_imp = 0
                largeur_imp_pince = 0
                longueur_imp_pince = 0
                qte_impression = 0
                if int(m.larg_mach / largeur) * int(m.long_mach / longueur) > int(m.long_mach / largeur) * int(
                                m.larg_mach / longueur):
                    nbr_pose_machine = int(m.larg_mach / largeur) * int(m.long_mach / longueur)
                    largeur_imp = largeur * int(m.larg_mach / largeur)
                    longueur_imp = longueur * int(m.long_mach / longueur)
                else:
                    nbr_pose_machine = int(m.long_mach / largeur) * int(m.larg_mach / longueur)
                    largeur_imp = largeur * int(m.long_mach / largeur)
                    longueur_imp = longueur * int(m.larg_mach / longueur)
                if largeur_imp < longueur_imp:
                    largeur_imp_pince = largeur_imp + m.prise_pince
                    longueur_imp_pince = longueur_imp
                else:
                    largeur_imp_pince = largeur_imp
                    longueur_imp_pince = longueur_imp + m.prise_pince
                if not nbr_pose_machine: continue
                qte_impression = (quantite / nbr_pose_machine) * nbr_face

                npm = []
                while nbr_pose_machine >= 1:
                    npm.append(nbr_pose_machine)
                    nbr_pose_machine -= 1
                for nbr_pose_machine in npm:
                    for s in printshop.support_id.line_ids:
                        nbr_pose_support = 0
                        nbr_feuille = 0
                        nbr_tirage = 0
                        if int(s.largeur_support / largeur_imp_pince) * int(
                                        s.longueur_support / longueur_imp_pince) > int(
                                    s.largeur_support / longueur_imp_pince) * int(
                                    s.longueur_support / largeur_imp_pince):
                            nbr_pose_support = int(s.largeur_support / largeur_imp_pince) * int(
                                s.longueur_support / longueur_imp_pince)
                        else:
                            nbr_pose_support = int(s.largeur_support / longueur_imp_pince) * int(
                                s.longueur_support / largeur_imp_pince)
                        if nbr_pose_support:
                            if nbr_pose_machine % 2 == 0:
                                nbr_callage = int((((nbr_coul_recto) / m.nbr_coul_mach)) + 0.75)
                                nbr_insolation = nbr_coul_recto
                            else:
                                nbr_callage = int(((nbr_coul_recto + nbr_coul_verso) / m.nbr_coul_mach) + 0.75)
                                nbr_insolation = (nbr_coul_recto + nbr_coul_verso)

                            nbr_tirage = int(((quantite / nbr_pose_machine) * nbr_face) * nbr_callage) + 1

                            nbr_feuille = int((quantite / nbr_pose_machine) / nbr_pose_support) + 1

                            cout_papier = nbr_feuille * s.list_price
                            cout_tirage = nbr_tirage * m.print_id.list_price
                            cout = cout_papier + cout_tirage
                            line = {'name': m.name + ' ' + s.name,
                                    'machine_id': m.id,
                                    'support_id': s.id,
                                    'support_name': s.name,
                                    'support_uom': s.uom_id.id,
                                    'poses_machine': nbr_pose_machine,
                                    'poses_support': nbr_pose_support,
                                    'cout': cout,
                                    'nbr_feuille': nbr_feuille,
                                    'nbr_tirage': nbr_tirage,
                                    'compute': False,
                                    'printshop_id': self.id,
                                    'largeur_imp': largeur_imp,
                                    'longueur_imp': longueur_imp
                                    }
                            # self.env['offset.printshop.line'].create(line)
                            line = self.env['offset.printshop.line'].create(line)
                            if cout_minimal == 0: cout_minimal = cout
                            if cout <= cout_minimal:
                                cout_minimal = cout
                                largeur_impression = largeur_imp
                                longueur_impression = 0
                                printshop.line_id = line.id
        self.generate_subproducts(quantite, qte_impression)
        return True

    def compute_signroll(self, force=False):
        # printshop = self
        # id_printshop = ids[0]
        printshop = self.env['offset.printshop'].browse(self.ids)
        longueur = printshop.longueur + (printshop.fond_perdu / 10)
        largeur = printshop.largeur + (printshop.fond_perdu / 10)
        fond_perdu = printshop.fond_perdu / 10
        quantite = printshop.quantite
        # ajout ligne en bas
        nbr_face = float(printshop.nbr_pages)
        nbr_coul_recto = 4
        nbr_coul_verso = 0
        line = {}
        sql = '''
        DELETE from offset_printshop_subproduct where printshop_id = %s
        '''
        self.env.cr.execute(sql, (printshop.id,))
        if not force:
            sql = '''
            DELETE from sign_printshop_line where printshop_id = %s
            '''
            self.env.cr.execute(sql, (printshop.id,))
            poses = 0
            ml = 0
            m2 = 0
            cout_minimal = 0
            # self.compute_contre_collage ( ids, context={'support_collage':True},force=False): False
            # if not force_poses and force_m2:
            for m in printshop.machine_ids_roll:
                laize_mach = printshop.machine_ids_roll.larg_mach - (printshop.machine_ids_roll.prise_pince / 10)

                for s in printshop.support_id.line_ids:
                    nbr_pose = 0
                    nbr_ml = 0
                    nbr_m2 = 0
                    if s.largeur_support <= laize_mach:
                        if (int(s.largeur_support / largeur) > int(s.largeur_support / longueur)):
                            nbr_pose = int(s.largeur_support / largeur)
                            if nbr_pose == 0: nbr_pose = 1
                            nbr_ml = longueur * (quantite / int(nbr_pose))
                            nbr_m2 = nbr_ml * s.largeur_support
                            m2_print = largeur * longueur * quantite
                        else:
                            nbr_pose = int(s.largeur_support / longueur)
                            if nbr_pose == 0: nbr_pose = 1
                            nbr_ml = (largeur * quantite) / int(nbr_pose)
                            nbr_m2 = nbr_ml * s.largeur_support
                        if m2 == 0:
                            m2 = nbr_m2
                        if nbr_m2 <= m2:
                            poses = nbr_pose
                            ml = nbr_ml
                            m2 = nbr_m2
                        qte_impression = (quantite / nbr_pose)
                        cout_papier = m2 * s.list_price
                        cout_tirage = m2 * m.print_id.list_price
                        cout = cout_papier + cout_tirage
                        line = {'name': m.name + ' ' + s.name,
                                'machine_id': m.id,
                                'support_id': s.id,
                                'support_name': s.name,
                                'support_uom': s.uom_id.id,
                                'poses_machine': nbr_pose,
                                'poses_support': nbr_pose,
                                'cout': cout,
                                'nbr_m2': nbr_m2,
                                'nbr_ml': nbr_ml,
                                'nbr_tirage': nbr_m2,

                                'compute': False,
                                'printshop_id': self.id,
                                'largeur_imp': largeur,
                                'longueur_imp': longueur
                                }
                        # self.env['offset.printshop.line'].create(line)
                        line = self.env['offset.printshop.line'].create(line)
                        if cout_minimal == 0: cout_minimal = cout
                        if cout <= cout_minimal:
                            cout_minimal = cout
                            largeur_impression = largeur
                            longueur_impression = 0
                            printshop.line_id = line.id
        self.generate_subproducts_roll(quantite, qte_impression)

        return True

    # calcul contre collage sur carton
    def compute_contre_collage(self, force=False):
        # pool = pooler.get_pool(cr.dbname)
        # id_printshop = self.ids[0]
        printshop = self.env['offset.printshop'].browse(self.ids)
        longueur = printshop.longueur_contrecollage
        largeur = printshop.largeur_contrecollage
        quantite = printshop.quantite * printshop.tolerance
        # ajout ligne en bas
        line = {}
        sql = '''
            DELETE from offset_printshop_subproduct where printshop_id = %s
            '''
        self._cr.execute(sql, (self.ids[0],))
        if not force:
            sql = '''
                DELETE from offset_printshop_line where printshop_id = %s
                '''
            self._cr.execute(sql, (self.ids[0],))
            cout_minimal = 0
            for s in printshop.support_id_rigide.line_ids:

                if int(s.largeur_support / largeur) * int(s.longueur_support / longueur) > int(
                                s.largeur_support / longueur) * int(s.longueur_support / largeur):
                    nbr_pose_support = int(s.largeur_support / largeur) * int(s.longueur_support / longueur)
                else:
                    nbr_pose_support = int(s.largeur_support / longueur) * int(s.longueur_support / largeur)

                nbr_feuille = int(quantite / nbr_pose_support) + 1
                cout_papier = nbr_feuille * s.list_price
                # cout= cout_papier+cout_tirage+cout_insolation+cout_calage
                cout = cout_papier
                line = {'name': s.support_id.name,
                        'support_id': s.support_id.id, 'poses_support': nbr_pose_support, 'cout': cout,
                        'nbr_feuille': nbr_feuille,
                        'compute': False, 'printshop_id': self.ids[0],

                        }
                # line_id=self.env['offset.printshop.line'].create(line)
                line = self.env['offset.printshop.line'].create(line)

                if cout_minimal == 0: cout_minimal = cout
                if cout <= cout_minimal:
                    cout_minimal = cout
                    printshop.line_id = line.id

                    # self.write({'line_id' : line_id})
        # Création des lignes des produits consomés  --------------------------------------------------------------------------------
        self.generate_subproducts_collage(quantite)


        # fonction calcul quantite

    def compute_qte_1(self, force=False):
        # pool = pooler.get_pool(cr.dbname)
        # id_printshop = self.ids[0]
        printshop = self.env['offset.printshop'].browse(self.ids[0])
        line = {}
        sql = '''
            DELETE from offset_printshop_priceline where printshop_id = %s
            '''
        self._cr.execute(sql, (self.ids[0],))
        if not force:
            sql = '''
                DELETE from offset_printshop_priceline where printshop_id = %s
                '''
            self._cr.execute(sql, (self.ids[0],))
        for q in printshop.Multiqty:

            self.write({'quantite': q.quantites})

            # self.compute( ids, context={},force=False)
            if printshop.typeshop == 'offsetprinting':
                if printshop.type_offset == 'applat':
                    self.compute(force=False)
                if printshop.type_offset == 'depliant':
                    self.compute(force=False)
                    self.write({'largeur_ferme': printshop.largeur / 2})
                    self.write({'longueur_ferme': printshop.longueur})
                if printshop.type_offset == 'blocnote':
                    self.compute_int_bloc(force=False)
                    # self.compute(force=False)

                if printshop.type_offset == 'brochure':
                    self.compute_int_brochure(force=False)

                if printshop.type_offset == 'sac':
                    self.compute_sac(force=False)
                if printshop.type_offset == 'boite':
                    self.compute_boite(force=False)
            if printshop.typeshop == 'signroll':
                self.compute_signroll(force=False)
            if printshop.typeshop == 'signsheet':
                self.compute_signsheet(force=False)

            # self.write({ q.price_qtes : float(printshop.prix_vente_unitaire)})
            price = printshop.prix_vente_unitaire
            total_prix_qte = printshop.prix_vente_unitaire * printshop.quantite

            price2 = q.price_qtes
            cout = printshop.cout_total

            cout_mat = printshop.cout_total_mat / printshop.quantite

            self.env['offset.printshop.priceline'].create({
                'name': printshop.imprime,
                'code_id': printshop.name,
                'size': str(printshop.largeur) + "*" + str(printshop.longueur),
                'type_paper': printshop.support_id.name,
                'description': printshop.desc_ventes,

                'side': printshop.nbr_pages,
                'color': printshop.nbr_coul_recto,
                'laminate': str(printshop.pelliculage_id) + " " + str(printshop.nbr_pelliculage),
                # 'cut':fields.char('cutting', size=64, required=False, readonly=False),
                # 'surface_traitement':fields.char('surface traitement', size=64, required=False, readonly=False),
                # 'weight' : fields.float('weight'),
                'prix_qte': price,
                'total_prix_qte': total_prix_qte,
                'prix_qte_cout_mat': cout_mat * printshop.raw_marge,
                'quantites': printshop.quantite,
                'printshop_id': self.id})

        return True

    def compute_dos_livre(self, force=False):
        printshop = self.env['offset.printshop'].browse(self.ids[0])
        gr_couv = printshop.support_id.grammage / 1000
        gr_inter = printshop.support_id_inter.grammage / 1000

        if printshop.type_offset == 'blocnote':
            p_inter = int(printshop.nbr_feuille_bloc)
        if printshop.type_offset == 'brochure':
            p_inter = int(printshop.nbr_pages_brochure) / 2
        self.write({'dos_livre': (2 * gr_couv) + (p_inter * gr_inter / 10)})

        # self.write({'dos_livre' :  250/1000 })

        if printshop.dos_livre <= 3.7:
            self.write({'ref_spiral': "3/16   - 3:1"})
        elif printshop.dos_livre >= 3.8 and printshop.dos_livre <= 5.4:
            self.write({'ref_spiral': "1/4   - 3:1"})
        elif printshop.dos_livre >= 5.5 and printshop.dos_livre <= 6.9:
            self.write({'ref_spiral': "5/16   - 3:1"})
        elif printshop.dos_livre >= 7 and printshop.dos_livre <= 8.4:
            self.write({'ref_spiral': "3/8   - 3:1"})
        elif printshop.dos_livre >= 8.5 and printshop.dos_livre <= 10:
            self.write({'ref_spiral': "7/16   - 3:1"})
        elif printshop.dos_livre >= 10.1 and printshop.dos_livre <= 11.6:
            self.write({'ref_spiral': "1/2   - 3:1"})
        elif printshop.dos_livre >= 11.7 and printshop.dos_livre <= 13.2:
            self.write({'ref_spiral': "9/16   - 3:1"})
        elif printshop.dos_livre >= 13.3 and printshop.dos_livre <= 14.8:
            self.write({'ref_spiral': "5/8   - 2:1"})
        elif printshop.dos_livre >= 14.9 and printshop.dos_livre <= 17.9:
            self.write({'ref_spiral': "3/4   - 2:1"})
        elif printshop.dos_livre >= 18 and printshop.dos_livre <= 22.7:
            self.write({'ref_spiral': "7/8   - 2:1"})
        elif printshop.dos_livre >= 22.8 and printshop.dos_livre <= 25:
            self.write({'ref_spiral': "1   - 2:1"})

        return

    def compute_int_bloc(self, force=False):
        printshop = self.env['offset.printshop'].browse(self.ids)
        longueur = printshop.longueur_inter_bloc + printshop.fond_perdu
        largeur = (printshop.largeur_inter_bloc) + printshop.fond_perdu
        fond_perdu = printshop.fond_perdu
        quantite = printshop.quantite * printshop.tolerance * printshop.nbr_feuille_bloc
        print quantite
        # ajout ligne en bas
        nbr_face = float(printshop.nbr_pages_inter)
        nbr_coul_recto = float(printshop.nbr_coul_recto_inter)
        nbr_coul_verso = float(printshop.nbr_coul_verso_inter)
        nbr_pelliculage = float(printshop.nbr_pelliculage)
        line = {}
        sql = '''
        DELETE from offset_printshop_subproduct where printshop_id = %s
        '''
        self.env.cr.execute(sql, (printshop.id,))
        if not force:
            sql = '''
            DELETE from offset_printshop_line where printshop_id = %s
            '''
            self.env.cr.execute(sql, (printshop.id,))
            cout_minimal = 0
            # self.compute_contre_collage ( ids, context={'support_collage':True},force=False): False
            self.compute(force=False)
            if printshop.contrecollage == 1:
                self.compute_contre_collage()
            for m in printshop.machine_ids2_inter:
                if nbr_coul_recto > m.nbr_coul_mach * 2:
                    continue

                nbr_pose_machine = 0
                largeur_imp = 0
                longueur_imp = 0
                largeur_imp_pince = 0
                longueur_imp_pince = 0
                qte_impression = 0
                if int(m.larg_mach / largeur) * int(m.long_mach / longueur) > int(m.long_mach / largeur) * int(
                                m.larg_mach / longueur):
                    nbr_pose_machine = int(m.larg_mach / largeur) * int(m.long_mach / longueur)
                    largeur_imp = largeur * int(m.larg_mach / largeur)
                    longueur_imp = longueur * int(m.long_mach / longueur)
                else:
                    nbr_pose_machine = int(m.long_mach / largeur) * int(m.larg_mach / longueur)
                    largeur_imp = largeur * int(m.long_mach / largeur)
                    longueur_imp = longueur * int(m.larg_mach / longueur)
                if largeur_imp < longueur_imp:
                    largeur_imp_pince = largeur_imp + m.prise_pince
                    longueur_imp_pince = longueur_imp
                else:
                    largeur_imp_pince = largeur_imp
                    longueur_imp_pince = longueur_imp + m.prise_pince
                if not nbr_pose_machine: continue
                qte_impression = (quantite / nbr_pose_machine) * nbr_face

                npm = []
                while nbr_pose_machine >= 1:
                    npm.append(nbr_pose_machine)
                    nbr_pose_machine -= 1
                for nbr_pose_machine in npm:
                    if nbr_pose_machine == int(m.larg_mach / largeur) * int(m.long_mach / longueur):
                        largeur_imp = largeur * int(m.larg_mach / largeur)
                        longueur_imp = longueur * int(m.long_mach / longueur)
                        if largeur_imp < longueur_imp:
                            largeur_imp_pince = largeur_imp + m.prise_pince
                            longueur_imp_pince = longueur_imp
                        else:
                            largeur_imp_pince = largeur_imp
                            longueur_imp_pince = longueur_imp + m.prise_pince
                    elif nbr_pose_machine == int(m.long_mach / largeur) * int(m.larg_mach / longueur):
                        largeur_imp = largeur * int(m.long_mach / largeur)
                        longueur_imp = longueur * int(m.larg_mach / longueur)
                        if largeur_imp < longueur_imp:
                            largeur_imp_pince = largeur_imp + m.prise_pince
                            longueur_imp_pince = longueur_imp
                        else:
                            largeur_imp_pince = largeur_imp
                            longueur_imp_pince = longueur_imp + m.prise_pince
                    # if not nbr_pose_machine == int(m.larg_mach / largeur) * int(m.long_mach / longueur) : continue
                    for s in printshop.support_id_inter.line_ids2:
                        nbr_pose_support = 0
                        nbr_feuille = 0
                        nbr_callage = 0
                        nbr_insolation = 0
                        nbr_tirage = 0
                        if int(s.largeur_support / largeur_imp_pince) * int(
                                        s.longueur_support / longueur_imp_pince) > int(
                                    s.largeur_support / longueur_imp_pince) * int(
                                    s.longueur_support / largeur_imp_pince):
                            nbr_pose_support = int(s.largeur_support / largeur_imp_pince) * int(
                                s.longueur_support / longueur_imp_pince)
                        else:
                            nbr_pose_support = int(s.largeur_support / longueur_imp_pince) * int(
                                s.longueur_support / largeur_imp_pince)
                        if nbr_pose_support:
                            if nbr_pose_machine % 2 == 0:
                                nbr_callage = int((((nbr_coul_recto) / m.nbr_coul_mach)) + 0.75)
                                nbr_insolation = nbr_coul_recto
                            else:
                                nbr_callage = int(((nbr_coul_recto + nbr_coul_verso) / m.nbr_coul_mach) + 0.75)
                                nbr_insolation = (nbr_coul_recto + nbr_coul_verso)

                            nbr_tirage = int(((quantite / nbr_pose_machine) * nbr_face) * nbr_callage) + 1

                            nbr_feuille = int((quantite / nbr_pose_machine) / nbr_pose_support) + int(m.nbr_passe)

                            cout_papier = nbr_feuille * s.list_price

                            cout_tirage = nbr_tirage * m.print_id.list_price
                            if cout_tirage < m.mini_cost_tirage:
                                cout_tirage = m.mini_cost_tirage
                            cout_insolation = nbr_insolation * m.insolation_id.list_price
                            cout_calage = nbr_callage * m.calage_id.list_price
                            # cout = cout_papier + cout_tirage + cout_insolation + cout_calage


                            if not printshop.type_pelliculage_inter:
                                cout = cout_papier + cout_tirage + cout_insolation + cout_calage
                                line = {'name': m.name + ' ' + s.name,
                                        'machine_id': m.id,
                                        'support_id': s.id,
                                        'support_name': s.name,
                                        'support_uom': s.uom_id.id,
                                        'support_list_price': s.list_price,
                                        'poses_machine': nbr_pose_machine,
                                        'poses_support': nbr_pose_support,
                                        'cout': cout,
                                        'nbr_feuille': nbr_feuille,
                                        'nbr_callage': nbr_callage,
                                        'nbr_insolation': nbr_insolation,
                                        'nbr_tirage': nbr_tirage,
                                        'compute': False,
                                        'printshop_id': self.id,
                                        'largeur_imp': largeur_imp_pince,
                                        'longueur_imp': longueur_imp_pince
                                        }
                                # cout = cout_papier + cout_tirage + cout_insolation + cout_calage
                                # self.env['offset.printshop.line'].create(line)
                                line = self.env['offset.printshop.line'].create(line)
                                if cout_minimal == 0: cout_minimal = cout
                                if cout <= cout_minimal:
                                    cout_minimal = cout
                                    largeur_impression = largeur_imp
                                    longueur_impression = 0
                                    printshop.line_id = line.id



                            else:
                                for pel in printshop.type_pelliculage_inter.line_ids2:
                                    nbr_ml_pelliuclage = 0
                                    if pel.laize_rouleau > largeur_imp_pince or pel.laize_rouleau > longueur_imp_pince:
                                        nbr_pose_pel = (pel.laize_rouleau) / largeur_imp

                                        nbr_ml_pelliuclage_1 = (int((qte_impression))) * (
                                            largeur_imp_pince / 100) * float(printshop.nbr_pelliculage_inter) * (
                                                                   pel.laize_rouleau / 100)
                                        nbr_ml_pelliuclage_2 = (int((qte_impression ))) * (
                                            longueur_imp_pince / 100) * float(printshop.nbr_pelliculage_inter) * (
                                                                   pel.laize_rouleau / 100)
                                        if nbr_ml_pelliuclage_1 >= nbr_ml_pelliuclage_2:
                                            nbr_ml_pelliuclage = nbr_ml_pelliuclage_1
                                        else:
                                            nbr_ml_pelliuclage = nbr_ml_pelliuclage_2
                                        cout_pelliuclage = nbr_ml_pelliuclage * pel.list_price

                                    else:
                                        nbr_pose_pel = 0
                                        nbr_ml_pelliuclage = 9999999 * quantite
                                        cout_pelliuclage = 9999999 * quantite







                                        # if printshop.type_pelliculage:
                                    cout = cout_papier + cout_tirage + cout_insolation + cout_calage + cout_pelliuclage
                                    line = {'name': m.name + ' ' + s.name,
                                            'machine_id': m.id,
                                            'support_id': s.id,
                                            'support_name': s.name,
                                            'support_uom': s.uom_id.id,
                                            'support_list_price': s.list_price,
                                            'pelliculage2_id': pel.id,
                                            'nbr_pose_pel': nbr_pose_pel,
                                            'qte_impression': qte_impression,

                                            'laize_pel': pel.laize_rouleau,
                                            'ml_pelliculage': nbr_ml_pelliuclage,
                                            'pelliculage_list_price': pel.list_price,
                                            'pelliculage_name': pel.name,
                                            'pelliculage_uom': pel.uom_id.id,
                                            'cout_pelliculage': cout_pelliuclage,
                                            'poses_machine': nbr_pose_machine,
                                            'poses_support': nbr_pose_support,
                                            'cout': cout,
                                            'nbr_feuille': nbr_feuille,
                                            'nbr_callage': nbr_callage,
                                            'nbr_insolation': nbr_insolation,
                                            'nbr_tirage': nbr_tirage,
                                            'compute': False,
                                            'printshop_id': self.id,
                                            'largeur_imp': largeur_imp_pince,
                                            'longueur_imp': longueur_imp_pince
                                            }
                                    cout = cout_papier + cout_tirage + cout_insolation + cout_calage + cout_pelliuclage
                                    line = self.env['offset.printshop.line'].create(line)

                                    if cout_minimal == 0: cout_minimal = cout
                                    if cout <= cout_minimal:
                                        cout_minimal = cout
                                        largeur_impression = largeur_imp
                                        longueur_impression = 0
                                        printshop.line_id = line.id

        self.generate_subproducts_inter_bloc(quantite, qte_impression)
        return True

    ###
    # calcul interieur bloc note
    def compute_int_bloc_WW(self, force=False):
        # pool = pooler.get_pool(cr.dbname)
        id_printshop = self.ids[0]
        printshop = self.env['offset.printshop'].browse(id_printshop)

        longueur = printshop.longueur_inter + printshop.fond_perdu
        largeur = (printshop.largeur_inter) + printshop.fond_perdu
        fond_perdu = printshop.fond_perdu
        quantite = printshop.quantite_prod * printshop.nbr_feuille_bloc
        # ajout ligne en bas
        nbr_face = float(printshop.nbr_pages_inter)
        nbr_coul_recto = float(printshop.nbr_coul_recto_inter)
        nbr_coul_verso = float(printshop.nbr_coul_verso_inter)
        nbr_pelliculage = float(printshop.nbr_pelliculage)
        line = {}
        sql = '''
            DELETE from offset_printshop_subproduct where printshop_id = %s
            '''
        self._cr.execute(sql, (self.ids[0],))
        if not force:
            sql = '''
                DELETE from offset_printshop_line where printshop_id = %s
                '''
            self._cr.execute(sql, (self.ids[0],))
            cout_minimal = 0
            self.compute(force=False)
            for m in printshop.machine_ids2_inter:
                if nbr_coul_recto > m.nbr_coul_mach * 2:
                    continue

                nbr_pose_machine = 0
                largeur_imp = 0
                longueur_imp = 0
                largeur_imp_pince = 0
                longueur_imp_pince = 0
                qte_impression = 0
                if int(m.larg_mach / largeur) * int(m.long_mach / longueur) > int(m.long_mach / largeur) * int(
                                m.larg_mach / longueur):
                    nbr_pose_machine = int(m.larg_mach / largeur) * int(m.long_mach / longueur)
                    largeur_imp = largeur * int(m.larg_mach / largeur)
                    longueur_imp = longueur * int(m.long_mach / longueur)
                else:
                    nbr_pose_machine = int(m.long_mach / largeur) * int(m.larg_mach / longueur)
                    largeur_imp = largeur * int(m.long_mach / largeur)
                    longueur_imp = longueur * int(m.larg_mach / longueur)
                if largeur_imp < longueur_imp:
                    largeur_imp_pince = largeur_imp + m.prise_pince
                    longueur_imp_pince = longueur_imp
                else:
                    largeur_imp_pince = largeur_imp
                    longueur_imp_pince = longueur_imp + m.prise_pince
                if not nbr_pose_machine: continue
                qte_impression = (quantite / nbr_pose_machine) * nbr_face
                npm = []
                while nbr_pose_machine >= 1:
                    npm.append(nbr_pose_machine)
                    nbr_pose_machine -= 1
                for nbr_pose_machine in npm:
                    if nbr_pose_machine == int(m.larg_mach / largeur) * int(m.long_mach / longueur):
                        largeur_imp = largeur * int(m.larg_mach / largeur)
                        longueur_imp = longueur * int(m.long_mach / longueur)
                        if largeur_imp < longueur_imp:
                            largeur_imp_pince = largeur_imp + m.prise_pince
                            longueur_imp_pince = longueur_imp
                        else:
                            largeur_imp_pince = largeur_imp
                            longueur_imp_pince = longueur_imp + m.prise_pince
                    elif nbr_pose_machine == int(m.long_mach / largeur) * int(m.larg_mach / longueur):
                        largeur_imp = largeur * int(m.long_mach / largeur)
                        longueur_imp = longueur * int(m.larg_mach / longueur)
                        if largeur_imp < longueur_imp:
                            largeur_imp_pince = largeur_imp + m.prise_pince
                            longueur_imp_pince = longueur_imp
                        else:
                            largeur_imp_pince = largeur_imp
                            longueur_imp_pince = longueur_imp + m.prise_pince
                    # if not nbr_pose_machine == int(m.larg_mach / largeur) * int(m.long_mach / longueur) : continue
                    for s in printshop.support_id_inter.line_ids:
                        nbr_pose_support = 0
                        nbr_feuille = 0
                        nbr_callage = 0
                        nbr_insolation = 0
                        nbr_tirage = 0
                        if int(s.largeur_support / largeur_imp_pince) * int(
                                        s.longueur_support / longueur_imp_pince) > int(
                                    s.largeur_support / longueur_imp_pince) * int(
                                    s.longueur_support / largeur_imp_pince):
                            nbr_pose_support = int(s.largeur_support / largeur_imp_pince) * int(
                                s.longueur_support / longueur_imp_pince)
                        else:
                            nbr_pose_support = int(s.largeur_support / longueur_imp_pince) * int(
                                s.longueur_support / largeur_imp_pince)
                        if nbr_pose_support:
                            if nbr_pose_machine % 2 == 0:
                                nbr_callage = int((((nbr_coul_recto) / m.nbr_coul_mach)) + 0.75)
                                nbr_insolation = nbr_coul_recto
                            else:
                                nbr_callage = int(((nbr_coul_recto + nbr_coul_verso) / m.nbr_coul_mach) + 0.75)
                                nbr_insolation = (nbr_coul_recto + nbr_coul_verso)

                            nbr_tirage = int(((quantite / nbr_pose_machine) * nbr_face) * nbr_callage) + 1
                            nbr_feuille = int((quantite / nbr_pose_machine) / nbr_pose_support) + 1
                            cout_papier = nbr_feuille * s.list_price
                            cout_tirage = nbr_tirage * m.print_id.list_price
                            cout_insolation = nbr_insolation * m.insolation_id.list_price
                            cout_calage = nbr_callage * m.calage_id.list_price
                            cout = cout_papier + cout_tirage + cout_insolation + cout_calage
                            line = {'name': m.name + ' ' + s.name,
                                    'machine_id': m.id,
                                    'support_id': s.id,
                                    'support_name': s.name,
                                    'support_uom': s.uom_id.id,

                                    'poses_machine': nbr_pose_machine,
                                    'poses_support': nbr_pose_support,
                                    'cout': cout,
                                    'nbr_feuille': nbr_feuille,
                                    'nbr_callage': nbr_callage,
                                    'nbr_insolation': nbr_insolation,
                                    'nbr_tirage': nbr_tirage,
                                    'compute': False,
                                    'printshop_id': self.id,
                                    'largeur_imp': largeur_imp_pince,
                                    'longueur_imp': longueur_imp_pince
                                    }

                            line_id = self.env['offset.printshop.line'].create(line)

                            if cout_minimal == 0: cout_minimal = cout
                            if cout <= cout_minimal:
                                cout_minimal = cout
                                largeur_impression = largeur_imp
                                longueur_impression = 0
                                # self.write({'line_id' : line_id})
                                # line = self.env['offset.printshop.line'].write(line)
                                # self.write(cr, uid, [printshop.id], {'line_id' : line_id})
                                # self.env['offset.printshop.line'].write({'line_id' : line_id})

        # Création des lignes des produits consomés  --------------------------------------------------------------------------------
        self.generate_subproducts_inter_bloc(quantite, qte_impression)

        return True

    ##__________________
    def generate_subproducts_inter_bloc(self, quantite, qte_impression):
        # pool = pooler.get_pool(cr.dbname)
        id_printshop = self.ids[0]
        printshop = self.env['offset.printshop'].browse(id_printshop)

        support_line_inter = {'name': '[Print media inside] ' + str(printshop.line_id.support_name) + '\n'
                                      + "__________Print size : " + str(printshop.line_id.largeur_imp) + " * " + str(
            printshop.line_id.longueur_imp)
                                      + "__________Pnbr pose in sheet:" + str(
            printshop.line_id.poses_support) + "__________Pnbr pose in print:" + str(printshop.line_id.poses_machine)
                                      + "__________nbr passe en grande feuille: " + str(
            printshop.line_id.machine_id.nbr_passe * printshop.line_id.nbr_callage),
                              'product_id': printshop.line_id.support_id.id,
                              'product_qty': printshop.line_id.nbr_feuille + (
                                  printshop.line_id.machine_id.nbr_passe * printshop.line_id.nbr_callage),
                              'unit_price': printshop.line_id.support_list_price,
                              'constante': 0,
                              'matieres': True,
                              'workcenter': False,
                              # 'product_uom': printshop.line_id.support_id.uom_id.id,
                              'printshop_id': self.id}
        if not printshop.support_fournis:
            self.env['offset.printshop.subproduct'].create(support_line_inter)

        insolation_line = {'name': '[Plate insollation] ' + printshop.line_id.machine_id.insolation_id.name,
                           'product_id': printshop.line_id.machine_id.insolation_id.id,
                           'product_qty': printshop.line_id.nbr_insolation,
                           'unit_price': printshop.line_id.machine_id.insolation_id.list_price,
                           'product_uom': printshop.line_id.machine_id.insolation_id.uom_id.id,
                           'constante': 1,
                           'matieres': True,
                           'workcenter': False,

                           'printshop_id': self.id}
        self.env['offset.printshop.subproduct'].create(insolation_line)

        callage_line = {'name': '[Setting] ' + printshop.line_id.machine_id.calage_id.name,
                        'product_id': printshop.line_id.machine_id.calage_id.id,
                        'product_qty': printshop.line_id.nbr_callage,
                        'unit_price': printshop.line_id.machine_id.calage_id.list_price,
                        'product_uom': printshop.line_id.machine_id.calage_id.uom_id.id,
                        'constante': 1,
                        'matieres': False,
                        'workcenter': True,
                        'printshop_id': self.id}
        self.env['offset.printshop.subproduct'].create(callage_line)

        tirage_line = {'name': '[Print] ' + str(
            printshop.line_id.machine_id.print_id.name) + "__________Pnbr pose in print:" + str(
            printshop.line_id.poses_machine) + '\n',
                       'product_id': printshop.line_id.machine_id.print_id.id,
                       'product_qty': printshop.line_id.nbr_tirage,
                       'unit_price': printshop.line_id.machine_id.prix_tirage,
                       'product_uom': printshop.line_id.machine_id.print_id.uom_id.id,
                       'constante': 0,
                       'matieres': False,
                       'workcenter': True,
                       'printshop_id': self.id}
        self.env['offset.printshop.subproduct'].create(tirage_line)

        if printshop.type_pelliculage_inter:
            pelliculage_line = {'name': printshop.type_pelliculage_inter.name + '\n'
                                        + " ft: " + str(printshop.line_id.largeur_imp) + "*" + str(
                printshop.line_id.longueur_imp) + " ________nbr face:" + str(printshop.nbr_pelliculage) + '\n'
                                        + "  qte  feuilles: " + str(
                printshop.line_id.qte_impression ) + " feuilles",
                                'product_id': printshop.line_id.pelliculage2_id.id,
                                'product_qty': int(
                                    printshop.line_id.ml_pelliculage) + 1,
                                # 'product_qty' : int(printshop.nbr_pelliculage)*(printshop.quantite*108/100)*(printshop.largeur/100)*(printshop.longueur/100),
                                'unit_price': printshop.line_id.pelliculage_list_price,
                                # 'product_uom': printshop.line_id.pelliculage_uom,
                                # 'finition_pel': 'name',
                                'constante': 0,
                                'matieres': True,
                                'workcenter': False,
                                'printshop_id': self.id}
            self.env['offset.printshop.subproduct'].create(pelliculage_line)

        if printshop.serigraphie_id_inter:
            serigraphie_line_inter = {'name': printshop.serigraphie_id_inter.name + '\n'
                                              + " ft: " + str(printshop.line_id.largeur_imp + 1) + "*" + str(
                printshop.line_id.longueur_imp + 1) + " face:" + str(printshop.nbr_serigraphie_inter) + '\n'
                                              + "  qte : " + str(
                int(printshop.nbr_serigraphie_inter) * (printshop.quantite * 1.10 / printshop.line_id.poses_machine) * (
                    (printshop.line_id.largeur_imp + 1) / 100) * ((printshop.line_id.longueur_imp + 1) / 100)) + " m2",
                                      'product_id': printshop.serigraphie_id_inter.id,
                                      'product_qty': int(printshop.nbr_serigraphie_inter) * (
                                          printshop.quantite * 1.10 / printshop.line_id.poses_machine),
                                      # 'product_qty' : int(printshop.nbr_pelliculage)*(printshop.quantite*108/100)*(printshop.largeur/100)*(printshop.longueur/100),
                                      'unit_price': printshop.serigraphie_id_inter.list_price,
                                      'product_uom': printshop.serigraphie_id_inter.uom_id.id,
                                      'constante': 0,
                                      'matieres': False,
                                      'workcenter': True,
                                      # 'finition_pel': 'name',
                                      'printshop_id': self.id}
            self.env['offset.printshop.subproduct'].create(serigraphie_line_inter)

        if printshop.pliage_id_inter:
            pliage_line = {'name': '[Folding] ' + printshop.pliage_id_inter.name,
                           'product_id': printshop.pliage_id_inter.id,
                           'product_qty': quantite,
                           'unit_price': printshop.pliage_id_inter.list_price,
                           'product_uom': printshop.pliage_id_inter.uom_id.id,
                           'constante': 0,
                           'matieres': False,
                           'workcenter': True,
                           'printshop_id': self.id}
            self.env['offset.printshop.subproduct'].create(pliage_line)

        if printshop.decoupe_id_inter:
            decoupe_line = {'name': '[Cutting] ' + printshop.decoupe_id_inter.name,
                            'product_id': printshop.decoupe_id_inter.id,
                            'product_qty': quantite / printshop.poses_forme,
                            'unit_price': printshop.decoupe_id_inter.list_price,
                            'product_uom': printshop.decoupe_id_inter.uom_id.id,
                            'constante': 0,
                            'matieres': False,
                            'workcenter': True,
                            'printshop_id': self.id}
            self.env['offset.printshop.subproduct'].create(decoupe_line)

        if printshop.form_decoupe_id_inter:
            form_decoupe_line_inter = {'name': '[clichet] ' + printshop.form_decoupe_id_inter.name,
                                       'product_id': printshop.form_decoupe_id_inter.id,
                                       'product_qty': 1,
                                       'unit_price': printshop.form_decoupe_id_inter.list_price,
                                       'product_uom': printshop.form_decoupe_id_inter.uom_id.id,
                                       'constante': 1,
                                       'matieres': True,
                                       'workcenter': False,
                                       'printshop_id': self.id}
            self.env['offset.printshop.subproduct'].create(form_decoupe_line_inter)

        if printshop.clichet_vernis_inter:
            form_decoupe_line_inter = {'name': '[Varnish] ' + printshop.clichet_vernis_inter.name,
                                       'product_id': printshop.clichet_vernis_inter.id,
                                       'product_qty': 1,
                                       'unit_price': printshop.clichet_vernis_inter.list_price,
                                       'product_uom': printshop.clichet_vernis_inter.uom_id.id,
                                       'constante': 1,
                                       'matieres': True,
                                       'workcenter': False,
                                       'printshop_id': self.id}
            self.env['offset.printshop.subproduct'].create(form_decoupe_line_inter)

        compteur = 0
        for e in printshop.line_ids:
            compteur += 1
        description = '''Machine : %s
    Support : %s0,00
    Combinaisons possibles : %s
                        ''' % (
            printshop.line_id.machine_id.print_id.name, printshop.line_id.support_id.name, str(compteur))

        self.write({'description': description})
        pell = '-Coating : ' + str(printshop.nbr_pelliculage) + ' faces de type ' + str(
            printshop.pelliculage_id.name) + '\n'
        if printshop.nbr_pelliculage_inter == '0': pell_inter = ''  # pelliculage
        pell_inter = '-Coating  : ' + str(printshop.nbr_pelliculage_inter) + ' faces de type ' + str(
            printshop.pelliculage_id_inter.name) + '\n'
        if printshop.nbr_pelliculage_inter == '0': pellinter = ''  # pelliculage
        deco = '-Cutting : ' + str(printshop.form_decoupe_id.name) + '\n'
        if printshop.form_decoupe_id.name == False: deco = ''  # découpe
        pli = '-Folding : ' + str(printshop.pliage_id.name) + '\n'
        if printshop.pliage_id.name == False: pli = ''  # pliage
        coll = '-Glue : ' + str(printshop.collage_id.name) + '\n'
        if printshop.collage_id.name == False: coll = ''  # collage
        ver = '-Varnish : ' + str(printshop.clichet_vernis.id) + '\n'
        if printshop.clichet_vernis.id == False: ver = ''  # vernie
        plaqu = '   Assemblage :' + '\n' + '-Piquage : ' + str(printshop.piquage_id.name) + '\n'
        if printshop.piquage_id.name == '0': plaqu = ''
        spir = '   Assemblage :' + '\n' + '-Spirale : ' + str(printshop.nbr_spirale) + ' Boucles' + '\n'
        if printshop.nbr_spirale == 0.0: spir = ''
        verso = str(printshop.nbr_coul_verso_inter) + 'couleur(s) verso' + '\n'
        if printshop.nbr_coul_verso_inter == 0: verso = ''

        self.write({'desc_ventes': 'Article n°:' + str(printshop.name) + '\n' +
                                   str(printshop.imprime) + '\n' +
                                   ' __Cover : ' + '\n' +
                                   '   size : ' + str(printshop.largeur) + ' x ' + str(printshop.longueur) + '\n' +
                                   '   Print : ' + str(printshop.nbr_coul_recto) + ' recto, ' + str(
            printshop.nbr_coul_verso) + ' verso.' + '\n' +
                                   '   print media : ' + str(printshop.support_id.name) + ' ' + ',' + '\n'
                                   + str(pell)
                                   + str(deco)
                                   + str(coll)
                                   + str(pli)
                                   + str(ver)
                                   + str(spir)
                                   + '\n' +
                                   ' __Inside : ' + '\n' +
                                   '   Size  : ' + str(printshop.largeur_inter) + ' x ' + str(
            printshop.longueur_inter) + '\n' +
                                   '   Print : ' + str(printshop.nbr_feuille_bloc) + ' feuilles, ' + str(
            printshop.nbr_coul_recto_inter) + 'couleur(s) recto, ' + str(
            printshop.nbr_coul_verso_inter) + ' couleur(s) verso.' + '\n' +
                                   '   Print media : ' + str(printshop.support_id_inter.name) + ' ' + ',' + '\n'

                       , })

    ##__________________

    # calcul interieur brochures
    def compute_int_brochure(self, force=False):
        id_printshop = self.ids[0]
        printshop = self.env['offset.printshop'].browse(id_printshop)

        self.write({'largeur_ferme': printshop.largeur / 2})
        self.write({'longueur_ferme': printshop.longueur})
        self.write({'largeur_ferme_inter': printshop.largeur_inter / 2})
        self.write({'longueur_ferme_inter': printshop.longueur_inter})
        longueur_int = printshop.longueur_inter + printshop.fond_perdu
        largeur_int = printshop.largeur_inter + printshop.fond_perdu
        fond_perdu = printshop.fond_perdu
        quantite = printshop.quantite * printshop.tolerance
        # ajout ligne en bas
        nbr_face = float(printshop.nbr_pages)
        nbr_coul_recto = float(printshop.nbr_coul_recto)
        nbr_coul_verso = float(printshop.nbr_coul_verso)
        nbr_pelliculage = float(printshop.nbr_pelliculage)
        line = {}
        if printshop.nbr_pages_brochure % 4:
            raise osv.except_osv(('Error'),
                                 ('Le nombre de page doit etre multiple de 4'))
        if printshop.type_offset == 'brochure':
            nbr_pages = float(printshop.nbr_pages_brochure) / 2
        else:
            nbr_pages = float(printshop.nbr_pages_brochure) / 2
        nbr_coul_r_v = float(printshop.nbr_coul_r_v)

        sql = '''
        DELETE from offset_printshop_subproduct where printshop_id = %s
        '''
        self.env.cr.execute(sql, (printshop.id,))
        if not force:
            sql = '''
            DELETE from offset_printshop_line where printshop_id = %s
            '''
            self.env.cr.execute(sql, (printshop.id,))
            cout_minimal = 0
            self.compute(force=False)
            for m in printshop.machine_ids2_inter:
                if nbr_coul_r_v > m.nbr_coul_mach * 2:
                    continue
                nbr_couleur_machine = m.nbr_coul_mach
                nbr_pose_machine, largeur_imp, longueur_imp, largeur_imp_pince, longueur_imp_pince, qte_impression = 0, 0, 0, 0, 0, 0
                if int(m.larg_mach / largeur_int) * int(m.long_mach / longueur_int) > int(
                                m.long_mach / largeur_int) * int(m.larg_mach / longueur_int):
                    nbr_pose_machine = int(m.larg_mach / largeur_int) * int(m.long_mach / longueur_int)
                    largeur_imp = largeur_int * int(m.larg_mach / largeur_int)
                    longueur_imp = longueur_int * int(m.long_mach / longueur_int)
                else:
                    nbr_pose_machine = int(m.long_mach / largeur_int) * int(m.larg_mach / longueur_int)
                    largeur_imp = largeur_int * int(m.long_mach / largeur_int)
                    longueur_imp = longueur_int * int(m.larg_mach / longueur_int)
                if largeur_imp < longueur_imp:
                    largeur_imp_pince = largeur_imp + m.prise_pince
                    longueur_imp_pince = longueur_imp
                else:
                    largeur_imp_pince = largeur_imp
                    longueur_imp_pince = longueur_imp + m.prise_pince
                if not nbr_pose_machine: continue
                # qte_impression=(quantite/nbr_pose_machine)*2#nbr_face
                npm = []
                while nbr_pose_machine >= 1:
                    npm.append(nbr_pose_machine)
                    nbr_pose_machine -= 1
                for nbr_pose_machine in npm:
                    if nbr_pose_machine == int(m.larg_mach / largeur_int) * int(m.long_mach / longueur_int):
                        largeur_imp = largeur_int * int(m.larg_mach / largeur_int)
                        longueur_imp = longueur_int * int(m.long_mach / longueur_int)
                        if largeur_imp < longueur_imp:
                            largeur_imp_pince = largeur_imp + m.prise_pince
                            longueur_imp_pince = longueur_imp
                        else:
                            largeur_imp_pince = largeur_imp
                            longueur_imp_pince = longueur_imp + m.prise_pince
                    elif nbr_pose_machine == int(m.long_mach / largeur_int) * int(m.larg_mach / longueur_int):
                        largeur_imp = largeur_int * int(m.long_mach / largeur_int)
                        longueur_imp = longueur_int * int(m.larg_mach / longueur_int)
                        if largeur_imp < longueur_imp:
                            largeur_imp_pince = largeur_imp + m.prise_pince
                            longueur_imp_pince = longueur_imp
                        else:
                            largeur_imp_pince = largeur_imp
                            longueur_imp_pince = longueur_imp + m.prise_pince
                    # if not nbr_pose_machine == int(m.larg_mach / largeur) * int(m.long_mach / longueur) : continue
                    for s in printshop.support_id_inter.line_ids2:
                        nbr_pose_support, nbr_feuille, nbr_callage, nbr_insolation, nbr_tirage = 0, 0, 0, 0, 0
                        if int(s.largeur_support / largeur_imp_pince) * int(
                                        s.longueur_support / longueur_imp_pince) > int(
                                    s.largeur_support / longueur_imp_pince) * int(
                                    s.longueur_support / largeur_imp_pince):
                            nbr_pose_support = int(s.largeur_support / largeur_imp_pince) * int(
                                s.longueur_support / longueur_imp_pince)
                        else:
                            nbr_pose_support = int(s.largeur_support / longueur_imp_pince) * int(
                                s.longueur_support / largeur_imp_pince)
                        x, y = str(((nbr_pages) / nbr_pose_machine)).split('.')
                        if nbr_pose_support:
                            if y == 0:
                                nbr_callage = round(
                                    float(((nbr_pages) / nbr_pose_machine) * ((nbr_coul_r_v) / nbr_couleur_machine)), 0)
                                # nbr_insolation =((nbr_pages/2)/nbr_pose_machine)*(nbr_coul_r_v)
                                nbr_insolation = nbr_callage * nbr_couleur_machine
                                qte_impression = quantite * ((nbr_pages) / nbr_pose_machine)
                                nbr_feuille = (qte_impression / 2) / nbr_pose_support
                                nbr_tirage = quantite * nbr_callage
                            else:
                                nbr_pages_a = int(float(x) * nbr_pose_machine * 2)
                                nbr_pages_b = nbr_pages - nbr_pages_a

                                # print ((nbr_pages_a/2)/nbr_pose_machine)
                                # print ( (nbr_coul_r_v)/nbr_couleur_machine)
                                nbr_callage = round(float(((nbr_pages_a) / nbr_pose_machine) * (
                                    int(((nbr_coul_r_v) / nbr_couleur_machine) + 0.75)) + (
                                                              (nbr_pages_b) / nbr_pose_machine) * (
                                                              int(((nbr_coul_r_v) / nbr_couleur_machine) + 0.75))), 0)
                                nbr_insolation = nbr_callage * nbr_couleur_machine
                                # nbr_insolation =((nbr_pages_a/2)/nbr_pose_machine)*(nbr_coul_r_v)+((nbr_pages_b/2)/nbr_pose_machine)*(nbr_coul_r_v)
                                qte_impression = (quantite * ((nbr_pages_a) / nbr_pose_machine)) + (
                                    quantite * ((nbr_pages_b) / nbr_pose_machine))
                                nbr_feuille = (qte_impression / 2) / nbr_pose_support
                                # nbr_tirage = qte_impression*nbr_callage*2
                                nbr_tirage = quantite * nbr_callage

                                # nbr_callage_a = ((nbr_pages_a/2)/nbr_pose_machine) *( (nbr_coul_r_v)/nbr_couleur_machin)
                                # nbr_insolation_a = ((nbr_pages_a/2)/nbr_pose_machine)*(nbr_coul_r_v)
                                # qte_impression_a = quantite * ((nbr_pages_a/2)/nbr_pose_machine)
                                # nbr_feuille_a = (qte_impression_a/2)/nbr_pose_support
                                # tirage_a = qte_impression_a*nbr_callage

                            cout_papier = nbr_feuille * s.list_price

                            cout_tirage = nbr_tirage * m.print_id.list_price
                            if cout_tirage < m.mini_cost_tirage:
                                cout_tirage = m.mini_cost_tirage
                            cout_insolation = nbr_insolation * m.insolation_id.list_price
                            cout_calage = nbr_callage * m.calage_id.list_price
                            # cout = cout_papier + cout_tirage + cout_insolation + cout_calage


                            if not printshop.type_pelliculage_inter:
                                cout = cout_papier + cout_tirage + cout_insolation + cout_calage
                                line = {'name': m.name + ' ' + s.name,
                                        'machine_id': m.id,
                                        'support_id': s.id,
                                        'support_name': s.name,
                                        'support_uom': s.uom_id.id,
                                        'support_list_price': s.list_price,
                                        'poses_machine': nbr_pose_machine,
                                        'poses_support': nbr_pose_support,
                                        'cout': cout,
                                        'nbr_feuille': nbr_feuille,
                                        'nbr_callage': nbr_callage,
                                        'nbr_insolation': nbr_insolation,
                                        'nbr_tirage': nbr_tirage,
                                        'compute': False,
                                        'printshop_id': self.id,
                                        'largeur_imp': largeur_imp_pince,
                                        'longueur_imp': longueur_imp_pince
                                        }
                                # cout = cout_papier + cout_tirage + cout_insolation + cout_calage
                                # self.env['offset.printshop.line'].create(line)
                                line = self.env['offset.printshop.line'].create(line)
                                if cout_minimal == 0: cout_minimal = cout
                                if cout <= cout_minimal:
                                    cout_minimal = cout
                                    largeur_impression = largeur_imp
                                    longueur_impression = 0
                                    printshop.line_id = line.id



                            else:
                                for pel in printshop.type_pelliculage_inter.line_ids2:
                                    nbr_ml_pelliuclage = 0
                                    if pel.laize_rouleau > largeur_imp_pince or pel.laize_rouleau > longueur_imp_pince:
                                        nbr_pose_pel = (pel.laize_rouleau) / largeur_imp

                                        nbr_ml_pelliuclage_1 = (int((qte_impression))) * (
                                            largeur_imp_pince / 100) * float(printshop.nbr_pelliculage_inter) * (
                                                                   pel.laize_rouleau / 100)
                                        nbr_ml_pelliuclage_2 = (int((qte_impression ))) * (
                                            longueur_imp_pince / 100) * float(printshop.nbr_pelliculage_inter) * (
                                                                   pel.laize_rouleau / 100)
                                        if nbr_ml_pelliuclage_1 >= nbr_ml_pelliuclage_2:
                                            nbr_ml_pelliuclage = nbr_ml_pelliuclage_1
                                        else:
                                            nbr_ml_pelliuclage = nbr_ml_pelliuclage_2
                                        cout_pelliuclage = nbr_ml_pelliuclage * pel.list_price

                                    else:
                                        nbr_pose_pel = 0
                                        nbr_ml_pelliuclage = 9999999 * quantite
                                        cout_pelliuclage = 9999999 * quantite







                                        # if printshop.type_pelliculage:
                                    print qte_impression
                                    print "qte_impression"
                                    cout = cout_papier + cout_tirage + cout_insolation + cout_calage + cout_pelliuclage
                                    line = {'name': m.name + ' ' + s.name,
                                            'machine_id': m.id,
                                            'support_id': s.id,
                                            'support_name': s.name,
                                            'support_uom': s.uom_id.id,
                                            'support_list_price': s.list_price,
                                            'pelliculage2_id': pel.id,
                                            'nbr_pose_pel': nbr_pose_pel,
                                            'qte_impression' : qte_impression,

                                            'laize_pel': pel.laize_rouleau,
                                            'ml_pelliculage': nbr_ml_pelliuclage,
                                            'pelliculage_list_price': pel.list_price,
                                            'pelliculage_name': pel.name,
                                            'pelliculage_uom': pel.uom_id.id,
                                            'cout_pelliculage': cout_pelliuclage,
                                            'poses_machine': nbr_pose_machine,
                                            'poses_support': nbr_pose_support,
                                            'cout': cout,
                                            'nbr_feuille': nbr_feuille,
                                            'nbr_callage': nbr_callage,
                                            'nbr_insolation': nbr_insolation,
                                            'nbr_tirage': nbr_tirage,
                                            'compute': False,
                                            'printshop_id': self.id,
                                            'largeur_imp': largeur_imp_pince,
                                            'longueur_imp': longueur_imp_pince
                                            }
                                    cout = cout_papier + cout_tirage + cout_insolation + cout_calage + cout_pelliuclage
                                    line = self.env['offset.printshop.line'].create(line)

                                    if cout_minimal == 0: cout_minimal = cout
                                    if cout <= cout_minimal:
                                        cout_minimal = cout
                                        largeur_impression = largeur_imp
                                        longueur_impression = 0
                                        printshop.line_id = line.id

        self.generate_subproducts_inter_brochure(quantite, qte_impression)
        return True

        ##__________________

    def generate_subproducts_inter_brochure(self, quantite, qte_impression):
        # pool = pooler.get_pool(cr.dbname)
        # id_printshop = self.ids[0]
        # printshop = self.env['offset.printshop'].browse(id_printshop)
        printshop = self.env['offset.printshop'].browse(self.ids[0])
        support_line_inter = {'name': '[Print media inside] ' + str(printshop.line_id.support_name) + '\n'
                                      + "__________Print size : " + str(printshop.line_id.largeur_imp) + " * " + str(
            printshop.line_id.longueur_imp)
                                      + "__________Pnbr pose in sheet:" + str(
            printshop.line_id.poses_support) + "__________Pnbr pose in print:" + str(printshop.line_id.poses_machine)
                                      + "__________nbr passe en grande feuille: " + str(
            printshop.line_id.machine_id.nbr_passe * printshop.line_id.nbr_callage),
                              'product_id': printshop.line_id.support_id.id,
                              'product_qty': printshop.line_id.nbr_feuille + (
                                  printshop.line_id.machine_id.nbr_passe * printshop.line_id.nbr_callage),
                              'unit_price': printshop.line_id.support_list_price,
                              'constante': 0,
                              'matieres': True,
                              'workcenter': False,
                              # 'product_uom': printshop.line_id.support_id.uom_id.id,
                              'printshop_id': self.id}
        if not printshop.support_fournis:
            self.env['offset.printshop.subproduct'].create(support_line_inter)

        insolation_line = {'name': '[Plate insollation] ' + printshop.line_id.machine_id.insolation_id.name,
                           'product_id': printshop.line_id.machine_id.insolation_id.id,
                           'product_qty': printshop.line_id.nbr_insolation,
                           'unit_price': printshop.line_id.machine_id.insolation_id.list_price,
                           'product_uom': printshop.line_id.machine_id.insolation_id.uom_id.id,
                           'constante': 1,
                           'matieres': True,
                           'workcenter': False,

                           'printshop_id': self.id}
        self.env['offset.printshop.subproduct'].create(insolation_line)

        callage_line = {'name': '[Setting] ' + printshop.line_id.machine_id.calage_id.name,
                        'product_id': printshop.line_id.machine_id.calage_id.id,
                        'product_qty': printshop.line_id.nbr_callage,
                        'unit_price': printshop.line_id.machine_id.calage_id.list_price,
                        'product_uom': printshop.line_id.machine_id.calage_id.uom_id.id,
                        'constante': 1,
                        'matieres': False,
                        'workcenter': True,
                        'printshop_id': self.id}
        self.env['offset.printshop.subproduct'].create(callage_line)

        tirage_line = {'name': '[Print] ' + str(
            printshop.line_id.machine_id.print_id.name) + "__________Pnbr pose in print:" + str(
            printshop.line_id.poses_machine) + '\n',
                       'product_id': printshop.line_id.machine_id.print_id.id,
                       'product_qty': printshop.line_id.nbr_tirage,
                       'unit_price': printshop.line_id.machine_id.prix_tirage,
                       'product_uom': printshop.line_id.machine_id.print_id.uom_id.id,
                       'constante': 0,
                       'matieres': False,
                       'workcenter': True,
                       'printshop_id': self.id}
        self.env['offset.printshop.subproduct'].create(tirage_line)

        if printshop.type_pelliculage_inter:
            pelliculage_line = {'name': printshop.type_pelliculage_inter.name + '\n'
                                        + " ft: " + str(printshop.line_id.largeur_imp) + "*" + str(
                printshop.line_id.longueur_imp) + " ________nbr face:" + str(printshop.nbr_pelliculage) + '\n'
                                        + "  qte  feuilles: " + str(
                printshop.line_id.qte_impression ) + " feuilles",
                                'product_id': printshop.line_id.pelliculage2_id.id,
                                'product_qty': int(
                                    printshop.line_id.ml_pelliculage) + 1,
                                # 'product_qty' : int(printshop.nbr_pelliculage)*(printshop.quantite*108/100)*(printshop.largeur/100)*(printshop.longueur/100),
                                'unit_price': printshop.line_id.pelliculage_list_price,
                                # 'product_uom': printshop.line_id.pelliculage_uom,
                                # 'finition_pel': 'name',
                                'constante': 0,
                                'matieres': True,
                                'workcenter': False,
                                'printshop_id': self.id}
            self.env['offset.printshop.subproduct'].create(pelliculage_line)

        if printshop.serigraphie_id_inter:
            serigraphie_line_inter = {'name': printshop.serigraphie_id_inter.name + '\n'
                                              + " ft: " + str(printshop.line_id.largeur_imp + 1) + "*" + str(
                printshop.line_id.longueur_imp + 1) + " face:" + str(printshop.nbr_serigraphie_inter) + '\n'
                                              + "  qte : " + str(
                int(printshop.nbr_serigraphie_inter) * (printshop.quantite * 1.10 / printshop.line_id.poses_machine) * (
                    (printshop.line_id.largeur_imp + 1) / 100) * ((printshop.line_id.longueur_imp + 1) / 100)) + " m2",
                                      'product_id': printshop.serigraphie_id_inter.id,
                                      'product_qty': int(printshop.nbr_serigraphie_inter) * (
                                          printshop.quantite * 1.10 / printshop.line_id.poses_machine),
                                      # 'product_qty' : int(printshop.nbr_pelliculage)*(printshop.quantite*108/100)*(printshop.largeur/100)*(printshop.longueur/100),
                                      'unit_price': printshop.serigraphie_id_inter.list_price,
                                      'product_uom': printshop.serigraphie_id_inter.uom_id.id,
                                      'constante': 0,
                                      'matieres': False,
                                      'workcenter': True,
                                      # 'finition_pel': 'name',
                                      'printshop_id': self.id}
            self.env['offset.printshop.subproduct'].create(serigraphie_line_inter)

        if printshop.pliage_id_inter:
            pliage_line = {'name': '[Folding] ' + printshop.pliage_id_inter.name,
                           'product_id': printshop.pliage_id_inter.id,
                           'product_qty': quantite,
                           'unit_price': printshop.pliage_id_inter.list_price,
                           'product_uom': printshop.pliage_id_inter.uom_id.id,
                           'constante': 0,
                           'matieres': False,
                           'workcenter': True,
                           'printshop_id': self.id}
            self.env['offset.printshop.subproduct'].create(pliage_line)

        if printshop.decoupe_id_inter:
            decoupe_line = {'name': '[Cutting] ' + printshop.decoupe_id_inter.name,
                            'product_id': printshop.decoupe_id_inter.id,
                            'product_qty': quantite / printshop.poses_forme,
                            'unit_price': printshop.decoupe_id_inter.list_price,
                            'product_uom': printshop.decoupe_id_inter.uom_id.id,
                            'constante': 0,
                            'matieres': False,
                            'workcenter': True,
                            'printshop_id': self.id}
            self.env['offset.printshop.subproduct'].create(decoupe_line)

        if printshop.form_decoupe_id_inter:
            form_decoupe_line_inter = {'name': '[clichet] ' + printshop.form_decoupe_id_inter.name,
                                       'product_id': printshop.form_decoupe_id_inter.id,
                                       'product_qty': 1,
                                       'unit_price': printshop.form_decoupe_id_inter.list_price,
                                       'product_uom': printshop.form_decoupe_id_inter.uom_id.id,
                                       'constante': 1,
                                       'matieres': True,
                                       'workcenter': False,
                                       'printshop_id': self.id}
            self.env['offset.printshop.subproduct'].create(form_decoupe_line_inter)

        if printshop.clichet_vernis_inter:
            form_decoupe_line_inter = {'name': '[Varnish] ' + printshop.clichet_vernis_inter.name,
                                       'product_id': printshop.clichet_vernis_inter.id,
                                       'product_qty': 1,
                                       'unit_price': printshop.clichet_vernis_inter.list_price,
                                       'product_uom': printshop.clichet_vernis_inter.uom_id.id,
                                       'constante': 1,
                                       'matieres': True,
                                       'workcenter': False,
                                       'printshop_id': self.id}
            self.env['offset.printshop.subproduct'].create(form_decoupe_line_inter)

        compteur = 0
        for e in printshop.line_ids:
            compteur += 1
        description = '''Machine : %s
    Support : %s0,00
    Combinaisons possibles : %s
                        ''' % (
            printshop.line_id.machine_id.print_id.name, printshop.line_id.support_id.name, str(compteur))

        self.write({'description': description, })
        pell = '-Pelliculage : ' + str(printshop.nbr_pelliculage) + ' faces de type ' + str(
            printshop.pelliculage_id.name) + '\n'
        if printshop.nbr_pelliculage == False: pell = ''  # pelliculage
        pellinter = '-Pelliculage : ' + str(printshop.nbr_pelliculage_inter) + ' faces de type ' + str(
            printshop.pelliculage_id_inter) + '\n'
        if printshop.nbr_pelliculage_inter == '0': pellinter = ''  # pelliculage
        deco = '-Découpe : ' + str(printshop.form_decoupe_id.name) + '\n'
        if printshop.form_decoupe_id.name == False: deco = ''  # découpe
        pli = '-Pliage : ' + str(printshop.pliage_id.name) + '\n'
        if printshop.pliage_id.name == False: pli = ''  # pliage
        coll = '-Collage : ' + str(printshop.collage_id.name) + '\n'
        if printshop.collage_id.name == False: coll = ''  # collage
        ver = '-Vernis : ' + str(printshop.clichet_vernis.id) + '\n'
        if printshop.clichet_vernis.id == False: ver = ''  # vernie
        plaqu = '   Assemblage :' + '\n' + '-Piquage : ' + str(printshop.piquage_id.name) + '\n'
        if printshop.piquage_id.name == False: plaqu = ''
        spir = '   Assemblage :' + '\n' + '-Spirale : ' + str(printshop.nbr_spirale) + ' Boucles' + '\n'
        if printshop.nbr_spirale == False: spir = ''
        self.write({'desc_ventes': 'Article n°:' + str(printshop.name) + '\n' +
                                   str(printshop.imprime) + '\n' +
                                   ' __Cover : ' + '\n' +
                                   '   Open size : ' + str(printshop.largeur) + ' x ' + str(printshop.longueur) + '\n' +
                                   '   Size : ' + str(printshop.largeur_ferme) + ' x ' + str(
            printshop.longueur_ferme) + '\n' +
                                   '   Print : ' + str(printshop.nbr_coul_recto) + ' recto, ' + str(
            printshop.nbr_coul_verso) + ' verso.' + '\n' +
                                   '   Print Media : ' + str(printshop.support_id.name) + ' ' + ' gr,' + '\n'
                                   + str(pell)
                                   + str(deco)
                                   + str(pli)
                                   + str(coll)
                                   + str(ver)
                                   + '\n' +
                                   ' __Inside : ' + str(
            int(float(printshop.nbr_pages_brochure))) + ' pages hors couverture' + '\n' +
                                   '   Open size : ' + str(printshop.largeur_inter) + ' x ' + str(
            printshop.longueur_inter) + '\n' +
                                   '   Size : ' + str(printshop.largeur_ferme_inter) + ' x ' + str(
            printshop.longueur_ferme_inter) + '\n' +
                                   '   Print : ' + str(printshop.nbr_coul_r_v) + ' recto,verso ' + '\n' +
                                   '   Print Media : ' + str(printshop.support_id_inter.name) + ' ' + ' gr,' + '\n'
                                   + str(pellinter)
                                   + str(coll)
                                   + str(ver)
                                   + str(plaqu)
                                   + str(spir)
                       , })

    ##__________________



    # calcul sac
    def compute_sac(self, force=False, quantite=None):
        # pool = pooler.get_pool(cr.dbname)
        # id_printshop = self.ids[0]
        printshop = self.env['offset.printshop'].browse(self.ids)
        longueur = printshop.hauteur + printshop.soufflet + 4
        largeur = printshop.largeur_sac + printshop.soufflet + 2
        largeur_ouvert = largeur * 2
        self.write({'largeur': largeur_ouvert, 'longueur': longueur})
        longueur = printshop.hauteur + printshop.soufflet + 4
        largeur = printshop.largeur_sac + printshop.soufflet + 2
        largeur_ouvert = largeur * 2
        nbr_face = float(printshop.nbr_pages)
        nbr_coul_recto = float(printshop.nbr_coul_recto)
        nbr_coul_verso = float(printshop.nbr_coul_verso)
        nbr_pelliculage = float(printshop.nbr_pelliculage)
        line = {}
        sql = '''
        DELETE from offset_printshop_subproduct where printshop_id = %s
        '''
        self.env.cr.execute(sql, (printshop.id,))
        if not force:
            sql = '''
            DELETE from offset_printshop_line where printshop_id = %s
            '''
            self.env.cr.execute(sql, (printshop.id,))
            cout_minimal = 0
            # self.compute_contre_collage ( ids, context={'support_collage':True},force=False): False
            if printshop.contrecollage == 1:
                self.compute_contre_collage()
            for m in printshop.machine_ids:
                if nbr_coul_recto > m.nbr_coul_mach * 2:
                    continue

                nbr_pose_machine = 0
                largeur_imp = 0
                longueur_imp = 0
                largeur_imp_pince = 0
                longueur_imp_pince = 0
                qte_impression = 0
                if int(m.larg_mach / largeur) * int(m.long_mach / longueur) > int(m.long_mach / largeur) * int(
                                m.larg_mach / longueur):
                    nbr_pose_machine = int(m.larg_mach / largeur) * int(m.long_mach / longueur)
                    largeur_imp = largeur * int(m.larg_mach / largeur)
                    longueur_imp = longueur * int(m.long_mach / longueur)
                else:
                    nbr_pose_machine = int(m.long_mach / largeur) * int(m.larg_mach / longueur)
                    largeur_imp = largeur * int(m.long_mach / largeur)
                    longueur_imp = longueur * int(m.larg_mach / longueur)
                if largeur_imp < longueur_imp:
                    largeur_imp_pince = largeur_imp + m.prise_pince
                    longueur_imp_pince = longueur_imp
                else:
                    largeur_imp_pince = largeur_imp
                    longueur_imp_pince = longueur_imp + m.prise_pince
                if not nbr_pose_machine: continue
                qte_impression = (quantite / nbr_pose_machine) * nbr_face

                npm = []
                while nbr_pose_machine >= 1:
                    npm.append(nbr_pose_machine)
                    nbr_pose_machine -= 1
                for nbr_pose_machine in npm:
                    if nbr_pose_machine == int(m.larg_mach / largeur) * int(m.long_mach / longueur):
                        largeur_imp = largeur * int(m.larg_mach / largeur)
                        longueur_imp = longueur * int(m.long_mach / longueur)
                        if largeur_imp < longueur_imp:
                            largeur_imp_pince = largeur_imp + m.prise_pince
                            longueur_imp_pince = longueur_imp
                        else:
                            largeur_imp_pince = largeur_imp
                            longueur_imp_pince = longueur_imp + m.prise_pince
                    elif nbr_pose_machine == int(m.long_mach / largeur) * int(m.larg_mach / longueur):
                        largeur_imp = largeur * int(m.long_mach / largeur)
                        longueur_imp = longueur * int(m.larg_mach / longueur)
                        if largeur_imp < longueur_imp:
                            largeur_imp_pince = largeur_imp + m.prise_pince
                            longueur_imp_pince = longueur_imp
                        else:
                            largeur_imp_pince = largeur_imp
                            longueur_imp_pince = longueur_imp + m.prise_pince
                    # if not nbr_pose_machine == int(m.larg_mach / largeur) * int(m.long_mach / longueur) : continue
                    for s in printshop.support_id.line_ids2:
                        nbr_pose_support = 0
                        nbr_feuille = 0
                        nbr_callage = 0
                        nbr_insolation = 0
                        nbr_tirage = 0
                        if int(s.largeur_support / largeur_imp_pince) * int(
                                        s.longueur_support / longueur_imp_pince) > int(
                                    s.largeur_support / longueur_imp_pince) * int(
                                    s.longueur_support / largeur_imp_pince):
                            nbr_pose_support = int(s.largeur_support / largeur_imp_pince) * int(
                                s.longueur_support / longueur_imp_pince)
                        else:
                            nbr_pose_support = int(s.largeur_support / longueur_imp_pince) * int(
                                s.longueur_support / largeur_imp_pince)
                        if nbr_pose_support:
                            if nbr_pose_machine % 2 == 0:
                                nbr_callage = int((((nbr_coul_recto) / m.nbr_coul_mach)) + 0.75)
                                nbr_insolation = nbr_coul_recto
                            else:
                                nbr_callage = int(((nbr_coul_recto + nbr_coul_verso) / m.nbr_coul_mach) + 0.75)
                                nbr_insolation = (nbr_coul_recto + nbr_coul_verso)

                            nbr_tirage = int(((quantite / nbr_pose_machine) * nbr_face) * nbr_callage) + 1

                            nbr_feuille = int((quantite / nbr_pose_machine) / nbr_pose_support) + int(m.nbr_passe)

                            cout_papier = nbr_feuille * s.list_price
                            cout_tirage = nbr_tirage * m.print_id.list_price
                            cout_insolation = nbr_insolation * m.insolation_id.list_price
                            cout_calage = nbr_callage * m.calage_id.list_price
                            cout = cout_papier + cout_tirage + cout_insolation + cout_calage
                            line = {'name': m.name + ' ' + s.name,
                                    'machine_id': m.id,
                                    'support_id': s.id,
                                    'support_name': s.name,
                                    'support_uom': s.uom_id.id,

                                    'poses_machine': nbr_pose_machine,
                                    'poses_support': nbr_pose_support,
                                    'cout': cout,
                                    'nbr_feuille': nbr_feuille,
                                    'nbr_callage': nbr_callage,
                                    'nbr_insolation': nbr_insolation,
                                    'nbr_tirage': nbr_tirage,
                                    'compute': False,
                                    'printshop_id': self.id,
                                    'largeur_imp': largeur_imp_pince,
                                    'longueur_imp': longueur_imp_pince
                                    }
                            # self.env['offset.printshop.line'].create(line)
                            line = self.env['offset.printshop.line'].create(line)
                            if cout_minimal == 0: cout_minimal = cout
                            if cout <= cout_minimal:
                                cout_minimal = cout
                                largeur_impression = largeur_imp
                                longueur_impression = 0
                                printshop.line_id = line.id
        self.generate_subproducts(quantite, qte_impression)
        return True

        # calcul boite

    def compute_boite(self, force=False):
        # pool = pooler.get_pool(cr.dbname)
        id_printshop = self.ids[0]
        printshop = self.env['offset.printshop'].browse(id_printshop)
        longueur = ((printshop.hauteur_boite + printshop.profondeur_boite) * 2) + 1
        largeur = printshop.largeur_boite + (printshop.profondeur_boite * 2)
        self.write({'largeur': largeur, 'longueur': longueur})
        fond_perdu = printshop.fond_perdu
        quantite = printshop.quantite * printshop.tolerance
        # ajout ligne en bas
        nbr_face = float(printshop.nbr_pages)
        nbr_coul_recto = float(printshop.nbr_coul_recto)
        nbr_coul_verso = float(printshop.nbr_coul_verso)
        nbr_pelliculage = float(printshop.nbr_pelliculage)
        line = {}
        sql = '''
        DELETE from offset_printshop_subproduct where printshop_id = %s
        '''
        self.env.cr.execute(sql, (printshop.id,))
        if not force:
            sql = '''
            DELETE from offset_printshop_line where printshop_id = %s
            '''
            self.env.cr.execute(sql, (printshop.id,))
            cout_minimal = 0
            # self.compute_contre_collage ( ids, context={'support_collage':True},force=False): False
            if printshop.contrecollage == 1:
                self.compute_contre_collage()
            for m in printshop.machine_ids:
                if nbr_coul_recto > m.nbr_coul_mach * 2:
                    continue

                nbr_pose_machine = 0
                largeur_imp = 0
                longueur_imp = 0
                largeur_imp_pince = 0
                longueur_imp_pince = 0
                qte_impression = 0
                if int(m.larg_mach / largeur) * int(m.long_mach / longueur) > int(m.long_mach / largeur) * int(
                                m.larg_mach / longueur):
                    nbr_pose_machine = int(m.larg_mach / largeur) * int(m.long_mach / longueur)
                    largeur_imp = largeur * int(m.larg_mach / largeur)
                    longueur_imp = longueur * int(m.long_mach / longueur)
                else:
                    nbr_pose_machine = int(m.long_mach / largeur) * int(m.larg_mach / longueur)
                    largeur_imp = largeur * int(m.long_mach / largeur)
                    longueur_imp = longueur * int(m.larg_mach / longueur)
                if largeur_imp < longueur_imp:
                    largeur_imp_pince = largeur_imp + m.prise_pince
                    longueur_imp_pince = longueur_imp
                else:
                    largeur_imp_pince = largeur_imp
                    longueur_imp_pince = longueur_imp + m.prise_pince
                if not nbr_pose_machine: continue
                qte_impression = (quantite / nbr_pose_machine) * nbr_face

                npm = []
                while nbr_pose_machine >= 1:
                    npm.append(nbr_pose_machine)
                    nbr_pose_machine -= 1
                for nbr_pose_machine in npm:
                    if nbr_pose_machine == int(m.larg_mach / largeur) * int(m.long_mach / longueur):
                        largeur_imp = largeur * int(m.larg_mach / largeur)
                        longueur_imp = longueur * int(m.long_mach / longueur)
                        if largeur_imp < longueur_imp:
                            largeur_imp_pince = largeur_imp + m.prise_pince
                            longueur_imp_pince = longueur_imp
                        else:
                            largeur_imp_pince = largeur_imp
                            longueur_imp_pince = longueur_imp + m.prise_pince
                    elif nbr_pose_machine == int(m.long_mach / largeur) * int(m.larg_mach / longueur):
                        largeur_imp = largeur * int(m.long_mach / largeur)
                        longueur_imp = longueur * int(m.larg_mach / longueur)
                        if largeur_imp < longueur_imp:
                            largeur_imp_pince = largeur_imp + m.prise_pince
                            longueur_imp_pince = longueur_imp
                        else:
                            largeur_imp_pince = largeur_imp
                            longueur_imp_pince = longueur_imp + m.prise_pince
                    # if not nbr_pose_machine == int(m.larg_mach / largeur) * int(m.long_mach / longueur) : continue
                    for s in printshop.support_id.line_ids2:
                        nbr_pose_support = 0
                        nbr_feuille = 0
                        nbr_callage = 0
                        nbr_insolation = 0
                        nbr_tirage = 0
                        if int(s.largeur_support / largeur_imp_pince) * int(
                                        s.longueur_support / longueur_imp_pince) > int(
                                    s.largeur_support / longueur_imp_pince) * int(
                                    s.longueur_support / largeur_imp_pince):
                            nbr_pose_support = int(s.largeur_support / largeur_imp_pince) * int(
                                s.longueur_support / longueur_imp_pince)
                        else:
                            nbr_pose_support = int(s.largeur_support / longueur_imp_pince) * int(
                                s.longueur_support / largeur_imp_pince)
                        if nbr_pose_support:
                            if nbr_pose_machine % 2 == 0:
                                nbr_callage = int((((nbr_coul_recto) / m.nbr_coul_mach)) + 0.75)
                                nbr_insolation = nbr_coul_recto
                            else:
                                nbr_callage = int(((nbr_coul_recto + nbr_coul_verso) / m.nbr_coul_mach) + 0.75)
                                nbr_insolation = (nbr_coul_recto + nbr_coul_verso)

                            nbr_tirage = int(((quantite / nbr_pose_machine) * nbr_face) * nbr_callage) + 1

                            nbr_feuille = int((quantite / nbr_pose_machine) / nbr_pose_support) + int(m.nbr_passe)

                            cout_papier = nbr_feuille * s.list_price
                            cout_tirage = nbr_tirage * m.print_id.list_price
                            cout_insolation = nbr_insolation * m.insolation_id.list_price
                            cout_calage = nbr_callage * m.calage_id.list_price
                            cout = cout_papier + cout_tirage + cout_insolation + cout_calage
                            line = {'name': m.name + ' ' + s.name,
                                    'machine_id': m.id,
                                    'support_id': s.id,
                                    'support_name': s.name,
                                    'support_uom': s.uom_id.id,

                                    'poses_machine': nbr_pose_machine,
                                    'poses_support': nbr_pose_support,
                                    'cout': cout,
                                    'nbr_feuille': nbr_feuille,
                                    'nbr_callage': nbr_callage,
                                    'nbr_insolation': nbr_insolation,
                                    'nbr_tirage': nbr_tirage,
                                    'compute': False,
                                    'printshop_id': self.id,
                                    'largeur_imp': largeur_imp_pince,
                                    'longueur_imp': longueur_imp_pince
                                    }
                            # self.env['offset.printshop.line'].create(line)
                            line = self.env['offset.printshop.line'].create(line)
                            if cout_minimal == 0: cout_minimal = cout
                            if cout <= cout_minimal:
                                cout_minimal = cout
                                largeur_impression = largeur_imp
                                longueur_impression = 0
                                printshop.line_id = line.id
        self.generate_subproducts(quantite, qte_impression)
        return True

    def generate_subproducts(self, quantite, qte_impression):

        printshop = self.env['offset.printshop'].browse(self.ids[0])

        support_line = {'name': '[Print media] ' + str(printshop.line_id.support_name) + '\n'
                                + "__________Print size : " + str(printshop.line_id.largeur_imp) + " * " + str(
            printshop.line_id.longueur_imp)
                                + "__________Pnbr pose in sheet:" + str(
            printshop.line_id.poses_support) + "__________Pnbr pose in print:" + str(printshop.line_id.poses_machine)
                                + "__________nbr passe en grande feuille: " + str(
            printshop.line_id.machine_id.nbr_passe * printshop.line_id.nbr_callage),
                        'product_id': printshop.line_id.support_id.id,
                        'product_qty': printshop.line_id.nbr_feuille + (
                            printshop.line_id.machine_id.nbr_passe * printshop.line_id.nbr_callage),
                        'unit_price': printshop.line_id.support_list_price,
                        'constante': 0,
                        'matieres': True,
                        'workcenter': False,
                        # 'product_uom': self.product_id.uom_id.id,
                        'printshop_id': self.id}
        if not printshop.support_fournis:
            self.env['offset.printshop.subproduct'].create(support_line)

        insolation_line = {'name': '[Plate insollation] ' + printshop.line_id.machine_id.insolation_id.name,
                           'product_id': printshop.line_id.machine_id.insolation_id.id,
                           'product_qty': printshop.line_id.nbr_insolation,
                           'unit_price': printshop.line_id.machine_id.insolation_id.list_price,
                           'product_uom': printshop.line_id.machine_id.insolation_id.uom_id.id,
                           'constante': 1,
                           'matieres': True,
                           'workcenter': False,

                           'printshop_id': self.id}
        if printshop.line_id.machine_id.insolation_id:
            self.env['offset.printshop.subproduct'].create(insolation_line)

        callage_line = {'name': '[Setting] ' + printshop.line_id.machine_id.calage_id.name,
                        'product_id': printshop.line_id.machine_id.calage_id.id,
                        'product_qty': printshop.line_id.nbr_callage,
                        'unit_price': printshop.line_id.machine_id.calage_id.list_price,
                        'product_uom': printshop.line_id.machine_id.calage_id.uom_id.id,
                        'constante': 1,
                        'matieres': False,
                        'workcenter': True,
                        'printshop_id': self.id}
        if printshop.line_id.machine_id.calage_id:
            self.env['offset.printshop.subproduct'].create(callage_line)

        tirage_line = {'name': '[Print] ' + str(
            printshop.line_id.machine_id.print_id.name) + "__________Pnbr pose in print:" + str(
            printshop.line_id.poses_machine) + '\n',
                       'product_id': printshop.line_id.machine_id.print_id.id,
                       'product_qty': printshop.line_id.nbr_tirage,
                       'unit_price': printshop.line_id.machine_id.prix_tirage,
                       'product_uom': printshop.line_id.machine_id.print_id.uom_id.id,
                       'minimum_price': printshop.line_id.machine_id.mini_cost_tirage,
                       'constante': 0,
                       'matieres': False,
                       'workcenter': True,
                       'printshop_id': self.id}
        self.env['offset.printshop.subproduct'].create(tirage_line)

        if printshop.type_pelliculage:
            pelliculage_line = {'name': printshop.type_pelliculage.name + '\n'
                                        + " ft: " + str(printshop.line_id.largeur_imp) + "*" + str(
                printshop.line_id.longueur_imp) + " ________nbr face:" + str(printshop.nbr_pelliculage) + '\n'
                                        + "  qte  feuilles: " + str(
                printshop.line_id.qte_impression) + " feuilles",
                                'product_id': printshop.line_id.pelliculage2_id.id,
                                'product_qty': int(
                                    printshop.line_id.ml_pelliculage) + 1,
                                # 'product_qty' : int(printshop.nbr_pelliculage)*(printshop.quantite*108/100)*(printshop.largeur/100)*(printshop.longueur/100),
                                'unit_price': printshop.line_id.pelliculage_list_price,
                                # 'product_uom': printshop.line_id.pelliculage_uom,
                                # 'finition_pel': 'name',
                                'constante': 0,
                                'matieres': True,
                                'workcenter': False,
                                'printshop_id': self.id}
            self.env['offset.printshop.subproduct'].create(pelliculage_line)

        if printshop.serigraphie_id:
            serigraphie_line = {'name': printshop.serigraphie_id.name + '\n'
                                        + " ft: " + str(printshop.line_id.largeur_imp + 1) + "*" + str(
                printshop.line_id.longueur_imp + 1) + " face:" + str(printshop.nbr_serigraphie) + '\n'
                                        + "  qte : " + str(
                int(printshop.nbr_serigraphie) * (printshop.quantite * 1.10 / printshop.line_id.poses_machine) * (
                    (printshop.line_id.largeur_imp + 1) / 100) * ((printshop.line_id.longueur_imp + 1) / 100)) + " m2",
                                'product_id': printshop.serigraphie_id.id,
                                'product_qty': int(printshop.nbr_serigraphie) * (
                                    printshop.line_id.nbr_feuille),
                                # 'product_qty' : int(printshop.nbr_pelliculage)*(printshop.quantite*108/100)*(printshop.largeur/100)*(printshop.longueur/100),
                                'unit_price': printshop.serigraphie_id.list_price,
                                'product_uom': printshop.serigraphie_id.uom_id.id,
                                'constante': 0,
                                'matieres': False,
                                'workcenter': True,
                                # 'finition_pel': 'name',
                                'printshop_id': self.id}
            self.env['offset.printshop.subproduct'].create(serigraphie_line)

        if printshop.spirale_id:
            spirale_line = {'name': '[Spirale] ' + printshop.spirale_id.name,
                            'product_id': printshop.spirale_id.id,
                            'product_qty': printshop.nbr_spirale * quantite,
                            'unit_price': printshop.spirale_id.list_price,
                            'product_uom': printshop.spirale_id.uom_id.id,
                            'constante': 0,
                            'matieres': True,
                            'workcenter': False,
                            'printshop_id': self.id}
            self.env['offset.printshop.subproduct'].create(spirale_line)

        if printshop.piquage_id:
            piquage_line = {'name': '[Piquage] ' + printshop.piquage_id.name,
                            'product_id': printshop.piquage_id.id,
                            'product_qty': quantite,
                            'unit_price': printshop.piquage_id.list_price,
                            'product_uom': printshop.piquage_id.uom_id.id,
                            'constante': 0,
                            'matieres': False,
                            'workcenter': True,
                            'printshop_id': self.id}
            self.env['offset.printshop.subproduct'].create(piquage_line)

        if printshop.pliage_id:
            pliage_line = {'name': '[Folding] ' + printshop.pliage_id.name,
                           'product_id': printshop.pliage_id.id,
                           'product_qty': quantite,
                           'unit_price': printshop.pliage_id.list_price,
                           'product_uom': printshop.pliage_id.uom_id.id,
                           'constante': 0,
                           'matieres': False,
                           'workcenter': True,
                           'printshop_id': self.id}
            self.env['offset.printshop.subproduct'].create(pliage_line)

        if printshop.collage_id:
            collage_line = {'name': '[Glue] ' + printshop.collage_id.name,
                            'product_id': printshop.collage_id.id,
                            'product_qty': quantite,
                            'unit_price': printshop.collage_id.list_price,
                            'product_uom': printshop.collage_id.uom_id.id,
                            'constante': 0,
                            'matieres': False,
                            'workcenter': True,
                            'printshop_id': self.id}
            self.env['offset.printshop.subproduct'].create(collage_line)

        if printshop.decoupe_id:
            decoupe_line = {'name': '[Cutting] ' + printshop.decoupe_id.name,
                            'product_id': printshop.decoupe_id.id,
                            'product_qty': quantite / printshop.poses_forme,
                            'unit_price': printshop.decoupe_id.list_price,
                            'product_uom': printshop.decoupe_id.uom_id.id,
                            'constante': 0,
                            'matieres': False,
                            'workcenter': True,
                            'printshop_id': self.id}
            self.env['offset.printshop.subproduct'].create(decoupe_line)

        if printshop.form_decoupe_id:
            form_decoupe_line = {'name': '[clichet] ' + printshop.form_decoupe_id.name,
                                 'product_id': printshop.form_decoupe_id.id,
                                 'product_qty': 1,
                                 'unit_price': printshop.form_decoupe_id.list_price,
                                 'product_uom': printshop.form_decoupe_id.uom_id.id,
                                 'constante': 1,
                                 'matieres': True,
                                 'workcenter': False,
                                 'printshop_id': self.id}
            self.env['offset.printshop.subproduct'].create(form_decoupe_line)

        if printshop.clichet_vernis:
            form_decoupe_line = {'name': '[Varnish] ' + printshop.clichet_vernis.name,
                                 'product_id': printshop.clichet_vernis.id,
                                 'product_qty': 1,
                                 'unit_price': printshop.clichet_vernis.list_price,
                                 'product_uom': printshop.clichet_vernis.uom_id.id,
                                 'constante': 1,
                                 'matieres': True,
                                 'workcenter': False,
                                 'printshop_id': self.id}
            self.env['offset.printshop.subproduct'].create(form_decoupe_line)

        if printshop.accessoires_ids:
            for line in printshop.accessoires_ids:
                accessoires_line = {'name': '[accessoires] ' + line.product_id.name,
                                    'product_id': line.product_id.id,
                                    'product_qty': quantite * line.quantite,
                                    'unit_price': line.prix,
                                    'matieres': True,
                                    'product_uom': line.product_id.uom_id.id,
                                    'constante': 0,
                                    'matieres': True,
                                    'workcenter': False,
                                    'printshop_id': self.id}
                self.env['offset.printshop.subproduct'].create(accessoires_line)

        if printshop.emballage_id:
            emballage_id_line = {'name': '[Boite carton] ' + printshop.emballage_id.name,
                                 'product_id': printshop.emballage_id.id,
                                 'product_qty': quantite / printshop.qte_emballage,
                                 'unit_price': printshop.emballage_id.list_price,
                                 'product_uom': printshop.emballage_id.uom_id.id,
                                 'constante': 0,
                                 'matieres': True,
                                 'workcenter': False,
                                 'printshop_id': self.id}
            self.env['offset.printshop.subproduct'].create(emballage_id_line)

        compteur = 0
        for e in printshop.line_ids:
            compteur += 1
        description = '''Machine : %s
        Support : %s0,00
        Combinaisons possibles : %s
                            ''' % (
            printshop.line_id.machine_id.print_id.name, printshop.line_id.support_id.name, str(compteur))

        self.write({'description': description, })
        pell = '-Coating : ' + str(printshop.nbr_pelliculage) + ' Faces ' + str(
            printshop.pelliculage_id) + '\n'
        if printshop.nbr_pelliculage == '0':
            pell = ''  # pelliculage
        if not printshop.nbr_pelliculage == '0':
            pell = '-Coating : ' + str(printshop.nbr_pelliculage) + ' Faces ' + str(
                printshop.pelliculage_id.name) + '\n'

        pellinter = '-Coating : ' + str(printshop.nbr_pelliculage_inter) + ' faces ' + str(
            printshop.pelliculage_id_inter) + '\n'
        if printshop.nbr_pelliculage_inter == '0': pellinter = ''  # pelliculage
        deco = '-Cutting : ' + str(printshop.form_decoupe_id.name) + '\n'
        if printshop.form_decoupe_id.name == None: deco = ''  # découpe
        pli = '-Folding : ' + str(printshop.pliage_id.name) + '\n'
        if printshop.pliage_id.name == None: pli = ''  # pliage
        coll = '-Gulling : ' + str(printshop.collage_id.name) + '\n'
        if printshop.collage_id.name == None: coll = ''  # collage
        ver = '-Varnish : ' + str(printshop.clichet_vernis.id) + '\n'
        if printshop.clichet_vernis.id == False: ver = ''  # vernie
        plaqu = '   Assemblage :' + '\n' + '-Piquage : ' + str(printshop.piquage_id.name) + '\n'
        if printshop.piquage_id.name == None: plaqu = ''
        spir = '   Assemblage :' + '\n' + '-Spirale : ' + str(printshop.nbr_spirale) + ' Boucles' + '\n'
        if printshop.nbr_spirale == 0.0: spir = ''

        self.write({'desc_ventes': 'Product_quote n°:' + str(printshop.name) + '\n' +
                                   str(printshop.imprime) + '\n' +
                                   '   Open Size : ' + str(
            printshop.largeur) + ' x ' + str(printshop.longueur) + '\n' +
                                   '   Print : ' + str(
            printshop.nbr_coul_recto) + ' Front, ' + str(printshop.nbr_coul_verso) + ' Back.' + '\n' +
                                   '   SPrint Media : ' + str(
            printshop.support_id.name) + ' ' + ' gr,' + '\n'
                                   + str(pell)
                                   + str(deco)
                                   + str(pli)
                                   + str(coll)
                                   + str(ver)
                                   + str(plaqu)
                                   + str(spir) + '\n'

                       , })
        #######

    # for roll product
    def generate_subproducts_roll(self, quantite, qte_impression):

        printshop = self.env['offset.printshop'].browse(self.ids[0])
        support_line = {'name': '[Print media] ' + str(printshop.line_id.support_id.name) + '\n'
                                + "__________Print size : " + str(printshop.line_id.largeur_imp + 1) + " * " + str(
            printshop.line_id.longueur_imp + 1) + '\n'
                                + "__________Pnbr pose :" + str(printshop.line_id.poses_support) + '\n',
                        'product_id': printshop.line_id.support_id.id,
                        'product_qty': printshop.line_id.nbr_m2,
                        'unit_price': printshop.line_id.support_id.list_price,
                        'constante': 0,
                        'matieres': True,
                        'workcenter': False,
                        'product_uom': printshop.line_id.support_id.uom_id.id,
                        'printshop_id': self.id}
        if not printshop.support_fournis:
            self.env['offset.printshop.subproduct'].create(support_line)

        tirage_line = {'name': '[Print] ' + str(
            printshop.line_id.machine_id.print_id.name) + "__________Pnbr pose in print:" + str(
            printshop.line_id.poses_machine) + '\n',
                       'product_id': printshop.line_id.machine_id.print_id.id,
                       'product_qty': printshop.line_id.nbr_m2,
                       'unit_price': printshop.line_id.machine_id.print_id.list_price,
                       'product_uom': printshop.line_id.machine_id.print_id.uom_id.id,
                       'constante': 0,
                       'matieres': False,
                       'workcenter': True,
                       'printshop_id': self.id}
        self.env['offset.printshop.subproduct'].create(tirage_line)

        if printshop.pelliculage_id:
            pelliculage_line = {'name': printshop.pelliculage_id.name + '\n'
                                        + " ft: " + str(printshop.line_id.largeur_imp + 1) + "*" + str(
                printshop.line_id.longueur_imp + 1) + " nbr face:" + str(printshop.nbr_pelliculage) + '\n'
                                        + "  qte : " + str(
                int(printshop.nbr_pelliculage) * (printshop.quantite * 1.10 / printshop.line_id.poses_machine) * (
                    (printshop.line_id.largeur_imp + 1) / 100) * ((printshop.line_id.longueur_imp + 1) / 100)) + " m2",
                                'product_id': printshop.pelliculage_id.id,
                                'product_qty': int(printshop.nbr_pelliculage) * (
                                    printshop.quantite * 1.10 / printshop.line_id.poses_machine),
                                # 'product_qty' : int(printshop.nbr_pelliculage)*(printshop.quantite*108/100)*(printshop.largeur/100)*(printshop.longueur/100),
                                'unit_price': printshop.pelliculage_id.list_price * (
                                    (printshop.line_id.largeur_imp + 1) / 100) * (
                                                  (printshop.line_id.longueur_imp + 1) / 100),
                                'product_uom': printshop.pelliculage_id.uom_id.id,
                                # 'finition_pel': 'name',
                                'constante': 0,
                                'matieres': True,
                                'workcenter': False,
                                'printshop_id': self.id}
            self.env['offset.printshop.subproduct'].create(pelliculage_line)

        if printshop.serigraphie_id:
            serigraphie_line = {'name': printshop.serigraphie_id.name + '\n'
                                        + " ft: " + str(printshop.line_id.largeur_imp + 1) + "*" + str(
                printshop.line_id.longueur_imp + 1) + " face:" + str(printshop.nbr_serigraphie) + '\n'
                                        + "  qte : " + str(
                int(printshop.nbr_serigraphie) * (printshop.quantite * 1.10 / printshop.line_id.poses_machine) * (
                    (printshop.line_id.largeur_imp + 1) / 100) * ((printshop.line_id.longueur_imp + 1) / 100)) + " m2",
                                'product_id': printshop.serigraphie_id.id,
                                'product_qty': int(printshop.nbr_serigraphie) * (
                                    printshop.quantite * 1.10 / printshop.line_id.poses_machine),
                                # 'product_qty' : int(printshop.nbr_pelliculage)*(printshop.quantite*108/100)*(printshop.largeur/100)*(printshop.longueur/100),
                                'unit_price': printshop.serigraphie_id.list_price * (
                                    (printshop.line_id.largeur_imp + 1) / 100) * (
                                                  (printshop.line_id.longueur_imp + 1) / 100),
                                'product_uom': printshop.serigraphie_id.uom_id.id,
                                'constante': 0,
                                'matieres': False,
                                'workcenter': True,
                                # 'finition_pel': 'name',
                                'printshop_id': self.id}
            self.env['offset.printshop.subproduct'].create(serigraphie_line)

        if printshop.collage_id:
            collage_line = {'name': '[Glue] ' + printshop.collage_id.name,
                            'product_id': printshop.collage_id.id,
                            'product_qty': quantite,
                            'unit_price': printshop.collage_id.list_price,
                            'product_uom': printshop.collage_id.uom_id.id,
                            'constante': 0,
                            'matieres': False,
                            'workcenter': True,
                            'printshop_id': self.id}
            self.env['offset.printshop.subproduct'].create(collage_line)

        if printshop.decoupe_id:
            decoupe_line = {'name': '[Cutting] ' + printshop.decoupe_id.name,
                            'product_id': printshop.decoupe_id.id,
                            'product_qty': quantite / printshop.poses_forme,
                            'unit_price': printshop.decoupe_id.list_price,
                            'product_uom': printshop.decoupe_id.uom_id.id,
                            'constante': 0,
                            'matieres': False,
                            'workcenter': True,
                            'printshop_id': self.id}
            self.env['offset.printshop.subproduct'].create(decoupe_line)

        if printshop.form_decoupe_id:
            form_decoupe_line = {'name': '[clichet] ' + printshop.form_decoupe_id.name,
                                 'product_id': printshop.form_decoupe_id.id,
                                 'product_qty': 1,
                                 'unit_price': printshop.form_decoupe_id.list_price,
                                 'product_uom': printshop.form_decoupe_id.uom_id.id,
                                 'constante': 1,
                                 'matieres': True,
                                 'workcenter': False,
                                 'printshop_id': self.id}
            self.env['offset.printshop.subproduct'].create(form_decoupe_line)

        if printshop.clichet_vernis:
            form_decoupe_line = {'name': '[Varnish] ' + printshop.clichet_vernis.name,
                                 'product_id': printshop.clichet_vernis.id,
                                 'product_qty': 1,
                                 'unit_price': printshop.clichet_vernis.list_price,
                                 'product_uom': printshop.clichet_vernis.uom_id.id,
                                 'constante': 1,
                                 'matieres': True,
                                 'workcenter': False,
                                 'printshop_id': self.id}
            self.env['offset.printshop.subproduct'].create(form_decoupe_line)

        if printshop.accessoires_ids:
            for line in printshop.accessoires_ids:
                accessoires_line = {'name': '[accessoires] ' + printshop.accessoires_id.name,
                                    'product_id': printshop.accessoires_id.id,
                                    'product_qty': quantite * printshop.qte_accessoires,
                                    'unit_price': printshop.accessoires_id.list_price,
                                    'matieres': True,
                                    'product_uom': printshop.accessoires_id.uom_id.id,
                                    'constante': 0,
                                    'matieres': True,
                                    'workcenter': False,
                                    'printshop_id': self.id}
                self.env['offset.printshop.subproduct'].create(accessoires_line)

        if printshop.emballage_id:
            emballage_id_line = {'name': '[Boite carton] ' + printshop.emballage_id.name,
                                 'product_id': printshop.emballage_id.id,
                                 'product_qty': quantite / printshop.qte_emballage,
                                 'unit_price': printshop.emballage_id.list_price,
                                 'product_uom': printshop.emballage_id.uom_id.id,
                                 'constante': 0,
                                 'matieres': True,
                                 'workcenter': False,
                                 'printshop_id': self.id}
            self.env['offset.printshop.subproduct'].create(emballage_id_line)

        compteur = 0
        for e in printshop.line_ids:
            compteur += 1
        description = '''Machine : %s
        Support : %s0,00
        Combinaisons possibles : %s
                            ''' % (
            printshop.line_id.machine_id.print_id.name, printshop.line_id.support_id.name, str(compteur))

        self.write({'description': description, })

        self.write({'desc_ventes': 'Product_quote n°:' + str(printshop.name) + '\n' +
                                   str(printshop.imprime) + '\n' +
                                   '   Open Size : ' + str(
            printshop.largeur) + ' x ' + str(printshop.longueur) + '\n' +
                                   '   Print : ' + str(
            printshop.nbr_coul_recto) + '\n' +
                                   '   SPrint Media : ' + str(
            printshop.support_id.name) + ' ' + ' gr,' + '\n'

                       , })

    def generate_subproducts_collage(self, quantite):
        # pool = pooler.get_pool(cr.dbname)
        # id_printshop = self.ids[0]
        printshop = self.env['offset.printshop'].browse(self.ids[0])

        if printshop.support_id_rigide:
            support_contrecollage_line = {'name': '[Media] ' + str(printshop.line_id.support_id.name) + '\n'
                                                                                                        'Size :' + str(
                printshop.longueur_contrecollage) + ' * ' + str(printshop.largeur_contrecollage) + '  nbr pose' + str(
                printshop.line_id.poses_support),
                                          'product_id': printshop.line_id.support_id.id,
                                          'product_qty': printshop.line_id.nbr_feuille,
                                          'unit_price': printshop.line_id.support_id.list_price,
                                          'product_uom': printshop.line_id.support_id.uom_id.id,
                                          'constante': 0,
                                          'matieres': True,
                                          'workcenter': False,
                                          'printshop_id': self.ids[0]}
            self.env['offset.printshop.subproduct'].create(support_contrecollage_line)

        if printshop.contrecollage_id:
            contrecollage_line = {'name': '[collage] ' + printshop.contrecollage_id.name,
                                  'product_id': printshop.contrecollage_id.id,
                                  'product_qty': printshop.quantite * int(printshop.qte_contrecollage),
                                  'unit_price': printshop.contrecollage_id.list_price,
                                  'product_uom': printshop.contrecollage_id.uom_id.id,
                                  'constante': 0,
                                  'matieres': False,
                                  'workcenter': True,
                                  'printshop_id': self.ids[0]}
            self.env['offset.printshop.subproduct'].create(contrecollage_line)



            ########
            # Le calcul forcé  en cas de choix d'une combinaison précise

    def compute_force(self):
        # pool = pooler.get_pool(cr.dbname)
        id_printshop = self.ids[0]
        printshop = self.env['offset.printshop'].browse(id_printshop)

        for line in printshop.line_ids:
            if line.compute:
                self.write({'line_id': line.id})
        self.compute(force=True)
        return True


        # générer bom.........................................................................................................
        # génération de la nomenclature

    def generate_bom(self):
        # pool = pooler.get_pool(cr.dbname)
        # context = {}
        id_printshop = self.ids[0]
        printshop = self.env['offset.printshop'].browse(id_printshop)
        if not printshop.product_tmpl_id:
            raise UserError(_("Please attach product"))
        # -------------------------------------------------------------
        for q in printshop.Multiqty:

            self.write({'quantite': q.quantites})

            # self.compute( ids, context={},force=False)
            if printshop.type_offset == 'applat':
                self.compute(force=False)
            if printshop.type_offset == 'depliant':
                self.compute(force=False)
                self.write({'largeur_ferme': printshop.largeur / 2})
                self.write({'longueur_ferme': printshop.longueur})
            if printshop.type_offset == 'blocnote':
                self.compute_int_bloc(force=False)
                # self.compute(force=False)
            if printshop.type_offset == 'brochure':
                self.compute_int_brochure(force=False)
            if printshop.type_offset == 'sac':
                self.compute_sac(force=False)
            if printshop.type_offset == 'boite':
                self.compute_boite(force=False)

            workcenter = {'name': str(printshop.product_tmpl_id.name) + ' / ' + str(printshop.quantite)}
            work_id = self.env['mrp.routing'].create(workcenter)
            subw_ids = printshop.subproduct_ids.search([('workcenter', '=', True)])
            for line in printshop.subproduct_ids:
                if line.workcenter:
                    print 'line.product_id.work_id.id'
                    print line.product_id.work_id.id
                    workcenter_line = {'name': line.name,
                                       'workcenter_id': line.product_id.work_id.id,
                                       # 'sequence' : 1,
                                       # 'time_mode' : [manuel],
                                       'time_cycle_manuel': 1,
                                       'routing_id': work_id.id,
                                       'qty_printshop': line.product_qty
                                       }

                    self.env['mrp.routing.workcenter'].create(workcenter_line)

            bom = {'name': str(printshop.product_tmpl_id.name) + ' / ' + str(printshop.quantite),
                   'product_tmpl_id': printshop.product_tmpl_id.id,
                   'product_qty': printshop.quantite,
                   'product_uom': printshop.product_tmpl_id.uom_id.id,
                   'code': str(printshop.name) + '/' + str(printshop.quantite),
                   'routing_id': work_id.id
                   }
            bom_id = self.env['mrp.bom'].create(bom)
            subr_ids = printshop.subproduct_ids.search([('matieres', '=', True)])
            for line in printshop.subproduct_ids:  # ici on créer les sous produit................
                # const1=0
                # if "[Callage]" in line.name or "[Insolation]" in line.name or "[Clichet]" : const1 = 1
                bom_line = {'name': line.name,
                            'product_id': line.product_id.id,
                            'product_qty': line.product_qty,
                            'product_uom': line.product_uom.id,
                            'constante': line.product_id.constante,
                            'bom_id': bom_id.id,
                            'desc_tech': line.name
                            }
                if line.matieres:
                    self.env['mrp.bom.line'].create(bom_line)

            # self.env['offset.printshop'].write( ids[0], {'bom_id' : bom_id})

            self.write({'bom_id': bom_id.id})

        return True
        # ................................................................................................................................................

    def product_create(self):
        # pool = pooler.get_pool(cr.dbname)
        context = {}
        id_printshop = self.ids[0]
        printshop = self.env['offset.printshop'].browse(id_printshop)
        model = self.env['product.attribute']

        modeltype_id = model.search([('name', '=', 'type_product')])
        if not modeltype_id:
            self.env['product.attribute'].create({'name': 'type_product'})
            modeltype_id = model.search([('name', '=', 'type_product')])
        type = str(printshop.type_offset)
        type_id = self.env['product.attribute.value'].search([('name', 'like', type)])
        if not type_id:
            self.env['product.attribute.value'].create({'name': type, 'attribute_id': modeltype_id[0]})
            type_id = self.env['product.attribute.value'].search([('name', '=', type)])

        print type_id

        modelsize_id = model.search([('name', 'like', 'size')])
        if not modelsize_id:
            self.env['product.attribute'].create({'name': 'size'})
            modeltype_id = model.search([('name', '=', 'size')])
        size = str(printshop.largeur) + " * " + str(printshop.longueur)
        size_id = self.env['product.attribute.value'].search([('name', '=', size)])
        if not size_id:
            self.env['product.attribute.value'].create({'name': size, 'attribute_id': modelsize_id[0]})
            size_id = self.env['product.attribute.value'].search([('name', '=', size)])

        print size_id

        modelcolor_id = model.search([('name', 'like', 'color')])
        if not modelcolor_id:
            self.env['product.attribute'].create({'name': 'color'})
            modelcolor_id = model.search([('name', '=', 'color')])
        color = "Recto:" + str(printshop.nbr_coul_recto) + ", Verso: " + str(printshop.nbr_coul_verso)
        color_id = self.env['product.attribute.value'].search([('name', '=', color)])
        if not color_id:
            self.env['product.attribute.value'].create({'name': color, 'attribute_id': modelcolor_id[0]})
            color_id = self.env['product.attribute.value'].search([('name', '=', color)])

        modelpaper_id = model.search([('name', 'like', 'paper')])
        if not modelpaper_id:
            self.env['product.attribute'].create({'name': 'paper'})
            modelpaper_id = model.search([('name', '=', 'paper')])
        paper = str(printshop.support_id.name)
        paper_id = self.env['product.attribute.value'].search([('name', '=', paper)])
        if not paper_id:
            self.env['product.attribute.value'].create({'name': paper, 'attribute_id': modelpaper_id[0]})
            paper_id = self.env['product.attribute.value'].search([('name', '=', paper)])
        # if printshop.pelliculage_id :

        print paper_id

        modelprinter_id = model.search([('name', 'like', 'type_print')])
        if not modelprinter_id:
            self.env['product.attribute'].create({'name': 'type_print'})
            modelprinter_id = model.search([('name', '=', 'type_print')])
        printer = str(printshop.line_id.machine_id.print_id.name)
        printer_id = self.env['product.attribute.value'].search([('name', '=', printer)])
        if not printer_id:
            self.env['product.attribute.value'].create({'name': printer, 'attribute_id': modelprinter_id[0]})
            printer_id = self.env['product.attribute.value'].search([('name', '=', printer)])

        modelfinitions_id = model.search([('name', 'like', 'finitions')])
        if not modelfinitions_id:
            self.env['product.attribute'].create({'name': 'finitions'})
            modelfinitions_id = model.search([('name', '=', 'finitions')])
        finitions = str(printshop.pelliculage_id.name) + " " + str(printshop.nbr_pelliculage) + " ," + str(
            printshop.serigraphie_id.name)
        finitions_id = self.env['product.attribute.value'].search([('name', '=', finitions)])
        if not finitions_id:
            self.env['product.attribute.value'].create({'name': finitions, 'attribute_id': modelfinitions_id[0]})
            finitions_id = self.env['product.attribute.value'].search([('name', '=', finitions)])
        # if printshop.pelliculage_id :

        print finitions_id

        modeldecoupe_id = model.search([('name', 'like', 'decoupe')])
        if not modeldecoupe_id:
            self.env['product.attribute'].create({'name': 'decoupe'})
            modeldecoupe_id = model.search([('name', '=', 'decoupe')])
        decoupe = str(printshop.form_decoupe_id.name)
        decoupe_id = self.env['product.attribute.value'].search([('name', '=', decoupe)])
        if not decoupe_id:
            self.env['product.attribute.value'].create({'name': decoupe, 'attribute_id': modeldecoupe_id[0]})
            decoupe_id = self.env['product.attribute.value'].search([('name', '=', decoupe)])
        # if printshop.pelliculage_id :

        print decoupe_id

        product = {'name': printshop.imprime,
                   'sale_ok': 1,
                   'purchase_ok': 0,
                   'produce_delay': 0,
                   'sale_delay': 0,
                   'supply_method': "produce",
                   'type': "product",
                   }
        product_id = printshop.product_id.id
        product_tmpl_id = printshop.product_id.product_tmpl_id.id
        if product_id:
            self.env['product.product'].write(product_id, product)
            self.env['product.product'].write(product_id, {'attribute_value_ids': [(6, 0, [size_id[0], color_id[0],
                                                                                           paper_id[0], printer_id[0],
                                                                                           type_id[0], finitions_id[0],
                                                                                           decoupe_id[0]])]})
            # self.env['offset.printshop'].write( ids[0], {'product_id' : product_id})
        else:
            product_id = self.env['product.product'].create(product)
            product_tmpl_id = printshop.product_id.product_tmpl_id.id
            # self.env['offset.printshop'].write( ids[0], {'product_id' : product_id,'state' : 'done'})
            self.env['product.product'].write(product_id, {'attribute_value_ids': [(6, 0, [size_id[0], color_id[0],
                                                                                           paper_id[0], printer_id[0],
                                                                                           type_id[0], finitions_id[0],
                                                                                           decoupe_id[0]])]})

        return True



        # generer produit final pour vente

    def generate_product_ok(self):
        context = {}
        id_printshop = self.ids[0]
        printshop = self.env['offset.printshop'].browse(id_printshop)
        product = {'name': printshop.imprime,

                   'standard_price': float(printshop.cout_total * 1.10) / printshop.quantite,
                   # 'largeur' :printshop.largeur,
                   # 'longueur_ouvert' :printshop.longueur,
                   'list_price': printshop.prix_vente_unitaire,
                   'description_sale': printshop.desc_ventes,
                   # 'type_offset': printshop.type_offset,
                   # 'partner_id' : printshop.partner_id
                   'sale_ok': 1,
                   'purchase_ok': 0,
                   # 'categ_id' : "Tous les articles - Ventes"
                   'route_ids': "manufacture",

                   'produce_delay': 0,
                   'sale_delay': 0,
                   'supply_method': "produce",
                   'type': "product",

                   }
        product_tmpl = self.env['product.template'].create(product)

        # product_id = self.env['product.product'].create( product)
        # product_id = self.env['product.template'].browse( {'product_tmpl_id' : product_tmpl_id_c})

        # vals = {}
        # vals['product_tmpl2_id'] = product_tmpl.id
        # print product_id
        self.write({'product_tmpl2_id': product_tmpl.id})
        self.write({'product_tmpl_id': product_tmpl.id})

        # self.write( {'quantite' : printshop.quantite})
        return True

    def generate_list_price(self):
        context = {}
        id_printshop = self.ids[0]
        printshop = self.env['offset.printshop'].browse(id_printshop)
        for q in printshop.priceline_ids:
            pricelist = {
                'product_tmpl_id': printshop.product_tmpl_id.id,
                'applied_on': '1_product',
                # 'base' :-3,

                'min_quantity': q.quantites,
                'fixed_price': q.prix_qte_sale,
                'compute_price': 'fixed',
                'pricelist_id': 1
                # 'price_version_id' : 1
            }
            pricelist_id = self.env['product.pricelist.item'].create(pricelist)

            # self.env['offset.printshop'].write({'product_id' : product_id,})
        return True

    def generate_ordre_prod(self):
        context = {}
        id_printshop = self.ids[0]
        printshop = self.env['offset.printshop'].browse(id_printshop)
        bom_obj = self.env['mrp.bom']

        bom_id = bom_obj._bom_find(product_id=printshop.product_id.id)

        prod = {
            'product_id': printshop.product_id.id,
            # 'price_max_marge' : printshop.prix_vente_unitaire,

            'product_qty': printshop.quantite,
            'product_uom': 19,
            'bom_id': bom_id

        }
        prod_id = self.env['mrp.production'].create(prod)

        # self.env['offset.printshop'].write( ids[0], {'product_id' : product_id,})
        return True



        # genere les sous produits pour sac

    def generate_subproducts_sac(self, quantite=1, qte_impression=1):
        # pool = pooler.get_pool(cr.dbname)
        id_printshop = self.ids[0]
        printshop = self.env['offset.printshop'].browse(id_printshop)
        self.generate_subproducts(quantite, qte_impression)
        # self.write( {'description' : description, })
        # self.write( {'desc_ventes':  'Article : ' + str(printshop.imprime)+'\n'+
        # '   Format Sac : '+ str(printshop.hauteur)+' x '+ str(printshop.largeur_sac)+' x '+ str(printshop.soufflet)+ '\n'+
        # '   Format ouvert : '+ str(printshop.largeur)+' x '+ str(printshop.longueur)+ '\n'+
        # '   Impression : ' + str(printshop.nbr_coul_recto)+ ' recto, '+ str(printshop.nbr_coul_verso)+' verso.'+ '\n'+
        # '   Support : ' +str(printshop.support_id.name)+ ' '+ '\n'+
        # + str(pell)
        # + str(coll)
        # + str(ver)


        # , })


class offset_printshop_subproduct(models.Model):
    _name = 'offset.printshop.subproduct'
    _description = 'OFFSET PRINTSHOP SUBPRODUCT'

    def get_subtotal(self):
        for record in self:
            if record.minimum_price:
                record.subtotal = record.product_qty * record.unit_price
                if record.minimum_price > record.subtotal:
                    record.subtotal = record.minimum_price
                else:
                    record.subtotal = record.product_qty * record.unit_price
            else:
                record.subtotal = record.product_qty * record.unit_price

    name = fields.Text('Designation', required=False, readonly=False)
    constante = fields.Selection([
        (1, 'Constant'),
        (0, 'Variable')], string='Product constant')
    product_id = fields.Many2one('product.product', 'Product', required=True)
    product_qty = fields.Float('Product qty', required=True, digits=(16, 2))
    unit_price = fields.Float('Unit Price', required=True)
    minimum_price = fields.Float('minimum Price')

    subtotal = fields.Float(compute='get_subtotal', method=True, type='float', string='Sub total', required=True)
    product_uom = fields.Many2one('product.uom', 'Product UOM')
    printshop_id = fields.Many2one('offset.printshop', 'Offset Printshop', required=False)
    matieres = fields.Boolean('Is a raw material', required=False)
    workcenter = fields.Boolean('Is a workcenter', required=False)


class printshop2_rigide(models.Model):
    _name = 'printshop2.rigide'
    _description = 'printshop2 Support rigide'

    @api.model
    def _media_get_default(self):
        allpapermedia = self.env['printshop2.rigide.line'].search([('support_id', '=', id)])
        return allpapermedia

    name = fields.Char('Familly', size=64, readonly=True)
    typeshop = fields.Selection([
        ('offsetprinting', 'OFFSET PRINTING'), ('signroll', 'ROLL SIGN SHOP'), ('signsheet', 'SHEET SIGN SHOP'),
    ], 'Type of business shop', states={'draft': [('readonly', False)]})
    grammage = fields.Float('Grammage', required=False, readonly=False, digits=(8, 0), help="in gr")
    prix_kg = fields.Float('prix du KG', digits=(8, 1))
    marque = fields.Char('Category')
    couleur = fields.Char('Color', default=" ")
    epaisseur = fields.Char('epaisseur', default=" ", help="in mm")

    line_ids = fields.One2many('printshop2.rigide.line', 'support_id', 'Variants Print media')

    @api.one
    def write_papername(self):
        id_product = self.ids[0]
        support = self.env['printshop2.rigide'].browse(id_product)
        self.write({'name': str(support.marque) + '_' + str(support.couleur) + '_' + str(support.grammage) + '_' + str(
            support.epaisseur)})
        return True

    @api.one
    def Create_paperline(self):
        id_product = self.ids[0]

        support = self.env['printshop2.rigide'].browse(id_product)
        paper_var = self.env['product.product'].search([('marque_support3', '=', support.name)])
        line_id = self.env['printshop2.rigide.line'].search([('support_id', '=', id_product)])
        for r in paper_var:
            lines_ids = [(2, 0, {'support_id': support.id, 'product_id': r.id, 'active': True})]

            lines_ids = [(0, 0, {'support_id': support.id, 'product_id': r.id})]

            support.write({"line_ids": lines_ids})


class printshop2_rigide_line(models.Model):
    _name = 'printshop2.rigide.line'
    _description = 'PRINTSHOP Support rigide line'

    support_id = fields.Many2one('printshop2.rigide', 'Print media', required=False)
    typeshop = fields.Selection(related='support_id.typeshop', string="type printshop")
    product_id = fields.Many2one('product.product', 'Product', required=True)
    longueur_feuille = fields.Float(related='product_id.longueur_support', string="Print media length", help="in cm")
    largeur_feuille = fields.Float(related='product_id.largeur_support', string="Print media width", help="in cm")
    longueur_support = fields.Float(string="media length", readonly=True, help="in cm")
    largeur_support = fields.Float(rstring=" media width", readonly=True, help="in cm")
    gr_support = fields.Float(related='support_id.grammage', string="Print media grammage")
    kg_support = fields.Float(related='support_id.prix_kg', string="Print media kg's price")
    marque_support = fields.Char(related='product_id.marque_support3', string="Print media brand")
    prix_support = fields.Float(related='product_id.prix_feuille', store=False)
    list_price = fields.Float(related='product_id.list_price', string="Price sale of the sheet")
    actif = fields.Boolean('actif for calcul', default=True)

    @api.onchange('typeshop')
    def size_media(self):
        if self.typeshop == 'offsetprinting':
            self.largeur_support = self.largeur_feuille
            self.longueur_support = self.longueur_feuille

        if self.typeshop == 'signsheet':
            self.largeur_support = self.largeur_feuille
            self.longueur_support = self.longueur_feuille

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
