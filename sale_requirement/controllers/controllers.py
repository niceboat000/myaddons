# -*- coding: utf-8 -*-
from odoo import http

# class QuestionBank(http.Controller):
#     @http.route('/question_bank/question_bank/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/question_bank/question_bank/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('question_bank.listing', {
#             'root': '/question_bank/question_bank',
#             'objects': http.request.env['question_bank.question_bank'].search([]),
#         })

#     @http.route('/question_bank/question_bank/objects/<model("question_bank.question_bank"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('question_bank.object', {
#             'object': obj
#         })