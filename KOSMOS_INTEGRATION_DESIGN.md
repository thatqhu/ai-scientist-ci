# SCI AI Scientist - Kosmos 集成设计方案

## 目录
- [方案概述](#方案概述)
- [架构设计](#架构设计)
- [集成方案对比](#集成方案对比)
- [推荐方案详细设计](#推荐方案详细设计)
- [实施步骤](#实施步骤)
- [使用示例](#使用示例)
- [优缺点分析](#优缺点分析)

---

## 方案概述

将 `sci-ai-scientist` 集成到 `Kosmos` 框架的核心目标：
- **最小改动原则**：两个项目都保持独立性，改动最小化
- **插件式架构**：sci-ai-scientist 作为 Kosmos 的领域扩展
- **可选依赖**：Kosmos 可以在不安装 sci-ai-scientist 的情况下正常运行
- **双向兼容**：sci-ai-scientist 既可以独立运行，也可以作为 Kosmos 扩展

---

## 架构设计

### 当前项目结构

```
Kosmos/                          sci-ai-scientist/
├── kosmos/                      ├── src/sci_scientist/
│   ├── agents/                  │   ├── agents/
│   ├── workflow/                │   │   ├── planner.py
│   ├── orchestration/           │   │   ├── executor.py
│   ├── knowledge/               │   │   └── analysis.py
│   ├── validation/              │   ├── core/
│   └── world_model/             │   │   ├── scientist.py
└── ...                          │   │   └── data_structures.py
                                 │   ├── models/
                                 │   │   └── world_model.py
                                 │   └── llm/
                                 └── main.py
```

### 集成后的架构

```
Kosmos/ (主项目)
├── kosmos/
│   ├── agents/
│   ├── workflow/
│   ├── extensions/              # 新增：扩展系统
│   │   ├── __init__.py
│   │   ├── base.py             # ExtensionBase 基类
│   │   ├── registry.py         # 扩展注册器
│   │   └── loader.py           # 动态加载器
│   └── ...
│
sci-ai-scientist/ (扩展项目)
├── src/sci_scientist/
│   ├── kosmos_extension.py     # Kosmos 扩展接口 ✨
│   ├── agents/                 # 保持不变
│   ├── core/                   # 保持不变
│   └── ...
└── setup.py                    # 添加 kosmos 作为可选依赖
```

---

## 集成方案对比

### 方案 1：插件式扩展（推荐 ⭐）

**原理**：sci-ai-scientist 作为独立的 Python 包，通过标准的扩展接口集成到 Kosmos

**优点**：
- ✅ 两个项目完全解耦，各自独立开发
- ✅ sci-ai-scientist 可以独立使用或作为扩展
- ✅ Kosmos 改动最小，只需添加扩展系统
- ✅ 易于维护和测试

**缺点**：
- ❌ 需要在 Kosmos 中添加扩展系统（约 200 行代码）
- ❌ 第一次使用需要安装两个包

**Kosmos 需要改动**：
```python
# 新增 3 个文件
kosmos/extensions/base.py      # ~50 行
kosmos/extensions/registry.py  # ~100 行
kosmos/extensions/loader.py    # ~50 行
```

**sci-ai-scientist 需要改动**：
```python
# 新增 1 个文件
src/sci_scientist/kosmos_extension.py  # ~250 行

# 修改 setup.py
# 添加 kosmos 作为可选依赖
```

---

### 方案 2：子模块集成

**原理**：将 sci-ai-scientist 作为 Kosmos 的 git submodule

**优点**：
- ✅ 代码在一个仓库中
- ✅ 版本同步简单

**缺点**：
- ❌ 耦合度高，不利于独立开发
- ❌ 用户必须同时安装两个项目
- ❌ 违背"最小改动"原则

---

### 方案 3：Monorepo

**原理**：将两个项目合并到一个 monorepo

**优点**：
- ✅ 统一管理

**缺点**：
- ❌ 需要重构项目结构
- ❌ 违背"最小改动"和"独立性"原则
- ❌ 不利于社区贡献

---

## 推荐方案详细设计

### 方案 1：插件式扩展

#### 1. Kosmos 端改动

**a) 创建扩展基类** (`kosmos/extensions/base.py`)

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List

class KosmosExtension(ABC):
    """Kosmos 扩展基类"""

    # 扩展元数据（必须）
    EXTENSION_NAME: str
    EXTENSION_VERSION: str
    SUPPORTED_DOMAINS: List[str]

    @abstractmethod
    async def run_research_cycle(
        self,
        research_objective: str,
        **kwargs
    ) -> Dict[str, Any]:
        """执行研究循环"""
        pass

    @abstractmethod
    def get_research_summary(self) -> Dict[str, Any]:
        """获取研究摘要"""
        pass

    def export_for_knowledge_graph(self) -> Dict[str, Any]:
        """导出到知识图谱（可选）"""
        return {'nodes': [], 'relationships': []}
```

**b) 创建扩展注册器** (`kosmos/extensions/registry.py`)

```python
from typing import Dict, Type, Optional
from .base import KosmosExtension

class ExtensionRegistry:
    """扩展注册器"""

    _extensions: Dict[str, Type[KosmosExtension]] = {}

    @classmethod
    def register(cls, extension_class: Type[KosmosExtension]):
        """注册扩展"""
        name = extension_class.EXTENSION_NAME
        cls._extensions[name] = extension_class
        return extension_class

    @classmethod
    def get(cls, name: str) -> Optional[Type[KosmosExtension]]:
        """获取扩展"""
        return cls._extensions.get(name)

    @classmethod
    def list_extensions(cls) -> List[str]:
        """列出所有扩展"""
        return list(cls._extensions.keys())
```

**c) 修改研究工作流** (`kosmos/workflow/research_loop.py`)

```python
# 添加扩展支持
class ResearchWorkflow:
    def __init__(
        self,
        research_objective: str,
        domain: Optional[str] = None,
        extension: Optional[str] = None,  # 新增参数
        **kwargs
    ):
        self.extension_instance = None

        # 如果指定了扩展，加载它
        if extension:
            from kosmos.extensions.loader import load_extension
            self.extension_instance = load_extension(
                extension,
                config=kwargs
            )

    async def run(self, num_cycles: int = 5, **kwargs):
        # 如果有扩展，优先使用扩展
        if self.extension_instance:
            return await self.extension_instance.run_research_cycle(
                self.research_objective,
                num_cycles=num_cycles,
                **kwargs
            )

        # 否则使用 Kosmos 默认流程
        return await self._run_default_workflow(num_cycles, **kwargs)
```

**总改动量**：约 **3 个新文件，200 行代码**

---

#### 2. sci-ai-scientist 端改动

**a) 创建 Kosmos 扩展接口** (`src/sci_scientist/kosmos_extension.py`)

```python
from kosmos.extensions.base import KosmosExtension
from kosmos.extensions.registry import ExtensionRegistry

@ExtensionRegistry.register
class SCIKosmosExtension(KosmosExtension):
    """SCI 领域扩展"""

    EXTENSION_NAME = "sci-ai-scientist"
    EXTENSION_VERSION = "3.0.0"
    SUPPORTED_DOMAINS = ["sci", "imaging", "computational-imaging"]

    def __init__(self, config: Dict[str, Any]):
        # 使用现有的 sci_scientist 组件
        self.scientist = AIScientist(...)
        self.world_model = WorldModel(...)

    async def run_research_cycle(self, research_objective: str, **kwargs):
        # 调用现有的 scientist.run_async()
        pareto_set, insights = await self.scientist.run_async(...)

        return {
            'status': 'completed',
            'pareto_front': pareto_set,
            'insights': insights,
            ...
        }

    def export_for_knowledge_graph(self):
        # 将 SCI 实验结果转换为知识图谱格式
        return {...}
```

**b) 修改 `setup.py`/`pyproject.toml`**

```toml
[project.optional-dependencies]
kosmos = [
    "kosmos-ai>=1.0.0"  # 可选依赖
]

[project.entry-points."kosmos.extensions"]
sci = "sci_scientist.kosmos_extension:SCIKosmosExtension"
```

**总改动量**：**1 个新文件约 250 行，setup.py 添加 5 行**

---

## 实施步骤

### Phase 1: Kosmos 端准备（可以作为独立 PR）

1. **创建扩展系统**
   ```bash
   cd Kosmos
   mkdir -p kosmos/extensions
   # 创建 base.py, registry.py, loader.py
   ```

2. **修改工作流**
   - 在 `ResearchWorkflow` 添加扩展支持
   - 保持向后兼容

3. **测试**
   ```bash
   # 确保现有功能不受影响
   pytest tests/
   ```

### Phase 2: sci-ai-scientist 端实现

1. **创建扩展接口**
   ```bash
   cd sci-ai-scientist
   # 创建 kosmos_extension.py
   ```

2. **修改 setup.py**
   - 添加 kosmos 作为可选依赖

3. **测试独立运行**
   ```bash
   # 确保不安装 kosmos 时仍可独立运行
   python main.py --mock --budget 10
   ```

### Phase 3: 集成测试

1. **安装两个包**
   ```bash
   pip install kosmos-ai
   pip install sci-ai-scientist[kosmos]
   ```

2. **测试集成**
   ```python
   from kosmos.workflow.research_loop import ResearchWorkflow

   workflow = ResearchWorkflow(
       research_objective="Optimize SCI reconstruction",
       extension="sci-ai-scientist",
       domain="sci"
   )

   result = await workflow.run(num_cycles=5)
   ```

---

## 使用示例

### 场景 1：作为 Kosmos 扩展使用

```python
from kosmos.workflow.research_loop import ResearchWorkflow

async def main():
    # 使用 SCI 扩展
    workflow = ResearchWorkflow(
        research_objective="Find optimal SCI reconstruction config",
        extension="sci-ai-scientist",
        budget=20,
        artifacts_dir="./artifacts/sci"
    )

    result = await workflow.run(num_cycles=5)

    # 结果会自动添加到 Kosmos 知识图谱
    print(f"Pareto front: {result['pareto_front']}")
    print(f"Insights: {result['insights']}")

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
```

### 场景 2：独立使用（不依赖 Kosmos）

```python
from src.sci_scientist.core.scientist import AIScientist
# ... 现有的使用方式保持不变

ai_scientist = AIScientist(...)
pareto_set, insights = await ai_scientist.run_async(...)
```

### 场景 3：Kosmos CLI 集成

```bash
# 使用 SCI 扩展
kosmos run "Optimize SCI reconstruction" \
    --extension sci-ai-scientist \
    --domain sci \
    --budget 50

# 查看可用扩展
kosmos extensions list

# 查看扩展信息
kosmos extensions info sci-ai-scientist
```

---

## 优缺点分析

### 插件式扩展方案

| 维度 | 评分 | 说明 |
|------|------|------|
| **最小改动** | ⭐⭐⭐⭐⭐ | Kosmos ~200 行，sci-ai-scientist ~260 行 |
| **独立性** | ⭐⭐⭐⭐⭐ | 两个项目完全独立，互不影响 |
| **可维护性** | ⭐⭐⭐⭐⭐ | 清晰的接口，易于维护 |
| **易用性** | ⭐⭐⭐⭐ | 需要安装两个包，略有学习曲线 |
| **扩展性** | ⭐⭐⭐⭐⭐ | 可以添加更多领域扩展 |
| **性能** | ⭐⭐⭐⭐⭐ | 无性能损失 |

### 实施复杂度

- **Kosmos 改动**：低（约 2-3 小时）
- **sci-ai-scientist 改动**：低（约 2-3 小时）
- **测试工作量**：中（约 4-6 小时）
- **文档更新**：中（约 2-3 小时）

**总计**：约 1-2 个工作日

---

## 替代方案考虑

### 如果觉得扩展系统太复杂

**轻量级方案**：直接在 Kosmos 中导入使用

```python
# kosmos/domains/sci.py (新文件，约 100 行)
from typing import Optional

try:
    from sci_scientist.core.scientist import AIScientist
    from sci_scientist.agents.planner import PlannerAgent
    SCI_AVAILABLE = True
except ImportError:
    SCI_AVAILABLE = False

class SCIDomainAdapter:
    """轻量级 SCI 适配器"""

    def __init__(self, config):
        if not SCI_AVAILABLE:
            raise ImportError("sci-ai-scientist not installed")

        self.scientist = AIScientist(...)

    async def run(self, objective: str, num_cycles: int):
        return await self.scientist.run_async(...)
```

**优点**：
- ✅ 更简单，不需要扩展系统
- ✅ Kosmos 改动更小（约 100 行）

**缺点**：
- ❌ 不够通用，难以支持其他领域
- ❌ 耦合度稍高

---

## 推荐实施路径

### 短期（快速集成）

1. **使用轻量级方案**
   - 在 Kosmos 添加 `kosmos/domains/sci.py`
   - sci-ai-scientist 添加 `kosmos` 作为可选依赖
   - 快速验证集成可行性

### 长期（完整架构）

1. **构建扩展系统**
   - 实现完整的扩展架构
   - 支持多个领域扩展
   - 提供更好的生态系统

---

## 下一步行动

### 建议您先：

1. ✅ **Review 这个设计文档**
   - 确认方案是否符合需求
   - 提出修改意见

2. ✅ **选择实施方案**
   - 插件式扩展（推荐，长期）
   - 轻量级适配器（短期快速）

3. ✅ **与 Kosmos 维护者沟通**
   - 确认他们是否接受扩展系统
   - 讨论技术细节

4. ✅ **创建 POC (Proof of Concept)**
   - 先实现一个最小版本
   - 验证技术可行性

### 我可以帮助您：

- 📝 创建详细的技术提案（供 Kosmos 项目）
- 💻 实现 POC 代码
- 📚 编写集成文档
- 🧪 设计测试用例

---

## 附录

### A. 相关资源

- Kosmos GitHub: https://github.com/jimmc414/Kosmos
- Kosmos 架构文档: （待补充）
- Python 插件系统最佳实践: https://packaging.python.org/guides/creating-and-discovering-plugins/

### B. 技术栈兼容性

| 组件 | Kosmos | sci-ai-scientist | 兼容性 |
|------|--------|------------------|--------|
| Python | 3.11+ | 3.9+ | ✅ |
| Async/Await | ✅ | ✅ | ✅ |
| LLM Client | Anthropic/OpenAI | OpenAI/Gemini | ✅ 可适配 |
| 数据存储 | JSON/Neo4j | SQLite | ✅ 独立 |

### C. 常见问题

**Q: 是否需要修改 sci-ai-scientist 的核心逻辑？**
A: 不需要。只需要添加一个适配层（kosmos_extension.py）

**Q: 用户必须安装 Kosmos 才能使用 sci-ai-scientist 吗？**
A: 不需要。sci-ai-scientist 可以完全独立运行。

**Q: 性能会受影响吗？**
A: 不会。只是多了一层适配接口，性能影响可以忽略不计。
