# memory-management

| Rule ID | Strength | Applicable conditions | Program requirement |
|---|---|---|---|
| MEM-ALLOC-001 | MUST | 有資源或時間限制的配置路徑 | 配置及釋放符合容量與期限；無法滿足時使用符合限制的預配置、固定容量或適當池，耗盡時不得回退到違反限制的配置。 |
| MEM-CAP-001 | MUST | 有限 buffer、queue、pool | 容量及耗盡行為有明確契約；不得無界擴容或覆寫仍使用的資料。 |
| MEM-OWNER-001 | MUST | 資源及共享資料生命週期 | 預設單一擁有者；轉移、借用、共享明定存活、權限、同步及回收，不將共享存活當共同寫入權。 |
| MEM-LIFE-001 | MUST | 成功、失敗、取消、逾時與非同步持有 | 所有退出路徑均有資源收尾；持有未解除前不得釋放或重用，逾時本身不代表使用已結束。 |
