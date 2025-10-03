from odoo import models,fields,api


class AiAgentObjectReference(models.Model):
    _name = 'ai.agent.object.reference'
    _description = 'AI Agent Object Reference'

    sequence = fields.Integer(string='Sequence')
    output = fields.Text(string='Output')
    reference_name = fields.Char(string='Reference Name')
    reference_id = fields.Integer(string='Reference ID')
    agent_response_history_step_id = fields.Many2one( 'agent.response.history.step', string='Agent Response History Step ID')