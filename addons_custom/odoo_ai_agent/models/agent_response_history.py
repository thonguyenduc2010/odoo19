import base64
import io
import logging
from lxml import etree
import pandas as pd
from dateutil.relativedelta import relativedelta
from odoo import fields, models, api, _
import requests
import re
from .tools import TokenManager, ResponseManager
from odoo.http import request
import json
_logger = logging.getLogger(__name__)
from odoo.exceptions import ValidationError, UserError, AccessError
import traceback
import ast

ImportString = """
import re
import calendar
import io
import ast
import time
import json
import random
import math
from math import ceil
import base64
import itertools
from itertools import chain
import pytz
import numpy as np
from pytz import timezone, UTC, utc
from babel.dates import format_datetime, format_date
from odoo.exceptions import UserError, ValidationError, MissingError
from collections import defaultdict, namedtuple
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.osv import expression
from odoo.http import request
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_is_zero, float_compare, float_round, format_date, groupby, str2bool
from string import digits
from werkzeug.urls import url_encode
from markupsafe import Markup, escape
from odoo.tools.safe_eval import safe_eval
from odoo.tools.date_utils import get_timedelta
from odoo.tools.misc import DEFAULT_SERVER_DATE_FORMAT
from odoo.tools.misc import format_duration
from odoo.addons.odoo_ai_agent.models.call_back import search_internet_and_interpret_results_with_llm, DecisionMakingAgent, ForecastProductSale, CalculateLeadTime


class OdooAIAgent:
"""

response_manager = ResponseManager()

class AgentResponseHistory(models.Model):
    _name = 'agent.response.history'
    _description = 'Agent Response History'
    _rec_name = 'action_name'
    _order = 'id desc'

    run_time_of = fields.Datetime(string='Run Time of')
    response = fields.Html(string='Response History')
    description = fields.Text(string='Description')
    action_type = fields.Selection([('manual','Manual'),('automatic','Automatic')], string='Action Type')
    copilot_agent_id = fields.Many2one('copilot.agent.dashboard', string='Copilot Agent')
    copilot_agent_status = fields.Selection(related='copilot_agent_id.status', string='Copilot Agent Status')
    state = fields.Selection([('waiting','Waiting'),('in_progress','In Progress'),('done','Done'),('failed','Failed')], string='Status')
    action_state = fields.Selection([('to_do','To Do'),('done','Done')], string='Action Status', default="to_do")
    action_name = fields.Char(string='Action Name')
    action_description = fields.Text(string='Action Description')
    agent_response_history_step_ids = fields.One2many('agent.response.history.step', 'agent_response_history_id',string='Response History Steps')
    complexity_level = fields.Char(string="Complexity Level")
    odoo_version = fields.Selection(
        string="Odoo Version",
        selection=[
            ('10', "10"),('11', "11"),('12', "12"),('13', "13"),
            ('14', "14"),('15', "15"),('16', "16"),('17', "17"),('18', "18"),('19', "19"),('20', "20"),
        ],
    )
    odoo_edition = fields.Selection(
        string="Odoo Edition",
        selection=[
            ('community', "Community"),('enterprise', "Enterprise"),
        ],
    )
    server_ref_id = fields.Integer(string="Server Ref Id")
    data_excel_ids = fields.Binary(string='Data Excel')
    data_line_product = fields.Text(string='Product Data Line')

    def apply_now(self):
        if self.env.context.get('from_cron'):
            self.action_type = 'automatic'
        else:
            self.action_type = 'manual'
        try:
            role = "ODOO Functional Consultant"
            step = 0
            max_steps = 0
            answer = self._get_server_answer(role, step, max_steps, None, None)
            print(f"Answer from server: {answer}")
            agent_response_step_id = self.create_response_line(answer)
            _logger.info(f"Agent Response Step ID: {agent_response_step_id.id}  (Step: {step+1} / {max_steps})")

            while True:
                role = "ODOO Developer"
                step = step+1
                max_steps = agent_response_step_id.max_step
                functional_response = agent_response_step_id.functional_response
                answer = self._get_server_answer(role, step, max_steps, None, functional_response)
                _logger.info(f"Answer from server: {answer}")
                agent_response_step_id = self.create_response_line(answer)
                _logger.info(f"Agent Response Step ID: {agent_response_step_id.id}  (Step: {step+1} / {max_steps})")
                if step+1 >= max_steps:
                    break
            
            # role = "ODOO Developer"
            # step = step + 1
            # max_steps = agent_response_step_id.max_step
            # functional_response = agent_response_step_id.functional_response
            # answer = self._get_server_answer(role, step, max_steps, None, functional_response)
            # print(f"Answer from server: {answer}")
            # agent_response_step_id = self.create_response_line(answer)
            # print(f"Agent Response Step ID: {agent_response_step_id.id}")


            # role = "ODOO Developer"
            # step = step + 1
            # max_steps = agent_response_step_id.max_step
            # functional_response = agent_response_step_id.functional_response
            # answer = self._get_server_answer(role, step, max_steps, None, functional_response)
            # print(f"Answer from server: {answer}")
            # agent_response_step_id = self.create_response_line(answer)
            # print(f"Agent Response Step ID: {agent_response_step_id.id}")


            # role = "ODOO Developer"
            # step = step + 1
            # max_steps = agent_response_step_id.max_step
            # functional_response = agent_response_step_id.functional_response
            # answer = self._get_server_answer(role, step, max_steps, None, functional_response)
            # print(f"Answer from server: {answer}")
            # agent_response_step_id = self.create_response_line(answer)
            # print(f"Agent Response Step ID: {agent_response_step_id.id}")


            
            self.copilot_agent_id.status = 'to_review'
            self.copilot_agent_id.last_run = fields.Datetime.now()
            # self.copilot_agent_id.next_run = fields.Datetime.now() + relativedelta(months=1)
            self.copilot_agent_id.next_run = self.copilot_agent_id.last_run + relativedelta(**{self.copilot_agent_id.execute_unit: self.copilot_agent_id.execute_every})
            self.run_time_of = fields.Datetime.now()
            self.state = 'done'

        except Exception as e:
            self.copilot_agent_id.status = 'failed'
            self.state = 'failed'
            self.copilot_agent_id.next_run = self.copilot_agent_id.last_run + relativedelta(
                **{self.copilot_agent_id.execute_unit: self.copilot_agent_id.execute_every})

            _logger.info(e)
            trace_msg = traceback.format_exc()
            _logger.info(trace_msg)
        return {
                'type': 'ir.actions.act_window',
                'res_model': self._name,
                'res_id': self.id,
                'view_mode': 'form',
                'target': 'new',
            }

    def _get_server_answer(self, role, step, max_steps, current_step_output, functional_response):
        header = TokenManager()
        config_pram = header.get_copilot_config_parameter()
        url = config_pram.get('redirect_url') + '/get/api-v1/get-agent-response'

        environ = request.httprequest.environ
        data = {
            'agent_code': self.copilot_agent_id.agent_code,
            'user_query': self.copilot_agent_id.user_query,
            "business_summary": config_pram.get('business_summary'),
            'database_structure': self.copilot_agent_id.extract_class_column_data(),
            'reference_id': self.server_ref_id,
            'role': role,
            'step': step,
            'max_steps': max_steps,
            'current_step_output': current_step_output,
            'functional_response': functional_response,
            'domain': environ.get('HTTP_HOST') or environ.get('SERVER_NAME'),
            'ip_address': environ.get('REMOTE_ADDR'),
            'port': environ.get('REMOTE_PORT'),
        }

        response = requests.get(url, json=data, headers=header.get_headers())

        # Handle the response
        if response.status_code != 200:
            raise ValidationError('Server error code ' + str(response.status_code))

        result = response.json()
        result = result.get('result', {})
        result = json.loads(result) if isinstance(result, str) else result
        # print(f"\n\nServer Response: {result['business_summary']}\n\n")
        # result = eval(result)
        # print(f"\n\nServer Response: {result}")
        return result
        # # Check for success or error messages in the response
        # if result.get('success_msg'):
        #     answer = result.get('answer')
        #     return result

        # if result.get('error_msg'):
        #     return result

    def confirm_and_review(self):
        pass

    def execute_query(self, answer, question):
        answer_dictionary = answer
        if answer_dictionary.get('error_msg'):
            self.server_exception = answer_dictionary.get('error_msg')
            if answer_dictionary.get('show_original'):
                return {'err_msg': answer_dictionary.get('error_msg')}
            return {
                'err_msg': "Sorry!!! Can't process your query this time. Please try again and use more specific meaning full words. Thank You !!!"}
        else:
            answer_dictionary = answer.get('answer')

        if answer_dictionary.get('output_format') == 'Business Planning':
            val = self.create_response_line(answer_dictionary)
            self.server_ref_id = answer.get('copilot_ref_id')
            return val

    def create_response_line(self, answer):
        # if self.env.context.get('called_res_user'):
        #     answer = answer.get('answer')
        context = answer.get('context')
        python_code = answer.get('python_functions')
        text = answer.get('text')
        final_step = answer.get('final_step')
        agent_code = answer.get('agent_code') or self.copilot_agent_id.agent_code
        text_response = False
        full_response = False
        output_response = False
        final_output_response = False
        column_dict = False
        template_id = False
        output_dictionary = dict()
        final_step_output_dictionary = dict()
        print("\n\npython_code: ", python_code)
        if python_code:
            try:
                # try:
                #     output_response = self.get_response_line_data(answer.get('step'))
                #     output_dictionary = self.execute_python_function_multi(python_code, output_response)
                # except Exception as e:
                #     _logger.info(e)
                #     error_message = str(e)
                #     _logger.info(f'(First Retry) Error Message: \n{error_message}')
                #     python_code = self.with_context(error_message=error_message)._get_server_answer_multi_step()
                #     try:
                #         output_dictionary = self.execute_python_function_multi(python_code, output_response)
                #     except Exception as e:
                #         _logger.info(e)
                #         error_message = str(e)
                #         _logger.info(f'(Second Retry) Error Message: \n{error_message}')
                #         python_code = self.with_context(error_message=error_message)._get_server_answer_multi_step()
                #         output_dictionary = self.execute_python_function_multi(python_code, output_response)
                try:
                    output_response = self.get_response_line_data(answer.get('step'))
                    output_dictionary = self.execute_python_function_multi(python_code, output_response)
                except Exception as e:
                    error_message = str(e)
                    trace_msg = traceback.format_exc()
                    _logger.info(f'Traceback: \n{trace_msg}')
                    text_response = python_code.replace("\n", "<br/>")

                _logger.info("Code Execution completed")
                print(output_dictionary)
                # print("========================================")
                if not isinstance(output_dictionary, dict):
                    try:
                        output_dictionary = eval(output_dictionary)
                    except Exception as e:
                        try:
                            output_dictionary = ast.literal_eval(output_dictionary)
                        except Exception as e:
                            output_dictionary = json.loads(output_dictionary)
                # _logger.info(f'Output for step {answer.get("step")} : \n{output_dictionary}')
                full_response = ""
                if final_step and not agent_code in ["004","008","002", "600", "007"]:
                    formatted_output_dictionary = self.store_formated_data(output_dictionary, agent_code)
                    print(f"Output Dictionary: {formatted_output_dictionary}")
                    template_id = f"agent_template_{agent_code}"
                    output_dictionary = formatted_output_dictionary[0] if formatted_output_dictionary and len(formatted_output_dictionary) > 0 else False
                    if formatted_output_dictionary and len(formatted_output_dictionary) > 1:
                        final_step_output_dictionary = formatted_output_dictionary[1]
                        full_response = self.get_formatted_html(final_step_output_dictionary)

                column_dict = dict()
                if not template_id:
                    full_response = self.get_formatted_html(output_dictionary)

                output_response = output_dictionary
                final_output_response = final_step_output_dictionary
            except Exception as e:
                _logger.info(e)
                trace_msg = traceback.format_exc()
                _logger.info(trace_msg)
                full_response = f'<table cellpadding="5" class="table ans-response-table"><thead><tr><th scope="col" style="text-align:center">Description</th></tr></thead><tbody><tr><td style="text-align:center">{answer.get("description")}</td></tr></tbody></table>'
                # text_response = '<table cellpadding="5" class="table ans-response-table"><thead><tr><th scope="col" style="text-align:center">Error</th></tr></thead><tbody><tr><td style="text-align:center">Cannot Execute Python Functions Have Some Errors</td></tr></tbody></table>'
        else:
            text_response = answer.get('odoo_functional_response_text')
            full_response = text_response
        print("======= Saving Response =======")
        step = answer.get("step")
        response_for_1st_2nd = f'<div style="background-color: #666; color: #fff; padding: 1.5rem; border-radius: 0.5rem;">{answer.get("text")}</div>'
        print("Final Step: ", answer.get("final_step"))
        val = {
            "special_id": answer.get("special_id"),
            # "text": text_response,
            "text": full_response,
            "text_response": full_response if not final_step else False,
            "final_step_text_response": full_response if final_step else False,
            # "text_response": text_response,
            "output_response": output_response,
            "final_step_output_response": final_output_response if final_step else False,
            "template_id": template_id,
            "output_column": column_dict,
            "title": answer.get("title"),
            "current_role": answer.get("role"),
            # "next_role": answer.get("role"),
            "final_step": answer.get("final_step"),
            "python_functions": answer.get('python_functions'),
            # "reference_url": reference_url if show_query else False,
            # "full_response": answer.get("full_response"),
            "functional_response": answer.get("functional_response"),
            "max_step": answer.get("max_steps"),
            "step": answer.get("step"),
            # "loading_message": answer.get("loading_message"),
            # "no_animate": context.get("no_animate"),
            'agent_response_history_id': self.id,
        }

        if final_step and agent_code in ["004","008","002","006","007"]:
            val['text_response'] = full_response

        # self.write({"agent_response_history_step_ids": [(0, 0, val)]})
        step_id = self.env['agent.response.history.step'].create(val)
        self.server_ref_id = answer.get('reference_id')
        return step_id
    

    def store_formated_data(self, output_dictionary, agent_code):
        if agent_code == "001":
            purchase_order_data = output_dictionary.get('purchase_order_data')
            formatted_result = {}
            for idx in range(len(purchase_order_data)):
                purchase_order_data[idx]['vendor_info']['identifier'] = idx + 1
                formatted_result[f'Purchase Order # {idx+1}'] = purchase_order_data[idx]
            return [purchase_order_data, formatted_result]
    
        if agent_code == "003":
            formatted_product_wise_data = output_dictionary.get('formatted_product_wise_data')
            formatted_result = {}
            for item in formatted_product_wise_data:
                formatted_result[item['product_info']['product_name']] = item['vendor_list']
            return [formatted_product_wise_data, formatted_result]

    def _get_server_answer_multi_step(self):
        header = TokenManager()
        config_pram = header.get_copilot_config_parameter()
        url = config_pram.get('redirect_url') + '/get/api-v1/get-multi-step'
        last_step_id = self.agent_response_history_step_ids[len(self.agent_response_history_step_ids) - 1]
        # client_output = last_step_id.output_response
        client_output = last_step_id.output_column
        data = {
            "copilot_ref_id": self.server_ref_id,
            "client_output": client_output,
            "last_step": last_step_id.step
        }

        if self.env.context.get('error_message'):
            data.update({
                "client_output": self.env.context.get('error_message'),
                "need_bug_fixing": True
            })

        # header = TokenManager()
        # Send the request
        try:
            response = requests.get(url, json=data, headers=header.get_headers())
        except requests.exceptions.ConnectionError:
            raise ValidationError('connection timeout')
        # response = requests.get(url, json=data, headers=header.get_headers(),timeout=8)

        # Handle the response
        if response.status_code != 200:
            _logger.info('Server error code from multi' + str(response.status_code))

            # raise ValidationError('Server error code ' + str(response.status_code))

        result = response.json()

        # _logger.info("\n\n\n" + str(result) + "\n\n\n")
        # Check for success or error messages in the response
        if result.get('success_msg'):
            answer = result.get('answer')
            if answer.get('correction_status') == 'Bug-Fixed':
                _logger.info("Correction function Returned")
                return answer.get('python_functions')
            self.with_context(called_res_user=True).create_response_line(result)
            # if result.get('history_title'):
            #     self.chat_session_id.name = result.get('history_title')
            return answer

        elif result.get('error_msg'):
            return result

    def get_response_line_data(self, step):
        response_lines = self.agent_response_history_step_ids.filtered(lambda line: line.step>1 and line.step < step).sorted(
            key=lambda l: l.step)
        response_line_responses = {}
        if response_lines:
            for line in response_lines:
                response_line_responses[f"step_{line.step - 1}"] = eval(line.output_response)
        return response_line_responses

    def execute_python_function_multi(self, code_to_execute, prev_step_executed_data=None):
        _logger.info("\n\n -----from Multi-Business Planning execution started -----\n\n")
        code_to_execute = code_to_execute.replace("self.env", "request.env")
        executable_code = ImportString 
        for line in code_to_execute.splitlines():
            executable_code += "    " + line + "\n"  # indent for class scope
        # print(f"Executable Code:\n{executable_code}")
        # print(f"\n\n Previous Step Executed Data:\n{prev_step_executed_data}")
        # Execute the class definition
        exec(executable_code, globals())

        # Create an instance and call the method
        obj = OdooAIAgent()  # Create an instance of the model
        # output_dictionary = obj.get_response_main()
        if "previous_step_data" in code_to_execute:
            output_dictionary = obj.get_response_main(prev_step_executed_data)
        else:
            output_dictionary = obj.get_response_main()
        # print(f"Output Dictionary: {output_dictionary}")
        # import_line = "from odoo.addons.copilot.models.call_back import search_internet_and_interpret_results_with_llm, DecisionMakingAgent"
        # code_to_execute = import_line + "\n" + code_to_execute
        # try:
        #     if "prev_step_executed_data" in code_to_execute or "prev_step_executed_columns" in code_to_execute:
        #         exec(code_to_execute, globals())
        #         output_dictionary = eval(f"get_response_main(self, {prev_step_executed_data})")
        #     else:
        #         exec(code_to_execute, globals())
        #         output_dictionary = eval("get_response_main(self)")
        # except Exception as e:
        #     error_message = "Traceback with issue details:\n"
        #     tb_list = traceback.format_exception(type(e), e, e.__traceback__)
        #     filtered_trace = [line for line in tb_list if 'get_response' in line and 'execute_python_function_multi' not in line]
            
        #     # Print or log filtered lines
        #     for line in filtered_trace:
        #         error_message += line.strip() + "\n"
        #     error_message += f"\n{type(e).__name__}: {e}"
        #     raise ValidationError(error_message)
        return output_dictionary

    # def execute_python_function_multi(self, code_to_execute, prev_step_executed_data=None):
    #     _logger.info("\n\n -----from Multi-Business Planning execution started -----\n\n")
    #     # locals = {
    #     #     "prev_step_executed_data": eval(prev_step_executed_data) if prev_step_executed_data else None,
    #     # }
    #     try:
    #         if "prev_step_executed_data" in code_to_execute:
    #             exec(code_to_execute, globals())
    #             output_dictionary = eval(f"get_response_main(self.env, {prev_step_executed_data})")
    #         else:
    #             exec(code_to_execute, globals())
    #             output_dictionary = eval("get_response_main(self.env)")
    #     except Exception as e:
    #         error_message = "Traceback with issue details:\n"
    #         tb_list = traceback.format_exception(type(e), e, e.__traceback__)
    #         filtered_trace = [line for line in tb_list if
    #                           'get_response' in line and 'execute_python_function_multi' not in line]

    #         # Print or log filtered lines
    #         for line in filtered_trace:
    #             error_message += line.strip() + "\n"
    #         error_message += f"\n{type(e).__name__}: {e}"
    #         raise ValidationError(error_message)
    #     return output_dictionary


    def calling_df_to_html(self, value):
        df = response_manager.dict_to_table(value)
        df = df.head(100)
        df = df.apply(lambda col: col.round(2) if col.dtype == 'float64' else col)
        # if len(df.index) > 15:
        #     text_response = response_manager.df_to_html(df.head(15))
        #     column = len(df.columns)
        #     see_more = f"""
        #                     <tr>
        #                         <td class="text-center" colspan="{column}">------------------------</td>
        #                     </tr>
        #                     <tr>
        #                         <td class="text-center" colspan="{column}">To see more download excel</td>
        #                     </tr>
        #                 """
        #     index = text_response.find('</tbody>')
        #     text_response = text_response[:index] + see_more + text_response[index:]
        # else:
        #     text_response = response_manager.df_to_html(df)
        text_response = response_manager.df_to_html(df)
        return text_response

    def dictionary_to_columns_template(self, dictionary):
        """
        on dictionary replace value with datatype
        only value of dictionary is replaced with datatype all structure will be same
        it will return same dictionary structure with values replaced by their data types.
        """
        def replace_values_with_types(d):
            if isinstance(d, dict):
                return {k: replace_values_with_types(v) for k, v in d.items()}
            elif isinstance(d, list):
                return [replace_values_with_types(item) for item in d]
            else:
                return type(d).__name__

        return replace_values_with_types(dictionary)

    def process_item(self, item):
        pattern = re.compile(r'^[0-9.,-]+$')
        if isinstance(item, float):
            return round(item, 2)
        item_str = str(item).replace(',', '')
        is_match = bool(pattern.match(item_str))
        return round(float(item_str), 2) if is_match else item


    def open_review_response(self):
        last_record = self
        if not last_record:
            raise ValidationError("No agent response history record found.")
        view_id = self.env.ref('odoo_ai_agent.agent_response_history_form_view_custom_design').id

        return {
            'type': 'ir.actions.act_window',
            'name': 'Agent Details',
            'res_model': 'agent.response.history',
            'res_id': self.id,
            'view_mode': 'form',
            'views': [[view_id, 'form']],
            'target': 'new',
        }

    def get_steps_data(self):
        # Implement the logic to retrieve steps data
        steps = self.agent_response_history_step_ids
        data = steps.read(['id','has_user_confirmation', 'step', 'text_response', 'output_response', 'text', 'title', 'current_role', 'final_step', 'template_id'])

        return data

    def excel_export(self):
        if self.agent_response_history_step_ids:
            pages = {}
            for response_line in self.agent_response_history_step_ids:
                if response_line.step > 1:
                    pages[response_line.title] = response_line.get_list_of_df()

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                workbook = writer.book

                # Write data for each page
                for page_name, tables in pages.items():
                    worksheet = workbook.add_worksheet(page_name)
                    writer.sheets[page_name] = worksheet
                    row = 0
                    bold_format = workbook.add_format({'bold': True, 'font_size': 14})
                    for key, df in tables:
                        worksheet.write(row, 0, key, bold_format)
                        row += 1

                        df.to_excel(writer, sheet_name=page_name, startrow=row, index=False)
                        row += len(df) + 3

            output.seek(0)
            file_data = base64.b64encode(output.read())
            output.close()

            self.data_excel_ids = file_data
            file_name = f"{self.copilot_agent_id.name}.xlsx"

            return {
                'type': 'ir.actions.act_url',
                'url': f"/web/content?model=agent.response.history&download=true&field=data_excel_ids&filename={file_name}&id={self.id}",
                'target': 'new',
            }
        else:
            raise UserError("No Copilot Response Line")

    def action_download_pdf(self):
        data = {
            'create_date': self.create_date,
            'user': self.create_uid,
            'custom_message': self.copilot_agent_id.name,
            'line_items': [{'title': line.title, 'text': line.text if line.step == 1 else False , 'text_response': line.text_response if not line.final_step else line.final_step_text_response} for line in self.agent_response_history_step_ids],
        }
        return  self.env.ref('odoo_ai_agent.action_chat_message_model').sudo().report_action([], data=data)

    @api.model
    def fetch_last_agent_response(self, agent_id, fields=None):
        data = []
        xml = self.env.ref('odoo_ai_agent.agent_response_history_form_view_custom_design').arch_db
        parser = etree.XMLParser(remove_comments=True)  # removes commented nodes
        tree = etree.fromstring(xml.encode("utf-8"), parser)

        # Find all <button> in the view
        buttons = tree.xpath("//button")
        button_list = [dict(button.attrib) for button in buttons]
        btn_2 = []
        for btn in button_list:
            converted = {
                "className": btn.get("class"),
                "clickParams": {k: v for k, v in btn.items() if k not in ("class",)},  # rest of attrs
                "name": btn.get("name"),
                "type": "button",   # normalize to "button"
                "column_invisible": None,
                "defaultRank": "btn-link",
                "disabled": False,
                "display": "selection",
                "icon": False,
                "id": 0,
                "invisible": btn.get("invisible"),
                "options": {},
                "readonly": None,
                "required": None,
                "string": btn.get("string"),
                "title": None,
                # prototype ignored
            }
            btn_2.append(converted)
        for id in agent_id:
            response = self.search([("copilot_agent_id", "=", id), ("state", "!=", "failed")], limit=1, order="id desc")
            if response:
                steps_data = response.agent_response_history_step_ids.read(['id','has_user_confirmation', 'step', 'text_response', 'output_response', 'text', 'title', 'current_role', 'final_step', 'template_id'])
                data.append({response.copilot_agent_id.name: steps_data, 'agent_id': response.copilot_agent_id.id, 'status': response.copilot_agent_id.status, 'history_id': response.id, 'buttons': btn_2, 'last_run': response.copilot_agent_id.last_run })
        return data


    def get_formatted_html(self, output_response):
        full_response = ""

        column_dict = dict()
        for main_key, main_value in output_response.items():
            if main_key == 'timestamp':
                continue
            if isinstance(main_value, dict):
                if all(isinstance(item, (int, float)) for item in main_value.keys()):
                    list_of_dic = []
                    list_of_dic.extend(main_value.values())
                    text_response = self.calling_df_to_html(list_of_dic)
                    full_response = full_response + f"""<h3>{main_key.replace("_", " ").title()}</h3><br/>{text_response}<br/>"""
                    continue
                sub_column_dict = dict()
                for key, value in main_value.items():
                    column_list = []
                    if isinstance(value, (dict, list)):
                        if not value:
                            continue
                        if isinstance(value, dict):
                            # column_list = list(value.keys())
                            column_list = self.dictionary_to_columns_template(value)
                            if all(isinstance(item, (int, float)) for item in value.keys()):
                                list_of_dic = []
                                list_of_dic.extend(value.values())
                                text_response = self.calling_df_to_html(list_of_dic)
                                full_response = full_response + f"""<h3>{main_key.replace("_", " ").title()}</h3><br/>{text_response}<br/>"""
                                continue
                        text_response = self.calling_df_to_html(value)
                        if "table" in text_response:
                            if isinstance(value, list):
                                if isinstance(value[0], dict):
                                    # column_list = list(value[0].keys())
                                    column_list = self.dictionary_to_columns_template(value[0])
                            elif isinstance(value, dict):
                                # column_list = list(value.keys())
                                column_list = self.dictionary_to_columns_template(value)
                            full_response = full_response + f"""<h3>{main_key.replace("_", " ").title()} For {str(key).replace("_", " ").title()}</h3><br/>{text_response}<br/>"""
                        else:
                            full_response = full_response + f"""<h3>{main_key.replace("_", " ").title()} For {str(key).replace("_", " ").title()}:- {text_response}</h3><br/>"""
                    else:
                        full_response = full_response + f"""<h3>{main_key.replace("_", " ").title()} For {str(key).replace("_", " ").title()}:- {self.process_item(value)}</h3><br/>"""
                    sub_column_dict.update({key: column_list})
                column_dict.update({main_key: sub_column_dict})
            elif isinstance(main_value, list):
                text_response = self.calling_df_to_html(main_value)
                full_response = full_response + f"""<h3>{main_key.replace("_", " ").title()}</h3><br/>{text_response}<br/>"""
            else:
                full_response += f"""<p><strong>{main_key.replace("_", " ").title()}:</strong> {f"<b>{main_value}</b>" if isinstance(main_value, (int, float)) else self.process_item(main_value)}</p>"""
        return full_response
