import re
import pandas as pd
import requests
import random
import json
from odoo.exceptions import ValidationError
from odoo.http import request
from odoo import models, fields, api, _
import logging
_logger = logging.getLogger(__name__)
from odoo.addons.odoo_ai_agent.models.tools import TokenManager, ResponseManager


def search_internet_and_interpret_results_with_llm(query, interpretation_prompt, expected_json_format):
	print("\n\n search_internet_and_interpret_results_with_llm called with query: ")
	config = TokenManager()
	config_pram = config.get_copilot_config_parameter()
	url = config_pram.get('redirect_url') + '/get/api-v1/call-back-data-analysis'

	print("\n\n Expected JSON format: ", expected_json_format)

	environ = request.httprequest.environ
	json_data = {
		"query": query,
		"prompt": interpretation_prompt,
		"output_format": expected_json_format,
		"call_type": "internet_search",
		"domain": environ.get('HTTP_HOST') or environ.get('SERVER_NAME'),
		"ip_address": environ.get('REMOTE_ADDR'),
		"port": environ.get('REMOTE_PORT'),
	}
	# Send the request
	try:
		response = requests.get(url, json=json_data, headers=config.get_headers())
		# Handle the response
		if response.status_code != 200:
			_logger.info('Server error code ' + str(response.status_code))

		result = response.json()
		_logger.info("Random function called successfully.")
		return result
	except Exception as e:
		print('\n\n Exception: ', e)
		_logger.info('Request failed: ' + str(e))



def DecisionMakingAgent(data, interpretation_prompt, expected_json_format):
	print("\n\n DecisionMakingAgent called with data: ",)
	config = TokenManager()
	config_pram = config.get_copilot_config_parameter()
	url = config_pram.get('redirect_url') + '/get/api-v1/call-back-data-analysis'

	environ = request.httprequest.environ
	json_data = {
		"data": data,
		"prompt": interpretation_prompt,
		"output_format": expected_json_format,
		"call_type": "decision_making",
		'domain': environ.get('HTTP_HOST') or environ.get('SERVER_NAME'),
		'ip_address' : environ.get('REMOTE_ADDR'),
		'port' : environ.get('REMOTE_PORT'),
	}
	print("\n\n json_data: ", json_data)

	# Send the request
	response = requests.get(url, json=json_data, headers=config.get_headers())

	# Handle the response
	if response.status_code != 200:
		_logger.info('Server error code ' + str(response.status_code))

	result = response.json()
	print("\n\n Decision Making Agent result: ", result)
	_logger.info("Decision making function called successfully.")

	return result


def ForecastProductSale(sales_data, stock_data):
	config = TokenManager()
	config_pram = config.get_copilot_config_parameter()
	url = config_pram.get('redirect_url') + '/get/api-v1/call-back-data-analysis'

	environ = request.httprequest.environ
	json_data = {
		"sales_data": sales_data,
		"stock_data": stock_data,
		"call_type": "forecast",
		'domain': environ.get('HTTP_HOST') or environ.get('SERVER_NAME'),
		'ip_address' : environ.get('REMOTE_ADDR'),
		'port' : environ.get('REMOTE_PORT'),
	}

	# Send the request
	response = requests.get(url, json=json_data, headers=config.get_headers())
	print('\n Response: ', response)
	# Handle the response
	if response.status_code != 200:
		_logger.info('Server error code ' + str(response.status_code))

	result = response.json()
	_logger.info("Forecast product sale function called successfully.")

	return result



def CalculateLeadTime(vendor_product_data):
	config = TokenManager()
	config_pram = config.get_copilot_config_parameter()
	url = config_pram.get('redirect_url') + '/get/api-v1/call-back-data-analysis'

	environ = request.httprequest.environ
	json_data = {
		"vendor_product_data": vendor_product_data,
		"call_type": "lead_time",
		'domain': environ.get('HTTP_HOST') or environ.get('SERVER_NAME'),
		'ip_address' : environ.get('REMOTE_ADDR'),
		'port' : environ.get('REMOTE_PORT'),
	}

	# Send the request
	response = requests.get(url, json=json_data, headers=config.get_headers())
	# Handle the response
	if response.status_code != 200:
		raise ValidationError('Server error code ' + str(response.status_code))

	result = response.json()
	_logger.info("Calculate lead time function called successfully.")

	return result