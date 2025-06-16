/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { Chatter } from "@mail/chatter/web_portal/chatter";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";

patch(Chatter.prototype, {
    async setup() {
        super.setup();
        this.orm = useService("orm");

    },
    async changeThread(threadModel, threadId) {
        this.state.thread = this.store.Thread.insert({ model: threadModel, id: threadId });
        try {
            const modelData = await this.orm.searchRead("ir.model", [["model", "=", threadModel]], ["name"]);
            if (modelData.length > 0) {
                var modelName = modelData[0].name;
                console.log('modelName',modelName)
            }
        } catch (error) {
            var modelName = 'record';
        }
        if (threadId === false) {
            if (this.state.thread.messages.length === 0) {
                this.state.thread.messages.push({
                    id: this.store.getNextTemporaryId(),
                    author: this.store.self,
                    body: _t("Creating a new ") + (this.env.model.action.currentController.action.context.record_name || modelName) + "...",
                    message_type: "notification",
                    thread: this.state.thread,
                    trackingValues: [],
                    res_id: threadId,
                    model: threadModel,
                });
            }
        }
    },
})