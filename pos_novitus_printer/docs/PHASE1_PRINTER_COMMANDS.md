# Phase 1 — Printer Commands (copy-paste ready)

Replace `PRINTER_IP` with your printer's actual IP address.

## H-01: Enable NoviAPI (on printer keypad)

```
MENU → Ustawienia (3) → Konfiguracja → Polaczenia → NOVIAPI → OPCJE
  Aktywna = ON
  Protocol = HTTP
  Port = 8888
Save → Restart printer
```

## H-02: Check firmware version (on printer keypad)

```
Informacje → Wersja oprogramowania
Minimums: DEON >= 3.10 | BONO >= 3.00 | HD II >= 3.50 | POINT >= 1.00
```

## H-03: Confirm network reachability

```bash
# Step 1: Ping
ping -c 4 PRINTER_IP

# Step 2: Connection test
curl -v --max-time 5 -H "User-Agent: NoviApi" http://PRINTER_IP:8888/api/v1
# Expect: HTTP 200
```

## H-04: Resolve nov_cmd field names (THE CRITICAL TEST)

```bash
# Step 1: Get token
TOKEN=$(curl -s http://PRINTER_IP:8888/api/v1/token \
  -H 'User-Agent: NoviApi' | \
  python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")
echo "Token: $TOKEN"

# Step 2: Send test receipt via direct_io
curl -X POST http://PRINTER_IP:8888/api/v1/direct_io \
  -H 'Content-Type: application/json' \
  -H 'User-Agent: NoviApi' \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"direct_io":{"nov_cmd":{"h":{"cashier":"TEST","system_no":"T/001"},"l":[{"name":"Test","quantity":"1","unit_price":"1.00","gross_value":"1.00","ptu":"A"}],"b":[{"type":0,"value":"1.00"}],"y":{"total":"1.00","buyer_nip":""}}}}' \
  -v 2>&1 | tee /tmp/novcmd.txt

# Step 3: If 201 — FIELD NAMES ARE CORRECT. Cancel the test job:
JOB_ID=$(python3 -c "import sys,json; print(json.load(sys.stdin)['request']['id'])" < /tmp/novcmd.txt)
curl -X DELETE http://PRINTER_IP:8888/api/v1/direct_io/$JOB_ID \
  -H 'User-Agent: NoviApi' \
  -H "Authorization: Bearer $TOKEN"

# Step 4: If 400 — FIELD NAMES ARE WRONG. Read the error:
python3 -c "import json; print(json.dumps(json.load(open('/tmp/novcmd.txt')), indent=2))"
```

## H-05: Confirm training mode

```bash
# Print a test receipt via direct_io (full 3-step flow)
# Step A: POST
RESP=$(curl -s -X POST http://PRINTER_IP:8888/api/v1/direct_io \
  -H 'Content-Type: application/json' \
  -H 'User-Agent: NoviApi' \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"direct_io":{"nov_cmd":{"h":{"cashier":"TEST","system_no":"T/002"},"l":[{"name":"Kawa test","quantity":"1","unit_price":"5.00","gross_value":"5.00","ptu":"A"}],"b":[{"type":0,"value":"5.00"}],"y":{"total":"5.00","buyer_nip":""}}}}')
JOB_ID=$(echo $RESP | python3 -c "import sys,json; print(json.load(sys.stdin)['request']['id'])")
echo "Job ID: $JOB_ID"

# Step B: PUT (confirm)
curl -s -X PUT http://PRINTER_IP:8888/api/v1/direct_io/$JOB_ID \
  -H 'User-Agent: NoviApi' \
  -H "Authorization: Bearer $TOKEN" \
  -d '""'

# Step C: GET (poll for DONE)
curl -s http://PRINTER_IP:8888/api/v1/direct_io/$JOB_ID?timeout=5000 \
  -H 'User-Agent: NoviApi' \
  -H "Authorization: Bearer $TOKEN"

# Now examine the physical printout:
# - Must say #PARAGON NIEFISKALNY# or #NIEFISKALNY#
# - Must NOT have CRK number
```

## H-07: Cash drawer open

```bash
# Step A: POST drawer command
RESP=$(curl -s -X POST http://PRINTER_IP:8888/api/v1/direct_io \
  -H 'Content-Type: application/json' \
  -H 'User-Agent: NoviApi' \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"direct_io":{"nov_cmd":{"d":{}}}}')
JOB_ID=$(echo $RESP | python3 -c "import sys,json; print(json.load(sys.stdin)['request']['id'])")

# Step B: PUT (confirm)
curl -s -X PUT http://PRINTER_IP:8888/api/v1/direct_io/$JOB_ID \
  -H 'User-Agent: NoviApi' \
  -H "Authorization: Bearer $TOKEN" \
  -d '""'

# Step C: GET (poll — drawer should open after CONFIRMED)
curl -s http://PRINTER_IP:8888/api/v1/direct_io/$JOB_ID?timeout=5000 \
  -H 'User-Agent: NoviApi' \
  -H "Authorization: Bearer $TOKEN"
# Drawer should physically open
```
