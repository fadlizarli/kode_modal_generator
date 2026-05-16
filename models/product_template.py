from odoo import models

KODE_PERTAMA = {'1': 'M', '2': 'O', '3': 'B', '4': 'I', '5': 'L',
                '6': 'S', '7': 'E', '8': 'D', '9': 'A', '0': 'N'}
KODE_KEDUA   = {'1': 'A', '2': 'B', '3': 'C', '4': 'D', '5': 'E',
                '6': 'F', '7': 'G', '8': 'H', '9': 'I', '0': 'L'}


def _encode(price, mapping):
    price = int(round(price))
    if price <= 0:
        return ''
    if price % 1_000_000 == 0:
        number, suffix = price // 1_000_000, 'JT'
    elif price % 1_000 == 0:
        number, suffix = price // 1_000, 'RB'
    elif price % 100 == 0:
        number, suffix = price // 100, 'RT'
    else:
        number, suffix = price, ''
    letters = ''.join(mapping.get(d, d) for d in str(number))
    return (letters + ' ' + suffix) if suffix else letters


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def action_generate_kode1(self):
        self.kode_modal = _encode(self.standard_price, KODE_PERTAMA)

    def action_generate_kode2(self):
        self.kode_modal = _encode(self.standard_price, KODE_KEDUA)
