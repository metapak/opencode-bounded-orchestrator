# Examples

After installation, ask OpenCode normally: “Fix the checkout total and add a regression test.” The owner maps the request, delegates the write scope to `implementer`, freezes the result, and assigns verification.

Use the ledger for larger work:

```bash
python3 .opencode/tools/ledger.py start checkout-fix --title "Fix checkout total"
python3 .opencode/tools/ledger.py add map --title "Map calculation flow" --owner-role explorer
python3 .opencode/tools/ledger.py add build --title "Implement fix" --owner-role implementer --depends-on map
python3 .opencode/tools/ledger.py status
```

Freeze the exact candidate before independent checks:

```bash
python3 .opencode/tools/candidate.py freeze --label checkout-fix
python3 .opencode/tools/candidate.py verify
```
