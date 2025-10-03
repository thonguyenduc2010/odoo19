/** @odoo-module **/

import { registry } from "@web/core/registry";
import { CANCEL_GLOBAL_CLICK, KanbanRecord } from "@web/views/kanban/kanban_record";
import { kanbanView } from "@web/views/kanban/kanban_view";
import { useService } from "@web/core/utils/hooks";
import { KanbanRenderer } from "@web/views/kanban/kanban_renderer";

export class AgentKanbanRenderer extends KanbanRenderer {
    setup() {
        super.setup();
    }
}

AgentKanbanRenderer.components = {
    ...KanbanRenderer.components,
};
AgentKanbanRenderer.template = "ai_agent.AgentKanbanRenderer";
