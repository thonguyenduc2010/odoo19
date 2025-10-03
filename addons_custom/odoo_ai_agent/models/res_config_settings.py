import json
import re

import odoo

from odoo import api, fields, models
from odoo.exceptions import ValidationError, UserError
import requests

import logging

_logger = logging.getLogger(__name__)
from .tools import TokenManager


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'


    client_key = fields.Char(string='Client Key', config_parameter="copilot.client_key")
    client_secret = fields.Char(string='Client Secret', config_parameter="copilot.client_secret")
    redirect_url = fields.Char(string='Redirect url', config_parameter="copilot.redirect_url",
                               default="https://api.odoocopilot.ai")
    ai_agent_credit = fields.Float(string="Credit Balance", config_parameter="ai_agent.credit")
    connection_status = fields.Char(string="Connection Status", config_parameter="copilot.connection_status")
    business_summary = fields.Char(string="Business Summary", config_parameter="copilot.business_summary")
    enable_web_search = fields.Boolean(string="Enable Web Search", config_parameter="copilot.enable_web_search")
    enable_adv_decision_making = fields.Boolean(string="Enable Adv Decision Making",
                                                config_parameter="copilot.enable_adv_decision_making")
    enable_custom_architecture = fields.Boolean(string="Enable Custom Architecture",
                                                config_parameter="copilot.enable_custom_architecture")
    client_email = fields.Char(string="Email", config_parameter="copilot.client_email")


    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        try:
            token = TokenManager()
            config_pram = token.get_copilot_config_parameter()
            if config_pram.get('client_key') and config_pram.get('client_secret') and config_pram.get('redirect_url'):
                # self.get_ai_agent()
                # if not self.is_copilot_installed():
                self._get_ai_agent_credit()
                token = TokenManager()
                config_pram = token.get_copilot_config_parameter()
                res.update(
                    ai_agent_credit=config_pram.get('ai_agent_credit'),
                    connection_status=config_pram.get('connection_status'),
                )
        except Exception as e:
            _logger.info(f"Error in credit api {e}")
        return res

    # @api.model
    # def create(self, vals):
    #     res = super(ResConfigSettings, self).create(vals)
    #
    #     if not vals.get('client_key') or not vals.get('client_secret'):
    #         res.connection_status = "Connection failed"
    #         res.ai_agent_credit = 0.00
    #
    #     if vals.get('client_key') and vals.get('client_secret') and self.check_credentials(vals.get('client_key'),
    #                                                                                        vals.get('client_secret')):
    #         previous_token = self.env['client.bearer.token'].search([('active', '=', True)])
    #         for token in previous_token:
    #             token.active = False
    #         # self.env['favorite.questions'].get_favorite_questions_from_server()
    #         # self.get_ai_agent()
    #     elif vals.get('client_key') and res.client_secret and self.check_credentials(vals.get('client_key'),
    #                                                                                  res.client_secret):
    #         previous_token = self.env['client.bearer.token'].search([('active', '=', True)])
    #         for token in previous_token:
    #             token.active = False
    #         # self.env['favorite.questions'].get_favorite_questions_from_server()
    #         # self.get_ai_agent()
    #     elif vals.get('client_secret') and res.client_key and self.check_credentials(res.client_key,
    #                                                                                  vals.get('client_secret')):
    #         previous_token = self.env['client.bearer.token'].search([('active', '=', True)])
    #         for token in previous_token:
    #             token.active = False
    #         # self.env['favorite.questions'].get_favorite_questions_from_server()
    #         # self.get_ai_agent()
    #
    #     return res

    @api.onchange('client_key', 'client_secret')
    def onchange_client_secret(self):
        if (self.client_key or self.client_secret) and (self.client_key == self.client_secret):
            raise ValidationError('Client key and Client Secret can not be same')

    def goto_ai_dashboard(self):
        redirect_url = 'https://odoocopilot.ai'
        url = redirect_url + '/my/portal/client-ai-dashboard'

        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
        }

    def get_client_key(self):
        redirect_url = 'https://odoocopilot.ai'
        url = redirect_url + '/web/signup'

        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
        }

    def _display_notification(self, message, notification_type):
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': notification_type,
                'message': message,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }

    def get_connection(self):
        token = TokenManager()
        config_pram = token.get_copilot_config_parameter()
        if not config_pram.get('client_key'):
            raise ValidationError('Client key not found')
        if not config_pram.get('client_secret'):
            raise ValidationError('Client secret not found')
        if not config_pram.get('redirect_url'):
            raise ValidationError('Redirect Url not found')
        url = config_pram.get('redirect_url') + '/get/api-v1/connection-test'
        _logger.info(url)
        headers = {
            'Content-Type': 'application/json',
            'client-key': config_pram.get('client_key'),
            'client-secret': config_pram.get('client_secret')
        }
        response = requests.get(url, headers=headers)
        # Handle the response
        if response.status_code != 200:
            return self._display_notification(
                message=f"Failed status code: {response.status_code}",
                notification_type='danger'
            )

        result = response.json()

        # Check for success or error messages in the response
        if result.get('success_msg'):
            return self._display_notification(
                message=result.get('success_msg'),
                notification_type='success'
            )
        elif result.get('error_msg'):
            return self._display_notification(
                message=result.get('error_msg'),
                notification_type='danger'
            )

    def get_sync_database_configuration(self):
        # Get the company information
        company = self.env.user.company_id
        if not company.my_database:
            raise ValidationError('My database not found')
        if not company.username:
            raise ValidationError('Username not found')
        if not company.password:
            raise ValidationError('Password not found')
        if not company.host:
            raise ValidationError('Host not found')
        if not company.port:
            raise ValidationError('Port not found')

        # Get available bearer token
        bearer_token = self._get_available_bearer_token()

        # Check if the bearer token is available
        if not bearer_token:
            return self._display_notification(
                message="Valid Bearer Token not found",
                notification_type='danger'
            )

        # Set the request headers and data
        url = company.redirect_url + '/get/api-v1/database-configuration'
        headers = {
            'Content-Type': 'application/json',
            'bearer-token': bearer_token
        }
        data = {
            "my-database": company.my_database,
            "username": company.username,
            "password": company.password,
            "host": company.host,
            "port": company.port
        }

        # Send the request
        response = requests.get(url, json=data, headers=headers)

        # Handle the response
        if response.status_code != 200:
            return self._display_notification(
                message=f"Failed status code: {response.status_code}",
                notification_type='danger'
            )

        result = response.json()

        # Check for success or error messages in the response
        if result.get('success_msg'):
            return self._display_notification(
                message=result.get('success_msg'),
                notification_type='success'
            )
        elif result.get('error_msg'):
            return self._display_notification(
                message=result.get('error_msg'),
                notification_type='danger'
            )

    def _get_ai_agent_credit(self):
        try:
            header = TokenManager()
            config_pram = header.get_copilot_config_parameter()
            url = config_pram.get('redirect_url') + '/get/api-v1/ai-agent/get-credit-description'
            _logger.info(url)
            response = requests.get(url, headers=header.get_headers())
            if response.status_code == 200:
                result = response.json()
                _logger.info(result)
                self.env['ir.config_parameter'].sudo().set_param('ai_agent.credit',
                                                                 result.get('total_credit_availability'))
                self.env['ir.config_parameter'].sudo().set_param('copilot.connection_status', "Connected")

            else:
                self.env['ir.config_parameter'].sudo().set_param('ai_agent.credit', 0.00)
                self.env['ir.config_parameter'].sudo().set_param('copilot.connection_status', "Connection failed")

        except Exception as e:
            self.env['ir.config_parameter'].sudo().set_param('ai_agent.credit', 0.00)
            self.env['ir.config_parameter'].sudo().set_param('copilot.connection_status', "Connection failed")

    def buy_credit(self):
        redirect_url = 'https://odoocopilot.ai'
        url = redirect_url + '/#s_home_credit_packages'

        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
        }

    def check_credentials(self, client_key, client_secret):
        # api_url = self.env['ir.config_parameter'].sudo().get_param('copilot.redirect_url')
        # if not api_url:
        #     self.env['ir.config_parameter'].sudo().set_param('copilot.redirect_url', "https://api.odoocopilot.ai")
        token = TokenManager()
        config_pram = token.get_copilot_config_parameter()
        url = config_pram.get('redirect_url') + '/get/api-v1/connection-test'
        headers = {
            'Content-Type': 'application/json',
            'client-key': client_key,
            'client-secret': client_secret
        }
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return self._display_notification(
                message=f"Failed status code: {response.status_code}",
                notification_type='danger'
            )

        result = response.json()
        if result.get('success_msg'):
            self.env['ir.config_parameter'].sudo().set_param('copilot.client_key', client_key)
            self.env['ir.config_parameter'].sudo().set_param('copilot.client_secret', client_secret)
            return True
        elif result.get('error_msg'):
            raise ValidationError("Credentials not matching!! Please provide a valid client_key and client_secret.")

    def sync_database(self):
        try:
            header = TokenManager()
            config_pram = header.get_copilot_config_parameter()
            tables = self.env['res.users'].get_user_accessed_model_info()
            url = config_pram.get('redirect_url') + '/sync/api-v1/client-allowed-models'
            data = {
                "tables": tables,
            }
            response = requests.get(url, json=data, headers=header.get_headers())
            if response.status_code != 200:
                return self._display_notification(
                    message=f"Failed status code: {response.status_code}",
                    notification_type='danger'
                )
            result = response.json()
            if result.get('success_msg'):
                return self._display_notification(
                    message=result.get('success_msg'),
                    notification_type='success'
                )
            elif result.get('error_msg'):
                return self._display_notification(
                    message=result.get('error_msg'),
                    notification_type='danger'
                )
        except Exception as e:
            return self._display_notification(
                message=e,
                notification_type='danger'
            )

    def is_copilot_installed(self):
        module = self.env['ir.module.module'].sudo().search([
            ('name', '=', 'copilot'),
            ("state", "in", ["installed", "to upgrade", "to remove"])
        ], limit=1)
        return bool(module)

    def get_ai_agent(self):
        try:
            header = TokenManager()
            config_pram = header.get_copilot_config_parameter()
            url = config_pram.get('redirect_url') + '/get/api-v1/get-ai-agents'
            data = {}
            response = requests.get(url, json=data, headers=header.get_headers())
            if response.status_code != 200:
                return self._display_notification(
                    message=f"Failed status code: {response.status_code}",
                    notification_type='danger'
                )
            data = response.json()
            result = json.loads(data['result'])
            ai_agents = result.get('ai_agents')
            for ai_agent in ai_agents:
                val = {}
                name = ai_agent.get('agent_name')
                if name:
                    val['name'] = name

                agent_code = ai_agent.get('agent_code')
                if agent_code:
                    val['agent_code'] = agent_code

                description = ai_agent.get('description')
                if description:
                    val['description'] = description

                cost = ai_agent.get('cost')
                if cost:
                    val['cost'] = cost

                agent_group = ai_agent.get('agent_group')
                if agent_group:
                    val['agent_group'] = agent_group

                agent_type = ai_agent.get('agent_type')
                if agent_type:
                    category = self.env['agent.category'].sudo().search([('name', '=', agent_type)], limit=1)
                    if not category:
                        category = self.env['agent.category'].sudo().create({'name': agent_type})
                    val['category_id'] = category.id

                module_list = ai_agent.get('module_list')
                if module_list:
                    module_ids = self.env["ir.module.module"].sudo().search([('name', 'in', module_list)]).ids
                    val['module_ids'] = [(6, 0, module_ids)]

                class_list = ai_agent.get('class_list')
                if class_list:
                    local_model_ids = self.env["ir.model"].sudo().search([('model', 'in', class_list)]).ids
                    val['model_ids'] = [(6, 0, local_model_ids)]

                if agent_code:
                    existing_agent = self.env['copilot.agent.dashboard'].sudo().search([('agent_code', '=', agent_code)], limit=1)
                    if existing_agent:
                        existing_agent.sudo().write(val)
                    else:
                        self.env['copilot.agent.dashboard'].sudo().create(val)

            if result.get('success_msg'):
                return self.env.ref('odoo_ai_agent.action_copilot_agent_dashboard').sudo().read()[0]
                # return self._display_notification(
                #     message=result.get('success_msg'),
                #     notification_type='success'
                # )
            elif result.get('error_msg'):
                return self._display_notification(
                    message=result.get('error_msg'),
                    notification_type='danger'
                )
        except Exception as e:
            return self._display_notification(
                message=e,
                notification_type='danger'
            )

    def get_agents(self):
        url = 'https://apps.odoo.com/apps/modules/17.0/odoo_ai_agent'
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
        }

    def user_configure(self):
        url = "https://odoocopilot.ai/api-v1/user-configuration"
        email = self.env['ir.config_parameter'].sudo().get_param('copilot.client_email')
        if email:
            try:
                match = re.match(r"(\d+)(?:\.\d+)?(\+e)?", odoo.release.version)
                version_number = match.group(1)
                edition_flag = match.group(2) or ""
                data = {
                    "email": email,
                    "odoo_version": version_number,
                    "odoo_edition": 'enterprise' if edition_flag else 'community'
                }
                headers = {
                    "Content-Type": "application/json",
                }
                response = requests.post(url, json=data, headers=headers)
                if response.status_code != 200:
                    return self._display_notification(
                        message=f"Failed status code: {response.status_code}",
                        notification_type='danger'
                    )

                data = response.json()
                if data.get('error'):
                    return self._display_notification(
                        message=data.get('error',{}).get('data',{}).get('arguments',[]),
                        notification_type='danger'
                    )
                result = data['result']
                if result.get('success_msg'):
                    self.env['ir.config_parameter'].set_param('copilot.client_key', result.get('client_key'))
                    self.env['ir.config_parameter'].set_param('copilot.client_secret', result.get('client_secret'))
                    return self._display_notification(
                        message=result.get('success_msg'),
                        notification_type='success'
                    )
                elif result.get('error_msg'):
                    return self._display_notification(
                        message=result.get('error_msg'),
                        notification_type='danger'
                    )
                elif result.get('error'):
                    return self._display_notification(
                        message=result.get('error'),
                        notification_type='danger'
                    )

            except Exception as e:
                return self._display_notification(
                    message=e,
                    notification_type='danger'
                )
        else:
            return self._display_notification(
                message='User Email not given!!',
                notification_type='danger'
            )