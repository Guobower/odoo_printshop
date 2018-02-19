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


#class pour determiner type de machine de production

#  def create(self,  data, context=None):
#     if 'stype' in data:
#        if 'gr' in data:
#           data['line_ids'] = self._compute_factor_inv(data['factor_inv'])
#
#       return super(product_uom, self].create( data, context)





class printshop_machine(models.Model):
    _name = 'printshop.machine'
    _description = 'printshop Machine'

    name = fields.Char('Machine name', size=64, required=True, readonly=False)
    print_id = fields.Many2one('product.product', 'Print', required=True)
    laize_mach = fields.Float('Machine width' , digits=(8,2))
    long_mach = fields.Float('Machine length' , digits=(8,2))
    nbr_coul_mach = fields.Float('Nbr color of the machine' , digits=(8,0))
    nbr_passe = fields.Float('Nbr of sup. Quantity for production' , digits=(8,0))
    prise_pince = fields.Float('Machine gripper clamp' , digits=(8,2))
    laize_mach = fields.Float('machine laize' , digits=(8,2))
    brand = fields.Char('Brand', size=64,  readonly=False)

    prix_tirage = fields.Float(related='print_id.list_price', string="Price of the print run" )
    type_printer = fields.Selection([
        ('sign', 'sign'), ('digital', 'Digital'),
    ], 'Type of Machine', states={'draft': [('readonly', False)]})
    sous_traitance = fields.Boolean('Print subcontracting')
    workcenter_id_print = fields.Many2one('mrp.workcenter', 'Attached workcenter')
    cycle_print = fields.Float('cycle' , help="Production cylcle /hour ", digits=(8,0))

class printshop_type_support(models.Model):
    _name = 'printshop.type_support'
    _description = 'printshop Type Support'

    name = fields.Char('Type media', size=64)
    description = fields.Char('Description',size=128)


# class pour determiner les supports pour impression en feuille
class printshop_support(models.Model):
    _name = 'printshop.support'
    _description = 'printshop Support'
    
    
    
    @api.model
    def _media_get_default(self):
        allpapermedia = self.env['printshop.support.line'].search([('support_id', '=', id)])
        return allpapermedia





    name = fields.Char('Familly', size=64, readonly=True)
    grammage = fields.Float('Grammage', required=False, readonly=False , digits=(8,0))
    prix_kg = fields.Float('prix du KG' , digits=(8,1))
    brand = fields.Char('Category')
    couleur = fields.Char('Color' ,default=" ")
    type_id = fields.Many2one('printshop.type_support', 'Print media type', required=True)
    type = fields.Char(related='type_id.name',string="Print media type" , readonly=True)

    line_ids = fields.One2many('printshop.support.line', 'support_id', 'Variants Print media')

    @api.one
    def write_papername(self):
        id_product = self.ids[0]
        support = self.env['printshop.support'].browse(id_product)
        self.write({'name': str(support.type)+ '_' + str(support.marque) + '_' + str(support.couleur)+ '_' + str(support.grammage) })
        return True

    @api.one
    def Create_paperline(self):
        id_product = self.ids[0]
        
        support = self.env['printshop.support'].browse(id_product)
        paper_var = self.env['product.product'].search([('marque_support3','=',support.name)])
        line_id = self.env['printshop.support.line'].search([('support_id','=',id_product)])

        for r in paper_var :

            lines_ids = [(2, 0, {'support_id':support.id, 'product_id':r.id}) ]

            lines_ids = [(0, 0, {'support_id':support.id, 'product_id':r.id}) ]
        
            support.write({"line_ids" : lines_ids})



class printshop_support_line(models.Model):
    _name = 'printshop.support.line'
    _description = 'PRINTSHOP Support line'

    support_id = fields.Many2one('printshop.support', 'Print media', required=False)
    product_id = fields.Many2one('product.product', 'Product', required=True)
    longueur_support = fields.Float(related='product_id.longueur_support',string="Print media length")
    largeur_support = fields.Float(related='product_id.largeur_support',string="Print media width" )
    gr_support = fields.Float(related='support_id.grammage', string="Print media grammage" )
    kg_support = fields.Float(related='support_id.prix_kg', string="Print media kg's price" )
    marque_support = fields.Char(related='product_id.marque_support3', string="Print media brand" )
    prix_support = fields.Float( related='product_id.prix_feuille',store=False)
    list_price = fields.Float(related='product_id.list_price', string="Price sale of the sheet" )
    actif = fields.Boolean( 'actif for calcul')





class printshop_remise(models.Model):
    _name = 'printshop.remise'
    _description = 'printshop remise'

    name = fields.Char('Name', size=64, required=False, readonly=False)
    valeur = fields.Float('Discount', required=False, readonly=False)

class printshop_quantite(models.Model):
    _name = 'printshop.quantite'
    _description = 'printshop quantite'
    _order = 'quantites'

    name = fields.Char('Name', size=64, required=False, readonly=False)
    printshop_id = fields.Many2one('sign.printshop', 'sign Printshop', required=False)
    quantites = fields.Float('quantity', required=False, readonly=False, default=1 , digits=(16,0))
    price_qtes = fields.Float('prices qty', required=False, readonly=False)


class sign_printshop_priceline(models.Model):
    _name = 'sign.printshop.priceline'
    _description = 'sign PRINTSHOP priceLine'
    _order = 'quantites,prix_qte'

    name = fields.Char('Name', size=64, required=False, readonly=False)
    #quantites = fields.Many2one('printshop.quantite', 'quantite', required=False)
    quantites = fields.Float('Quantity', readonly=True)
    code_id = fields.Char('code_id', size=64, required=False, readonly=False)
    size = fields.Char('size', size=64, required=False, readonly=False)
    type_paper = fields.Char('type paper', size=64, required=False, readonly=False)
    side = fields.Char('nbr of side', size=64, required=False, readonly=False)
    color = fields.Char('nbr of color', size=64, required=False, readonly=False)
    laminate = fields.Char('type laminate', size=64, required=False, readonly=False)
    surface_traitement = fields.Char('surface traitement', size=64, required=False, readonly=False)
    weight = fields.Float('weight')
    prix_qte_cout_mat = fields.Float('raw materials' , readonly=True)
    prix_qte = fields.Float('Calculte price' , readonly=True)
    prix_qte_sale = fields.Float('Sale Price')

    total_prix_qte = fields.Float('total prix vente' , readonly=True)

    product_id = fields.Many2one('sign.printshop', 'produit')
    printshop_id = fields.Many2one('sign.printshop', 'sign Printshop')

#nombre de combinaisons possible pour la realisation du travail
class sign_printshop_line(models.Model):
    _name = 'sign.printshop.line'
    _description = 'sign PRINTSHOP Line'

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
    machine_id = fields.Many2one('printshop.machine', 'machine', required=False)
    support_id = fields.Many2one('product.product', 'Print media', required=True)
    poses_machine = fields.Float('Poses machine' )
    poses_support = fields.Float('Poses support')
    nbr_feuille = fields.Float('Nbr sheet' )
    nbr_tirage = fields.Float('print')
    cout = fields.Float('Cost')
    largeur_imp = fields.Float('Print width')
    longueur_imp = fields.Float('Print length')
    compute = fields.Boolean('Force')
    printshop_id = fields.Many2one('sign.printshop', 'sign Printshop', required=True)
    support_id = fields.Many2one('product.product', 'Print media', required=True)


class printshop_rigide(models.Model):
    _name = 'printshop.rigide'
    _description = 'printshop rigide'

    @api.one
    def write_name(self):
        id_product = self.ids[0]
        support = self.env['printshop.rigide'].browse(id_product)
        self.write({'name': str(support.type_id.name)+ '_' + str(support.reference)})
        return True

    name= fields.Char('Name', size=64, required=True, readonly=True)
    line_ids = fields.One2many('printshop.rigide.line', 'rigide_id', 'Supprts rigide')
    type_id = fields.Many2one('printshop.type_rigide', 'Support', required=True)
    reference = fields.Char('refernce',size=32)


class printshop_type_rigide(models.Model):
    _name = 'printshop.type_rigide'
    _description = 'printshop Type rigide'

    name = fields.Char('Type support', size=64)
    description = fields.Char('Description',size=128)

class printshop_rigide_line(models.Model):
    _name = 'printshop.rigide.line'
    _description = 'printshop Rigide line'


    product_id = fields.Many2one('product.product', 'Produit', required=True)
            #'largeur_rigide'= fields.Float('largeur rigide'),
            #'longueur_rigide'= fields.Float('longueur rigide'),
    largeur_rigide = fields.Float(related='product_id.largeur_calcul', store=False)
    longueur_rigide = fields.Float('product_id.longueur_calcul',  store=False)
    prix_rigide  = fields.Float('product_id.standard_price',  store=False)
    rigide_id = fields.Many2one('printshop.rigide', 'rigide', required=False) 







class other_product_line(models.Model):
    _name = 'other.product.line'
    _description = 'other_price_product line'
    
    def get_prix_total(self):
        result = {}
        for line in self:
            total=0
            total+=(line.product_id.standard_price*1.1*line.quantite)
            result[line.id] = total
        return result
    



    product_id = fields.Many2one('product.product', 'Produit', required=True,  select=1)
    prix = fields.Float('product_id.standard_price',  store=False)
    quantite = fields.Float('quantite',  required=False, readonly=False)

    prix_total = fields.Float(compute=get_prix_total, method=True, type='Float', string='cout Total Matieres', store=False)

    other_product_id = fields.Many2one('sign.printshop', 'printshop_id', required=False)
    

class signprintshop_setting(models.Model):
    _name = 'signprintshop.setting'
    _description = 'printshop admin setting'

    name = fields.Char('Setting Profil', size=64, readonly=False)
    marge = fields.Float('general marge' , digits=(8,2))
    raw_marge = fields.Float('raw maetriel marge' , digits=(8,2))

    tolerance = fields.Float('Tolerance of production' , digits=(8,2))
    remise_id = fields.Many2one('printshop.remise', 'Discount', required=False,
                                states={'draft': [('readonly', False)]})    
    bleed = fields.Float('Bleed', states={'draft': [('readonly', False)]}, default= 0.3)


class sign_printshop(models.Model):
    _order = "parent_id , date"
    _name = 'sign.printshop'
    _description = 'sign PRINTSHOP'
    _order = 'name desc,partner_id,date'



            


   
    #def get_quantite_prod(self):
     #   for line in self:
      #      (record.quantite+1)_prod = (record.quantite+1) + ((record.quantite+1)*float(record.tolerance))

    def get_quantite_prod(self):
        result = {}
        for line in self.browse(ids[0]):
                result[line.id] = line.quantite +line.quantite*float(line.tolerance)
        return result



    
    # mise àjour des champs
    def _name_get_default(self):
        
        return self.env['ir.sequence'].next_by_code('sign.printshop')


   # @api.model
    #def _setting_get_default(self):
     #   profil_setting = self.env['printshop.setting'].search([('name', '=', 'Standard')])
      #  return profil_setting

   # @api.model
   # def _machine_get_default(self):
    #    allmachines = self.env['printshop.machine'].search([('sous_traitance', '=', False)])
        #self.write({'machine_ids':allmachines})
     #   return allmachines
    




    name = fields.Char('Reference', size=64, required=True, readonly=True, default=_name_get_default)
    signprofil_setting = fields.Many2one('signprintshop.setting','name')
    child_ids = fields.One2many('sign.printshop', 'parent_id', 'Chils product', required=False,
                                states={'draft': [('readonly', False)]})
    parent_id = fields.Many2one('sign.printshop', 'Parent', required=False, index=True,
                                states={'draft': [('readonly', False)]})
    parent_is = fields.Boolean('Article compose', help='Check if the item is composed of several items')

    date = fields.Date('Date', states={'draft': [('readonly', False)]}, default=lambda * a: time.strftime('%Y-%m-%d'))

    partner_id = fields.Many2one('res.partner', 'Partner', required=False, states={'draft': [('readonly', False)]})
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env['res.company']._company_default_get('sale.order'))

    imprime = fields.Char('Print Product', size=64, required=True, readonly=False, states={'draft': [('readonly', False)]})
    largeur = fields.Float('width ', states={'draft': [('readonly', False)]})
    longueur = fields.Float('Length', states={'draft': [('readonly', False)]})
    fond_perdu = fields.Float(related='signprofil_setting.bleed', string="bleed" , readonly=True)
    imprime  = fields.Char('Nom d"Imprime', size=64,  readonly=False   )
    product_id  = fields.Many2one('product.product', 'Produit', required=False, state={'draft':[('readonly',False)]})
    product_categorie = fields.Many2one('product_tmpl_id.categ_id',  store=False)
        #'product_id': fields.Many2many('product.product', id1='att_id', id2='prod_id', string='Variants', readonly=True),

    product_tmpl_id = fields.Many2one('product.template', 'Product created', required=False)
    product_tmpl2_id = fields.Char( 'Product created', required=False)

    quantite = fields.Float('Quantity ordered', states={'draft': [('readonly', False)]}, required=False, digits=(16,0))

    marge = fields.Float(related='signprofil_setting.marge', string="general marge" , readonly=True)
    raw_marge = fields.Float(related='signprofil_setting.raw_marge', string="raw materiels marge" , readonly=True)

    quantite_prod = fields.Float( string='Production Quantity'  , digits=(16,0))
    remise_id = fields.Many2one('printshop.remise', 'Discount', required=False,
                                states={'draft': [('readonly', False)]})
    machine_id = fields.Many2one('printshop.machine', 'Machine', required=False,
                                states={'draft': [('readonly', False)]})

    support_id = fields.Many2one('printshop.support', 'Print Media', required=False,
                                 states={'draft': [('readonly', False)]})
    support_fournis = fields.Boolean('Print media Supplied',
                                     help='Check whether the print media is supplied by the client')
    support_line_id = fields.Many2one('printshop.support.line', 'Prints Media variants', required=False,
                                      states={'draft': [('readonly', False)]})
    support_ids = fields.Many2many('printshop.support.line', 'printshop_support_line_rel', 'printshop_id', 'support_id',
                                   string='Print Media', states={'draft': [('readonly', False)]}, required=False,
                                   help="Add Print Media to calculate printing")

    Multiqty = fields.One2many('printshop.quantite','printshop_id', 'Multiquantity',readonly=False)
    type_sign = fields.Selection([('applat', 'Card & flyer'),
                                        ('depliant', 'Leaflet folder'),
                                        ('brochure', 'Book & Booket'),
                                        ('blocnote', 'Notebook'),
                                        ('sac', 'Bag'),
                                        ('boite', 'Box'),
                                        ('Compose', 'Compound products')], 'Type', index=True)    
    largeur_raclage_rigide = fields.Float('Largeur a racler en m', required=False)
    longueur_raclage_rigide = fields.Float('Longueur ea racler m', required=False)
    quantite_raclage_rigide = fields.Float('Quantite raclage rigide', required=False)

        #'marge' : fields.Float('Marge', required=True   ),
    priceline_ids = fields.One2many('sign.printshop.priceline', 'printshop_id', 'Calculs', required=False, states={'draft':[('readonly',False)]})


    rigide_id =  fields.Many2one('printshop.rigide', 'Rigide', required=False   ) 
    qty_feuilles =  fields.Float('Nombre de feuilles', readonly=True,)
    oeillet_id =  fields.Many2one('product.product', 'Oeillet', required=False   )
    oeillets = fields.Float('oeillets par m'   )
    nbr_oeillets_produit = fields.Float( type='Float', string='Oeillets par produit', store=False)
    couture_id = fields.Many2one('product.product', 'Couture', required=False   )
    couture = fields.Float('ml de couture',readonly=True)
    qte_couture = fields.Float('Qte Couture',readonly=True)
    baguette_id = fields.Many2one('product.product', 'Baguette', required=False   )
    baguettes = fields.Float('Nbr Baguettes'   )
    qte_baguettes = fields.Float('Qte Baguettes', readonly=True)
    raclage_id = fields.Many2one('product.product', 'Raclage', required=False   )
    qte_raclage = fields.Float('Qte Raclage')
    desc_ventes = fields.Text('Description')
    bom_id = fields.Many2one('mrp.bom', 'Nomenclature'   )
    line_ids = fields.One2many('sign.printshop.line', 'printshop_id', 'Calculs')
    line_id = fields.Many2one('sign.printshop.line', 'Ligne optimale', required=False, state={'draft':[('readonly',False)]})
    rigide_line_ids = fields.One2many('sign.printshop.rigide.line', 'printshop_id', 'Nombre de feuilles', required=False   )
    rigide_line_id = fields.Many2one('sign.printshop.rigide.line', 'Nombre de feuilles optimal', required=False   )
    other_product_line_id = fields.One2many('other.product.line', 'other_product_id','Autres matieres', required=False   )
    cout_total_matieres = fields.Float( 'cout Total Matieres')
    compute = fields.Boolean('Force')
    bom_id = fields.Many2one('mrp.bom', 'BOM', states={'draft': [('readonly', False)]})
    line_ids = fields.One2many('sign.printshop.line', 'printshop_id', 'Calculs', required=False,
                               states={'draft': [('readonly', False)]})
    line_id = fields.Many2one('sign.printshop.line', 'optimal line', required=False,
                              states={'draft': [('readonly', False)]})
    user_id = fields.Many2one('res.users', 'user calculator', required=True, readonly=True,
    states={'draft': [('readonly', False)]},
    default=lambda self: self.env.uid)
    subproduct_ids = fields.One2many('sign.printshop.subproduct', 'printshop_id', 'Sub-products', required=False,
                                     states={'draft': [('readonly', False)]})
    cout_total = fields.Float(compute='get_cout_total_price', string='Total cost' )
    cout_total_mat = fields.Float(compute='get_cout_total_price', type='Float', string='Total cost of materials' )

    prix_vente_unitaire = fields.Float(compute='get_cout_total_price', string='Unit selling price' )
    prix_vente_total = fields.Float(compute='get_cout_total_price', string='Total selling price' )
    state = fields.Selection([('draft', 'Draft'),
                              ('done', 'Done')], 'State', default='draft', index=True, readonly=True)                
    #def _name_get_default(self):
     #       return self.pool.get('ir.sequence').get(cr, uid, 'sign.printshop')



 

    @api.depends('quantite')
    def get_cout_total_price(self):
        for record in self:
            total=0
            for sub in record.subproduct_ids:
                total+=sub.subtotal
                
            record.cout_total = total
            record.cout_total_mat = total
            marge = record.marge
            print "total"
            print total
            record.prix_vente_unitaire = ((total*marge)/((record.quantite+1)+1)) 
            record.prix_vente_total = ((total*marge/(record.quantite+1)) + (total*(float(record.remise_id.valeur)/100))/(record.quantite+1))*(record.quantite+1)
            
                

    @api.multi
    def compute_price(self, force=False):
        # pool = pooler.get_pool(cr.dbname)
        #id_printshop = self[0].id
        printshop = self.env['sign.printshop'].browse(self.id)
        return True

    @api.multi  # here
    def compute_parent(self):
        # pool = pooler.get_pool(cr.dbname)
        # id_printshop = self[0].id
        # printshop = self.env['sign.printshop'].browse( id_printshop)
        sql = '''
        DELETE from sign_printshop_subproduct where printshop_id = %s
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
                self.env['sign.printshop.subproduct'].create(l)
        return True





    def compute(self, force=False):
        #printshop = self
        #id_printshop = ids[0]
        printshop = self.env['sign.printshop'].browse(self.ids)
        laize_mach=printshop.machine_id.laize_mach
        longueur=printshop.longueur + printshop.fond_perdu
        largeur=printshop.largeur + printshop.fond_perdu
        fond_perdu=printshop.fond_perdu
        quantite=printshop.quantite
        machine=printshop.machine_id
        # ajout ligne en bas
        line = {}
        sql = '''
        DELETE from sign_printshop_subproduct where printshop_id = %s
        '''
        self.env.cr.execute(sql, (printshop.id,))
        if not force:
            sql = '''
            DELETE from sign_printshop_line where printshop_id = %s
            '''
            self.env.cr.execute(sql, (printshop.id,))
            poses=0
            ml=0
            m2=0
            cout_minimal = 0
            # self.compute_contre_collage ( ids, context={'support_collage':True},force=False): False
           # if not force_poses and force_m2:
            for s in printshop.support_id.line_ids :
                nbr_pose=0
                nbr_ml=0
                nbr_m2=0
                if s.largeur_support <= laize_mach :
                    if (int(s.largeur_support / largeur) > int(s.largeur_support / longueur)):
                        nbr_pose = int(s.largeur_support/largeur) 
                        if nbr_pose==0:nbr_pose=1
                        nbr_ml = (longueur*quantite)/ int(nbr_pose)
                        nbr_m2=nbr_ml*s.largeur_support
                    else:
                        nbr_pose = int(s.largeur_support/longueur) 
                        if nbr_pose==0:nbr_pose=1
                        nbr_ml = (largeur*quantite)/ int(nbr_pose)
                        nbr_m2=nbr_ml*s.largeur_support
                    if m2==0:
                        m2=nbr_m2
                    if nbr_m2<=m2:
                        poses=nbr_pose
                        ml=nbr_ml
                        m2=nbr_m2
                    qte_impression = (quantite / nbr_pose) 
                    cout_papier = m2 * s.product_id.list_price
                    cout_tirage = m2 * machine.print_id.list_price
                    cout = cout_papier + cout_tirage
                    line = {'name': machine.name + ' ' + s.product_id.name,
                            'machine_id': machine.id,
                            'support_id': s.product_id.id,
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
                    #self.env['sign.printshop.line'].create(line)
                    line = self.env['sign.printshop.line'].create(line)
                    if cout_minimal == 0: cout_minimal = cout
                    if cout <= cout_minimal:
                        cout_minimal = cout
                        largeur_impression = largeur
                        longueur_impression = 0
                        printshop.line_id = line.id
            self.generate_subproducts(quantite,qte_impression)
            self.compute_rigide

        return True    


    def compute_rigide(self, force=False):
        #printshop = self
        #id_printshop = ids[0]
        printshop = self.env['sign.printshop'].browse(self.ids)
        laize_mach=printshop.machine_id.laize_mach
        longueur=printshop.longueur + printshop.fond_perdu
        largeur=printshop.largeur + printshop.fond_perdu
        fond_perdu=printshop.fond_perdu
        quantite=printshop.quantite
        if not force_feuille and printshop.rigide_id:
            if printshop.etat == 'draft':
                sql = '''
                DELETE from digital_printshop_rigide_line where printshop_id = %s
                    '''
                cr.execute(sql, (ids[0],))
            feuilles=0
            for r in printshop.rigide_id.line_ids :
                nbr_poses=0
                if int((r.largeur_rigide / largeur)* (r.longueur_rigide / longueur)) < int((r.largeur_rigide / longueur)* (r.longueur_rigide / largeur)): 
                    nbr_poses = int((r.largeur_rigide / longueur))*int((r.longueur_rigide / largeur))
                    if nbr_poses==0:nbr_poses=1
                else :
                    nbr_poses = int((r.largeur_rigide / largeur)) * int((r.longueur_rigide / longueur))
                    if nbr_poses==0:nbr_poses=1
                nbr_feuille =  int(quantite / nbr_poses)
                if nbr_feuille==0:nbr_feuille=1
                if feuilles==0:
                    feuilles=nbr_feuille
                if nbr_feuille<=feuilles:
                    feuilles=nbr_feuille
                    self.write(cr, uid, [printshop.id], {'rigide_line_id':r.id,})
                line = {'nbr_feuille' : nbr_feuille,'largeur_rigide' : r.largeur_rigide,
                        'longueur_rigide':r.longueur_rigide,'rigide_line_id':r.id,'compute' : False,'printshop_id':ids[0]
                                } 
                line = self.env['sign.printshop.rigide.line'].create(line)
                if cout_minimal == 0: cout_minimal = cout
                if cout <= cout_minimal:
                    cout_minimal = cout
                    largeur_impression = largeur_imp
                    longueur_impression = 0
                    printshop.line_id = line.id
        self.generate_subproducts(quantite,nbr_feuille)

        return True    


    def compute_qte_1 (self, force=False):
        #pool = pooler.get_pool(cr.dbname)
        #id_printshop = self.ids[0]
        printshop = self.env['sign.printshop'].browse(self.ids[0])
        line={}
        sql = '''
            DELETE from sign_printshop_priceline where printshop_id = %s
            '''
        self._cr.execute(sql, (self.ids[0],))
        if not force:
            sql = '''
                DELETE from sign_printshop_priceline where printshop_id = %s
                '''
            self._cr.execute(sql, (self.ids[0],))
        for q in printshop.Multiqty :
                
                self.write({'quantite' : q.quantites})
                
                print "q.quantites"
                print q.quantites
                #self.compute( ids, context={},force=False)
                if printshop.type_sign=='applat':
                    self.compute(force=False)
                #self.write({ q.price_qtes : float(printshop.prix_vente_unitaire)})
                price= printshop.prix_vente_unitaire
                total_prix_qte= printshop.prix_vente_unitaire*printshop.quantite
                print "price"
                print price
                price2 = q.price_qtes
                cout= printshop.cout_total
                
                
                cout_mat=printshop.cout_total_mat/printshop.quantite

                self.env['sign.printshop.priceline'].create({
                    'name':printshop.imprime,
                    'code_id':printshop.name,
                    'size':str(printshop.largeur)+"*"+str(printshop.longueur),                               
                    'type_paper':printshop.support_id.name,
                    'prix_qte' : price,
                    'total_prix_qte' : total_prix_qte,
                    'prix_qte_cout_mat' : cout_mat * printshop.raw_marge,
                    'quantites':printshop.quantite,
                    'printshop_id':self.id})

        return True

 
    def compute_old(self, force=False):
        force_poses=0
        force_ml=0
        force_m2=0
        force_feuille=0
        printshop = self.env['sign.printshop'].browse(self.ids)
        laize_mach=printshop.machine_id.laize_mach
        longueur=printshop.longueur + printshop.fond_perdu
        largeur=printshop.largeur + printshop.fond_perdu
        fond_perdu=printshop.fond_perdu
        quantite=printshop.quantite
        nbr_feuille=0
        line={}
        sql = '''
        DELETE from sign_printshop_subproduct where printshop_id = %s
        '''
        self.env.cr.execute(sql, (printshop.id,))
        poses=0
        ml=0
        m2=0
        support_line_id=False
        #calcul des mètres linéraires et du nombre de poses 
        if not force_poses and force_m2:
            if printshop.etat == 'draft':
                sql = '''
                DELETE from sign_printshop_line where printshop_id = %s
                    '''
                cr.execute(sql, (ids[0],))
            for s in printshop.support_id.line_ids :
                nbr_pose=0
                nbr_ml=0
                nbr_m2=0
                if s.largeur_support <= laize_mach :
                    if (int(s.largeur_support / largeur) > int(s.largeur_support / longueur)):
                        nbr_pose = int(s.largeur_support/largeur) 
                        if nbr_pose==0:nbr_pose=1
                        nbr_ml = (longueur*quantite)/ int(nbr_pose)
                        nbr_m2=nbr_ml*s.largeur_support
                    else:
                        nbr_pose = int(s.largeur_support/longueur) 
                        if nbr_pose==0:nbr_pose=1
                        nbr_ml = (largeur*quantite)/ int(nbr_pose)
                        nbr_m2=nbr_ml*s.largeur_support
                    if m2==0:
                        m2=nbr_m2
                    if nbr_m2<=m2:
                        poses=nbr_pose
                        ml=nbr_ml
                        m2=nbr_m2
                        self.write(cr, uid, [printshop.id], {'support_line_id':s.id,})
                    line = {
                            'laize' : s.largeur_support,'support_line_id':s.id,'poses' : nbr_pose,'ml':nbr_ml,
                            'm2':nbr_m2,'compute' : False,'printshop_id':ids[0]
                            } 
                    pool.get('xl.printshop.line').create(cr, uid, line)
        else:
            poses=force_poses
            ml=force_ml
            m2=force_m2

        #calcul du nombre de feuilles par ligne du support rigide
        if not force_feuille and printshop.rigide_id:
            if printshop.etat == 'draft':
                sql = '''
                DELETE from digital_printshop_rigide_line where printshop_id = %s
                    '''
                cr.execute(sql, (ids[0],))
            feuilles=0
            for r in printshop.rigide_id.line_ids :
                nbr_poses=0
                if int((r.largeur_rigide / largeur)* (r.longueur_rigide / longueur)) < int((r.largeur_rigide / longueur)* (r.longueur_rigide / largeur)): 
                    nbr_poses = int((r.largeur_rigide / longueur))*int((r.longueur_rigide / largeur))
                    if nbr_poses==0:nbr_poses=1
                else :
                    nbr_poses = int((r.largeur_rigide / largeur)) * int((r.longueur_rigide / longueur))
                    if nbr_poses==0:nbr_poses=1
                nbr_feuille =  int(quantite / nbr_poses)
                if nbr_feuille==0:nbr_feuille=1
                if feuilles==0:
                    feuilles=nbr_feuille
                if nbr_feuille<=feuilles:
                    feuilles=nbr_feuille
                    self.write(cr, uid, [printshop.id], {'rigide_line_id':r.id,})
                line = {'nbr_feuille' : nbr_feuille,'largeur_rigide' : r.largeur_rigide,
                        'longueur_rigide':r.longueur_rigide,'rigide_line_id':r.id,'compute' : False,'printshop_id':ids[0]
                                } 
                pool.get('xl.printshop.rigide.line').create(line)
        else:
            nbr_feuille=force_feuille
            
        #Calcul des couts
        #printshop = pool.get('xl.printshop').browse(cr, uid, id_printshop)
        printshop = self.env['sign.printshop'].browse(self.ids)
        

        
        self.write( {'nbr_pose' : poses,
                                             'nbr_ml':ml,
                                             'nbr_m2':m2,
                                             'support_line_id':support_line_id,
                                             'nbr_feuille':nbr_feuille,
                                             'qte_raclage' : (largeur-fond_perdu)*(longueur-fond_perdu)*quantite,
                                             'qte_baguettes' : printshop.baguettes*quantite,
                                             'couture' : (largeur+longueur)*2,
                                             'qte_couture' : (largeur+longueur)*2*quantite,

                                             
                                             })
        self.generate_subproducts(quantite)
        print "ttttttt"
        return True        
    

    
    def generate_subproducts(self, quantite,qte_impression):

                printshop = self.env['sign.printshop'].browse(self.ids[0])
                support_line = {'name': '[Print media] ' + str(printshop.line_id.support_id.name) + '\n'
                                        + "__________Print size : " + str(printshop.line_id.largeur_imp + 1) + " * " + str(
                    printshop.line_id.longueur_imp + 1) + '\n',
                                'product_id': printshop.line_id.support_id.id,
                                'product_qty': printshop.line_id.nbr_ml ,
                                'unit_price': printshop.line_id.support_id.list_price,
                                'product_uom': printshop.line_id.support_id.uom_id.id,
                                'printshop_id': self.id}
                if not printshop.support_fournis:
                    self.env['sign.printshop.subproduct'].create(support_line)

                tirage_line = {'name': '[Print] ' + str(printshop.line_id.machine_id.print_id.name) + "__________Pnbr pose in print:" + str(printshop.line_id.poses_machine) + '\n' ,
                               'product_id': printshop.line_id.machine_id.print_id.id,
                               'product_qty': printshop.line_id.nbr_tirage,
                               'unit_price': printshop.line_id.machine_id.prix_tirage,
                               'product_uom': printshop.line_id.machine_id.print_id.uom_id.id,

                               'printshop_id': self.id}
                self.env['sign.printshop.subproduct'].create(tirage_line)

        

                if printshop.rigide_id:
                    rigide_line = {'name': '[rigide] '+printshop.rigide_line_id.name,
                                    'product_id' : printshop.rigide_line_id.product_id.id,
                                    'product_qty' : nbr_feuille,
                                    'unit_price' : printshop.rigide_line_id.product_id.prix_interne,
                                    'product_uom' : printshop.rigide_line_id.product_id.uom_id.id,
                                    'printshop_id' : self.id}
                    self.env['sign.printshop.subproduct'].create(rigide_line)
                if printshop.baguette_id:
                    baguette_line = {'name': '[baguette] '+printshop.baguette_id.name,
                                    'product_id' : printshop.baguette_id.id,
                                    'product_qty' : printshop.baguettes*quantite,
                                    'unit_price' : printshop.baguette_id.prix_interne,
                                    'product_uom' : printshop.baguette_id.uom_id.id,
                                    'printshop_id' : self.id}
                    self.env['sign.printshop.subproduct'].create(baguette_line)
                if printshop.raclage_id:
                    raclage_line = {'name': '[raclage] '+printshop.raclage_id.name,
                                    'product_id' : printshop.raclage_id.id,
                                    'product_qty' : (largeur-fond_perdu)*(longueur-fond_perdu)*quantite,
                                    'unit_price' : printshop.raclage_id.prix_interne,
                                    'product_uom' : printshop.raclage_id.uom_id.id,
                                    'printshop_id' : self.id}
                    self.env['sign.printshop.subproduct'].create(raclage_line)
                if printshop.couture_id:
                    couture_line = {'name': '[couture] '+printshop.couture_id.name,
                                    'product_id' : printshop.couture_id.id,
                                    'product_qty' : (largeur+longueur)*2*quantite,
                                    'unit_price' : printshop.couture_id.prix_interne,
                                    'product_uom' : printshop.couture_id.uom_id.id,
                                    'printshop_id' : self.id}
                    self.env['sign.printshop.subproduct'].create(couture_line)
                if printshop.oeillet_id:
                    oiellet_line = {'name': '[oiellet] '+printshop.oeillet_id.name,
                                    'product_id' : printshop.oeillet_id.id,
                                    'product_qty' : printshop.nbr_oeillets_produit*quantite,
                                    'unit_price' : printshop.oeillet_id.prix_interne,
                                    'product_uom' : printshop.oeillet_id.uom_id.id,
                                    'printshop_id' : self.id}
                    self.env['sign.printshop.subproduct'].create(oiellet_line)

                
                self.write({'description' : 'Article n°:' +str(printshop.name)+'\n'+ 
                str(printshop.imprime)+'\n'+
                '   Size : '+ str(printshop.largeur)+' x '+ str(printshop.longueur) +' m'+'\n'+ 
                '   Print : quadri recto en qualite ' + str(printshop.machine_id.name)+  '\n'+
                '   Print Media : ' +str(printshop.support_id.name)  + '\n',
                                                     'nbr_pose' : printshop.line_id.poses_support,
                                                     'nbr_ml':printshop.line_id.nbr_ml,
                                                     'nbr_m2':printshop.line_id.nbr_m2,
                                                     #'support_line_id':printshop.line_id.support_line_id,
                                                    # 'nbr_feuille':printshop.rigide_line_id.nbr_feuille,
                                                     'qte_raclage' : ((printshop.largeur)-(printshop.fond_perdu))*((printshop.longueur)-(printshop.fond_perdu))*printshop.quantite,
                                                     'qte_baguettes' : printshop.baguettes*quantite,
                                                     'couture' : ((printshop.largeur)+(printshop.longueur))*2,
                                                     'qte_couture' : ((printshop.largeur)+(printshop.longueur))*2*(printshop.quantite),

                                                     
                                                     })
                return True
    

    
    def generate_bom(self):
        #pool = pooler.get_pool(cr.dbname)
        #context = {}
        #id_printshop = self.ids[0]
        printshop = self.env['sign.printshop'].browse(self.ids)
        if not printshop.product_id:
                raise UserError(_("Le nombre de page doit etre multiple de 4"))

        work = {'name' : str(printshop.product_id.name) + '  qty: '+ str(printshop.quantite) ,
                        'code':str(printshop.name),}
        

        work_id = self.env['rp.routing'].create(work)

        bom = {'name': printshop.product_id.name,
                        'product_tmpl_id' : printshop.product_id.product_tmpl_id.id,
                        'product_qty' : printshop.quantite,

                        'routing_id':work_id,

        }

        bom_id = self.env['mrp.bom'].create(bom)

        for line in printshop.subproduct_ids:       #ici on créer les sous produit................
                const1=0
                if "[Callage]" in line.name or "[Insolation]" in line.name or "[decoupe]" in line.name: const1=1
                bom_line = {'name': line.name,
                                'product_id' : line.product_id.id,
                                'product_qty' : line.product_qty,
                                'constante' : const1,
                                'bom_id' : bom_id,
                                }
                self.env['mrp.bom.line'].create(bom_line)
                if "service" in line.product_id.type :
                    work_line = {
                                'cycle_nbr' : line.product_qty,
                                'product_id':line.product_id.id,
                                'workcenter_id' : 1,
                                'name': str(line.product_id.name),
                                'routing_id':work_id,
                                }

                    self.env['mrp.routing.workcenter'].create(work_line)


        self.env['sign.printshop'].cxrite({'bom_id' : bom_id,'state' : 'done'})

        bom_obj = self.env['mrp.bom']

        bom_id = bom_obj._bom_find(product_id=printshop.product_id.id)

        prod = {
                            'product_id' : printshop.product_id.id,
                            #'partner_id' : printshop.partner_id,

                            'product_qty' :printshop.quantite,
                            'bom_id' : bom_id,
                            'routing_id':work_id,

        }
        prod_id = self.env['mrp.production'].create( prod)        
                           
        #self.pool.get('sign.printshop').write(cr, uid, ids[0], {'bom_id' : bom_id})
        self.penv(['sign.printshop']).write({'bom_id' : bom_id,'state' : 'done'})
        return True

    def generate_product(self):
        #pool = pooler.get_pool(cr.dbname)
        context = {}
        id_printshop = ids[0]
        printshop = self.env(['sign.printshop']).browse(id_printshop)
        product = {'name': 'printshop.imprime',
                    'standard_price' : Float(printshop.cout_total * 1.10)/printshop.quantite,

                    'list_price' : printshop.prix_vente_unitaire,
                    'description_sale':printshop.description,

                    'sale_ok': 1,
                    'purchase_ok': 0,
                    'produce_delay' : 0,
                    'sale_delay' : 0,
                    #'supply_method' : "produce",
                    'type' : "product",}
        product_id = self.pool.get('product.product').create(cr, uid, product)

        self.penv(['sign.printshop']).write({'product_id' : product_id,})
        return True



class sign_printshop_line(models.Model):
    _name = 'sign.printshop.line' 
    _description = 'sign printshop Line' 
    
    def get_optimal(self):
        result = {}
        for line in self:
            try:
                if line.id == line.printshop_id.line_id.id:
                    result[line.id] = 'yes'
                else:result[line.id] = 'no'
            except:pass
            return result 


    name = fields.Char('Name', size=64, required=False, readonly=False)
    machine_id = fields.Many2one('printshop.machine', 'machine', required=False)
    support_id = fields.Many2one('product.product', 'Print media', required=True)
    poses_machine = fields.Float('Poses machine' )
    poses_support = fields.Float('Poses support')
    nbr_tirage = fields.Float('print')
    cout = fields.Float('Cost')
    nbr_m2 = fields.Float('Cost')
    nbr_ml = fields.Float('Cost')

    largeur_imp = fields.Float('Print width')
    longueur_imp = fields.Float('Print length')
    compute = fields.Boolean('Force')
    printshop_id = fields.Many2one('offset.printshop', 'Offset Printshop', required=True)
    support_id = fields.Many2one('product.product', 'Print media', required=True)



class sign_printshop_rigide_line(models.Model):
    _name = 'sign.printshop.rigide.line' 
    _description = 'sign printshop Rigide Line' 
    
    def get_optimal(self):
        result = {}
        for line in self:
            try:
                if line.id == line.printshop_id.rigide_line_id.id:
                    result[line.id] = 'yes'
                else:result[line.id] = 'no'
            except:pass
            return result     

        

    largeur_rigide = fields.Float('largeur rigide')
    longueur_rigide = fields.Float('longueur rigide')
    qty_feuilles =  fields.Float('Nbr Feuilles')
    product_id = fields.Many2one('product.product', 'Produit', required=True)

    compute = fields.Boolean('Forcer')
    printshop_id = fields.Many2one('sign.printshop', 'sign printshop', required=False) 
    rigide_line_id = fields.Many2one('printshop.rigide.line', 'Support Rigide', required=False)
    cout  = fields.Float('Cout')



class sign_printshop_subproduct(models.Model):
    _name = 'sign.printshop.subproduct' 
    _description = 'XL printshop SUBPRODUCT' 
    
    #def get_subtotal(self):
     #   result = {}
      #  for line in self:
       #         result[line.id] = line.product_qty*line.unit_price
        #return result

    def get_subtotal(self):
            for record in self:
                record.subtotal = record.product_qty * record.unit_price


    
    name = fields.Char('Designation', size=64, required=False, readonly=False)
    product_id =  fields.Many2one('product.product', 'Product', required=True)
    product_qty = fields.Float('Qte Produit', required=True)
    unit_price =  fields.Float('Prix unitaire', required=True)
    subtotal =  fields.Float(compute=get_subtotal, method=True, type='Float',string='Sous total', required=True)
    #product_uom =  fields.Many2one('product.uom', 'Product UOM', required=True)
    printshop_id = fields.Many2one('sign.printshop', 'XL printshop', required=False)
       



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
