import {KanbanController} from "@web/views/kanban/kanban_controller";
import {patch} from "@web/core/utils/patch";
import {onWillStart, Component} from "@odoo/owl";
import {useService} from "@web/core/utils/hooks";
import {usePopover} from "@web/core/popover/popover_hook";

// Create the EBITDA Popover Component
class EbitdaPopoverComponent extends Component {
    static template = "averigo_crm.EbitdaPopoverTemplate";
}

// Patch the KanbanController to add the button functionality
patch(KanbanController.prototype, {
    setup() {
        super.setup();
        this.orm = useService("orm");

        // Initialize popover with the component
        this.popover = usePopover(EbitdaPopoverComponent, {
            position: "bottom",
            closeOnClickAway: true,
        });

        this.onButtonClick = this.onButtonClick.bind(this);

        onWillStart(async () => {
            console.log(this, this.env.config.viewType);
            console.log(this.env.searchModel.resModel);
            if (
                this.env.config.viewType === 'kanban' &&
                this.env.searchModel.resModel === 'crm.lead'
            ) {
                const ebitdaData = await this.orm.call("crm.lead", "get_dashboard_data", []);
                console.log("ebitdaData", ebitdaData);
                // Merge the returned data into the state
                this.state = {
                    ...this.state,
                    ebitda_open: ebitdaData.all_open_ebitda,
                    ebitda_closed: ebitdaData.all_closed_ebitda,
                    isShowEbitda: ebitdaData.is_show_ebitda
                };
            }
        });
    },

    // Define the button click handler
    onButtonClick(event) {
        console.log("Button was clicked!", this.state);

        // Toggle popover - if it's open, close it; if closed, open it
        if (this.popover.isOpen) {
            this.popover.close();
        } else {
            this.popover.open(event.target, {
                ebitda_open: this.state.ebitda_open,
                ebitda_closed: this.state.ebitda_closed,
            });
        }
    }
});