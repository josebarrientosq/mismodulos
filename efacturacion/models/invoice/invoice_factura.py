#!/usr/bin/env python
# -*- coding: utf-8 -*-
from odoo import fields,models,api,_
from utils.InvoiceLine import Factura
from utils.Boleta import Boleta
from utils.NotaCredito import NotaCredito
from utils.NotaDebito import NotaDebito
import xml.etree.ElementTree as ET
from signxml import XMLSigner, XMLVerifier,methods
import requests
import zipfile
import base64
import os
from suds.client import Client
from suds.wsse import *
import requests
import logging


class invoice_factura(models.Model):
    _inherit = "account.invoice"

    @api.multi
    def generarFactura(self):
        FacturaObject=Factura()

        Invoice=FacturaObject.Root()

        Total = FacturaObject.AdditionalMonetaryTotal(gravado=str(round(self.total_venta_gravado,2)),
                                                      exonerado=str(round(self.total_venta_exonerada,2)),
                                                      inafecto=str(round(self.total_venta_inafecto,2)),
                                                      gratuito=str(round(self.total_venta_gratuito,2)),
                                                      total_descuento=str(round(self.total_descuentos,2)),
                                                      currencyID=str(self.company_id.currency_id.name))
        Total.appendChild(FacturaObject.firma(id="placeholder"))
        Invoice.appendChild(Total)

        Invoice = FacturaObject.InvoiceRoot(rootXML=Invoice,
                                            versionid="2.0",
                                            customizationid="1.0",
                                            id=str(self.number),
                                            issuedate=str(self.date_invoice),
                                            issuetime="",
                                            invoicetypecode=str(self.journal_id.invoice_type_code_id),
                                            documentcurrencycode=str(self.company_id.currency_id.name),
                                            paymentduedate=str(self.date_due if self.date_due else ""))
        Invoice.appendChild(FacturaObject.Signature(Id="IDSignMT",
                                                    ruc=str(self.company_id.partner_id.vat),
                                                    razon_social=str(self.company_id.partner_id.registration_name),
                                                    uri="#SignatureMT"))

        Empresa=FacturaObject.cacAccountingSupplierParty(num_doc_ident=str(self.company_id.partner_id.vat),
                                                         tipo_doc_ident=str(self.company_id.partner_id.catalog_06_id.code),
                                                         nombre_comercial=self.company_id.partner_id.registration_name,
                                                         codigo_ubigeo=str(self.company_id.partner_id.zip),
                                                         nombre_direccion_full=str(self.company_id.partner_id.street),
                                                         nombre_direccion_division=self.company_id.partner_id.street2,
                                                         nombre_departamento=str(self.company_id.partner_id.state_id.name),
                                                         nombre_provincia=str(self.company_id.partner_id.province_id.name),
                                                         nombre_distrito=str(self.company_id.partner_id.district_id.name),
                                                         nombre_proveedor=str(self.company_id.partner_id.registration_name),
                                                         codigo_pais="PE")
        Invoice.appendChild(Empresa)

        Cliente=FacturaObject.cacAccountCustomerParty(num_doc_identidad=str(self.partner_id.vat),
                                                      tipo_doc_identidad=str(self.partner_id.catalog_06_id.code),
                                                      nombre_cliente=str(self.partner_id.registration_name))
        Invoice.appendChild(Cliente)




        for tax in self.tax_line_ids:
            TaxTotal=FacturaObject.TaxTotal(currencyID=str(self.company_id.currency_id.name),
                                                       TaxAmount=str(round(tax.amount,2)),
                                                       tributo_codigo=str(tax.tax_id.tax_group_id.name_code),
                                                       tributo_nombre=str(tax.tax_id.tax_group_id.description),
                                                       tributo_id=str(tax.tax_id.tax_group_id.code))
            Invoice.appendChild(TaxTotal)

        Moneda = FacturaObject.LegalMonetaryTotal(MontoTotal=str(round(self.amount_total,2)),
                                                  currency_id=str(self.company_id.currency_id.name))
        Invoice.appendChild(Moneda)



        id = 1
        for line in self.invoice_line_ids :
            TaxTotals=[]
            #Si No hay impuestos puede tratarse de un tipo de igv inafecto o exonerado
            if len(line.invoice_line_tax_ids)==0:
                taxDict = {
                    "currencyID": str(self.company_id.currency_id.name),
                    "TaxAmount": str(0.00),
                    "TaxExemptionReasonCode": str(line.tipo_afectacion_igv.code),
                    "tributo_codigo": "1000", "tributo_nombre": "IGV",
                    "tributo_tipo_codigo": "VAT","TierRange":"01"
                }
                TaxTotal = FacturaObject.cacTaxTotal(taxDict)
                TaxTotals.append(TaxTotal)

            subtotal=line.price_subtotal
            for tax in line.invoice_line_tax_ids.sorted(key=lambda r:r.tax_group_id.sequence):

                if tax.price_include==True:
                    if tax.amount_type=="percent":

                        taxDict = {
                            "currencyID": self.company_id.currency_id.name,
                            "TaxAmount": str(round(subtotal*tax.amount/100,2)),
                            "TaxExemptionReasonCode":str(line.tipo_afectacion_igv.code),
                            "tributo_codigo": tax.tax_group_id.code,
                            "tributo_nombre": tax.tax_group_id.description,
                            "tributo_tipo_codigo": tax.tax_group_id.name_code,
                            "TierRange":"01"
                        }

                        TaxTotal = FacturaObject.cacTaxTotal(taxDict)
                        TaxTotals.append(TaxTotal)
                        subtotal = subtotal*(1+tax.amount/100)

            a=FacturaObject.InvoiceLine(amount=str(round(line.price_subtotal,2)),
                                        currencyID=self.company_id.currency_id.name,
                                        ID=str(id),
                                        precio_unitario=round(line.price_unit,2),
                                        quantity=str(round(line.quantity,2)),
                                        unitCode=str(line.uom_id.code),
                                        no_onerosa=line.tipo_afectacion_igv.no_onerosa,
                                        valor_unitario=str(line.product_id.lst_price))

            for Tax in TaxTotals:
                a.appendChild(Tax)

            discount = (line.price_subtotal if line.price_subtotal else 0.0) * (line.discount / 100)
            a.appendChild(FacturaObject.cacItem(str(line.product_id.id), line.name))
            a.appendChild(FacturaObject.cacPrice(str(line.price_subtotal)))
            if discount > 0:
                a.appendChild(FacturaObject.AllowanceCharge(str(round(discount,2)), str(self.company_id.currency_id.name)))
            id=id+1
            Invoice.appendChild(a)

        I=Invoice.toprettyxml("        ")
        self.documentoXML =  I