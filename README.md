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

### 1. 安装

```bash
cd hippocampus
pip install sentence-transformers numpy
```

无需外部 API Key。嵌入模型 `all-MiniLM-L6-v2` (~80MB) 完全本地运行。

### 2. 编码一段记忆

```bash
python3 -m hippocampus.hippocampus.engine consolidate \
  "用户偏好用 Rust 写系统级代码，Python 写工具脚本" \
  --emotion 0.3 \
  --topic "编码偏好" \
  --tags rust python
```

### 3. 检索相关记忆

```bash
python3 -m hippocampus.hippocampus.engine retrieve "写什么语言好" --top 5
```

### 4. 生成会话上下文

```bash
python3 -m hippocampus.hippocampus.engine context "代码重构"
```

### 5. 查看统计

```bash
python3 -m hippocampus.hippocampus.engine stats
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
