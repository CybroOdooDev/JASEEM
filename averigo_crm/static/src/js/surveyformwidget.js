/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";

import OriginalSurveyFormWidget from "@survey/js/survey_form";

publicWidget.registry.SurveyFormWidget = OriginalSurveyFormWidget.extend({
    /**
     * Override the _prepareSubmitValues method
     * @override
     */
    _prepareSubmitValues(formData, params) {
        this._super(...arguments);
        console.log("SUPERRRRRRRRRR")
        this.$('[data-question-type]').each(function () {

            console.log("Imageeeeeeeeeeeeeeeeee",$(this).data('questionType'))


            if ($(this).data('questionType') === 'images') {

                params[this.name] = [$(this).data('oe-data'), $(this).data('oe-file_name')];
                    console.log("Nameeeeee", this.name,params)
                console.log("ssssssssssssssssssss", [$(this).data('oe-data'), $(this).data('oe-file_name')])
            }
        });
    },


});

export default publicWidget.registry.SurveyFormWidget;