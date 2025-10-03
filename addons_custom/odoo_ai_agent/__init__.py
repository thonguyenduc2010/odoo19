import json
import requests
import re
import odoo
import logging
import os
from odoo.http import request
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)
from . import models
from . import wizard


def pre_init_url(env):
    api_url = env['ir.config_parameter'].get_param('copilot.redirect_url')
    if not api_url:
        env['ir.config_parameter'].set_param('copilot.redirect_url', "https://api.odoocopilot.ai")
    user = env['res.users'].browse(request.uid)
    if not user.partner_id.email:
        raise UserError(f"Please set email for the user {user.name} before installing the module.")
    license_dir = f"{odoo.addons.odoo_ai_agent.__path__[0]}/static/src/lib/licenses.lic"
    if not os.path.exists(license_dir):
        raise UserError("Module seems to be corrupted, Please purchase the original module from Odoo App Store.")


def read_license_file(env):
    license_dir = f"{odoo.addons.odoo_ai_agent.__path__[0]}/static/src/lib/licenses.lic"
    if not os.path.exists(license_dir):
        return None  # File does not exist
    try:
        with open(license_dir, "r") as f:
            data = json.load(f)  # Parse JSON content
        return data
    except Exception as e:
        return None

def post_init_hook(env):
    user = env['res.users'].browse(request.uid)
    email = user.partner_id.email
    db_uuid = env['ir.config_parameter'].sudo().get_param('database.uuid')
    environ = request.httprequest.environ
    admin_partner = user.partner_id
    address_parts = [
        admin_partner.street,
        admin_partner.street2,
        admin_partner.city,
        admin_partner.state_id.name if admin_partner.state_id else None,
        admin_partner.country_id.name if admin_partner.country_id else None,
    ]
    address = ', '.join([part for part in address_parts if part])

    license_dir = f"{odoo.addons.odoo_ai_agent.__path__[0]}/static/src/lib/licenses.lic"
    if not os.path.exists(license_dir):
        license_data = {"license_key": "", "status": "invalid"}
    try:
        with open(license_dir, "r") as f:
            license_data = json.load(f)  # Parse JSON content
    except Exception as e:
        license_data = {"license_key": "", "status": "invalid"}

    url = "https://odoocopilot.ai/api-v1/user-configuration"
    # email = env['ir.config_parameter'].sudo().get_param('copilot.client_email')

    if email:
        try:
            # Extract version and edition
            match = re.match(r"(\d+)(?:\.\d+)?(\+e)?", odoo.release.version)
            version_number = match.group(1)
            edition_flag = match.group(2) or ""

            data = {
                "name": user.partner_id.name,
                "email": email,
                "odoo_version": version_number,
                "odoo_edition": 'enterprise' if edition_flag else 'community',
                "db_uuid": db_uuid,
                'domain': environ.get('HTTP_HOST') or environ.get('SERVER_NAME'),
                'ip_address': environ.get('REMOTE_ADDR'),
                'port': environ.get('REMOTE_PORT'),
                'address': address,
                'license_info': license_data
            }

            headers = {"Content-Type": "application/json"}
            response = requests.post(url, json=data, headers=headers, timeout=10)

            if response.status_code != 200:
                _logger.error("User configure API failed with status: %s", response.status_code)
                return

            data = response.json()
            if data.get('error'):
                _logger.info(data.get('error', {}).get('data', {}).get('arguments', []))

            result = data.get("result", {})
            _logger.info("User configure API result: %s", result)

            if result.get("success_msg"):
                try:
                    license_data = {
                        "license_key": result.get("license_key", ""),
                        "status": "valid"
                    }
                    with open(license_dir, "w") as f:
                        json.dump(license_data, f, indent=4)
                except Exception as e:
                    _logger.error("Failed to write license file: %s", e)
                env['ir.config_parameter'].sudo().set_param("copilot.client_key", result.get("client_key"))
                env['ir.config_parameter'].sudo().set_param("copilot.client_secret", result.get("client_secret"))
                env['ir.config_parameter'].sudo().set_param("copilot.client_email", email)
                _logger.info("User configured successfully: %s", result.get("success_msg"))
                '''calling get ai agent api'''
                try:
                    bearer_token_url = env['ir.config_parameter'].sudo().get_param('copilot.redirect_url') + '/get/api-v1/bearer-token'
                    headers = {
                        'Content-Type': 'application/json',
                        'client-key': result.get("client_key"),
                        'client-secret': result.get("client_secret")
                    }
                    response = requests.get(bearer_token_url, headers=headers)
                    data = response.json()
                    if 'error_msg' in data:
                        _logger.info(data['error_msg'])
                    if 'token' in data:
                        env['client.bearer.token'].sudo().create({
                            'token': data.get('token'),
                            'expiry': data.get('expiry'),
                            'expiration': data.get('expiration')
                        })

                    elif result.get('error_msg'):
                        _logger.error(result.get('error_msg'))
                except Exception as e:
                    _logger.error(e)

            elif result.get("error_msg"):
                _logger.error("User configure error_msg: %s", result.get("error_msg"))

            elif result.get("error"):
                _logger.error("User configure error: %s", result.get("error"))

        except Exception as e:
            _logger.exception("User configure API failed: %s", e)

    else:
        _logger.error("User Email not given in system parameter (copilot.client_email)!")

def _uninstall_hook_odoo_ai_agent(env):
    module = env['ir.module.module'].sudo().search([('name', '=', 'copilot'),("state", "in", ["installed", "to upgrade", "to remove"])], limit=1)
    if not module:
        env['ir.config_parameter'].sudo().search([('key', '=', 'copilot.redirect_url')]).unlink()
        env['ir.config_parameter'].sudo().search([('key', '=', 'copilot.client_key')]).unlink()
        env['ir.config_parameter'].sudo().search([('key', '=', 'copilot.client_secret')]).unlink()
        env['ir.config_parameter'].sudo().search([('key', '=', 'copilot.connection_status')]).unlink()
    env['ir.config_parameter'].sudo().search([('key', '=', 'copilot.client_email')]).unlink()
    env['ir.config_parameter'].sudo().search([('key', '=', 'ai_agent.credit')]).unlink()