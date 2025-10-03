/** @odoo-module **/

import { Component, onWillStart, onMounted, useEnv,useSubEnv, useState, useComponent, status } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService,useChildRef } from "@web/core/utils/hooks";
import { ControlPanel } from "@web/search/control_panel/control_panel";
import { Field } from "@web/views/fields/field";
import { Record } from "@web/model/record";
import { AccordionItem } from "./accordion_item";
import { markup } from "@odoo/owl";
import { executeButtonCallback, useViewButtons } from "@web/views/view_button/view_button_hook";

const viewRegistry = registry.category("views");

export class AgentDashboard extends Component {
    static template = "ai_agents.AgentDashboard";
    static components = {
        ControlPanel,
        Field,
        Record,
        AccordionItem
    };
    
    setup() {
        this.modalRef = useChildRef();
        this.actionService = useService("action");
        const action_var = useService("action");
        const comp = useComponent();
        this.orm = useService("orm");
        this.action = useService("action");
        this.env = useEnv();
        this.agents = [];
        this.agent_group = [];
        this.controlPanelDisplay = {}
        const { ArchParser } = viewRegistry.get('form');
        this.state = useState({
            records: [],
            activeAgent: [],
            agentHistory: [],
            expanded: false
        })
        this.allbuttons = []
        this.recordInfo = {
            model: "copilot.agent.dashboard",
            specification: { name: {} },
        };

        useSubEnv({
            async onClickViewButton({ clickParams, getResParams, beforeExecute }) {
                // const el = getEl();
                async function execute() {
                    let _continue = true;
                    const closeDialog =
                        (clickParams.close || clickParams.special) && env.dialogData?.close;
                    const params = getResParams();
                    const resId = params.resId;
                    const resIds = params.resIds || model.resIds;
                    let buttonContext = {};
                    if (clickParams.context) {
                        if (typeof clickParams.context === "string") {
                            buttonContext = evaluateExpr(clickParams.context, params.evalContext);
                        } else {
                            buttonContext = clickParams.context;
                        }
                    }
                    if (clickParams.buttonContext) {
                        Object.assign(buttonContext, clickParams.buttonContext);
                    }
                    const doActionParams = Object.assign({}, clickParams, {
                        resModel: params.resModel || model.resModel,
                        resId,
                        resIds,
                        context: params.context || {}, //LPE FIXME new Context(payload.env.context).eval();
                        buttonContext
                    });
                    let error;
                    try {
                        await action_var.doActionButton(doActionParams);
                    } catch (_e) {
                        error = _e;
                    }
                    if (closeDialog) {
                        closeDialog();
                    }
                    if (error) {
                        return Promise.reject(error);
                    }
                }

                if (clickParams.confirm) {
                    executeButtonCallback(getEl(), async () => {
                        await new Promise((resolve) => {
                            const dialogProps = {
                                ...(clickParams["confirm-title"] && {
                                    title: clickParams["confirm-title"],
                                }),
                                ...(clickParams["confirm-label"] && {
                                    confirmLabel: clickParams["confirm-label"],
                                }),
                                body: clickParams.confirm,
                                confirm: () => execute(),
                                cancel: () => {},
                            };
                            dialog.add(ConfirmationDialog, dialogProps, { onClose: resolve });
                        });
                    });
                } else {
                    return executeButtonCallback(getEl(), execute);
                }
            },
        })
        
        function getEl() {
            return document;
        }
        function undefinedAsTrue(val) {
            return typeof val === "undefined" || val;
        }

        // const { ArchParser } = viewRegistry.get("form");
        // const archInfo = new ArchParser().parse("", {}, "agent.response.history");
        onWillStart(async () => {
            this.agents = await this.orm.searchRead("copilot.agent.dashboard", [], ["name","agent_group", "category_id", "status", 'last_run']);
            console.log(this.agents);
            if (this.agents && this.agents.length > 0) {
                this.agents.forEach(element => {
                    if (element.status === 'done'){
                        element.status = ['done','Done']
                    }
                    else if (element.status === 'to_review'){
                        element.status = ['to_review','To Review']
                    }
                    else if (element.status === 'to_run'){
                        element.status = ['to_run','To Run']
                    }
                    else if (element.status === 'running'){
                        element.status = ['running','Running']
                    }
                    else if (element.status === 'failed'){
                        element.status = ['failed','Failed']
                    }

                });
                // Formate timestamp with local timezone
                this.agents.forEach(element => {
                    if (element.last_run) {
                        element.last_run = luxon.DateTime.fromString(element.last_run, "yyyy-MM-dd HH:mm:ss",{ zone: "UTC" }).toLocal().toLocaleString(luxon.DateTime.DATETIME_MED);
                    }
                });

                this.agent_group = this.agents.reduce((acc, agent) => {
                    const [id, name] = agent.category_id;
                    const groupName = agent.agent_group.toUpperCase();
                    if (!acc[groupName]) {
                        acc[groupName] = {};
                    }
                    if (!acc[groupName][id]) {
                        acc[groupName][id] = { name: name, items: [] };
                    }
                    acc[groupName][id].items.push(agent);
                    return acc;
                }, {})
                this.state.activeAgent = this.agents.map(agent => agent.id);
                if(this.props.action.dashboard_id){
                    this.state.activeAgent = [this.props.action.dashboard_id];
                }
                var agentHistory = await this.orm.call("agent.response.history", "fetch_last_agent_response", [this.state.activeAgent]);
                if (agentHistory && agentHistory.length > 0) {
                    console.log(agentHistory);
                    this.state.agentHistory = agentHistory[0];
                    // var stepsData = (await this.orm.call(
                    //     "agent.response.history",
                    //     "get_steps_data",
                    //     [[this.state.agentHistory.id]]
                    // ));
                    var stepsData = agentHistory;
                    if (stepsData && stepsData.length > 0) {
                        for (var i = 0; i < stepsData.length; i++) {
                            var step = stepsData[i];
                            var agent_id = step.agent_id;
                            var status = step.status;
                            var history_id = step.history_id;
                            var buttons = step.buttons;
                            var last_run = step.last_run;
                            if (last_run){
                                last_run = luxon.DateTime.fromString(last_run, "yyyy-MM-dd HH:mm:ss",{ zone: "UTC" }).toLocal().toLocaleString(luxon.DateTime.DATETIME_MED);
                            }
                            this.allbuttons = buttons;
                            //remove agent_id and status
                            delete step.agent_id;
                            delete step.status;
                            delete step.history_id;
                            delete step.buttons;
                            delete step.last_run;
                            if (status === 'to_review'){
                                status = ['to_review','To Review'];
                            }
                            else if (status === 'to_run'){
                                status = ['to_run','To Run'];
                            }
                            else if (status === 'running'){
                                status = ['running','Running'];
                            }
                            else if (status === 'failed'){
                                status = ['failed','Failed'];
                            }
                            else if (status === 'done'){
                                status = ['done','Done'];
                            }
                            Object.entries(step).forEach(([key, value]) => {
                                var data = [];
                                for (var v of value){
                                    data.push({
                                        id: v.id,
                                        resId: v.id,
                                        resIds: [v.id],
                                        resModel: 'agent.response.history.step',
                                        has_user_confirmation: v.has_user_confirmation,
                                        title: v.title,
                                        text_response: v.text_response? markup(v.text_response) : '',
                                        text: v.text,
                                        current_role: v.current_role,
                                        final_step: v.final_step,
                                        output_response: v.output_response,
                                        template_id: v.template_id,
                                        evalContextWithVirtualIds:{
                                            active_id: v.id,
                                            active_ids: [v.id],
                                            active_model: 'agent.response.history.step',
                                            final_step: v.final_step,
                                            id: v.id,
                                        }
                                    });
                                }
                                this.state.records.push([key, data, status, agent_id, history_id, buttons, last_run]);

                            });
                        }
                    }
                }
            }
        });

        onMounted(() => {
            if(this.props.action.dashboard_id) {
                var active_nav = document.querySelector(".agent_nav_btn[data-record-id='" + this.props.action.dashboard_id + "']");
                document.querySelectorAll(".agent_nav_btn").forEach((ele) => {
                    if (ele !== active_nav) {
                        ele.classList.remove("active");
                    }
                });
                active_nav.classList.add("active");
                this.state.expanded = true;
            }
        });
    }

    getEl() {
        return this.env.inDialog ? this.modalRef.el.closest(".modal") : this.modalRef.el;
    }

    onExpandButtonClick(ev) {
        var self = this;
        const agentId = [parseInt(ev.currentTarget.dataset.agentId)];
        if (agentId){
            document.querySelector(".agent_nav_btn[data-record-id='" + agentId + "']").click();
            ev.currentTarget.classList.toggle("d-none");
            ev.stopPropagation();
        }
        
    }

    onCollapseButtonClick(ev) {
        var self = this;
        var action = this.orm.call("copilot.agent.dashboard", "close_full_view", [[]]);
        if (action) {
            this.state.expanded = false;
            this.actionService.doAction(action);
        }
    }

    async onClickAgent(ev) {
        this.state.records = [];
        var self = this;
        this.state.expanded = true;
        ev.currentTarget.classList.add("active");
        document.querySelectorAll(".agent_nav_btn").forEach((ele) => {
            if (ele !== ev.currentTarget) {
                ele.classList.remove("active");
            }
        });
        const agentId = [parseInt(ev.currentTarget.dataset.recordId)];
        this.state.activeAgent = agentId;
        this.state.records = []
        var agentHistory = await this.orm.call("agent.response.history", "fetch_last_agent_response", [this.state.activeAgent]);
        if (agentHistory && agentHistory.length > 0) {
            this.state.agentHistory = agentHistory[0];
            // var stepsData = (await this.orm.call(
            //     "agent.response.history",
            //     "get_steps_data",
            //     [[this.state.agentHistory.id]]
            // ));
            var stepsData = agentHistory;
            if (stepsData && stepsData.length > 0) {
                for (var i = 0; i < stepsData.length; i++) {
                    var step = stepsData[i];
                    var agent_id = step.agent_id;
                    var status = step.status;
                    var history_id = step.history_id;
                    var buttons = step.buttons;
                    this.allbuttons = buttons;
                    var last_run = step.last_run;
                    if (last_run){
                        last_run = luxon.DateTime.fromString(last_run, "yyyy-MM-dd HH:mm:ss",{ zone: "UTC" }).toLocal().toLocaleString(luxon.DateTime.DATETIME_MED);
                    }
                    //remove agent_id and status
                    delete step.agent_id;
                    delete step.status;
                    delete step.history_id;
                    delete step.buttons;
                    delete step.last_run;
                    if (status === 'to_review'){
                        status = ['to_review','To Review'];
                    }
                    else if (status === 'to_run'){
                        status = ['to_run','To Run'];
                    }
                    else if (status === 'running'){
                        status = ['running','Running'];
                    }
                    else if (status === 'failed'){
                        status = ['failed','Failed'];
                    }
                    else if (status === 'done'){
                        status = ['done','Done'];
                    }
                    Object.entries(step).forEach(([key, value]) => {
                        var data = [];
                        for (var v of value){
                            data.push({
                                id: v.id,
                                resId: v.id,
                                resIds: [v.id],
                                resModel: 'agent.response.history.step',
                                has_user_confirmation: v.has_user_confirmation,
                                title: v.title,
                                text_response: v.text_response? markup(v.text_response) : '',
                                text: v.text,
                                current_role: v.current_role,
                                final_step: v.final_step,
                                output_response: v.output_response,
                                template_id: v.template_id,
                                evalContextWithVirtualIds:{
                                    active_id: v.id,
                                    active_ids: [v.id],
                                    active_model: 'agent.response.history.step',
                                    final_step: v.final_step,
                                    id: v.id,
                                }
                            });
                        }
                        this.state.records.push([key, data, status, agent_id, history_id, buttons, last_run]);

                    });
                }
            }
        }
    }

    openSingleAgentView(agentId){

    }

    async onRunNowButtonClick(ev){
        const agentId = parseInt(ev.currentTarget.dataset.agentId);

        this.changeAgentAndNavStatus(agentId, ['running', 'Running']);

        let action = await this.orm.call(
            'copilot.agent.dashboard',
            "run_agent",
            [agentId],
        );
        if (action) {
            this.actionService.doAction(action);
            this.changeAgentAndNavStatus(agentId, ['to_review', 'To Review']);
            document.querySelector(".agent_nav_btn[data-record-id='" + agentId + "']").click();
        }
    }

    changeAgentAndNavStatus(agentId, status){
        var record_index = this.state.records.findIndex(record => record[3] === agentId);
        if (record_index !== -1) {
            this.state.records[record_index][2] = status;
        }
        for (const key in this.agent_group){
            Object.entries(this.agent_group[key]).forEach(([agentCat, agentData]) => {
                Object.entries(agentData.items).forEach(([index, agent]) => {
                    if (agent.id === agentId) {
                        agent.status = status;
                    }
                });
            });
        }
    }

    onConfigureButtonClick(ev) {
        const resId = parseInt(ev.currentTarget.dataset.agentId);
        let action = this.orm.call(
            'copilot.agent.dashboard',
            "show_details",
            [resId],
        );
        this.actionService.doAction(action);
        ev.stopPropagation();
    }

    async onClickDownloadAgentPDF(ev){
        var history_id = parseInt(ev.currentTarget.dataset.historyId);
        let action = await this.orm.call("agent.response.history", "action_download_pdf", [history_id])
        if (action) {
            this.action.doAction(action);
        }
    }

    async onClickDownloadAgentExcel(ev){
        var history_id = parseInt(ev.currentTarget.dataset.historyId);
        let action = await this.orm.call("agent.response.history", "excel_export", [history_id])
        if (action) {
            this.action.doAction(action);
        }
    }

}

registry.category("actions").add("ai_agent_dashboard", AgentDashboard);
