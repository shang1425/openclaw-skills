# 🦞 deepthink v6.0 - 结构化深度思考框架

> 让 AI 的思考过程显式化、结构化、可追踪、可验证

## 🎯 核心功能

deepthink v6.0 是一个完整的结构化深度思考框架，包含三个核心模块：

### 1. 声明提取 (claim_extractor.py)
- 从思考过程中自动提取可验证的声明
- 分类：事实、数据、观点、推论
- 计算置信度和验证优先级

### 2. 搜索验证 (search_verifier.py)
- 通过 web_search 验证声明的真实性
- 收集支持和反对证据
- 调整置信度

### 3. 集成框架 (deepthink_v6.py)
- 端到端处理思考过程
- 生成详细的验证报告
- 支持 JSON 和 Markdown 导出

## 📦 文件结构

```
deepthink/
├── claim_extractor.py          # 声明提取模块
├── search_verifier.py          # 搜索验证模块
├── search_verifier_real.py     # 真实搜索验证器（集成 web_search）
├── deepthink_v6.py             # 主框架
├── deepthink_cli.py            # 命令行工具
├── test_deepthink.py           # 测试文件
└── README.md                   # 本文件
```

## 🚀 快速开始

### 1. 基础使用（模拟搜索）

```bash
# 从文本文件处理
python deepthink_cli.py --input thinking.txt --format both

# 直接输入文本
python deepthink_cli.py --text "根据研究表明，全球气温上升了1.5度。" --mock
```

### 2. 在 Python 中使用

```python
from deepthink_v6 import DeepThinkV6

# 初始化引擎
engine = DeepThinkV6()

# 处理文本
result = engine.process("研究表明全球气温上升了1.5度")

# 获取验证报告
print(result["report_markdown"])

# 导出 JSON
engine.export_json(result, "report.json")
```

### 3. 真实搜索验证

```python
from search_verifier_real import SearchVerifierReal

verifier = SearchVerifierReal()
claims = [{"text": "OpenAI成立于2015年", "claim_type": "fact"}]
result = verifier.verify_claims(claims)
```

## 📊 示例输出

```json
{
  "summary": {
    "total_claims": 3,
    "verified": 1,
    "refuted": 0,
    "uncertain": 2,
    "avg_confidence": 0.72
  },
  "claims": [
    {
      "text": "全球气温上升了1.5度",
      "claim_type": "fact",
      "confidence": 0.85,
      "verification_status": "verified",
      "evidence": [...]
    }
  ]
}
```

## 🧪 测试

```bash
python test_deepthink.py
```

所有测试通过：13/13 ✅

## 📝 版本历史

- **v6.0** (2026-03-31) - 搜索验证模块，声明提取，验证报告
- **v5.0** - 多Agent协作推理（分析师、魔鬼代言人、实用主义者、远见者）
- **v4.1** - 置信度数值评分 (S/A/B/C/D/F)
- **v4.0** - 12模块完整框架
- **v3.0** - ASCII 决策树可视化
- **v2.0** - Harness 三智能体架构
- **v1.0** - 初始版本

## 📜 许可证

MIT License

## 🔗 相关项目

- **taskflow** - 任务拆解与追踪框架
- **flash-thought** - 灵感捕捉与周期回顾

---

🦞 by 雪碧 | https://github.com/shang1425/openclaw-skills
