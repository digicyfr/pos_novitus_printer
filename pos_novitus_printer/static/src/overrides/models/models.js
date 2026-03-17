/** @odoo-module */

import { PosStore } from "@point_of_sale/app/store/pos_store";
import { NovitusPrinter } from "@pos_novitus_printer/app/novitus_printer";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";

/**
 * Odoo 17 PosStore patch for Novitus fiscal printers.
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
                    ptu_a_tax_id: config.novitus_ptu_a_tax_id ? config.novitus_ptu_a_tax_id[0] : null,
                    ptu_b_tax_id: config.novitus_ptu_b_tax_id ? config.novitus_ptu_b_tax_id[0] : null,
                    ptu_c_tax_id: config.novitus_ptu_c_tax_id ? config.novitus_ptu_c_tax_id[0] : null,
                    ptu_d_tax_id: config.novitus_ptu_d_tax_id ? config.novitus_ptu_d_tax_id[0] : null,
                    ptu_e_tax_id: config.novitus_ptu_e_tax_id ? config.novitus_ptu_e_tax_id[0] : null,
                },
            });
        }
        return super.create_printer(...arguments);
    },

    async after_load_server_data() {
        await super.after_load_server_data(...arguments);
        const novitusPrinters = (this.config.printer_ids || []).filter(
            p => p.printer_type === 'novitus_online'
        );
        if (novitusPrinters.length > 0) {
            const receiptPrinter = novitusPrinters.find(
                p => !p.product_categories_ids || p.product_categories_ids.length === 0
            );
            if (receiptPrinter && this.config.other_devices) {
                this.hardwareProxy.printer = this.create_printer(receiptPrinter);
            }
        }
    },

    _flush_orders(orders) {
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
    },

    async printNovitusDailyReport() {
        const novitusPrinters = (this.config.printer_ids || []).filter(
            p => p.printer_type === 'novitus_online'
        );
        if (!novitusPrinters.length) return;

        try {
            const result = await this.orm.call(
                'novitus.noviapi', 'print_daily_report_from_pos',
                [novitusPrinters[0].id]
            );
            if (result && result.success) {
                this.env.services.notification.add(_t('Daily Z-report printed successfully.'), { type: 'success' });
            } else {
                this.env.services.notification.add(_t('Daily report failed: ') + (result.error || ''), { type: 'danger', sticky: true });
            }
        } catch (error) {
            this.env.services.notification.add(_t('Daily report error: ') + (error.message || error.data?.message || error), { type: 'danger', sticky: true });
        }
    },
});
