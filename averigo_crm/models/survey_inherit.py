from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError


class SurveyInherit(models.Model):
    _inherit = "survey.survey"

    def _create_answer(self, user=False, partner=False, email=False,
                       res_id=None,
                       test_entry=False, check_attempts=True,
                       **additional_vals):
        self.check_access_rights('read')
        self.check_access_rule('read')
        user_inputs = self.env['survey.user_input']
        for survey in self:
            user = partner.user_ids[
                0] if partner and not user and partner.user_ids else user
            invite_token = additional_vals.pop('invite_token', False)

            print("Answer_detailssss", user, partner, email, test_entry,
                  check_attempts, invite_token)
            survey._check_answer_creation(user, partner, email, test_entry,
                                          check_attempts, invite_token)
            answer_vals = {
                'survey_id': survey.id, 'test_entry': test_entry,
                'lead_id': res_id,
                'is_session_answer': survey.session_state in ['ready',
                                                              'in_progress']
            }
            if survey.session_state == 'in_progress':
                answer_vals.update({'state': 'in_progress',
                                    'start_datetime': fields.Datetime.now()})
            if user and not user._is_public():
                answer_vals.update(
                    {'partner_id': user.partner_id.id, 'email': user.email,
                     'nickname': user.name})
            elif partner:
                answer_vals.update(
                    {'partner_id': partner.id, 'email': partner.email,
                     'nickname': partner.name})
            else:
                answer_vals.update({'email': email, 'nickname': email})
            if invite_token:
                answer_vals['invite_token'] = invite_token
            elif survey.is_attempts_limited and survey.access_mode != 'public':
                answer_vals['invite_token'] = self.env[
                    'survey.user_input']._generate_invite_token()
            answer_vals.update(additional_vals)
            user_inputs += user_inputs.create(answer_vals)
        for question in self.mapped('question_ids').filtered(
                lambda q: q.question_type == 'char_box' and (
                        q.save_as_email or q.save_as_nickname)):
            for user_input in user_inputs:
                if question.save_as_email and user_input.email:
                    user_input._save_lines(question, user_input.email)
                if question.save_as_nickname and user_input.nickname:
                    user_input._save_lines(question, user_input.nickname)
        return user_inputs


class SurveyImageQuestion(models.Model):
    _inherit = 'survey.question'
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.company.id)
    question_type = fields.Selection(selection_add=[('images', 'Images')])
    width = fields.Selection(
        [('full_width', 'Full-Width'), ('half_width', 'Half-Width'),
         ('thrice_width', 'Thrice-width')])


class MergeSurveyData(models.Model):
    _inherit = "survey.user_input"
    lead_id = fields.Many2one('crm.lead')

    def _save_lines(self, question, answer, comment=None,
                    overwrite_existing=True):
        old_answers = self.env['survey.user_input.line'].search([
            ('user_input_id', '=', self.id), ('question_id', '=', question.id)])

        print("QUENSTION TYPE",question.question_type)
        print("ANSWERRRRRRRTYPE",answer)
        if old_answers and not overwrite_existing:
            raise UserError(_("This answer cannot be overwritten."))
        if question.question_type in ['char_box', 'text_box', 'numerical_box',
                                      'date', 'datetime']:
            self._save_line_simple_answer(question, old_answers, answer)
            if question.save_as_email and answer:
                self.write({'email': answer})
            if question.save_as_nickname and answer:
                self.write({'nickname': answer})
        elif question.question_type in ['simple_choice', 'multiple_choice']:
            self._save_line_choice(question, old_answers, answer, comment)
        elif question.question_type == 'matrix':
            self._save_line_matrix(question, old_answers, answer, comment)
        elif question.question_type == 'images':
            self._save_line_images(question, old_answers, answer, comment)
        else:
            raise AttributeError(
                f"{question.question_type}: This type of question has no saving function")

    def _save_line_images(self, question, old_answers, answer, comment):


        vals = {'user_input_id': self.id, 'question_id': question.id,
                'survey_id': question.survey_id.id,
                'skipped': False, 'file_type': 'image'}
        file = answer[0][0] if answer and answer[0] != '' else None
        vals.update(
            {'answer_type': 'images', 'value_images': file} if file else {
                'answer_type': None, 'skipped': True})
        return old_answers.write(vals) if old_answers else self.env[
            'survey.user_input.line'].create(vals)


class SurveyUserInputLine(models.Model):
    _inherit = 'survey.user_input.line'
    answer_type = fields.Selection(selection_add=[('images', 'Images')])
    value_images = fields.Binary('Images')
    file_type = fields.Selection([('image', 'image'), ('pdf', 'pdf')])
