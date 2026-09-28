# NEXUS V8 Russian Cognitive Cortex

## Цель
V8 заменяет случайно инициализированный русский cortex на предобученный Qwen3, но не передаёт языковой модели право истины.

## Authority
1. R1.3-X / exact / formal / memory / world.
2. Qwen3 - только структурированное semantic/reasoning proposal.
3. Независимый verifier.
4. VERIFIED или ABSTAIN.

## R2.1, восстановленный с Google Drive
Пакет `NEXUS_R2.1_QWEN3_14B_SOURCE_PHASE2.zip` локально прошёл 31/31 pytest.
Его manifest задаёт production-модель `Qwen3-14B-Q4_K_M.gguf`, ожидаемый SHA-256:
`500a8806e85ee9c83f3ae08420295592451379b4f8cf2d0f41c15dffeb6b81f0`.

На Drive сохранён source/manifest, но сами 9 GB 14B-веса сейчас не обнаружены.
Текущая ~6 GB RAM среда недостаточна для честного Q4_K_M inference.

## Proxy experiment
Для проверки самой идеи V8 подготовлен официальный `Qwen/Qwen3-0.6B` frozen-backbone experiment:
pretrained hidden states -> trainable context adapter -> plan + answer-pointer heads.
`HARD-OOS-K2` запечатан до первого inference.

GitHub Actions run был создан, но не получил runner (runner_id=0, steps=[]), поэтому K2 ещё не открыт моделью и остаётся чистым.

## Следующий критерий
Нельзя объявлять V8 успешным по train/validation. Нужен первый clean K2 one-shot, а затем новый независимый L для production/более сильного backbone.
