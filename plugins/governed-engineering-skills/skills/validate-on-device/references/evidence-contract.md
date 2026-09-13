# Runtime evidence contract

Use tagged key-value records. Quote values containing spaces. Every validation record has a continuous `seq` and monotonic `t_ms` unless it is a parser-independent normal log line.

Required session records:

```text
VAL_SESSION_BEGIN run=R001 scenario=boot observer=user t_ms=0 seq=1
VAL_EVENT name=system_initialized t_ms=800 seq=2
VAL_SESSION_END run=R001 reason=complete records=3 dropped=0 duration_ms=800 seq=3
```

Every scenario declares `phase: enablement|smoke|acceptance`, `evidence_mode: flow|statistical|mixed`, its own `max_duration_ms`, and a completion contract naming trigger criteria, required criteria, and the accepted session-end reason. There is no universal 30-second default.

For flow evidence, a missing required event is `FAIL` only when the trigger and complete bounded window are proven. Otherwise it is `BLOCKED`. A matching session-end marker cannot override missing required coverage.

For user-operated collection, the `run` value must equal the nonce from `prepare-guided-session`; pass that document with `--guided-session` (or its value with `--expected-run-id`). A matching begin/end pair alone is not replay protection.

For the full guided route, also pass the confirmed `review.json` and every response revision. The runner recomputes them and stores the session, responses, review table, and hashes under the bundle's `guided/` directory. A checked Markdown box is display-only; `confirmation.confirmed` in validated JSON is the evidence gate.

High-frequency paths must aggregate rather than print per sample:

```text
VAL_STATS metric=latency_us phase=steady window_start_ms=1000 n=10000 min=10 max=70 sum=300000 sum_sq=9200000 errors=0 unit=us start_event=sample_begin end_event=sample_end clock=cycle_counter t_ms=10000 seq=4
VAL_BUCKET metric=latency_us le=25 count=1200 t_ms=10000 seq=5
VAL_BUCKET metric=latency_us le=50 count=8600 t_ms=10000 seq=6
VAL_STATS_META metric=latency_us update_cycles_max=80 snapshot_us=200 log_bytes=400 allocation_count=0 isr_log_writes=0 critical_section_us=5 clock=cycle_counter clock_hz=240000000 resolution_ns=4 saturated=0 t_ms=10000 seq=7
VAL_STATS_END metric=latency_us n=10000 dropped=0 elapsed_ms=10000 t_ms=10000 seq=8
```

Accumulators must be O(1), allocation-free, and must not emit from an ISR. Use fixed histogram buckets. Report overflow or saturation. Separate warm-up with `VAL_PHASE name=warmup state=begin|end`; warm-up errors and hard limits still count, while its distribution samples do not.

When warm-up is enabled, distribution metrics declare `phase=steady`. A separate metric used for a hard limit must cover the entire run and declare `scope=all_phases`; this avoids silently excluding warm-up violations while keeping distribution samples separate.

Missing begin/end, non-monotonic or absent `t_ms`, a sequence gap, nonzero dropped count, counter saturation, insufficient samples, an absent `VAL_STATS_END`, inconsistent count/min/max/sum/sum-squares/histogram data, or instrumentation over budget makes affected evidence `BLOCKED`. A completed criterion outside its required threshold is `FAIL`.

Statistical and native metrics declare a `sample_plan`. A calculated plan uses a proportion, mean, or DKW distribution model with confidence and absolute error; an external plan supplies a stable standard reference and minimum sample count. The runner recomputes or reads that minimum and stores it with the criterion result.

Use a single `VAL_STATS`, `VAL_STATS_META`, and `VAL_STATS_END` per metric/window in schema 1.0. Multiple snapshots without distinct window identifiers are ambiguous and therefore blocked. Histogram bucket counts are non-overlapping and must sum to `n`.

User-only observations enter the same raw log through a test-only command and appear as:

```text
VAL_OBSERVATION step=2 observer=user result=pass code=led_green t_ms=900 seq=8
```

Test command parsers and diagnostic wiring must be absent from release firmware.
