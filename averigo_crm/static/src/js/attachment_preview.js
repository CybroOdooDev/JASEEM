/** @odoo-module **/
import {Component, useState} from "@odoo/owl";
import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";
import {standardFieldProps} from "@web/views/fields/standard_field_props";
import {FileInput} from "@web/core/file_input/file_input";
import {useX2ManyCrud} from "@web/views/fields/relational_utils";


export class Many2ManyAttachmentPreview extends Component {
    static template = 'Many2ManyImageField';
    static components = {
        FileInput,
    };
    static props = {
        ...standardFieldProps,
        acceptedFileExtensions: {type: String, optional: true},
        className: {type: String, optional: true},
        numberOfFiles: {type: Number, optional: true},
    };

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.operations = useX2ManyCrud(() => this.props.record.data[this.props.name], true);
//        this.operations = useX2ManyCrud(() => this.props.value, true);
        this.state = useState({
            flag: false,
        });

    }

    get uploadText() {
        return this.props.record.fields[this.props.name].string;
    }

    get files() {
        return this.props.record.data[this.props.name].records.map((record) => {
            return {
                ...record.data,
                id: record.resId,
            };
        });
    }

    getUrl(id) {
        return "/web/content/ir.attachment/" + id + "/datas";
    }

    getExtension(file) {
        return file.name.replace(/^.*\./, "");
    }

    async onFileUploaded(files) {
        for (const file of files) {
            if (file.error) {
                return this.notification.add(file.error, {
                    title: this.env._t("Uploading error"),
                    type: "danger",
                });
            }
            await this.operations.saveRecord([file.id]);
        }
    }

    async onFileRemove(deleteId) {
        const record = this.props.value.records.find((record) => record.data.id === deleteId);
        this.operations.removeRecord(record);
    }
}

export const many2ManyAttachmentPreview = {
    component: Many2ManyAttachmentPreview,
    supportedOptions: [
        {
            label: ("Accepted file extensions"),
            name: "accepted_file_extensions",
            type: "string",
        },
        {
            label: ("Number of files"),
            name: "number_of_files",
            type: "integer",
        },
    ],
    supportedTypes: ["many2many"],
    isEmpty: () => false,
    relatedFields: [
        {name: "name", type: "char"},
        {name: "mimetype", type: "char"},
    ],
    extractProps: ({attrs, options}) => ({
        acceptedFileExtensions: options.accepted_file_extensions,
        className: attrs.class,
        numberOfFiles: options.number_of_files,
    }),
};

registry.category("fields").add("many2many_attachment_preview", many2ManyAttachmentPreview)
