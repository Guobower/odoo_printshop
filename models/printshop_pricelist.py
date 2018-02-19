# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2011 PLVDESIGN All Rights Reserved
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
import openerp.addons.decimal_precision as dp
from openerp.osv import osv, orm
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP
from openerp.tools import float_compare
from openerp.tools.translate import _
from openerp import tools, SUPERUSER_ID
from openerp import SUPERUSER_ID
from odoo import fields, models, api, _
from dateutil import parser


class printshop_listsprice(models.Model):
    _name = 'printshop.listsprice' 
    _description = 'PRINTSHOP priceList' 
    _order = 'product_tmpl_id,quantite,qte_listprice'

    name = fields.Char('Name', size=64, required=False, readonly=False)
    #quantites = fields.Many2one('printshop2.quantite', 'quantite', required=False)
    quantite = fields.Float('quantite')
    qte_listprice = fields.Float('prix unitaire vente')
    qte_bom_price = fields.Float('prix unitaire revient')

    product_tmpl_id = fields.Many2one('product.template', 'produit')
    product_id = fields.Many2one('product.product', 'produit')
    bom_id = fields.Many2one('mrp.bom', 'Nomenclature', states={'draft':[('readonly',False)]})
    qte_bom = fields.Float('Qte nomenclature', related="bom_id.product_qty")
    printshop_id = fields.Many2one('offset.printshop', 'Offset Printshop')
