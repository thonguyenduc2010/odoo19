# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions Inc.
# Copyright (C) 2025 (http://www.bistasolutions.com)
#
##############################################################################

{
    'name': "Odoo AI Agent",

    'summary': """Revolutionize your business operations with specialized AI agents that work in the background or on-demand. Each agent delivers expert-level performance in their specialized domain.""",

    'description': """
        Revolutionize your business operations with specialized AI agents that work in the background or on-demand. Each agent delivers expert-level performance in their specialized domain. 
    """,

    'author': "Bista Solutions Inc.",
    'website': "https://www.bistasolutions.com",
    # 'live_test_url': 'https://odoocopilot.ai/live-test-form/17',
    'license': 'LGPL-3',

    # for the full list
    'category': 'Technical',
    'version': '19.0.1.0',
    'sequence': 1,

    # any module necessary for this one to work correctly
    'depends': ['base_setup', 'stock', 'purchase', 'sale', 'account','web'],

    'data': [
        'security/ir.model.access.csv',
        'data/ai_agent_next_run_cron.xml',
        'data/get_ai_agents_run_cron.xml',
        'views/agent_dashboard.xml',
        'views/agent_response_history_views.xml',
        'views/agent_response_history_step_views.xml',
        'views/ai_agent_object_reference_views.xml',
        'views/bearer_token_views.xml',
        'views/res_config_settings_views.xml',
        'report/chat_message_report_views.xml',
        'report/copilot_response_line_report_views.xml',
        'views/main_menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'web/static/lib/jquery/jquery.js',
            'odoo_ai_agent/static/src/css/dashboard.scss',
            'odoo_ai_agent/static/src/css/kanban_style.scss',
            'odoo_ai_agent/static/src/js/ai_agent_details.js',
            'odoo_ai_agent/static/src/xml/ai_agent_details.xml',
            'odoo_ai_agent/static/src/img/loader.gif',
            'odoo_ai_agent/static/src/js/x2many_accordion_field.js',
            'odoo_ai_agent/static/src/xml/x2many_accordion_field.xml',
            'odoo_ai_agent/static/src/js/accordion_item.js',
            'odoo_ai_agent/static/src/xml/accordion_item.xml',
            'odoo_ai_agent/static/src/js/form_renderer.js',
            'odoo_ai_agent/static/src/js/agent_dashboard.js',
            'odoo_ai_agent/static/src/xml/agent_dashboard.xml',
            'odoo_ai_agent/static/src/js/x2many_field.js',
            'odoo_ai_agent/static/src/js/kanbanheader.js',
            'odoo_ai_agent/static/src/xml/kanbanrender.xml',
            # ('before','web_enterprise/static/src/views/kanban/kanban_header_patch.js', 'odoo_ai_agent/static/src/js/kanbanheader.js')
        ],
    },

    'images': ['static/description/banner.gif'],
    'pre_init_hook': 'pre_init_url',
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': '_uninstall_hook_odoo_ai_agent',
    'installable': True,
    'application': True,
}
