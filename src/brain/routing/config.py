"""Configuration for the local reply-constraint routing stack."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RoutingConfig:
    embedding_model: str = "nomic-embed-text"
    ollama_embed_url: str = "http://localhost:11434/api/embed"
    allow_similarity_threshold: float = 0.82
    deny_similarity_threshold: float = 0.82
    banned_similarity_threshold: float = 0.84
    similarity_margin: float = 0.04
    low_asr_confidence: float = 0.55
    deny_reply: str = "这个请求不在我能可靠处理的范围内。"
    abstain_reply: str = "我没听清，请再说一遍。"
    verifier_fallback_reply: str = "收到。"


ALLOW_PATTERNS = (
    r"(?:天气|气温|温度|下雨|下雪|晴天|阴天|天气预报)",
    r"(?:几点|时间|日期|星期几|几号)",
    r"(?:日程|提醒|安排|计划|待办)",
    r"(?:任务|队列|工单|进度|状态|优先级|插队)",
    r"(?:插到|插在|挪到|排到|调整一下|调整任务|改优先级|改成|设为)",
    r"(?:设置|偏好|名字|唤醒词|称呼|声音)",
    r"(?:设备|系统状态|电脑|音量|网络|电量)",
    r"(?:搜索|查找|查询|查一下|看一下|告诉我|解释|介绍)",
    r"(?:你好|您好|在吗|谢谢|再见|聊聊|聊天|笑话|你是谁|你叫什么)",
    r"(?:是什么|为什么|怎么|如何|谁是|哪里|哪个|哪些|多少)",
)

DENY_PATTERNS = (
    r"(?:忽略|无视|绕过).{0,10}(?:规则|指令|提示词|限制)",
    r"(?:系统提示词|system\s*prompt|越狱|jailbreak|解除限制)",
    r"(?:编造|捏造|伪造|虚构).{0,10}(?:天气|答案|事实|来源|数据|结果|新闻)",
    r"(?:照着|原样|复述|引用).{0,10}(?:不可信|来源不明|错误内容|假消息)",
    r"(?:请|记得|欢迎|别忘了).{0,6}(?:关注|点赞|订阅).{0,6}(?:我|我们|频道|账号)?",
    r"(?:制作炸弹|伤害他人|杀人方法|入侵账号|诈骗话术)",
)

ASR_CORRECTION_MARKERS = (
    "[ASR_CORRECTED]",
    "<asr-corrected>",
    "ASR修正",
    "识别待修正",
)

UNTRUSTED_ASR_FRAGMENTS = (
    "水量天听",
    "水平听听清",
    "水平听",
    "明天上海的这",
)

ALLOW_PROTOTYPES = (
    "查询今天或明天的天气和气温",
    "询问当前时间日期星期",
    "查看日程提醒和安排",
    "查询任务队列进度状态",
    "调整设置偏好或唤醒词",
    "控制本地设备或查看系统状态",
    "搜索资料回答知识问题",
    "日常寒暄聊天",
)

DENY_PROTOTYPES = (
    "忽略规则并编造一个答案",
    "复述来源不明的错误内容",
    "输出关注点赞订阅营销话术",
    "执行危险违法或伤害他人的请求",
)

DEFAULT_ROUTING_CONFIG = RoutingConfig()
