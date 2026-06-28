# Phase 424 — Golden Dataset Runtime Replay Bridge

## الهدف

Phase 423 أنشأت السيناريو الذهبي والأرصدة المتوقعة. Phase 424 تحول هذا السيناريو إلى **بروتوكول Replay** قابل للربط لاحقًا مع DAO/Repositories/API/Offline Queue، بدل أن يبقى مجرد حاسبة Python منفصلة.

## ما تم إضافته

- `alrajhi_client/workspace/quality/golden_dataset_runtime_replay_contract.py`
- `alrajhi_client/workspace/quality/golden_dataset_runtime_replay.py`
- `tools/phase424_golden_dataset_runtime_replay_guard.py`
- `tests/test_phase424_golden_dataset_runtime_replay.py`

## مبدأ العمل

كل عملية من Phase 423 تتحول إلى replay envelope يحتوي على:

- `operation_id`
- `idempotency_key`
- `group`
- `kind`
- `branch_id`
- `payload`

القانون الجديد: `operation_id` هو نفسه `idempotency_key` في السيناريو الذهبي. أي adapter مستقبلي يجب أن يحترم هذا، خصوصًا عند تشغيل offline replay أو API replay.

## Adapter الحالي

تم تنفيذ adapter مرجعي:

`InMemoryGoldenReplayAdapter`

وهو لا يستخدم PyQt ولا قاعدة بيانات ولا سيرفر. وظيفته إثبات أن بروتوكول replay، المقارنة، مخرجات CI، و idempotency metadata كلها تعمل بثبات.

## Adapters معلنة كـ backlog

لم يتم الادعاء أن Phase 424 شغّلت DAO أو API فعليًا. هذه adapters معلنة صراحة كخطوات لاحقة:

- `dao_repository_runtime`
- `http_api_runtime`
- `offline_replay_runtime`

هذا مقصود حتى لا نعطي نتيجة مضللة. Phase 424 تبني الجسر والبروتوكول، لا تدعي أن قاعدة البيانات الفعلية أصبحت مطابقة بعد.

## مخرجات التدقيق

يتم توليد:

- `tools/audit_outputs/golden_dataset_runtime_replay_matrix.csv`
- `tools/audit_outputs/golden_dataset_runtime_replay_steps.json`
- `tools/audit_outputs/golden_dataset_runtime_replay_comparison.csv`
- `tools/audit_outputs/golden_dataset_runtime_replay_actual_balances.json`
- `tools/audit_outputs/golden_dataset_runtime_replay_adapter_manifest.json`

## الأمر التشغيلي

```bash
python tools/phase424_golden_dataset_runtime_replay_guard.py
```

## النتيجة المعمارية

بعد هذه المرحلة أصبح لدينا خط واضح:

Phase 423 = الأرقام الذهبية.
Phase 424 = replay bridge + comparison engine.
Phase 425 = replay against DAO/Repositories أو disposable DB.
Phase 426 = replay against HTTP API.
Phase 427 = replay through offline queue.
