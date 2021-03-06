#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
#################################################################################

from odoo import api, fields, models

class GstInvoiceData(models.TransientModel):
    _name = "gst.invoice.data"

    def getGSTInvoiceData(self, invoiceObj, invoiceType, data):
        jsonItemData = []
        count = 0
        rateDataDict = {}
        rateDict = {}
        rateJsonDict = {}
        for invoiceLineObj in invoiceObj.invoice_line_ids:
            invoiceLineData = self.getInvoiceLineData(data, invoiceLineObj, invoiceObj, invoiceType)
            if invoiceLineData:
                rate = invoiceLineData[2]
                rateAmount = invoiceLineData[3]
                if invoiceLineData[1]:
                    invoiceLineData[1]['txval'] = rateAmount
                if rate not in rateDict.keys():
                    rateDataDict[rate] = {'taxval':rateAmount, 'cess':0.0}
                else:
                    rateDataDict[rate]['taxval'] = rateDataDict[rate]['taxval'] + rateAmount
                    rateDataDict[rate]['cess'] = rateDataDict[rate]['cess'] + 0.0
                if rate not in rateJsonDict.keys():
                    rateJsonDict[rate] = invoiceLineData[1]
                else:
                    for key in invoiceLineData[1].keys():
                        if key in ['rt', 'sply_ty', 'typ']:
                            continue
                        if rateJsonDict[rate].get(key):
                            rateJsonDict[rate][key] = rateJsonDict[rate][key] + invoiceLineData[1][key]
                            rateJsonDict[rate][key] = round(rateJsonDict[rate][key], 2)
                        else:
                            rateJsonDict[rate][key] = invoiceLineData[1][key]
                invData = invoiceLineData[0] + [rateDataDict[rate]['taxval']]
                if invoiceType == 'b2b':
                    invData = invData + [0.0]
                elif invoiceType in ['b2cs', 'b2cl']:
                    invData = invData + [0.0, '']
                rateDict[rate] = invData
        mainData = rateDict.values()
        if rateJsonDict:
            for jsonData in rateJsonDict.values():
                count = count + 1
                jsonItemData.append({"num":count, 'itm_det':jsonData})
        return [mainData, jsonItemData, rateDataDict, rateJsonDict]

    def getInvoiceLineData(self, invoiceLineData, invoiceLineObj, invoiceObj, invoiceType):
        lineData = []
        jsonLineData = {}
        taxedAmount = 0.0
        rate = 0.0
        rateAmount = 0.0
        currency = invoiceObj.currency_id or None
        price = invoiceLineObj.price_subtotal/invoiceLineObj.quantity
        rateObjs = invoiceLineObj.invoice_line_tax_ids
        if rateObjs:
            for rateObj in rateObjs:
                if rateObj.amount_type == "group":
                    for childObj in rateObj.children_tax_ids:
                        rate = childObj.amount*2
                        lineData.append(rate)
                        break
                else:
                    rate = rateObj.amount
                    lineData.append(rate)
                break
            taxData = self.env['gst.tax.data'].getTaxedAmount(rateObjs, price, currency, invoiceLineObj, invoiceObj)
            rateAmount = taxData[1]
            rateAmount = round(rateAmount, 2)
            taxedAmount = taxData[0]
            jsonLineData = self.env['gst.tax.data'].getGstTaxData(invoiceObj, invoiceLineObj, rateObjs, taxedAmount, invoiceType)
        else:
            rateAmount = invoiceLineObj.price_subtotal
            rateAmount = rateAmount * currency.rate
            rateAmount = round(rateAmount, 2)
            lineData.append(0)
            jsonLineData = self.env['gst.tax.data'].getGstTaxData(invoiceObj, invoiceLineObj, False, taxedAmount, invoiceType)
        data = invoiceLineData + lineData
        return [data, jsonLineData, rate, rateAmount]