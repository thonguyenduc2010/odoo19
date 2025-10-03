/* @odoo-module */
import { patch } from "@web/core/utils/patch";
import { KanbanHeader } from "@web/views/kanban/kanban_header";
import { GroupConfigMenu } from "@web/views/view_components/group_config_menu";
import { registry } from "@web/core/registry";

import { KanbanRenderer } from "@web/views/kanban/kanban_renderer";
import { Component, onMounted } from "@odoo/owl";
import { usePopover } from "@web/core/popover/popover_hook";

patch(GroupConfigMenu.prototype, {
    setup(){
        super.setup();
    },
    get configItems() {
        const args = { permissions: this.permissions };
        // if (this.props.list.resModel === 'copilot.agent.dashboard' && args.permissions.canEditAutomations === true){
        //     args.permissions.canEditAutomations = false;
        // }
        return this.props.configItems
            .filter(([key, desc]) => {
                if (this.props.list.resModel === 'copilot.agent.dashboard' && desc.method === 'openAutomations'){
                    return false;
                }
                return true;
            })
            .map(([key, desc]) => (
                {
                key,
                label: desc.label,
                isVisible:
                    typeof desc.isVisible === "function" ? desc.isVisible(args) : desc.isVisible,
                class: typeof desc.class === "function" ? desc.class(args) : desc.class,
                icon: desc.icon,
                isVisible: typeof desc.isVisible === "function" ? desc.isVisible(args) : desc.isVisible,
                method: typeof desc.method === "function" ? desc.method : this[desc.method].bind(this),
            }));
    }
});

export class HelpTextPopOver extends Component {
    static props = {
        info: String,
        link: {
            type: String,
            optional: true,
            default: '#',
        },
        close: Function,
    };
    setup() {
        this.popoverClass = "aihelp_popover_design";
    }
}
HelpTextPopOver.template = "odoo_ai_agent.ExtraInfoTooltip";

export class AiHelpTextButton extends Component {
    static template = "odoo_ai_agent.AiHelpTextButton";
    static props = {
        record: Object,
        readonly: Boolean,
        info: {
            type: String,
            optional: true,
            default: '',
        },
        link: {
            type: String,
            optional: true,
            default: '#',
        },
    };
    setup() {
        this.helpTextPopOver = usePopover(HelpTextPopOver, {
            popoverClass: "aihelp_popover_design",
            placement: "bottom",
        });
    }
    onHelpIconClick(ev) {
        if (this.helpTextPopOver.isOpen) {
            this.helpTextPopOver.close();
        } else if (this.props.record.data.icon_text) {
            this.helpTextPopOver.open(ev.currentTarget,{
                info: this.props.record.data.icon_text && this.props.record.data.icon_text || '',
                link: this.props.record.data.icon_link && this.props.record.data.icon_link || '#'
            });
        }
    }
}

export const aiHelpTextButton = {
    component: AiHelpTextButton
};

registry.category("view_widgets").add("aiHelpTextButton", aiHelpTextButton);

