/** @odoo-module **/
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { usePopover } from "@web/core/popover/popover_hook";
import { Component } from "@odoo/owl";
import { formatDate, deserializeDate } from "@web/core/l10n/dates";


export class aiAgentDetailsPopover extends Component {
    setup() {
        this.actionService = useService("action");
    }
}
aiAgentDetailsPopover.template = "ai_agents.aiAgentDetailsPopover";

export class AiAgentDetailsButton extends Component {
    static template = "ai_agents.aiAgentDetailsButton";
    setup() {
        this.actionService = useService("action");
        this.orm = useService("orm");
        this.popover = usePopover(aiAgentDetailsPopover, {
            popoverClass: "custom_popover_design",
            placement: "top",
        });
    }

    formatDate(date) {
        const pad = (n) => n.toString().padStart(2, '0');

        const day = pad(date.day);
        const month = pad(date.month);
        const year = date.year;

        const hours = pad(date.hour);
        const minutes = pad(date.minute);
        const seconds = pad(date.second);

        return `${month}/${day}/${year} ${hours}:${minutes}:${seconds}`;
    }


    onClick(ev) {
        if (this.popover.isOpen) {
            this.popover.close();
        } else {
            const resId = this.props.record.resId;
            let last_run = this.props.record.data.last_run ? this.formatDate(this.props.record.data.last_run) : false;
            // const selectedRecords = this.env?.model?.root?.selection ?? [];
            // const selectedIds = selectedRecords.map((r) => r.resId);
            // const resIds =
            //     selectedIds.includes(resId) && selectedIds.length > 1 ? selectedIds : undefined;
            this.popover.open(ev.currentTarget, {
                record: this.props.record,
                resId: resId,
                last_run: last_run,
                onResultButtonClick: this.onResultButtonClick.bind(this),
                onViewButtonClick: this.onViewButtonClick.bind(this),
                onRunNowButtonClick: this.onRunNowButtonClick.bind(this),
                onScheduleButtonClick: this.onScheduleButtonClick.bind(this),
                onConfigureButtonClick: this.onConfigureButtonClick.bind(this),
                // resIds: resIds,
                resModel: this.props.record.resModel,
            });
        }
    }

    onViewButtonClick(ev) {
        const resId = this.props.record.resId;
        let action = this.orm.call(
            this.props.record.resModel,
            "get_list_response",
            [resId],
        );
        this.actionService.doAction(action);
        this.popover.close();
        ev.stopPropagation();
    }

    onResultButtonClick(ev){
        const resId = this.props.record.resId;
        let action = this.orm.call(
            this.props.record.resModel,
            "get_last_response_form",
            [resId],
        );
        this.actionService.doAction(action);
        this.popover.close();
        ev.stopPropagation();
    }

    async onRunNowButtonClick(ev) {
        const resId = this.props.record.resId;
        // update status field

        await this.orm.call(
            this.props.record.resModel,
            "change_status_to_running",
            [resId],
        );
        this.props.record.update({
            status: "running",
            last_run: luxon.DateTime.now(),
//            next_run: this.props.record.data.next_run,
        });
        // rerender the kanban view
        // this.props.record.trigger("kanban_record_updated");
        let action = await this.orm.call(
            this.props.record.resModel,
            "run_agent",
            [resId],
        );
        this.actionService.doAction(action);
        if (action) {
            this.props.record.update({
                status: "to_review",
            });
        }
        
        this.popover.close();
        ev.stopPropagation();
    }

    onScheduleButtonClick(ev) {
        const resId = this.props.record.resId;
        let action = this.orm.call(
            this.props.record.resModel,
            "schedule_agent",
            [resId],
        );
        this.actionService.doAction(action);
        this.popover.close();
        ev.stopPropagation();
    }

    onConfigureButtonClick(ev) {
        const resId = this.props.record.resId;
        let action = this.orm.call(
            this.props.record.resModel,
            "show_details",
            [resId],
        );
        this.actionService.doAction(action);
        this.popover.close();
        ev.stopPropagation();
    }
}


export const aiAgentDetailsButton = {
    component: AiAgentDetailsButton,
//    dependencies: ["action"],
}

registry.category("view_widgets").add("agent_details", aiAgentDetailsButton);

