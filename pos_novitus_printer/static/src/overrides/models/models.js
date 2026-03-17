/** @odoo-module */

import { PosStore } from "@point_of_sale/app/services/pos_store";
import { NovitusPrinter } from "@pos_novitus_printer/app/novitus_printer";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";

/**
 * Odoo 19 PosStore patch for Novitus fiscal printers.
 *
 * Key v19 differences from v18:
 * - PosStore at app/services/pos_store (moved from app/store/)
 * - createPrinter() (renamed from create_printer)
 * - Printer data via relPrinter.raw (not .serialize())
 */
patch(PosStore.prototype, {
    createPrinter(config) {
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
        return super.createPrinter(...arguments);
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
