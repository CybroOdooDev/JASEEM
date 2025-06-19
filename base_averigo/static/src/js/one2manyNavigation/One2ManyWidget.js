/** @odoo-module **/

import { onMounted, onWillUnmount, useRef } from "@odoo/owl";
import { patch } from "@web/core/utils/patch";
import { X2ManyField } from "@web/views/fields/x2many/x2many_field";

patch(X2ManyField.prototype, {
    setup() {
        super.setup();
        this.root = useRef("rootX2ManyField");
        this.onKeyDown = this.onKeyDown.bind(this);

        onMounted(() => {
            if (this.root.el) {
                this.root.el.addEventListener("keydown", this.onKeyDown);
            }
        });

        onWillUnmount(() => {
            if (this.root.el) {
                this.root.el.removeEventListener("keydown", this.onKeyDown);
            }
        });
    },

    async onKeyDown(event) {
        const { key } = event;
        if (!["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"].includes(key)) {
            return;
        }

        const activeElement = document.activeElement;
        const currentCell = activeElement.closest("td.o_data_cell");
        if (!currentCell) {
            console.debug("No current cell found for navigation.");
            return;
        }

        const currentRow = currentCell.closest("tr.o_data_row");
        if (!currentRow) {
            console.debug("No current row found for navigation.");
            return;
        }

        const rows = Array.from(this.root.el.querySelectorAll("tr.o_data_row"));
        const rowIndex = rows.indexOf(currentRow);
        if (rowIndex === -1) {
            console.debug("Current row not found in rows list.");
            return;
        }

        const cellsInRow = Array.from(currentRow.querySelectorAll("td.o_data_cell")).filter(
            (cell) => this._isEditableCell(cell)
        );
        const cellIndex = cellsInRow.indexOf(currentCell);
        if (cellIndex === -1) {
            console.debug("Current cell not found in editable cells.");
            return;
        }

        let targetRowIndex = rowIndex;
        let targetCellIndex = cellIndex;

        if (key === "ArrowUp" && rowIndex > 0) {
            targetRowIndex -= 1;
        } else if (key === "ArrowDown") {
            if (rowIndex < rows.length - 1) {
                targetRowIndex += 1;
            } else if (this.props.viewMode === "list" && this.rendererProps.editable) {
                console.debug("Creating new row on ArrowDown.");
                await this.onAdd({ position: "bottom" });
                // Wait for the new row to render
                setTimeout(() => this._focusFirstCellInLastRow(), 0);
                return;
            } else {
                console.debug("Cannot move down: last row reached and not editable.");
                return;
            }
        } else if (key === "ArrowRight" && cellIndex < cellsInRow.length - 1) {
            targetCellIndex += 1;
        } else if (key === "ArrowLeft" && cellIndex > 0) {
            targetCellIndex -= 1;
        } else {
            console.debug(`No navigation action for ${key} at row ${rowIndex}, cell ${cellIndex}.`);
            return;
        }

        const targetRow = rows[targetRowIndex];
        if (!targetRow) {
            console.debug(`Target row at index ${targetRowIndex} not found.`);
            return;
        }

        // Ensure the target row is in edit mode
        if (this.rendererProps.editable) {
            await this._makeRowEditable(targetRow, targetRowIndex);
        }

        const targetCells = Array.from(targetRow.querySelectorAll("td.o_data_cell")).filter(
            (cell) => this._isEditableCell(cell)
        );
        const targetCell = targetCells[targetCellIndex];

        if (targetCell) {
            const focusable = targetCell.querySelector(
                "input, select, textarea, .o_field_widget input, .o_field_widget select, .o_field_widget textarea"
            );
            if (focusable) {
                event.preventDefault();
                focusable.focus();
                this._highlightSelectedCell(targetCell);
                console.debug(`Navigated to row ${targetRowIndex}, cell ${targetCellIndex}.`);
            } else {
                console.debug(`No focusable element in target cell at row ${targetRowIndex}, cell ${targetCellIndex}.`);
            }
        } else {
            console.debug(`No target cell at index ${targetCellIndex} in row ${targetRowIndex}.`);
        }
    },

    _isEditableCell(cell) {
        // Check for standard inputs and Odoo-specific field widgets
        return !!cell.querySelector(
            "input:not([disabled]), select:not([disabled]), textarea:not([disabled]), " +
            ".o_field_widget input:not([disabled]), .o_field_widget select:not([disabled]), .o_field_widget textarea:not([disabled])"
        );
    },

    async _makeRowEditable(row, rowIndex) {
        // If the row isn’t in edit mode, trigger editing
        if (!row.classList.contains("o_selected_row")) {
            console.debug(`Making row ${rowIndex} editable.`);
            const listRenderer = this.rendererProps.list;
            if (listRenderer && listRenderer.editRecord) {
                const recordId = row.dataset.id;
                if (recordId) {
                    await listRenderer.editRecord(recordId);
                }
            }
        }
    },

    _focusFirstCellInLastRow() {
        const rows = Array.from(this.root.el.querySelectorAll("tr.o_data_row"));
        const lastRow = rows[rows.length - 1];
        if (lastRow) {
            const firstEditableCell = Array.from(lastRow.querySelectorAll("td.o_data_cell")).find(
                (cell) => this._isEditableCell(cell)
            );
            if (firstEditableCell) {
                const focusable = firstEditableCell.querySelector(
                    "input, select, textarea, .o_field_widget input, .o_field_widget select, .o_field_widget textarea"
                );
                if (focusable) {
                    focusable.focus();
                    this._highlightSelectedCell(firstEditableCell);
                    console.debug("Focused first cell in new row.");
                }
            }
        }
    },

    _highlightSelectedCell(cell) {
        this.root.el.querySelectorAll(".o_cell_selected").forEach((el) =>
            el.classList.remove("o_cell_selected")
        );
        cell.classList.add("o_cell_selected");
    },
});