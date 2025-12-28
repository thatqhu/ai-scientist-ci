"""
SCI Experiment Data Structures

Defines configuration and result structures for SCI reconstruction experiments.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Tuple, Optional


class ReconFamily(str, Enum):
    """Reconstruction algorithm family"""
    CIAS_CORE = "CIAS-Core"
    CIAS_PLUS = "CIAS-Plus"
    TRADITIONAL = "Traditional"


class UQScheme(str, Enum):
    """Uncertainty Quantification scheme"""
    CONFORMAL = "conformal"
    ENSEMBLE = "ensemble"
    BAYESIAN = "bayesian"
    NONE = "none"


@dataclass
class ForwardConfig:
    """Forward model configuration"""
    compression_ratio: int
    mask_type: str
    sensor_noise: float
    resolution: Tuple[int, int]
    frame_rate: int


@dataclass
class ReconParams:
    """Reconstruction model parameters"""
    num_stages: int
    num_features: int
    num_blocks: int
    learning_rate: float
    use_physics_prior: bool
    activation: str


@dataclass
class TrainConfig:
    """Training configuration"""
    batch_size: int
    num_epochs: int
    optimizer: str
    scheduler: str
    early_stopping: bool


@dataclass
class SCIConfiguration:
    """Complete SCI experiment configuration"""
    experiment_id: str
    forward_config: ForwardConfig
    recon_family: ReconFamily
    recon_params: ReconParams
    uq_scheme: UQScheme
    uq_params: Dict[str, Any]
    train_config: TrainConfig
    timestamp: str


@dataclass
class Metrics:
    """Experiment metrics"""
    psnr: float
    ssim: float
    coverage: float
    latency: float
    memory: float
    training_time: float
    convergence_epoch: int


@dataclass
class Artifacts:
    """Experiment artifacts"""
    checkpoint_path: str
    training_log_path: str
    sample_reconstructions: List[str] = field(default_factory=list)
    figure_scripts: List[str] = field(default_factory=list)
    metrics_history: Dict[str, List] = field(default_factory=dict)


@dataclass
class ExperimentResult:
    """Complete experiment result"""
    experiment_id: str
    config: SCIConfiguration
    metrics: Metrics
    artifacts: Artifacts
    status: str
    started_at: str
    completed_at: str
    error_message: Optional[str] = None
