# ADR 0001：采用官方 MaaFramework 与 Rust 原生 Agent

日期：2026-09-07

状态：Proposed

## 背景

MaaYuan 当前使用 MaaFramework Python Binding 和 Python AgentServer。维护者已明确：

- 目标运行时不能依赖 Python；
- 可选实现语言限定为 Rust 或 Go；
- 国际服目标是 Yuan / 代号鸢，而非泛化的全球多语言矩阵。

## 决策

1. 不使用 MaaAssistantArknights 原始核心；其任务 API 与明日方舟资源强耦合。
2. 使用官方上游 MaaFramework 作为唯一识别、Pipeline 和控制器运行时。
3. 以官方 Rust Binding 实现 MaaYuan AgentServer。
4. Go Binding 保持关注，但不作为当前主线。
5. Python Agent 仅作为迁移期兼容产物，功能对等后删除。
6. 使用 Project Interface V2 描述如鸢国服、代号鸢港服、代号鸢台服的资源组合。
7. XLSX 只能作为源数据，构建期转换为 JSON，运行时由 Rust 强类型加载。

## 后果

### 正面

- 删除 Python、pip、pandas、openpyxl 和 Python OpenCV 运行时依赖；
- 降低长期解释器与依赖维护成本；
- Agent 启动、内存和分发路径更清晰；
- Rust 类型系统能够约束任务数据、资源清单和 Agent 参数；
- Yuan 港服 / 台服差异可以按资源层组合，而不是复制完整资源目录。

### 负面

- 需要维护 MaaFramework SDK 与 Rust Binding 的 ABI 配对；
- 六平台构建与动态库复制比 Python 打包更复杂；
- 图像、文本和 Excel 处理的开发成本高于 Python；
- 迁移期需要同时验证 legacy 与 native。

## 验证门槛

删除 Python 前必须满足：

1. Rust AgentServer 能由官方 GUI 启动；
2. 至少一个自定义 Recognition 和一个 Action 功能对等；
3. `game/common + lang + dist` 三类资源组合均可加载；
4. 港服简中、台服繁中、如鸢国服截图回放通过；
5. Project Interface、Pipeline 和数据 schema 在 CI 中全部通过；
6. 全平台 release artifact 不包含 Python 运行时。
