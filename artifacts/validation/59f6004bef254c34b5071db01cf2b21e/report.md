# 安裝後驗證

測試版：0.19.0+codex.local-20260920045258486235。

已直接載入安裝快取的 spec_contract.py 執行 11 項既有回歸斷言；詳見 installed-consolidation.log。實際執行來源與安裝版 acceptance CLI，退出碼及結果詳見 checks.json。

{
  "installed_file_mismatches": [
    "skills\\spec-governance\\scripts\\__pycache__\\spec_contract.cpython-312.pyc"
  ],
  "same_acceptance_verdict": true,
  "installed_acceptance_verdict": "BLOCKED",
  "errors": [
    "AC-001: evidence claims and applicability rationale required"
  ],
  "checked_files": 296
}

整體驗收仍 BLOCKED。21 項 AC 派生內容未包含逐項 selectors；不可把 CLI 預期拒絕當成 AC 驗收通過。正式版與測試版都啟用，四個測試版 hook 設定停用，故不能建立隔離測試版的真實 hook 觸發證據。本次未更改信任或 hook 啟用設定。Windows 安裝成功不能作為 Linux desktop 安裝證據。

SPEC-0036 維持 r61 confirmed；未修改產品或正式驗收定義。先前完整 423 項回歸證據保留於原固定 run，本次補足已安裝內容測試。
