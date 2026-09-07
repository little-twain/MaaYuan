# MaaYuan 技术栈与架构调研

日期：2026-09-07

## 结论

不建议立即把整个 MaaYuan 重写为 Rust 或 Go。MaaFramework 的截图、OCR、模板匹配、控制器调度和 Pipeline 执行核心本身是 C++ 原生实现；当前 Python Agent 只有约 1.7k 行，主要承担少量自定义动作、识别和数据表匹配。直接换语言不会加速识别主路径，反而会引入新的构建、绑定和发布风险。

更有效的重构路径是：

1. 先做架构中立重构：升级 Project Interface V2、拆分巨型 `interface.json`、引入分层资源包和界面 i18n。
2. 把 Excel 运行时解析改为构建期生成的 JSON，移除 `pandas` / `openpyxl`，并延迟或替换 Python `opencv-python` 依赖。
3. 为自定义热点逻辑建立可复现 benchmark 和截图回放测试。
4. 用 Rust 做一个独立 Agent PoC，验证启动时间、内存、包体和维护成本后，再决定是否替换 Python Agent。
5. Go 绑定目前仍是 beta，适合观察，不建议作为核心重写首选。

## 参考项目

### MAA

[MaaAssistantArknights](https://github.com/MaaAssistantArknights/MaaAssistantArknights) 是原始 MAA 项目，主体为 C++，并使用独立 GUI。它不是 MaaFramework 项目，但提供了两点经验：

- 高性能识别核心由 C++ / OpenCV / PaddleOCR / ONNX Runtime 承担。
- 国际服适配主要依赖资源与文本差异分层；项目文档明确说明，大部分外服适配可以由截图和 JSON 修改完成。

### M9A

[M9A](https://github.com/MAA1999/M9A) 是当前最值得借鉴的 MaaFramework 项目：

- 使用 Project Interface V2 和 `import` 拆分任务文件。
- `resource/base`、`global_jp`、`global_en`、`global_kr`、`tw` 分层加载，后加载资源覆盖前者。
- 界面文本使用 `$key` 加多语言表，并通过校验器保证各语言 key 一致。
- Python 使用 `uv`、Ruff、Pyright strict、pytest、Prettier、schema 与 i18n 校验。
- 提供 AGENTS.md、CONTRIBUTING.md、PR 模板和多类 CI 工作流。

M9A 的国际服资源层非常小，而当前 MaaYuan 的 `base` 与 `zh_tw` 几乎是两套完整拷贝。这是支持国际服前必须消除的结构性阻力。

### MaaNTE

[MaaNTE](https://github.com/1bananachicken/MaaNTE) 的重点是国际化和透明度：

- 维护 `zh_cn`、`zh_tw`、`en_us`、`ja_jp`、`ko_kr` 界面与 Agent 文本。
- 使用定时 workflow 从翻译仓库同步 OCR `expected` 文本，并通过自动 PR 审核变更。
- AGENTS.md 对 Pipeline 命名、坐标、硬延迟、重试、OCR 文本和日志都有明确约束。

这套模式适合 MaaYuan 处理多服 OCR 差异，避免手工复制 Pipeline。

### 官方模板与工具

[MaaPracticeBoilerplate](https://github.com/MaaXYZ/MaaPracticeBoilerplate) 展示了官方推荐结构、schema 校验、资源检查和安装流程。MaaYuan 当前检查链路明显落后于模板，应优先补齐 JSON schema、Pipeline 校验和打包 dry-run。

## Rust / Go 与 MaaFramework 相性

MaaFramework 通过 C ABI 与 AgentServer 支持跨语言扩展。官方文档明确推荐 AgentServer 用于复杂自定义识别和动作，并强调多进程隔离与多语言支持。

### Rust

[官方 Rust Binding](https://github.com/MaaXYZ/maa-framework-rs) 当前发布 `v1.23.0`，覆盖 Tasker、Resource、Controller、AgentClient、AgentServer、自定义识别和动作。它支持静态 / 动态链接、`Result` 错误处理和严格类型。

本次验证：

- 使用 MaaFramework `v5.13.0-beta.6` SDK。
- `cargo check --workspace` 通过。
- 绑定自带多进程 AgentServer 集成测试；单测和部分集成测试可运行，完整测试需要仓库内测试数据子模块。

判断：

- 优点：启动快、内存低、类型安全、二进制发布清晰，官方绑定功能完整。
- 风险：生态案例少；需要维护各平台 SDK 与二进制矩阵；图像、Excel、文本归一化等开发成本高于 Python；当前项目仍使用 MaaFW `5.0.5`，而绑定对应 `5.13.0-beta.6`，升级必须先行。

### Go

[官方 Go Binding](https://github.com/MaaXYZ/maa-framework-go) 当前为 `v4.0.0-beta.18`，无需 cgo，基于 purego，声明支持 AgentClient、AgentServer、自定义识别和动作。

本次验证：

- AgentServer 示例可编译，API 覆盖存在。
- 使用旧 MaaFW `5.0.5` 时无法加载新符号。
- 使用 `5.13.0-beta.6` 后基础包可加载，但本机完整测试仍有若干失败，且该版本仍是 pre-release。

判断：

- 优点：交叉编译和工具链简单，Agent API 明确，无 cgo。
- 风险：beta 状态、运行时仍依赖原生库、错误处理和类型表达弱于 Rust；在 MaaYuan 这种图像和文本逻辑较多的项目中收益不确定。

## 当前仓库量化发现

- `assets/resource/base`：598 个文件，约 10.1 MB。
- `assets/resource/zh_tw`：470 个文件，约 6.5 MB。
- 两边相对路径相同的文件 445 个，其中 316 个内容完全一致。
- 仅 `base` 中与 `zh_tw` 完全重复的内容约 4.97 MB。
- Pipeline 中约 1790 个 OCR 节点、1757 个 OCR `expected` 字符串。
- `interface.json` 集中维护 47 个任务、130 个选项、21 个高级配置，且没有 `interface_version` / `languages`。

这些问题会导致：

- 国际服新增语言时复制成本线性增长。
- OCR 文案修改难以 review 和自动同步。
- 任务与选项冲突难以定位。
- 无法用 M9A 式 i18n 校验保障完整性。

## 建议目标架构

```text
interface.json                 # 只保留元数据、controller/resource/import 声明
tasks/*.json                   # 按功能拆分任务与选项
i18n/{zh_cn,zh_tw,en_us}.json  # 界面文本
resource/base/                 # 与语言无关的模板、流程和模型
resource/zh_tw/                # 仅覆盖繁中差异
resource/global/               # 国际服差异层
agent/                          # 自定义逻辑，先 Python 后评估 Rust
tools/                          # schema/i18n/resource/build 校验
tests/                          # 静态测试 + 截图回放 + Agent 单测
```

### 国际服策略

1. 先确认目标包体和 UI 语言矩阵：简中、繁中、英文、日文、韩文，以及不同发行渠道的窗口 / 包名。
2. 把 OCR `expected` 从 Pipeline 中抽取为可比较的翻译清单，构建时回填或生成覆盖层。
3. 每个 locale 只保存差异 Pipeline、差异图片和 OCR 映射，禁止整目录复制。
4. 为每个 locale 建立固定截图 fixture，至少覆盖启动、主页、日常入口、弹窗和结算画面。
5. 在 interface V2 中声明 resource/controller 兼容矩阵，避免不支持组合被误选。

## 开发透明度方案

- 引入 ADR 目录，记录语言、资源分层、国际服和发布策略决策。
- 使用 M9A 式 `pnpm check` 聚合 schema、i18n、JSON、Python lint、typecheck 和测试。
- PR 必须写明影响的服务器、界面语言、验证截图和资源路径。
- 为 Pipeline 变更生成节点级证据，可结合 MaaLogAnalyzer 或自定义回调导出。
- 维护风险矩阵：每个任务标注 CN / TW / Global 支持状态。

## 实施顺序

1. **基础治理**：补 CONTRIBUTING、PR 模板、schema 校验、Pipeline 校验和 Python 测试。
2. **接口升级**：迁移 Project Interface V2，拆分 `interface.json`，引入 i18n。
3. **资源瘦身**：把 `zh_tw` 改为差异覆盖层，删除 316 个重复文件。
4. **依赖瘦身**：Excel 构建期转 JSON，移除 pandas / openpyxl，处理 cv2 与 zhconv。
5. **国际服 PoC**：选择启动和日常两条链路建立 global 资源层与截图回放。
6. **Rust Agent PoC**：迁移一个自定义识别和一个自定义动作，量化启动、内存、包体和正确性。

只有第 6 步数据明显优于优化后的 Python Agent，才应推进完整 Rust 化。Go 则建议等官方绑定稳定后再评估。
