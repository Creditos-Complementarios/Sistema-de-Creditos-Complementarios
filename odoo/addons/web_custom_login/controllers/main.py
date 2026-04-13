from odoo.addons.web.controllers.home import Home
from odoo import http


class CustomHome(Home):
    @http.route('/web/login', type='http', auth='none', sitemap=False)
    def web_login(self, redirect=None, **kw):
        response = super().web_login(redirect=redirect, **kw)
        return response
