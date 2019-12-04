# -*- coding: utf-8 -*-
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields, api
from datetime import datetime


class StockQuantsMoveWizard(models.TransientModel):
    _name = 'stock.quants.move'

    pack_move_items = fields.One2many(
        comodel_name='stock.quants.move_items', inverse_name='move_id',
        string='Quants', domain="[('source_loc', '=', source_loc )]")


    # quant_move_line = fields.One2many('stock.quant', 'Articulos')


    dest_loc = fields.Many2one(
        comodel_name='stock.location', string='Destination Location')

    sour_loc = fields.Many2one(
        comodel_name='stock.location', string='Ubicación origen',)

    destiny = fields.Selection([('warehouse', 'Almacen'), ('package', 'Paquete')], default='warehouse'  , string='Almacenamiento en')

    # rm
    package_loc = fields.Many2one(
        comodel_name='stock.quant.package', string='Paquete destino',)

    quant = fields.Many2one(
        comodel_name='stock.quant', string='Quant',
        domain="[('location_id', '=', sour_loc )]")

    # move to package
    picking_id = fields.Many2one('stock.picking', 'Picking')
    item_ids = fields.One2many('stock.transfer_details_items', 'move_id', 'Items', domain=[('product_id', '!=', False)])
    picking_source_location_id = fields.Many2one('stock.location', string="Head source location", related='picking_id.location_id', store=False, readonly=True)
    picking_destination_location_id = fields.Many2one('stock.location', string="Head destination location", related='picking_id.location_dest_id', store=False, readonly=True)

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
        if self.destiny == 'warehouse':
            self.quant.move_to(self.package_loc)
        elif self.destiny == 'package':
            print("*******************transfer to package", self.env.context.get('active_ids', []))
            # processed_ids = []

            for prod in self.item_ids:
                pack_datas = {
                    'product_id': prod.product_id.id,
                    'product_uom_id': prod.product_uom_id.id,
                    'product_qty': prod.quantity,
                    'package_id': prod.package_id.id,
                    'lot_id': prod.lot_id.id,
                    'location_id': prod.sourceloc_id.id,
                    'location_dest_id': prod.destinationloc_id.id,
                    'result_package_id': prod.result_package_id.id,
                    'date': prod.date if prod.date else datetime.now(),
                    'owner_id': prod.owner_id.id,
                }
                # print("*******************1", pack_datas)
                print("+++++++++++++++++",self.env.context.get('active_ids', []))
                picking = self.env['stock.picking'].create()
                pack_datas['picking_id'] = picking
                # if prod.packop_id:
                #     print("*******************2",prod.packop_id)
                prod.packop_id.with_context(no_recompute=True).write(pack_datas)
                # processed_ids.append(prod.packop_id.id)
                # else:a
                #pack_datas['picking_id'] = self.picking_id.id
                # packop_id = self.env['stock.pack.operation'].create(pack_datas)
                    # processed_ids.append(packop_id.id)

            
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


class stock_transfer_details_items(models.TransientModel):
    _inherit = 'stock.transfer_details_items'

    move_id = fields.Many2one('stock.quants.move', 'Transfer')
