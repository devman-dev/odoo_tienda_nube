from odoo import http
import base64
from odoo.http import request # -*- coding: utf-8 -*-
import logging
import io
import imghdr
from PIL import Image
_logger = logging.getLogger(__name__)

class PublicController(http.Controller):

    @http.route('/ati_tn_product_template_ids/<int:id>', type='http', auth='public')
    def serve_image(self, id, **kwargs):
        record = request.env['product.product'].sudo().browse(id)
        binary_data = base64.b64decode(record.image_1920) 
        image_format = imghdr.what(None, binary_data) or 'png'

        headers = [('Content-Type', f'image/{image_format.lower()}')]
        return request.make_response(binary_data, headers)
    
    @http.route('/ati_tn_product_template_galery_ids/<int:id>', type='http', auth='public')
    def serve_image_galery(self, id, **kwargs):
        record = request.env['product.image.tn'].sudo().browse(id)
        binary_data = base64.b64decode(record.image_1920) 
        image_format = imghdr.what(None, binary_data) or 'png'
    
        headers = [('Content-Type', f'image/{image_format.lower()}')]
        return request.make_response(binary_data, headers)