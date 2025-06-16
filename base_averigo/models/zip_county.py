# -*- coding: utf-8 -*-
from odoo import models, fields


class ZipCounty(models.Model):
    """
    Model representing ZIP code, county, and related geographical information.

    This model stores information about ZIP codes, including associated cities, streets, states,
    counties, area codes, country, and geographical coordinates (latitude and longitude).
    It is used to manage and retrieve location-based data for various purposes, such as address
    validation and geographical mapping.

    Attributes:
        _name (str): Model name in Odoo (zip.county).
        _rec_name (str): Field used as the display name for records (county).
        _description (str): Description of the model.
    """

    _name = "zip.county"
    _rec_name = 'county'
    _description = "Zip County"

    zip = fields.Char(
        string="ZIP Code",
        help="The postal code or ZIP code for the location.")
    city = fields.Char(
        string="City",
        help="The city or town associated with the ZIP code.")
    street = fields.Char(
        string="Street",
        help="The street name or address associated with the ZIP code.")
    state = fields.Char(
        string="State",
        help="The state or region associated with the ZIP code.")
    county = fields.Char(
        string="County",
        help="The county or administrative district associated with the ZIP code.")
    area_codes = fields.Char(
        string="Area Codes",
        help="The telephone area codes associated with the ZIP code.")
    country = fields.Char(
        string="Country",
        help="The country associated with the ZIP code.")
    latitude = fields.Float(
        string="Latitude",
        help="The geographical latitude coordinate of the location.")
    longitude = fields.Float(
        string="Longitude",
        help="The geographical longitude coordinate of the location.")



