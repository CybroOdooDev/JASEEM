
from odoo import http
from odoo.http import request
from odoo.exceptions import UserError
from odoo.addons.survey.controllers.main import Survey


class SurveyExtend(Survey):
    @http.route('/survey/start/<string:survey_token>', type='http', auth='public', website=True)
    def survey_start(self, survey_token, res_id=None, answer_token=None, email=False, **post):
        """ Start a survey by providing
         * a token linked to a survey;
         * a token linked to an answer or generate a new token if access is allowed;
        """
        # Get the current answer token from cookie
        print(survey_token, 'hhhhh', res_id)
        answer_from_cookie = False
        if not answer_token:
            answer_token = request.httprequest.cookies.get \
                ('survey_%s' % survey_token)
            answer_from_cookie = bool(answer_token)

        access_data = self._get_access_data(survey_token, answer_token, ensure_token=False)

        if answer_from_cookie and access_data['validity_code'] in \
        ('answer_wrong_user', 'token_wrong'):
            # If the cookie had been generated for another user or does not correspond to any existing answer object
            # (probably because it has been deleted), ignore it and redo the check.
            # The cookie will be replaced by a legit value when resolving the URL, so we don't clean it further here.
            access_data = self._get_access_data(survey_token, None,
                                                ensure_token=False)

        if access_data['validity_code'] is not True:
            return self._redirect_with_error(access_data,
                                             access_data['validity_code'])

        survey_sudo, answer_sudo = access_data['survey_sudo'], access_data[
            'answer_sudo']
        print(12324, answer_sudo.read())
        if not answer_sudo:
            try:
                answer_sudo = survey_sudo._create_answer(user=request.env.user,
                                                         email=email, res_id=res_id)
            except UserError:
                answer_sudo = False

        if not answer_sudo:
            try:
                survey_sudo.with_user(request.env.user).check_access_rights('read')
                survey_sudo.with_user(request.env.user).check_access_rule('read')
            except:
                return request.redirect("/")
            else:
                return request.render("survey.survey_403_page",
                                      {'survey': survey_sudo})

        return request.redirect(
            '/survey/%s/%s' % (survey_sudo.access_token, answer_sudo.access_token))