# -*- coding: utf-8 -*-
from . import models


def add_group_to_user(cr):
    cr.ref("base_averigo.averigo_admin_backend_group").write({
        "users": [(4, cr.ref("base.user_admin").id)]
    })

def remove_group_from_user(cr):
    cr.ref("base_averigo.averigo_admin_backend_group").write({
        "users": [(3, cr.ref("base.user_admin").id)]
    })

def install_uninstall_module(cr):
    cr['ir.module.module'].search([('name', 'in', ['stock_sms'])]).button_install()