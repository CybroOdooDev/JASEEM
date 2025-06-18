/** @odoo-module */
import {X2ManyField, x2ManyField} from "@web/views/fields/x2many/x2many_field";
import {registry} from "@web/core/registry";
import {useRef, onMounted, onWillUnmount, onWillRender} from "@odoo/owl";

export class NavigateOne2Many extends X2ManyField {
    static template = "web.X2ManyField";

    setup() {
        super.setup();
        this.root = useRef("rootX2ManyField");
        this.listRenderer = useRef("listRenders");
        this.currentRow = -1; // Initialize to -1 to indicate no row is focused
        this.currentCol = -1; // Initialize to -1 to indicate no column is focused
        this._list = null; // Store list data
        this._rows = []; // Store rows
        this._columns = []; // Store columns
        this._previousEditingRecord = null; // Track the previously editing record

        onMounted(() => {
            if (this.root.el) {
                this.root.el.addEventListener("keydown", this.onKeyDown.bind(this));
                // Initialize list, rows, and columns after DOM is rendered
                this.updateTableData();
            }
        });

        onWillRender(() => {
            // Update table data before rendering to ensure rows and columns are current
            this.updateTableData();
        });

        onWillUnmount(() => {
            if (this.root.el) {
                this.root.el.removeEventListener("keydown", this.onKeyDown.bind(this));
            }
        });
    }

    updateTableData() {
        this._list = this.getList();
        this._columns = this.getColumns();
        this._rows = this.getRows();
        console.log("Table Data Updated:", {
            list: this._list,
            rows: this._rows.length,
            columns: this._columns.length,
        });
    }

    getList() {
        return this.props.record.data[this.props.name];
    }

    getColumns() {
        // Filter out non-data columns (e.g., handle, button_group, selectors)
        const columns = this.listRenderer.el?.querySelectorAll("thead th[data-name]:not([data-name='handle'])") || [];
        return Array.from(columns).filter(col => {
            const fieldName = col.dataset.name;
            const field = this._list?.fields[fieldName];
            // Include only columns that are fields and not button groups or widgets
            return field && !["button_group", "widget"].includes(field.type);
        });
    }

    getRows() {
        return this.listRenderer.el?.querySelectorAll("tbody tr.o_data_row") || [];
    }

    async exitEditMode(record) {
        if (record && record.isInEdition) {
            try {
                // Save the current record and exit edit mode
                await this._list.leaveEditMode(record);
                console.log("Successfully exited edit mode for record:", record.resId);
            } catch (error) {
                console.warn("Error exiting edit mode:", error);
                // Force exit edit mode even if save fails
                if (record.isInEdition) {
                    record.isInEdition = false;
                }
            }
        }
    }

    async onKeyDown(event) {
        if (!["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"].includes(event.key)) {
            return;
        }

        // Prevent default browser behavior and stop propagation to avoid conflicts
        event.preventDefault();
        event.stopPropagation();

        // Update table data to ensure we have the latest rows and columns
        this.updateTableData();

        const rows = this._rows;
        const cols = this._columns;

        // Check if the One2Many tree exists and is rendered
        if (!rows.length || !cols.length || !this.listRenderer.el) {
            console.warn("No One2Many tree found or not rendered.");
            return;
        }

        // Store the current editing record before navigation
        const currentEditingRecord = this._list.records.find(record => record.isInEdition);

        // Initialize focus on the first editable cell if no cell is currently focused
        if (this.currentRow === -1 || this.currentCol === -1) {
            this.currentRow = 0; // Start with the first row
            this.currentCol = this.findFirstEditableColumn(0); // Find the first editable column
            await this.focusCell();
            return;
        }

        const previousRow = this.currentRow;
        const previousCol = this.currentCol;

        switch (event.key) {
            case "ArrowUp":
                if (this.currentRow > 0) {
                    this.currentRow--;
                    this.currentCol = this.findFirstEditableColumn(this.currentRow); // Get editable column in the new row
                }
                break;
            case "ArrowDown":
                if (this.currentRow < rows.length - 1) {
                    this.currentRow++;
                    this.currentCol = this.findFirstEditableColumn(this.currentRow); // Get editable column in the new row
                }
                break;
            case "ArrowLeft":
                if (this.currentCol > 0) {
                    this.currentCol--;
                }
                break;
            case "ArrowRight":
                if (this.currentCol < cols.length - 1) {
                    this.currentCol++;
                }
                break;
        }

        // Only proceed if the position actually changed
        if (previousRow !== this.currentRow || previousCol !== this.currentCol) {
            // Exit edit mode from the previous record if we're changing rows
            if (previousRow !== this.currentRow && currentEditingRecord) {
                await this.exitEditMode(currentEditingRecord);
            }

            await this.focusCell();
        }
    }

    findFirstEditableColumn(rowIndex) {
        const row = this._rows[rowIndex];
        if (!row) return 0;

        const cols = this._columns;
        for (let i = 0; i < cols.length; i++) {
            const colName = cols[i].dataset.name;
            const cell = row.querySelector(`td[name="${colName}"]`);
            if (cell && !cell.classList.contains("o_readonly_modifier")) {
                return i;
            }
        }
        return 0; // Fallback to first column if no editable column is found
    }

    async focusCell() {
        const rows = this._rows;
        const cols = this._columns;

        // Remove the selected-cell class from previously focused cell
        if (this._previousRow !== undefined && this._previousCol !== undefined) {
            const prevRowEl = rows[this._previousRow];
            const prevColName = cols[this._previousCol]?.dataset.name;
            if (prevRowEl && prevColName) {
                const prevCell = prevRowEl.querySelector(`td[name="${prevColName}"]`);
                if (prevCell) {
                    prevCell.classList.remove("selected-cell");
                }
            }
        }

        if (!rows[this.currentRow] || !cols[this.currentCol]) {
            console.warn(`No valid row or column at row ${this.currentRow}, col ${this.currentCol}`);
            return;
        }

        const row = rows[this.currentRow];
        const colName = cols[this.currentCol].dataset.name;
        const cell = row.querySelector(`td[name="${colName}"]`);

        if (!cell) {
            console.warn(`Cell not found for row ${this.currentRow}, column ${colName}`);
            return;
        }

        // Add the selected-cell class to the currently focused cell
        cell.classList.add("selected-cell");

        // Store the current indices for next focusCell call
        this._previousRow = this.currentRow;
        this._previousCol = this.currentCol;

        // Update table to indicate keyboard navigation
        this.listRenderer.el.querySelector("tbody")?.classList.add("o_keyboard_navigation");

        // Get the record for the current row
        const record = this._list.records[this.currentRow];

        // Enter edit mode for the new record if the cell is editable
        if (record && !record.isInEdition && !cell.classList.contains("o_readonly_modifier")) {
            try {
                await this._list.enterEditMode(record);
                console.log("Entered edit mode for record:", record.resId);

                // Wait for the DOM to update after entering edit mode
                await new Promise(resolve => setTimeout(resolve, 0));

                // Re-query the cell after entering edit mode as the DOM might have changed
                const updatedCell = row.querySelector(`td[name="${colName}"]`);
                if (updatedCell) {
                    // Find focusable element within the updated cell
                    const focusable = updatedCell.querySelector("input, select, textarea, button, [tabindex]:not([tabindex='-1'])");
                    if (focusable) {
                        console.log("Focusable element found:", focusable);
                        focusable.focus();
                        if (["INPUT", "TEXTAREA"].includes(focusable.tagName)) {
                            focusable.select();
                        }
                    } else {
                        // Fallback to cell itself if no focusable element is found
                        updatedCell.setAttribute("tabindex", "0");
                        updatedCell.focus();
                        console.log(`No focusable element in cell at row ${this.currentRow}, column ${colName}`);
                    }
                }
            } catch (error) {
                console.warn("Error entering edit mode:", error);
                // Fallback to just focusing the cell
                cell.setAttribute("tabindex", "0");
                cell.focus();
            }
        } else {
            // If not entering edit mode, just focus the cell
            const focusable = cell.querySelector("input, select, textarea, button, [tabindex]:not([tabindex='-1'])");
            if (focusable) {
                focusable.focus();
                if (["INPUT", "TEXTAREA"].includes(focusable.tagName)) {
                    focusable.select();
                }
            } else {
                cell.setAttribute("tabindex", "0");
                cell.focus();
            }
        }
    }
}

registry.category("fields").add("navigate_one2many", {
    ...x2ManyField,
    component: NavigateOne2Many,
});