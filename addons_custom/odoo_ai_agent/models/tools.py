import re
import pandas as pd
import requests
import random
from odoo.exceptions import ValidationError
from odoo.http import request
from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class TokenManager:

    def display_notification(self, message, notification_type):
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': notification_type,
                'message': message,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }

    def _request_token(self):
        config_pram = request.env['ir.config_parameter'].sudo()
        if not config_pram.get_param('copilot.client_key'):
            raise ValidationError('Client key not found')
        if not config_pram.get_param('copilot.client_secret'):
            raise ValidationError('Client secret not found')
        if not config_pram.get_param('copilot.redirect_url'):
            raise ValidationError('Redirect Url not found')
        url = config_pram.get_param('copilot.redirect_url') + '/get/api-v1/bearer-token'

        headers = {
            'Content-Type': 'application/json',
            'client-key': config_pram.get_param('copilot.client_key'),
            'client-secret': config_pram.get_param('copilot.client_secret')
        }
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            return self.display_notification(
                message=f"Failed status code: {response.status_code}",
                notification_type='danger'
            )

        data = response.json()
        if 'error_msg' in data:
            raise ValidationError(data['error_msg'])

        if 'token' in data:
            previous_token = request.env['client.bearer.token'].search(
                [('expiry', '<', fields.Datetime.now()), ('active', '=', True)])
            for token in previous_token:
                token.active = False
            request.env['client.bearer.token'].create({
                'token': data.get('token'),
                'expiry': data.get('expiry'),
                'expiration': data.get('expiration')
            })
            return data.get('token')

    def get_token(self):
        bearer_token_obj = request.env['client.bearer.token'].search(
            [('expiry', '>', fields.Datetime.now()), ('active', '=', True)], limit=1)
        if bearer_token_obj:
            return bearer_token_obj.token
        elif not bearer_token_obj:
            return self._request_token()

    def get_headers(self):
        return {
            'Authorization': f'Bearer {self.get_token()}',
            'Content-Type': 'application/json'
        }

    def get_copilot_config_parameter(self):
        config_pram = request.env['ir.config_parameter'].sudo()
        return {
            'client_key': config_pram.get_param('copilot.client_key'),
            'client_secret': config_pram.get_param('copilot.client_secret'),
            'redirect_url': config_pram.get_param('copilot.redirect_url'),
            'credit': config_pram.get_param('copilot.credit'),
            'ai_agent_credit': config_pram.get_param('ai_agent.credit'),
            'connection_status': config_pram.get_param('copilot.connection_status'),
            'business_summary': config_pram.get_param('copilot.business_summary'),
        }


# Data Formater
def detect_list_keys(data):
    """Detects keys that contain lists (of dicts) from the first dictionary in the dataset."""
    list_keys = set()

    if isinstance(data, list) and len(data) > 0:
        first_entry = data[0]
        for key, value in first_entry.items():
            if isinstance(value, list) and all(isinstance(i, dict) for i in value):
                list_keys.add(key)

    return list_keys


def expand_list_entries(data):
    """Expands list entries into multiple rows while keeping non-list fields identical."""
    list_keys = detect_list_keys(data)
    expanded_data = []

    for entry in data:
        # Identify list fields to expand
        list_columns = {key: entry.get(key, []) for key in list_keys}
        max_rows = max((len(v) for v in list_columns.values()), default=1)

        for i in range(max_rows):
            new_entry = entry.copy()

            for key, values in list_columns.items():
                if i < len(values):
                    new_entry[key] = values[i]  # Use the specific row's value
                else:
                    new_entry[key] = None  # Fill with None for shorter lists

            expanded_data.append(new_entry)

    return expanded_data


def flatten_dict(d, parent_key='', sep='_'):
    """Recursively flattens a dictionary, handling nested dictionaries and lists."""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        elif isinstance(v, list) and all(isinstance(i, dict) for i in v):
            items.append((new_key, v))  # Keep lists of dicts for row expansion
        elif isinstance(v, list):
            items.append((new_key, ", ".join(map(str, v))))  # Convert lists to comma-separated strings
        else:
            items.append((new_key, v))
    return dict(items)


class ResponseManager:

    def generate_random_colors(num_colors: int) -> list:
        min_brightness = 0.4
        colors = []

        for _ in range(num_colors):
            r = random.uniform(min_brightness, 1.0 - 0.15)
            g = random.uniform(min_brightness, 1.0 - 0.15)
            b = random.uniform(min_brightness, 1.0 - 0.15)
            colors.append((r, g, b))
        return colors

    def remove_en_us_keys(self, df):
        for column in df.columns: df[column] = df[column].apply(lambda x: x.get('en_US') if isinstance(x, dict) else x)
        cleaned_columns = [col.replace('_', ' ').title() for col in df.columns]
        df.columns = cleaned_columns
        return df

    def suggest_plot_type(self, question, data):
        """
		Suggests the appropriate plotting type based on the query and data.

		Parameters:
			question (str): The user's query regarding the data.
			data (pd.DataFrame): The DataFrame containing the data to be plotted.

		Returns:
			str: The suggested plotting type.
		"""
        question = question.lower()

        if any(keyword in question for keyword in ['trend', 'over time', 'time series']):
            return 'line'
        if any(keyword in question for keyword in ['distribution', 'spread', 'frequency']):
            return 'histogram'
        if any(keyword in question for keyword in ['relationship', 'correlation', 'scatter']):
            return 'scatter'
        if any(keyword in question for keyword in ['categorical', 'bar', 'category']):
            return 'bar'
        if any(keyword in question for keyword in ['part-to-whole', 'proportion', 'percentage']):
            return 'pie'
        if any(keyword in question for keyword in ['hierarchy', 'tree']):
            return 'tree map'

        # Data-based suggestions
        num_cols = data.select_dtypes(include='number').columns
        cat_cols = data.select_dtypes(include='object').columns

        if len(num_cols) == 0:
            # If no numeric columns, suggest a table or a count plot for categorical data
            return 'table' if len(cat_cols) == 0 else 'count'
        if len(num_cols) == 1 and len(cat_cols) > 0:
            # If one numeric and multiple categorical columns, suggest a bar plot
            return 'bar'
        if len(num_cols) > 1:
            # If multiple numeric columns, suggest scatter or line based on the presence of a time-related column
            if any(col for col in data.columns if 'date' in col.lower() or 'time' in col.lower()):
                return 'line'
            return 'scatter'

        return 'table'

    def df_to_html(self, df, special_class=''):
        pattern = re.compile(r'^[0-9.,-]+$')

        html = f'<div class="ai-agent-response-table-container"><table class="table agent-response-table">\n'

        html += '  <thead>\n    <tr>\n'
        for column in df.columns:
            # value = df.at[0, column]
            value = df[column].iloc[0]
            col_number = df.columns.get_loc(column) + 1
            try:
                is_match = pattern.match(str(value))
                alignment = 'right' if is_match else 'left'
            except:
                alignment = 'left'
            if len(df.columns) == 1:
                alignment = 'center'
            column = column.replace('_', ' ').title()
            html += f'      <th scope="col" class="column{col_number}" t-att-data-column="column{col_number}" style="text-align:{alignment}">{column}</th>\n'
        html += '    </tr>\n  </thead>\n'

        html += '  <tbody>\n'
        for row in df.itertuples(index=False):
            html += '    <tr>\n'
            col_number = 0
            for item in row:
                col_number += 1
                if isinstance(item, list):
                    item = "" if not item else item + ''.join(f"{item_of_item}," for item_of_item in item)
                else:
                    if pd.isna(item) or item is False:
                        item = ""
                try:
                    is_match = pattern.match(str(item))
                    alignment = 'right' if is_match else 'left'
                except:
                    alignment = 'left'
                if len(df.columns) == 1:
                    alignment = 'center'
                html += f'      <td class="column{col_number}" data-column="column{col_number}" style="text-align:{alignment}">{item}</td>\n'
            html += '    </tr>\n'
        html += '  </tbody>\n'
        html += '</table></div>'

        return html

    def dict_to_table(self, data):
        """Converts a nested dictionary to a Pandas DataFrame, dynamically expanding list entries."""
        _logger.info(f'Response data type --->{type(data)}')
        if isinstance(data, list) and len(data) > 0:
            if all(isinstance(item, str) for item in data):
                data_list_dic = [{'Recommendations': value} for value in data]
                flattened_data = [flatten_dict(item) for item in data_list_dic]
                expanded_data = expand_list_entries(flattened_data)
                return pd.DataFrame(expanded_data)
            else:
                flattened_data = [flatten_dict(item) if isinstance(item, dict) else item for item in data]
                expanded_data = expand_list_entries(flattened_data)
                return pd.DataFrame(expanded_data)
        elif isinstance(data, dict) and len(data) > 0:
            flattened_data = [flatten_dict(data)]
            expanded_data = expand_list_entries(flattened_data)
            return pd.DataFrame(expanded_data)
        else:
            return pd.DataFrame()

# def dict_to_table(self, data):
# 	"""Converts a nested dictionary to a Pandas DataFrame, dynamically expanding list entries."""
# 	print(type(data))
# 	if isinstance(data, list) and len(data) > 0:
# 		if isinstance(data[0], dict):
# 			flattened_data = [flatten_dict(item) for item in data]
# 			expanded_data = expand_list_entries(flattened_data)
# 			return pd.DataFrame(expanded_data)
# 		elif isinstance(data[0], str):
# 			data_list_dic = [{'Recommendations': value} for value in data]
# 			flattened_data = [flatten_dict(item) for item in data_list_dic]
# 			expanded_data = expand_list_entries(flattened_data)
# 			return pd.DataFrame(expanded_data)
# 	elif isinstance(data, dict) and len(data) > 0:
# 		data = data.get('recommendations')
# 		if isinstance(data, list) and len(data) > 0:
# 			if isinstance(data[0], dict):
# 				flattened_data = [flatten_dict(item) for item in data]
# 				expanded_data = expand_list_entries(flattened_data)
# 				return pd.DataFrame(expanded_data)
# 			elif isinstance(data[0], str):
# 				data_list_dic = [{'Recommendations': value} for value in data]
# 				flattened_data = [flatten_dict(item) for item in data_list_dic]
# 				expanded_data = expand_list_entries(flattened_data)
# 				return pd.DataFrame(expanded_data)
# 	else:
# 		return pd.DataFrame()
