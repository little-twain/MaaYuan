# MaaYuan 原生运行时与 Yuan 国际服架构调研

日期：2026-09-07

## 前提修正

本调研基于两个明确约束：

1. 目标运行时不使用 Python。Rust 或 Go 只作为官方 Maa 运行时的调用方和扩展进程，不维护 Python Agent。
2. “国际服”指 **Yuan / 代号鸢**，当前至少包含港服与台服；不是泛化的 EN/JP/KR 多语言项目，也不是如鸢国服。

因此，先前“先优化 Python、再评估 Rust”的路线不再适用。Python 只能作为迁移期的遗留兼容层，不能进入目标架构。

## 结论

### 不应使用原始 MaaAssistantArknights 核心

[MaaAssistantArknights](https://github.com/MaaAssistantArknights/MaaAssistantArknights) 虽然提供 C / Go / Rust 等调用接口，但它的任务 API 和资源协议是明日方舟专用的。其 `StartUp`、`Fight`、`Recruit`、基建、肉鸽等任务类型与明日方舟资源深度耦合，客户端枚举也是 `Official`、`Bilibili`、`txwy`、`YoStarEN`、`YoStarJP`、`YoStarKR`。

它不能作为代号鸢的业务运行时。强行复用只会得到一个不可维护的 fork。

### 应使用官方上游 MaaFramework

MaaYuan 的正确基础是 [MaaFramework](https://github.com/MaaXYZ/MaaFramework) 官方上游发行版：

- 官方 C ABI 承担截图、OCR、模板匹配、Pipeline 执行和控制器调度。
- 官方 Project Interface 描述资源、任务和 Agent。
- Rust / Go 二进制只实现薄的业务编排与少量自定义 Recognition / Action。
- 不 fork MaaFramework；版本、ABI 和安全更新必须跟随上游。

换句话说，目标不是“用 Rust / Go 重写 Maa”，而是：

```text
官方 MaaFramework 原生库
        +
Rust/Go 宿主或 AgentServer
        +
Yuan / 如鸢资源与任务声明
```

## Rust 与 Go 选择

### Rust：目标首选

[官方 Rust Binding](https://github.com/MaaXYZ/maa-framework-rs) 当前覆盖：

- Tasker
- Resource
- Controller
- AgentClient
- AgentServer
- 自定义 Recognition
- 自定义 Action
- 静态 / 动态链接

本次使用 MaaFramework `v5.13.0-beta.6` SDK 验证：

```bash
cargo check --workspace
```

结果通过。绑定仓库也包含多进程 AgentServer 集成测试。

选择 Rust 的理由：

- 官方绑定功能完整；
- 类型和错误处理适合长期单人维护；
- Agent 二进制启动快、内存占用低；
- 数据结构可由 serde 强类型建模；
- 不需要 Python 解释器、pip、pandas 或 Python OpenCV 包；
- 更容易在 CI 中做格式化、clippy、测试和二进制矩阵。

主要代价：

- 需要维护 MaaFramework SDK 与绑定版本的严格配对；
- Windows / Linux / macOS 的动态库复制和打包更复杂；
- 图像与文本处理开发效率低于 Python。

### Go：保留为备选，不作为当前主线

[官方 Go Binding](https://github.com/MaaXYZ/maa-framework-go) 具备 AgentServer API，并使用 purego 避免 cgo。但当前版本仍是 `v4.0.0-beta.18`。

实测结论：

- AgentServer 示例可编译；
- MaaFW `5.0.5` 缺少新 ABI 符号，无法直接配合当前绑定；
- 使用 `5.13.0-beta.6` 后基础库可加载，但完整测试仍存在失败项；
- 其稳定性和错误边界不如 Rust Binding。

Go 的优势是交叉编译和工具链简单，但在本项目里并不能消除 MaaFramework 原生库依赖，且绑定仍处于 beta。因此：

```text
主线：Rust
备选：Go，等待官方 binding 稳定后再做等价 PoC
```

## 目标架构

```text
bin/maayuan-agent(.exe)       # Rust AgentServer
interface.json                # Project Interface V2 入口
tasks/*.json                  # 按功能拆分的任务与选项
i18n/*.json                   # 界面文案，不代表游戏 UI 语言
resource/game/common/         # 与版本和语言无关的流程、模板
resource/lang/zh_hans/        # 简中游戏 UI 差异
resource/lang/zh_hant/        # 繁中游戏 UI 差异
resource/dist/ruyuan-cn/      # 如鸢国服包名与渠道差异
resource/dist/yuan-hk/        # 代号鸢港服包名与渠道差异
resource/dist/yuan-tw/        # 代号鸢台服包名与渠道差异
data/*.json                   # 构建期生成的强类型业务数据
tools/                        # schema、资源、数据、打包校验
```

### Agent 边界

目标 interface 中的 Agent 配置应为：

```json
{
  "agent": {
    "child_exec": "{PROJECT_DIR}/bin/maayuan-agent",
    "child_args": []
  }
}
```

Project Interface V2 会在启动 Agent 时注入：

- `PI_CLIENT_NAME`
- `PI_CLIENT_LANGUAGE`
- `PI_CLIENT_MAAFW_VERSION`
- `PI_CONTROLLER`
- `PI_RESOURCE`

Rust Agent 应解析 `PI_RESOURCE`，而不是让用户手动选择游戏版本。这样可以保证：

```text
资源包选择 = 游戏发行版本 + 游戏 UI 语言
```

### 官方 GUI

初期不重写 GUI。继续使用官方 MFAAvalonia / MXU 加载 Project Interface V2。这样可以把重构范围限制在：

```text
资源结构 + 原生 Agent + CI / 发布
```

等原生架构稳定后，再评估是否需要独立 CLI 或 GUI。

## Yuan 国际服资源模型

当前仓库事实如下。

### 简中资源

```text
assets/resource/base
```

同时服务：

- 如鸢国服；
- 代号鸢港服，且现有文档说明港服可使用简中界面。

港包名：

```text
com.qookkagames.codekite.gw.hk
```

### 繁中资源

```text
assets/resource/zh_tw
```

主要服务代号鸢台服。

台包名：

```text
com.sialiagames.codekite.gw.tw
```

### 目标组合

Project Interface V2 的 resource path 应按顺序叠加：

| 目标 | 资源组合 |
| --- | --- |
| 如鸢国服 | `game/common` + `lang/zh_hans` + `dist/ruyuan-cn` |
| 代号鸢港服 | `game/common` + `lang/zh_hans` + `dist/yuan-hk` |
| 代号鸢台服 | `game/common` + `lang/zh_hant` + `dist/yuan-tw` |

后加载资源覆盖先前资源。这样：

- 不再复制整套 `base` / `zh_tw`；
- 包名和渠道差异独立维护；
- OCR 文案按游戏 UI 语言维护；
- 任务可用性按发行版本声明。

当前统计显示，`base` 与 `zh_tw` 有 316 个内容完全一致的重复文件，约 4.97 MB。这部分应由差异层消除。

### 能力矩阵

现有文档已提示：

- 心纸营建偏港服限定；
- 地宫主要测试如鸢国服；
- 部分通用导航明确兼容国服与港服简中。

重构后必须把这些经验显式化为 `task.resource` 过滤条件，而不是写在文档里靠用户猜测。

## 数据处理

目标运行时禁止读取 XLSX。

当前 `agent/*.xlsx` 应改为构建期输入：

```text
sources/*.xlsx
        |
        | tools/convert-data
        v
data/*.json
```

Rust Agent 使用 serde 加载 JSON：

- 题库；
- 大富翁事件；
- 派遣策略；
- 文本规范化映射；
- OCR 匹配数据。

这样可以移除：

```text
pandas
openpyxl
```

少量颜色识别应在 Rust Agent 中实现，或优先改写为 MaaFramework Pipeline 内建 Recognition，避免引入 Python OpenCV。

## CI 与发布策略

### 当前报错与修复

本次 fork CI 的 `install` workflow 在 Windows 两个架构失败：

```text
ModuleNotFoundError: No module named 'install_common'
```

原因是 Windows embedded Python 通过 `python._pth` 使用隔离 `sys.path`，没有自动加入脚本目录。

已在 `install4release.py` 中显式插入项目根目录。修复后推送的 `check` 与 `install` workflow 均已通过。

### 迁移期 CI

在 Python Agent 删除前，应同时保留：

```text
legacy Python package artifact
native Rust agent artifact
```

Native job 应包含：

```bash
cargo fmt --check
cargo clippy -- -D warnings
cargo test
cargo build --release
```

### 目标 CI

Native 达到功能对等后删除：

- `setup_embed_python.py`
- Python agent 打包步骤；
- `requirements.txt` 运行时依赖；
- pip mirror 探测；
- Python 嵌入式包下载。

目标矩阵：

| 平台 | 架构 |
| --- | --- |
| Windows | x86_64, aarch64 |
| Linux | x86_64, aarch64 |
| macOS | x86_64, aarch64 |

每个平台必须校验：

1. 官方 MaaFramework 版本；
2. Rust binding ABI 版本；
3. Rust Agent 是否能启动 AgentServer；
4. Project Interface V2 schema；
5. Pipeline schema；
6. Yuan 三种资源组合是否可加载；
7. 截图回放是否通过。

## 实施顺序

1. **版本配对**：固定官方 MaaFramework 与 Rust Binding 的兼容矩阵，先支持一个稳定版本。
2. **Rust Agent PoC**：实现 AgentServer，迁移一个 Recognition 和一个 Action。
3. **数据构建**：XLSX 转 JSON，定义 serde 类型，移除运行时 Excel。
4. **Interface V2**：拆分任务文件，声明 controller / resource / task.resource。
5. **Yuan 分层**：建立 `common + lang + dist` 三层资源，消除重复文件。
6. **截图回放**：为港服简中、台服繁中、如鸢国服建立固定场景测试。
7. **并行发布**：同时打包 legacy 与 native，标记 native 为 experimental。
8. **切换默认**：native 通过能力矩阵和回放测试后删除 Python。

## 决策

在“目标绝不用 Python”的前提下，推荐：

```text
官方 MaaFramework + Rust AgentServer + Project Interface V2
```

Go 不排除，但只应在官方 Go Binding 稳定后作为备选实验，不作为当前重构主线。
