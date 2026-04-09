/** @odoo-module */

import { ClosePosPopup } from "@point_of_sale/app/components/popups/closing_popup/closing_popup";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { ask } from "@point_of_sale/app/utils/make_awaitable_dialog";

/**
 * Odoo 19: Patch ClosePosPopup to add Novitus daily Z-report button.
 * Uses ask(this.dialog, {...}) for confirmation.
 * ClosePosPopup path: app/components/popups/closing_popup (moved from app/navbar/)
 * ask() path: app/utils/make_awaitable_dialog (moved from app/store/)
 */
patch(ClosePosPopup.prototype, {
    async printNovitusDailyReport() {
        const allPrinters = this.pos.models["pos.printer"].getAll();
        const novitusPrinter = allPrinters.find(p => p.printer_type === 'novitus_online');
        if (!novitusPrinter) {
            this.pos.notification.add(_t('No Novitus fiscal printer configured.'), { type: 'warning' });
            return;
        }

        const confirmed = await ask(this.dialog, {
            title: _t('Daily Z-Report'),
            body: _t('This will print the daily fiscal Z-report. Continue?'),
        });
        if (!confirmed) return;

        await this.pos.printNovitusDailyReport();
    },
});
