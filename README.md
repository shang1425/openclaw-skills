# deepthink v6.0 - 结构化深度思考框架

## 🎯 核心功能

deepthink v6.0 是一个完整的结构化深度思考框架，包含三个核心模块：

1. **声明提取** (claim_extractor.py)
   - 从思考过程中自动提取可验证的声明
   - 分类：事实、数据、观点、推论
   - 计算置信度和验证优先级

2. **搜索验证** (search_verifier.py)
   - 通过 web_search 验证声明的真实性
   - 收集支持和反对证据
   - 调整置信度

3. **集成框架** (deepthink_v6.py)
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
import asyncio
from deepthink_v6 import DeepthinkV6

async def main():
    deepthink = DeepthinkV6(use_mock_search=True)
    
    thinking_text = """
    根据最新研究表明，全球气温在过去十年上升了1.5度。
    这意味着气候变化正在加速。
    """
    
    report = await deepthink.process(thinking_text)
    print(report.summary)
    
    # 导出报告
    deepthink.export_json(report, "report.json")
    deepthink.export_markdown(report, "report.md")

asyncio.run(main())
```

### 3. 集成 OpenClaw web_search

```python
from search_verifier_real import DeepthinkV6WithRealSearch

async def search_with_openclaw(query: str):
    # 这里调用 OpenClaw 的 web_search 工具
    # 返回搜索结果列表
    pass

deepthink = DeepthinkV6WithRealSearch(search_function=search_with_openclaw)
result = await deepthink.process(thinking_text)
```

## 📊 输出示例

### JSON 报告

```json
{
  "timestamp": "2026-03-31T09:50:00",
  "total_claims": 5,
  "verified_claims": 3,
  "partially_verified_claims": 1,
  "unverifiable_claims": 1,
  "refuted_claims": 0,
  "claims": [
    {
      "text": "全球气温在过去十年上升了1.5度",
      "type": "data",
      "confidence": 0.7,
      "needs_verification": true
    }
  ],
  "verification_results": [
    {
      "claim": "全球气温在过去十年上升了1.5度",
      "status": "verified",
      "confidence_before": 0.7,
      "confidence_after": 0.84,
      "supporting_evidence": [...],
      "opposing_evidence": []
    }
  ]
}
```

### Markdown 报告

```markdown
# deepthink v6.0 验证报告

## 📊 统计概览

| 指标 | 数量 | 比例 |
|------|------|------|
| 总声明数 | 5 | 100% |
| ✅ 已验证 | 3 | 60% |
| ⚠️ 部分验证 | 1 | 20% |
| ❓ 无法验证 | 1 | 20% |
| ❌ 已反驳 | 0 | 0% |

## 🔍 详细验证结果

### 1. 全球气温在过去十年上升了1.5度

**验证状态**: verified
**置信度变化**: 0.70 → 0.84
...
```

## 🔧 核心类和方法

### ClaimExtractor

```python
extractor = ClaimExtractor()

# 提取声明
claims = extractor.extract(text)

# 按置信度过滤
high_confidence = extractor.filter_by_confidence(claims, min_confidence=0.7)

# 按类型过滤
facts = extractor.filter_by_type(claims, ClaimType.FACT)

# 获取验证队列
queue = extractor.get_verification_queue(claims)
```

### SearchVerifier

```python
verifier = SearchVerifier(use_mock=False)

# 验证单个声明
result = await verifier.verify(claim)

# 结果包含：
# - status: 验证状态
# - confidence_before/after: 置信度变化
# - supporting_evidence: 支持证据
# - opposing_evidence: 反对证据
```

### DeepthinkV6

```python
deepthink = DeepthinkV6(use_mock_search=True)

# 处理思考过程
report = await deepthink.process(thinking_text)

# 导出报告
deepthink.export_json(report, "report.json")
deepthink.export_markdown(report, "report.md")
```

## 📈 验证状态说明

| 状态 | 说明 | 置信度调整 |
|------|------|----------|
| ✅ VERIFIED | 已验证，有充分支持证据 | ×1.2 |
| ⚠️ PARTIALLY_VERIFIED | 部分验证，有一定支持证据 | ×(1.0 + 支持权重) |
| ❓ UNVERIFIABLE | 无法验证，缺乏相关信息 | 不变 |
| ❌ REFUTED | 已反驳，有反对证据 | ×0.3 |

## 🎓 声明类型说明

| 类型 | 说明 | 示例 | 默认置信度 |
|------|------|------|----------|
| FACT | 客观事实 | "地球是圆的" | 0.7 |
| DATA | 数据/统计 | "2023年增长5%" | 0.8 |
| OPINION | 观点/判断 | "我认为这很重要" | 0.4 |
| INFERENCE | 推论/结论 | "因此可以推断..." | 0.6 |

## 🔍 搜索验证流程

1. **查询生成**
   - 直接查询声明文本
   - 根据类型生成特定查询
   - 最多 3 个查询

2. **搜索执行**
   - 调用 web_search 工具
   - 获取搜索结果
   - 缓存结果避免重复查询

3. **结果分析**
   - 计算相关度
   - 评估来源可信度
   - 判断支持/反对

4. **状态确定**
   - 比较支持和反对证据权重
   - 确定验证状态
   - 调整置信度

## 🛠️ 开发计划

### v6.0 (当前)
- ✅ 声明提取模块
- ✅ 搜索验证模块
- ✅ 集成框架
- ✅ CLI 工具
- 🔄 集成 web_search

### v6.1 (计划)
- NLP 增强（更精准的声明提取）
- LLM 集成（更智能的验证判断）
- 多语言支持
- 缓存优化

### v7.0 (计划)
- 实时验证流
- 证据链追踪
- 可视化报告
- API 服务

## 📝 测试

运行测试：

```bash
python claim_extractor.py      # 测试声明提取
python search_verifier.py      # 测试搜索验证
python deepthink_v6.py         # 测试完整流程
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

---

**作者**: 雪碧 🦞  
**最后更新**: 2026-03-31
