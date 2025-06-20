/** @odoo-module **/

import {onMounted, onWillUnmount, useRef} from "@odoo/owl";
import {patch} from "@web/core/utils/patch";
import {X2ManyField} from "@web/views/fields/x2many/x2many_field";

patch(X2ManyField.prototype, {
    setup() {
        super.setup();
        this.root = useRef("rootX2ManyField");
        this.onKeyDown = this.onKeyDown.bind(this);

        onMounted(() => {
            if (this.root.el) {
                this.root.el.addEventListener("keydown", this.onKeyDown);
                console.debug("Keydown listener added to X2ManyField root.");
            }
        });

        onWillUnmount(() => {
            if (this.root.el) {
                this.root.el.removeEventListener("keydown", this.onKeyDown);
                console.debug("Keydown listener removed from X2ManyField root.");
            }
        });
    },

    async onKeyDown(event) {
        const {key} = event;
        if (!["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"].includes(key)) {
            return;
        }

        event.preventDefault(); // Prevent default browser scrolling
        const activeElement = document.activeElement;
        const currentCell = activeElement.closest("td.o_data_cell");
        if (!currentCell) {
            console.debug("No current cell found for navigation.");
            return;
        }

        const currentRow = currentCell.closest("tr.o_data_row");
        console.log(currentRow);
        if (!currentRow) {
            console.debug("No current row found for navigation.");
            return;
        }

        // Fetch rows initially
        let rows = Array.from(this.root.el.querySelectorAll("tr.o_data_row"));
        console.log("rowsssssssss", rows.length);
        let rowIndex = rows.indexOf(currentRow);
        if (rowIndex === -1) {
            console.debug("Current row not found in rows list.");
            return;
        }

        const cellsInRow = Array.from(currentRow.querySelectorAll("td.o_data_cell")).filter((cell) => this._isEditableCell(cell));
        console.log("cellsInRowwwwwwwwwwwww", cellsInRow)
        const cellIndex = cellsInRow.indexOf(currentCell);
        if (cellIndex === -1) {
            console.debug("Current cell not found in editable cells.");
            return;
        }

        let targetRowIndex = rowIndex;
        let targetCellIndex = cellIndex;

        if (key === "ArrowUp") {
            if (rowIndex > 0) {
                targetRowIndex = rowIndex - 1;
                console.log("targetRowIndexxxxx (ArrowUp)", targetRowIndex);
            } else {
                console.debug("Cannot move up: already at first row.");
                return;
            }
        } else if (key === "ArrowDown") {
            console.log("ArrowDownnnnnnn", rowIndex);
            console.log("ArrowDownsssss", rows.length);
            console.log("ArrowDownsssss", rowIndex < rows.length - 1);
            if (rowIndex < rows.length - 1) {
                targetRowIndex = rowIndex + 1;
            } else if (this.props.viewMode === "list" && this.rendererProps.editable) {
                console.debug("Creating new row on ArrowDown.");
                await this.onAdd({position: "bottom"});
                // Wait for the new row to render and refresh rows
                await this._waitForRender();
                rows = Array.from(this.root.el.querySelectorAll("tr.o_data_row")); // Refresh rows
                targetRowIndex = rows.length - 1; // Set to the new row
                console.log("targetRowIndexssss (New Row)", targetRowIndex);
            } else {
                console.debug("Cannot move down: last row reached and not editable.");
                return;
            }
        } else if (key === "ArrowRight") {
            if (cellIndex < cellsInRow.length - 1) {
                targetCellIndex = cellIndex + 1;
            } else {
                console.debug("Cannot move right: already at last cell in row.");
                return;
            }
        } else if (key === "ArrowLeft") {
            if (cellIndex > 0) {
                targetCellIndex = cellIndex - 1;
            } else {
                console.debug("Cannot move left: already at first cell in row.");
                return;
            }
        }

        console.log("_navigateToCell", targetRowIndex, targetCellIndex);
        await this._navigateToCell(targetRowIndex, targetCellIndex);
    },

    _isEditableCell(cell) {
        const selector = "input:not([disabled]), select:not([disabled]), textarea:not([disabled]), " + ".o_field_widget input:not([disabled]), .o_field_widget select:not([disabled]), " + ".o_field_widget textarea:not([disabled]), .o_field_widget .o_input:not([disabled]), " + ".o_datepicker_input:not([disabled])";
        console.log("selectorrrrrrrrrrrrr", selector)
        return !!cell.querySelector(selector);
    },

    async _waitForRender(timeout = 500) {
        return new Promise((resolve) => setTimeout(resolve, timeout));
    },

    async _makeRowEditable(row, rowIndex) {
        if (row.classList.contains("o_selected_row")) {
            console.debug(`Row ${rowIndex} is already editable.`);
            return true;
        }
        const listRenderer = this.rendererProps.list;
        if (listRenderer && listRenderer.editRecord) {
            const recordId = row.dataset.id;
            if (recordId) {
                console.debug(`Triggering edit for record ID ${recordId} in row ${rowIndex}.`);
                try {
                    await listRenderer.editRecord(recordId);
                    await this._waitForRender(100); // Wait for edit mode to apply
                    if (!row.classList.contains("o_selected_row")) {
                        console.warn(`Row ${rowIndex} did not enter edit mode.`);
                        return false;
                    }
                    return true;
                } catch (error) {
                    console.error(`Failed to make row ${rowIndex} editable:`, error);
                    return false;
                }
            } else {
                console.debug(`No record ID found for row ${rowIndex}.`);
                return false;
            }
        } else {
            console.debug("List renderer or editRecord method not available.");
            return false;
        }
    },

    async _focusCell(cell, rowIndex, cellIndex) {
        const selector = "input:not([disabled]), select:not([disabled]), textarea:not([disabled]), " + ".o_field_widget input:not([disabled]), .o_field_widget select:not([disabled]), " + ".o_field_widget textarea:not([disabled]), .o_field_widget .o_input:not([disabled]), " + ".o_datepicker_input:not([disabled])";
        let focusable = cell.querySelector(selector);

        let attempts = 0;
        const maxAttempts = 3;
        while (!focusable && attempts < maxAttempts) {
            console.debug(`Retrying focus for cell in row ${rowIndex}, cell ${cellIndex}, attempt ${attempts + 1}.`);
            await this._waitForRender(100);
            focusable = cell.querySelector(selector);
            attempts++;
        }

        if (focusable) {
            focusable.focus();
            this._highlightSelectedCell(cell);
            console.debug(`Focused cell in row ${rowIndex}, cell ${cellIndex}.`);
            return true;
        } else {
            console.warn(`No focusable element found in cell at row ${rowIndex}, cell ${cellIndex} after ${maxAttempts} attempts.`);
            return false;
        }
    },

    async _navigateToCell(rowIndex, cellIndex) {
        const rows = Array.from(this.root.el.querySelectorAll("tr.o_data_row"));
        const targetRow = rows[rowIndex];
        if (!targetRow) {
            console.debug(`Target row at index ${rowIndex} not found.`);
            return;
        }

        // Ensure the target row is in edit mode
        if (this.rendererProps.editable) {
            const editSuccess = await this._makeRowEditable(targetRow, rowIndex);
            if (!editSuccess) {
                console.debug(`Failed to make row ${rowIndex} editable; aborting navigation.`);
                return;
            }
        }

        const targetCells = Array.from(targetRow.querySelectorAll("td.o_data_cell")).filter((cell) => this._isEditableCell(cell));
        let targetCell = targetCells[cellIndex];

        if (!targetCell && targetCells.length > 0) {
            cellIndex = Math.min(cellIndex, targetCells.length - 1);
            targetCell = targetCells[cellIndex];
            console.debug(`Adjusted target cell index to ${cellIndex} due to fewer columns in row ${rowIndex}.`);
        }

        if (targetCell) {
            await this._focusCell(targetCell, rowIndex, cellIndex);
        } else {
            console.debug(`No editable cell at index ${cellIndex} in row ${rowIndex}.`);
        }
    },

    _highlightSelectedCell(cell) {
        this.root.el.querySelectorAll(".o_cell_selected").forEach((el) => el.classList.remove("o_cell_selected"));
        cell.classList.add("o_cell_selected");
    },
});