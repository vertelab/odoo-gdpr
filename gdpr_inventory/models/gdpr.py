import logging
from uuid import uuid4

from odoo import models,  fields,  api,  _
from odoo.exceptions import UserError, AccessError

_logger = logging.getLogger(__name__)

class gdpr_inventory_state(models.Model):
    _name = 'gdpr.inventory.state'

    name = fields.Char(string='Name', required=True)
    sequence = fields.Integer(string='Sequence')
    fold = fields.Boolean()
    technical_name = fields.Char(string='Technical Name')

class gdpr_system(models.Model):
    _name = 'gdpr.system'
    _description = 'GDPR Data System'

    name = fields.Char(string='Name')
    description = fields.Text(string='Description')

class gdpr_subject(models.Model):
    _name = 'gdpr.subject'
    _description = 'GDPR Data Subject'

    name = fields.Char(string='Name')

class gdpr_data_type(models.Model):
    _name = 'gdpr.data_type'
    _description = 'GDPR Data Type'

    name = fields.Char(string='Name')

class gdpr_role(models.Model):
    _name = 'gdpr.role'
    _description = 'GDPR Role'

    name = fields.Char(string='Name')

class gdpr_category(models.Model):
    _name = 'gdpr.category'
    _description = 'GDPR Category'

    sequence = fields.Integer(string='Sequence')
    name = fields.Char(string='Name')
    description = fields.Text(string='Description')
    inventory_ids = fields.One2many(comodel_name='gdpr.inventory',inverse_name='category')

class gdpr_bp(models.Model):
    _name = 'gdpr.bp'
    _description = 'GDPR Business Process'

    sequence = fields.Integer(string='Sequence')
    name = fields.Char(string='Name')

class GdprLog(models.Model):
    _name = "gdpr.log"
    _description = "GDPR model to keep logs of restrictions"

    name = fields.Char(default=str(uuid4()))
    restriction_date = fields.Datetime(default=fields.Datetime.now())
    inventory_id = fields.Many2one(comodel_name="gdpr.inventory")
    responsible = fields.Many2one(comodel_name="res.users")
    restriction_domain = fields.Char()
    restriction_method = fields.Char()

class gdpr_lawsection(models.Model):
    """
    1. Processing shall be lawful only if and to the extent that at least one of the following applies:
=> Article: 9
(a) the data subject has given consent to the processing of his or her personal data for one or more specific purposes;
=> Article: 7
=> Recital: 42,  171
(b) processing is necessary for the performance of a contract to which the data subject is party or in order to take steps at the request of the data subject prior to entering into a contract;
(c) processing is necessary for compliance with a legal obligation to which the controller is subject;
(d) processing is necessary in order to protect the vital interests of the data subject or of another natural person;
(e) processing is necessary for the performance of a task carried out in the public interest or in the exercise of official authority vested in the controller;
(f) processing is necessary for the purposes of the legitimate interests pursued by the controller or by a third party,  except where such interests are overridden by the interests or fundamental rights and freedoms of the data subject which require protection of personal data,  in particular where the data subject is a child.
=> Article: 13,  21
=> Recital: 113,  47
    """
    _name = 'gdpr.lawsection'
    _description = "Lawfullness of processing"

    sequence = fields.Integer(string='Sequence')
    name = fields.Char(string='Name',translate=True)
    description = fields.Html(string='Description',translate=True)
    consent = fields.Boolean(string='Consent')

class gdpr_security(models.Model):
    """

        1. Taking into account the state of the art,  the costs of implementation and the nature,  scope,  context and purposes of processing as well as the risk of varying likelihood and severity for the rights and freedoms of natural persons,  the controller and the processor shall implement appropriate technical and organisational measures to ensure a level of security appropriate to the risk,  including inter alia as appropriate:
        (a) the pseudonymisation and encryption of personal data;
        => Article: 4
        (b) the ability to ensure the ongoing confidentiality,  integrity,  availability and resilience of processing systems and services;
        (c) the ability to restore the availability and access to personal data in a timely manner in the event of a physical or technical incident;
        (d) a process for regularly testing,  assessing and evaluating the effectiveness of technical and organisational measures for ensuring the security of the processing.
        2. In assessing the appropriate level of security account shall be taken in particular of the risks that are presented by processing,  in particular from accidental or unlawful destruction,  loss,  alteration,  unauthorised disclosure of,  or access to personal data transmitted,  stored or otherwise processed.
        => Recital: 75
        3. Adherence to an approved code of conduct as referred to in Article 40 or an approved certification mechanism as referred to in Article 42 may be used as an element by which to demonstrate compliance with the requirements set out in paragraph 1 of this Article.
        4. The controller and processor shall take steps to ensure that any natural person acting under the authority of the controller or the processor who has access to personal data does not process them except on instructions from the controller,  unless he or she is required to do so by Union or Member State law.


        1. Med beaktande av den senaste utvecklingen,  genomförandekostnaderna och behandlingens art,  omfattning,  sammanhang och ändamål samt riskerna,  av varierande sannolikhetsgrad och allvar,  för fysiska personers rättigheter och friheter ska den personuppgiftsansvarige och personuppgiftsbiträdet vidta lämpliga tekniska och organisatoriska åtgärder för att säkerställa en säkerhetsnivå som är lämplig i förhållande till risken,  inbegripet,  när det är lämpligt
        a) pseudonymisering och kryptering av personuppgifter,
        => Artikel: 4
        b) förmågan att fortlöpande säkerställa konfidentialitet,  integritet,  tillgänglighet och motståndskraft hos behandlingssystemen och -tjänsterna,
        c) förmågan att återställa tillgängligheten och tillgången till personuppgifter i rimlig tid vid en fysisk eller teknisk incident,
        d) ett förfarande för att regelbundet testa,  undersöka och utvärdera effektiviteten hos de tekniska och organisatoriska åtgärder som ska säkerställa behandlingens säkerhet.
        2. Vid bedömningen av lämplig säkerhetsnivå ska särskild hänsyn tas till de risker som behandling medför,  i synnerhet från oavsiktlig eller olaglig förstöring,  förlust eller ändring eller till obehörigt röjande av eller obehörig åtkomst till de personuppgifter som överförts,  lagrats eller på annat sätt behandlats.
        => Grundläggande: 75
        3. Anslutning till en godkänd uppförandekod som avses i artikel 40 eller en godkänd certifieringsmekanism som avses i artikel 42 får användas för att visa att kraven i punkt 1 i den här artikeln följs.
        4. Den personuppgiftsansvarige och personuppgiftsbiträdet ska vidta åtgärder för att säkerställa att varje fysisk person som utför arbete under den personuppgiftsansvariges eller personuppgiftsbiträdets överinseende,  och som får tillgång till personuppgifter,  endast behandlar dessa på instruktion från den personuppgiftsansvarige,  om inte unionsrätten eller medlemsstaternas nationella rätt ålägger honom eller henne att göra det.

    """
    _name = 'gdpr.security'
    _description = "Security of processing"

    name = fields.Char()
    description = fields.Text()