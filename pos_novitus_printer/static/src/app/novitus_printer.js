/** @odoo-module */

import { BasePrinter } from "@point_of_sale/app/printer/base_printer";
import { _t } from "@web/core/l10n/translation";

/**
 * Novitus Online Fiscal Printer Integration
 *
 * This class extends BasePrinter to integrate Novitus online fiscal printers
 * with Odoo POS using the NoviAPI REST protocol.
 *
 * ARCHITECTURE: JavaScript sends order reference to Python backend.
 * Python does ALL payload construction and printer communication.
 * JavaScript handles UI, notifications, and storing fiscal data.
 *
 * Supports:
 * - Novitus POINT (ONLINE 3.0)
 * - Novitus HD II Online (ONLINE 2.0)
 * - Novitus BONO Online
 * - Novitus DEON Online
 */
export class NovitusPrinter extends BasePrinter {
    setup({ ip, port, use_https, printer_id, fiscal_id, ptu_mappings }) {
        super.setup(...arguments);

        this.ip = ip;
        this.port = port || 8888;
        this.use_https = use_https || false;
        this.printer_id = printer_id;
        this.fiscal_id = fiscal_id;
        this.ptu_mappings = ptu_mappings || {};

        // Build base URL for display purposes only
        const protocol = this.use_https ? 'https' : 'http';
        this.baseUrl = `${protocol}://${this.ip}:${this.port}`;

        console.log(`[Novitus] Printer initialized: ${this.baseUrl}`);

        // Set up token refresh interval (every 18 minutes)
        this._tokenRefreshInterval = setInterval(() => {
            this._refreshToken();
        }, 18 * 60 * 1000);
    }

    /**
     * Clean up on destroy
     */
    destroy() {
        if (this._tokenRefreshInterval) {
            clearInterval(this._tokenRefreshInterval);
            this._tokenRefreshInterval = null;
        }
    }

    /**
     * Proactively refresh token to avoid expiry during transactions
     * @private
     */
    async _refreshToken() {
        try {
            await this.env.services.orm.call(
                'novitus.noviapi',
                'test_connection_from_pos',
                [this.printer_id]
            );
            console.log('[Novitus] Token refresh triggered via connection test');
        } catch (error) {
            console.warn('[Novitus] Background token refresh failed:', error);
        }
    }

    /**
     * Test connection to printer
     * @returns {Promise<boolean>}
     */
    async testConnection() {
        try {
            console.log('[Novitus] Testing connection to', this.baseUrl);

            const result = await this.env.services.orm.call(
                'novitus.noviapi',
                'test_connection_from_pos',
                [this.printer_id]
            );

            if (result) {
                this.env.services.notification.add(
                    _t('Novitus printer connected successfully.'),
                    { type: 'success', sticky: false }
                );
            } else {
                this.env.services.notification.add(
                    _t('Cannot connect to Novitus printer. Check IP and network.'),
                    { type: 'danger', sticky: true }
                );
            }

            return result;

        } catch (error) {
            console.error('[Novitus] Connection test error:', error);
            this.env.services.notification.add(
                _t('Connection test failed: ') + (error.message || error),
                { type: 'danger', sticky: true }
            );
            return false;
        }
    }

    /**
     * Print fiscal receipt
     * Sends order reference to Python backend which handles all payload construction
     *
     * @param {Object} order - POS order object
     * @returns {Promise<Object>} {successful: bool}
     */
    async printFiscalReceipt(order) {
        if (!order) {
            return {
                successful: false,
                message: {
                    title: _t('Fiscal Printing Error'),
                    body: _t('No active order found.'),
                },
            };
        }

        // Show printing notification
        const closePrintingNotif = this.env.services.notification.add(
            _t('Printing fiscal receipt...'),
            { type: 'info', sticky: true }
        );

        try {
            // Call Python backend — it handles ALL payload construction
            const result = await this.env.services.orm.call(
                'novitus.noviapi',
                'print_fiscal_receipt_from_pos',
                [order.name, this.printer_id]
            );

            // Close the "Printing..." notification
            if (closePrintingNotif) {
                closePrintingNotif();
            }

            if (result.success) {
                // Save fiscal data to order
                if (order.id && !result.already_printed) {
                    await this._saveFiscalData(order.id, result);
                }

                // Store fiscal number on the local order object for sync
                order.fiscal_receipt_number = result.fiscal_number;
                order.fiscal_printer_id = result.printer_id;
                order.fiscal_receipt_date = new Date().toISOString();
                order.crk_transmitted = result.crk_transmitted || false;

                const jpkMsg = result.jpkid ? ` (JPK: ${result.jpkid})` : '';
                this.env.services.notification.add(
                    _t('Fiscal receipt printed successfully') + jpkMsg,
                    { type: 'success', sticky: false }
                );

                return { successful: true };
            } else {
                this.env.services.notification.add(
                    _t('Fiscal print failed: ') + (result.error || _t('Unknown error')) +
                    _t('. Check printer connection.'),
                    { type: 'danger', sticky: true }
                );

                return {
                    successful: false,
                    message: {
                        title: _t('Fiscal Printing Error'),
                        body: result.error || _t('Unknown error'),
                    },
                };
            }

        } catch (error) {
            // Close the "Printing..." notification
            if (closePrintingNotif) {
                closePrintingNotif();
            }

            console.error('[Novitus] printFiscalReceipt error:', error);

            // Parse specific error types from backend UserError messages
            const errorMsg = error.message || error.data?.message || String(error);

            if (errorMsg.includes('409') || errorMsg.includes('Z-report')) {
                this.env.services.notification.add(
                    _t('Daily Z-report required. Run daily report from POS settings first.'),
                    { type: 'warning', sticky: true }
                );
            } else if (errorMsg.includes('429') || errorMsg.includes('rate limit')) {
                this.env.services.notification.add(
                    _t('Printer token limit reached. Wait or reset from printer menu.'),
                    { type: 'danger', sticky: true }
                );
            } else if (errorMsg.includes('507') || errorMsg.includes('memory full')) {
                this.env.services.notification.add(
                    _t('CRITICAL: Printer memory full. Contact system administrator immediately.'),
                    { type: 'danger', sticky: true }
                );
            } else if (errorMsg.includes('did not respond')) {
                this.env.services.notification.add(
                    _t('Printer did not respond in time. Check printer status and retry.'),
                    { type: 'danger', sticky: true }
                );
            } else {
                this.env.services.notification.add(
                    _t('Fiscal print failed: ') + errorMsg,
                    { type: 'danger', sticky: true }
                );
            }

            return {
                successful: false,
                message: {
                    title: _t('Fiscal Printing Error'),
                    body: errorMsg,
                },
            };
        }
    }

    /**
     * Print receipt — override of BasePrinter
     * Routes to printFiscalReceipt
     *
     * @override
     * @param {HTML} receipt - Receipt HTML element (unused — backend builds payload)
     * @returns {Promise<Object>}
     */
    async printReceipt(receipt) {
        const order = this.pos.get_order();
        return this.printFiscalReceipt(order);
    }

    /**
     * Save fiscal data to order via backend controller
     *
     * @param {number} orderId - POS order database ID
     * @param {Object} result - Fiscal print result from backend
     * @private
     */
    async _saveFiscalData(orderId, result) {
        try {
            await this.env.services.orm.call(
                'pos.order',
                'write',
                [[orderId], {
                    fiscal_receipt_number: result.fiscal_number || '',
                    fiscal_printer_id: result.printer_id || '',
                    fiscal_receipt_date: new Date().toISOString(),
                    is_fiscal_receipt: true,
                    fiscal_print_status: 'printed',
                    crk_transmitted: result.crk_transmitted || false,
                }]
            );
            console.log('[Novitus] Fiscal data saved for order', orderId);
        } catch (error) {
            // Don't throw — fiscal receipt is already printed on the printer,
            // data save failure is non-critical for the customer
            console.error('[Novitus] Failed to save fiscal data:', error);
        }
    }

    /**
     * Print daily Z-report
     * @returns {Promise<Object>}
     */
    async printDailyReport() {
        try {
            const result = await this.env.services.orm.call(
                'novitus.noviapi',
                'print_daily_report_from_pos',
                [this.printer_id]
            );

            if (result.success) {
                this.env.services.notification.add(
                    _t('Daily Z-report printed successfully.'),
                    { type: 'success', sticky: false }
                );
            } else {
                this.env.services.notification.add(
                    _t('Daily report failed: ') + (result.error || ''),
                    { type: 'danger', sticky: true }
                );
            }

            return result;

        } catch (error) {
            const errorMsg = error.message || error.data?.message || String(error);

            if (errorMsg.includes('409') || errorMsg.includes('Z-report')) {
                this.env.services.notification.add(
                    _t('Daily Z-report required. Run daily report from POS settings first.'),
                    { type: 'warning', sticky: true }
                );
            } else {
                this.env.services.notification.add(
                    _t('Daily report error: ') + errorMsg,
                    { type: 'danger', sticky: true }
                );
            }

            return { success: false, error: errorMsg };
        }
    }

    /**
     * Open cash drawer
     * @returns {Promise<void>}
     */
    async openCashbox() {
        try {
            console.log('[Novitus] Opening cash drawer');

            const result = await this.env.services.orm.call(
                'novitus.noviapi',
                'open_cashbox',
                [this.printer_id]
            );

            if (!result) {
                console.error('[Novitus] Failed to open cash drawer');
            }

        } catch (error) {
            console.error('[Novitus] openCashbox error:', error);
        }
    }

    /**
     * Get printer queue status
     * @returns {Promise<number>} Number of requests in queue
     */
    async getQueueStatus() {
        try {
            const count = await this.env.services.orm.call(
                'novitus.noviapi',
                'get_queue_status',
                [this.printer_id]
            );
            return count;
        } catch (error) {
            console.error('[Novitus] getQueueStatus error:', error);
            return 0;
        }
    }
}
