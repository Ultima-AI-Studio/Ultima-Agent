"""监听进程的失败降级必须是"丢一轮"，不是"整体下线"。

本轮真实事故：一轮语音处理超时（我被批量 /ask 请求堵在串行锁后面），
live.py 在 processing 超时时直接 raise 出主循环，进程以 state=error 退出，
用户表现为"唤起不了"，必须手动重启。这里用源码级断言锁住修复方向。
"""

import re
from pathlib import Path

LIVE = Path(__file__).with_name("live.py")


def test_turn_timeout_does_not_raise_out_of_loop():
    src = LIVE.read_text(encoding="utf-8")
    assert not re.search(r"raise\s+TimeoutError\(\s*'Voice turn timed out'", src), (
        "单轮超时不得 raise 出主循环：那会让整个监听进程下线"
    )


def test_turn_timeout_returns_to_listen():
    src = LIVE.read_text(encoding="utf-8")
    assert "turn_timeout" in src, "超时需发布 turn_timeout 事件供状态/日志追踪"
    timeout_block = src.split("turn_timeout", 1)[1][:400]
    assert "self.listen()" in timeout_block, "超时后必须回到 listen，而不是退出"
    assert "self.turn_id=''" in timeout_block or 'self.turn_id = ""' in timeout_block, (
        "超时后必须作废 turn_id，让迟到的 worker 结果被丢弃"
    )
