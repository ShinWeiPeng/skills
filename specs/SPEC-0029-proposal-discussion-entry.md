---
spec_version: 1
spec_id: SPEC-0029
revision: 22
status: confirmed
change_set: proposal-discussion-entry
working_id: WORKING-SPEC-da8f8e96a6ac-proposal-discussion-entry
task_ref: 01a0b3c1-92b2-7401-882d-d2454d749656
---
# 工程任務預設啟動 grilling 與討論保存

## Problem
任務 01a0b339-4b59-7002-9ea1-1b82132dd2c4 在「提出量測方案」後直接產出方案，直到使用者詢問 SPEC 才保存。稍後 router 已選 grilling，仍直接補寫規格。現行 intent-rules.json 未涵蓋提出量測方案，技能將保存時點放在第一個決策問題之前，未涵蓋沒有發問便產出方案的路徑。

## Solution
將 grilling 管理討論與單一 SPEC 保存改為所有工程任務的預設入口，再依任務需要進行診斷、說明或方案探索。討論保存必須早於第一份實質方案或決策問題，不等待使用者追問。不以增加問題數作為完成依據。每個主題在 specs/ 中以同一 SPEC 作為討論至確認的唯一文件，持續整理規格、決策、待討論事項、完整性缺口及來源/修訂歷史；working 與 confirmed 是同一檔案的狀態，不再分設 WORKING-SPEC 與討論 journal。每輪先更新並核對既有決策再繼續，已採納變更收斂後自動正式化，不等待使用者追問。

## User Stories
- 使用者要求提出量測或修改方案時，系統自動開始保存需求及討論，後續可接續，無須提醒建立 SPEC。

## Requirements
| ID | Requirement |
|---|---|
| REQ-001 | 所有工程任務從開始即建立或接續本任務討論紀錄，由 grilling 管理討論狀態；不以辨識方案或變更請求為保存前提。診斷、說明與只讀探索照常進行，有真正使用者決策才提問。 |
| REQ-002 | 工程任務入口先在 specs/ 建立或接續本主題唯一 SPEC Markdown，以 working 狀態保存目標、限制、事實來源及待決事項，再呈現實質工程答覆；必要初始事實讀取可先進行。工作版與正式版使用同一 SPEC 身分與路徑，不另建立 spec-governance/WORKING-SPEC 或討論 journal；產品執行授權保持獨立。 |
| REQ-003 | grilling 主導需求與決策；diagnosis、量測與 proposal 技能提供事實或候選方案。每次答案與需求變更更新同一 SPEC；只讀插問保留既有狀態。無待決事項時保存決策依據後可完成，不強制虛構問題。 |
| REQ-004 | managed handoff 與 finish-turn 檢查工程任務是否有匹配 task、working reference、revision/hash 的已保存討論；缺失時要求初始化或修復，不能只以 selected_skill 或自報完成旗標通過。以獨立對話 trace 檢查保存與方案呈現的先後；不得宣稱能攔截宿主所有工具或回覆。 |
| REQ-005 | 正式確認前核對需求、決策來源、未決事項與目前 SPEC 版本。既有 confirmed 未實作 SPEC 遇範圍變更時在同一檔案改回 working；implemented SPEC 新建關聯規格。舊 bundle 的恢復改依 REQ-018 遷移至單檔，不虛構歷史進入證據。 |
| REQ-006 | 同步 ask-matt、grilling、clarify-improvement-proposals、spec-governance 與相關支援技能、docs、路由契約及必要架構描述；加入原始案例、反例、恢復及不同專案狀態的回歸驗證。 |
| REQ-007 | 純診斷、程式說明只保存工作紀錄；形成具體變更目標後在同一工作紀錄收斂範圍與驗收，決策完整才產生正式 SPEC。方案討論與正式確認不是同一時點。 |
| REQ-008 | 助理主動提出具體修改時，在既有工作紀錄標記來源、理由、影響及候選狀態並主動釐清。使用者可接受、否決或延後；未採納的候選不阻擋原任務完成、不擴大正式 SPEC 或執行授權。 |
| REQ-009 | 插件攜帶宿主 hooks 接線，由收到訊息/任務恢復事件建立或恢復本任務保存義務，工具前檢查依賴紀錄的受支援操作，回合結束檢查本輪保存。沿用 spec owner 責任並改以單一 SPEC 的內容與版本為權威，依 task/turn/version 綁定，不依賴模型自願呼叫檢查，也不要求獨立討論 journal。 |
| REQ-010 | 漏存時每個原始使用者回合最多自動接續補存一次，接續不得重設次數；只保存有來源的實際討論，不補造決策、不確認未採納候選、不授權實作。補存失敗後停止依賴該紀錄的操作並回報原因及未保存範圍，禁止無限循環；無關只讀回覆不冒充保存成功。 |
| REQ-011 | 明確回報 hooks 是否支援、已信任、已載入及實際觸發。缺失、錯誤、逾時或未覆蓋路徑不得宣告完整治理有效；使用既有可用路徑維持討論保存並呈現能力缺口。不得繞過宿主信任審核，不承諾對所有工具、文字回覆或中斷完全攔截。 |

| REQ-012 | 與 SPEC-0030 共用恢復狀態時，補存額度仍綁定原始回合；修復、重驗、接續與重新載入不重設額度。通用恢復只能在其既有授權及依賴邊界內工作，不將未採納候選視為已授權修復。 |

| REQ-013 | 每個主題从第一次實質討論前建立或接續 specs/ 中同一 SPEC，提供目前規格、決策紀錄、待討論事項及完整性檢查。工作版是該檔案的 working 狀態，並非另一份 WORKING-SPEC；正式化在同一身分與路徑改為 confirmed，不複製成第二份文件。討論来源、決策理由與修訂歷史直接納入 SPEC，不再維護獨立討論/候選 Markdown 或 journal 作為必要保存入口。 |
| REQ-014 | 每輪討論取得新目標、限制、事實、答案、候選或需求變更後，先更新同一工作版 SPEC，再提出下一個問題或實質方案；沒有新資訊時核對並保留既有狀態，不虛構需求或增加無內容變更的規格版本。保存失敗須依既有一次補存與阻擋規則處理。 |
| REQ-015 | 下一輪或任務恢復前讀取目前工作版及既有決策。使用穩定問題/決策識別碼記錄已回答事項與理由；已解決問題不重新詢問。只有新資訊或明確要求改變前提時才重開，保存變更來源、原因及受影響需求，保留原決策可追溯性。 |
| REQ-016 | 每輪更新後檢查目標、範圍、行為、例外處理、重要決策與驗收對照的完整性。缺口關聯到需求或決策，區分可由資料查得的事實與真正需要使用者決定的事項；先調查事實，再從尚未解決且影響結論的缺口繼續討論，不為了湊問題重問已解決項目。 |
| REQ-017 | 同一 SPEC 明確區分已確認、候選、否決、延後、待決及事實來源；每輪保存不等於採納。已採納變更的範圍、需求、重要決策與驗收完整且沒有阻礙確認的未決事項時，自動在原檔整理並轉為 confirmed，於回覆呈現，不等待追問。純說明可保留原檔的工作紀錄並結束，不虛構修改需求或強制 confirmed；正式化不授權實作。 |

| REQ-018 | 既有 WORKING-SPEC、journal 及暫存討論筆記，先核對身分、版本與來源，再將有效內容、已定決策、待決事項及必要歷史遷入同一 SPEC。缺少或衝突的歷史明確標示，不猜測或靜默覆蓋。驗證成功後停用舊討論雙寫；失敗保留原始資料與恢復方式，禁止未驗證即刪除。遷移不得恢復過期授權或重設原始回合補存額度。 |

## Decisions
| ID | Decision |
|---|---|
| DEC-001 | 使用者已明確要求方案請求當下切換 grilling 並開始保存討論；保存不以第一個問題或追問 SPEC 為前提。 |
| DEC-002 | 建議沿用現有 router、working bundle、journal 與 finish-turn，增加入口及交接檢查，不建立第二套狀態儲存。 |
| DEC-003 | 本次為技能庫共通流程修改方案；不修改被引用任務的韌體、不要求安裝宿主 hook。 |
| DEC-004 | 使用者選擇 Q-001 選項 1：從所有工程任務開始即保存，由 grilling 管理討論狀態；有真正決策才提問。取代 DEC-001 僅以方案請求為入口的範圍，其自動保存目標保留。 |
| DEC-005 | 使用者選擇 Q-002 選項 1：純診斷與程式說明保留工作紀錄；形成且釐清變更方案後才產生正式 SPEC。 |
| DEC-006 | 採用 Q-003 選項 1，助理具體修改建議立即列為候選並主動釐清；沿用前一則解釋的界線：候選不得阻擋原任務完成，不自動納入正式 SPEC、不等同採納或實作授權。 |
| DEC-007 | 使用者採用 Q-004 修訂後選項 1：將插件接至宿主 hooks 自動檢查；漏存時自動接續補存一次，仍失敗則停止依賴該紀錄的後續操作並說明原因。取代 DEC-003 不使用 hook 的邊界；不修改原始韌體。 |

| DEC-008 | 維持 DEC-007 與 REQ-010：0030 通用修復及重驗不得重設每原始回合一次補存額度。此為已確認決策的整合約束，撤回 Q-005 再選一次或兩次的不必要問題；使用者已要求開始執行兩份 SPEC。 |

| DEC-009 | 使用者以「把這個納入正式SPEC」採納同一工作版 SPEC 持續更新方案：討論與決策直接納入工作版，讀取既有紀錄避免重問，檢查缺口並持續討論，收斂後自動正式化；保留候選與授權邊界。細化 DEC-002、DEC-005、DEC-006，不變更一次補存上限。 |

| DEC-010 | 依使用者澄清，工作版與正式版是同一 SPEC 的不同狀態，取代 DEC-002 沿用 working bundle/journal 的存放設計，以及 DEC-009 曾保留討論 journal 的解讀。保留持續討論、來源追溯、一次補存及執行授權界線。 |

## Discussion Context
| ID | Context | Source | Rationale |
|---|---|---|---|
| DISC-001 | 使用者：「提出量測方案 就要切換grilling 然後開始保存討論。不是靠使用者詢問為什麼沒有 SPEC」。 | 本任務使用者前一則訊息 | 保存必須從方案討論入口開始。 |
| DISC-002 | 使用者要求「提出修改方案」。 | 本任務目前訊息 | 授權形成及保存本方案，尚未要求實作。 |

### DISC-004: 工程任務預設保存
- **Situation:** 使用者指出反覆修正方案辨識仍然漏掉 grilling 與保存，需要決定入口範圍。
- **Question:** 工程任務的討論保存，應從哪個時點開始？
- **Options and tradeoffs:** 從工程任務開始就保存（建議）：grilling 管理討論狀態，診斷與說明照常進行，有真正決策才提問；不必等辨識到方案請求，但一般工程問答也會留下工作紀錄。／辨識到方案或變更請求才開始：一般問答較輕量；仍保留判斷切換時機的依賴，必須另證明入口與交接不會漏掉。
- **User answer:** 1
- **Explicit rationale:** 未另述理由。
- **Resulting impact:** REQ-001、REQ-002、REQ-004、AC-001、DEC-004；保存不再依賴方案請求切換。

### DISC-005: 純問答與正式規格
- **Situation:** 工程任務已選擇預設保存，需要區分工作紀錄與正式規格。
- **Question:** 只有診斷或程式說明、尚未形成修改方案時，紀錄應如何保存？
- **Options and tradeoffs:** 保留工作紀錄，形成變更方案才產生正式 SPEC（建議）：問答不遺失，也不為每次說明建立正式規格。／每個工程任務都產生正式 SPEC：所有討論都有正式編號，但純問答也會增加規格與維護成本。
- **User answer:** 選擇1，那行程變更方案的條件是什麼?
- **Explicit rationale:** 未另述理由；同時詢問形成變更方案的條件。
- **Resulting impact:** DEC-005、REQ-007、AC-007；正式化以明確變更目標、範圍、行為與驗收及無未決事項為門檻。助理自行提出建議的處理仍待決定。

### DISC-006: 主動建議自動列為候選
- **Situation:** 使用者詢問兩選項差異；助理解釋保存相同，差別是是否自動展開釐清，並補充候選不阻擋原任務、不擴大正式 SPEC 的界線。
- **Question:** 如果是助理主動提出具體修改建議，應如何處理？
- **Options and tradeoffs:** 立即列為待討論的變更候選（建議）：保存理由與影響，繼續釐清；不代表你已採納，也不授權實作。／先保留為一般建議：等你表示要進一步討論或採用後，才列為變更候選。
- **User answer:** 採用選項1
- **Explicit rationale:** 未另述理由。
- **Resulting impact:** DEC-006、REQ-008、AC-008；同時保存上一則解釋對候選範圍的限定。

### DISC-007: Hooks 與一次自動補存
- **Situation:** 官方與本機能力核對證明 hooks 有可行支援，但現有插件未接線；改用具體漏存處理問題取代原抽象保證問題。
- **Question:** 是否採用 hooks 自動檢查，並在發現漏存時先自動補存一次？
- **Options and tradeoffs:** 採用自動檢查與補存（建議）：漏存時自動接續一輪，依實際對話補存；仍失敗就停止需要該紀錄的後續操作並說明原因，避免無限重試。／採用自動檢查，但不自動補存：發現漏存就說明原因並等待處理；行為較保守，但你可能仍需指示繼續。
- **User answer:** 1
- **Explicit rationale:** 未另述理由。
- **Resulting impact:** DEC-007、REQ-009～REQ-011、AC-009～AC-011；採用宿主觸發與每個原始回合一次補救，產品執行尚未授權。

### DISC-008: 保留既有補存決策並開始執行
- **Situation:** 比對0030後曾再次提出一次或兩次的問題；後續已說明這是既有決策的整合，不需重複選擇。使用者現在授權執行兩份規格。
- **Question:** 同一原始回合的補存失敗後，0030 修好原因，是否可以再自動補存？
- **Options and tradeoffs:** 維持一次上限（建議）：可以修復與重驗，但不再自動補存；告知結果，等你明確要求恢復。保留原決策，代價是偶爾需要你再回覆一次。／修復確認成功後，再允許補存一次：同一原始回合最多兩次，第二次仍失敗就停止。減少人工接續，但需同步修改 0029 的上限與驗收。
- **User answer:** 開始執行SPEC-0029/0030
- **Explicit rationale:** 未另述理由；既有一次上限不變，本輪不是選擇放寬次數。
- **Resulting impact:** DEC-008、REQ-012、AC-012；依目前討論範圍記錄雙規格授權，具體工具 admission 尚待核對。

### DISC-009: 工作版 SPEC 作為持續討論入口
- **Situation:** 使用者要求避免討論只存在聊天或另建筆記，並希望從彙整規格看出尚未討論的部分。助理提出同一工作版 SPEC 持續更新方案後仍只保存筆記，使用者要求正式納入。
- **Question:** 討論文件與 SPEC 如何整合，才能避免重複討論並辨識缺口？
- **Options and tradeoffs:** 分開討論文件與規格會增加同步成本；工作版 SPEC 包含規格、決策、待討論事項與完整性檢查，保留演進脈絡且只有一份人工閱讀與更新的權威內容。journal 保留稽核用途。
- **User answer:** 應該說只要有討論就要有討論文件，一直討論就會一直更新討論文件，每有一個討論，就會更新SPEC，並且繼續討論，直到討論結束。寫討論文件的目的是為了避免重複討論，以及在彙整SPEC後，可以確認有哪些還沒討論到的。或著不需要有討論文件，寫進SPEC也可以；把這個納入正式SPEC。
- **Explicit rationale:** 使用者明述避免重複討論及辨識尚未討論的缺口，並明確要求納入正式規格；未要求實作本次新增內容。
- **Decision:** DEC-009。
- **Resulting impact:** REQ-013～REQ-017、AC-013～AC-017；本任務 spec-governance/discussion-spec-workflow.md 的建議納入本規格，暫存筆記不再作為平行的權威方案。SPEC-0031 仍獨立處理執行指令簡寫。

### DISC-010: 修正工作版為另一份文件的誤解
- **Situation:** 助理在第 19 版仍保留 WORKING-SPEC 和 journal；使用者質疑為何舊文件仍存在，並再次指出已採納的五步流程。
- **Question:** 為何還會存在？使用者認知是這個流程就是修改原有討論文件機制。
- **Options and tradeoffs:** 保留兩份檔案需同步及移轉；同一 SPEC 以 working/confirmed 狀態演進，直接保存討論、決策與缺口，須調整既有生命週期與遷移流程。
- **User answer:** 為什麼還會存在?我的認知是這個流程就是修改這各的；開始討論建立工作版、每輪更新、讀既有紀錄、檢查缺口、收斂後整理為正式 SPEC。
- **Explicit rationale:** 使用者要求流程取代舊討論文件機制，助理先前沿用分檔設計未符合此意圖。本輪為規格更正，未要求產品實作或立即刪除既有檔案。
- **Decision:** DEC-010。
- **Resulting impact:** 修訂 REQ-002、REQ-003、REQ-005、REQ-009、REQ-013、REQ-017 及對應驗收；新增 REQ-018、AC-018。工作版與正式版同一檔案；舊檔驗證遷移後停用，不在本次規格更新中刪除。

## Acceptance Criteria
| ID | Requirements | Criterion | Validation Method | Evidence |
|---|---|---|---|---|
| AC-001 | REQ-001 | 工程診斷、說明、方案與變更任務均從入口保存；只讀問答不虛構決策；非工程任務不誤觸發。 | 路由與多輪真實任務驗證，分別核對入口有無呼叫、紀錄與答覆先後。 | PENDING |
| AC-002 | REQ-002 | 首份方案或問題前已有 specs/ 中本主題唯一工作狀態 SPEC，保存原始目標；無新增平行 WORKING-SPEC/journal。 | 重播原始對話，核對 trace 順序、檔案路徑及建立清單。 | PENDING |
| AC-003 | REQ-003 | 短答、混合回答、只讀插問、零問題完成均保留或更新同一 SPEC。 | 多回合整合測試及 DISC/版本斷言。 | PENDING |
| AC-004 | REQ-004 | 僅 selected_skill、自報完成、錯任務或過期 hash 不能通過；有效保存可繼續。 | managed handoff/finish-turn 正反例與獨立 trace 審查。 | PENDING |
| AC-005 | REQ-005 | 範圍變更、舊工作檔恢復、confirmed/implemented 邊界可驗證且不偽造舊證據。 | lifecycle 回歸案例與正式 SPEC 檢查。 | PENDING |
| AC-006 | REQ-006 | 技能、文件、契約和發布產物規則一致，完整原始失敗案例無使用者追問也能保存。 | 文件檢查、完整測試、架構 gate、assemble 與 distribution validation。 | PENDING |
| AC-007 | REQ-007 | 純解釋不產生正式 SPEC；具體變更在同一紀錄發展，範圍與驗收未明時不確認正式 SPEC。 | 多輪測試，核對工作版本與 materialize 順序。 | PENDING |
| AC-008 | REQ-008 | 主動建議被保存並釐清；否決或延後保留紀錄，原任務仍可完成；未採納候選不進入正式需求與授權範圍。 | 多輪候選狀態及正式化/完成判定正反例。 | PENDING |
| AC-009 | REQ-009 | 刻意讓模型不呼叫 router/finish-turn，已啟用 hooks 仍有主動觸發證據；錯任務與過期版本不通過；正常只讀解釋可保存而不產生正式 SPEC。 | 隔離候選插件與真實桌面多輪紀錄，核對 hook 事件、task/turn 與檔案版本。 | PENDING |
| AC-010 | REQ-010 | 成功漏存補救只有一次；持續失敗時無第二次自動接續，依賴操作停止；重啟與接續不重設額度；不創造使用者決策。 | 合成事件/整合測試加真實漏存及持續失敗案例，核對次數與原始對話。 | PENDING |
| AC-011 | REQ-011 | 未信任、停用、不支援、hook 執行錯誤及工具未覆蓋均有明確缺口，不能回報整體成功；安裝候選不略過信任。 | 能力/載入/觸發矩陣及桌面真實證據，完整回歸、架構与發布檢查。 | PENDING |

| AC-012 | REQ-012 | 補存失敗後即使 0030 修好設定並重驗通過，同一原始回合亦不發起第二次自動補存；未採納候選不執行。 | 兩規格共用恢復整合測試，核對原始回合、額度及副作用。 | PENDING |

| AC-013 | REQ-013 | 討論、持續更新至正式確認使用相同 SPEC ID/路徑；四類內容與來源/歷史均在該檔，無獨立 WORKING-SPEC 或討論 journal 的必要依賴。 | 新任務及多輪確認/重開測試，核對檔案清單、身分、內容與狀態。 | PENDING |
| AC-014 | REQ-014 | 每輪新資訊先寫入工作版再呈現下一問題/方案；無新資訊不虛增規格版本，漏存不繞過既有一次上限。 | 多輪事件順序、快照及版本斷言，加真實桌面討論 trace 檢查。 | PENDING |
| AC-015 | REQ-015 | 恢復後不重問已解決問題；新資訊改變前提時可重開，原決策、原因與影響可追溯。 | 跨回合與重啟案例，比對問題/決策識別碼、重開來源與實際提問內容。 | PENDING |
| AC-016 | REQ-016 | 可辨識缺少行為、例外或驗收等缺口；可查得事實先調查，只對真正未決事項提問，更新後正確移除已解決缺口。 | 使用缺漏/完整規格 fixtures 與多輪討論，核對缺口清單、需求對照與問題順序。 | PENDING |
| AC-017 | REQ-017 | 收斂後不待追問即在原檔確認並呈現；候選/否決/延後不誤列採納，純說明可保存後結束且不強制確認，正式化不放行實作。 | 單檔討論至確認/finish-turn/admission 整合及真實多輪 trace。 | PENDING |

| AC-018 | REQ-018 | 舊工作檔/筆記/歷史可遷入唯一 SPEC；缺損或衝突明確阻擋、不遺失來源，不雙寫、不重設補存額度或舊授權。 | 遷移成功、衝突、缺檔、中途失敗及重試 fixtures，核對原檔保存、內容完整性、授權與額度。 | PENDING |

## Relationships
| Source | Relation | Target |
|---|---|---|
| REQ-004 | refines | SPEC-0024 |
| DEC-004 | supersedes | DEC-001 |
| DEC-007 | supersedes | DEC-003 |
| REQ-012 | refines | SPEC-0030 |

| REQ-013 | refines | REQ-002 |
| REQ-014 | refines | REQ-003 |
| REQ-015 | refines | REQ-003 |
| REQ-016 | refines | REQ-005 |
| REQ-017 | refines | REQ-007 |
| REQ-017 | refines | REQ-008 |

| DEC-010 | supersedes | DEC-002 |
| DEC-010 | refines | DEC-009 |
| REQ-018 | refines | REQ-005 |

## Out of Scope
- 改變執行授權政策、修改原始韌體、部署外部服務、修改 Codex 宿主原始碼或承諾完整防繞過。插件支援的 hook 接線納入本案。

## Open Decisions
None.

## Routing/Gates
- grilling: 使用者已確定討論入口與保存時點；本方案內部接線選擇沿用既有責任，沒有需另選的產品決策。
- 修改既有 ALG-0003 workflow selection 與 spec lifecycle；新增宿主 hook adapter 接至既有 owner，更新插件 manifest、組裝與相關 Flow/契約描述，受現有架構治理檢查。
- 實作前盤點 schema 相容性、確定受影響公共介面及架構 gate；測試結果僅可在實際驗證後記錄。
- 預期驗證：路由、spec lifecycle、completion 整合與 plugin distribution。第 17 版已有本機實作及部分證據，正式桌面驗收仍未完成；本次新增 REQ-013～REQ-017 尚未實作或驗收。既有第 17 版證據不可當作本次新增要求通過的證據。
- 本次新增 AC-013～AC-017；validation/acceptance-SPEC-0029.json 及綁定計畫需在後續實作前同步。此次僅保存規格，不宣稱驗證規劃或產品執行就緒。第 21 版另新增 AC-018 並修訂相關 AC，驗收映射與計畫須一併更新；第 17 版實作不代表已符合單檔設計。

## Proposal impacts and alternatives
- 第 21 版更正存放設計：由同一 SPEC 在原路徑變更狀態，取代舊 working bundle/journal 討論保存。下列早期方案中的 working bundle/journal 字樣僅為歷史實作背景，以 DEC-010 及目前 REQ 為準。單檔保存、來源追溯及遷移是新增實作與驗收工作。
- 僅增加提示文字成本最低，但不能檢查漏掉保存，不能單獨滿足需求。
- 本次重點為預設討論保存與宿主自動觸發；修改 workflow selection、spec lifecycle/completion、插件 hooks 與組裝/文件。辨識詞調整不能代替入口及交接落實。
- 已選擇插件 hook 自動觸發；取代只依賴模型主動呼叫的方案，增加宿主相容、信任、載入與真實事件驗證成本。
- 風險是普通問答誤觸發及歷史 bundle 被誤封鎖；以反例與顯式恢復路徑驗證。
- 不承諾執行效能提升；保存沿用現有本機檔案 IO，驗證重點是行為與順序。
- 實作順序：隔離環境驗證 hook 接線與覆蓋 → 工程預設保存/狀態契約 → 受限一次補存與完成檢查 → 恢復與相容 → 真實多輪驗收及發布回歸。

## Question Record

```json
{
  "question_id": "Q-004",
  "history": [
    {
      "action": "revise",
      "question": {
        "id": "Q-004",
        "version": 11,
        "question": "這次修正希望達到哪一層保證？",
        "options": [
          "先完成插件內改善（建議）：工程任務預設保存，並以真實多輪任務驗收；漏做就判失敗。範圍較小，但仍依賴模型執行入口。",
          "要求模型漏做也無法跳過：先調查宿主是否支援強制入口與攔截，再決定實作；範圍較大，目前無法保證現有插件能做到。"
        ]
      },
      "source_ref": "current-thread:user:繼續討論-after-hook-capability-investigation",
      "user_text": "繼續討論"
    }
  ],
  "failed_surfaces": {}
}
```

## Revision History
| Revision | Date | Change |
|---|---|---|
| 1 | 2026-09-18 | 從使用者明確要求建立共通方案入口修改規格，驗收待實作。 |
| 14 | 2026-09-18 | 整合四項使用者選擇：工程預設保存、正式化門檻、候選不阻擋、hooks 一次補存。 |
| 3 | 2026-09-18 | Reopened before clarification: 使用者指出已多次修改方案辨識，要求開始討論；撤回修復方向已定案的假設，先核對繞過與驗收缺口。 |
| 15 | 2026-09-18 | Reopened before clarification: 使用者要求討論 SPEC-0030 通用恢復與 SPEC-0029 每原始回合一次補存的整合邊界；原決策保留，待釐清優先序或是否修訂。 |
| 18 | 2026-09-18 | Reopened before clarification: 使用者要求將工作版 SPEC 隨討論更新、避免重複討論、缺口檢查及收斂後自動正式化方案納入正式 SPEC。 |

| 19 | 2026-09-18 | 納入 DEC-009、REQ-013～REQ-017 與 AC-013～AC-017：工作版 SPEC 持續討論、避免重問、缺口檢查及自動正式化；新增內容待實作與驗收。 |
| 20 | 2026-09-18 | Reopened before clarification: 使用者澄清五步流程要取代舊討論文件機制；同一 SPEC 由工作狀態持續更新至正式確認，不保留平行 WORKING-SPEC/journal 討論文件。 |

| 21 | 2026-09-18 | 依使用者澄清改為同一 SPEC 檔案由 working 演進至 confirmed；新增 DEC-010、REQ-018、AC-018，取代平行 WORKING-SPEC/journal 討論保存設計。 |

## Historical reopened discussion — resolved by DEC-004 through DEC-007
原修復設計仍為候選，不得依 DEC-002/DEC-003 或 Routing/Gates 的先前評估宣称方案已決策完整。使用者指出已多次修改方案辨識；本次先區分入口未執行、交接未遵守、版本載入與驗收缺口，不以補詞直接結案。舊決策保留供追溯，其方案設計部分待本輪重評。

### DISC-003: Reassess repeated recognition fixes
- **Situation:** 原任務曾回傳 selected_skill=grilling，但後續仍沒有可核對的 grilling 完成過程；SPEC-0026 AC-003/AC-005 真實行為驗收仍標示 Pending。
- **Question:** 為何多次修正方案辨識後仍發生相同問題？
- **Options and tradeoffs:** 啟動條件與執行遵循是不同問題；目前未確認新的修復架構，先討論是否將保存改為工程任務預設流程。
- **User answer:** 之前有好幾次都是修改辨識方案請求；開始討論
- **Explicit rationale:** 使用者指出重複處理方案辨識，沒有另述理由。
- **Resulting impact:** REQ-001, REQ-002, REQ-004, REQ-006 的解法與驗收方式重新評估，原始自動保存目標保留。
## Transition criteria
以討論內容是否要求改變現況為準：可指出變更對象及預期差異即進入方案討論，不必知道完整實作方法，也不依赖「方案」字詞。具體測量能力、測試設定與流程的改變均屬變更；讀取既有紀錄或解釋目前行為不是變更。正式 SPEC 另需範圍、需求、重要決策與驗收完整且無未決事項。助理建議屬候選，不等同使用者決策或執行授權。

## Historical reliability boundary — superseded by DEC-007
移除方案切換判斷只能減少漏接點；plugin 仍依賴模型執行入口與保存，不能把受控工具拒絕或事後 trace 稽核當成宿主強制攔截。既有 DEC-003 的無宿主 hook 邊界為先前方案設定，現需使用者確認是否維持；若要求獨立於模型的保證，須先查證宿主支援並據此重定範圍，不預設可用。

## Capability investigation — 2026-09-18
使用者要求先確認能力，而非選擇 Q-004；不把「先確認」當成選項答案。Q-004 技術前提已修正，暫不要求使用者回答原問題。尚未授權或實作插件/宿主設定變更。

- 現有插件 manifest 只有 skills 與 interface，已安裝 0.16.0 根目錄沒有 hooks 目錄，遞迴找不到 hooks 檔案。managed_delivery.py 回傳 managed-entrypoint-only / observed-trace-only；workflow_selection.py 為 routing-only；finish-turn 為 observed-discussion-only。因此受控入口未被呼叫時，檢查不會自動攔截其他路徑。
- 官方文件 https://learn.chatgpt.com/docs/hooks 明確支援 plugin-bundled hooks、UserPromptSubmit、PreToolUse 與 Stop。PreToolUse 可拒絕支援的工具；Stop 的 block 會產生接續提示，並非撤回已產生回覆。特殊工具路徑與既有 write_stdin 會有覆蓋限制；不能宣稱完全防繞過。
- 本機 npm CLI 為 0.147.0；目前桌面 app 使用 C:/Users/hugo_peng/AppData/Local/OpenAI/Codex/bin/cdef5aaf3e41ab53/codex.exe，其 --version 為 0.155.0-alpha.9，features list 回報 hooks stable true。這證明本機 runtime 宣告功能，尚不證明具體 hook 已載入、獲信任或通過端到端行為測試。
- 普通 plugin hook 須使用者信任確切定義。此次未配置/安裝 hooks、未改 config、未更改產品程式；只讀能力核對不能稱作功能修復或驗收完成。
- 根據上述證據，可行候選是由 UserPromptSubmit 建立/恢復狀態，PreToolUse 查受支援操作，Stop 查本輪保存並要求補做；具體腳本、錯誤策略、防循環與桌面路徑驗證仍需設計。原先「插件只能靠模型提醒」不能作為永久平台限制；應改成「目前插件尚未接上宿主 hooks」。

## Current Specification

See Problem, Solution, Requirements and Acceptance Criteria above.

## Decision History

See Decisions, Discussion Context and the sourced Discussion History below.

## Pending Discussion

None.

## Completeness Gaps

None.

<!-- spec-audit:start -->
## Discussion History

- 01a0b40b-3d33-7d71-9e7b-766e8a9ae38c: 開始執行 specs/SPEC-0029-proposal-discussion-entry.md
- prepared-final:SPEC-0029:01a0b40b-3cb8-7783-b328-626f8d9b0af1: Authorized SPEC-0029 revision 17 implemented locally. 562 Python tests passed and 2 POSIX cases skipped. Windows installer/ACL, release architecture, distribution and release rehearsal passed. Standards and Spec review defects fixed. Formal acceptance remains BLOCKED for real desktop trust/loading/firing, independent traces and actual SPEC-0030 integration. Evidence: artifacts/validation/113edc215a1f40459b30a78e9ea2556c/report.md; managed assessment artifacts/validation/9f3c3f675ce240ed9b8b8fd47854ea02/assessment.json. This late owner entry is not historical proof of initial hook firing. No new user decision, execution grant, commit, publication, installed-plugin replacement or hook trust was inferred.
- 01a0b48b-5d14-7512-b1af-8ff15c52b725: 提出開始執行與 SPEC 編號簡寫相容方案，僅討論，不修改產品
- prepared-proposal:01a0b48b-5c94-7010-b1a4-1ecd91d98d9c: User requests a proposal to support short execution commands. Observed workflow_selection.py only matches bare phrase or canonical path; spec_delivery.py likewise accepts bare phrase or exact relative path. Proposed consistent parsing/target resolution/admission plus skills/docs and regression coverage. Include bare SPEC suffix as current-context alias and explicit SPEC ID with or without spacing. No candidate adoption or product implementation grant inferred; SPEC-0029 revision remains unchanged.
- 01a0b500-9da6-7352-ae72-801f6c530932: 開始執行SPEC-0029/0030   
- 01a0b500-9da6-7352-ae72-801f6c530932: 完成 SPEC-0029/0030 原始碼、skill 與人類文件修改。單檔工作 SPEC、持續保存、完整性審查、自動確認、舊雙檔驗證遷移；能力與 gate 結果分離、AC 新增刪除與同 ID 語意差異、criterion_sha256、結構化診斷及有限恢復；組合 SPEC 授權完整綁定。SPEC0029 r22 和 SPEC0030 r2 僅補上派生閱讀視圖，未變更確認需求。來源與補存額度保留。插件回歸 308 項 PASS: artifacts/tests/e25d227a3eaf418298d8deabe2e48178/manifest.json；驗證規劃 31 項 PASS: artifacts/tests/536b8233fc6e432cbaaed0aba51aa918/manifest.json；封裝 38 項中 36 PASS/2 skipped: artifacts/tests/5091a3291a4a43e493039f03fc6d300d/manifest.json。實際當前來源事件組合授權 admission 已 PASS（非宿主認證）。未執行安裝、信任變更、提交或發布。真實桌面 hook firing、多輪 trace 與完整 AC 驗收仍未證明，不能以單元測試代替。狀態保持 confirmed，未標記 implemented。
- 01a0b54d-1aaa-7390-a0c3-a7cd312b2df2: 安裝測試版後，開始測試
- 01a0b54d-1aaa-7390-a0c3-a7cd312b2df2: 使用者明確授權安裝測試版並測試。已用目前桌面實際 runtime 0.155.0-alpha.9 的 plugin add 成功安裝 governed-engineering-skills@governed-engineering-development 0.16.0+codex.local-20260918161704513960，快取內容雜湊293檔一致。以該安裝快取執行 Windows launcher/owner smoke：初始化、工程分類、單檔保存、正確回覆Stop、漏存最多一次修復、Python缺失拒絕，共4檢查PASS。不可冒稱真實桌面事件觸發。證據 artifacts/tests/116bbe01f01040cf927b4b1729f11667/manifest.json；spec-governance/installed-package-test.json。用相同桌面runtime app-server hooks/list只讀查詢，四事件sessionStart/userPromptSubmit/preToolUse/stop loaded enabled但全部untrusted。未修改信任、未使用bypass。真實桌面驗收仍BLOCKED等待宿主hook審閱/信任。當前任務cwd在父目錄，測試需以實際repo根C:/Users/hugo_peng/skill/skills開新任務以匹配紀錄/Python。已開啟插件頁並排入hook定義檢視。正式release未替換，未提交發布。

### Source and Revision Audit

```jsonl
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"0b7b6982a503435f85ab06aa048f0b38","event_hash":"5d659a2bd94ce708dd878d4b6d4997d1135a34a5561700616b363a7566111cc0","event_type":"start","event_version":1,"open_decisions":[],"previous_event_hash":null,"previous_snapshot_hash":null,"recorded_at":"2026-09-18T09:11:44.552102+00:00","relationships":[{"relation":"refines","source":"","target":"SPEC-0024"}],"revision":1,"snapshot_hash":"896cb89f7d210a143d2fdccc1b6658b8eb3d6e7ff5faaba142d7c512f6ff5743","verdict":"PASS","working_id":"WORKING-SPEC-da8f8e96a6ac-proposal-discussion-entry"}
{"affected_ids":["AC-001","AC-002","AC-003","AC-004","AC-005","AC-006"],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":["AC-001","AC-002","AC-003","AC-004","AC-005","AC-006"],"removed_ids":[]},"epoch":"0b7b6982a503435f85ab06aa048f0b38","event_hash":"82584f7730a9a65aea436b16683eb1e5ee61d1c283315ea17a804c68127f6b5e","event_type":"reconcile","event_version":1,"open_decisions":[],"previous_event_hash":"5d659a2bd94ce708dd878d4b6d4997d1135a34a5561700616b363a7566111cc0","previous_snapshot_hash":"896cb89f7d210a143d2fdccc1b6658b8eb3d6e7ff5faaba142d7c512f6ff5743","recorded_at":"2026-09-18T09:12:42.858974+00:00","relationships":[{"relation":"refines","source":"REQ-004","target":"SPEC-0024"}],"revision":2,"snapshot_hash":"48dc7feeca1ec500f4791ae3207575df674035bc7015c32720676b8f52ad8b01","verdict":"PASS","working_id":"WORKING-SPEC-da8f8e96a6ac-proposal-discussion-entry"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"0b7b6982a503435f85ab06aa048f0b38","event_hash":"d34f1863fc8d339cd7b58525ff01d39acdf53671d8395e4d76cc0cadaf1673b7","event_type":"materialize","event_version":1,"open_decisions":[],"previous_event_hash":"82584f7730a9a65aea436b16683eb1e5ee61d1c283315ea17a804c68127f6b5e","previous_snapshot_hash":"48dc7feeca1ec500f4791ae3207575df674035bc7015c32720676b8f52ad8b01","recorded_at":"2026-09-18T09:12:50.174089+00:00","relationships":[],"revision":2,"snapshot_hash":"28cd151871dd74c236d03c5e00a479bd0b5e2f6fcd7f03b59f808240fca5dcab","verdict":"PASS","working_id":"WORKING-SPEC-da8f8e96a6ac-proposal-discussion-entry"}
{"affected_ids":[],"baseline_contract_hash":"9693b2da91609f77a3440cbca4c7445559605770299fa40cbeba7d3308139a6b","conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"0b7b6982a503435f85ab06aa048f0b38","event_hash":"7a598cfc7c927d0f42073fdf4fda41fc3c6fb0d8993b2d6cf08b09b4a2a2563f","event_type":"reopen","event_version":1,"open_decisions":[],"previous_event_hash":"d34f1863fc8d339cd7b58525ff01d39acdf53671d8395e4d76cc0cadaf1673b7","previous_snapshot_hash":"28cd151871dd74c236d03c5e00a479bd0b5e2f6fcd7f03b59f808240fca5dcab","recorded_at":"2026-09-18T09:19:32.113682+00:00","relationships":[],"revision":3,"snapshot_hash":"0ec1d005c36ffdb90ecbcaa8d888fd4cdb3b52511eaa96c0da4d3a10631e6be4","verdict":"BLOCKED","working_id":"WORKING-SPEC-da8f8e96a6ac-proposal-discussion-entry"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"0b7b6982a503435f85ab06aa048f0b38","event_hash":"fffc624acbcccad763cdc67d7b30409ce2864d715aeb919abfa576acc72d7df7","event_type":"reconcile","event_version":1,"open_decisions":["OD-001: 待決定討論保存是所有工程任務的預設入口，或仍依方案/變更意圖切換。"],"previous_event_hash":"7a598cfc7c927d0f42073fdf4fda41fc3c6fb0d8993b2d6cf08b09b4a2a2563f","previous_snapshot_hash":"0ec1d005c36ffdb90ecbcaa8d888fd4cdb3b52511eaa96c0da4d3a10631e6be4","recorded_at":"2026-09-18T09:20:18.541100+00:00","relationships":[{"relation":"refines","source":"REQ-004","target":"SPEC-0024"}],"revision":4,"snapshot_hash":"e418a271488dd9881adcacf892f12a58d3ce0c16f3397e0aa6501c8e978c377c","verdict":"BLOCKED","working_id":"WORKING-SPEC-da8f8e96a6ac-proposal-discussion-entry"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"0b7b6982a503435f85ab06aa048f0b38","event_hash":"79aaebf59e3e5dc89ea02c5bf4bdac990143bee326d05e7d7724e36b0f2935d7","event_type":"reconcile","event_version":1,"open_decisions":["OD-001: 待決定討論保存是所有工程任務的預設入口，或仍依方案/變更意圖切換。","Q-001@5"],"previous_event_hash":"fffc624acbcccad763cdc67d7b30409ce2864d715aeb919abfa576acc72d7df7","previous_snapshot_hash":"e418a271488dd9881adcacf892f12a58d3ce0c16f3397e0aa6501c8e978c377c","recorded_at":"2026-09-18T09:20:33.424899+00:00","relationships":[{"relation":"refines","source":"REQ-004","target":"SPEC-0024"}],"revision":5,"snapshot_hash":"87a68a6dc0c541d83b3a3a3633f731394faf871697e1056f682b51d3c90df901","verdict":"BLOCKED","working_id":"WORKING-SPEC-da8f8e96a6ac-proposal-discussion-entry"}
{"affected_ids":["AC-001","DEC-004","DISC-004","REQ-001","REQ-002","REQ-004"],"conflicts":[],"continuity":"continuous","delta":{"added_ids":["DEC-004","DISC-004"],"changed_ids":["AC-001","REQ-001","REQ-002","REQ-004"],"removed_ids":[]},"epoch":"0b7b6982a503435f85ab06aa048f0b38","event_hash":"57b97d055346bfc425daf82e43e2ac54fb10dfb57b10c7197ef1827517188414","event_type":"reconcile","event_version":1,"open_decisions":["OD-002: 純診斷與說明討論是否形成正式 SPEC，或只保留工作紀錄。"],"previous_event_hash":"79aaebf59e3e5dc89ea02c5bf4bdac990143bee326d05e7d7724e36b0f2935d7","previous_snapshot_hash":"87a68a6dc0c541d83b3a3a3633f731394faf871697e1056f682b51d3c90df901","recorded_at":"2026-09-18T09:24:15.075942+00:00","relationships":[{"relation":"refines","source":"REQ-004","target":"SPEC-0024"},{"relation":"supersedes","source":"DEC-004","target":"DEC-001"}],"revision":6,"snapshot_hash":"0a3b56d09ab94980aa6a7900f5c4cf4f0c3a323b316029f2f9475173c326f60d","verdict":"BLOCKED","working_id":"WORKING-SPEC-da8f8e96a6ac-proposal-discussion-entry"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"0b7b6982a503435f85ab06aa048f0b38","event_hash":"4bf34398ffecf6b4b9421a1373fa8447f3096208acb3e59b27cd9e3a7c532e1b","event_type":"reconcile","event_version":1,"open_decisions":["OD-002: 純診斷與說明討論是否形成正式 SPEC，或只保留工作紀錄。","Q-002@7"],"previous_event_hash":"57b97d055346bfc425daf82e43e2ac54fb10dfb57b10c7197ef1827517188414","previous_snapshot_hash":"0a3b56d09ab94980aa6a7900f5c4cf4f0c3a323b316029f2f9475173c326f60d","recorded_at":"2026-09-18T09:24:26.878486+00:00","relationships":[{"relation":"refines","source":"REQ-004","target":"SPEC-0024"},{"relation":"supersedes","source":"DEC-004","target":"DEC-001"}],"revision":7,"snapshot_hash":"8b0e02697168ebeeeea866a2b5f1d89e870d55428a536c420510934961a8dafb","verdict":"BLOCKED","working_id":"WORKING-SPEC-da8f8e96a6ac-proposal-discussion-entry"}
{"affected_ids":["AC-007","DEC-005","DISC-005","REQ-007"],"conflicts":[],"continuity":"continuous","delta":{"added_ids":["AC-007","DEC-005","DISC-005","REQ-007"],"changed_ids":[],"removed_ids":[]},"epoch":"0b7b6982a503435f85ab06aa048f0b38","event_hash":"f050de0d67783d772ec67a7d77bfb0e1ab4b72ee3f71c07a1413f32eaaaaf4e6","event_type":"reconcile","event_version":1,"open_decisions":["OD-003: 助理主動提出具體修改建議，是否立即標記為待討論變更；不表示使用者採納。"],"previous_event_hash":"4bf34398ffecf6b4b9421a1373fa8447f3096208acb3e59b27cd9e3a7c532e1b","previous_snapshot_hash":"8b0e02697168ebeeeea866a2b5f1d89e870d55428a536c420510934961a8dafb","recorded_at":"2026-09-18T09:28:11.175340+00:00","relationships":[{"relation":"refines","source":"REQ-004","target":"SPEC-0024"},{"relation":"supersedes","source":"DEC-004","target":"DEC-001"}],"revision":8,"snapshot_hash":"d3820979853f792882811cbb369f6d6459b8a484e604cc242293d437f6115cb2","verdict":"BLOCKED","working_id":"WORKING-SPEC-da8f8e96a6ac-proposal-discussion-entry"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"0b7b6982a503435f85ab06aa048f0b38","event_hash":"e0f5b8477912738ae6d537f25da4bc4fa8abb460178215c0a0d302d4fe82ee0c","event_type":"reconcile","event_version":1,"open_decisions":["OD-003: 助理主動提出具體修改建議，是否立即標記為待討論變更；不表示使用者採納。","Q-003@9"],"previous_event_hash":"f050de0d67783d772ec67a7d77bfb0e1ab4b72ee3f71c07a1413f32eaaaaf4e6","previous_snapshot_hash":"d3820979853f792882811cbb369f6d6459b8a484e604cc242293d437f6115cb2","recorded_at":"2026-09-18T09:28:26.372064+00:00","relationships":[{"relation":"refines","source":"REQ-004","target":"SPEC-0024"},{"relation":"supersedes","source":"DEC-004","target":"DEC-001"}],"revision":9,"snapshot_hash":"c7a3f95885fdd2e928042fe191df901ee60da9eff911e5582e4e044d5400fa8e","verdict":"BLOCKED","working_id":"WORKING-SPEC-da8f8e96a6ac-proposal-discussion-entry"}
{"affected_ids":["AC-008","DEC-006","DISC-006","REQ-008"],"conflicts":[],"continuity":"continuous","delta":{"added_ids":["AC-008","DEC-006","DISC-006","REQ-008"],"changed_ids":[],"removed_ids":[]},"epoch":"0b7b6982a503435f85ab06aa048f0b38","event_hash":"795e79e0062d7d0e463ae9c4566dd17b4bb0026cd9e101cd368d33f46a126380","event_type":"reconcile","event_version":1,"open_decisions":["OD-004: 本次是否限定插件內流程可靠性與真實任務驗收，或要求獨立於模型遵循的強制入口；後者宿主能力尚未驗證。"],"previous_event_hash":"e0f5b8477912738ae6d537f25da4bc4fa8abb460178215c0a0d302d4fe82ee0c","previous_snapshot_hash":"c7a3f95885fdd2e928042fe191df901ee60da9eff911e5582e4e044d5400fa8e","recorded_at":"2026-09-18T09:34:50.123230+00:00","relationships":[{"relation":"refines","source":"REQ-004","target":"SPEC-0024"},{"relation":"supersedes","source":"DEC-004","target":"DEC-001"}],"revision":10,"snapshot_hash":"6e780d6a771a00f06ac311f44ec2a7d6d307af5105c57fa3a33eb55b1cc322c3","verdict":"BLOCKED","working_id":"WORKING-SPEC-da8f8e96a6ac-proposal-discussion-entry"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"0b7b6982a503435f85ab06aa048f0b38","event_hash":"d7dd6c9928077db664c8bf5d6fc08c5fcee4c0c3c11efa5e52949dc580c249d6","event_type":"reconcile","event_version":1,"open_decisions":["OD-004: 本次是否限定插件內流程可靠性與真實任務驗收，或要求獨立於模型遵循的強制入口；後者宿主能力尚未驗證。","Q-004@11"],"previous_event_hash":"795e79e0062d7d0e463ae9c4566dd17b4bb0026cd9e101cd368d33f46a126380","previous_snapshot_hash":"6e780d6a771a00f06ac311f44ec2a7d6d307af5105c57fa3a33eb55b1cc322c3","recorded_at":"2026-09-18T09:35:06.946247+00:00","relationships":[{"relation":"refines","source":"REQ-004","target":"SPEC-0024"},{"relation":"supersedes","source":"DEC-004","target":"DEC-001"}],"revision":11,"snapshot_hash":"819371394694a463de1da850ae70cf40d8cfac1f70d29e1a9dd10d5cd4b44d56","verdict":"BLOCKED","working_id":"WORKING-SPEC-da8f8e96a6ac-proposal-discussion-entry"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"0b7b6982a503435f85ab06aa048f0b38","event_hash":"677add0d067e0c7df2d94c9cac48149861e321d8d083d405491f2f51c4189bd4","event_type":"reconcile","event_version":1,"open_decisions":["OD-004: 本次是否限定插件內流程可靠性與真實任務驗收，或要求獨立於模型遵循的強制入口；後者宿主能力尚未驗證。","Q-004@11"],"previous_event_hash":"d7dd6c9928077db664c8bf5d6fc08c5fcee4c0c3c11efa5e52949dc580c249d6","previous_snapshot_hash":"819371394694a463de1da850ae70cf40d8cfac1f70d29e1a9dd10d5cd4b44d56","recorded_at":"2026-09-18T09:41:04.819570+00:00","relationships":[{"relation":"refines","source":"REQ-004","target":"SPEC-0024"},{"relation":"supersedes","source":"DEC-004","target":"DEC-001"}],"revision":12,"snapshot_hash":"59203c3015f881a936a73c64cf359d3121534d1e2d09f0c91b60d4987fdd605c","verdict":"BLOCKED","working_id":"WORKING-SPEC-da8f8e96a6ac-proposal-discussion-entry"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"0b7b6982a503435f85ab06aa048f0b38","event_hash":"d5406123774fc7db9a058a8ff4d7bb066a0b9821d1fa63ba3bf498dc7658a4d2","event_type":"reconcile","event_version":1,"open_decisions":["OD-004: 本次是否限定插件內流程可靠性與真實任務驗收，或要求獨立於模型遵循的強制入口；後者宿主能力尚未驗證。","Q-004@13"],"previous_event_hash":"677add0d067e0c7df2d94c9cac48149861e321d8d083d405491f2f51c4189bd4","previous_snapshot_hash":"59203c3015f881a936a73c64cf359d3121534d1e2d09f0c91b60d4987fdd605c","recorded_at":"2026-09-18T09:43:38.447349+00:00","relationships":[{"relation":"refines","source":"REQ-004","target":"SPEC-0024"},{"relation":"supersedes","source":"DEC-004","target":"DEC-001"}],"revision":13,"snapshot_hash":"2a070bc48aa44a0fb9101e0c55da0dc2c7fd933d40335227297f0b678fb630ae","verdict":"BLOCKED","working_id":"WORKING-SPEC-da8f8e96a6ac-proposal-discussion-entry"}
{"affected_ids":["AC-009","AC-010","AC-011","DEC-007","DISC-007","REQ-001","REQ-009","REQ-010","REQ-011"],"conflicts":[],"continuity":"continuous","delta":{"added_ids":["AC-009","AC-010","AC-011","DEC-007","DISC-007","REQ-009","REQ-010","REQ-011"],"changed_ids":["REQ-001"],"removed_ids":[]},"epoch":"0b7b6982a503435f85ab06aa048f0b38","event_hash":"0364405156bc18e48d5c7dc13e40ba3992f5205385f1d6f59b5087c0671d7b41","event_type":"reconcile","event_version":1,"open_decisions":[],"previous_event_hash":"d5406123774fc7db9a058a8ff4d7bb066a0b9821d1fa63ba3bf498dc7658a4d2","previous_snapshot_hash":"2a070bc48aa44a0fb9101e0c55da0dc2c7fd933d40335227297f0b678fb630ae","recorded_at":"2026-09-18T09:46:54.418396+00:00","relationships":[{"relation":"refines","source":"REQ-004","target":"SPEC-0024"},{"relation":"supersedes","source":"DEC-004","target":"DEC-001"},{"relation":"supersedes","source":"DEC-007","target":"DEC-003"}],"revision":14,"snapshot_hash":"65740a0ce0a4753bdb66c2dc6a9fa5c6466234f7e287a5b83494156f647b27e1","verdict":"PASS","working_id":"WORKING-SPEC-da8f8e96a6ac-proposal-discussion-entry"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"0b7b6982a503435f85ab06aa048f0b38","event_hash":"c6ca3d38801cc15f62e6faaa7217148f19f12a9ab2d197a0c67cf44262ed02e8","event_type":"materialize","event_version":1,"open_decisions":[],"previous_event_hash":"0364405156bc18e48d5c7dc13e40ba3992f5205385f1d6f59b5087c0671d7b41","previous_snapshot_hash":"65740a0ce0a4753bdb66c2dc6a9fa5c6466234f7e287a5b83494156f647b27e1","recorded_at":"2026-09-18T09:47:02.619313+00:00","relationships":[],"revision":14,"snapshot_hash":"dddfa3b8f878c821c5746cb273f8ed8ca4d49afc10d9d069c89c0b8bc62084c8","verdict":"PASS","working_id":"WORKING-SPEC-da8f8e96a6ac-proposal-discussion-entry"}
{"affected_ids":[],"baseline_contract_hash":"0ecf29548e0620778afb570f490362bc7dc032e28ae0faf4e7b973b356b93b91","conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"0b7b6982a503435f85ab06aa048f0b38","event_hash":"4745d4067c736fd83ff14932a71ff712d0dda449c2a3b83676408747a69706bd","event_type":"reopen","event_version":1,"open_decisions":[],"previous_event_hash":"c6ca3d38801cc15f62e6faaa7217148f19f12a9ab2d197a0c67cf44262ed02e8","previous_snapshot_hash":"dddfa3b8f878c821c5746cb273f8ed8ca4d49afc10d9d069c89c0b8bc62084c8","recorded_at":"2026-09-18T09:53:19.108214+00:00","relationships":[],"revision":15,"snapshot_hash":"28349d22522c611075e07d23620ff78fff9e57f5325d4c21f692ee6f129bbd93","verdict":"BLOCKED","working_id":"WORKING-SPEC-da8f8e96a6ac-proposal-discussion-entry"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"0b7b6982a503435f85ab06aa048f0b38","event_hash":"f65d9a6939727d60d16000a36e832bd07451231e35733459196cc0e16b778587","event_type":"reconcile","event_version":1,"open_decisions":["Q-005@16"],"previous_event_hash":"4745d4067c736fd83ff14932a71ff712d0dda449c2a3b83676408747a69706bd","previous_snapshot_hash":"28349d22522c611075e07d23620ff78fff9e57f5325d4c21f692ee6f129bbd93","recorded_at":"2026-09-18T09:53:34.644131+00:00","relationships":[{"relation":"refines","source":"REQ-004","target":"SPEC-0024"},{"relation":"supersedes","source":"DEC-004","target":"DEC-001"},{"relation":"supersedes","source":"DEC-007","target":"DEC-003"}],"revision":16,"snapshot_hash":"fe8406f8b2fe7a5c2cc52d1e1bcc4b74169fb80387ab4de698340a2ae73cf092","verdict":"BLOCKED","working_id":"WORKING-SPEC-da8f8e96a6ac-proposal-discussion-entry"}
{"affected_ids":["AC-012","DEC-008","DISC-008","REQ-012"],"conflicts":[],"continuity":"continuous","delta":{"added_ids":["AC-012","DEC-008","DISC-008","REQ-012"],"changed_ids":[],"removed_ids":[]},"epoch":"0b7b6982a503435f85ab06aa048f0b38","event_hash":"44ce0e1c1c9fe77378be685f4de06d2d7878dee324be99074f357a4c7c712dfd","event_type":"reconcile","event_version":1,"open_decisions":[],"previous_event_hash":"f65d9a6939727d60d16000a36e832bd07451231e35733459196cc0e16b778587","previous_snapshot_hash":"fe8406f8b2fe7a5c2cc52d1e1bcc4b74169fb80387ab4de698340a2ae73cf092","recorded_at":"2026-09-18T10:21:09.544162+00:00","relationships":[{"relation":"refines","source":"REQ-004","target":"SPEC-0024"},{"relation":"supersedes","source":"DEC-004","target":"DEC-001"},{"relation":"supersedes","source":"DEC-007","target":"DEC-003"},{"relation":"refines","source":"REQ-012","target":"SPEC-0030"}],"revision":17,"snapshot_hash":"1b9ddf942d7b0b6b539271600d19584119a521a1d97c91bda2f0096bfe986475","verdict":"PASS","working_id":"WORKING-SPEC-da8f8e96a6ac-proposal-discussion-entry"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"0b7b6982a503435f85ab06aa048f0b38","event_hash":"5acb63b8eb8bbc6880a64fba0b66c9f5c02f7298deac8a5e7f8f3857fba40741","event_type":"materialize","event_version":1,"open_decisions":[],"previous_event_hash":"44ce0e1c1c9fe77378be685f4de06d2d7878dee324be99074f357a4c7c712dfd","previous_snapshot_hash":"1b9ddf942d7b0b6b539271600d19584119a521a1d97c91bda2f0096bfe986475","recorded_at":"2026-09-18T10:21:20.952308+00:00","relationships":[],"revision":17,"snapshot_hash":"b17703b449024715075796b2612def5758efa7fdc723eddd2c73574157806aa3","verdict":"PASS","working_id":"WORKING-SPEC-da8f8e96a6ac-proposal-discussion-entry"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"discussion":{"goal":"開始執行 specs/SPEC-0029-proposal-discussion-entry.md","historical_entry_evidence":"not-inferred","kind":"entry","source_ref":"01a0b40b-3d33-7d71-9e7b-766e8a9ae38c","task_ref":"01a0b3c1-92b2-7401-882d-d2454d749656","turn_id":"01a0b40b-3cb8-7783-b328-626f8d9b0af1"},"removed_ids":[]},"epoch":"0b7b6982a503435f85ab06aa048f0b38","event_hash":"f9dc431d09c36fbf53a29c9bd196f1ed88b6b200ae1d5ed580ae934c0a8ba8e7","event_type":"discussion","event_version":1,"open_decisions":[],"previous_event_hash":"5acb63b8eb8bbc6880a64fba0b66c9f5c02f7298deac8a5e7f8f3857fba40741","previous_snapshot_hash":"b17703b449024715075796b2612def5758efa7fdc723eddd2c73574157806aa3","recorded_at":"2026-09-18T11:44:11.186107+00:00","relationships":[],"revision":17,"snapshot_hash":"b17703b449024715075796b2612def5758efa7fdc723eddd2c73574157806aa3","verdict":"PASS","working_id":"WORKING-SPEC-da8f8e96a6ac-proposal-discussion-entry"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"discussion":{"binding":{"revision":17,"snapshot_hash":"b17703b449024715075796b2612def5758efa7fdc723eddd2c73574157806aa3","working_id":"WORKING-SPEC-da8f8e96a6ac-proposal-discussion-entry"},"candidates":[],"kind":"saved","reply_sha256":"b10983782b85452ec4233bb7387236ac57a1239edea52cbb3fe3b7828c637799","reply_stage":"prepared-until-host-stop","source_ref":"prepared-final:SPEC-0029:01a0b40b-3cb8-7783-b328-626f8d9b0af1","summary":"Authorized SPEC-0029 revision 17 implemented locally. 562 Python tests passed and 2 POSIX cases skipped. Windows installer/ACL, release architecture, distribution and release rehearsal passed. Standards and Spec review defects fixed. Formal acceptance remains BLOCKED for real desktop trust/loading/firing, independent traces and actual SPEC-0030 integration. Evidence: artifacts/validation/113edc215a1f40459b30a78e9ea2556c/report.md; managed assessment artifacts/validation/9f3c3f675ce240ed9b8b8fd47854ea02/assessment.json. This late owner entry is not historical proof of initial hook firing. No new user decision, execution grant, commit, publication, installed-plugin replacement or hook trust was inferred.","task_ref":"01a0b3c1-92b2-7401-882d-d2454d749656","turn_id":"01a0b40b-3cb8-7783-b328-626f8d9b0af1"},"removed_ids":[]},"epoch":"0b7b6982a503435f85ab06aa048f0b38","event_hash":"187f20296da0d38b83eeecf86f3e2c93fc9fe64fd5a2d3f9e7cb9f77aa2f0a42","event_type":"discussion","event_version":1,"open_decisions":[],"previous_event_hash":"f9dc431d09c36fbf53a29c9bd196f1ed88b6b200ae1d5ed580ae934c0a8ba8e7","previous_snapshot_hash":"b17703b449024715075796b2612def5758efa7fdc723eddd2c73574157806aa3","recorded_at":"2026-09-18T11:44:11.336200+00:00","relationships":[],"revision":17,"snapshot_hash":"b17703b449024715075796b2612def5758efa7fdc723eddd2c73574157806aa3","verdict":"PASS","working_id":"WORKING-SPEC-da8f8e96a6ac-proposal-discussion-entry"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"discussion":{"goal":"提出開始執行與 SPEC 編號簡寫相容方案，僅討論，不修改產品","historical_entry_evidence":"not-inferred","kind":"entry","source_ref":"01a0b48b-5d14-7512-b1af-8ff15c52b725","task_ref":"01a0b3c1-92b2-7401-882d-d2454d749656","turn_id":"01a0b48b-5c94-7010-b1a4-1ecd91d98d9c"},"removed_ids":[]},"epoch":"0b7b6982a503435f85ab06aa048f0b38","event_hash":"23b4080a246859ae4eb2e8692e00ff75ff36929609ce4c5b53d3c7fd48b2a8b9","event_type":"discussion","event_version":1,"open_decisions":[],"previous_event_hash":"187f20296da0d38b83eeecf86f3e2c93fc9fe64fd5a2d3f9e7cb9f77aa2f0a42","previous_snapshot_hash":"b17703b449024715075796b2612def5758efa7fdc723eddd2c73574157806aa3","recorded_at":"2026-09-18T12:44:37.632331+00:00","relationships":[],"revision":17,"snapshot_hash":"b17703b449024715075796b2612def5758efa7fdc723eddd2c73574157806aa3","verdict":"PASS","working_id":"WORKING-SPEC-da8f8e96a6ac-proposal-discussion-entry"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"discussion":{"binding":{"revision":17,"snapshot_hash":"b17703b449024715075796b2612def5758efa7fdc723eddd2c73574157806aa3","working_id":"WORKING-SPEC-da8f8e96a6ac-proposal-discussion-entry"},"candidates":[{"id":"execution-command-aliases","impact":"Align skill guidance, intent parser, SPEC lookup and admission; preserve task/version binding and reject negation, quotation and unresolved target ambiguity.","reason":"Restore short execution commands and remove mandatory-looking full paths.","source_ref":"01a0b48b-5d14-7512-b1af-8ff15c52b725","status":"candidate"}],"kind":"saved","reply_sha256":"6dc129b0c5aaf633063ef19f5a66957ca73499836d2094b15f53e53734851aba","reply_stage":"prepared-until-host-stop","source_ref":"prepared-proposal:01a0b48b-5c94-7010-b1a4-1ecd91d98d9c","summary":"User requests a proposal to support short execution commands. Observed workflow_selection.py only matches bare phrase or canonical path; spec_delivery.py likewise accepts bare phrase or exact relative path. Proposed consistent parsing/target resolution/admission plus skills/docs and regression coverage. Include bare SPEC suffix as current-context alias and explicit SPEC ID with or without spacing. No candidate adoption or product implementation grant inferred; SPEC-0029 revision remains unchanged.","task_ref":"01a0b3c1-92b2-7401-882d-d2454d749656","turn_id":"01a0b48b-5c94-7010-b1a4-1ecd91d98d9c"},"removed_ids":[]},"epoch":"0b7b6982a503435f85ab06aa048f0b38","event_hash":"abe94829550ce2b092b18b526793e16671b3ccbec3e7a258d5329f090c1a465f","event_type":"discussion","event_version":1,"open_decisions":[],"previous_event_hash":"23b4080a246859ae4eb2e8692e00ff75ff36929609ce4c5b53d3c7fd48b2a8b9","previous_snapshot_hash":"b17703b449024715075796b2612def5758efa7fdc723eddd2c73574157806aa3","recorded_at":"2026-09-18T12:45:40.998861+00:00","relationships":[],"revision":17,"snapshot_hash":"b17703b449024715075796b2612def5758efa7fdc723eddd2c73574157806aa3","verdict":"PASS","working_id":"WORKING-SPEC-da8f8e96a6ac-proposal-discussion-entry"}
{"affected_ids":[],"baseline_contract_hash":"8f3edbede8ff9f99bd17637e2f4cbd6e63e448e226b20e69c5ba2f2ef3a8343d","conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"0b7b6982a503435f85ab06aa048f0b38","event_hash":"620a19c8ef591247ef45d25d6773c30d6f9017c0928adb76e99d4a8247a447f0","event_type":"reopen","event_version":1,"open_decisions":[],"previous_event_hash":"abe94829550ce2b092b18b526793e16671b3ccbec3e7a258d5329f090c1a465f","previous_snapshot_hash":"b17703b449024715075796b2612def5758efa7fdc723eddd2c73574157806aa3","recorded_at":"2026-09-18T13:11:05.267509+00:00","relationships":[],"revision":18,"snapshot_hash":"f323891bcd1f025da4449a1b4f08094749d73744088ae4d725d031b98e9cb147","verdict":"BLOCKED","working_id":"WORKING-SPEC-da8f8e96a6ac-proposal-discussion-entry"}
{"affected_ids":["AC-013","AC-014","AC-015","AC-016","AC-017","DEC-009","DISC-009","REQ-013","REQ-014","REQ-015","REQ-016","REQ-017"],"conflicts":[],"continuity":"continuous","delta":{"added_ids":["AC-013","AC-014","AC-015","AC-016","AC-017","DEC-009","DISC-009","REQ-013","REQ-014","REQ-015","REQ-016","REQ-017"],"changed_ids":[],"removed_ids":[]},"epoch":"0b7b6982a503435f85ab06aa048f0b38","event_hash":"2ea09502011744d1b9dbb695ade78d267501a1dd044862ff4094b720111ee0fc","event_type":"reconcile","event_version":1,"open_decisions":[],"previous_event_hash":"620a19c8ef591247ef45d25d6773c30d6f9017c0928adb76e99d4a8247a447f0","previous_snapshot_hash":"f323891bcd1f025da4449a1b4f08094749d73744088ae4d725d031b98e9cb147","recorded_at":"2026-09-18T13:11:05.325906+00:00","relationships":[{"relation":"refines","source":"REQ-004","target":"SPEC-0024"},{"relation":"supersedes","source":"DEC-004","target":"DEC-001"},{"relation":"supersedes","source":"DEC-007","target":"DEC-003"},{"relation":"refines","source":"REQ-012","target":"SPEC-0030"},{"relation":"refines","source":"REQ-013","target":"REQ-002"},{"relation":"refines","source":"REQ-014","target":"REQ-003"},{"relation":"refines","source":"REQ-015","target":"REQ-003"},{"relation":"refines","source":"REQ-016","target":"REQ-005"},{"relation":"refines","source":"REQ-017","target":"REQ-007"},{"relation":"refines","source":"REQ-017","target":"REQ-008"}],"revision":19,"snapshot_hash":"eae469a276740f7d699ea5ff4180c6ea18bdcbe8e0431ac97047ba505eff1d14","verdict":"PASS","working_id":"WORKING-SPEC-da8f8e96a6ac-proposal-discussion-entry"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"0b7b6982a503435f85ab06aa048f0b38","event_hash":"616431a05783fdd9e69a4b4f4b27f45ac9be0878e75924c145355169f1f65280","event_type":"materialize","event_version":1,"open_decisions":[],"previous_event_hash":"2ea09502011744d1b9dbb695ade78d267501a1dd044862ff4094b720111ee0fc","previous_snapshot_hash":"eae469a276740f7d699ea5ff4180c6ea18bdcbe8e0431ac97047ba505eff1d14","recorded_at":"2026-09-18T13:11:05.389282+00:00","relationships":[],"revision":19,"snapshot_hash":"fbb1d234aa9f07205862382022bec51ea7ce05dd0d0dbeec2ea000daa9b63e82","verdict":"PASS","working_id":"WORKING-SPEC-da8f8e96a6ac-proposal-discussion-entry"}
{"affected_ids":[],"baseline_contract_hash":"89b284c985e0db89c450fdf57f82be344ce442a090428cd0006a32329aefe80c","conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"0b7b6982a503435f85ab06aa048f0b38","event_hash":"faa079e2d30bc5acc3e69583656605536640c4f8fc9f58747846f339b60692cb","event_type":"reopen","event_version":1,"open_decisions":[],"previous_event_hash":"616431a05783fdd9e69a4b4f4b27f45ac9be0878e75924c145355169f1f65280","previous_snapshot_hash":"fbb1d234aa9f07205862382022bec51ea7ce05dd0d0dbeec2ea000daa9b63e82","recorded_at":"2026-09-18T14:26:33.907206+00:00","relationships":[],"revision":20,"snapshot_hash":"caba8d2c444ad1b073b2455c8e35eacfcffb1963bb7d2d90686950d1f000f37b","verdict":"BLOCKED","working_id":"WORKING-SPEC-da8f8e96a6ac-proposal-discussion-entry"}
{"affected_ids":["AC-002","AC-003","AC-013","AC-017","AC-018","DEC-010","DISC-010","REQ-002","REQ-003","REQ-005","REQ-009","REQ-013","REQ-017","REQ-018"],"conflicts":[],"continuity":"continuous","delta":{"added_ids":["AC-018","DEC-010","DISC-010","REQ-018"],"changed_ids":["AC-002","AC-003","AC-013","AC-017","REQ-002","REQ-003","REQ-005","REQ-009","REQ-013","REQ-017"],"removed_ids":[]},"epoch":"0b7b6982a503435f85ab06aa048f0b38","event_hash":"6646c841af84dae811a6b33d186f3e3ce725b61e295a5863f90af861fd9637fc","event_type":"reconcile","event_version":1,"open_decisions":[],"previous_event_hash":"faa079e2d30bc5acc3e69583656605536640c4f8fc9f58747846f339b60692cb","previous_snapshot_hash":"caba8d2c444ad1b073b2455c8e35eacfcffb1963bb7d2d90686950d1f000f37b","recorded_at":"2026-09-18T14:26:33.969653+00:00","relationships":[{"relation":"refines","source":"REQ-004","target":"SPEC-0024"},{"relation":"supersedes","source":"DEC-004","target":"DEC-001"},{"relation":"supersedes","source":"DEC-007","target":"DEC-003"},{"relation":"refines","source":"REQ-012","target":"SPEC-0030"},{"relation":"refines","source":"REQ-013","target":"REQ-002"},{"relation":"refines","source":"REQ-014","target":"REQ-003"},{"relation":"refines","source":"REQ-015","target":"REQ-003"},{"relation":"refines","source":"REQ-016","target":"REQ-005"},{"relation":"refines","source":"REQ-017","target":"REQ-007"},{"relation":"refines","source":"REQ-017","target":"REQ-008"},{"relation":"supersedes","source":"DEC-010","target":"DEC-002"},{"relation":"refines","source":"DEC-010","target":"DEC-009"},{"relation":"refines","source":"REQ-018","target":"REQ-005"}],"revision":21,"snapshot_hash":"6624ee6e2e1467e24790a896a0a7c5f2427f4fc8abaaa4334fd72c0b38f1cd64","verdict":"PASS","working_id":"WORKING-SPEC-da8f8e96a6ac-proposal-discussion-entry"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"0b7b6982a503435f85ab06aa048f0b38","event_hash":"5c09eec901c0d013951ad5c8f28a5533c0649811191f586dc700c327071867c9","event_type":"materialize","event_version":1,"open_decisions":[],"previous_event_hash":"6646c841af84dae811a6b33d186f3e3ce725b61e295a5863f90af861fd9637fc","previous_snapshot_hash":"6624ee6e2e1467e24790a896a0a7c5f2427f4fc8abaaa4334fd72c0b38f1cd64","recorded_at":"2026-09-18T14:26:34.038171+00:00","relationships":[],"revision":21,"snapshot_hash":"8eab7ab2061c51bcaf895b0c5e09f4046728b1a6a28c1f6755284e5eba2bc074","verdict":"PASS","working_id":"WORKING-SPEC-da8f8e96a6ac-proposal-discussion-entry"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"legacy_journal":"spec-governance/WORKING-SPEC-da8f8e96a6ac-proposal-discussion-entry.journal.jsonl","legacy_notes":[],"legacy_snapshot":"spec-governance/WORKING-SPEC-da8f8e96a6ac-proposal-discussion-entry.md","removed_ids":[]},"epoch":"0b7b6982a503435f85ab06aa048f0b38","event_hash":"0199882325e232f9f30e5050ca2462e1b6e014e04564ff5b4b0ac6af3272ebe4","event_type":"migration","event_version":1,"open_decisions":[],"previous_event_hash":"5c09eec901c0d013951ad5c8f28a5533c0649811191f586dc700c327071867c9","previous_snapshot_hash":"8eab7ab2061c51bcaf895b0c5e09f4046728b1a6a28c1f6755284e5eba2bc074","recorded_at":"2026-09-18T15:22:46.340659+00:00","relationships":[],"revision":21,"snapshot_hash":"8eab7ab2061c51bcaf895b0c5e09f4046728b1a6a28c1f6755284e5eba2bc074","verdict":"PASS","working_id":"WORKING-SPEC-da8f8e96a6ac-proposal-discussion-entry"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"discussion":{"goal":"開始執行SPEC-0029/0030  \n","historical_entry_evidence":"not-inferred","kind":"entry","source_ref":"01a0b500-9da6-7352-ae72-801f6c530932","task_ref":"01a0b3c1-92b2-7401-882d-d2454d749656","turn_id":"01a0b500-9d21-7001-b6f9-aa12d74a43c0"},"removed_ids":[]},"epoch":"0b7b6982a503435f85ab06aa048f0b38","event_hash":"f70b8329030cb5ed7de2d3214daeaa3ebc82cd6d5c16625711bc100c14ed5bd6","event_type":"discussion","event_version":1,"open_decisions":[],"previous_event_hash":"0199882325e232f9f30e5050ca2462e1b6e014e04564ff5b4b0ac6af3272ebe4","previous_snapshot_hash":"8eab7ab2061c51bcaf895b0c5e09f4046728b1a6a28c1f6755284e5eba2bc074","recorded_at":"2026-09-18T15:22:46.351315+00:00","relationships":[],"revision":21,"snapshot_hash":"8eab7ab2061c51bcaf895b0c5e09f4046728b1a6a28c1f6755284e5eba2bc074","verdict":"PASS","working_id":"WORKING-SPEC-da8f8e96a6ac-proposal-discussion-entry"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":[],"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"0b7b6982a503435f85ab06aa048f0b38","event_hash":"b9f30d32f2cb552e55b4ee90a5eb241baeda154011d146d4404480c0b38a04fe","event_type":"reconcile","event_version":1,"open_decisions":[],"previous_event_hash":"f70b8329030cb5ed7de2d3214daeaa3ebc82cd6d5c16625711bc100c14ed5bd6","previous_snapshot_hash":"8eab7ab2061c51bcaf895b0c5e09f4046728b1a6a28c1f6755284e5eba2bc074","recorded_at":"2026-09-18T15:50:11.579585+00:00","relationships":[{"relation":"refines","source":"REQ-004","target":"SPEC-0024"},{"relation":"supersedes","source":"DEC-004","target":"DEC-001"},{"relation":"supersedes","source":"DEC-007","target":"DEC-003"},{"relation":"refines","source":"REQ-012","target":"SPEC-0030"},{"relation":"refines","source":"REQ-013","target":"REQ-002"},{"relation":"refines","source":"REQ-014","target":"REQ-003"},{"relation":"refines","source":"REQ-015","target":"REQ-003"},{"relation":"refines","source":"REQ-016","target":"REQ-005"},{"relation":"refines","source":"REQ-017","target":"REQ-007"},{"relation":"refines","source":"REQ-017","target":"REQ-008"},{"relation":"supersedes","source":"DEC-010","target":"DEC-002"},{"relation":"refines","source":"DEC-010","target":"DEC-009"},{"relation":"refines","source":"REQ-018","target":"REQ-005"}],"revision":22,"snapshot_hash":"413c97822c92e1dde9d9de1866c6a8686e30d5d558bd6f98599956f1dbffbf30","verdict":"PASS","working_id":"WORKING-SPEC-da8f8e96a6ac-proposal-discussion-entry"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"0b7b6982a503435f85ab06aa048f0b38","event_hash":"0e0d8a5f0b7aa2fc3ba2171b9e844a0d7f512e200007389d947868be120ec1b5","event_type":"materialize","event_version":1,"open_decisions":[],"previous_event_hash":"b9f30d32f2cb552e55b4ee90a5eb241baeda154011d146d4404480c0b38a04fe","previous_snapshot_hash":"413c97822c92e1dde9d9de1866c6a8686e30d5d558bd6f98599956f1dbffbf30","recorded_at":"2026-09-18T15:50:11.690496+00:00","relationships":[],"revision":22,"snapshot_hash":"0e1dab8f8b39fe0c4a331c964150ef084b39900b12c03e7904e4057c65ed7d13","verdict":"PASS","working_id":"WORKING-SPEC-da8f8e96a6ac-proposal-discussion-entry"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"discussion":{"binding":{"revision":22,"snapshot_hash":"0e1dab8f8b39fe0c4a331c964150ef084b39900b12c03e7904e4057c65ed7d13","working_id":"WORKING-SPEC-da8f8e96a6ac-proposal-discussion-entry"},"candidates":[],"completeness_review":null,"kind":"saved","reply_sha256":"4e7262037cc16ad6637bb27e64593ed43552ec51e98899c67320cac34f8427fa","reply_stage":"prepared-until-host-stop","source_ref":"01a0b500-9da6-7352-ae72-801f6c530932","summary":"完成 SPEC-0029/0030 原始碼、skill 與人類文件修改。單檔工作 SPEC、持續保存、完整性審查、自動確認、舊雙檔驗證遷移；能力與 gate 結果分離、AC 新增刪除與同 ID 語意差異、criterion_sha256、結構化診斷及有限恢復；組合 SPEC 授權完整綁定。SPEC0029 r22 和 SPEC0030 r2 僅補上派生閱讀視圖，未變更確認需求。來源與補存額度保留。插件回歸 308 項 PASS: artifacts/tests/e25d227a3eaf418298d8deabe2e48178/manifest.json；驗證規劃 31 項 PASS: artifacts/tests/536b8233fc6e432cbaaed0aba51aa918/manifest.json；封裝 38 項中 36 PASS/2 skipped: artifacts/tests/5091a3291a4a43e493039f03fc6d300d/manifest.json。實際當前來源事件組合授權 admission 已 PASS（非宿主認證）。未執行安裝、信任變更、提交或發布。真實桌面 hook firing、多輪 trace 與完整 AC 驗收仍未證明，不能以單元測試代替。狀態保持 confirmed，未標記 implemented。","task_ref":"01a0b3c1-92b2-7401-882d-d2454d749656","turn_id":"01a0b500-9d21-7001-b6f9-aa12d74a43c0"},"removed_ids":[]},"epoch":"0b7b6982a503435f85ab06aa048f0b38","event_hash":"4903b5ca1ab744c13e95ca1658071b756a011a4b7f944b5a968ed73e3a19837e","event_type":"discussion","event_version":1,"open_decisions":[],"previous_event_hash":"0e0d8a5f0b7aa2fc3ba2171b9e844a0d7f512e200007389d947868be120ec1b5","previous_snapshot_hash":"0e1dab8f8b39fe0c4a331c964150ef084b39900b12c03e7904e4057c65ed7d13","recorded_at":"2026-09-18T15:51:02.888527+00:00","relationships":[],"revision":22,"snapshot_hash":"0e1dab8f8b39fe0c4a331c964150ef084b39900b12c03e7904e4057c65ed7d13","verdict":"PASS","working_id":"WORKING-SPEC-da8f8e96a6ac-proposal-discussion-entry"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"discussion":{"goal":"安裝測試版後，開始測試","historical_entry_evidence":"not-inferred","kind":"entry","source_ref":"01a0b54d-1aaa-7390-a0c3-a7cd312b2df2","task_ref":"01a0b3c1-92b2-7401-882d-d2454d749656","turn_id":"01a0b54d-19e8-7912-b91c-9d50e22b92ac"},"removed_ids":[]},"epoch":"0b7b6982a503435f85ab06aa048f0b38","event_hash":"090aeb307433fbc7dfb926636e7637c2dcfd1b66b7b28ec1d7ea5fd0c63f93e9","event_type":"discussion","event_version":1,"open_decisions":[],"previous_event_hash":"4903b5ca1ab744c13e95ca1658071b756a011a4b7f944b5a968ed73e3a19837e","previous_snapshot_hash":"0e1dab8f8b39fe0c4a331c964150ef084b39900b12c03e7904e4057c65ed7d13","recorded_at":"2026-09-18T16:18:39.039717+00:00","relationships":[],"revision":22,"snapshot_hash":"0e1dab8f8b39fe0c4a331c964150ef084b39900b12c03e7904e4057c65ed7d13","verdict":"PASS","working_id":"WORKING-SPEC-da8f8e96a6ac-proposal-discussion-entry"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"discussion":{"binding":{"revision":22,"snapshot_hash":"0e1dab8f8b39fe0c4a331c964150ef084b39900b12c03e7904e4057c65ed7d13","working_id":"WORKING-SPEC-da8f8e96a6ac-proposal-discussion-entry"},"candidates":[],"completeness_review":null,"kind":"saved","reply_sha256":"6aef78e23afc8ab49b7aa32900095e01ea097080abf6f640d727b9a16f9f7bd3","reply_stage":"prepared-until-host-stop","source_ref":"01a0b54d-1aaa-7390-a0c3-a7cd312b2df2","summary":"使用者明確授權安裝測試版並測試。已用目前桌面實際 runtime 0.155.0-alpha.9 的 plugin add 成功安裝 governed-engineering-skills@governed-engineering-development 0.16.0+codex.local-20260918161704513960，快取內容雜湊293檔一致。以該安裝快取執行 Windows launcher/owner smoke：初始化、工程分類、單檔保存、正確回覆Stop、漏存最多一次修復、Python缺失拒絕，共4檢查PASS。不可冒稱真實桌面事件觸發。證據 artifacts/tests/116bbe01f01040cf927b4b1729f11667/manifest.json；spec-governance/installed-package-test.json。用相同桌面runtime app-server hooks/list只讀查詢，四事件sessionStart/userPromptSubmit/preToolUse/stop loaded enabled但全部untrusted。未修改信任、未使用bypass。真實桌面驗收仍BLOCKED等待宿主hook審閱/信任。當前任務cwd在父目錄，測試需以實際repo根C:/Users/hugo_peng/skill/skills開新任務以匹配紀錄/Python。已開啟插件頁並排入hook定義檢視。正式release未替換，未提交發布。","task_ref":"01a0b3c1-92b2-7401-882d-d2454d749656","turn_id":"01a0b54d-19e8-7912-b91c-9d50e22b92ac"},"removed_ids":[]},"epoch":"0b7b6982a503435f85ab06aa048f0b38","event_hash":"f3268c4be3d2ee33892bc20bece53866e75d4d889ded04590605c91606bde45c","event_type":"discussion","event_version":1,"open_decisions":[],"previous_event_hash":"090aeb307433fbc7dfb926636e7637c2dcfd1b66b7b28ec1d7ea5fd0c63f93e9","previous_snapshot_hash":"0e1dab8f8b39fe0c4a331c964150ef084b39900b12c03e7904e4057c65ed7d13","recorded_at":"2026-09-18T16:24:37.314189+00:00","relationships":[],"revision":22,"snapshot_hash":"0e1dab8f8b39fe0c4a331c964150ef084b39900b12c03e7904e4057c65ed7d13","verdict":"PASS","working_id":"WORKING-SPEC-da8f8e96a6ac-proposal-discussion-entry"}
```
<!-- spec-audit:end -->
