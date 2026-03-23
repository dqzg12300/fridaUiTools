import json
import re
import urllib.error
import urllib.request

from PyQt5.QtCore import QThread, pyqtSignal

from utils.IniUtil import IniConfig


AI_SECTION = "ai"
AI_REQUIRED_FIELDS = {
    "apikey": "API Key",
    "host": "Host",
    "model": "模型",
}

HOOK_SYSTEM_PROMPT = """你是一名资深 Frida/Android 逆向工程师。
你要为 fridaUiTools 生成可直接保存到 custom 模块中的自定义 hook 脚本。
请严格遵守以下规则：
1. 只输出 JavaScript 代码，不要输出 Markdown 代码块，不要解释说明。
2. 代码必须兼容 Frida Java.perform 风格，尽量保证异常安全。
3. 必须包含清晰的日志输出，方便在 fridaUiTools 输出日志中查看。
4. 如果需要导出主动调用函数，请使用全局对象 call_funs，例如：call_funs.demo = function(args) { ... }。
5. 如果需求不明确，请给出一个安全、通用、可运行的最小实现，并在日志中标记 TODO。
6. 自定义模块保存的脚本会被工具直接拼接执行，因此不要再次包裹额外的模块系统，不要输出 import/require。
7. 尽量使用如下日志格式：console.log('[custom] ...')。
"""

HOOK_USER_TEMPLATE = """请根据下面信息生成 fridaUiTools custom 模块脚本：
脚本别名：{name}
备注：{remark}
用户需求：
{requirement}

请优先按以下结构组织：
- 先定义需要的辅助函数
- 再在 Java.perform(function() {{ ... }}) 中完成 hook
- 如需主动调用函数，定义 call_funs.xxx = function(...) {{ ... }}
- 日志统一以 [custom] 前缀输出
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

    def missing_fields(self):
        config = self.get_config()
        return [label for key, label in AI_REQUIRED_FIELDS.items() if not config.get(key)]

    def is_available(self):
        return len(self.missing_fields()) == 0

    def missing_message(self):
        missing = self.missing_fields()
        if not missing:
            return "AI 配置可用"
        return "未配置 " + " / ".join(missing) + "，请先在设置中完成 AI 配置"

    def _build_endpoint(self, host):
        host = host.rstrip("/")
        if host.endswith("/chat/completions"):
            return host
        if host.endswith("/v1"):
            return host + "/chat/completions"
        return host + "/v1/chat/completions"

    def chat(self, messages, temperature=0.2, timeout=120):
        config = self.get_config()
        missing = self.missing_fields()
        if missing:
            raise ValueError(self.missing_message())
        payload = json.dumps({
            "model": config["model"],
            "messages": messages,
            "temperature": temperature,
        }).encode("utf-8")
        request = urllib.request.Request(
            self._build_endpoint(config["host"]),
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {config['apikey']}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            body = error.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"AI 请求失败: HTTP {error.code} {body}")
        except urllib.error.URLError as error:
            raise RuntimeError(f"AI 连接失败: {error}")
        except Exception as error:
            raise RuntimeError(f"AI 请求异常: {error}")

        try:
            content = data["choices"][0]["message"]["content"]
        except Exception:
            raise RuntimeError(f"AI 返回格式异常: {data}")
        return content.strip()

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
        return self.extract_code(result)

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

    @staticmethod
    def extract_code(text):
        text = (text or "").strip()
        if text.startswith("```"):
            match = re.search(r"```(?:javascript|js)?\s*(.*?)```", text, re.S)
            if match:
                return match.group(1).strip()
        return text


class AiWorker(QThread):
    success = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, handler, *args, **kwargs):
        super().__init__()
        self.handler = handler
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            result = self.handler(*self.args, **self.kwargs)
            self.success.emit(result)
        except Exception as error:
            self.error.emit(str(error))
