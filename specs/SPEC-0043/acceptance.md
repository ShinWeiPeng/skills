## Acceptance Criteria
| ID | Requirements | Criterion | Validation Method | Evidence |
|---|---|---|---|---|
| AC-001 | REQ-001 | 既定 OS 沿用；未定案時提出比較並確認；無多 OS 需求時不強制多平台實作。 | 三類設計正反案例審查；具體檢查映射待討論。 | PASS: artifacts/validation/3e507de0b39d456dacd353005c2aec47/AC-001-review.json |
| AC-002 | REQ-002 | 九項無遺漏；適用項有方法及理由，不適用項有原因；單執行緒、RTOS 及硬即時案例依條件展開，未知資訊不被當作不適用或已驗證。 | 三類設計正反案例、欄位及既有排程規範對照；詳細驗證映射待補。 | PASS: artifacts/validation/3e507de0b39d456dacd353005c2aec47/AC-002-review.json |
| AC-003 | REQ-003 | 對應驗收由 SPEC-0044 的 AC-003 負責。 | 核對分工引用；具體驗收見該 SPEC。 | PASS: artifacts/validation/3e507de0b39d456dacd353005c2aec47/AC-003-review.json |
| AC-004 | REQ-004 | 對應驗收由 SPEC-0044 的 AC-004 負責。 | 核對分工引用；具體驗收見該 SPEC。 | PASS: artifacts/validation/3e507de0b39d456dacd353005c2aec47/AC-004-review.json |
| AC-005 | REQ-005 | 對應驗收由 SPEC-0044 的 AC-005 負責。 | 核對分工引用；具體驗收見該 SPEC。 | PASS: artifacts/validation/3e507de0b39d456dacd353005c2aec47/AC-005-review.json |
| AC-006 | REQ-006 | 對應驗收由 SPEC-0044 的 AC-006 負責。 | 核對分工引用；具體驗收見該 SPEC。 | PASS: artifacts/validation/3e507de0b39d456dacd353005c2aec47/AC-006-review.json |
| AC-007 | REQ-007 | 對應驗收由 SPEC-0044 的 AC-007 負責。 | 核對分工引用；具體驗收見該 SPEC。 | PASS: artifacts/validation/3e507de0b39d456dacd353005c2aec47/AC-007-review.json |
| AC-008 | REQ-008 | 對應驗收由 SPEC-0044 的 AC-008 負責。 | 核對分工引用；具體驗收見該 SPEC。 | PASS: artifacts/validation/3e507de0b39d456dacd353005c2aec47/AC-008-review.json |
| AC-009 | REQ-009 | 對應驗收由 SPEC-0044 的 AC-009 負責。 | 核對分工引用；具體驗收見該 SPEC。 | PASS: artifacts/validation/3e507de0b39d456dacd353005c2aec47/AC-009-review.json |
| AC-010 | REQ-010 | 對應驗收由 SPEC-0044 的 AC-010 負責。 | 核對分工引用；具體驗收見該 SPEC。 | PASS: artifacts/validation/3e507de0b39d456dacd353005c2aec47/AC-010-review.json |
| AC-011 | REQ-011 | 固定與可變條件有對應檢查時機；能力不足、錯誤呼叫環境或不符合等待限制時，不繼續受影響操作且異常可觀測；合法條件可執行，不能臨時替換未確認方法或沿用範例門檻。 | 能力／環境／等待條件設計正反案例、初始化或使用前拒絕與異常契約檢查；工具證據映射待補。 | PASS: artifacts/validation/3e507de0b39d456dacd353005c2aec47/AC-011-review.json |
| AC-012 | REQ-012 | 依階段拆分的執行單元、通道與模組對應可追溯；合併有分析及明確理由，容量及時序要求不因拆分／合併被略過。 | 階段管線與合併設計正反案例、排程及交接成本審查；目標證據依專案。 | PASS: artifacts/validation/3e507de0b39d456dacd353005c2aec47/AC-012-review.json |
| AC-013 | REQ-013 | Task 間資料、事件及訊息通道均可指出 OS 工具與公開契約；越界私有狀態／未宣告全域交接可被指出；OS 相依 API 不外洩至功能契約，工具選擇不省略容量與持有規則。 | 通道盤點、工具能力、資料流／port／所有權及 source review 正反案例。 | PASS: artifacts/validation/3e507de0b39d456dacd353005c2aec47/AC-013-review.json |
| AC-014 | REQ-014 | 各資料／命令／事件／通知通道可表達容量、排序、交付及完成語意；受影響資料的所有權可追溯。滿載、合併及部分處理案例不能誤報完成，故障通知覆寫不清除持續狀態；缺少契約被指出。 | 通道四類設計與容量／合併／逾時／停止／生命週期正反案例，核對已採用資料流與異常規則。 | PASS: artifacts/validation/3e507de0b39d456dacd353005c2aec47/AC-014-review.json |
| AC-015 | REQ-015 | 所有權與共享保護可追溯；持有引用期間不被覆寫／回收，鎖等待與通道交互不造成互等，取消與失敗安全收尾；不符 ISR／時序限制的操作被指出，未因通道或 const 宣稱資料已安全。 | 共享引用、鎖／通道互等、優先權反轉及失敗／逾時／取消正反設計案例；目標時序證據依專案。 | PASS: artifacts/validation/3e507de0b39d456dacd353005c2aec47/AC-015-review.json |
| AC-016 | REQ-016 | 各實際 OS 資源及同時使用的總預算可追溯；未知與實測區分，建立失敗／耗盡有處置與異常；取消／重啟不累積資源，共享資料在用期間不被回收；沒有無界擴容或未確認的配置回退。 | 資源表、容量／建立失敗、共享持有與反覆取消／重啟正反案例；實測證據依專案。 | PASS: artifacts/validation/3e507de0b39d456dacd353005c2aec47/AC-016-review.json |
| AC-017 | REQ-017 | Task 觸發與優先權等參數有推導依據；端到端等待及開銷被納入，平均值不能掩蓋期限違反；候選／分析與實際排程器一致，硬違約與未定義軟容忍不被視為合格；未知或缺少量測不冒充最壞界限。 | 端到端管線、尖峰／慢消費者、分析模型錯配及設計預算／實測區別正反案例；目標時序證據依專案。 | PASS: artifacts/validation/3e507de0b39d456dacd353005c2aec47/AC-017-review.json |
| AC-018 | REQ-018 | 設計交代生命週期擁有者、狀態、順序與就緒／完成語意；實作符合契約，部分初始化失敗、停止逾時及重啟情境不產生使用已釋放資源、舊訊息誤用或資源累積。 | 設計與實作對照；適用的失敗注入、停止／重啟測試及必要目標環境證據；未知證據保持待驗證。 | PASS: artifacts/validation/3e507de0b39d456dacd353005c2aec47/AC-018-review.json |
| AC-019 | REQ-019 | OS 檢查映射可追溯規則、設計版本及 AC，區別三階段與判定方式；必要設計分析不延後至驗收，主機模擬不冒充目標證據，缺失正確阻擋相依工作且未完成整體验收不得標完成。 | 審查 OS 檢查映射與正反案例，涵蓋欄位缺失、實作偏離、測試失敗、目標證據不足與不相依工作可繼續；實際工具及證據入口列於最終驗收計畫。 | PASS: artifacts/validation/3e507de0b39d456dacd353005c2aec47/AC-019-review.json |
| AC-020 | REQ-020 | 平台與執行設計可表達已採用欄位及其適用性；執行設計引用平台、模組及資料流版本，沒有重複手填的來源欄位。未知、不適用、估算及量測可區分，數值單位與依據可追溯。 | 欄位格式及引用正反案例，涵蓋裸機不適用 OS 項目、RTOS／一般 OS 的實際能力、版本不符、漏欄位、未知冒充不適用及數值缺依據；通用解析與版本檢查由 SPEC-0044 提供。 | PASS: artifacts/validation/3e507de0b39d456dacd353005c2aec47/AC-020-review.json |
| AC-021 | REQ-021 | 七組 OS 規則 ID 唯一、強度為 MUST且有適用條件；條文涵蓋前述完整要求，不混入工作流程或重複 OS 隔離條款。未知、不適用與專案數值依據正確處理。 | 對照 REQ-011 至 REQ-018 的完整搬移映射、規則四欄格式檢查、ID 重複檢查及適用／不適用／未知正反案例；各規則實際驗證依 REQ-019 映射。 | PASS: artifacts/validation/3e507de0b39d456dacd353005c2aec47/AC-021-review.json |

## Acceptance Mapping
```json
{
  "AC-001": {
    "evidence_claims": [
      "host-semantics"
    ],
    "rationale": "本次修改主機上的治理規則、文件／來源／版本及執行入口；依 Implementation Plan 對應 AC 正反案例驗證。專案必要的 OS 目標證據義務仍保留，主機 fixture 不代替產品實機證據。"
  },
  "AC-002": {
    "evidence_claims": [
      "host-semantics"
    ],
    "rationale": "本次修改主機上的治理規則、文件／來源／版本及執行入口；依 Implementation Plan 對應 AC 正反案例驗證。專案必要的 OS 目標證據義務仍保留，主機 fixture 不代替產品實機證據。"
  },
  "AC-003": {
    "evidence_claims": [
      "host-semantics"
    ],
    "rationale": "本次修改主機上的治理規則、文件／來源／版本及執行入口；依 Implementation Plan 對應 AC 正反案例驗證。專案必要的 OS 目標證據義務仍保留，主機 fixture 不代替產品實機證據。"
  },
  "AC-004": {
    "evidence_claims": [
      "host-semantics"
    ],
    "rationale": "本次修改主機上的治理規則、文件／來源／版本及執行入口；依 Implementation Plan 對應 AC 正反案例驗證。專案必要的 OS 目標證據義務仍保留，主機 fixture 不代替產品實機證據。"
  },
  "AC-005": {
    "evidence_claims": [
      "host-semantics"
    ],
    "rationale": "本次修改主機上的治理規則、文件／來源／版本及執行入口；依 Implementation Plan 對應 AC 正反案例驗證。專案必要的 OS 目標證據義務仍保留，主機 fixture 不代替產品實機證據。"
  },
  "AC-006": {
    "evidence_claims": [
      "host-semantics"
    ],
    "rationale": "本次修改主機上的治理規則、文件／來源／版本及執行入口；依 Implementation Plan 對應 AC 正反案例驗證。專案必要的 OS 目標證據義務仍保留，主機 fixture 不代替產品實機證據。"
  },
  "AC-007": {
    "evidence_claims": [
      "host-semantics"
    ],
    "rationale": "本次修改主機上的治理規則、文件／來源／版本及執行入口；依 Implementation Plan 對應 AC 正反案例驗證。專案必要的 OS 目標證據義務仍保留，主機 fixture 不代替產品實機證據。"
  },
  "AC-008": {
    "evidence_claims": [
      "host-semantics"
    ],
    "rationale": "本次修改主機上的治理規則、文件／來源／版本及執行入口；依 Implementation Plan 對應 AC 正反案例驗證。專案必要的 OS 目標證據義務仍保留，主機 fixture 不代替產品實機證據。"
  },
  "AC-009": {
    "evidence_claims": [
      "host-semantics"
    ],
    "rationale": "本次修改主機上的治理規則、文件／來源／版本及執行入口；依 Implementation Plan 對應 AC 正反案例驗證。專案必要的 OS 目標證據義務仍保留，主機 fixture 不代替產品實機證據。"
  },
  "AC-010": {
    "evidence_claims": [
      "host-semantics"
    ],
    "rationale": "本次修改主機上的治理規則、文件／來源／版本及執行入口；依 Implementation Plan 對應 AC 正反案例驗證。專案必要的 OS 目標證據義務仍保留，主機 fixture 不代替產品實機證據。"
  },
  "AC-011": {
    "evidence_claims": [
      "host-semantics"
    ],
    "rationale": "本次修改主機上的治理規則、文件／來源／版本及執行入口；依 Implementation Plan 對應 AC 正反案例驗證。專案必要的 OS 目標證據義務仍保留，主機 fixture 不代替產品實機證據。"
  },
  "AC-012": {
    "evidence_claims": [
      "host-semantics"
    ],
    "rationale": "本次修改主機上的治理規則、文件／來源／版本及執行入口；依 Implementation Plan 對應 AC 正反案例驗證。專案必要的 OS 目標證據義務仍保留，主機 fixture 不代替產品實機證據。"
  },
  "AC-013": {
    "evidence_claims": [
      "host-semantics"
    ],
    "rationale": "本次修改主機上的治理規則、文件／來源／版本及執行入口；依 Implementation Plan 對應 AC 正反案例驗證。專案必要的 OS 目標證據義務仍保留，主機 fixture 不代替產品實機證據。"
  },
  "AC-014": {
    "evidence_claims": [
      "host-semantics"
    ],
    "rationale": "本次修改主機上的治理規則、文件／來源／版本及執行入口；依 Implementation Plan 對應 AC 正反案例驗證。專案必要的 OS 目標證據義務仍保留，主機 fixture 不代替產品實機證據。"
  },
  "AC-015": {
    "evidence_claims": [
      "host-semantics"
    ],
    "rationale": "本次修改主機上的治理規則、文件／來源／版本及執行入口；依 Implementation Plan 對應 AC 正反案例驗證。專案必要的 OS 目標證據義務仍保留，主機 fixture 不代替產品實機證據。"
  },
  "AC-016": {
    "evidence_claims": [
      "host-semantics"
    ],
    "rationale": "本次修改主機上的治理規則、文件／來源／版本及執行入口；依 Implementation Plan 對應 AC 正反案例驗證。專案必要的 OS 目標證據義務仍保留，主機 fixture 不代替產品實機證據。"
  },
  "AC-017": {
    "evidence_claims": [
      "host-semantics"
    ],
    "rationale": "本次修改主機上的治理規則、文件／來源／版本及執行入口；依 Implementation Plan 對應 AC 正反案例驗證。專案必要的 OS 目標證據義務仍保留，主機 fixture 不代替產品實機證據。"
  },
  "AC-018": {
    "evidence_claims": [
      "host-semantics"
    ],
    "rationale": "本次修改主機上的治理規則、文件／來源／版本及執行入口；依 Implementation Plan 對應 AC 正反案例驗證。專案必要的 OS 目標證據義務仍保留，主機 fixture 不代替產品實機證據。"
  },
  "AC-019": {
    "evidence_claims": [
      "host-semantics"
    ],
    "rationale": "本次修改主機上的治理規則、文件／來源／版本及執行入口；依 Implementation Plan 對應 AC 正反案例驗證。專案必要的 OS 目標證據義務仍保留，主機 fixture 不代替產品實機證據。"
  },
  "AC-020": {
    "evidence_claims": [
      "host-semantics"
    ],
    "rationale": "本次修改主機上的治理規則、文件／來源／版本及執行入口；依 Implementation Plan 對應 AC 正反案例驗證。專案必要的 OS 目標證據義務仍保留，主機 fixture 不代替產品實機證據。"
  },
  "AC-021": {
    "evidence_claims": [
      "host-semantics"
    ],
    "rationale": "本次修改主機上的治理規則、文件／來源／版本及執行入口；依 Implementation Plan 對應 AC 正反案例驗證。專案必要的 OS 目標證據義務仍保留，主機 fixture 不代替產品實機證據。"
  }
}
```

