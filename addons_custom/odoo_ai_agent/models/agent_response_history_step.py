import base64
import io
import re

import pandas as pd

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import json
from .tools import TokenManager, ResponseManager
response_manager = ResponseManager()

class AgentResponseHistoryStep(models.Model):
    _name = 'agent.response.history.step'
    _description = 'Agent Response History Step'
    _rec_name = 'name'
    _order = 'step asc'

    name = fields.Char(string='Name')
    response = fields.Text(string='Response')
    agent_response_history_id = fields.Many2one('agent.response.history' ,string='Agent Response History')
    sequence = fields.Integer(string='Sequence')
    title = fields.Char(string='Title')
    # copilot_message_id = fields.Many2one('copilot.message', string='Copilot Message')
    special_id = fields.Char(string='Special ID')
    text = fields.Text(string='Text')
    text_response = fields.Html(string='Text Response')
    final_step_text_response = fields.Html(string='Final Step Text Response')
    output_response = fields.Text(string='Output Response')
    final_step_output_response = fields.Text(string='Final Step Output Response')
    output_column = fields.Text(string='Output Column')
    full_response = fields.Text(string='Full Response')
    final_step = fields.Boolean(string='Final Step')
    current_role = fields.Char(string='Role')
    next_role = fields.Char(string='Next Role')
    max_step = fields.Integer(string='Max Step')
    step = fields.Integer(string='Step')
    loading_message = fields.Char(string='Loading Message')
    no_animate = fields.Boolean(string='No Animate')
    data_excel_id = fields.Binary(string='Data Excel')
    customer_feedback_status = fields.Selection([('like', 'Like'), ('unlike', 'Unlike')], string='Customer Feedback Status')
    customer_feedback = fields.Text(string='Customer Feedback')
    python_functions = fields.Text(string="Python Function")
    reference_url = fields.Char(string='Reference URL')
    has_user_confirmation = fields.Boolean(string='Has User Confirmation')
    functional_response = fields.Text(string='Functional Response')
    ai_agent_object_reference_ids = fields.One2many('ai.agent.object.reference','agent_response_history_step_id', string='AI Agent Object Reference')
    template_id = fields.Char(string='Template ID')
    related_document_ids = fields.Char(string='Related Document IDs')
    related_model = fields.Char(string='Related Model')
    copilot_agent_id = fields.Many2one('copilot.agent.dashboard', string="Agent", related="agent_response_history_id.copilot_agent_id", store=True)

    @api.model
    def create(self, vals):
        record = super().create(vals)
        if not record.name:
            record.name = f"[{record.copilot_agent_id.name if record.copilot_agent_id else ''}]-{fields.Date.today().isoformat().replace('-', '')}-{record.title.split(':', 1)[1].strip() if record.title else ''}"
        return record

    def apply_now(self):
        """This method is called when the 'View Response' button is clicked."""
        # Logic to handle the response view can be added here.
        # For now, it just returns a message.
        raise UserError(_("This feature is not implemented yet. Please check back later."))

    def confirm_and_review(self):
        if self.agent_response_history_id.copilot_agent_id.agent_code == "001":
            if not self.related_document_ids:
                purchase_data = eval(self.output_response)
                purchase_ids = list()
                for pd in purchase_data:
                    order_lines = []
                    for product in pd.get('product_list', []):
                        product_id = self.env['product.product'].browse(int(product.get('product_id')))
                        purchase_order_line_vals = {
                            'product_id': product_id.id,
                            'product_qty': product.get('quantity'),
                            'price_unit': product.get('price'),
                        }
                        order_lines.append((0, 0, purchase_order_line_vals))

                    purchase_order_id = self.env['purchase.order'].create({
                        'partner_id': pd.get('vendor_info').get('vendor_id'),
                        'date_order': pd.get('vendor_info').get('expected_delivery'),
                        'date_planned': pd.get('vendor_info').get('expected_delivery'),
                        'order_line': order_lines,
                    })
                    purchase_order_id.message_post(body="Created from AI Agent With Forcasted Information")
                    purchase_ids.append(purchase_order_id.id)
                    pd['vendor_info']['purchase_reference'] = purchase_order_id.name
                    menu = self.env.ref('odoo_ai_agent.odoo_ai_agent_menu_root').sudo().read()[0].get('id')
                    url = f"/web#id={purchase_order_id.id}&model=purchase.order&view_type=form&cids=1&menu_id={menu}"
                    pd['vendor_info']['purchase_url'] = url


                self.output_response = purchase_data
                self.related_model = 'purchase.order'
                self.related_document_ids = json.dumps(purchase_ids)

            else:
                purchase_ids = eval(self.related_document_ids)

            self.agent_response_history_id.copilot_agent_id.status = 'done'
            self.agent_response_history_id.action_state = 'done'

            # creating manufacturing order
            prev_steps_data = self.agent_response_history_id.get_response_line_data(step=6)
            manufacturing_product_list = prev_steps_data.get('step_3', {}).get('manufacturing_product_list',[])

            for item in manufacturing_product_list:
                product = self.env['product.product'].browse(item['product_id'])

                val = {
                    'product_id': product.id,
                    'product_qty': item.get('recommended_manufacture', 0),
                    'product_uom_id': product.uom_id.id,
                }

                bom = self.env['mrp.bom'].search([('product_tmpl_id', '=', product.product_tmpl_id.id)], limit=1)
                if bom:
                    val['bom_id'] = bom.id

                self.env['mrp.production'].create(val)


            return {
                'type': 'ir.actions.act_window',
                'name': 'Purchase Orders',
                'res_model': 'purchase.order',
                'view_mode': 'list,form',
                'domain': [('id', 'in', purchase_ids)],
                'target': 'current',
            }

        elif self.agent_response_history_id.copilot_agent_id.agent_code == "003":
            output_response = eval(self.output_response)
            product_supplier_info = self.env['product.supplierinfo']

            if output_response:
                supplier_info_ids = []
                for item in output_response:
                    product_id = self.env['product.product'].sudo().browse(int(item.get('product_info',{}).get('product_id')))
                    product_tmpl_id = product_id.product_tmpl_id if product_id else False
                    if not product_tmpl_id:
                        continue
                    for vendor in item.get('vendor_list',[]):
                        vendor_id = vendor.get('vendor_id')
                        if not vendor_id:
                            continue
                        found_product_supplier_info = product_supplier_info.sudo().search([("date_start", "=", False),("date_end", "=", False),('product_tmpl_id', '=', product_tmpl_id.id),('partner_id', '=', vendor_id)])
                        if found_product_supplier_info:
                            for info in found_product_supplier_info:
                                # info.delay = vendor.get('suggested_lead_time')
                                # info.price = vendor.get('suggested_price')
                                info.calculated_delay = vendor.get('suggested_lead_time')
                                info.calculated_price = vendor.get('suggested_price')
                                supplier_info_ids.append(info.id)

                self.agent_response_history_id.copilot_agent_id.status = 'done'
                self.agent_response_history_id.action_state = 'done'

                return {
                    'type': 'ir.actions.act_window',
                    'name': 'Supplier Info',
                    'res_model': 'product.supplierinfo',
                    'view_mode': 'list,form',
                    'domain': [('id', 'in', supplier_info_ids)],
                    'target': 'current',
                }
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'type': 'danger',
                        'message': 'No Output Response Found!!',
                        'next': {'type': 'ir.actions.act_window_close'},
                    }
                }

        elif self.agent_response_history_id.copilot_agent_id.agent_code == "007":
            if self.agent_response_history_id.data_line_product:
                output_response = eval(self.output_response)
                if output_response:
                    po_ids = []
                    for vendor, products in output_response.items():
                        if vendor == 'timestamp':
                            continue
                        vendor_name = vendor.removeprefix("Vendor - ").strip()
                        found_vendor = self.env['res.partner'].search([('name', '=', vendor_name),("supplier_rank", ">", 0)], limit=1)
                        if not found_vendor:
                            raise UserError(f"Vendor '{vendor_name}' not found!")
                        purchase_order = self.env['purchase.order'].create({
                            'partner_id': found_vendor.id,
                            'order_line': [],
                        })
                        order_lines = []
                        for product in products:
                            order_lines.append((0, 0, {
                                'product_id': product['product_id'],
                                'product_qty': product['product_qty'],
                                'price_unit': product['price_unit'],
                                'name': product['product_name'],
                                'date_planned': fields.Datetime.now(),
                            }))
                        purchase_order.write({'order_line': order_lines})
                        po_ids.append(purchase_order.id)
                    return {
                        'type': 'ir.actions.act_window',
                        'name': 'Purchase Orders',
                        'res_model': 'purchase.order',
                        'view_mode': 'list,form',
                        'domain': [('id', 'in', po_ids)],
                        'target': 'current',
                    }
                else:
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'type': 'danger',
                            'message': 'No Output Response Found!!',
                            'next': {'type': 'ir.actions.act_window_close'},
                        }
                    }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'danger',
                    'message': 'No data_line_product Response Found!!',
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }


    def process_item(self, item):
        pattern = re.compile(r'^[0-9.,-]+$')
        if isinstance(item, float):
            return round(item, 2)
        item_str = str(item).replace(',', '')
        is_match = bool(pattern.match(item_str))
        return round(float(item_str), 2) if is_match else item


    def calling_df_to_html(self, value):
        df = response_manager.dict_to_table(value)
        text_response = response_manager.df_to_html(df)
        df = df.apply(lambda col: col.round(2) if col.dtype == 'float64' else col)
        return df,text_response

    def get_list_of_df(self):
        table_data = []
        output_response = self.output_response if not self.final_step else self.final_step_output_response
        if output_response:
            output_dictionary = eval( output_response,     {
                                        "datetime": __import__("datetime"),
                                        "relativedelta": __import__("dateutil.relativedelta", fromlist=["relativedelta"]).relativedelta,
                                        "pytz": __import__("pytz")
                                    })
            full_response = ""
            if output_dictionary and  isinstance(output_dictionary, dict):
                for main_key, main_value in output_dictionary.items():
                    if main_key == 'timestamp':
                        continue
                    if isinstance(main_value, dict):
                        if all(isinstance(item, (int, float)) for item in main_value.keys()):
                            list_of_dic = []
                            list_of_dic.extend(main_value.values())
                            df, text_response = self.calling_df_to_html(list_of_dic)
                            full_response = full_response + f"""<h3>{main_key.replace("_", " ").title()}</h3><br/>{text_response}<br/>"""
                            table_data.append((main_key.replace("_", " ").title(), df))
                            continue
                        for key, value in main_value.items():
                            if isinstance(value, (dict, list)):
                                if not value:
                                    continue
                                if isinstance(value, dict):
                                    if all(isinstance(item, (int, float)) for item in value.keys()):
                                        list_of_dic = []
                                        list_of_dic.extend(value.values())
                                        df, text_response = self.calling_df_to_html(list_of_dic)
                                        full_response = full_response + f"""<h3>{main_key.replace("_", " ").title()}</h3><br/>{text_response}<br/>"""
                                        table_data.append((main_key.replace("_", " ").title(), df))
                                        continue
                                df, text_response = self.calling_df_to_html(value)
                                if "table" in text_response:
                                    full_response = full_response + f"""<h3>{main_key.replace("_", " ").title()} For {str(key).replace("_", " ").title()}</h3><br/>{text_response}<br/>"""
                                    table_data.append((main_key.replace("_", " ").title() + ' For ' + str(key).replace("_", " ").title(), df))
                                else:
                                    full_response = full_response + f"""<h3>{main_key.replace("_", " ").title()} For {str(key).replace("_", " ").title()}:- {text_response}</h3><br/>"""
                                    table_data.append((main_key.replace("_", " ").title() + ' For ' + str(key).replace("_", " ").title(), df))
                            else:
                                full_response = full_response + f"""<h3>{main_key.replace("_", " ").title()} For {str(key).replace("_", " ").title()}:- {value}</h3><br/>"""
                                df = pd.DataFrame([{main_key.replace("_", " ").title() + ' For ' + str(key).replace("_"," ").title(): self.process_item(value)}])
                                table_data.append((main_key.replace("_", " ").title() + ' For ' + str(key).replace("_", " ").title(), df))
                    elif isinstance(main_value, list):
                        df, text_response = self.calling_df_to_html(main_value)
                        full_response = full_response + f"""<h3>{main_key.replace("_", " ").title()}</h3><br/>{text_response}<br/>"""
                        table_data.append((main_key.replace("_", " ").title(), df))
                    else:
                        full_response = full_response + f"""<h3>{main_key.replace("_", " ").title()}:- {main_value}<br/></h3>"""
                        df = pd.DataFrame([{main_key.replace("_", " ").title(): self.process_item(main_value)}])
                        table_data.append((main_key.replace("_", " ").title(), df))
        return table_data


    def action_download_excel(self):
        self.ensure_one()
        try:
            if not self.output_response or (self.final_step and not self.final_step_output_response):
                raise UserError("No output_response.")
            table_data = self.get_list_of_df()
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                workbook = writer.book
                worksheet = workbook.add_worksheet(f"{self.title}")
                writer.sheets[f"{self.title}"] = worksheet

                row = 0
                bold_format = workbook.add_format({'bold': True, 'font_size': 14})

                for key, df in table_data:
                    worksheet.write(row, 0, key, bold_format)
                    row += 1

                    df.to_excel(writer, sheet_name=f"{self.title}", startrow=row, index=False)
                    row += len(df) + 3

            output.seek(0)
            file_data = base64.b64encode(output.read())
            output.close()

            self.data_excel_id = file_data
            file_name = f"{self.title}.xlsx"

            return {
                'type': 'ir.actions.act_url',
                'url': f"/web/content?model=agent.response.history.step&download=true&field=data_excel_id&filename={file_name}&id={self.id}",
                'target': 'new',
            }
        except Exception as e:
            raise UserError(f"Failed to download the file: {e}")

    def action_download_pdf(self):
        data = {
            'create_date': self.agent_response_history_id.create_date,
            'user': self.agent_response_history_id.create_uid,
            'custom_message': self.agent_response_history_id.copilot_agent_id.name,
            'title': self.title,
            'text': self.text if self.step == 1 else False,
            'text_response': self.text_response if not self.final_step else self.final_step_text_response,}
        return  self.env.ref('odoo_ai_agent.action_chat_message_response_line_model').sudo().report_action([], data=data)
    

    def run_manually(self):
        agent_response_history_id = self.agent_response_history_id
        output_response = agent_response_history_id.get_response_line_data(self.step)
        output_dictionary = agent_response_history_id.execute_python_function_multi(self.python_functions, output_response)
