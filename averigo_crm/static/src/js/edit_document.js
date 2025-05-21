/** @odoo-module **/

import { useService } from "@web/core/utils/hooks";
import { registry } from "@web/core/registry";
import { PdfViewerField } from "@web/views/fields/pdf_viewer/pdf_viewer_field";
import { useRef } from "@odoo/owl";

// Define the OWL component for the custom PDF viewer field
export class EditPdfViewerField extends PdfViewerField {
    static template = "averigo_crm.EditPdfViewerField"; // Use a namespaced template name
    static props = {
        ...PdfViewerField.props, // Inherit props from PdfViewerField
    };

    setup() {
        super.setup();
        this.iframePdf = useRef("iframePdf");
        this.tabs1 = [];
        this.count = 0;
        this.orm = useService("orm");
    }

    onLoadSuccess() {
        const email_count = [];
        const recipients_list = [];
        const self = this;

        // Collect email addresses from record data
        if (this.props.record.data.email_id || this.props.record.data.additional_emails || this.props.record.data.email_ids) {
            if (this.props.record.data.email_id) {
                email_count.push(this.props.record.data.email_id[1]);
            }
            if (this.props.record.data.additional_emails) {
                for (const email of this.props.record.data.additional_emails.records) {
                    email_count.push(email.data.display_name);
                }
            }
            if (this.props.record.data.email_ids) {
                email_count.push(this.props.record.data.email_ids.records[0].data.display_name);
            }

            // Disable text selection in the iframe
            const $iFrame = $(this.iframePdf.el.contentWindow.document);
            $iFrame.find("*").css("user-select", "none");

            // Handle double-click event on the PDF viewer
            $iFrame.find("#viewer").on("dblclick", function (e) {
                self.count++;
                let pageno;
                let rect_doc;

                // Determine the page number and bounding rectangle
                if ($(e.target.parentNode).attr("class") === "textLayer") {
                    pageno = $(e.target.parentNode.parentNode).data("pageNumber");
                    rect_doc = e.target.parentNode.getBoundingClientRect();
                } else {
                    pageno = $(e.target.parentNode).data("pageNumber");
                    rect_doc = e.target.getBoundingClientRect();
                }

                // Create a select dropdown for field options
                const values = ["<Select Fields>", "FullName", "Email", "Company", "Signature", "Text"];
                const select = document.createElement("select");
                select.name = "fields";

                // Populate recipients list
                recipients_list.length = 0; // Clear the list
                email_count.forEach((email) => recipients_list.push(email));

                // Create tabs for each recipient
                recipients_list.forEach((recipient, index) => {
                    self.tabs1.push({
                        fullNameTabs: [],
                        signHereTabs: [],
                        emailTabs: [],
                        companyTabs: [],
                        textTabs: [],
                        dateSignedTabs: [],
                    });

                    // Add options to the select dropdown
                    values.forEach((val) => {
                        const option = document.createElement("option");
                        option.value = `${val} by ${recipient}`;
                        option.text = `${val} by ${recipient}`;
                        option.id = index + 1;
                        select.appendChild(option);
                    });
                });

                // Add "Date" option
                const option_date = document.createElement("option");
                option_date.value = "Date";
                option_date.text = "Date";
                select.appendChild(option_date);

                // Style and position the select dropdown
                select.setAttribute("style", "width:130px; position:absolute; z-index:999");
                const rect = e.currentTarget.getBoundingClientRect();
                const z = e.clientX - rect.x;
                const y = e.clientY - rect.y;
                const z_doc = e.clientX - rect_doc.x;
                const y_doc = e.clientY - rect_doc.y;
                select.style.left = `${z}px`;
                select.style.top = `${y}px`;

                // Handle select change event
                $(select).on("change", function () {
                    const x_extra = z_doc * 1.34 - z_doc;
                    const y_extra = y_doc * 1.34 - y_doc;
                    const doc_x = z_doc - x_extra;
                    const doc_y = y_doc - y_extra;

                    const data = {
                        xPosition: parseInt(doc_x),
                        yPosition: parseInt(doc_y),
                        tabLabel: parseInt(doc_x + doc_y),
                        documentId: "1",
                        pageNumber: pageno,
                    };

                    // Remove duplicate data from tabs
                    self.tabs1.forEach((li) => {
                        for (const dict in li) {
                            const arr = li[dict];
                            arr.forEach((item, index) => {
                                if (JSON.stringify(item) === JSON.stringify(data)) {
                                    arr.splice(index, 1);
                                }
                            });
                        }
                    });

                    // Process selected value
                    const whole_string = select.value;
                    const split_string = whole_string.split(" by ");
                    recipients_list.forEach((recipient, index) => {
                        if (select.value === "Date") {
                            self.tabs1[index].dateSignedTabs.push(data);
                        } else if (recipient === split_string[1]) {
                            if (whole_string === `FullName by ${recipient}`) {
                                self.tabs1[index].fullNameTabs.push(data);
                            } else if (whole_string === `Signature by ${recipient}`) {
                                self.tabs1[index].signHereTabs.push(data);
                            } else if (whole_string === `Email by ${recipient}`) {
                                self.tabs1[index].emailTabs.push(data);
                            } else if (whole_string === `Company by ${recipient}`) {
                                self.tabs1[index].companyTabs.push(data);
                            } else if (whole_string === `Text by ${recipient}`) {
                                self.tabs1[index].textTabs.push(data);
                            }
                        }
                    });

                    // Call ORM to save data
                    const id = self.props.record.evalContextWithVirtualIds.active_id;
                    self.orm.call("agreement.action.wizard", "get_json_data", ["", self.tabs1, id], {});
                });

                // Append select to the viewer
                $iFrame.find("#viewer").append(select);
            });
        }
    }
}

// Register the field widget
registry.category("fields").add("pdf_viewer_edit", {
    component: EditPdfViewerField,
    displayName: "Editable PDF Viewer",
    supportedTypes: ["binary"],
});