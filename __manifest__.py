# -*- coding: utf-8 -*-

{
    'name': "Vertical printing industry",
    'version': '2.0',
    'author' : "Akenoo",
    'depends': [
        'base',
        'product',
        'mrp',
        'sale',
        'account',
    ],
    'category': 'Specific Modules/Printshop',
    'description': """
 This module allows:
   * Calculate production cost of machine prints OFFSET
   * Calculation of unit selling price
   * Possibility of adding new by-products of finiton:
   * Calculation of all combinations possible support-machine is choose the machine and the support which gives the minimum cost
   * Automatic generation of nomenclature
   * Generate product with a single click
   * Possibility of printing the Quote
  """,
    # data files always loaded at installation
    'data': [
        "security/offset_printshop_security.xml",
        "security/ir.model.access.csv",
        #"view/offset_printshop_sequence.xml",
        "view/product_view.xml",
        "view/offset_printshop_view.xml",
        "view/offset_printshop_parent_view.xml",
        "view/mrp_constante_view.xml",
        "view/printshop_pricelist.xml",
      "report/mrp_report_printshop.xml"


    ],
    # data files containing optionally loaded demonstration data
    'demo': [
        # 'demo_data.xml',
    ],
    "active": False,
    'installable': True,
    'auto_install': False,
    'application': True,
}