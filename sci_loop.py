#!/usr/bin/env python3
"""
AI Scientist for SCI - Main Entry Point
"""

import os
import argparse
from pathlib import Path

import yaml
from loguru import logger
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from src.core.scientist import (
    AIScientist,
    WorldModel,
    PlannerAgent,
    ExecutorAgent,
    AnalysisAgent,
    PlanReviewerAgent,
    MessageBus,
)
from src.agents.sci.planner import create_baseline_configs


def load_config(config_path: str) -> dict:
    """Load configuration file"""
    if not Path(config_path).exists():
        logger.warning(f"Config not found: {config_path}")
        return {}

    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    # Parse environment variables
    if 'llm' in config and 'api_key' in config['llm']:
        api_key = config['llm']['api_key']
        if api_key.startswith('${') and api_key.endswith('}'):
            env_var = api_key[2:-1]
            config['llm']['api_key'] = os.environ.get(env_var, '')

    return config


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="AI Scientist for SCI v3.0")
    parser.add_argument("--config", type=str, default="config/default.yaml")
    parser.add_argument("--mock", action="store_true", help="Mock mode")
    parser.add_argument("--budget", type=int, default=None)
    parser.add_argument("--cycles", type=int, default=None)
    args = parser.parse_args()

    config = load_config(args.config)

    # Design space
    design_space = config.get('design_space', {
        "compression_ratios": [8, 16, 24],
        "mask_types": ["random", "optimized"],
        "num_stages": [5, 7, 9],
        "num_features": [32, 64, 128],
        "num_blocks": [2, 3, 4],
        "learning_rates": [1e-4, 5e-5],
        "activations": ["ReLU", "LeakyReLU"]
    })

    # LLM configuration
    llm_config = config.get('llm', {
        'base_url': 'https://api.openai.com/v1',
        'api_key': os.environ.get('OPENAI_API_KEY', ''),
        'model': 'gpt-4-turbo-preview',
    })

    # Experiment settings
    exp_cfg = config.get('experiment', {})
    budget_max = args.budget or exp_cfg.get('budget_max', 20)
    max_cycles = args.cycles or exp_cfg.get('max_cycles', 5)
    mock_mode = args.mock or exp_cfg.get('mock_mode', True)
    db_path = config.get('database', {}).get('path', 'world_model_v3.db')

    # Initialize components
    bus = MessageBus()
    world_model = WorldModel(db_path)

    planner = PlannerAgent(
        config.get('planner', {}),
        bus=bus,
        world_model=world_model,
        llm_config=llm_config
    )

    # Executor config (merge with mock mode setting)
    executor_config = config.get('executor', {})
    executor_config['mock'] = mock_mode
    executor = ExecutorAgent(executor_config, bus=bus)

    analyzer = AnalysisAgent(llm_config, bus=bus, world_model=world_model)
    reviewer = PlanReviewerAgent(
        llm_client=planner.llm_client,
        bus=bus,
        design_space=design_space,
        world_model=world_model
    )

    ai_scientist = AIScientist(
        world_model, planner, executor, analyzer, reviewer, bus, design_space, budget_max
    )

    # Run
    initial_configs = create_baseline_configs(design_space)
    pareto_set, insights = ai_scientist.run(initial_configs, max_cycles)

    # Results
    logger.info(f"\nPareto Front: {pareto_set[:5]}")
    if 'trends' in insights:
        logger.info(f"Findings: {insights['trends'].get('key_findings', [])[:3]}")


if __name__ == "__main__":
    main()
