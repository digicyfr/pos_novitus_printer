/** @odoo-module */

import { BasePrinter } from "@point_of_sale/app/printer/base_printer";
import { _t } from "@web/core/l10n/translation";

/**
 * Novitus Online Fiscal Printer Integration
 *
 * This class extends BasePrinter to integrate Novitus online fiscal printers
 * with Odoo POS using the NoviAPI REST protocol.
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

        // Build base URL
        const protocol = this.use_https ? 'https' : 'http';
        this.baseUrl = `${protocol}://${this.ip}:${this.port}`;

        console.log(`[Novitus] Printer initialized: ${this.baseUrl}`);
    }

    /**
     * Print fiscal receipt
     * Called by POS when order is completed
     *
     * @override
     * @param {HTML} receipt - Receipt HTML element
     * @returns {Promise<Object>} Print result
     */
    async printReceipt(receipt) {
        try {
            console.log('[Novitus] printReceipt called');

            // Get order data from POS
            const order = this.pos.get_order();

            if (!order) {
                throw new Error(_t('No active order found'));
            }

            // Prepare receipt data for Novitus
            const receiptData = this.prepareReceiptData(order);

            console.log('[Novitus] Receipt data prepared:', receiptData);

            // Send to printer via backend
            const result = await this.sendPrintingJob(receiptData);

            if (!result.success) {
                return this.getResultsError(result);
            }

            // Store fiscal number in order
            if (result.fiscal_number) {
                await this.saveFiscalNumber(order, result);
            }

            return {
                successful: true,
                fiscalNumber: result.fiscal_number,
                printerId: result.printer_id,
                crkTransmitted: result.crk_transmitted
            };

        } catch (error) {
            console.error('[Novitus] Print error:', error);
            return {
                successful: false,
                message: {
                    title: _t("Fiscal Printing Error"),
                    body: _t("Failed to print fiscal receipt: ") + error.message
                }
            };
        }
    }

    /**
     * Prepare receipt data for Novitus printer
     * Converts POS order to NoviAPI format
     *
     * @param {Object} order - POS order
     * @returns {Object} Receipt data for NoviAPI
     */
    prepareReceiptData(order) {
        const company = this.pos.company;
        const session = this.pos.pos_session;

        // Prepare items
        const items = [];
        for (const line of order.get_orderlines()) {
            // Skip display-only lines
            if (line.display_type) {
                continue;
            }

            // Get PTU rate for this line
            const ptu = this.getPTURate(line);

            items.push({
                name: line.get_product().display_name,
                quantity: line.get_quantity(),
                price: line.get_unit_price(),
                vat_rate: ptu,
                gross_amount: line.get_price_with_tax(),
                net_amount: line.get_price_without_tax(),
            });
        }

        // Get payment method
        let payment_method = 'cash';
        const payments = order.get_paymentlines();
        if (payments && payments.length > 0) {
            const payment = payments[0];
            if (payment.payment_method.type === 'bank') {
                payment_method = 'card';
            } else if (payment.payment_method.type === 'pay_later') {
                payment_method = 'credit';
            }
        }

        // Get customer info
        const partner = order.get_partner();
        const buyer = {
            name: partner ? partner.name : 'Paragon',
            nip: partner && partner.vat ? partner.vat : '',
        };

        // Build payload
        return {
            system_identifier: session.name,
            cashier: this.pos.get_cashier()?.name || this.pos.user.name,
            seller: {
                name: company.name,
                nip: company.vat || '',
                address: company.street || '',
                city: company.city || '',
                postal_code: company.zip || '',
            },
            buyer: buyer,
            items: items,
            payment_method: payment_method,
            total_gross: order.get_total_with_tax(),
            total_net: order.get_total_without_tax(),
            total_vat: order.get_total_tax(),
            currency: this.pos.currency.name,
        };
    }

    /**
     * Get PTU (Polish VAT) rate for order line
     *
     * @param {Object} line - Order line
     * @returns {string} PTU rate ('A', 'B', 'C', 'D', 'E')
     */
    getPTURate(line) {
        const taxes = line.get_taxes();

        if (!taxes || taxes.length === 0) {
            return 'D'; // 0% if no tax
        }

        const tax = taxes[0];

        // Check configured PTU mappings
        if (this.ptu_mappings) {
            if (tax.id === this.ptu_mappings.ptu_a_tax_id) return 'A';
            if (tax.id === this.ptu_mappings.ptu_b_tax_id) return 'B';
            if (tax.id === this.ptu_mappings.ptu_c_tax_id) return 'C';
            if (tax.id === this.ptu_mappings.ptu_d_tax_id) return 'D';
            if (tax.id === this.ptu_mappings.ptu_e_tax_id) return 'E';
        }

        // Fallback: map by tax amount
        const amount = tax.amount;
        if (amount === 23) return 'A';
        if (amount === 8) return 'B';
        if (amount === 5) return 'C';
        if (amount === 0) return 'D';

        return 'E'; // Exempt
    }

    /**
     * Send printing job to Novitus printer
     *
     * @override
     * @param {Object} receiptData - Receipt data
     * @returns {Promise<Object>} Result from printer
     */
    async sendPrintingJob(receiptData) {
        try {
            // Call backend to print via NoviAPI
            const response = await this.env.services.orm.call(
                'novitus.noviapi',
                'print_fiscal_receipt_from_pos',
                [receiptData, this.printer_id]
            );

            console.log('[Novitus] Print response:', response);

            return response;

        } catch (error) {
            console.error('[Novitus] sendPrintingJob error:', error);
            return {
                success: false,
                error: error.message || _t('Unknown error')
            };
        }
    }

    /**
     * Open cash drawer
     *
     * @override
     * @returns {Promise<void>}
     */
    async openCashbox() {
        try {
            console.log('[Novitus] Opening cash drawer');

            const response = await this.env.services.orm.call(
                'novitus.noviapi',
                'open_cashbox',
                [this.printer_id]
            );

            if (!response.success) {
                console.error('[Novitus] Failed to open cash drawer:', response.error);
            }

        } catch (error) {
            console.error('[Novitus] openCashbox error:', error);
        }
    }

    /**
     * Save fiscal number to order
     * Updates order in backend with fiscal receipt information
     *
     * @param {Object} order - POS order
     * @param {Object} result - Print result with fiscal number
     * @returns {Promise<void>}
     */
    async saveFiscalNumber(order, result) {
        try {
            // Store in order data (will be saved when order is synced)
            order.fiscal_receipt_number = result.fiscal_number;
            order.fiscal_printer_id = result.printer_id;
            order.fiscal_receipt_date = new Date().toISOString();
            order.crk_transmitted = result.crk_transmitted || false;

            console.log('[Novitus] Fiscal number stored:', result.fiscal_number);

            // If order is already in backend, update it immediately
            if (order.id) {
                await this.env.services.orm.call(
                    'pos.order',
                    'write',
                    [[order.id], {
                        fiscal_receipt_number: result.fiscal_number,
                        fiscal_printer_id: result.printer_id,
                        fiscal_receipt_date: order.fiscal_receipt_date,
                        is_fiscal_receipt: true,
                        fiscal_print_status: 'printed',
                        crk_transmitted: result.crk_transmitted
                    }]
                );
            }

        } catch (error) {
            console.error('[Novitus] Failed to save fiscal number:', error);
            // Don't throw - fiscal number is already printed,
            // just logging failed
        }
    }

    /**
     * Test connection to printer
     * Used for diagnostics
     *
     * @returns {Promise<Object>} Connection test result
     */
    async testConnection() {
        try {
            console.log('[Novitus] Testing connection to', this.baseUrl);

            const response = await this.env.services.orm.call(
                'novitus.noviapi',
                'test_connection_from_pos',
                [this.printer_id]
            );

            console.log('[Novitus] Connection test result:', response);

            return response;

        } catch (error) {
            console.error('[Novitus] Connection test error:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }
}
