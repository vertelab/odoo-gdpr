# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution, third party addon
#    Copyright (C) 2004-2017 Vertel AB (<http://vertel.se>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import models, fields, api, _

import logging
_logger = logging.getLogger(__name__)

# https://www.privacy-regulation.eu
class gdpr_inventory(models.Model):
    _name = 'gdpr.inventory'
    
    name = fields.Char()
    type_of_personal_data (allmänna uppgifter, genetiska uppgifter/Genetic data 34, biometriska uppgifter/biometric data  91, concent, data concerning health, Brottsuppgifter, känsliga uppgifter)
    purpose_limitation
    user_id
    lawsection_id
    lawsection_desc
    concent_desc
    website_desc
    website_published
    restrict_time_days
    restrict_method (erase, hide, de-identify )
    fields_ids
    
    
    
class gdpr_lawsection(models.Model):
    _name = 'gdpr.lawsection'
    _description = "Lawfullness of processing"
    
    name
    description
    concent (true/false)
    

class gdpr_concent(models.Model):
    _name = 'gdpr.concent'
    _description = "Given Concents"
    
    partner_id 
    gdpr_id 
    date_given
    state
    logging
    
    
