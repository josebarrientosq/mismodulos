from odoo import api, models
from dateutil.parser import parse
from odoo.exceptions import UserError

class UserReportMovimiento(models.AbstractModel):
    _name = "report.mifact.mifact_template_factura2"

    @api.model
    def get_report_values(self, docids, data=None):
        print("Lista de Docids")
        print(docids)

        docs = self.env["account.invoice"].search([("state","=","paid")])

        return {
            "doc_ids": docids,
            "data": data,
            "docs": docs,
        }

class UserReportfacturaspagadas(models.AbstractModel):
    _name = "report.mifact.mifact_template_factura3"

    @api.model
    def get_report_values(self, docids, data=None):
        docs = self.env["account.invoice"].search([("state","=","paid")])
        return {
            "doc_ids": docids,
            "data": data,
            "docs": docs,
        }





class UserReportPLEVentas(models.AbstractModel):
    _name = "report.efacturacion_template_pleventas"



    @api.model
    def render_html(self, docids, data=None):
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('efacturacion_template_pleventas')
        docs = self.env['account.invoice'].search([("state", "!=", "draft")])



        def getCUO(id):
            return 'M'+str(id).zfill(4)

        def getserie(letra):
            return letra[:4]


        def getcorrelativo(letra):
            return  letra[8:]

        docargs = {
            'doc_ids' : docids,
            'doc_model' : report.model,
            'docs' : docs,
            'facturas' : ple,
            "get_CUO": getCUO,
            "getserie": getserie,
            "getcorrelativo": getcorrelativo
        }
        return report_obj.render('efacturacion_template_pleventas' , docargs)