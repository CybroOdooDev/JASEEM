/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, onMounted } from "@odoo/owl";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { useService } from "@web/core/utils/hooks";

export class ImagePreviewWidget extends Component {
    static template = "ImagePreviewWidget";

    setup() {
        this.displayMode = this.props.displayMode || 'image';
        this.iconClass = this.props.iconClass || 'fa fa-eye';
        this.displayMode = this.props.displayMode;
        // Initialize FancyBox when the component is mounted
        onMounted(() => this.initializeFancybox());
        this.orm = useService("orm");
    }

    initializeFancybox() {
        if (window.Fancybox) {
            // Bind FancyBox to elements with the `data-fancybox` attribute
            Fancybox.bind("[data-fancybox]", {
                // Customize options as needed
            });
        } else {
            console.error("Fancybox is not available. Ensure it is loaded.");
        }
    }

    get previewSrc() {
        const model = this.props.record.resModel;
        const recordId = this.props.record.resId;
        const fieldName = this.props.name;
        const fileName = this.props.record.data.file_name || this.props.record.data.name || "";
        if (!(recordId && model && fieldName)) return false;

        // Get extension
        const extension = fileName.split('.').pop().toLowerCase();

        // Define supported previewable image types
        const imageExtensions = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp', 'svg'];

        // Return image preview if it's an image
        if (imageExtensions.includes(extension)) {
            return `/web/content/${model}/${recordId}/${fieldName}`;
        }
        return `/web/content/${model}/${recordId}/${fieldName}?filename=${fileName}`;
    }
}

ImagePreviewWidget.props = {
    ...standardFieldProps,
    displayMode: { type: String, optional: true },
    iconClass: { type: String, optional: true },
};

export const imagePreviewWidget = {
    component: ImagePreviewWidget,
    extractProps: ({ attrs, options }) => ({
        displayMode: attrs.displayMode || options.displayMode,
        iconClass: attrs.iconClass,
    }),
};

registry.category("fields").add("image_preview", imagePreviewWidget);
