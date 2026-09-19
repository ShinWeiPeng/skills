# SPEC-0032 後續修正驗證

規格：[SPEC-0032 保留 SPEC 同步檢查並解除討論與修復阻擋](C:/Users/hugo_peng/skill/skills/specs/SPEC-0032-recoverable-spec-sync.md)，修訂 6（修訂 4 授權範圍的完成紀錄）。

本次使用者已對修訂 4 明確說「開始執行」。修改前快照保存在 spec-governance/followup-before，保留既有未提交內容，未提交或發布。

## 已完成的修正

- REQ-009：前置 SPEC 必須唯一且 implemented；檢查多層相依與循環，不暫停無關任務。
- REQ-010：使用程序退出即釋放的 OS 鎖；狀態 CAS 與檔案提交只持短鎖，耗時驗證在鎖外。
- REQ-011：提供 before_content 時整合不重疊變更，最多三次提交；候選驗證器須回傳精確 hash 的 PASS。缺驗證器或衝突時回傳候選供檢查，原檔不變。一般 apply 與 recover 均支援。
- REQ-012：SPEC 編號掃描與建立序列化，並行建立不重號。
- REQ-013：快取綁定驗證階段、輸入、檢查與成功條件；納入 validation 與 architecture 設定雜湊。
- REQ-014：新綁定須先確認有效授權，才能開始新恢復週期，舊週期保留於歷史。
- REQ-015：router 保留 pending 與恢復資訊；finish-turn 解析失敗回報缺口並允許回合正常結束。
- REQ-016：技能及文件要求每次保存貼 canonical 連結、修訂、狀態、摘要與授權；已呈現規格的程式檢查加入可見修訂與狀態驗證。

## 驗證狀態

| 驗證 | 證據 |
|---|---|
| 來源組裝：291 檔案，PASS | [manifest](C:/Users/hugo_peng/skill/skills/artifacts/tests/25c098df7acc4214b80e888a0905229f/manifest.json) · [stdout](C:/Users/hugo_peng/skill/skills/artifacts/tests/25c098df7acc4214b80e888a0905229f/stdout.log) · [stderr](C:/Users/hugo_peng/skill/skills/artifacts/tests/25c098df7acc4214b80e888a0905229f/stderr.log) |
| Plugin：337 項全部通過 | [manifest](C:/Users/hugo_peng/skill/skills/artifacts/tests/20458e27688b42a29cc281f8902c0a30/manifest.json) · [stdout](C:/Users/hugo_peng/skill/skills/artifacts/tests/20458e27688b42a29cc281f8902c0a30/stdout.log) · [stderr](C:/Users/hugo_peng/skill/skills/artifacts/tests/20458e27688b42a29cc281f8902c0a30/stderr.log) |
| Distribution：39 項，37 通過、2 平台跳過 | [manifest](C:/Users/hugo_peng/skill/skills/artifacts/tests/a10be2a89c794407aacdc713c9c09407/manifest.json) · [stdout](C:/Users/hugo_peng/skill/skills/artifacts/tests/a10be2a89c794407aacdc713c9c09407/stdout.log) · [stderr](C:/Users/hugo_peng/skill/skills/artifacts/tests/a10be2a89c794407aacdc713c9c09407/stderr.log) |
| 架構 development：PASS，保留 SHOULD 建議 | [manifest](C:/Users/hugo_peng/skill/skills/artifacts/tests/d5b01298d9c64ee0aac5998e613389d0/manifest.json) · [stdout](C:/Users/hugo_peng/skill/skills/artifacts/tests/d5b01298d9c64ee0aac5998e613389d0/stdout.log) · [stderr](C:/Users/hugo_peng/skill/skills/artifacts/tests/d5b01298d9c64ee0aac5998e613389d0/stderr.log) |
| 格式：7 檔案通過 | [manifest](C:/Users/hugo_peng/skill/skills/artifacts/tests/7bb2b007e7a7488a9268c190372b42b1/manifest.json) · [stdout](C:/Users/hugo_peng/skill/skills/artifacts/tests/7bb2b007e7a7488a9268c190372b42b1/stdout.log) · [stderr](C:/Users/hugo_peng/skill/skills/artifacts/tests/7bb2b007e7a7488a9268c190372b42b1/stderr.log) |
| Lint：無新增問題；原有 4 項保留 | [manifest](C:/Users/hugo_peng/skill/skills/artifacts/tests/9272eb125e084743b355e9d46d075c52/manifest.json) · [stdout](C:/Users/hugo_peng/skill/skills/artifacts/tests/9272eb125e084743b355e9d46d075c52/stdout.log) · [stderr](C:/Users/hugo_peng/skill/skills/artifacts/tests/9272eb125e084743b355e9d46d075c52/stderr.log) |
| git diff --check：PASS | [manifest](C:/Users/hugo_peng/skill/skills/artifacts/tests/b73d0b809e5946f4a1c41e3de6c99f71/manifest.json) · [stdout](C:/Users/hugo_peng/skill/skills/artifacts/tests/b73d0b809e5946f4a1c41e3de6c99f71/stdout.log) · [stderr](C:/Users/hugo_peng/skill/skills/artifacts/tests/b73d0b809e5946f4a1c41e3de6c99f71/stderr.log) |

## 安裝與限制

本機測試版：`0.16.0+codex.local-20260919043342659436`。已安裝 292 檔案（含 inventory），與最終組裝檔案逐一雜湊一致；12 個核心來源／安裝檔案比對一致。
[安裝清單核對](C:/Users/hugo_peng/skill/skills/spec-governance/SPEC-0032-followup-installed-inventory.json) · [核心來源與 hooks 狀態](C:/Users/hugo_peng/skill/skills/spec-governance/SPEC-0032-followup-installed-test-version.json)

Distribution 測試會重建 dist；安裝前已恢復完整 291 檔案候選，正式內容 fingerprint 與 Plugin 測試使用版本一致：`sha256:6eee71009d80f8447f9e9ce18d6b7e6340132c950022f266f4ae264944834a04`。localize 僅刷新本機快取版本與其 inventory。

四個本機 hooks 維持關閉，未改動 trust、未提交或發布。新任務才會載入更新技能。

[正式 acceptance 結果](C:/Users/hugo_peng/skill/skills/spec-governance/SPEC-0032-followup-acceptance.json) 與本次 host 測試結果分開呈現。run-reference 尚未提供正式分層 acceptance 證據；真正 Codex hook firing 未驗證。SPEC 維持 confirmed，不宣稱 implemented。雙軸審查的具體問題均已修正，無已知剩餘程式阻擋。
