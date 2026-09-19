# Native evidence providers

- `etw-wpr`: Windows ETW/WPR for scheduler, context-switch, CPU, waits, memory, I/O, and networking. Native artifacts are ETL plus a bounded export usable by the evaluator.
- `perf-ftrace`: Linux perf and tracefs/ftrace scheduler events such as `sched_switch` and `sched_waking`. Preserve trace-loss counters and a text/JSON export.
- `instruments-xctest`: iOS Instruments, xctrace, XCTest metrics, and os_signpost. When Codex is not running on macOS, generate guided capture/export steps for the user.
- `structured-log`: application events and O(1) statistics for bare-metal targets or an explicitly allowed fallback.

Native traces are authoritative for scheduler/resource criteria. Application events are authoritative for domain semantics. Correlate both with a run ID and monotonic markers. If correlation is required but missing, return `BLOCKED`; never choose whichever source gives the more favorable result.

If a required Windows, Linux, or iOS native provider is unavailable, return `BLOCKED`. Structured application logs remain valid for domain semantics but cannot pass scheduler, CPU, memory, I/O, or network resource criteria. Bare-metal and custom targets may use structured logs and O(1) statistics as their selected provider.

## Profile action examples

Declare native commands as bounded executable-plus-argv actions and review them for the installed tool version before execution. Because WPR start is asynchronous, wrap Windows start/workload/size-monitor/stop in one reviewed foreground helper and expose it as `trace_role: record`; a raw `wpr -start` action is rejected. Typical Linux phases use `perf sched record -o <perf.data> -- <declared workload>` and `perf script -i <perf.data>`. Typical iOS phases use `xcrun xctrace record` and a separate `xcrun xctrace export` action on macOS.

These are patterns, not permission to invent a workload, provider profile, process scope, or output path. Put the exact reviewed argv in the target project's profile. Mark native capture actions with `risk: trace`, the appropriate `trace_role`, a monitored `bounded_artifact`/`max_artifact_bytes` for start or record, and an idempotent stop/cancel cleanup. Administrator/root/Developer Mode remains an explicit approval boundary. If trace approval is withheld, record the decision and return `BLOCKED` for affected native-resource criteria.
