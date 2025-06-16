/** @odoo-module **/
import { registry } from "@web/core/registry";
import {Component, useRef} from "@odoo/owl";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { useService } from "@web/core/utils/hooks";

export class BooleanButtonWidget extends Component {
    static template = 'BooleanButtonWidget'

    setup() {
        this.label = this.props.string || this.props.name;
        this.input = useRef("inputConfirm");
        this.orm = useService("orm");
    }

    get value() {
        return this.props.record.data[this.props.name];
    }


    handleClick() {
        this.props.record.update({
            [this.props.name]: !this.value
        })
    }
}

BooleanButtonWidget.props = {
    ...standardFieldProps,
    string: { type: String, optional: true },
}

export const booleanButtonField = {
    component: BooleanButtonWidget,
    supportedTypes: ["boolean"],
    extractProps: ({ attrs }) => ({
        string: attrs.label,
    }),
};

registry.category("fields").add("bool_button", booleanButtonField);