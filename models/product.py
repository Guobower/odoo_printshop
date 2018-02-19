# -*- encoding: utf-8 -*-
'''
Created on 6 december. 2010

@author: tarik Lallouch
'''



import time
from datetime import datetime
import odoo.addons.decimal_precision as dp
from odoo import api, fields, models, _
from dateutil import parser
from odoo.exceptions import UserError


class product_template(models.Model):
    _name = 'product.template'
    _inherit = 'product.template'
    _order = 'type_matieres, type_production, name'
    
    
    
    @api.onchange('prix_kg')
    def compute_sheet_kg(self):
        #pool = pooler.get_pool(cr.dbname)
        id_product = self.ids[0]
        product = self.env['product.template'].browse(self.ids)
        self.write({
                    
                    'prix_feuille' : (product.largeur_support/100)*(product.longueur_support/100)*(product.marque_support.grammage/1000)*1.02*product.prix_kg
                    })
        
        return True  

    def _search_price_list_item_p(self):
        item_obj = self.env['product.pricelist.item']
        res = {}
        for product in self.browse(self.ids):
            item_ids = item_obj.search([('product_id', '=', product.id)])
            if self._context.get('query', True):
                sql_str = item_ids and len(self.ids) == 1 and \
                          '''UPDATE product_pricelist_item set
                                      product_active_id=%d
                                      WHERE id %s %s ''' % \
                          (product.id, len(item_ids) > 1 and
                           'in' or '=', len(item_ids) > 1 and
                           tuple(item_ids) or item_ids[0])
                sql_str and self._cr.execute(sql_str)
                item_ids and len(self.ids) == 1 and self._cr.commit()
            res[product.id] = item_ids
        return res

    def _write_price_list_item_p(self, value):
        for val in value:
            if val[0] == 1:
                sql_str = val[2].get('price_discount', False) and \
                          """UPDATE product_pricelist_item set
                                  price_discount='%s'
                                  WHERE id=%d """ % (val[2].get('price_discount'),
                                                     val[1])
                val[2].get('price_discount', False) and self._cr.execute(sql_str)
        return True

    calculate_price =  fields.Boolean('Enable to Calculate Internal Price', help="Check this box if the product is included in the price calculation.", default = False)
    prix_interne =  fields.Float('Cost of production', digits=(8,2))
    user_id =  fields.Many2one('res.users', 'User', required=True, readonly=True, default = lambda self: self.env.uid)
    longueur_calcul =  fields.Float('Length')
    largeur_calcul =  fields.Float('Width / Width roll')
    #list_price_id =  fields.One2many('product.pricelist.item', 'price_version_id','prix', required=False, readonly=False)
    support_offset_is =  fields.Boolean('Leaf Print Support', help="Check this box if the product is a support for the sheet printing used in the calculation of the price.", default = False)
    actif = fields.Boolean( 'actif for calcul',default=True)

    #______papier
    marque_support =  fields.Many2one('printshop2.support','Categorie paper' )
    type_pelliculage =  fields.Many2one('printshop2.type_pelliculage','Type of coating' )

    longueur_support =  fields.Float('Lenght print media' ,digits=(8,2))
    largeur_support =  fields.Float('width print media' ,digits=(8,2))
    prix_kg =  fields.Float(related= 'marque_support.prix_kg' ,string='Prix KG',digits=(8,2))
    marge_support =  fields.Float(related= 'marque_support.marge_support' ,string='marge list price from cost price',digits=(8,2), help='10% = 1.10')

    prix_feuille =  fields.Float('Sheet price',digits=(8,2))
    marque_support_GF =  fields.Many2one('printshop.support','Category Digital print media' )

    price_list_item =  fields.One2many('printshop.listsprice','product_tmpl_id','Prices bases')
    marque_support3 =  fields.Char(related= 'marque_support.name',string='type of paper', readonly=True)
    marque_supportGF =  fields.Char(related= 'marque_support_GF.name',string='type of paper', readonly=True)
    marque_rigide =  fields.Many2one('printshop2.rigide','Categorie support rigide' )

    #grammage =  fields.related('printshop2_support','grammage',type='Float',relation='printshop2.support',string='grammage',digits=(16,0))
    grammage =  fields.Float(related= 'marque_support.grammage' ,string='Grammage',digits=(8,0))

    #______papier

    #______support en rouleaux
    longueur_rouleau =  fields.Float('lenght roll', digits=(8,2))
    laize_rouleau =  fields.Float('width roll', digits=(8,2))
    type_s = fields.Many2one('printshop2.stype', 'Type of Support', required=False)
    epaisseur_calcul = fields.Float('Thickness grammage' ,digits=(8,2))
    weight_sheet = fields.Float('weight sheet' ,digits=(8,2))

    type_matieres = fields.Selection([
        ('baguette','Baguette'),
        ('clichet','clichet'),
        ('divers_mat','Divers'),
        ('emballage_carton','emballage_carton'),
        ('emballage','emballage'),
        ('oeillet','Oeillet'),
        ('rigide','Rigide'),
        ('support_offset','Sup. impression offset'),
        ('support_GF','Sup. impression GF'),
        ('spirale','Spirale'),
        ('pelliculage','Pelliculage'),

        ],'Type of raw material' , readonly=False)
    
    
    type_production = fields.Selection([
        ('couture','sewing'),
        ('calage','setting machine'),
        ('collage','gluing'),
        ('divers_prod','Various'),
        ('decoupe_offset','Offset cutting'),
        ('decoupe_digital','Digital cutting'),
        ('insolation','Plate Insolation'),
        ('laminage','Laminage'),
        ('piquage','Stitching'),
        ('pliage','Folding'),
        ('tirageoffset','Offset print'),
        ('tiragedigital','Digital Print'),
        ('raclage','Scraping'),
        ('rigide','Rigid support'),
        ('perfo_spirale','Spirale punching'),
        ('traitement_surface','Surface treatment'),],'Type production' , readonly=False)
    work_id = fields.Many2one('mrp.workcenter', 'Attached workcenter')
    cycle = fields.Float('cycle' , help="Production cylcle /hour ", digits=(8,0))
    constante = fields.Selection([
        (1, 'Constant'),
        (0, 'Variable')], string='Product constant',default=1)
    def generate_attribute(self):
        context = {}
        id_product = self.ids[0]
        product = self.env['product.product'].browse(id_product)

        #self.write(cr, uid, [product.id], {'attribute_line_ids': {'attribute_id':3, 'value_ids': [(6, 0, [209])]}})
        #self.write(cr, uid,ids,{'attribute_line_ids': {'attribute_id':3, 'value_ids':209}})
        #self.create_variant_ids(self, cr, uid, ids, context={})

        ##self.pool.get('product.attribute.line').create(cr, uid, {'product_tmpl_id': product.id , 'attribute_id': 3, 'value_ids': 13})                              
        ##self.pool.get('product.attribute.line').create(cr, uid, {'product_tmpl_id': product.id , 'attribute_id': 3, 'value_ids': [(6, 0, [26])]})                              
        #self.pool.get('product.attribute.line').create(cr, uid, {'product_tmpl_id': product.id , 'attribute_id': 3, 'value_ids': [(6, 0, [26])]})                              
        #self.pool.get('product.attribute.line').create(cr, uid, {'product_tmpl_id': product.id , 'attribute_id': 4, 'value_ids': [(6, 0, [299])]}) 
        line_id = self.env['product.attribute.line'].search(([('product_tmpl_id', '=', product.id),('attribute_id','=', 4)]))
        mylist= {}
        self.env['product.attribute.value'].search([('attribute_id','=', 4)])
        for item in mylist:
            print item

        #self.pool.get('product.attribute.line').write(cr, uid, line_id,{'product_tmpl_id': product.id , 'attribute_id': 4, 'value_ids': [(1, id,{'id':71})]})
        #self.pool.get('product.attribute.line').write(cr, uid, line_id,{'product_tmpl_id': product.id , 'attribute_id': 4, 'value_ids': [(1,id, {'id':93})]})

        #self.pool.get('product.attribute.line').write(cr, uid, line_id,{'product_tmpl_id': product.id , 'attribute_id': 4, 'value_ids': [(0, 0, value_2)]})                              

        #self.write(cr, uid, [product.id], {'attribute_line_ids': {'product_tmpl_id': product.id , 'attribute_id': 4, 'value_ids': [(6, 0, [27,52])]}})                        
        #self.write(cr, uid, [product.id], {'attribute_line_ids': {'product_tmpl_id': product.id , 'attribute_id': 4, 'value_ids': [(6, 0, [13])]}})                        

        return True

    def generate_attribute_1(self):
        context = {}
        id_product = self.ids[0]
        product = self.env['product.template'].browse(id_product)
        of_longueur = product.of_longueur
        for ids2 in self.env['product.attribute'].search([('name','=','longueur')]):
            ids3 = self.env['product.attribute.value'].search([('name','like',of_longueur)])
            print len(ids3)
            if not ids3 in self.env['product.attribute.value'].search([('name','like',of_longueur)]):
                vals = {'name': str(of_longueur), 'attribute_id': ids2}
                self.env['product.attribute.value'].create(vals)
            else:
                for ids3 in self.env['product.attribute.value'].search([('name','like',of_longueur)]):
                    self.env['product.attribute.line'].create({'product_tmpl_id': product.id , 'attribute_id': ids2, 'value_ids': [(6, 0, {ids3})]})
        self.generate_attribute_2()

        return True

    def generate_attribute_2(self):
        context = {}
        id_product = self.ids[0]
        product = self.env['product.template'].browse(id_product)
        of_gamme = product.type_offset
        for ids2 in self.env['product.attribute'].search([('name','=','gamme')]):
            ids3 = self.env['product.attribute.value'].search([('name','like',of_gamme)])
            print len(ids3)
            if not ids3 in self.env['product.attribute.value'].search([('name','like',of_gamme)]):
                vals = {'name': of_gamme, 'attribute_id': ids2}
                self.env['product.attribute.value'].create(vals)
            else:
                for ids3 in self.env['product.attribute.value'].search([('name','like',of_gamme)]):
                    self.env['product.attribute.line'].create({'product_tmpl_id': product.id , 'attribute_id': ids2, 'value_ids': [(6, 0, {ids3})]})
        self.generate_attribute_3()

        return True

    def generate_attribute_3(self):
        context = {}
        id_product = self.ids[0]
        product = self.env['product.template'].browse(id_product)
        of_support = product.of_support
        for ids2 in self.env['product.attribute'].search([('name','=','support')]):
            ids3 = self.env['product.attribute.value'].search([('name','like',of_support)])
            print len(ids3)
            if not ids3 in self.env['product.attribute.value'].search([('name','like',of_support)]):
                vals = {'name': of_support, 'attribute_id': ids2}
                self.env['product.attribute.value'].create(vals)
            else:
                for ids3 in self.env['product.attribute.value'].search([('name','like',of_support)]):
                    self.env['product.attribute.line'].create({'product_tmpl_id': product.id , 'attribute_id': ids2, 'value_ids': [(6, 0, {ids3})]})



        return True

    def miseajour_papier(self):
        #pool = pooler.get_pool(cr.dbname)
        #id_product = self.ids[0]
        product = self.env['product.template'].browse(self.ids)
        if self._context.get('support_offset_is', True):
            self.write({'name' : str(product.marque_support.name)+' - '+str(product.largeur_support)+'*'+str(product.longueur_support)})

            self.write({'type_matieres' : 'support_offset','produce_delay' : 0,
                    'list_price' : (product.largeur_support/100)*(product.longueur_support/100)*(product.grammage/1000)*1.02*product.prix_kg *1.10,
                    'sale_delay' : 0,
                    'supply_method' : "buy",
                    'type' : "product",
                    'name':  str(product.marque_support.name)+' - '+str(product.largeur_support)+'*'+str(product.longueur_support),
                    'cost_method' : "average",
                    'sale_ok': 0,
                    'purchase_ok': 1,
                    'weight' : (product.largeur_support/100)*(product.longueur_support/100)*(product.grammage/1000)*1.02,
                    'prix_feuille' : (product.largeur_support/100)*(product.longueur_support/100)*(product.grammage/1000)*1.02*product.prix_kg
                    })

        return True 


    def compute_sheet(self):
        #pool = pooler.get_pool(cr.dbname)
        id_product = self.ids[0]
        product = self.env['product.template'].browse(self.ids)
        if product.marque_support:
            self.write({
                    
                    'weight_sheet' : (product.largeur_support/100)*(product.longueur_support/100)*(product.grammage/1000)*1.02,
                    'prix_feuille' : (product.largeur_support/100)*(product.longueur_support/100)*(product.marque_support.grammage/1000)*1.02*product.prix_kg
                    })
        if product.marque_rigide:
            self.write({
                    
                    'weight_sheet' : (product.largeur_support/100)*(product.longueur_support/100)*(product.grammage/1000)*1.02,
                    'prix_feuille' : (product.largeur_support/100)*(product.longueur_support/100)*(product.marque_rigide.grammage/1000)*1.02*product.prix_kg
                    })
        return True 

    def compute_listprice_sheet(self):
        #pool = pooler.get_pool(cr.dbname)
        id_product = self.ids[0]
        product = self.env['product.template'].browse(self.ids)
        self.write({
                    
                    'list_price' : ((product.largeur_support/100)*(product.longueur_support/100)*(product.marque_support.grammage/1000)*1.02*product.prix_kg) * product.marge_support,

                    })

                    
        return True 




    def creer_rouleau(self):
        # pool = pooler.get_pool(cr.dbname)
        #id_product = self.ids[0]
        product = self.env['product.template'].browse(self.ids)
        #self.write([product.id], {'name_template' : str(product.marque_rouleau.name)+' - '+str(product.laize_rouleau)+'*'+str(product.longueur_rouleau)+ ' m'})


        self.write({'type_matieres' : 'support_GF',
                    'produce_delay' : 0,
                    'calculate_price' : 1,
                    'name' : str(product.marque_support_GF.name)+' - '+str(product.laize_rouleau)+'*'+str(product.longueur_rouleau)+ ' m',
                    'product.marque_support_GF' : str(product.marque_support_GF.name),

                    'sale_delay' : 0,
                    'supply_method' : "buy",
                    'type' : "product",
                    'cost_method' : "average",
                    'sale_ok': 0,
                    'purchase_ok': 1,
                    #'prix_interne' : 1.10*product.standard_price,
                    'list_price' : product.standard_price*1.10
                    })

        return True

    def creer_consommables(self):
        #pool = pooler.get_pool(cr.dbname)
        id_product = self.ids[0]
        product = self.env['product.product'].browse(id_product)
        self.write({'produce_delay' : 0,
                    'sale_delay' : 0,
                    'procure_method' : "make_to_stock",
                    'supply_method' : "buy",
                    'type' : "consu",
                    'sale_ok': 0,
                    'purchase_ok': 1,
                    })
        return True

    def on_change_type2(self, product_id):
        if self.type2 :
            return {'value': {'type2': False}}

    def compute_price(self):
        for prod_id in self.ids:
            bom_ids = self._cr.dbname.get('mrp.bom').search([('product_id', '=', prod_id)])
            if bom_ids:
                for bom in self._cr.dbname.get('mrp.bom').browse(bom_ids):
                    self._calc_price(bom)
        return True

    def _calc_price(self, bom):
        if not bom.product_id.calculate_price:
            return bom.product_id.prix_interne
        else:
            price = 0
            if bom.bom_lines:
                for sbom in bom.bom_lines:
                    price += self._calc_price(sbom) * sbom.product_qty
            else:
                bom_obj = self._cr.dbname.get('mrp.bom')
                no_child_bom = bom_obj.search([('product_id', '=', bom.product_id.id), ('bom_id', '=', False)])
                if no_child_bom and bom.id not in no_child_bom:
                    other_bom = bom_obj.browse(no_child_bom)[0]
                    if not other_bom.product_id.calculate_price:
                        price += self._calc_price(other_bom) * other_bom.product_qty
                    else:
                        #                        price += other_bom.product_qty * other_bom.product_id.prix_interne
                        price += other_bom.product_id.prix_interne
                else:
                    #                    price += bom.product_qty * bom.product_id.prix_interne
                    price += bom.product_id.prix_interne
                    #                if no_child_bom:
                    #                    other_bom = bom_obj.browse(no_child_bom)[0]
                    #                    price += bom.product_qty * self._calc_price(other_bom)
                    #                else:
                    #                    price += bom.product_qty * bom.product_id.prix_interne
            if bom.routing_id:
                for wline in bom.routing_id.workcenter_lines:
                    wc = wline.workcenter_id
                    cycle = wline.cycle_nbr
                    hour = (wc.time_start + wc.time_stop + cycle * wc.time_cycle) *  (wc.time_efficiency or 1.0)
                    price += wc.costs_cycle * cycle + wc.costs_hour * hour
                    price = self.env['product.uom']._compute_price(bom.product_uom.id,price,bom.product_id.uom_id.id)
            if bom.bom_lines:
                self.write({'prix_interne' : price/bom.product_qty})
            if bom.product_uom.id != bom.product_id.uom_id.id:
                price = self.env['product.uom']._compute_price(bom.product_uom.id,price,bom.product_id.uom_id.id)
            return price

product_template()

class printshop2_stype(models.Model):
    _name = 'printshop2.stype'
    _description = 'PRINTSHOP2 support type'

    name = fields.Char('Name', size=64, required=False, readonly=False)

printshop2_stype()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

