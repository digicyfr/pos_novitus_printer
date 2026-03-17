/** @odoo-module */

import { ClosePosPopup } from "@point_of_sale/app/components/popups/closing_popup/closing_popup";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";

/**
 * Patch ClosePosPopup to add Novitus daily Z-report button.
 * The button calls pos.printNovitusDailyReport() which is defined
 * in the PosStore patch (models.js).
 */
patch(ClosePosPopup.prototype, {
    async printNovitusDailyReport() {
        // Check if Novitus printer is configured
        const novitusPrinters = (this.pos.config.printer_ids || []).filter(
            p => p.printer_type === 'novitus_online'
        );
        if (novitusPrinters.length === 0) {
            this.env.services.notification.add(
                _t('No Novitus fiscal printer configured.'),
                { type: 'warning' }
            );
            return;
        }

        // Confirmation dialog
        const confirmed = await this.popup.add(this.constructor.components?.ConfirmPopup || (await import("@point_of_sale/app/generic_components/popups/confirm_popup")).default, {
            title: _t('Daily Z-Report'),
            body: _t('This will print the daily fiscal Z-report. Continue?'),
        });

        if (!confirmed) {
            return;
        }

        // Delegate to PosStore method
        await this.pos.printNovitusDailyReport();
    },
});
