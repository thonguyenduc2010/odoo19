/** @odoo-module **/

import { makeContext } from "@web/core/context";
import { evaluateBooleanExpr } from "@web/core/py_js/py";
// import { AccordionItem } from "@copilot/js/accordion_item";
// import { AccordionItem } from "@web/core/dropdown/accordion_item";
import { AccordionItem } from "./accordion_item";
import { X2ManyField, x2ManyField } from "@web/views/fields/x2many/x2many_field";
import { _t } from "@web/core/l10n/translation";
import { Pager } from "@web/core/pager/pager";
import { registry } from "@web/core/registry";
import {
    useActiveActions,
    useAddInlineRecord,
    useOpenX2ManyRecord,
    useSelectCreate,
    useX2ManyCrud,
} from "@web/views/fields/relational_utils";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { KanbanRenderer } from "@web/views/kanban/kanban_renderer";
import { ListRenderer } from "@web/views/list/list_renderer";
import { computeViewClassName } from "@web/views/utils";
import { ViewButton } from "@web/views/view_button/view_button";
import { useService } from "@web/core/utils/hooks";

import { Component } from "@odoo/owl";

export class X2ManyAccordionField extends X2ManyField {
    static template = "ai_agents.X2ManyAccordionField";
    static components = {
        AccordionItem,
        Pager,
        ViewButton,
        KanbanRenderer,
        ListRenderer,
    };
    // static extractProps = ({ attrs })=> {
    //     return {
    //         labelField: attrs.labelField,
    //         contentField: attrs.contentField,
    //     };
    // }
    static props = {
        ...X2ManyField.props,
        labelField: {
            type: String,
            optional: true,
        },
        contentField: {
            type: String,
            optional: true,
        },
    }
    setup() {
        super.setup();
        const { saveRecord, updateRecord } = useX2ManyCrud(
            () => this.list,
            this.isMany2Many
        );

        const openRecord = useOpenX2ManyRecord({
            resModel: this.list.resModel,
            activeField: this.activeField,
            activeActions: this.activeActions,
            getList: () => this.list,
            saveRecord: async (record) => {
                await saveRecord(record);
                await this.props.record.save();
            },
            updateRecord: updateRecord,
            withParentId: this.props.widget !== "many2many",
        });

        this._openRecord = (params) => {
            params.title = this.getWizardTitleName();
            openRecord({...params});
        };
        this.buttons();
    }

    buttons() {
        var button_group = this.archInfo.columns.filter((columns) => columns.type === "button_group");
        var buttons = button_group.length ? button_group[0].buttons : [];
        this.allButtons = buttons;
    }
};

//export const x2ManyAccordionField = {
//    ...x2ManyField,
//    component: X2ManyAccordionField,
//    props: {
//        ...x2ManyField.props,
//        labelField: {
//            type: String,
//            optional: true,
//        },
//        contentField: {
//            type: String,
//            optional: true,
//        },
//    },
//};

export const x2ManyAccordionField = {
    ...x2ManyField,
    component: X2ManyAccordionField, // only this
};


registry.category("fields").add("x2many_accordion", x2ManyAccordionField);
