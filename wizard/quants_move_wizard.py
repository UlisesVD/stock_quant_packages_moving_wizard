# -*- coding: utf-8 -*-
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields, api


class StockQuantsMoveWizard(models.TransientModel):
    _name = 'stock.quants.move'

    pack_move_items = fields.One2many(
        comodel_name='stock.quants.move_items', inverse_name='move_id',
        string='Quants', domain="[('source_loc', '=', source_loc )]")

    dest_loc = fields.Many2one(
        comodel_name='stock.location', string='Destination Location',
        required=True)

    @api.model
    def default_get(self, fields):
        res = super(StockQuantsMoveWizard, self).default_get(fields)
        quants_ids = self.env.context.get('active_ids', [])
        if not quants_ids:
            return res
        quant_obj = self.env['stock.quant']
        quants = quant_obj.browse(quants_ids)

        items = []

        #.filtered(lambda q: not q.package_id)
        for quant in quants:
            item = {
                'quant': quant.id,
                'source_loc': quant.location_id.id,
            }
            items.append(item)
        res.update(pack_move_items=items)
        return res

    @api.one
    def do_transfer(self):
        for item in self.pack_move_items:
            item.quant.move_to(self.dest_loc)
        return True


    @api.multi
    @api.onchange('pack_move_items')
    def onchange_source_loc(self):
        print("***********ch")
        for locac in self:
            locac.update({'pack_move_items': None})

        if locac.pack_move_items:
            return {'domain': {
                'pack_move_items': [('location_id', '=', self.pack_move_items.source_loc.id)],
            }}
            
    # @api.model
    # @api.onchange('pack_move_items')
    # def onchange_source_loc(self):
    #     print("**************change:", self.pack_move_items.source_loc)
    #     quants_ids = self.env.context.get('active_ids', [])

    #     quant_obj = self.env['stock.quant']
    #     quants = quant_obj.search([('location_id', '=', self.pack_move_items.source_loc.id)])
    #     print("********************", quants)
    #     items = []
    #     for quant in quants.filtered(lambda q: not q.package_id):
    #         item = {
    #             'quant': quant.id,
    #             'source_loc': quant.location_id.id,
    #         }
    #         items.append(item)
    #     self.pack_move_items = items 
    #     print("*************finish:", items)


class StockQuantsMoveItems(models.TransientModel):
    _name = 'stock.quants.move_items'
    _description = 'Picking wizard items'

    move_id = fields.Many2one(
        comodel_name='stock.quants.move', string='Quant move')
    quant = fields.Many2one(
        comodel_name='stock.quant', string='Quant',
        domain=[('package_id', '=', False)])
    source_loc = fields.Many2one(
        comodel_name='stock.location', string='Source Location', required=True)

    @api.one
    @api.onchange('quant')
    def onchange_quant(self):
        self.source_loc = self.quant.location_id
