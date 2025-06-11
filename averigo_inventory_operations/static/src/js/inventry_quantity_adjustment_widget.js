/** @odoo-module **/

import {registry} from "@web/core/registry";
import {Component, useState, onWillStart, onWillUpdateProps} from "@odoo/owl";
import {standardFieldProps} from "@web/views/fields/standard_field_props";

export class InventoryQuantAdjustment extends Component {
    static template = "averigo_inventory_operations.InventoryQuantAdjustment";

    setup() {
        this.props.readonly = this.props.record.data.state === "confirm" ? false : true;
        this.state = useState({
            value: this.props.record.data[this.props.name] || 0,
        });

        onWillStart(() => {
            this.state.value = this.props.record.data[this.props.name] || 0;
        });

        onWillUpdateProps((nextProps) => {
            this.state.value = nextProps.record.data[nextProps.name] || 0;
        });
    }

    /**
     * Handle input changes - only allow numbers
     */
    onInput(ev) {
        let value = ev.target.value;

        // Remove any non-numeric characters except decimal point and minus sign
        value = value.replace(/[^0-9.-]/g, '');

        // Ensure only one decimal point
        const parts = value.split('.');
        if (parts.length > 2) {
            value = parts[0] + '.' + parts.slice(1).join('');
        }

        // Ensure only one minus sign at the beginning
        if (value.indexOf('-') > 0) {
            value = value.replace(/-/g, '');
        }
        if (value.split('-').length > 2) {
            value = '-' + value.replace(/-/g, '');
        }

        // Update input value
        ev.target.value = value;
        this.state.value = value;
    }

    /**
     * Handle blur event - save the value
     */
    async onBlur(ev) {
        const value = ev.target.value;
        const floatValue = parseFloat(value) || 0;

        // Update the record
        await this.props.record.update({
            inventory_quantity: floatValue
        });
    }

    /**
     * Handle keypress - prevent non-numeric input
     */
    onKeyPress(ev) {
        const char = String.fromCharCode(ev.which);
        const currentValue = ev.target.value;

        // Allow: backspace, delete, tab, escape, enter
        if ([8, 9, 27, 13, 46].indexOf(ev.keyCode) !== -1 ||
            // Allow: Ctrl+A, Ctrl+C, Ctrl+V, Ctrl+X
            (ev.keyCode === 65 && ev.ctrlKey === true) ||
            (ev.keyCode === 67 && ev.ctrlKey === true) ||
            (ev.keyCode === 86 && ev.ctrlKey === true) ||
            (ev.keyCode === 88 && ev.ctrlKey === true)) {
            return;
        }

        // Allow: numbers, decimal point, minus sign
        if (!/[0-9\.-]/.test(char)) {
            ev.preventDefault();
            return;
        }

        // Allow only one decimal point
        if (char === '.' && currentValue.indexOf('.') !== -1) {
            ev.preventDefault();
            return;
        }

        // Allow minus only at the beginning
        if (char === '-' && currentValue.length > 0) {
            ev.preventDefault();
            return;
        }
    }

    /**
     * Handle paste event - clean pasted content
     */
    onPaste(ev) {
        setTimeout(() => {
            let value = ev.target.value;

            // Clean the pasted value
            value = value.replace(/[^0-9.-]/g, '');

            // Ensure only one decimal point
            const parts = value.split('.');
            if (parts.length > 2) {
                value = parts[0] + '.' + parts.slice(1).join('');
            }

            // Ensure only one minus sign at the beginning
            if (value.indexOf('-') > 0) {
                value = value.replace(/-/g, '');
            }
            if (value.split('-').length > 2) {
                value = '-' + value.replace(/-/g, '');
            }

            ev.target.value = value;
            this.state.value = value;
        }, 0);
    }
}

// Register the widget
registry.category("fields").add("inventory_quant_adjustment", {
    component: InventoryQuantAdjustment,
    supportedTypes: ["float"],
});