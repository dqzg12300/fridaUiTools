# fridaUiTools

**English** | [中文](README.md)

fridaUiTools is a PyQt5-based desktop Frida workbench. It brings common connection flows, attach actions, script template management, log viewing, AI-assisted analysis, GumTrace, and memory search into one interface, so you can build a reusable local repository of your own Frida workflows.

![fridaUiTools](img/img.png)

## Project Positioning

- Reduce the daily operating cost of Frida through a desktop UI
- Gradually reshape built-in features into a maintainable template library
- Save commonly used scripts as custom templates and enable them quickly
- Connect to AI-compatible endpoints for AI script generation and AI log analysis

## Feature Overview

- Multiple attach modes: attach current foreground process, attach a specified process, and spawn attach
- Multiple connection modes: USB, WiFi, custom port, and multi-device switching
- Custom script management: template maintenance, quick enable, import and export of hook lists
- Common reversing features: JNI Trace, Stalker, Dump So, Dump Dex, Patch, and Wallbreaker
- AI assistance: log analysis and script generation
- GumTrace workbench: visual trace script generation and log download
- Memory workbench: experimental string/value search, breakpoints, and disassembly support

## Environment Requirements

- Python 3
- ADB must be available, and USB debugging must be enabled on the device
- The target device must already have the matching `frida-server` binary
- Linux, macOS, and Windows are supported

## Install and Run

Using a virtual environment is recommended:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 kmainForm.py
```

If you already have your own Python environment, you can also run:

```bash
pip install -r requirements.txt
python3 kmainForm.py
```

## 5-Minute Quick Start

1. Connect the phone and make sure `adb devices` can see the target device.
2. Start the application with `python3 kmainForm.py`.
3. Select the current device in the main window.
4. Upload and start the matching `frida-server` version from the menu.
5. Switch USB / WiFi connection mode and port when needed.
6. Select the templates or custom scripts you want to enable.
7. Start working with attach current process, attach specified process, or spawn attach.
8. View the output in the log panel.

## AI Configuration

```ini
[ai]
host = https://api.openai.com/v1
apikey = your_api_key
model = gpt-5.4
```

Notes:

- If `host`, `apikey`, or `model` is missing, AI script generation and AI log analysis are disabled automatically
- `config/ai.local.ini` should stay in your personal ignore list and should not be committed
- `host` supports OpenAI-compatible API endpoints

## Thanks

* [jnitrace](https://github.com/chame1eon/jnitrace)
* [r0capture](https://github.com/r0ysue/r0capture)
* [ZenTracer](https://github.com/hluwa/ZenTracer)
* [DroidSSLUnpinning](https://github.com/WooyunDota/DroidSSLUnpinning)
* [frida_dump](https://github.com/lasting-yang/frida_dump)
* [FRIDA-DEXDump](https://github.com/hluwa/FRIDA-DEXDump)
* [FART](https://github.com/hanbinglengyue/FART)
* [sktrace](https://github.com/bmax121/sktrace)
* [Wallbreaker](https://github.com/hluwa/Wallbreaker)
