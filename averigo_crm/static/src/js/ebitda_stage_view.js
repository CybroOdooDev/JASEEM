/** @odoo-module **/

import {Component, onWillStart, useState} from "@odoo/owl";
import {jsonRpc} from "@web/core/network/rpc_service";

export class EbitdaStageView extends Component {
    setup() {
        this.state = useState({stages: []});
        onWillStart(async () => {
            const data = await jsonRpc("/ebitda/kanban/data", {});
            console.log("EBITDA Data:", data);
            this.state.stages = data;
        });
    }

    getEbitda(stageId) {
        const record = this.state.stages.find(s => s.stage_id === stageId);
        return record ? record.total_ebitda.toFixed(2) : "0.00";
    }
}

EbitdaStageView.template = "averigo_crm.EbitdaStageTemplate";
