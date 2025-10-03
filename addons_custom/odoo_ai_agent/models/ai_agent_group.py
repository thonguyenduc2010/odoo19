from odoo import models, fields, api


class AiAgentGroup(models.Model):
    _name = 'ai.agent.group'
    _description = 'AI Agent Group'
    _rec_name = 'name'

    name = fields.Char(string='Name')
    code = fields.Char(string='Code')