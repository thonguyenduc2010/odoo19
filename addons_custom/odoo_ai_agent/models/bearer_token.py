from odoo import api, fields, models


class BearerToken(models.Model):
    _name = 'client.bearer.token'
    _description = 'Bearer Token'

    token = fields.Char(string='Bearer Token')
    expiry = fields.Datetime(string='Expiration Date')
    expiration = fields.Float(string='Expiration(sec.)')
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user)
    active = fields.Boolean(string='Active', default=True)
