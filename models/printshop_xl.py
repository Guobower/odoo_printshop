# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2011 akenoo. All Rights Reserved
#    authors: tarik lallouch
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
'''
Created on 22/01/2011

@author: tarik lAllouch
'''

import time
from datetime import datetime
import odoo.addons.decimal_precision as dp
from odoo import api, fields, models, _
from dateutil import parser
from odoo.exceptions import UserError

class printshop_machine(models.Model):
    _name = 'printshop.machine' 
    _description = 'printshop Machine' 

   
    name = fields.Char('Designation', size=64, required=True, readonly=False)
    qualite = fields.Char('qualite', size=64, required=True, readonly=False)

    product_id = fields.Many2one('product.product', 'Produit', required=True)
        #'laize_mach': fields.Float ('Laize machine')
    laize_mach = fields.Float(related='product_id.largeur_calcul', store=False)
    prix_m2 = fields.Float(related='product_id.standard_price',  store=False)
        


class printshop_support(models.Model):
    _name = 'printshop.support'
    _description = 'printshop Support'

    name = fields.Char('Designation', size=64,  readonly=False)
    line_ids = fields.One2many('printshop.support.line', 'support_id', 'Variants Print media')
     


class printshop_support_line(models.Model):
    _name = 'printshop.support.line'
    _description = 'printshop Support line'

    product_id= fields.Many2one('product.product', 'Produit', required=True)
            #'laize_support'= fields.Float('Laize support'),
    laize_support = fields.Float('product_id.laize_rouleau',  store=False)
    prix_support = fields.Float('product_id.standard_price',  store=False)
    support_id= fields.Many2one('printshop.support', 'Support', required=False)



class printshop_rigide(models.Model):
    _name = 'printshop.rigide'
    _description = 'printshop rigide'

    name= fields.Char('Designation', size=64, required=True, readonly=False)
    line_ids = fields.One2many('printshop.rigide.line', 'rigide_id', 'Supprts rigide', required=True)


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

        prix_total = fields.function(get_prix_total, method=True, type='Float', string='cout Total Matieres', store=False)

        other_product_id = fields.Many2one('xl.printshop', 'printshop_id', required=False)
    







class digital_printshop(models.Model):
    _name = 'xl.printshop' 
    _description = 'XL printshop' 
    
    def get_cout_total_matieres(self):
        result = {}
        for line in self:
            total_3=0
            for sub3 in line.other_product_line_id:
                total_3+=sub3.prix_total
            result[line.id] = total_3
        return result
    
    def get_cout_total(self):
        result = {}
        for line in self:
            total=0
            for sub in line.subproduct_ids:
                total+=sub.subtotal
            result[line.id] = total
        return result 
    
    def get_prix_vente_unitaire(self):
        result = {}
        for line in self:
            try:
                #result[line.id] = (line.cout_total + line.cout_total*line.marge/100)/line.quantite
                result[line.id] = ((line.cout_total*1.33/line.quantite) + (line.cout_total*(Float(line.remise_id.valeur)/100))/line.quantite)

            except:result[line.id]=0
        return result 
    
    def get_oeillets(self):
        result = {}
        for line in self:
            try:
                result[line.id] = (line.largeur+line.longueur)*2/line.oeillets
            except:result[line.id]=0
        return result


        name = fields.Char('Designation', size=64, required=False, readonly=False )
        date  = fields.Date('Date'   )
        partner_id  = fields.Many2one('res.partner', 'Client', required=False   )
        imprime  = fields.Char('Nom d"Imprime', size=64, required=True, readonly=False   )
        product_id  = fields.Many2one('product.product', 'Produit', required=False, states={'draft':[('readonly',False)]})
        product_categorie = fields.Many2one('product_tmpl_id.categ_id',  store=False)
            #'product_id': fields.Many2many('product.product', id1='att_id', id2='prod_id', string='Variants', readonly=True),
        child_ids = fields.One2many('offset.printshop', 'parent_id', 'Produits fils', required=False, states={'draft':[('readonly',False)]})
        parent_id = fields.Many2one('offset.printshop', 'Parent', required=False,select=1, states={'draft':[('readonly',False)]}),
        parent_is = fields.Boolean('Article compose', help='Cocher si larticle est compose de plueisuers articles')
        product_tmpl_id = fields.Many2one('product.template', 'Produit template', required=False, states={'draft':[('readonly',False)]})          
        largeur = fields.Float('Largeur en m',required=True   )
        longueur = fields.Float('Longueur en m',required=True   )
        largeur_raclage_rigide = fields.Float('Largeur a racler en m', required=False)
        longueur_raclage_rigide = fields.Float('Longueur ea racler m', required=False)
        quantite_raclage_rigide = fields.Float('Quantite raclage rigide', required=False)

        fond_perdu = fields.Float('Fond Perdu en m',  states={'done':[('readonly', True)]}) 
        quantite = fields.Float('Quantite'   , required=False)
            #'marge' : fields.Float('Marge', required=True   ),
        remise_id =fields.Many2one('printshop2.remise','remise', required=False , states={'draft':[('readonly',False)]})

        machine_id = fields.Many2one('printshop.machine', 'Machine', required=True   )
        nbr_pose =  fields.Float('Poses',help='nbr pose produit dans le support', readonly=True   )
        support_id =  fields.Many2one('printshop.support', 'Support', required=True   ),
        support_line_id = fields.Many2one('support_id.line', 'Produit Support', required=False   )
        nbr_ml = fields.Float('Ml',help='nbr metre linaire produit dans le support', readonly=True)
        nbr_m2 = fields.Float('M²',help='nbr m² produit dans le support', readonly=True)
        rigide_id =  fields.Many2one('printshop.rigide', 'Rigide', required=False   ) 
        qty_feuilles =  fields.Float('Nombre de feuilles', readonly=True,),
        oeillet_id =  fields.Many2one('product.product', 'Oeillet', required=False   )
        oeillets = fields.Float('oeillets par m'   )
        nbr_oeillets_produit = fields.function(get_oeillets, method=True, type='Float', string='Oeillets par produit', store=False),
        couture_id = fields.Many2one('product.product', 'Couture', required=False   )
        couture = fields.Float('ml de couture',readonly=True)
        qte_couture = fields.Float('Qte Couture',readonly=True)
        baguette_id = fields.Many2one('product.product', 'Baguette', required=False   )
        baguettes = fields.Float('Nbr Baguettes'   )
        qte_baguettes = fields.Float('Qte Baguettes', readonly=True)
        raclage_id = fields.Many2one('product.product', 'Raclage', required=False   )
        qte_raclage = fields.Float('Qte Raclage',readonly=True)
        description = fields.Text('Description')
        bom_id = fields.Many2one('mrp.bom', 'Nomenclature'   )
        line_ids = fields.one2many('xl.printshop.line', 'printshop_id', 'Calculs', required=False, states={'draft':[('readonly',False)]})
        line_id = fields.Many2one('xl.printshop.line', 'Ligne optimale', required=False, states={'draft':[('readonly',False)]})
        rigide_line_ids = fields.one2many('xl.printshop.rigide.line', 'printshop_id', 'Nombre de feuilles', required=False   )
        rigide_line_id = fields.Many2one('xl.printshop.rigide.line', 'Nombre de feuilles optimal', required=False   )
        other_product_line_id = fields.one2many('other.product.line', 'other_product_id','Autres matieres', required=False   )
        cout_total_matieres = fields.function(get_cout_total_matieres, method=True, type='Float', string='cout Total Matieres', store=False)
        user_id = fields.Many2one('res.users', 'Createur', required=True, readonly=True)
        subproduct_ids = fields.One2many('xl.printshop.subproduct', 'printshop_id', 'Les sous produits', required=False   )
        cout_total = fields.function(get_cout_total, method=True, type='Float', string='cout total', store=False),
        prix_vente_unitaire = fields.function(get_prix_vente_unitaire, method=True, type='Float', string='Prix de vente unitaire', store=False),#  = 'cout_de_reviens' + ('cout_de_reviens' *('marge'/100)) / 'quantite' 
        state = fields.Selection([
                ('draft','Draft'),
                ('done','Done'),
                 ],    'State', select=True, readonly=True)
                
    #def _name_get_default(self):
     #       return self.pool.get('ir.sequence').get(cr, uid, 'xl.printshop')


 
 
 
    def compute(self):
        #pool = pooler.get_pool(cr.dbname)

        id_printshop = self.ids[0]
        printshop = self.env['xl.printshop'].browse(id_printshop)
       # print 234444
        longueur=(printshop.longueur + printshop.fond_perdu)
        largeur=(printshop.largeur + printshop.fond_perdu)
        fond_perdu=printshop.fond_perdu
        quantite=printshop.quantite
        laize_mach=(printshop.machine_id.laize_mach)
        prix_tirage=printshop.machine_id.prix_m2
        
#ajout ligne en bas

        nbr_feuille=0
        line={}
        sql = '''
        DELETE from xl_printshop_subproduct where printshop_id = %s
        '''
        self.env.cr.execute(sql, (self.ids[0],))
        poses=0
        ml=0
        m2=0
        if not force:
            sql = '''
            DELETE from xl_printshop_line where printshop_id = %s
            '''
            self.env.cr.execute(sql, (self.ids[0],))
            cout_minimal=0
            #self.compute_contre_collage (cr, uid, ids, context={'support_collage':True},force=False): False
            for s in printshop.support_id.line_ids :
                nbr_pose=0
                nbr_ml=0
                nbr_m2=0
                if s.laize_support <= laize_mach :
                    if s.laize_support <=largeur and  s.laize_support <=longueur  :
                        largeur=int((largeur/ s.laize_support)+0.75 )
                        quantite=quantite*int((largeur/ s.laize_support)+0.75 )              
                    nbr_pose_a = int(s.laize_support/largeur) 
                    if nbr_pose_a<=1:nbr_pose_a=1
                    nbr_ml_a = (longueur*quantite*1.05)/ int(nbr_pose_a)
                    nbr_m2_a=nbr_ml_a*s.laize_support
                    nbr_pose_b = int(s.laize_support/longueur) 
                    if nbr_pose_b<=1:nbr_pose_b=1
                    nbr_ml_b= (largeur*quantite*1.05)/ int(nbr_pose_b)
                    nbr_m2_b=nbr_ml_b*s.laize_support
                    if nbr_m2_b<=nbr_m2_a:
                        nbr_m2=nbr_m2_b
                        nbr_ml=nbr_ml_b
                        nbr_pose=nbr_pose_b
                    else:
                        nbr_m2=nbr_m2_a
                        nbr_ml=nbr_ml_a
                        nbr_pose=nbr_pose_a
                        
                    
                    cout_tirage=nbr_m2*prix_tirage
                    cout_support=nbr_m2*s.product_id.standard_price
                    cout= cout_support+cout_tirage
                    line = {
                            'laize' : s.laize_support,'support_line_id':s.id,'poses' : nbr_pose,'ml':nbr_ml,
                            'm2':nbr_m2,'compute' : False,'printshop_id':ids[0]
                            } 
                    line_id=self.pool.get('xl.printshop.line').create(cr, uid, line)
                    if cout_minimal==0:
                        cout_minimal=cout
                    if cout<=cout_minimal:
                        cout_minimal=cout
                        print cout
                        self.write(cr, uid, [printshop.id], {'line_id' : line_id})
        #Création des lignes des produits consomés  --------------------------------------------------------------------------------
                                #print nbr_tirage
            if printshop.rigide_id:
                if printshop.state == 'draft':
                    print 33
                    sql = '''
                    DELETE from xl_printshop_rigide_line where printshop_id = %s
                        '''
                    self.env.cr.execute(sql, (self.ids[0],))
                feuilles=0
                for r in printshop.rigide_id.line_ids :
                    longueur= printshop.longueur_raclage_rigide
                    largeur= printshop.largeur_raclage_rigide
                    fond_perdu= (printshop.fond_perdu)
                    qty= printshop.quantite_raclage_rigide
                    #nbr_poses_r=0
                    print r.largeur_rigide
                    print r.longueur_rigide
                    print largeur
                    print longueur
                    print int((r.largeur_rigide/100) / largeur)
                    print int((r.longueur_rigide/100) / longueur)
                    #nbr_poses_r_a = (int(r.largeur_rigide/100 / longueur))*(int(r.longueur_rigide/100 / largeur))
                    if (int(r.largeur_rigide/100 / largeur)* int(r.longueur_rigide/100 / longueur)) < (int(r.largeur_rigide/100 / longueur)* int(r.longueur_rigide/100 / largeur)): 
                        nbr_poses_r = (int(r.largeur_rigide/100 / longueur))*(int(r.longueur_rigide/100 / largeur))
                    #if nbr_poses_r<=1:nbr_poses_r=1
                    else :
                        nbr_poses_r = (int(r.largeur_rigide/100 / largeur))*(int(r.longueur_rigide/100 / longueur))
                    #if nbr_poses_r<=1:nbr_poses_r=1
                    nbr_feuille =  int((qty / nbr_poses_r)+0.75)
                    #nbr_feuille =  30
                    if nbr_feuille<=1:nbr_feuille=1
                    cout_rigide=nbr_feuille*r.product_id.standard_price
                    cout= cout_rigide
                    line = {'qty_feuilles' : nbr_feuille,'largeur_rigide' : r.largeur_rigide,'cout' : cout,'product_id':r.product_id.id,
                            'longueur_rigide':r.longueur_rigide,'rigide_line_id':r.id,'compute' : False,'printshop_id':ids[0]
                                    } 
                    line_id=self.pool.get('xl.printshop.rigide.line').create(cr, uid, line)
                    #if cout_minimal==0:
                     #   cout_minimal=cout
                    #if cout<=cout_minimal:
                     #   cout_minimal=cout
                    self.write([printshop.id], {'rigide_line_id' : line_id})              
       
        
        self.generate_subproducts(quantite)
  
        return True
        
    

    
    def generate_subproducts(self):
        #pool = pooler.get_pool(cr.dbname)


        
        id_printshop = self.ids[0]
        printshop = self.env['xl.printshop'].browse(id_printshop)
        machine_line = {'name': '[Printer Machine] ' + printshop.machine_id.product_id.name,
                        'product_id' : printshop.machine_id.product_id.id,
                        'product_qty' : int(printshop.line_id.m2)+1,
                        'unit_price' : printshop.machine_id.prix_m2,
                        'product_uom' : 1,
                        'printshop_id' : ids[0]}
        self.pool.get('xl.printshop.subproduct').create(cr, uid, machine_line)
        
        support_line = {'name': '[Print Media] '+str(printshop.line_id.support_line_id.product_id.name),
                        'product_id' : printshop.line_id.support_line_id.product_id.id,
                        'product_qty' : int((printshop.line_id.ml)+1),
                        'unit_price' : printshop.line_id.support_line_id.product_id.list_price*printshop.line_id.support_line_id.product_id.laize_rouleau,
                        'product_uom' : 1,
                        'printshop_id' : ids[0]}
        self.pool.get('xl.printshop.subproduct').create(cr, uid, support_line)
        if printshop.rigide_id:
            rigide_line = {'name': str(printshop.rigide_line_id.rigide_line_id.product_id.name),
                            'product_id' : printshop.rigide_line_id.product_id.id,
                            'product_qty' : printshop.rigide_line_id.qty_feuilles,
                            'unit_price' : printshop.rigide_line_id.rigide_line_id.product_id.list_price,
                            'product_uom' : 1,
                            'printshop_id' : ids[0]}
            self.pool.get('xl.printshop.subproduct').create(cr, uid, rigide_line)


        for line in printshop.other_product_line_id :
            line = {'name': str(line.product_id.name),
                            'product_id' : line.product_id.id,
                            'product_qty' : line.quantite,
                            'unit_price' : line.product_id.list_price,
                            'product_uom' : 1,
                            'printshop_id' : ids[0]}
            self.pool.get('xl.printshop.subproduct').create(cr, uid, line)
            
        if printshop.baguette_id:
            baguette_line = {'name': '[baguette] '+str(printshop.baguette_id.name),
                            'product_id' : printshop.baguette_id.id,
                            'product_qty' : printshop.baguettes*quantite,
                            'unit_price' : printshop.baguette_id.list_price,
                            'product_uom' : 1,
                            'printshop_id' : ids[0]}
            self.pool.get('xl.printshop.subproduct').create(cr, uid, baguette_line)
        if printshop.raclage_id:
            raclage_line = {'name': '[raclage] '+str(printshop.raclage_id.name),
                            'product_id' : printshop.raclage_id.id,
                            'product_qty' : (printshop.largeur-printshop.fond_perdu)*(printshop.longueur-printshop.fond_perdu)*printshop.quantite,
                            'unit_price' : printshop.raclage_id.list_price,
                            'product_uom' : 1,
                            'printshop_id' : ids[0]}
            self.pool.get('xl.printshop.subproduct').create(cr, uid, raclage_line)
        if printshop.couture_id:
            couture_line = {'name': '[couture] '+str(printshop.couture_id.name),
                            'product_id' : printshop.couture_id.id,
                            'product_qty' : (printshop.largeur+printshop.longueur)*2*printshop.quantite,
                            'unit_price' : printshop.couture_id.list_price,
                            'product_uom' : 1,
                            'printshop_id' : ids[0]}
            self.pool.get('xl.printshop.subproduct').create(cr, uid, couture_line)
        if printshop.oeillet_id:
            oiellet_line = {'name': '[oiellet] '+str(printshop.oeillet_id.name),
                            'product_id' : printshop.oeillet_id.id,
                            'product_qty' : printshop.nbr_oeillets_produit*quantite,
                            'unit_price' : printshop.oeillet_id.list_price,
                            'product_uom' :1,
                            'printshop_id' : ids[0]}
            self.pool.get('xl.printshop.subproduct').create(cr, uid, oiellet_line)
        
        self.write(cr, uid, [printshop.id], {'description' : 'Article n°:' +str(printshop.name)+'\n'+ 
        str(printshop.imprime)+'\n'+
        '   Size : '+ str(printshop.largeur)+' x '+ str(printshop.longueur) +' m'+'\n'+ 
        '   Print : quadri recto en qualite ' + str(printshop.machine_id.qualite)+  '\n'+
        '   Print Media : ' +str(printshop.support_id.name)  + '\n',
                                             'nbr_pose' : printshop.line_id.poses,
                                             'nbr_ml':printshop.line_id.ml,
                                             'nbr_m2':printshop.line_id.m2,
                                             #'support_line_id':printshop.line_id.support_line_id,
                                            # 'nbr_feuille':printshop.rigide_line_id.nbr_feuille,
                                             'qte_raclage' : ((printshop.largeur)-(printshop.fond_perdu))*((printshop.longueur)-(printshop.fond_perdu))*printshop.quantite,
                                             'qte_baguettes' : printshop.baguettes*quantite,
                                             'couture' : ((printshop.largeur)+(printshop.longueur))*2,
                                             'qte_couture' : ((printshop.largeur)+(printshop.longueur))*2*(printshop.quantite),

                                             
                                             })
        return True
    
    def compute_force(self):
        #pool = pooler.get_pool(cr.dbname)
        id_printshop = self.ids[0]
        printshop = self.env['xl.printshop'].browse(id_printshop)
        poses=0
        ml=0
        m2=0
        
        feuilles=0
        for line in printshop.line_id:
            if line.compute:
                poses=line.poses
                ml=line.ml
                m2=line.m2
                self.write(cr, uid, [printshop.id], {'support_line_id':line.support_line_id.id})
        for line in printshop.rigide_line_ids:
            if line.compute:
                feuilles=line.nbr_feuille
                self.write(cr, uid, [printshop.id], {'rigide_line_id':line.rigide_line_id.id})
        self.compute(cr, uid, ids, context,poses,ml,m2,feuilles)
        return True
    
    def generate_bom(self, cr, uid, ids, context={}):
        #pool = pooler.get_pool(cr.dbname)
        context = {}
        id_printshop = self.ids[0]
        printshop = self.env['xl.printshop'].browse(id_printshop)
        if not printshop.product_id:
                raise UserError(_("Le nombre de page doit etre multiple de 4"))

        work = {'name' : str(printshop.product_id.name) + '  qty: '+ str(printshop.quantite) ,
                        'code':str(printshop.name),}
        

        work_id = self.env['rp.routing'].create(work)

        bom = {'name': printshop.product_id.name,
                        'product_tmpl_id' : printshop.product_id.product_tmpl_id.id,
                        'product_qty' : printshop.quantite,
                        'product_uom' : printshop.product_id.uom_id.id,
                        'routing_id':work_id,

        }

        bom_id = self.env['mrp.bom'].create(bom)

        for line in printshop.subproduct_ids:       #ici on créer les sous produit................
                const1=0
                if "[Callage]" in line.name or "[Insolation]" in line.name or "[decoupe]" in line.name: const1=1
                bom_line = {'name': line.name,
                                'product_id' : line.product_id.id,
                                'product_qty' : line.product_qty,
                                'product_uom' : line.product_uom.id,
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


        self.env['xl.printshop'].cxrite({'bom_id' : bom_id,'state' : 'done'})

        bom_obj = self.env['mrp.bom']

        bom_id = bom_obj._bom_find(product_id=printshop.product_id.id)

        prod = {
                            'product_id' : printshop.product_id.id,
                            #'partner_id' : printshop.partner_id,

                            'product_qty' :printshop.quantite,
                            'product_uom' :1,
                            'bom_id' : bom_id,
                            'routing_id':work_id,

        }
        prod_id = self.env['mrp.production'].create( prod)        
                           
        #self.pool.get('xl.printshop').write(cr, uid, ids[0], {'bom_id' : bom_id})
        self.penv(['xl.printshop']).write({'bom_id' : bom_id,'state' : 'done'})
        return True

    def generate_product(self):
        #pool = pooler.get_pool(cr.dbname)
        context = {}
        id_printshop = ids[0]
        printshop = self.env(['xl.printshop']).browse(id_printshop)
        product = {'name': printshop.imprime,
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

        self.penv(['xl.printshop']).write({'product_id' : product_id,})
        return True



class xl_printshop_line(models.Model):
    _name = 'xl.printshop.line' 
    _description = 'XL printshop Line' 
    
    def get_optimal(self):
        result = {}
        for line in self:
            try:
                if line.id == line.printshop_id.line_id.id:
                    result[line.id] = 'yes'
                else:result[line.id] = 'no'
            except:pass
            return result 


        laize = fields.Float('Laize')
        poses = fields.Float('Poses')
        ml = fields.Float('Ml')
        m2 =  fields.Float('M²')
        compute =  fields.Boolean('Forcer')
        printshop_id = fields.Many2one('xl.printshop', 'XL printshop', required=False)
        support_line_id = fields.Many2one('printshop.support.line', 'Produit Support', required=False)
        cout = fields.Float('Cout')


class xl_printshop_rigide_line(models.Model):
    _name = 'xl.printshop.rigide.line' 
    _description = 'XL printshop Rigide Line' 
    
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
        printshop_id = fields.Many2one('xl.printshop', 'XL printshop', required=False) 
        rigide_line_id = fields.Many2one('printshop.rigide.line', 'Support Rigide', required=False)
        cout  = fields.Float('Cout')



class xl_printshop_subproduct(models.Model):
    _name = 'xl.printshop.subproduct' 
    _description = 'XL printshop SUBPRODUCT' 
    
    def get_subtotal(self):
        result = {}
        for line in self:
                result[line.id] = line.product_qty*line.unit_price
        return result
    
        name = fields.Char('Designation', size=64, required=False, readonly=False)
        product_id =  fields.Many2one('product.product', 'Product', required=True)
        product_qty = fields.Float('Qte Produit', required=True)
        unit_price =  fields.Float('Prix unitaire', required=True)
        subtotal =  fields.function(get_subtotal, method=True, type='Float',string='Sous total', required=True)
        product_uom =  fields.Many2one('product.uom', 'Product UOM', required=True)
        printshop_id = fields.Many2one('xl.printshop', 'XL printshop', required=False)
           



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
