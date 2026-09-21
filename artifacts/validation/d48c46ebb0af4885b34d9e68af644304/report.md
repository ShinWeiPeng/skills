# 測試版接續驗證結果

測試版 `0.19.0+codex.local-20260920045258486235` 的安裝清單 294 檔逐一 SHA-256 核對通過。前次掃描的唯一差異是執行 Python 後產生的 .pyc 快取，不屬交付清單，不是來源檔差異。

直接載入安裝版 spec_contract 執行 11 項既有回歸測試全部通過，Windows 真實 Python acceptance CLI 已執行；來源與安裝版同為退出碼 2 / BLOCKED，原因一致。詳見 ../59f6004bef254c34b5071db01cf2b21e/ 的固定報告及原始輸出。這些是 CLI／契約證據，不代表宿主 hooks 觸發。

仍缺三項：

1. SPEC-0036 的 21 項 AC 缺少工具可讀 selectors，第一個診斷是 AC-001 evidence claims and applicability rationale required。應依已確認的主機驗證計畫补入逐項 evidence_claims、contract_dimensions、rationale，再從 SPEC 派生；不能直接改派生檔作第二份來源。修訂按已採納規則撤銷舊授權，不能冒稱維持 r61 又已完成欄位修補。本輪未修訂。
2. 正式版、測試版同時 enabled，測試版四個 hooks 為 disabled。完整真實宿主測試須先隔離測試版，經宿主正常信任／啟用流程啟用 hooks，再於新的測試任務取得 SessionStart、UserPromptSubmit、PreToolUse、Stop 原始事件和來源綁定。不直接填入信任雜湊，也不以手動呼叫 hook 冒充宿主事件。
3. 本機 WSL 探測失敗，原始輸出見 linux-probe.txt；Linux desktop 的終端開啟、結果顯示及等待關閉尚無可執行環境。Windows 成功不替代此項。

整體結果：BLOCKED（條件／證據不足），並非執行了 HIL 後失敗。既有 423 項來源回歸不重複計數；本輪新增安裝版 11 項測試證據。SPEC-0036 維持 r61 confirmed，授權相容檢查保留原授權；本輪未更改產品程式、SPEC 要求或 hooks 信任。
