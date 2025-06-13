/** @odoo-module */

import {X2ManyField, x2ManyField} from "@web/views/fields/x2many/x2many_field";
import {registry} from "@web/core/registry";
import {useExternalListener} from "@web/core/utils/hooks";
import {useRef} from "@odoo/owl";

export class NavigateOne2Many extends X2ManyField {
    setup() {
        super.setup();
        this.root = useRef('rootX2ManyField');
        this.currentRow = 0; // Track the current row index
        this.currentCol = 0; // Track the current column index
    }

    onMounted() {
        // Use the external listener for keyboard events after the component is mounted
        console.log("NavigateOne2Many", this.root.el);

        useExternalListener(this.root.el, 'keydown', this.onKeyDown.bind(this));
    }

    onKeyDown(event) {
        const rows = this.list.records; // Get the list of records
        const cols = this.props.relatedFields; // Get the fields (columns)

        switch (event.key) {
            case 'ArrowUp':
                if (this.currentRow > 0) {
                    this.currentRow--;
                    this.focusCell();
                }
                break;
            case 'ArrowDown':
                if (this.currentRow < rows.length - 1) {
                    this.currentRow++;
                    this.focusCell();
                }
                break;
            case 'ArrowLeft':
                if (this.currentCol > 0) {
                    this.currentCol--;
                    this.focusCell();
                }
                break;
            case 'ArrowRight':
                if (this.currentCol < cols.length - 1) {
                    this.currentCol++;
                    this.focusCell();
                }
                break;
            default:
                break;
        }
    }

    focusCell() {
        const rows = this.list.records;
        const cols = this.props.relatedFields;

        // Get the current cell element
        const cell = this.el.querySelector(`.o_list_record[data-index="${this.currentRow}"] .o_list_cell[data-field="${cols[this.currentCol].name}"]`);
        if (cell) {
            cell.focus(); // Focus the current cell
        }
    }
}

registry.category("fields").add("navigate_one2many", {
    ...x2ManyField,
    component: NavigateOne2Many,
});
