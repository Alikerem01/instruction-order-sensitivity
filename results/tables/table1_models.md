Table 1. Models (pinned revisions; bf16, greedy decoding, batch size 1 in the main run).

| Model | Hugging Face id | Parameters | License | Revision | Chat template |
|---|---|---|---|---|---|
| SmolLM2-1.7B | `HuggingFaceTB/SmolLM2-1.7B-Instruct` | 1.7B; 1,711,376,384 stored | Apache-2.0 | `31b70e2e869a` | official template; system role native |
| Qwen2.5-3B | `Qwen/Qwen2.5-3B-Instruct` | 3.1B; 3,085,938,688 stored | Qwen Research License (non-commercial) | `aa8e72537993` | official template; system role native |
| Phi-4-mini | `microsoft/Phi-4-mini-instruct` | 3.8B; 3,836,021,760 stored | MIT | `cfbefacb9925` | official template; system role native; Hub remote code never used |
| Gemma 4 E4B | `google/gemma-4-E4B-it` | 4.5B effective (8B with embeddings), as stated in the model card; 7,996,156,490 stored | Apache-2.0 | `ee0ef6023621` | official template; native system turn; thinking disabled (enable_thinking=False) |
