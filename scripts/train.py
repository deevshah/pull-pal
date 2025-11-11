from __future__ import annotations

import argparse
from pathlib import Path

from datasets import load_from_disk
from transformers import (
    AutoTokenizer,
    DataCollatorForSeq2Seq,
    EncoderDecoderModel,
    Trainer,
    TrainingArguments,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Fine-tune CodeBERT on code review examples.")
    parser.add_argument("--dataset", type=Path, required=True, help="Path to HF dataset directory.")
    parser.add_argument("--output", type=Path, default=Path("model/checkpoints"))
    parser.add_argument("--model-name", default="microsoft/codebert-base")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=2)
    args = parser.parse_args()

    dataset = load_from_disk(str(args.dataset))
    tokenizer = AutoTokenizer.from_pretrained(args.model_name)
    model = EncoderDecoderModel.from_encoder_decoder_pretrained(args.model_name, args.model_name)
    model.config.decoder_start_token_id = tokenizer.bos_token_id or tokenizer.cls_token_id
    model.config.pad_token_id = tokenizer.pad_token_id
    model.config.vocab_size = model.config.encoder.vocab_size

    data_collator = DataCollatorForSeq2Seq(tokenizer=tokenizer, model=model)

    training_args = TrainingArguments(
        output_dir=str(args.output),
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        save_total_limit=2,
        logging_steps=50,
        learning_rate=5e-5,
        weight_decay=0.01,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
        data_collator=data_collator,
    )
    trainer.train()
    trainer.save_model(str(args.output / "final"))
    tokenizer.save_pretrained(str(args.output / "final"))
    print(f"Training finished. Artifacts at {args.output}")


if __name__ == "__main__":
    main()
