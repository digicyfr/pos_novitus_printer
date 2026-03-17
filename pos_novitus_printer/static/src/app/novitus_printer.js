/** @odoo-module */

import { BasePrinter } from "@point_of_sale/app/printer/base_printer";
import { _t } from "@web/core/l10n/translation";

/**
 * Novitus Online Fiscal Printer — Odoo 18
 *
 * RPC calls go through this.pos.data.call() — the PosStore instance
 * is passed during construction in models.js.
 */
export class NovitusPrinter extends BasePrinter {
    setup({ pos, ip, port, use_https, printer_id, fiscal_id, ptu_mappings }) {
        super.setup(...arguments);

        this.pos = pos;
        this.ip = ip;
        this.port = port || 8888;
        this.use_https = use_https || false;
        this.printer_id = printer_id;
        this.fiscal_id = fiscal_id;
        this.ptu_mappings = ptu_mappings || {};

        const protocol = this.use_https ? 'https' : 'http';
        this.baseUrl = `${protocol}://${this.ip}:${this.port}`;
        console.log(`[Novitus] Printer initialized: ${this.baseUrl}`);

        this._tokenRefreshInterval = setInterval(() => {
            this._refreshToken();
        }, 18 * 60 * 1000);
    }

    destroy() {
        if (this._tokenRefreshInterval) {
            clearInterval(this._tokenRefreshInterval);
            this._tokenRefreshInterval = null;
        }
    }

    // ── Helper: RPC via PosStore.data service (Odoo 18 pattern) ──

    async _rpc(model, method, args) {
        return await this.pos.data.call(model, method, args);
    }

    _notify(message, type = 'info', sticky = false) {
        this.pos.notification.add(message, { type, sticky });
    }

    // ── Token refresh ─────────────────────────────────────────

    async _refreshToken() {
        try {
            await this._rpc('novitus.noviapi', 'test_connection_from_pos', [this.printer_id]);
        } catch (error) {
            console.warn('[Novitus] Background token refresh failed:', error);
        }
    }

    // ── Connection test ───────────────────────────────────────

    async testConnection() {
        try {
            const result = await this._rpc('novitus.noviapi', 'test_connection_from_pos', [this.printer_id]);
            if (result) {
                this._notify(_t('Novitus printer connected successfully.'), 'success');
            } else {
                this._notify(_t('Cannot connect to Novitus printer. Check IP and network.'), 'danger', true);
            }
            return result;
        } catch (error) {
            this._notify(_t('Connection test failed: ') + (error.message || error), 'danger', true);
            return false;
        }
    }

    // ── Print fiscal receipt ──────────────────────────────────

    async printFiscalReceipt(order) {
        if (!order) {
            return { successful: false, message: { title: _t('Error'), body: _t('No active order.') } };
        }

        this._notify(_t('Printing fiscal receipt...'), 'info', true);

        try {
            const result = await this._rpc('novitus.noviapi', 'print_fiscal_receipt_from_pos',
                [order.name, this.printer_id]);

            if (result.success) {
                if (order.id && !result.already_printed) {
                    await this._saveFiscalData(order.id, result);
                }
                order.fiscal_receipt_number = result.fiscal_number;
                order.fiscal_printer_id = result.printer_id;
                order.fiscal_receipt_date = new Date().toISOString();
                order.crk_transmitted = result.crk_transmitted || false;

                const jpkMsg = result.jpkid ? ` (JPK: ${result.jpkid})` : '';
                this._notify(_t('Fiscal receipt printed successfully') + jpkMsg, 'success');
                return { successful: true };
            } else {
                this._notify(_t('Fiscal print failed: ') + (result.error || _t('Unknown error')), 'danger', true);
                return { successful: false, message: { title: _t('Error'), body: result.error } };
            }
        } catch (error) {
            const errorMsg = error.message || error.data?.message || String(error);
            this._showFiscalError(errorMsg);
            return { successful: false, message: { title: _t('Error'), body: errorMsg } };
        }
    }

    async printReceipt(receipt) {
        const order = this.pos.get_order();
        return this.printFiscalReceipt(order);
    }

    // ── Save fiscal data ──────────────────────────────────────

    async _saveFiscalData(orderId, result) {
        try {
            await this._rpc('pos.order', 'write', [[orderId], {
                fiscal_receipt_number: result.fiscal_number || '',
                fiscal_printer_id: result.printer_id || '',
                fiscal_receipt_date: new Date().toISOString(),
                is_fiscal_receipt: true,
                fiscal_print_status: 'printed',
                crk_transmitted: result.crk_transmitted || false,
            }]);
        } catch (error) {
            console.error('[Novitus] Failed to save fiscal data:', error);
        }
    }

    // ── Cash drawer ───────────────────────────────────────────

    async openCashbox() {
        try {
            await this._rpc('novitus.noviapi', 'open_cashbox', [this.printer_id]);
        } catch (error) {
            console.error('[Novitus] openCashbox error:', error);
        }
    }

    // ── Error message helper ──────────────────────────────────

    _showFiscalError(errorMsg) {
        if (errorMsg.includes('409') || errorMsg.includes('Z-report')) {
            this._notify(_t('Daily Z-report required. Run daily report first.'), 'warning', true);
        } else if (errorMsg.includes('429') || errorMsg.includes('rate limit')) {
            this._notify(_t('Printer token limit reached. Wait or reset from printer menu.'), 'danger', true);
        } else if (errorMsg.includes('507') || errorMsg.includes('memory full')) {
            this._notify(_t('CRITICAL: Printer memory full. Contact administrator.'), 'danger', true);
        } else {
            this._notify(_t('Fiscal print failed: ') + errorMsg, 'danger', true);
        }
    }
}
