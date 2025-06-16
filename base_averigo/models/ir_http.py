# -*- coding: utf-8 -*-
from odoo import models, api
from odoo.tools.translate import code_translations


class IrHttp(models.AbstractModel):
    """
    Inherits the `ir.http` model to customize the date and time format for the web client.

    This class extends the `ir.http` model to override the `get_translations_for_webclient` method.
    The primary purpose of this override is to replace the default date and time formats from the
    language settings with the formats specified in the company settings.

    Attributes:
        _inherit (str): The name of the model being inherited (`ir.http`).
    """
    _inherit = 'ir.http'

    @api.model
    def get_translations_for_webclient(self, modules, lang):
        """
        Override the `get_translations_for_webclient` method to customize date and time formats.

        This method retrieves translations for the specified modules and language, but replaces
        the default date and time formats from the language settings with the formats defined
        in the company settings. If the company does not specify a format, it falls back to the
        language's default format.

        Args:
            modules (list): A list of module names for which translations are required.
                           If empty, all initialized modules are used.
            lang (str): The language code for which translations are required.
                        If empty, the language from the current context is used.

        Returns:
            tuple: A tuple containing two elements:
                - translations_per_module (dict): A dictionary mapping module names to their translations.
                - lang_params (dict): A dictionary containing language-specific parameters, including
                                     the customized date and time formats.
        """
        if not modules:
            modules = self.pool._init_modules
        if not lang:
            lang = self._context.get("lang")
        lang_data = self.env['res.lang']._get_data(code=lang)
        lang_params = {
            "name": lang_data.name,
            "code": lang_data.code,
            "direction": lang_data.direction,
            "date_format": self.env.company.date_format_selection if self.env.company.date_format_selection else self.env.company.language.date_format,
            "time_format": self.env.company.time_format_selection if self.env.company.time_format_selection else self.env.company.language.time_format,
            "short_time_format": lang_data.short_time_format,
            "grouping": lang_data.grouping,
            "decimal_point": lang_data.decimal_point,
            "thousands_sep": lang_data.thousands_sep,
            "week_start": int(lang_data.week_start),
        } if lang_data else None

        # Regional languages (ll_CC) must inherit/override their parent lang (ll), but this is
        # done server-side when the language is loaded, so we only need to load the user's lang.
        translations_per_module = {}
        for module in modules:
            translations_per_module[
                module] = code_translations.get_web_translations(module, lang)

        return translations_per_module, lang_params
