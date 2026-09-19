# SPEC-0032 模組契約與 SIL 驗收

2026-09-19：依使用者「繼續測試」執行。真實 Codex Desktop hooks 觸發測試依使用者決定不執行，四個開發版 hooks 確認維持 false。

規格：[SPEC-0032](C:/Users/hugo_peng/skill/skills/specs/SPEC-0032-recoverable-spec-sync.md)，revision 6、confirmed。本輪沒有修改 SPEC 或產品程式，也沒有重新安裝插件。

## 實測結果

- Plugin 回歸 337 項全部通過，0 失敗；耗時 34.655 秒。
- 15 項 AC 各有 module-contract / SIL 紀錄，共 30 筆 PASS。
- 兩層共用同一次測試：公共 API 斷言提供模組契約證據；正式 discussion/router/delivery 程式搭配隔離檔案及驗證替身提供 SIL 證據。程序崩潰、鎖及並行案例使用實際子程序。不是兩次獨立執行，也不是真實 Desktop 觸發。
- 測試輸出逐項核對成功名稱，AC 對應保存在 coverage.json。證據收集時重新比對來源快照，並綁定当前規劃、設定文件與 SPEC revision 6。

[原始測試輸出](C:/Users/hugo_peng/skill/skills/artifacts/tests/b56288863d37458cbee8add0cba5a814/stderr.log) · [測試 manifest](C:/Users/hugo_peng/skill/skills/artifacts/tests/b56288863d37458cbee8add0cba5a814/manifest.json)

[分層 manifest](C:/Users/hugo_peng/skill/skills/artifacts/validation/234c976476094b9b9c5f136f663567a2/manifest.json) · [AC 覆蓋對應](C:/Users/hugo_peng/skill/skills/artifacts/validation/234c976476094b9b9c5f136f663567a2/coverage.json) · [分層證據](C:/Users/hugo_peng/skill/skills/artifacts/validation/234c976476094b9b9c5f136f663567a2/evidence.json)

## 保留的限制

正式整體 acceptance 為 BLOCKED，而非測試 FAIL：

- AC-005 adapter-contract：真實宿主測試依使用者決定不執行，沒有偽造通過或移除原規格門檻。
- AC-008：包含 distribution、架構、格式與真正宿主觸發的綜合驗收；本輪僅重跑 Plugin 主機回歸，不宣稱這項完整通過。先前其他檢查結果見 followup-evidence.md。

[正式驗收結果](C:/Users/hugo_peng/skill/skills/spec-governance/SPEC-0032-layered-acceptance.json)。本輪未將 canonical AC Evidence 改為 PASS，也未將 SPEC 狀態改為 implemented。
