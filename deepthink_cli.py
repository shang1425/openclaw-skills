#!/usr/bin/env python3
"""
deepthink_cli.py - deepthink v6.0 命令行工具

使用方式:
  python deepthink_cli.py --input thinking.txt --output report.json
  python deepthink_cli.py --text "思考过程文本" --format markdown
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

from deepthink_v6 import DeepthinkV6


async def main():
    parser = argparse.ArgumentParser(
        description="deepthink v6.0 - 结构化深度思考框架"
    )

    # 输入选项
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--input", "-i", type=str, help="输入文件路径（包含思考过程）"
    )
    input_group.add_argument("--text", "-t", type=str, help="直接输入思考过程文本")

    # 输出选项
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="deepthink_report",
        help="输出文件路径（不含扩展名，默认: deepthink_report）",
    )

    parser.add_argument(
        "--format",
        "-f",
        choices=["json", "markdown", "both"],
        default="both",
        help="输出格式（默认: both）",
    )

    parser.add_argument(
        "--mock",
        action="store_true",
        help="使用模拟搜索（用于测试）",
    )

    args = parser.parse_args()

    # 读取输入
    if args.input:
        try:
            with open(args.input, "r", encoding="utf-8") as f:
                thinking_text = f.read()
        except FileNotFoundError:
            print(f"❌ 错误: 文件不存在 {args.input}")
            sys.exit(1)
    else:
        thinking_text = args.text

    if not thinking_text.strip():
        print("❌ 错误: 思考过程文本为空")
        sys.exit(1)

    # 处理
    print("🚀 开始处理思考过程...\n")

    deepthink = DeepthinkV6(use_mock_search=args.mock)
    report = await deepthink.process(thinking_text)

    # 输出统计
    print(report.summary)

    # 导出报告
    output_base = Path(args.output)

    if args.format in ["json", "both"]:
        json_path = output_base.with_suffix(".json")
        deepthink.export_json(report, str(json_path))
        print(f"\n✅ JSON 报告已导出: {json_path}")

    if args.format in ["markdown", "both"]:
        md_path = output_base.with_suffix(".md")
        deepthink.export_markdown(report, str(md_path))
        print(f"✅ Markdown 报告已导出: {md_path}")


if __name__ == "__main__":
    asyncio.run(main())
