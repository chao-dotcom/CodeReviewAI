from __future__ import annotations

import json
from pathlib import Path

import yaml
from datasets import load_dataset
from peft import LoraConfig, get_peft_model, TaskType
from transformers import AutoModelForCausalLM, AutoTokenizer, Trainer, TrainingArguments


def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def main() -> None:
    config = load_config("training/config/lora.yaml")
    dataset = load_dataset(config["dataset"]["name"], split=config["dataset"]["split"])

    tokenizer = AutoTokenizer.from_pretrained(config["model"]["base"])
    model = AutoModelForCausalLM.from_pretrained(config["model"]["base"])

    lora_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=config["lora"]["rank"],
        lora_alpha=config["lora"]["alpha"],
        target_modules=config["lora"]["target_modules"],
        lora_dropout=config["lora"]["dropout"],
        bias="none",
    )
    model = get_peft_model(model, lora_config)

    def tokenize(batch):
        return tokenizer(batch["text"], truncation=True, max_length=config["dataset"]["max_length"])

    tokenized = dataset.map(tokenize, batched=True, remove_columns=dataset.column_names)

    training_args = TrainingArguments(
        output_dir=config["output"]["dir"],
        per_device_train_batch_size=config["training"]["batch_size"],
        num_train_epochs=config["training"]["epochs"],
        learning_rate=config["training"]["learning_rate"],
        logging_steps=config["training"]["logging_steps"],
        save_steps=config["training"]["save_steps"],
    )

    trainer = Trainer(model=model, args=training_args, train_dataset=tokenized)
    trainer.train()

    model.save_pretrained(config["output"]["dir"])
    Path(config["output"]["dir"]).joinpath("config.json").write_text(
        json.dumps(config, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
