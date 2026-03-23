# AGENTS.md

## Repo overview
- Project: `fridaUiTools`
- Stack: PyQt5 desktop UI + Frida scripts + Python helpers
- Main entry: `kmainForm.py`
- Script loader: `TraceThread.py`
- Custom script module: `forms/Custom.py` + `ui/custom.py`
- Runtime config: `config/conf.ini`

## Useful commands
- Syntax check:
  - `python3 -m py_compile kmainForm.py TraceThread.py forms/Custom.py forms/AiSettings.py ui/custom.py ui/aiSettings.py utils/AiUtil.py utils/IniUtil.py`
- Offscreen UI smoke test:
  - `QT_QPA_PLATFORM=offscreen python3 - <<'PY'`
    `from PyQt5.QtWidgets import QApplication`
    `from kmainForm import kmainForm`
    `app = QApplication([])`
    `form = kmainForm()`
    `print(form.groupLogs.count())`
    `form.close()`
    `app.quit()`
    `PY`

## Notes
- `config/type.json` and `config/type_en.json` define checkbox-driven hook metadata.
- New AI capabilities use OpenAI-compatible chat endpoints configured through `config/conf.ini` `[ai]` section.
- If `apikey`, `host`, or `model` is missing, AI actions must stay disabled.
- Main log analysis uses output log buffer in `kmainForm.py`; external log files can temporarily replace the live view and then be restored.
- `refreshChecks()` should update checkboxes silently to avoid reopening hook dialogs during hook-list import/load.
- Main window now relies on dynamic regrouping inside `initSmartLayout()` / `configureCommonToolsPanel()` / `configureHookPanel()` instead of editing the generated `ui/kmain.py` heavily.
- Added practical Frida preset scripts: `root_bypass`, `webview_debug`, `okhttp_logger`, `shared_prefs_watch`, `sqlite_logger`, `clipboard_monitor`, `intent_monitor`.
- `kmainForm.py` contains the authoritative checkbox/tag wiring for preset scripts; `TraceThread.py` contains the authoritative JS assembly order.
