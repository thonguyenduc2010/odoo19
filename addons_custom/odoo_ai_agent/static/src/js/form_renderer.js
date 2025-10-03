/* @odoo-module */

import { FormRenderer } from "@web/views/form/form_renderer";
import { onMounted, onWillUnmount, useState } from "@odoo/owl";

import { browser } from "@web/core/browser/browser";
import { SIZES } from "@web/core/ui/ui_service";
import { useService } from "@web/core/utils/hooks";
import { patch } from "@web/core/utils/patch";

patch(FormRenderer.prototype, {
    setup(){
        super.setup();
        onMounted(() => {
            $('.ai-agent-response-table-container td').on('mouseover',function(){
                var table1 = $(this).parent().parent().parent();
                var table2 = $(this).parent().parent();
                var column = this.classList[0];

                $(table2).find("."+column).addClass('hov-column');
                $(table1).find("th."+column).addClass('hov-column-head');
            });

            $('.ai-agent-response-table-container th').on('mouseover',function(){
                var table1 = $(this).parent().parent().parent();
                var table2 = $(this).parent().parent();
                var column = this.classList[0];

                $(table2).find("."+column).addClass('hov-column');
                $(table1).find("th."+column).addClass('hov-column-head');
            });

            $('.ai-agent-response-table-container td').on('mouseout',function(){
                var table1 = $(this).parent().parent().parent();
                var table2 = $(this).parent().parent();
                var column = this.classList[0];

                $(table2).find("."+column).removeClass('hov-column');
                $(table1).find("th."+column).removeClass('hov-column-head');
            });
            $('.ai-agent-response-table-container th').on('mouseout',function(){
                var table1 = $(this).parent().parent().parent();
                var table2 = $(this).parent().parent();
                var column = this.classList[0];

                $(table2).find("."+column).removeClass('hov-column');
                $(table1).find("th."+column).removeClass('hov-column-head');
            });
        });
    }
});