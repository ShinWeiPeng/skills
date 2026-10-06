# data-flow

| Rule ID | Strength | Applicable conditions | Program requirement |
|---|---|---|---|
| FLOW-INPUT-001 | MUST | Command admission. | Use a typed input contract; validate syntax and admission conditions before acceptance. Reject unaccepted work immediately with a defined invalid/busy/unavailable result. |
| FLOW-OUTPUT-001 | MUST | Functional module notifications. | A functional module exposes one output sink. It does not own a subscriber collection. The parent or an adapter implements fan-out to zero or more subscribers. |
| FLOW-FANOUT-001 | MUST | Parent or adapter event fan-out. | invoke subscribers outside the producer's internal lock; |
| FLOW-FANOUT-002 | MUST | Parent or adapter event fan-out. | continue after one subscriber fails; |
| FLOW-FANOUT-003 | MUST | Parent or adapter event fan-out. | preserve deterministic configured order within a stream; |
| FLOW-FANOUT-004 | MUST | Parent or adapter event fan-out. | aggregate failures and publish them to the parent's error port; |
| FLOW-FANOUT-005 | MUST | Parent or adapter event fan-out. | avoid pretending that completed callbacks can be rolled back. |
| FLOW-EVENT-001 | MUST | Cross-module events; apply delivery/clock/stream conditions stated in the contract. | Every cross-module event MUST declare these fields: - `event_type` - `source` - `correlation_id` - `stream_id` - `sequence` - `payload` Timestamps are optional when no trustworthy clock exists. Persistent event IDs and retry metadata become mandatory for at-least-once delivery. |
| FLOW-LIFE-001 | MUST | Cross-module events; apply delivery/clock/stream conditions stated in the contract. | Core states: `received -> validated -> processing -> succeeded &#124; failed` Reliability extension: `accepted -> retrying -> cancelled &#124; dead-letter` The producer MUST commit its state before publishing success or failure. Processing of the same stream is serialized and non-reentrant. Different streams MAY run concurrently. |
| FLOW-DELIVERY-001 | MUST | Cross-module events; apply delivery/clock/stream conditions stated in the contract. | Every event contract declares `at-most-once` or `at-least-once`. - Use `at-most-once` by default for in-process callbacks without retries. - Use `at-least-once` when retries or persistence are enabled. Require a persistent event ID and an idempotency strategy. - Do not claim exactly-once delivery without a project-specific proof and accepted ADR. |
| FLOW-BOUND-001 | MUST | 跨執行單元或內外部介面資料傳遞 | 每層及在途容量有界；接收、拒絕、部分完成、持有與釋放符合契約，不能藉重複 bank 隱藏無界積壓。 |
| FLOW-BATCH-001 | MUST | 已選聚合的路徑 | 達容量門檻或最長等待時間任一條件即觸發送出嘗試，仍遵守背壓及期限；觸發不等於已交付。 |
| FLOW-STOP-001 | MUST | 資料流 Stop | 停止新接收；若有已接受資料，在專案指定期限內排空，逾期回報未完成並安全取消；仍被持有資料不得提前回收，停止期限不等於底層已釋放。 |
| FLOW-FANIN-001 | MUST | 本規範所述多命令來源交同一內部執行單元 | 輸入紀錄包含來源；以 mutex 保護 sequence／接收排序所需共享狀態；編號與入列符合所宣告順序，回覆可關聯來源；mutex 不等於公平性。 |
| FLOW-FANOUT-006 | MUST | 同資料頻率的多介面輸出 | 各分支取得契約要求的資料頻率，慢分支不阻塞其他分支；各自有容量與用途相符的跳過/停止政策、缺口及異常可觀測性。 |
| FLOW-SHARE-001 | MUST | 多消費者共享資料 | 發布、讀取、持有與回收同步明確，任何讀者仍使用時不得重用；慢讀者不使保留量無界增長。 |
| FLOW-SOURCE-001 | MUST | 來源不能暫停或硬體需 bank | 明定不可回壓位置的耗盡、缺口或停止處置；硬體 bank 的容量、複製及所有權符合限制，不能把有 bank 視為已有背壓。 |
