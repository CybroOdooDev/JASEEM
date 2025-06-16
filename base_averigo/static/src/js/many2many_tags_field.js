/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { Many2ManyTagsField } from "@web/views/fields/many2many_tags/many2many_tags_field";
import { Domain } from "@web/core/domain";


patch(Many2ManyTagsField.prototype, {
    getDomain() {
        const domain =
            typeof this.props.domain === "function" ? this.props.domain() : this.props.domain;
        const currentIds = this.props.record.data[this.props.name].currentIds.filter(
            (id) => typeof id === "number"
        );
        return Domain.and([domain, Domain.not([["id", "in", currentIds]])]).toList(
            this.props.context
        );
    },
})