from __future__ import annotations

import json
from pathlib import Path

import yaml
from datasets import load_dataset
from transformers import AutoModelForCausalLM, AutoTokenizer
from trl import DPOConfig, DPOTrainer


def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def main() -> None:
    config = load_config("training/config/dpo.yaml")
    dataset = load_dataset(
        config["dataset"]["name"],
        data_files=config["dataset"].get("data_files"),
        split=config["dataset"]["split"],
    )

    tokenizer = AutoTokenizer.from_pretrained(config["model"]["base"])
    model = AutoModelForCausalLM.from_pretrained(config["model"]["base"])

    training_args = DPOConfig(
        output_dir=config["output"]["dir"],
        beta=config["training"]["beta"],
        learning_rate=config["training"]["learning_rate"],
        per_device_train_batch_size=config["training"]["batch_size"],
        num_train_epochs=config["training"]["epochs"],
        logging_steps=config["training"]["logging_steps"],
    )

    trainer = DPOTrainer(
        model=model,
        ref_model=None,
        args=training_args,
        train_dataset=dataset,
        tokenizer=tokenizer,
    )
    trainer.train()

    model.save_pretrained(config["output"]["dir"])
    Path(config["output"]["dir"]).joinpath("config.json").write_text(
        json.dumps(config, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
