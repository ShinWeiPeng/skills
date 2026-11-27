---
spec_version: 1
spec_id: SPEC-0068
revision: 3
status: confirmed
change_set: governed-engineering-claude-code-support
branch_ref: feat/claude-code-support
---
# Governed Engineering Skills 支援 Claude Code

## Problem
governed-engineering-skills 的技能內容、安裝程式與問答契約以 Codex 為前提：

- 安裝程式（Windows `.cmd`/`install-marketplace.ps1`、Linux `.sh`/`.desktop`/`install-marketplace.sh`）只安裝 Codex CLI 與 `governed-engineering` Codex Marketplace，結束訊息也只提 Codex。
- `.claude-plugin/plugin.json` 的 `repository` 指向上游 `https://github.com/mattpocock/skills`，而實際來源是 `ShinWeiPeng/skills`。
- 技能 Markdown 以 Codex 的 `$skill-name` 語法呼叫其他技能（`skills/` 內 23 個檔案共約 51 處，另有 `docs/engineering/*.md` 頁面與 4 個測試檔斷言這些字串）。Claude Code 不認得 `$name`，`$` 前綴會被當成一般文字或變數。
- ask-matt `decision-question-contract.md`、spec-governance `SKILL.md` 與 `scripts/spec_contract.py` 的問答介面只列出 Codex 的 `request_user_input` / `request_user_input_async`，沒有 Claude Code 的 `AskUserQuestion`，所以 Claude Code 回報這個介面時，`question-policy` 會因介面不明而拒絕。
- 技能說明文字把執行者寫成「Codex」，例如「Codex 執行／Codex 無法操作」（clarify-improvement-proposals、validate-on-device、engineering-risk-routing、govern-modular-event-architecture 等）。
- README 的安裝與使用說明只寫 Codex。
- 另外，doc-coauthoring 的 `SKILL.md` 有兩句不通順的文字：「the platform web app web interface」與「What would they type into the platform web app?」。

## Solution
在不改變 Codex 行為與既有治理語意的前提下，加入 Claude Code 這個平行平台：

1. **安裝程式**：新增目標選擇 `codex`、`claude`、`both`。PowerShell 用 `-Target`，sh 用 `--target=`。雙擊互動時以編號詢問，非互動且未指定時預設 `codex`，維持現有行為。Claude 路徑：確認 `claude` CLI 存在，然後新增或更新 repository-root 的 Claude Marketplace（`ShinWeiPeng/skills`，marketplace 名稱 `mattpocock`），再安裝 `mattpocock-skills@mattpocock` 並確認已安裝。實作前以 `claude plugin --help` 等實際輸出核對子命令與參數，不憑記憶。啟動器結束訊息依目標顯示。
2. **Claude manifest**：`repository` 改為 `https://github.com/ShinWeiPeng/skills`。
3. **中性技能呼叫**：技能與 docs 頁面中的 `` `$skill-name` `` 一律改為 `` the `skill-name` skill ``（例如「invoke the `engineering-risk-routing` skill」）；ask-matt 的 `` `/formatter-governance` `` 也一併改寫。frontmatter `description` 內的引用同樣改寫。Codex 專用的 `plugins/governed-engineering-skills/.codex-plugin/plugin.json` `defaultPrompt` 保留 `$` 語法，因為那是 Codex 原生介面。斷言舊字串的測試同步更新。
4. **AskUserQuestion 對應**：`AskUserQuestion` 加為合法問答介面，並與 `request_user_input*` 一樣正規化為 `structured-menu`。**政策不變**：Default／未知模式一律不得使用選單，只有已啟用的 Plan 模式且主機允許時才可使用；失敗、重試紀錄也以 `structured-menu` 共用。文件改為列出兩個平台的工具名稱，並新增 Claude 介面在允許與拒絕兩種情況的測試。
5. **執行者中性化**：技能內容中把「Codex」當執行者的句子改為「the agent」。下列內容不改：功能性路徑（`.codex/on-device.local.yaml`、managed-delivery 的 `.codex` 排除規則）、`architecture/` 下的歷史 ADR／ALG 紀錄、ask-matt `PHASE-BOUNDARIES.md` 中已中性的「Claude → Codex」範例，以及 Codex manifest。
6. **文件與路由**：README 新增 Claude Code 安裝段落（啟動器的目標選擇、手動 `claude plugin` 指令），`/setup-matt-pocock-skills` 說明改為適用兩個平台。依 CLAUDE.md 的規定重新檢查 ask-matt 路由，確認沒有殘留平台專屬的呼叫寫法。
7. **Changeset**：engineering 套件新增 `plugins/governed-engineering-skills/.changeset/claude-code-support.md`（minor）。doc-coauthoring 修正兩句文字，另附 `doc-coauthoring/.changeset/*.md`（patch）。CHANGELOG 由 Version PR 依 changeset 產生，本 PR 不直接修改。
8. **登記**：在 `.github/validation/layout.yaml` 把本 SPEC 登記為 specification。只以部分暫存（`git add -p`）加入這一行，使用者在工作區尚未提交的其他修改不暫存、不改動。

## User Stories
- Claude Code 使用者雙擊啟動器、選擇 Claude Code 或兩者，就能安裝並使用同一套治理技能。
- 在 Claude Code 中，技能之間的交接文字可以直接讀懂，也能用 Skill 工具呼叫，不會出現 Codex 專用的 `$` 語法。
- 在 Claude Code 的 Plan 模式中，`AskUserQuestion` 依相同政策被允許；在 Default 模式中被拒絕。
- 既有 Codex 使用者的安裝、呼叫與問答行為不變。

## Requirements
| ID | Requirement |
| --- | --- |
| REQ-001 | Windows 與 Linux 安裝程式支援 `codex`／`claude`／`both`，提供互動選擇與 CLI 參數。非互動未指定時為 `codex`。Claude 路徑不自動安裝 Claude Code，缺少 CLI 時給出可操作的診斷並回傳非零退出碼（DEC-002）。`both` 中任一目標失敗時，回報並保留原始退出碼。 |
| REQ-002 | `.claude-plugin/plugin.json` 的 `repository` 為 `https://github.com/ShinWeiPeng/skills`，並通過 `claude plugin validate . --strict`。 |
| REQ-003 | 已推廣的 `skills/engineering`、`skills/productivity` 與 `docs/` 中，不再以 `$skill-name` 呼叫技能，改用中性寫法。Codex manifest 保持原樣。 |
| REQ-004 | spec-governance 的 `question-policy` 及問答紀錄接受 `AskUserQuestion`，並視為 `structured-menu`。模式政策、失敗介面封鎖與重試語意都不變。 |
| REQ-005 | 技能說明不再把 Codex 當成唯一執行者；功能性路徑、歷史架構紀錄與 Codex manifest 不變。 |
| REQ-006 | README、ask-matt 路由與 changeset（engineering minor、doc-coauthoring patch）同步更新；doc-coauthoring 的兩句文字修正為通順的英文。 |
| REQ-007 | 只暫存本次明確檢視過的路徑；不使用 `git add -A`、不修改 consumer 分支、不改動使用者在工作區尚未提交的修改。 |

## Acceptance Criteria
| ID | Criterion | Requirements | Validation Method | Expected Output / Pass condition | Evidence |
| --- | --- | --- | --- | --- | --- |
| AC-001 | 安裝程式的目標選擇、預設值與失敗處理正確。 | REQ-001 | 以假的 `codex`／`claude` 命令（mock）執行 ps1 與 sh 的每個目標、缺 CLI、無效參數、`both` 部分失敗等情況；在現有安裝程式測試中新增案例。 | 每個目標呼叫的命令序列正確，退出碼正確；真實 Claude Code 安裝標記為 NOT RUN（本機沒有 `claude` CLI）。 | PASS（mock）：Windows PowerShell 測試覆蓋 Claude 目標的 add、update、衝突與缺少 CLI；WSL Ubuntu 24.04 上的 POSIX 測試覆蓋 claude／both／無效目標（Codex 舊測試以 python3 代替 node）。真實 Claude Code 安裝：NOT RUN。 |
| AC-002 | Claude manifest 有效，且只列出已推廣的技能。 | REQ-002 | `claude plugin validate . --strict`；`python scripts/validate_distribution.py`。 | 兩者皆通過。若本機沒有 `claude` CLI，validate 結果標記為 NOT RUN，並請使用者執行。 | `validate_distribution.py` PASS；`claude plugin validate . --strict`：NOT RUN（本機沒有 `claude` CLI）。 |
| AC-003 | 已推廣的技能與 docs 中沒有殘留的 `$skill-name`。 | REQ-003 | 以 grep 搜尋 `` `\$[a-z][a-z0-9-]+` `` 並比對技能名稱清單；執行更新後的技能契約測試。 | 除 Codex manifest 外沒有命中，測試通過。 | PASS：已推廣技能、docs 與 README 中 `$skill-name` 命中數為 0；相關技能契約測試通過。 |
| AC-004 | `AskUserQuestion` 的政策與既有介面一致。 | REQ-004 | 新增單元測試：Plan 模式且允許時通過；Default／未知模式拒絕；`presentation-failed` 之後封鎖 `structured-menu`；`retry-requested` 之後解除封鎖。 | 全部通過，既有 `request_user_input*` 測試不變。 | PASS：`QuestionPresentationTests` 16 項全過，含新增的 AskUserQuestion 允許、拒絕、失敗與重試案例。 |
| AC-005 | 執行者已中性化，且例外範圍正確。 | REQ-005 | 以 grep 搜尋 `Codex` 並逐一檢視剩餘命中。 | 剩餘命中只屬於 Solution 第 5 點列出的例外。 | PASS：剩餘 `Codex` 只出現在 PHASE-BOUNDARIES 範例、問答工具名稱說明、核准者禁止名單說明，以及 architecture 歷史紀錄。 |
| AC-006 | 套件整體驗證通過。 | REQ-006, REQ-007 | `python .github/scripts/prepare_validation.py`；跨套件 unittest；`python governed-engineering-skills/scripts/assemble_plugin.py rehearse`；engineering 套件測試；`git diff --cached --stat` 檢查暫存範圍。 | 全部通過；暫存內容只有本次變更，`layout.yaml` 只多一行 SPEC-0068。 | 跨套件 72 項 OK；`rehearse` PASS；兩個套件的版本檢查 PASS；distribution 42 項 OK。其他套件的失敗在乾淨 HEAD 上同樣出現（5 MB 邊界、ladder、architecture setUpClass），或屬於 Windows 上的偶發失敗（單獨重跑皆通過）。 |

## Relationships
| Source | Relation | Target |
| --- | --- | --- |
| REQ-001 | refines | SPEC-0013 |
| REQ-006 | refines | SPEC-0064 |

## Out of Scope
- 不改名 Claude plugin（`mattpocock-skills`），也不改 marketplace 名稱（`mattpocock`），依 DEC-001 維持原名。
- 不修改 Codex manifest、`marketplace-release`／`plugin-release/*` consumer 分支、已發布的 tag，也不發布 release。
- 不改寫 `architecture/` 下的歷史決策紀錄。
- 不調整 Default 模式的選單政策。
- 不在使用者的真實 profile 上做 Claude Code 安裝驗收。

## Decisions
| ID | Decision | Source |
| --- | --- | --- |
| DEC-001 | `.claude-plugin/plugin.json` 與根目錄 `marketplace.json` 只改 `repository` 與 `description` 措辭；`name`、`author`、`homepage` 維持原樣，保留 `mattpocock-skills@mattpocock` 安裝 ID。 | user:manifest-fields |
| DEC-002 | 缺少 `claude` CLI 時不自動安裝，顯示官方安裝說明並以非零退出碼結束。 | user:missing-claude-cli |
| DEC-003 | Claude plugin 版本由 `1.3.1` 升到 `1.4.0`（與 OpenAI Plugin SemVer 互相獨立）。 | user:claude-plugin-version |
| DEC-004 | 將 `claude` 加入 6 份 `BANNED_AI_APPROVERS`，並同步 manifest-schema 文件說明；新增對應測試。 | user:banned-approvers |
| DEC-005 | 使用者檢視第 2 版規格後明確指示「開始執行」。 | user:start-execution |

## Open Decisions
None.

## Routing/Gates
使用者已指示「開始執行」（DEC-005）；依本規格在 feat/claude-code-support 分支實作並開 PR。

## Discussion Context
### DISC-001: 目標與範圍
- **Situation:** 套件偏向 Codex，使用者要在 Claude Code 中使用。
- **User answer:** 開新分支並開 PR；先寫 SPEC 等確認；修改範圍為安裝程式、manifest repository、`$` 語法、AskUserQuestion、Codex 字樣、README／路由／changeset；順帶修正 doc-coauthoring 的兩句文字；驗證方式為 plugin validate、unittest 與 rehearse。
- **Resulting impact:** REQ-001～REQ-007。

### DISC-002: main 上尚未提交的修改
- **Situation:** `layout.yaml`、SPEC-0064／0067 有修改，`specs/history` 有一個檔案被刪除，另有 18 份未追蹤的 SPEC。
- **User answer:** 帶著切分支，不暫存。
- **Resulting impact:** 已建立分支 `feat/claude-code-support`；REQ-007；`layout.yaml` 以部分暫存處理。

## Revision History
| Revision | Date | Change |
| --- | --- | --- |
| 1 | 2026-11-27 | 草稿：盤點 Codex 專屬用法，提出 Claude Code 支援範圍、驗收方式與待決事項。 |
| 2 | 2026-11-27 | 使用者採納四項建議（DEC-001～DEC-004），無待決事項。 |
| 3 | 2026-11-27 | 開始執行；記錄實作驗證證據。Changeset 依規定附上 release-intent.json。 |
