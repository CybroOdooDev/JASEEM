/** @odoo-module */
import publicWidget from "@web/legacy/js/public/public_widget";
import SurveyFormWidget from '@survey/js/survey_form';
import SurveyPreloadImageMixin from "@survey/js/survey_preload_image_mixin";
/**  Extends publicWidget to create "SurveyFormUpload" */
publicWidget.registry.SurveyFormUpload = publicWidget.Widget.extend(SurveyPreloadImageMixin, {
        selector: '.o_survey_form',
        events: {
            'change .o_survey_upload_file': '_onFileChange',
        },
        init() {
            console.log("Inittttttt")
            this._super(...arguments);
        },
        /** On adding file function */
        _onFileChange: function(event) {
            console.log("onFileChange", event);
            var self = this;
            var files = event.target.files;
            var fileNames = [];
            var dataURLs = [];
            var reader = new FileReader();
                reader.readAsDataURL(files[0]);
                reader.onload = function(e) {
                    var file = files[0];
                    var filename = file.name;
                    var dataURL = e.target.result.split(',')[1]; /**  split base64 data */
                    fileNames.push(filename);
                    dataURLs.push(dataURL);
                    /**  Set the data-oe-data and data-oe-file_name attributes of the input element self call el */
                    var $input = $(event.currentTarget)
                    console.log("asasasaassaasassaa",JSON.stringify(dataURLs))
                    console.log("asasasaassaasassaa",JSON.stringify(fileNames))
                    $input.attr('data-oe-data', JSON.stringify(dataURLs));
                    $input.attr('data-oe-file_name', JSON.stringify(fileNames));
                    }
        },
    });
export default publicWidget.registry.SurveyFormUpload;