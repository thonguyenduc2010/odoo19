/* @odoo-module */
import { patch } from "@web/core/utils/patch";
import { X2ManyField, x2ManyField } from "@web/views/fields/x2many/x2many_field";


patch(X2ManyField.prototype, {
    async openRecord(record) {
        if (this.canOpenRecord) {
            if (record.resModel === 'agent.response.history.step'){
                if (this.env.debug){
                    return this._openRecord({
                        record,
                        context: this.props.context,
                        mode: this.props.readonly ? "readonly" : "edit",
                    });
                }
            } else {
                return this._openRecord({
                    record,
                    context: this.props.context,
                    mode: this.props.readonly ? "readonly" : "edit",
                });
            }
        }
    }
})

