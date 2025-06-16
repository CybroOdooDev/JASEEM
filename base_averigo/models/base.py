# -*- coding: utf-8 -*-
import re

from odoo import models, exceptions


class Base(models.AbstractModel):
    """
    Inherits the `base` model to add custom validation methods for email and phone numbers.

    This class extends the `base` model to include utility methods for validating email addresses
    and phone numbers. These methods are designed to ensure that the provided email and phone
    number adhere to specific formats.

    Attributes:
        _inherit (str): The name of the model being inherited (`base`).
    """
    _inherit = 'base'

    def averigo_email_validation(self, email):
        """
        Validate the provided email address.

        This method checks if the given email address adheres to a standard email format using
        a regular expression. If the email is invalid, it raises a `ValidationError`.

        Args:
            email (str): The email address to validate.

        Raises:
            exceptions.ValidationError: If the email address does not match the expected format.

        Notes:
            The regular expression used for validation ensures the email follows the pattern:
            - Starts with alphanumeric characters, dots, underscores, or hyphens.
            - Contains an `@` symbol followed by a domain name.
            - The domain name must consist of alphanumeric characters, dots, or hyphens.
            - Ends with a top-level domain (2 to 4 characters long, e.g., `.com`, `.org`).
        """
        if email:
            match = re.match(
                r'^[_a-zA-Z0-9-]+(\.[_a-zA-Z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$',
                email)
            if match is None:
                raise exceptions.ValidationError(
                    'Please provide a valid email id.')

    def averigo_phone_validation(self, phone):
        """
        Validate the provided phone number.

        This method checks if the given phone number adheres to a standard US phone number format
        using a regular expression. If the phone number is invalid or exceeds 15 characters,
        it raises a `ValidationError`.

        Args:
            phone (str): The phone number to validate.

        Raises:
            exceptions.ValidationError: If the phone number does not match the expected format
                                        or exceeds the maximum allowed length.

        Notes:
            The regular expression used for validation ensures the phone number follows the pattern:
            - Optional parentheses around the area code (e.g., `(123)`).
            - Optional hyphens or spaces between number groups.
            - A total of 10 digits (e.g., `123-456-7890` or `(123) 456-7890`).
            - The maximum allowed length for the phone number is 15 characters.
        """
        if phone:
            match = re.match(r'\(?\d{3}\)?-? *\d{3}-? *-?\d{4}', phone)
            if match is None or len(phone) > 15:
                raise exceptions.ValidationError(
                    'Please provide a valid number.')
