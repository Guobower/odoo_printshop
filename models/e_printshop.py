# -*- coding: utf-8 -*-
##############################################################################
#
#    odoo, Open Source Management Solution
#    Copyright (C) 2017 AKENOO All Rights Reserved
#    authors: tariklallouch@gmail.com
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
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

class eprintshopSetting(models.Models):
    _name = "eprintshop.setting"
    _description = "setting for ecommerce printshop"


    name = fields.Char('Setting eprintshop Profil', size=64, required=True, readonly=False)
    attribut_ids = fields.One2many('product.attribut', 'name','option product ecommerce')
    description = fields.Text('Description')
