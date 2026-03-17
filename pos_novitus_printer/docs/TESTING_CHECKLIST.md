# POS Novitus Printer — Testing Checklist

**Module:** pos_novitus_printer v17.0.3.0.0
**Last Updated:** 2026-03-17

This checklist is designed to be followed by a developer with physical access
to a Novitus online fiscal printer. Complete each section in order.

---

## 1. PREREQUISITE SETUP

### 1.1 Enable NoviAPI on the Printer

Navigate on the printer keypad:

```
Ustawienia → Konfiguracja → Połączenia → NOVIAPI → OPCJE
```

Ensure:
- **NOVIAPI** is set to **AKTYWNE** (Active)
- **Protocol** is set to **HTTP** (or HTTPS if certificate is installed)
- **Port** is set to **8888** (default)
- Note the printer's **IP address** (e.g., 192.168.1.100)

### 1.2 Minimum Firmware Versions

| Printer Model | Minimum Firmware | NoviAPI Version |
|---------------|-----------------|-----------------|
| Novitus POINT | ONLINE 3.0 | NoviAPI v1 |
| Novitus HD II Online | ONLINE 2.0 | NoviAPI v1 |
| Novitus BONO Online | ONLINE 2.0 | NoviAPI v1 |
| Novitus DEON Online | ONLINE 2.0 | NoviAPI v1 |

Check firmware version on printer: `Ustawienia → Informacje → Wersja oprogramowania`

### 1.3 Network Configuration

- Printer and Odoo server must be on the same network (or have routed access)
- Static IP recommended for the printer
- Firewall must allow TCP traffic on port 8888
- Verify connectivity: `ping <PRINTER_IP>` from the Odoo server

### 1.4 Odoo Configuration

1. Install module `pos_novitus_printer`
2. Go to Point of Sale > Configuration > Point of Sale
3. Open your POS configuration
4. Under Connected Devices, click "Add a line" in Receipt/Order Printers
5. Select "Novitus Online Fiscal Printer" as the type
6. Enter printer IP and port (8888)
7. Map PTU tax rates (A=23%, B=8%, C=5%, D=0%, E=exempt)
8. Save

---

## 2. PHASE 1: CONNECTIVITY TESTS (no fiscal transactions)

### T01: Connection Test Returns 200 OK

**Steps:**
1. Open the printer configuration form in Odoo
2. Click "Test Connection" button
3. Verify green success notification appears

**Expected:** Status changes to "Connected" within 3 seconds.

**curl equivalent:**
```bash
curl -v -H "User-Agent: NoviApi" http://<PRINTER_IP>:8888/api/v1
# Expect: HTTP 200
```

### T02: Token Acquisition

**Steps:**
1. After T01 passes, check the printer record in Odoo
2. Verify `novitus_token_cache` field is populated with a JWT string
3. Verify `novitus_token_expiry` field has a future datetime

**curl equivalent:**
```bash
curl -v -H "User-Agent: NoviApi" \
  -H "Content-Type: application/json" \
  http://<PRINTER_IP>:8888/api/v1/token
# Expect: HTTP 200, {"token": "eyJ...", "expiration_date": "..."}
```

### T03: Token Refresh via PATCH

**Steps:**
1. Wait 18 minutes (or manually trigger by setting `novitus_token_expiry` to 1 minute from now)
2. Perform any printer action (test connection or print)
3. Check Odoo server logs: should see "refreshing via PATCH" not "fetching new token"
4. Verify `novitus_token_cache` value has changed

**curl equivalent:**
```bash
TOKEN="eyJ..."  # Use token from T02
curl -v -X PATCH \
  -H "User-Agent: NoviApi" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '""' \
  http://<PRINTER_IP>:8888/api/v1/token
# Expect: HTTP 200, new token in response
```

### T04: Queue Status Check

**Steps:**
1. From POS or via code, call `get_queue_status`
2. Verify it returns an integer (expected: 0 if no pending jobs)

**curl equivalent:**
```bash
curl -v \
  -H "User-Agent: NoviApi" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  http://<PRINTER_IP>:8888/api/v1/queue
# Expect: HTTP 200, {"requests_in_queue": 0}
```

---

## 3. PHASE 2: BASIC FISCAL TESTS

### T05: Single Item Receipt — PTU A, Cash, PLN

**Steps:**
1. Open POS, add 1 product with 23% VAT (PTU A), price 10.00 PLN
2. Pay with cash
3. Complete the order
4. Verify fiscal receipt prints on the Novitus printer
5. Check order in Odoo: `is_fiscal_receipt=True`, `fiscal_receipt_number` populated

**Expected:** Physical receipt printed, fiscal number stored in Odoo.

### T06: Multi-Item Receipt — Mixed PTU Rates

**Steps:**
1. Add items covering PTU A (23%), PTU B (8%), PTU C (5%)
2. Pay with cash
3. Verify receipt shows correct PTU breakdown per line

**Expected:** Each line on the printed receipt shows the correct PTU letter.

### T07: Card Payment Receipt

**Steps:**
1. Add 1 product, pay with card (bank payment method)
2. Verify receipt shows payment type as card (type=1)

**Expected:** Payment line on receipt shows card payment, not cash.

### T08: Receipt with Discount

**Steps:**
1. Add product with a discount applied in POS
2. Complete the order
3. Verify the gross_value calculation: `round(unit_price * quantity, 2) == gross_value`

**Expected:** No error 20 from printer. Decimal math is correct.

### T09: Receipt Cancellation (POST then DELETE)

**Steps:**
1. This requires code-level testing or API tool
2. POST a receipt to `/api/v1/direct_io`
3. Before confirming (PUT), send DELETE to cancel
4. Verify job is cancelled and no receipt is printed

**curl sequence:**
```bash
# Step 1: POST (submit)
curl -X POST \
  -H "User-Agent: NoviApi" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"direct_io": {"nov_cmd": {"h": {"cashier": "TEST"}, "l": [{"name": "Test", "quantity": "1", "unit_price": "1.00", "gross_value": "1.00", "ptu": "A"}], "b": [{"type": 0, "value": "1.00"}], "y": {"total": "1.00", "buyer_nip": ""}}}}' \
  http://<PRINTER_IP>:8888/api/v1/direct_io
# Save the "id" from response

# Step 2: CANCEL (delete before confirm)
JOB_ID="..."  # From step 1
curl -X DELETE \
  -H "User-Agent: NoviApi" \
  -H "Authorization: Bearer $TOKEN" \
  http://<PRINTER_IP>:8888/api/v1/direct_io/$JOB_ID
# Expect: job cancelled, no receipt printed
```

### T10: CRK Transmission Verification

**Steps:**
1. After T05, wait 5 minutes
2. Check CRK portal (if you have access) or printer CRK status
3. Verify the receipt was transmitted

**Expected:** Receipt visible in CRK within 5 minutes of printing.

---

## 4. PHASE 3: ERROR HANDLING TESTS

### T11: 409 Test — Daily Report Pending

**Steps:**
1. Trigger a state where a daily report is pending (end-of-day on printer)
2. Attempt to print a receipt
3. Verify clear error: "Daily Z-report is required before printing"

**Expected:** UserError with 409 message, no crash.

### T12: 403 Test — Concurrency

**Steps:**
1. Send two receipts simultaneously from two browser tabs
2. Verify one succeeds and the other retries (check logs for "403 — concurrency, retry")
3. Both should eventually succeed

**Expected:** Retry up to `novitus_max_retries` times with 1-second delay.

### T13: Printer Offline

**Steps:**
1. Disconnect the printer from the network (unplug cable)
2. Attempt to print a receipt
3. Verify error appears within 8 seconds (not 70 seconds)

**Expected:** ConnectionError within `DEFAULT_TIMEOUT_SECONDS` (8s).

### T14: Invalid PTU Mapping — Error 20

**Steps:**
1. Create a product with a manually mismatched price/quantity
   (e.g., unit_price=3.33, qty=3, but gross != 9.99 due to float)
2. Attempt to print
3. Verify our Decimal math prevents error 20

**Expected:** The `_calculate_gross` method using Decimal/ROUND_HALF_UP produces
the exact value the printer expects. No error 20.

---

## 5. PHASE 4: OPERATIONAL TESTS

### T15: Daily Z-Report

**Steps:**
1. Ensure queue is empty (check via `get_queue_status`)
2. Trigger daily report from POS or backend
3. Verify report prints and completes

**Expected:** Report completes with status DONE.

### T16: Cashbox Open

**Steps:**
1. Trigger cash drawer open from POS
2. Verify physical drawer opens

**Expected:** Drawer opens, no error.

### T17: Multi-POS Station Test

**Steps:**
1. Configure 2 POS terminals pointing to the same Novitus printer
2. Process transactions on both simultaneously
3. Verify 403 concurrency handling works (one retries while other completes)

**Expected:** Both transactions complete, fiscal numbers are unique and sequential.

### T18: Stress Test — 100 Consecutive Receipts

**Steps:**
1. Script or manually process 100 receipts in rapid succession
2. Monitor token usage — should NOT exceed 10 GET tokens/hour
   (most should use cached token or PATCH refresh)
3. Verify all 100 receipts have unique fiscal numbers

**Expected:** No 429 errors. Token is reused efficiently.

---

## 6. UNKNOWN TO VERIFY WITH REAL PRINTER

The native `/api/v1/receipt` endpoint field names are not publicly confirmed.
The module currently uses `/api/v1/direct_io` as the primary path, which is
100% verified and works on all 4 target printers.

To discover the native receipt endpoint field names for a potential future
optimization, run this curl sequence:

### T-TEST-NATIVE: Discover Native Receipt Field Names

```bash
# Step 1: Get a token
TOKEN=$(curl -s -H "User-Agent: NoviApi" \
  http://<PRINTER_IP>:8888/api/v1/token | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")

# Step 2: Send a deliberately malformed receipt to /api/v1/receipt
# The 400 error response will reveal the expected JSON schema
curl -v -X POST \
  -H "User-Agent: NoviApi" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"receipt": {"test": true}}' \
  http://<PRINTER_IP>:8888/api/v1/receipt

# Step 3: Read the 400 response carefully
# It should contain validation errors listing the expected field names
# Document every field name and type in a new file: docs/NATIVE_RECEIPT_SCHEMA.md

# Step 4: If 400 response is not informative, try:
curl -v -X POST \
  -H "User-Agent: NoviApi" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{}' \
  http://<PRINTER_IP>:8888/api/v1/receipt

# Step 5: Also check if the printer serves OpenAPI/Swagger docs:
curl -v http://<PRINTER_IP>:8888/swagger/v1/swagger.json
curl -v http://<PRINTER_IP>:8888/openapi.json
curl -v http://<PRINTER_IP>:8888/docs
curl -v http://<PRINTER_IP>:8888/swagger
```

Once the native field names are discovered, a second payload builder can be
added as `_build_receipt_native()` alongside the existing `_build_receipt_direct_io()`,
and the module can prefer the native path with direct_io as fallback.

---

## Results Template

| Test | Date | Result | Notes |
|------|------|--------|-------|
| T01 | | PASS/FAIL | |
| T02 | | PASS/FAIL | |
| T03 | | PASS/FAIL | |
| T04 | | PASS/FAIL | |
| T05 | | PASS/FAIL | |
| T06 | | PASS/FAIL | |
| T07 | | PASS/FAIL | |
| T08 | | PASS/FAIL | |
| T09 | | PASS/FAIL | |
| T10 | | PASS/FAIL | |
| T11 | | PASS/FAIL | |
| T12 | | PASS/FAIL | |
| T13 | | PASS/FAIL | |
| T14 | | PASS/FAIL | |
| T15 | | PASS/FAIL | |
| T16 | | PASS/FAIL | |
| T17 | | PASS/FAIL | |
| T18 | | PASS/FAIL | |
