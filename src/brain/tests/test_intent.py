from __future__ import annotations

import unittest
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from src.brain.intent import TASK_STATUS_INTENT, parse_task_status_intent


POSITIVE_CASES = (
    "查任务状态",
    "查一下任务状态。",
    "请查一下任务状态！",
    "麻烦帮我看看任务状态",
    "能不能看一下任务队列？",
    "帮我查询当前任务进度",
    "请告诉我任务执行情况。",
    "我想看任务状态",
    "任务现在怎么样了？",
    "查看所有任务的状态",
    "任务队列什么情况？",
    "请汇报任务队列状态",
    "看看任务有没有失败",
    "当前有哪些任务卡住了？",
    "帮我看下队列进展",
    "查查任务完成情况",
)

NEGATIVE_CASES = (
    "",
    "   ",
    "你好",
    "今天天气如何",
    "我不是要查任务状态",
    "不要查任务状态",
    "别查任务队列",
    "“查任务状态”是一个命令",
    "请把“查任务状态”写进文档",
    "如果我要查任务状态，该怎么说？",
    "任务状态很好",
    "刚才已经查过任务状态",
)

W4_NEGATIVE_CASES = (
    "先不查任务状态",
    "不需要查任务状态",
    "暂时不查任务状态",
    "现在不用查看任务进度",
    "目前不必汇报任务情况",
    "先别看任务队列",
    "我看过任务状态了",
    "我已经查看任务进度了",
    "任务状态我看过了",
    "我昨天看了任务状态",
    "上次已经查询过任务队列",
    "我们讨论过查询任务状态",
    "这段日志写着查任务状态",
    "他说查任务状态",
    "她提到查看任务进度",
    "文档里写着请查询任务状态",
    "查任务状态这个功能以后再做",
    "查询任务进度的功能后续再实现",
)


class TaskStatusIntentTests(unittest.TestCase):
    def test_positive_examples_reach_ninety_percent(self) -> None:
        matched = sum(parse_task_status_intent(text).matched for text in POSITIVE_CASES)
        print(
            f"INTENT_METRIC matched={matched} total={len(POSITIVE_CASES)} "
            f"rate={matched / len(POSITIVE_CASES):.2%}"
        )
        self.assertGreaterEqual(matched / len(POSITIVE_CASES), 0.90)

    def test_each_negative_example_stays_silent(self) -> None:
        for text in NEGATIVE_CASES:
            with self.subTest(text=text):
                result = parse_task_status_intent(text)
                self.assertFalse(result.matched)
                self.assertFalse(result.should_interrupt)

    def test_w4_negation_history_and_reported_speech_stay_silent(self) -> None:
        for text in W4_NEGATIVE_CASES:
            with self.subTest(text=text):
                result = parse_task_status_intent(text)
                self.assertFalse(result.matched)
                self.assertFalse(result.should_interrupt)

    def test_match_has_fixed_scope_and_no_external_inference(self) -> None:
        result = parse_task_status_intent("请查一下任务状态")
        self.assertEqual(TASK_STATUS_INTENT, result.intent)
        self.assertEqual("all", result.scope)
        self.assertTrue(result.should_interrupt)


if __name__ == "__main__":
    unittest.main()
