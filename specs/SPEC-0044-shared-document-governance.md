<!-- document-bundle:1 -->
<!-- document-navigation:start -->
[需求](SPEC-0044/requirements.md) | [驗收](SPEC-0044/acceptance.md) | [討論與決策](SPEC-0044/discussion.md) | [固定設計引用](SPEC-0044/references.yaml)
<!-- document-navigation:end -->
---
spec_version: 1
spec_id: SPEC-0044
revision: 12
status: implemented
change_set: shared-document-governance
working_id: WORKING-SPEC-a95230978287-shared-document-governance
task_ref: 01a0eb0c-4931-7112-8cdf-8862d42e984b
---
# 通用文件治理改版

## Problem
既有單檔 SPEC 內容過多；使用者已採用分檔引用與專案共用設計，並同意與 OS 規劃分開 SPEC。

## Solution
以分檔 Markdown 作專案設計來源，固定表格與指定 YAML 區塊由領域格式定義；SPEC 維護需求／驗收／討論／候選及固定版本引用。spec-governance 管共用文件契約、版本與來源、更新／遷移／恢復流程；架構 Skill 管各領域格式與內容檢查。manifest 及圖表由來源生成，授權依既有同範圍差異證明延續，多檔失敗須修復、驗證並完成原工作。本文件修改方案已由使用者整體確認，尚未實作。

## Relationships
None.

## Out of Scope
OS 與執行環境專業條款由 SPEC-0043 負責；本次尚未授權搬移既有文件、修改工具或安裝發布。

## Routing/Gates
Spec review: PASS
Discussion only. No implementation authorization.

## Current Specification

See Problem, Solution, Requirements and Acceptance Criteria above.

