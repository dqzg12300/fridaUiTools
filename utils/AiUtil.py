import json
import lzma
import os
import re
import subprocess
import tempfile
import urllib.error
import urllib.request

from PyQt5.QtCore import QThread, pyqtSignal

from utils.IniUtil import IniConfig


AI_SECTION = "ai"
AI_REQUIRED_FIELDS = {
    "apikey": {"China": "API Key", "English": "API Key"},
    "host": {"China": "Host", "English": "Host"},
    "model": {"China": "模型", "English": "Model"},
}

HOOK_SYSTEM_PROMPT = """你是一名资深 Frida/Android 逆向工程师。
你要为 fridaUiTools 生成可直接保存到 custom 模块中的自定义 hook 脚本。
请严格遵守以下规则：
1. 只输出 JavaScript 代码，不要输出 Markdown 代码块，不要解释说明。
2. 代码必须兼容 Frida Java.perform 风格，尽量保证异常安全。
3. 必须包含清晰的日志输出，方便在 fridaUiTools 输出日志中查看。
4. 如果需要导出主动调用函数，请使用全局对象 call_funs，例如：call_funs.demo = function(args) { ... }。
5. 如果用户没有明确要求其他名字，请默认保留一个可运行的 call_funs.demo 示例入口，便于在 UI 中直接验证脚本是否工作。
6. 如果需求不明确，请给出一个安全、通用、可运行的最小实现，并在日志中标记 TODO。
7. 自定义模块保存的脚本会被工具直接拼接执行，因此不要再次包裹额外的模块系统，不要输出 import/require。
8. 不要使用 console.log，统一使用 klog 输出日志。
9. 如果脚本里还没有 klog，请先定义：
function klog(data,...args){
    for (let item of args){
        data += "\t" + item;
    }
    var message = {};
    message["jsname"] = "custom";
    message["data"] = data;
    send(message);
}
10. 日志内容尽量使用 [custom] 前缀，例如：klog('[custom] hook installed')。
"""

HOOK_USER_TEMPLATE = """请根据下面信息生成 fridaUiTools custom 模块脚本：
脚本别名：{name}
备注：{remark}
用户需求：
{requirement}

请优先按以下结构组织：
- 如未提供 klog，请先定义与 custom 模块兼容的 klog(data,...args)
- 先定义需要的辅助函数
- 再在 Java.perform(function() {{ ... }}) 中完成 hook
- 如需主动调用函数，定义 call_funs.xxx = function(...) {{ ... }}
- 日志统一用 klog 输出，并以 [custom] 前缀输出
"""

LOG_ANALYSIS_SYSTEM_PROMPT = """你是一名 Android 动态分析与 Frida 调试专家。
你会分析日志，提炼关键信息、异常原因、可疑点和下一步 hook 建议。
输出要求：
1. 使用中文输出。
2. 结构尽量包含：概览、关键发现、风险/异常、下一步建议。
3. 若日志中包含明显的类名、so 名、方法名、异常堆栈、证书锁定、root 检测、反调试、网络请求等，需主动指出。
4. 不要编造日志中不存在的事实；不确定时明确写出“不确定”。
"""

LOG_ANALYSIS_USER_TEMPLATE = """请分析以下日志内容，并给出下一步 Frida hook 建议。
分析重点：{focus}
日志内容如下：
{content}
"""

SCRIPT_TUNE_SYSTEM_PROMPT = """你是一名资深 Frida/Android 逆向工程师与代码修复助手。
你要针对 fridaUiTools custom 模块脚本做“局部微调”，不能整份重写脚本。
必须严格遵守以下规则：
1. 只输出 JSON，不要输出 Markdown，不要解释说明。
2. 顶层结构必须为：
{
  "summary": "本次修改摘要",
  "operations": [
    {
      "action": "replace|insert_before|insert_after",
      "target": "需要精确匹配的原始代码片段",
      "content": "替换后或插入的新代码片段",
      "reason": "修改原因"
    }
  ]
}
3. 只能返回局部修改指令，不能返回整份完整脚本。
4. target 必须来自用户提供的当前脚本原文，并且尽量短小、稳定、可精确定位。
5. 优先使用 replace；只有在确实需要新增代码时才使用 insert_before 或 insert_after。
6. 修改后的脚本必须继续兼容 fridaUiTools custom 模块，日志统一使用 klog，不要使用 console.log。
7. 如果问题信息不足，也要给出最小可行修复；不要返回空 operations。
"""

SCRIPT_TUNE_USER_TEMPLATE = """请根据下面信息，对脚本生成局部修复指令：
脚本别名：{name}
备注：{remark}

当前问题描述：
{issue}

相关日志（可为空）：
{log_content}

当前脚本如下：
{script}
"""


class AiService:
    def __init__(self, config=None):
        self.config = config or IniConfig()

    def get_config(self):
        data = self.config.read_section(AI_SECTION)
        return {
            "apikey": data.get("apikey", "").strip(),
            "host": data.get("host", "").strip(),
            "model": data.get("model", "").strip(),
        }

    def missing_fields(self, language="China"):
        language = "English" if language == "English" else "China"
        config = self.get_config()
        return [labels[language] for key, labels in AI_REQUIRED_FIELDS.items() if not config.get(key)]

    def is_available(self):
        return len(self.missing_fields()) == 0

    def missing_message(self, language="China"):
        language = "English" if language == "English" else "China"
        missing = self.missing_fields(language)
        if not missing:
            return "AI configuration is ready" if language == "English" else "AI 配置可用"
        if language == "English":
            return "Missing " + " / ".join(missing) + ". Configure AI settings first"
        return "未配置 " + " / ".join(missing) + "，请先在设置中完成 AI 配置"

    def _build_endpoint(self, host):
        host = host.rstrip("/")
        if host.endswith("/chat/completions"):
            return host
        if host.endswith("/v1"):
            return host + "/chat/completions"
        return host + "/v1/chat/completions"

    def chat(self, messages, temperature=0.2, timeout=120):
        chunks = []

        def on_chunk(text):
            chunks.append(text)

        self.chat_stream(messages, on_chunk=on_chunk, temperature=temperature, timeout=timeout)
        return "".join(chunks).strip()

    def chat_stream(self, messages, on_chunk=None, temperature=0.2, timeout=120):
        config = self.get_config()
        missing = self.missing_fields()
        if missing:
            raise ValueError(self.missing_message())
        payload = json.dumps({
            "model": config["model"],
            "messages": messages,
            "temperature": temperature,
            "stream": True,
        }).encode("utf-8")
        request = urllib.request.Request(
            self._build_endpoint(config["host"]),
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {config['apikey']}",
                "Accept": "text/event-stream",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                content_type = response.headers.get("Content-Type", "")
                if "text/event-stream" in content_type.lower():
                    return self._read_stream_response(response, on_chunk=on_chunk)
                data = json.loads(response.read().decode("utf-8"))
                content = self._extract_content_from_response(data)
                if on_chunk and content:
                    on_chunk(content)
                return content.strip()
        except urllib.error.HTTPError as error:
            body = error.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"AI 请求失败: HTTP {error.code} {body}")
        except urllib.error.URLError as error:
            raise RuntimeError(f"AI 连接失败: {error}")
        except Exception as error:
            raise RuntimeError(f"AI 请求异常: {error}")

    def generate_hook_script(self, requirement, name="", remark=""):
        requirement = (requirement or "").strip()
        if not requirement:
            raise ValueError("AI 生成脚本前请先填写需求说明")
        result = self.chat([
            {"role": "system", "content": HOOK_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": HOOK_USER_TEMPLATE.format(
                    name=name or "未命名脚本",
                    remark=remark or "无",
                    requirement=requirement,
                ),
            },
        ])
        return self.normalize_hook_script(self.extract_code(result))

    def generate_hook_script_stream(self, requirement, name="", remark="", on_chunk=None):
        requirement = (requirement or "").strip()
        if not requirement:
            raise ValueError("AI 生成脚本前请先填写需求说明")
        chunks = []

        def handle_chunk(text):
            chunks.append(text)
            if on_chunk:
                on_chunk(text)

        self.chat_stream([
            {"role": "system", "content": HOOK_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": HOOK_USER_TEMPLATE.format(
                    name=name or "未命名脚本",
                    remark=remark or "无",
                    requirement=requirement,
                ),
            },
        ], on_chunk=handle_chunk)
        return self.normalize_hook_script(self.extract_code("".join(chunks)))

    def analyze_log(self, content, focus="定位异常、识别关键 hook 点"):
        content = (content or "").strip()
        if not content:
            raise ValueError("没有可供分析的日志内容")
        if len(content) > 16000:
            content = content[-16000:]
        return self.chat([
            {"role": "system", "content": LOG_ANALYSIS_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": LOG_ANALYSIS_USER_TEMPLATE.format(
                    focus=focus or "定位异常、识别关键 hook 点",
                    content=content,
                ),
            },
        ], temperature=0.1)

    def analyze_log_stream(self, content, focus="定位异常、识别关键 hook 点", on_chunk=None):
        content = (content or "").strip()
        if not content:
            raise ValueError("没有可供分析的日志内容")
        if len(content) > 16000:
            content = content[-16000:]
        return self.chat_stream([
            {"role": "system", "content": LOG_ANALYSIS_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": LOG_ANALYSIS_USER_TEMPLATE.format(
                    focus=focus or "定位异常、识别关键 hook 点",
                    content=content,
                ),
            },
        ], on_chunk=on_chunk, temperature=0.1)

    def tune_hook_script(self, script_text, issue, log_content="", name="", remark=""):
        script_text = (script_text or "").strip()
        issue = (issue or "").strip()
        log_content = (log_content or "").strip()
        if not script_text:
            raise ValueError("没有可供微调的脚本内容")
        if not issue and not log_content:
            raise ValueError("请先描述脚本问题，或提供相关日志")
        if len(log_content) > 12000:
            log_content = log_content[-12000:]
        result = self.chat([
            {"role": "system", "content": SCRIPT_TUNE_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": SCRIPT_TUNE_USER_TEMPLATE.format(
                    name=name or "未命名脚本",
                    remark=remark or "无",
                    issue=issue or "请根据日志与脚本推断问题并做最小修复",
                    log_content=log_content or "无",
                    script=script_text,
                ),
            },
        ], temperature=0.1)
        payload = self.parse_script_tune_payload(result)
        return json.dumps(payload, ensure_ascii=False, indent=2)

    @staticmethod
    def _extract_content_from_response(data):
        try:
            content = data["choices"][0]["message"]["content"]
        except Exception:
            raise RuntimeError(f"AI 返回格式异常: {data}")
        if isinstance(content, list):
            text_parts = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    text_parts.append(item.get("text", ""))
            return "".join(text_parts)
        return content

    @staticmethod
    def _extract_stream_delta(data):
        try:
            choice = data.get("choices", [{}])[0]
            delta = choice.get("delta", {})
        except Exception:
            return ""
        content = delta.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            text_parts = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    text_parts.append(item.get("text", ""))
            return "".join(text_parts)
        if isinstance(delta.get("text"), str):
            return delta.get("text", "")
        return ""

    def _read_stream_response(self, response, on_chunk=None):
        full_text = []
        event_lines = []
        for raw_line in response:
            line = raw_line.decode("utf-8", errors="ignore").strip()
            if not line:
                text = self._consume_stream_event(event_lines, on_chunk=on_chunk)
                if text:
                    full_text.append(text)
                event_lines = []
                continue
            event_lines.append(line)
        text = self._consume_stream_event(event_lines, on_chunk=on_chunk)
        if text:
            full_text.append(text)
        return "".join(full_text).strip()

    def _consume_stream_event(self, lines, on_chunk=None):
        if not lines:
            return ""
        data_lines = [line[5:].strip() for line in lines if line.startswith("data:")]
        payload = "\n".join(data_lines).strip()
        if not payload or payload == "[DONE]":
            return ""
        try:
            data = json.loads(payload)
        except Exception:
            return ""
        chunk = self._extract_stream_delta(data)
        if chunk and on_chunk:
            on_chunk(chunk)
        return chunk

    @staticmethod
    def normalize_hook_script(text):
        text = (text or "").strip()
        if not text:
            return text
        return text.replace("console.log(", "klog(")

    @staticmethod
    def extract_code(text):
        text = (text or "").strip()
        if text.startswith("```"):
            match = re.search(r"```(?:javascript|js)?\s*(.*?)```", text, re.S)
            if match:
                return match.group(1).strip()
        return text

    @staticmethod
    def extract_json(text):
        text = (text or "").strip()
        if not text:
            raise RuntimeError("AI 未返回可解析的 JSON 内容")
        if text.startswith("```"):
            match = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
            if match:
                text = match.group(1).strip()
        try:
            return json.loads(text)
        except Exception:
            pass
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except Exception:
                pass
        raise RuntimeError("AI 返回的局部修改结果不是合法 JSON")

    @classmethod
    def parse_script_tune_payload(cls, text):
        data = cls.extract_json(text)
        if not isinstance(data, dict):
            raise RuntimeError("AI 返回格式异常：顶层必须是 JSON 对象")
        summary = str(data.get("summary", "") or "").strip()
        operations = data.get("operations", [])
        if isinstance(operations, list) is False or len(operations) <= 0:
            raise RuntimeError("AI 未返回可用的局部修改指令")
        normalized = []
        valid_actions = {"replace", "insert_before", "insert_after"}
        for item in operations:
            if isinstance(item, dict) is False:
                continue
            action = str(item.get("action", "") or "").strip()
            target = str(item.get("target", "") or "")
            content = str(item.get("content", "") or "")
            reason = str(item.get("reason", "") or "").strip()
            if action not in valid_actions:
                raise RuntimeError("AI 返回了不支持的修改动作: %s" % action)
            if not target:
                raise RuntimeError("AI 返回的修改指令缺少 target")
            normalized.append({
                "action": action,
                "target": target,
                "content": content,
                "reason": reason,
            })
        if len(normalized) <= 0:
            raise RuntimeError("AI 未返回可执行的局部修改指令")
        return {"summary": summary, "operations": normalized}

    @staticmethod
    def apply_script_tune_operations(script_text, operations):
        script_text = script_text or ""
        updated_text = script_text
        applied = []
        for index, item in enumerate(operations):
            action = item.get("action", "")
            target = item.get("target", "")
            content = item.get("content", "")
            reason = item.get("reason", "")
            match_count = updated_text.count(target)
            if match_count <= 0:
                raise RuntimeError("第 %d 条局部修改未找到目标片段，请重新描述问题后再试。" % (index + 1))
            if match_count > 1:
                raise RuntimeError("第 %d 条局部修改匹配到多个位置，定位不唯一，请让 AI 提供更精确的 target。" % (index + 1))
            if action == "replace":
                updated_text = updated_text.replace(target, content, 1)
            elif action == "insert_before":
                updated_text = updated_text.replace(target, content + target, 1)
            elif action == "insert_after":
                updated_text = updated_text.replace(target, target + content, 1)
            else:
                raise RuntimeError("不支持的局部修改动作: %s" % action)
            applied.append({
                "action": action,
                "target": target,
                "content": content,
                "reason": reason,
            })
        return updated_text, applied


class AiWorker(QThread):
    success = pyqtSignal(str)
    error = pyqtSignal(str)
    chunk = pyqtSignal(str)

    def __init__(self, handler, *args, **kwargs):
        super().__init__()
        self.handler = handler
        self.args = args
        self.kwargs = kwargs
        self.stream_handler = kwargs.pop("stream_handler", None)

    def run(self):
        try:
            if self.stream_handler:
                result = self.stream_handler(*self.args, on_chunk=self.chunk.emit, **self.kwargs)
            else:
                result = self.handler(*self.args, **self.kwargs)
            self.success.emit(result)
        except Exception as error:
            self.error.emit(str(error))


class FileDownloadWorker(QThread):
    CHUNK_SIZE = 64 * 1024

    progress = pyqtSignal(int, int)
    status = pyqtSignal(str)
    success = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, url, target_path, parent=None):
        super().__init__(parent)
        self.url = url
        self.target_path = target_path
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def ensureNotCancelled(self):
        if self._cancelled:
            raise RuntimeError("cancelled")

    def copyStream(self, source, target, total=0, emit_progress=False):
        copied = 0
        while True:
            self.ensureNotCancelled()
            chunk = source.read(self.CHUNK_SIZE)
            if not chunk:
                break
            target.write(chunk)
            copied += len(chunk)
            if emit_progress:
                self.progress.emit(copied, total)
        return copied

    def run(self):
        binary_temp_path = None
        archive_temp_path = None
        try:
            self.status.emit("connecting")
            request = urllib.request.Request(self.url, headers={"User-Agent": "fridaUiTools/1.0"})
            with urllib.request.urlopen(request, timeout=120) as response:
                self.ensureNotCancelled()
                total = int(response.headers.get("Content-Length") or 0)
                with tempfile.NamedTemporaryFile(delete=False, suffix=".xz") as temp_handle:
                    archive_temp_path = temp_handle.name
                    self.copyStream(response, temp_handle, total=total, emit_progress=True)
            self.status.emit("extracting")
            target_dir = os.path.dirname(self.target_path)
            if target_dir:
                os.makedirs(target_dir, exist_ok=True)
            with lzma.open(archive_temp_path, "rb") as source, tempfile.NamedTemporaryFile(delete=False, dir=target_dir or None) as output:
                binary_temp_path = output.name
                self.copyStream(source, output)
            self.ensureNotCancelled()
            if os.path.getsize(binary_temp_path) <= 0:
                raise RuntimeError("downloaded file is empty after extraction")
            os.replace(binary_temp_path, self.target_path)
            binary_temp_path = None
            self.success.emit(self.target_path)
        except urllib.error.HTTPError as error:
            body = error.read().decode("utf-8", errors="ignore")
            self.error.emit(f"HTTP {error.code} {body}\nURL: {self.url}\nTarget: {self.target_path}")
        except urllib.error.URLError as error:
            self.error.emit(f"{error}\nURL: {self.url}\nTarget: {self.target_path}")
        except lzma.LZMAError as error:
            self.error.emit(f"extract failed: {error}\nURL: {self.url}\nTarget: {self.target_path}")
        except OSError as error:
            self.error.emit(f"save failed: {error}\nURL: {self.url}\nTarget: {self.target_path}")
        except Exception as error:
            self.error.emit(f"unexpected download error: {error}\nURL: {self.url}\nTarget: {self.target_path}")
        finally:
            if binary_temp_path and os.path.exists(binary_temp_path):
                os.remove(binary_temp_path)
            if archive_temp_path and os.path.exists(archive_temp_path):
                os.remove(archive_temp_path)


class AdbPushWorker(QThread):
    progress = pyqtSignal(int, int)
    status = pyqtSignal(str)
    success = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, command_args, remote_path, parent=None):
        super().__init__(parent)
        self.command_args = command_args
        self.remote_path = remote_path

    def run(self):
        try:
            self.status.emit(f"Uploading to {self.remote_path}...")
            process = subprocess.Popen(
                self.command_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            output_lines = []
            percent_re = re.compile(r"(\d+)%")
            if process.stdout is not None:
                for line in process.stdout:
                    text = (line or "").strip()
                    if text:
                        output_lines.append(text)
                        match = percent_re.search(text)
                        if match:
                            percent = max(0, min(100, int(match.group(1))))
                            self.progress.emit(percent, 100)
                        else:
                            self.status.emit(text)
            return_code = process.wait()
            output = "\n".join(output_lines).strip()
            if return_code != 0:
                raise RuntimeError(output or f"adb push failed with code {return_code}")
            self.progress.emit(100, 100)
            self.success.emit(self.remote_path)
        except FileNotFoundError as error:
            self.error.emit(f"adb not found: {error}\nCommand: {' '.join(self.command_args)}\nRemote: {self.remote_path}")
        except OSError as error:
            self.error.emit(f"failed to start adb push: {error}\nCommand: {' '.join(self.command_args)}\nRemote: {self.remote_path}")
        except Exception as error:
            self.error.emit(f"unexpected adb push error: {error}\nCommand: {' '.join(self.command_args)}\nRemote: {self.remote_path}")


class AdbPullWorker(QThread):
    progress = pyqtSignal(int, int)
    status = pyqtSignal(str)
    success = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, command_args, local_path, parent=None):
        super().__init__(parent)
        self.command_args = command_args
        self.local_path = local_path

    def run(self):
        try:
            self.status.emit(f"Downloading to {self.local_path}...")
            process = subprocess.Popen(
                self.command_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            output_lines = []
            percent_re = re.compile(r"(\d+)%")
            if process.stdout is not None:
                for line in process.stdout:
                    text = (line or "").strip()
                    if text:
                        output_lines.append(text)
                        match = percent_re.search(text)
                        if match:
                            percent = max(0, min(100, int(match.group(1))))
                            self.progress.emit(percent, 100)
                        else:
                            self.status.emit(text)
            return_code = process.wait()
            output = "\n".join(output_lines).strip()
            if return_code != 0:
                raise RuntimeError(output or f"adb pull failed with code {return_code}")
            self.progress.emit(100, 100)
            self.success.emit(self.local_path)
        except FileNotFoundError as error:
            self.error.emit(f"adb not found: {error}\nCommand: {' '.join(self.command_args)}\nLocal: {self.local_path}")
        except OSError as error:
            self.error.emit(f"failed to start adb pull: {error}\nCommand: {' '.join(self.command_args)}\nLocal: {self.local_path}")
        except Exception as error:
            self.error.emit(f"unexpected adb pull error: {error}\nCommand: {' '.join(self.command_args)}\nLocal: {self.local_path}")


class CommandWorker(QThread):
    started = pyqtSignal(str)
    output = pyqtSignal(str)
    success = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, command_args, parent=None):
        super().__init__(parent)
        self.command_args = command_args

    def commandText(self):
        return " ".join(self.command_args)

    def collectOutput(self, process):
        output_lines = []
        if process.stdout is None:
            return output_lines
        for line in process.stdout:
            text = (line or "").rstrip()
            if not text:
                continue
            output_lines.append(text)
            self.output.emit(text)
        return output_lines

    def run(self):
        command_text = self.commandText()
        try:
            self.started.emit(command_text)
            process = subprocess.Popen(
                self.command_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            output_lines = self.collectOutput(process)
            return_code = process.wait()
            output = "\n".join(output_lines).strip()
            if return_code != 0:
                raise RuntimeError(output or f"command failed with code {return_code}")
            self.success.emit(output)
        except FileNotFoundError as error:
            self.error.emit(f"command not found: {error}\nCommand: {command_text}")
        except OSError as error:
            self.error.emit(f"failed to start command: {error}\nCommand: {command_text}")
        except Exception as error:
            self.error.emit(f"{error}\nCommand: {command_text}")
