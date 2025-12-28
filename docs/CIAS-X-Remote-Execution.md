# CIAS-X 远程执行指南

本指南说明如何使用CIAS-X系统的远程执行模式，通过FastAPI服务执行实验。

## 系统架构

```
┌─────────────────┐         HTTP API         ┌──────────────────────┐
│   CIAS-X Core   │ ──────────────────────▶  │  FastAPI Service     │
│   (Workflow)    │                           │  (Training Server)   │
│                 │ ◀──────────────────────   │                      │
│  - Planner      │    Task Status/Results    │  - Task Queue        │
│  - Executor     │                           │  - Mock Training     │
│  - Analyst      │                           │  - Result Storage    │
└─────────────────┘                           └──────────────────────┘
```

## 快速开始

### 1. 启动FastAPI服务

```bash
# 安装依赖
pip install fastapi uvicorn numpy pydantic

# 启动服务
uvicorn mock_service:app --reload --port 8000

# 服务将运行在 http://localhost:8000
```

验证服务是否运行：
```bash
curl http://localhost:8000/health
# 应返回: {"status":"ok"}
```

### 2. 运行CIAS-X（远程模式）

```bash
# 使用远程执行模式
python run_cias_x.py \
  --remote \
  --service-url http://localhost:8000 \
  --budget 10 \
  --db cias_remote.db

# 指定其他参数
python run_cias_x.py \
  --remote \
  --service-url http://localhost:8000 \
  --budget 20 \
  --top-k 15 \
  --db my_experiments.db
```

### 3. Mock模式（默认，无需服务）

```bash
# 不使用--remote标志，使用本地mock
python run_cias_x.py --budget 10 --db cias_mock.db
```

## API接口说明

### 提交训练任务

**Endpoint**: `POST /train`

**Request**:
```json
{
  "experiment_id": "exp_abc123",
  "forward_model": {
    "compression_ratio": 16,
    "mask_type": "random",
    "sensor_noise": 0.01,
    "resolution": [256, 256],
    "frame_rate": 30
  },
  "reconstruction": {
    "family": "CIAS-Core",
    "num_stages": 7,
    "num_features": 64,
    "num_blocks": 3,
    "learning_rate": 0.0001,
    "use_physics_prior": true,
    "activation": "ReLU"
  },
  "training": {
    "batch_size": 4,
    "num_epochs": 50,
    "optimizer": "Adam",
    "scheduler": "CosineAnnealing",
    "early_stopping": true
  },
  "uncertainty_quantification": {
    "scheme": "conformal",
    "params": {}
  }
}
```

**Response**:
```json
{
  "task_id": "uuid-string",
  "experiment_id": "exp_abc123",
  "status": "pending",
  "created_at": "2025-12-28T19:00:00"
}
```

### 查询任务状态

**Endpoint**: `GET /tasks/{task_id}/status`

**Response**:
```json
{
  "task_id": "uuid-string",
  "experiment_id": "exp_abc123",
  "status": "running",
  "progress": 0.65,
  "message": "Training epoch 26-40",
  "started_at": "2025-12-28T19:00:01",
  "completed_at": null
}
```

### 获取任务结果

**Endpoint**: `GET /tasks/{task_id}/result`

**Response**:
```json
{
  "task_id": "uuid-string",
  "experiment_id": "exp_abc123",
  "status": "completed",
  "metrics": {
    "psnr": 28.5,
    "ssim": 0.85,
    "coverage": 0.92,
    "latency": 45.2,
    "memory": 1536,
    "training_time": 1.5,
    "convergence_epoch": 25
  },
  "artifacts": {
    "checkpoint_path": "/checkpoints/uuid/model_best.pth",
    "training_log_path": "/logs/uuid/training.log",
    "sample_reconstructions": ["/samples/uuid/recon_0.png", ...],
    "figure_scripts": ["/figures/uuid/plot_metrics.py"],
    "metrics_history": {"psnr": [...], "ssim": [...]}
  },
  "error_message": null,
  "completed_at": "2025-12-28T19:00:30"
}
```

## 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--remote` | 使用远程执行模式 | False (使用mock) |
| `--service-url` | FastAPI服务地址 | http://localhost:8000 |
| `--budget` | 实验预算 | 10 |
| `--top-k` | 每个strata的Pareto前沿数量 | 10 |
| `--db` | 数据库路径 | cias_x.db |
| `--config` | 配置文件路径 | config/default.yaml |

## 配置文件示例

`config/default.yaml`:
```yaml
experiment:
  budget_max: 20
  service_url: http://localhost:8000

pareto:
  top_k: 10

database:
  path: cias_x.db

design_space:
  compression_ratios: [8, 16, 24]
  mask_types: ["random", "optimized"]
  num_stages: [5, 7, 9]
  num_features: [32, 64, 128]
  num_blocks: [2, 3, 4]
  learning_rates: [0.0001, 0.00005]
  activations: ["ReLU", "LeakyReLU"]

llm:
  base_url: https://generativelanguage.googleapis.com/v1beta/openai/
  api_key: ${GOOGLE_API_KEY}
  model: gemini-2.5-flash
```

## Executor实现细节

远程执行器(`CIASExecutorAgent`)的工作流程：

1. **配置转换**：将`SCIConfiguration`转换为API格式
2. **任务提交**：POST请求到`/train`端点
3. **状态轮询**：每2秒查询一次`/tasks/{task_id}/status`
4. **结果获取**：任务完成后从`/tasks/{task_id}/result`获取
5. **超时处理**：默认最大等待300秒
6. **错误处理**：失败任务返回失败标记的`ExperimentResult`

## 依赖项

远程模式需要额外依赖：

```bash
pip install httpx  # HTTP客户端
```

Mock模式无需额外依赖。

## 故障排除

### 连接错误

```
httpx.ConnectError: Connection refused
```

**解决**：确保FastAPI服务正在运行

```bash
uvicorn mock_service:app --reload --port 8000
```

### 任务超时

```
Task timed out after 300s
```

**解决**：
1. 增加`max_wait_time`参数（修改executor初始化）
2. 检查服务端任务是否卡住

### 导入错误

```
ImportError: httpx is required for remote execution
```

**解决**：
```bash
pip install httpx
```

## 性能对比

| 模式 | 延迟 | 真实性 | 使用场景 |
|------|------|--------|----------|
| Mock | 极低（<1ms） | 模拟 | 快速开发、测试工作流 |
| Remote | 中等（1-5s） | 可配置 | 接近真实训练、集成测试 |
| Real | 高（分钟级） | 真实 | 生产环境 |

## 示例输出

```
2025-12-28 19:04:43 - INFO - Initializing CIAS-X (mode=remote, service=http://localhost:8000)
2025-12-28 19:04:43 - INFO - Starting CIAS-X workflow (budget=10)
2025-12-28 19:04:44 - INFO - Submitting experiment exp_abc123 to http://localhost:8000/train
2025-12-28 19:04:44 - INFO - Task submitted: uuid-123
2025-12-28 19:04:46 - DEBUG - Task uuid-123 status: running (35%)
2025-12-28 19:04:48 - DEBUG - Task uuid-123 status: running (70%)
2025-12-28 19:04:50 - DEBUG - Task uuid-123 status: completed (100%)
2025-12-28 19:04:50 - INFO - Task uuid-123 completed. PSNR: 28.50dB, SSIM: 0.8500
```

## 下一步

- 集成真实的GPU训练服务
- 添加任务队列和并发执行
- 实现结果缓存机制
- 支持分布式训练
