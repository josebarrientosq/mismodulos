# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class Pleventaswizard(models.TransientModel):
    _name = "efacturacion.pleventas"
    _description = "wizard pleventas"

    date_from = fields.Date(string='Start Date')
    date_to = fields.Date(string='End Date')
    target_move = fields.Selection([('posted', 'All Posted Entries'),
                                    ('all', 'All Entries'),
                                    ], string='Target Moves', required=True, default='posted')

    @api.multi
    def check_report(self):
        data = {}
        data['form'] = self.read(['date_from', 'date_to'])[0]
        return self._print_report(data)

    def _print_report(self, data):
        data['form'].update(self.read(['date_from', 'date_to'])[0])
        return self.env['report'].get_action(self, "efacturacion.efacturacion_template_pleventas", data=data)