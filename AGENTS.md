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
- Process intelligence now comes from both `appInfoFlush()` (adb `dumpsys` / `pm`) and `js/default.js::loadAppInfo()` (Frida runtime + Android `ApplicationInfo` / `PackageInfo`), then renders into the dynamic key-value tables created by `configureInfoTabs()`.
- Runtime language switching no longer relies on restart: `switchLanguage()` + `apply_app_language()` refresh the main window immediately, while `forms/Custom.py` and `forms/AiSettings.py` expose `refreshTranslations()` for safe child-dialog updates.
- Advanced-tool buttons are no longer a fixed 2-column grid; `rebuildAdvancedToolGrid()` adapts the column count to panel width to avoid the previously uneven layout.
- Release automation is defined by `.github/workflows/build-release.yml`; it uses `tools/build_release.py` (PyInstaller) and `tools/package_release.py` (zip archive) to publish per-platform artifacts on tag pushes.

- English runtime switching now has a manual fallback layer in `kmainForm.py`, `forms/Custom.py`, and `forms/AiSettings.py`; an offscreen CJK-text scan is a useful regression check after UI changes.
- Main window default size is intentionally larger (`1440x960`, min `1240x860`) and common-tool cards also reflow responsively via `rebuildResponsiveCards()` to avoid clipped/overlapping buttons.
- GumTrace integration uses the upstream release asset `exec/libGumTrace.so` (currently from `lidongyooo/GumTrace` release `1.2.0`), uploaded through the dynamic `actionPushGumTrace` menu item to `/data/local/tmp/libGumTrace.so`.
- The custom-script catalog now includes `custom/GumTrace_trace_sample.js`, which exposes `call_funs.gumtrace_start/gumtrace_stop/gumtrace_help` and keeps auto-trace disabled by default for safety.
- Assist-work tab now includes `btnPullGumTraceLog`, which searches common remote locations (`/data/local/tmp`, `/sdcard`, current package `files/`) for `gumtrace*.log`, copies private-app logs to `/sdcard/gumtrace_export/` when needed, then pulls them into `./logs/gumtrace/`.
- Beyond the base GumTrace sample, the custom-script catalog now also ships `GumTrace_offset_auto_trace.js` (offset trigger) and `GumTrace_export_trigger_trace.js` (export/symbol trigger) for more realistic native-analysis workflows.

- Main window was further redesigned into a dashboard/workbench layout: top summary cards + left operation panels + right log/status workspace. Keep future layout tweaks inside `kmainForm.py` dynamic builders instead of editing `ui/kmain.py` directly.
- Attach-process tab is now organized as `Native explorer -> Java explorer -> attached RE info`; app-info tab uses a horizontal splitter for base info vs extended metadata; assist tab uses a dedicated GumTrace log center.
- A dedicated GumTrace workbench tab now lives in `kmainForm.py` and persists settings in the `[gumtrace]` section of `config/conf.ini`. It generates custom-module-compatible scripts via `utils/GumTraceUtil.py` and can auto-add them to the active custom hook list.
- `forms/Custom.py` now exposes `upsertCustomScript()`, `ensureCustomHook()`, and `openCustomScript()` so other UI panels can generate/update scripts without duplicating custom-module persistence logic.
- GumTrace templates (`GumTrace_trace_sample.js`, `GumTrace_offset_auto_trace.js`, `GumTrace_export_trigger_trace.js`) now all support module whitelists and thread-ID filtering; `pullGumTraceLog()` should also honor the workbench-configured output path and auto-open the local directory when enabled.


