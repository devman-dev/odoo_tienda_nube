from odoo import http
import base64
from odoo.http import request # -*- coding: utf-8 -*-
import logging
import io
from PIL import Image
_logger = logging.getLogger(__name__)

class PublicController(http.Controller):

    @http.route('/ati_tn_product_template_ids/<int:id>', type='http', auth='public')
    def serve_image(self, id, **kwargs):
        record = request.env['product.product'].sudo().browse(id)
        binary_data = base64.b64decode(record.image_1920) 
        
        image = Image.open(io.BytesIO(binary_data))
        image_format = 'PNG'

        image_data = io.BytesIO()
        image.save(image_data, format=image_format)
        image_data.seek(0)

        headers = [('Content-Type', f'image/{image_format.lower()}')]
        return request.make_response(image_data, headers)