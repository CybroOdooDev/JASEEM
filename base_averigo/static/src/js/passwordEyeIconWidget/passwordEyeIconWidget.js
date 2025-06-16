/** @odoo-module **/

import {Component, useState} from "@odoo/owl";
import {registry} from "@web/core/registry";
import {standardFieldProps} from "@web/views/fields/standard_field_props";

class AverigoPasswordEyeWidget extends Component {
    static template = "base_averigo.PasswordEyeWidget";
    static props = {
        ...standardFieldProps,
        placeholder: {type: String, optional: true},
        maxlength: {type: Number, optional: true},
    };

    setup() {
        this.state = useState({
            showPassword: false,
        });
    }

    get value() {
        return this.props.record.data[this.props.name] || "";
    }

    get inputType() {
        return this.state.showPassword ? "text" : "password";
    }

    get eyeIcon() {
        return this.state.showPassword ? "fa-eye-slash" : "fa-eye";
    }

    togglePasswordVisibility() {
        this.state.showPassword = !this.state.showPassword;
    }

    onInput(ev) {
        this.props.record.update({[this.props.name]: ev.target.value});
    }

    onBlur(ev) {
        // Trigger validation on blur
        if (this.props.record.data[this.props.name] !== ev.target.value) {
            this.props.record.update({[this.props.name]: ev.target.value});
        }
    }
}

export const averigoPasswordEyeWidget = {
    component: AverigoPasswordEyeWidget,
};

registry.category("fields").add("password_eyes_icon", averigoPasswordEyeWidget);