from odoo import models, fields, api
import random

class BankComplaint(models.Model):
    _name = 'bank.complaint'
    _description = 'User Complaint'
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string='Ticket Number')
    subject = fields.Char(string='Subject', required=True)
    description = fields.Text(string='Description')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', required=True)
    account_id = fields.Many2one('bank.account', string='Related Account', required=True)

    date_created = fields.Datetime(string='Date Created', default=fields.Datetime.now)
    duration = fields.Float(string="Duration", tracking=4)

    priority = fields.Selection([
        ('normal', 'Normal'),
        ('urgent', 'Urgent'),
    ], string='Priority', default='normal', required=True)
    assigned_to = fields.Many2one('hr.employee', string='Assigned To', required=True)

    tag_ids = fields.Many2many('bank.complaint.tag', string='Tags')

    customer_id = fields.Many2one(related="account_id.customer_id", string="Related Customer", store=True)
    branch_id = fields.Many2one(related="account_id.branch_id", string="Account Branch", store=True)
    bank_id = fields.Many2one(related="branch_id.bank_id", string="Related Bank", store=True)

    progress = fields.Integer(string="Progress", compute="_compute_progress")

    @api.model
    def create(self, vals):
        ticket_no = self.env['ir.sequence'].next_by_code('bank.complaint')
        vals['name'] = ticket_no
        return super(BankComplaint, self).create(vals)

    @api.depends('state')
    def _compute_progress(self):
        for rec in self:
            if rec.state == 'draft':
                progress = random.randrange(0, 25)
            elif rec.state == "in_progress":
                progress = random.randrange(25, 99)
            elif rec.state == "resolved":
                progress = 100
            else:
                progress = 0
            rec.progress = progress

    def action_in_progress(self):
        template = self.env.ref("bank.complaint_mail_template")
        for rec in self:
            if rec.state == "draft":
                template.send_mail(rec.id, force_send=True)
                rec.state = 'in_progress'

    def action_resolved(self):
        template = self.env.ref("bank.resolve_complaint_mail_template")
        for rec in self:
            if rec.state == "in_progress":
                template.send_mail(rec.id, force_send=True)
                rec.state = 'resolved'
        return {
            'effect': {
                'fadeout': 'slow',
                'message': 'Issue Resolved',
                'type': 'rainbow_man',
            }
        }

    def action_cancel(self):
        template = self.env.ref("bank.resolve_complaint_mail_template")

        for rec in self:
            if rec.state == "draft" or rec.state == "in_progress":
                template.send_mail(rec.id, force_send=True)

                rec.state = 'cancelled'


class ComplaintTag(models.Model):
    _name = 'bank.complaint.tag'
    _description = 'Complaint Tags'
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string='Name', required=True, tracking=True)
    color = fields.Integer(string="Color", tracking=True)
