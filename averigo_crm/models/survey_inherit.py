# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError


class SurveyInherit(models.Model):
    _inherit = "survey.survey"

    def _create_answer(self, user=False, partner=False, email=False, res_id=None,
                       test_entry=False, check_attempts=True,
                       **additional_vals):
        self.check_access_rights('read')
        self.check_access_rule('read')

        user_inputs = self.env['survey.user_input']
        for survey in self:
            if partner and not user and partner.user_ids:
                user = partner.user_ids[0]

            invite_token = additional_vals.pop('invite_token', False)
            survey._check_answer_creation(user, partner, email,
                                          test_entry=test_entry,
                                          check_attempts=check_attempts,
                                          invite_token=invite_token)
            answer_vals = {
                'survey_id': survey.id,
                'test_entry': test_entry,
                'lead_id': res_id,
                'is_session_answer': survey.session_state in ['ready',
                                                              'in_progress']
            }
            if survey.session_state == 'in_progress':
                # if the session is already in progress, the answer skips the 'new' state
                answer_vals.update({
                    'state': 'in_progress',
                    'start_datetime': fields.Datetime.now(),
                })
            if user and not user._is_public():
                answer_vals['partner_id'] = user.partner_id.id
                answer_vals['email'] = user.email
                answer_vals['nickname'] = user.name
            elif partner:
                answer_vals['partner_id'] = partner.id
                answer_vals['email'] = partner.email
                answer_vals['nickname'] = partner.name
            else:
                answer_vals['email'] = email
                answer_vals['nickname'] = email

            if invite_token:
                answer_vals['invite_token'] = invite_token
            elif survey.is_attempts_limited and survey.access_mode != 'public':
                # attempts limited: create a new invite_token
                # exception made for 'public' access_mode since the attempts pool is global because answers are
                # created every time the user lands on '/start'
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
    question_type = fields.Selection(selection_add=[
        ('images', 'Images')
    ])
    width = fields.Selection([
        ('full_width', 'Full-Width'), ('half_width', 'Half-Width'),
        ('thrice_width', 'Thrice-width')
    ])


class MergeSurveyData(models.Model):
    _inherit = "survey.user_input"

    lead_id = fields.Many2one('crm.lead')

    def _save_lines(self, question, answer, comment=None, overwrite_existing=True):
        """ Save answers to questions, depending on question type.

        :param bool overwrite_existing: if an answer already exists for question and user_input_id
        it will be overwritten (or deleted for 'choice' questions) in order to maintain data consistency.
        :raises UserError: if line exists and overwrite_existing is False
        """
        old_answers = self.env['survey.user_input.line'].search([
            ('user_input_id', '=', self.id),
            ('question_id', '=', question.id)
        ])
        if old_answers and not overwrite_existing:
            raise UserError(_("This answer cannot be overwritten."))

        if question.question_type in ['char_box', 'text_box', 'numerical_box', 'date', 'datetime']:
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
            raise AttributeError(question.question_type + ": This type of question has no saving function")

    @api.model
    def _save_line_images(self, question, old_answers, answer, comment):
        vals = {
            'user_input_id': self.id,
            'question_id': question.id,
            'survey_id': question.survey_id.id,
            'skipped': False
        }
        vals.update({'file_type': 'image'})
        if answer[0] != '':
            file = answer[0][0]
        else:
            file = None
        if file:
            vals.update({'answer_type': 'images', 'value_images': file})
        else:
            vals.update({'answer_type': None, 'skipped': True})
        if old_answers:
            old_answers.write(vals)
            return old_answers
        else:
            return self.env['survey.user_input.line'].create(vals)


class SurveyUserInputLine(models.Model):
    _inherit = 'survey.user_input.line'

    answer_type = fields.Selection(selection_add=[
        ('images', 'Images')])
    value_images = fields.Binary('Images')
    file_type = fields.Selection([('image', 'image'), ('pdf', 'pdf')])
