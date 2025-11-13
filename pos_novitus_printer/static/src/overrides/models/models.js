/** @odoo-module */

import { PosStore } from "@point_of_sale/app/store/pos_store";
import { NovitusPrinter } from "@pos_novitus_printer/app/novitus_printer";
import { patch } from "@web/core/utils/patch";

/**
 * Patch PosStore to support Novitus printers
 *
 * This integrates Novitus printer creation into the standard POS printer system,
 * following the same pattern as Epson printers.
 */
patch(PosStore.prototype, {
    /**
     * Create printer instance based on configuration
     *
     * @override
     * @param {Object} config - Printer configuration from pos.printer model
     * @returns {Object} Printer instance (NovitusPrinter or base printer)
     */
    create_printer(config) {
        if (config.printer_type === "novitus_online") {
            console.log('[Novitus] Creating Novitus printer instance:', config.name);

            // Gather PTU tax mappings
            const ptu_mappings = {
                ptu_a_tax_id: config.novitus_ptu_a_tax_id ?
config.novitus_ptu_a_tax_id[0] : null,
                ptu_b_tax_id: config.novitus_ptu_b_tax_id ? config.novitus_ptu_b_tax_id[0] : null,
                ptu_c_tax_id: config.novitus_ptu_c_tax_id ? config.novitus_ptu_c_tax_id[0] : null,
                ptu_d_tax_id: config.novitus_ptu_d_tax_id ? config.novitus_ptu_d_tax_id[0] : null,
                ptu_e_tax_id: config.novitus_ptu_e_tax_id ? config.novitus_ptu_e_tax_id[0] : null,
            };

            return new NovitusPrinter({
                ip: config.novitus_printer_ip,
                port: config.novitus_printer_port,
                use_https: config.novitus_use_https,
                printer_id: config.id,
                fiscal_id: config.novitus_fiscal_id,
                ptu_mappings: ptu_mappings
            });
        }

        // Fall back to parent implementation for other printer types
        return super.create_printer(...arguments);
    },

    /**
     * Setup session - load Novitus printers
     *
     * @override
     */
    async after_load_server_data() {
        await super.after_load_server_data(...arguments);

        // Check if we have any Novitus printers configured
        const novitusPrinters = this.config.printer_ids.filter(
            p => p.printer_type === 'novitus_online'
        );

        if (novitusPrinters.length > 0) {
            console.log(`[Novitus] Found ${novitusPrinters.length} Novitus printer(s) configured`);

            // If we have a receipt printer configured and it's Novitus
            const receiptPrinter = novitusPrinters.find(p => !p.product_categories_ids || p.product_categories_ids.length === 0);

            if (receiptPrinter && this.config.other_devices) {
                console.log('[Novitus] Setting up Novitus receipt printer:', receiptPrinter.name);
                this.hardwareProxy.printer = this.create_printer(receiptPrinter);
            }
        }
    }
});

/**
 * Extend pos.order to include fiscal receipt fields
 */
patch(PosStore.prototype, {
    /**
     * Override _flush_orders to ensure fiscal data is included
     */
    _flush_orders(orders) {
        // Add fiscal fields to order data before flushing
        for (const order of orders) {
            if (order.fiscal_receipt_number) {
                order.data.fiscal_receipt_number = order.fiscal_receipt_number;
                order.data.fiscal_printer_id = order.fiscal_printer_id;
                order.data.fiscal_receipt_date = order.fiscal_receipt_date;
                order.data.is_fiscal_receipt = true;
                order.data.fiscal_print_status = 'printed';
                order.data.crk_transmitted = order.crk_transmitted || false;
            }
        }

        return super._flush_orders(...arguments);
    }
});
