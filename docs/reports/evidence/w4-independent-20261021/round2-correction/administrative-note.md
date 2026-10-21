# 结果文件裁决口径

最终完整裁决使用 `result-final.json`，结论为通过。

`result.json`保留首次自动化结果，结论为需修正，唯一未通过条件是任务卡字节前缀。独立正文diff随后证实三卡原内容都完整保留，仅追加修复段落；两卡原末尾附近的换行格式变化造成字节前缀不一致。正文追加口径复核通过，未修改任何测试断言。

结果文件处理过程：初检先逐字节保存为 `preliminary-byte-prefix-result.json`；补核后曾暂将完整裁决写到result.json。协调者要求初检原文件保留，故将完整裁决另存为 `result-final.json`，再把result.json从初检原始副本逐字节还原。最终封存时result.json与preliminary-byte-prefix-result.json的SHA256相同。此处理仅发生于本新审查目录，第一轮封存与产品文件没有改动。

`correction_runner.py`对应初次自动检查，`finalize_correction.py`对应正文核对后的完整判定，`preserve_and_seal.py`对应最终文件归位与封存。下一步骤应读取result-final.json与review-report.md。
