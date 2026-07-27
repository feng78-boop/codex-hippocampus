# 🧠 Hippocampus — Brain-Inspired Memory System for Codex

> 不删除记忆，只是有时候找不到路。  
> *Never delete. Only decay retrieval pathways.*

---

## 为什么需要 Hippocampus？

当前的 LLM 对话系统，每一轮几乎从零开始理解你。你消耗的 Token 里，90% 都在重新建立上下文——能源、GPU 算力、存储空间，大量被浪费在重复对话中。

**Hippocampus** 是一种完全不同的范式——它模拟人类的记忆方式：

| 人类大脑 | Hippocampus 实现 |
|---|---|
| 👁️ 工作记忆（前额叶） | 当前会话上下文 |
| 😨 情绪评分（杏仁核） | 情感加权重要性 |
| 🏗️ 记忆巩固（海马体） | 活跃层 → 休眠层 → 永久层 |
| 🗄️ 长时存储（新皮层） | 本地向量数据库 |
| 🔍 情景唤醒 | 语义上下文匹配 |
| 📉 遗忘曲线（艾宾浩斯） | 检索权重衰减，永不删除 |

---

## 核心特性

### 🚫 永不删除
记忆只会被降权、压缩，但永远不会被删除。就像你闻到桂花香会突然想起三十年前的外婆厨房——记忆一直在那里，只是平时找不到路。

### 🌊 三层记忆存储

```
🔴 活跃层 (Active)     — 高频检索，完整存储
🟡 休眠层 (Dormant)    — 低频检索，压缩摘要，极低权重
💎 永久层 (Permastore)  — 高情感记忆，永不衰退
```

### 🔮 上下文唤醒 (Context Wake)

当前对话的语义向量，会与**编码时的上下文向量**做匹配。超过阈值的休眠记忆会被"唤醒"——这就是"突然想起来"的技术等价。

### 📊 动态重要性

```
重要性 = 情绪分 × 0.6 + 内容实质性 × 0.3 + 检索次数加权
```

你反复提到的话题、你表达兴奋或沮丧的内容、你纠正过的方向——这些天然高权重。

### 🧹 类睡眠巩固

每天自动：合并相似记忆、压缩孤立记忆、提升被唤醒记忆的权重。

---

## 快速开始

### 1. 安装依赖

```bash
pip install fastembed numpy
```

首次运行时自动下载嵌入模型 (~130MB)，仅此一次。

### 2. 选择记忆范围（重要！）

Hippocampus 默认**全局模式**——所有项目共享同一份记忆。

| 你的环境 | 需要做什么 |
|---|---|
| 普通终端 (Linux/macOS/Windows) | 无需配置，直接使用 |
| Codex 沙箱 | 配置 `HIPPOCAMPUS_HOME` 环境变量（见下方） |

#### 全局记忆（默认，推荐）

终端用户无需任何配置。Codex 沙箱用户需在 `~/.codex/config.toml` 的 `[shell_environment_policy.set]` 段加一行：

```toml
[shell_environment_policy.set]
HIPPOCAMPUS_HOME = "C:\\Users\\你的用户名\\Documents\\hippocampus-data"
```

> 原因：沙箱默认不允许写入 `~/.codex/hippocampus/`，设置 `HIPPOCAMPUS_HOME` 指向 workspace 即可。

#### 项目局部记忆

```bash
# Linux/macOS
export HIPPOCAMPUS_SCOPE=local

# Windows PowerShell
$env:HIPPOCAMPUS_SCOPE = "local"
```

数据存储在项目根目录 `.hippocampus/` 下，不同项目互不干扰。

#### 交互式安装向导

```bash
python setup.py
```

### 3. 编码记忆

```bash
python -m hippocampus.engine consolidate \
  "用户偏好用 Rust 写系统级代码，Python 写工具脚本" \
  --emotion 0.3 \
  --topic "编码偏好" \
  --tags rust python
```

### 4. 检索记忆

```bash
python -m hippocampus.engine retrieve "写什么语言好" --top 5
```

### 5. 生成会话上下文

```bash
python -m hippocampus.engine context "代码重构"
```

### 6. 查看统计

```bash
python -m hippocampus.engine stats
```

---

## 架构

```
┌─────────────────────────────────────────────────┐
│                每次对话 Session                    │
│  ┌─────────┐   ┌──────────┐  ┌──────────────┐  │
│  │ 当前对话 │──▶│ 重要性评分 │──▶│ 记忆碎片提取  │  │
│  │ (WFM)   │   │ (Amygdala)│  │ (Hippocampus)│  │
│  └─────────┘   └──────────┘  └──────┬───────┘  │
│                                      │           │
│                                 ┌────▼─────┐    │
│                                 │ 本地向量库 │    │
│                                 │(Neocortex)│    │
│                                 └────┬─────┘    │
│                        ┌─────────────┼──────┐   │
│                        │ 遗忘曲线  │ 联想链  │   │
│                        │ (Forget)  │ (Link)  │   │
│                        └─────────────┴──────┘   │
└─────────────────────────────────────────────────┘
```

---

## 设计哲学

> **不治遗忘，治检索；**  
> **让线索来找记忆，而不是记忆等线索。**

The brain doesn't delete. It just loses the path.  
Our job is to build better paths.

---

## 理论基础

- **Tulving & Thomson (1973)** — Encoding Specificity Principle  
- **Bahrick (1984)** — Permastore: 50年记忆保持实验  
- **Ebbinghaus (1885)** — 遗忘曲线  
- **Nadel & Moscovitch (1997)** — Multiple Trace Theory  
- **McGaugh (2000)** — 杏仁核情绪加权记忆巩固  

---

## License

MIT — 开源，自由使用、修改、分发。

---

<p align="center">
  <i>记忆不是被删除的，而是迷路了。<br>
  我们做的事，就是为每一条记忆留下足够多的路标。</i>
</p>

---

## 安装与排障

### 依赖

```bash
pip install fastembed numpy
```

> 原方案使用 `sentence-transformers`，在 macOS Apple Silicon + 沙箱环境下因 PyTorch/OpenMP 冲突会导致 segfault。已切换为 `fastembed`（ONNX 运行时），更轻量、无冲突、兼容性更好。

### 常见问题

**Q: `PermissionError: '/Users/xxx/.cache/huggingface'`**

A: 沙箱环境可能限制 `~/.cache` 写入。设置环境变量解决：

```bash
export HF_HOME=/path/to/writable/dir
```

也可写到项目目录：
```bash
export HF_HOME=$(pwd)/.hf_cache
```

**Q: `OMP: Error #15: libomp.dylib already initialized`**

A: Apple Silicon 上 PyTorch 与系统 OpenMP 冲突。如使用 `sentence-transformers`，设置：
```bash
export KMP_DUPLICATE_LIB_OK=TRUE
```
但推荐直接使用 `fastembed`（已在 requirements.txt 中）。

**Q: 首次运行很慢？**

A: 嵌入模型 `BAAI/bge-small-en-v1.5` 首次需下载（~130MB）。之后缓存到 `HF_HOME`，后续运行秒级响应。

**Q: 如何切换全局/项目隔离？**

A: 默认全局（`~/.codex/hippocampus/global/`）。需要项目隔离时设置：
```bash
export HIPPOCAMPUS_SCOPE=project
```

**Q: 安装 Skill 到 Codex**

A:
```bash
cp -r codex-hippocampus ~/.codex/skills/codex-hippocampus
```
Install from GitHub:
```bash
git clone https://github.com/feng78-boop/codex-hippocampus.git ~/.codex/skills/codex-hippocampus
```
