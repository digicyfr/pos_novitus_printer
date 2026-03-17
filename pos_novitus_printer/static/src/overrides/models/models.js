/** @odoo-module */

import { PosStore } from "@point_of_sale/app/store/pos_store";
import { NovitusPrinter } from "@pos_novitus_printer/app/novitus_printer";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";

/**
 * Odoo 18 PosStore patch for Novitus fiscal printers.
 *
 * Key v18 differences from v17:
 * - create_printer() still exists (same name)
 * - after_load_server_data() REMOVED — not needed, create_printer() called in setup loop
 * - _flush_orders() REMOVED — replaced by syncAllOrders (fiscal data saved via Python)
 * - RPC: this.data.call() instead of this.orm.call()
 * - Notification: this.notification.add() instead of this.env.services.notification.add()
 * - Printers: this.models["pos.printer"].getAll() instead of this.config.printer_ids
 * - Printer data: relPrinter.serialize() output
 */
patch(PosStore.prototype, {
    create_printer(config) {
        if (config.printer_type === "novitus_online") {
            return new NovitusPrinter({
                pos: this,
                ip: config.novitus_printer_ip,
                port: config.novitus_printer_port,
                use_https: config.novitus_use_https,
                printer_id: config.id,
                fiscal_id: config.novitus_fiscal_id,
                ptu_mappings: {
                    ptu_a_tax_id: config.novitus_ptu_a_tax_id || null,
                    ptu_b_tax_id: config.novitus_ptu_b_tax_id || null,
                    ptu_c_tax_id: config.novitus_ptu_c_tax_id || null,
                    ptu_d_tax_id: config.novitus_ptu_d_tax_id || null,
                    ptu_e_tax_id: config.novitus_ptu_e_tax_id || null,
                },
            });
        }
        return super.create_printer(...arguments);
    },

    async printNovitusDailyReport() {
        const allPrinters = this.models["pos.printer"].getAll();
        const novitusPrinter = allPrinters.find(p => p.printer_type === 'novitus_online');
        if (!novitusPrinter) return;

        try {
            const result = await this.data.call(
                'novitus.noviapi', 'print_daily_report_from_pos',
                [novitusPrinter.id]
            );
            if (result && result.success) {
                this.notification.add(_t('Daily Z-report printed successfully.'), { type: 'success' });
            } else {
                this.notification.add(_t('Daily report failed: ') + (result.error || ''), { type: 'danger', sticky: true });
            }
        } catch (error) {
            this.notification.add(_t('Daily report error: ') + (error.message || error.data?.message || error), { type: 'danger', sticky: true });
        }
    },
});
