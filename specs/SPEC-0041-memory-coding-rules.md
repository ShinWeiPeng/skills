---
spec_version: 1
spec_id: SPEC-0041
revision: 36
status: implemented
change_set: memory-coding-rules
working_id: WORKING-SPEC-b8886a6cd704-memory-coding-rules
task_ref: 01a0eb0c-4931-7112-8cdf-8862d42e984b
---

# 新增程式規則：記憶體、邊界異常事件與資料流

## Problem
本對話要求將既有程式規則治理重整與新增程式規則分開規劃，避免搬移時混入新限制。

## Solution
新增記憶體、邊界異常事件、資料流、模組與公開介面契約及設計文件規則。本文件為討論中的工作 SPEC，尚未確認或取得實作授權。

## User Stories
所有專案使用共用且可持續修訂的分檔規則，依各專案平台與執行路徑套用。

## Requirements
| ID | Requirement |
|---|---|
| REQ-001 | 新增規則與治理搬移分開 SPEC；使用已選定 coding-standards 機制發布。 |
| REQ-002 | 通用安全、資源限制、配置策略可共同套用。一般路徑允許動態配置；受限路徑須說明配置與釋放策略符合預算和期限，否則採預配置、固定容量或適當記憶體池。零 heap 配置由專案對路徑明定。 |
| REQ-003 | 有限容量緩衝區、佇列與記憶體池必須定義耗盡行為；不得靜默覆寫仍使用資料、無上限擴容或違反配置／等待限制。具體行為由專案選定。 |
| REQ-004 | 採方案 B：單一擁有者為預設；轉移、借用與有條件共享均須定義權限及生命週期。共享需明確存活追蹤、回收及同步方式並符合限制。 |
| REQ-005 | 成功、失敗、取消及逾時均有資源收尾；非同步使用結束前不得回收／重用。共享生命週期不授予共享修改權限。不強制特定語言智慧指標。 |

| REQ-006 | 採 B+C：外部輸入及跨信任邊界先驗證大小計算、有效長度與容量；內部依明確契約使用。優先以型別或靜態限制提供保證，無法證明安全處補執行期檢查；資料或狀態變更使保證失效時重驗。不得把型別包裝本身當作安全證明。 |

| REQ-007 | 所有模組的邊界驗證異常均須有結構化異常事件出口，供後續 log 或異常處理使用；不限記憶體管理。分派、失敗與狀態語意依 REQ-009 至 REQ-012、REQ-023。 |
| REQ-008 | 原無條件聚合要求已由 REQ-015 取代；內外部資料流仍須明定容量、接收、部分完成、持有、觸發及耗盡語意，適用聚合與背壓的方法依情境選擇。 |

| REQ-009 | 異常處理採方案 C：模組發現邊界異常時，立即完成必要保護、停止非法操作並使狀態符合契約，再透過異常事件觸發 log、通知與後續復原。必要保護不得依賴事件消費成功；ISR／硬即時路徑回報須有界且不阻塞。事件分派方式依專案執行環境決定，不強制新增執行緒。 |

| REQ-010 | 高頻重複異常採方案 C：首次立即提交事件，不等待 log 完成；同一異常持續發生時累計並依專案期限聚合回報。每次異常仍執行必要保護。專案須定義聚合識別、期限與結束條件，不自行假設固定全域數值。 |

| REQ-011 | 異常事件出口滿載採方案 B：維持專案定義的有限容量，接收新事件時移除最舊待送事件並累計覆寫數量；保留最新事件。不得無界擴容，不因覆寫递迴產生新異常。必要保護仍每次立即執行。已被消費者借用的記憶體不得直接覆寫；以安全所有權交接實作邏輯上的移除最舊事件。 |

| REQ-012 | 持續影響模組行為的故障須由其模組擁有者保存有界狀態；事件通知被覆寫不得清除該狀態或推定已恢復。由擁有者依實際恢復條件更新狀態，外部只能透過契約查詢或請求操作。單次拒收等不持續影響行為的異常不強制新增故障狀態。復原流程進度由負責該流程的擁有者管理，與模組狀態分清責任。 |

| REQ-013 | 聚合批次達容量門檻或最長聚合等待時間任一條件時，必須結束等待聚合並提出送出；Stop 時依明確契約處理剩餘資料。容量門檻與時間依專案需求和資源預算決定，不設定通用數值。下游背壓仍有效；觸發送出不代表下游已接受或已完成交付。 |

| REQ-014 | Stop 採方案 C 限時排空：停止接收新資料，在專案指定期限內送出已接受資料；逾時依契約取消可安全取消的剩餘資料並回報異常及未完成量。下游仍持有引用時不得回收或覆寫，須完成安全取消或釋放交接；停止期限不得被誤認為保證底層已釋放。 |

| REQ-015 | 資料流依情境選擇聚合與背壓，並明確交代實作方法；本條取代 REQ-008 中所有內外部傳送一律採用的部分。每次複製、bank 與緩衝須有用途及預算，保留原容量、所有權及耗盡約束。適用性分析涵蓋單入單出、多入單出（多命令來源）、單入多出（同一 IMU 多介面輸出）及組合資料流；拓撲本身不代表必須聚合。 |

| REQ-016 | 多命令來源由產品內部執行單元接收；使用者指定透過 mutex 保護 sequence，buffer 項目須攜帶來源資料。sequence 的排序語意、與入列的原子性、来源識別格式及不允許 mutex 的執行環境需在設計中明定，不推定 mutex 自動保證來源公平性。 |
| REQ-017 | 單來源多輸出採共享資料方向，各輸出介面不得因慢速分支被拖住；使用者要求各輸出 baudrate 相同並提出類似 RCU。baudrate 是資料頻率或實體傳輸速率尚待釐清；RCU 為候選實作概念，不能直接視為已採用 Linux RCU 或零遺失保證。 |

| REQ-018 | REQ-017 的相同 baudrate 明確指相同資料頻率，不是介面實體傳輸速率；各介面承載同一來源的資料頻率，不要求封包大小或實際傳送瞬間一致。慢介面不得拖住其他介面的要求維持；暫時落後、丟棄或停止該分支的政策尚待選定。 |
| REQ-019 | 每條新增或受影響資料流，在設計確認前向使用者呈現實作設計表，包含情境與要求、候選及選定方法、資料與複製路徑、容量與所有權、協調、異常／Stop、理由與驗證。實作後對照真實程式核對，契約變更先更新設計並依既有確認／授權流程處理。不能只保存檔案而未向使用者呈現。 |
| REQ-020 | 每個模組都須有實作設計表，明定責任、輸入輸出、方法／演算法、型別與狀態所有權、執行與同步、記憶體／資源、邊界異常、生命週期、依賴與驗證；與資料流設計互相引用。模組實作前呈現，實作後核對；可查明的事實由 Codex 調查，僅未決行為取捨詢問使用者。表格格式與呈現／核對程序由階段規範管理，純程式規則不混入流程。 |

| REQ-021 | 多輸出慢分支容量耗盡採方案 C：依用途在設計表明定跳過舊資料或停止該分支等處置及觸發條件；即時顯示可選跳過並記錄缺口、發出異常事件，完整記錄可選停止並保存異常狀態、發出事件。這些是用途範例，不將所有介面固定分類；其他分支不被拖住，容量與共享生命週期約束維持。相同資料頻率是正常輸出契約，異常跳過不等於授權常態降採樣；不得覆寫仍在使用中的資料。 |

| REQ-022 | 操作失敗狀態採方案 C：每種操作在模組／資料流實作設計表中明定成功、失敗與部分完成語意。一般設定等操作預先驗證，失敗保留原狀；串流等可能部分完成的操作明確回報已完成及未完成範圍，定義完成層級及剩餘資料的保留、取消或續傳方式。依既有規則執行必要保護與異常事件，不得留下未定義的中間狀態，也不得將已發生的外部效果宣稱為未發生。 |

| REQ-023 | 對於專案要求必須執行的異常復原，不得只依賴可覆寫事件；須能從持續狀態重新發現未完成工作並重新觸發。由專案在設計表明定責任擁有者、重新發現及觸發機制與期限，不強制統一輪詢。模組故障狀態與復原流程進度各有擁有者；狀態與資源須有界，事件被覆寫不代表復原已完成。此要求不保證外部永久故障一定可恢復，也不授權無限重試。 |

| REQ-024 | 特殊資料流依情境適用：不可暫停來源須明定容量耗盡與資料遺失處置，不宣稱背壓可使來源停止或有限容量可保證無限期無損；即時控制以截止時間判斷是否聚合；硬體必要的 bank 可使用，但須在設計表說明必要性、容量、複製及所有權。各情境均保留既有安全、容量、生命週期與異常處理要求；特定實作與參數由專案決定。 |

| REQ-025 | 新增規則採 MUST／SHOULD／MAY 分級：已採用的必要安全、容量、所有權、異常處理及設計呈現／核對要求列 MUST，依條款適用條件生效；額外最佳化建議列 SHOULD，未採用須在設計表說明理由；可選實作方法列 MAY，但仍須符合 MUST。不得以 SHOULD 或 MAY 降低已採用的必要要求。既有規則強度及例外政策維持；設計呈現／核對等流程要求仍放階段規範，純程式規則文件不混入流程。 |

| REQ-026 | 採用模組化設計補強：設計確認前明列每個模組的責任／非責任、共同外部契約、內部可變實作、狀態所有權與外部依賴；未釐清時不得宣稱設計完成或進入相關實作。實作後核對呼叫端對內部演算法及私有狀態的依賴，對宣稱可替換的實作驗證共同外部契約。不得將模組化等同固定檔案數、固定 GET／事件佇列或所有演算法相同。既有義務由 SPEC-0040 搬移，新增明確檢查及驗收義務由本 SPEC 引入。 |

| REQ-027 | 模組設計採十二組欄位：識別與範圍、責任與非責任、外部介面契約、共同不變條件、可變實作與選擇、型別與狀態所有權、內部處理方法、依賴與交互邊界、執行與同步、資源與時間、異常與生命週期、實作與驗證追溯；介面、狀態轉移等以子表呈現。引用既有 manifest／catalog ID，由唯一維護來源產生文件，必要時正式擴充 schema，不另手寫重複事實。無關項目註明不適用及理由，未知事項標待確認；計畫與已實作／已驗證分清，不為填表製造替代實作。設計來源描述預期行為，仍須對照程式與證據。 |

| REQ-028 | 模組介面依操作完成程度選擇：返回前已完成的操作可同步回傳結果，包括狀態更新操作；契約須明定完成範圍、狀態更新、失敗／部分完成及資料所有權。返回時只接受但尚未完成的工作，回傳接受結果，後續另行提供完成／失敗通知及關聯。對其他訂閱者的事件另依契約發布，不與呼叫回傳混為一談；邊界異常事件、持續故障狀態及必要保護要求維持。此項在 SPEC-0041 修訂既有 event-contract.md 的完成回報政策，SPEC-0040 搬移仍保留原語意。 |

| REQ-029 | 資料流設計表採八組欄位：識別與目的、起點與完成終點、路徑與步驟、資料及關聯、所有權與緩衝、執行與時間、傳送與協調、異常停止與驗證；步驟子表列契約引用、同步／非同步方式、完成判定及資料交接。引用既有模組與架構資料，不重複展開私有演算法，不為填表新增佇列／聚合。 |
| REQ-030 | 引數設計依資料用途、修改權限、生命週期與實際成本選擇傳值／傳址，不設通用大小門檻或引數數量硬限制；同一概念的資料可組成結構，不為減少數量硬包裝。介面契約明定讀寫權限、是否保存引用、有效期間與所有權。高頻、硬即時或堆疊受限路徑核對目標 ABI、編譯結果及必要量測。納入既有介面欄位及檢查規範，不新增平行文件。 |

| REQ-031 | 模組文件中每個公開介面採九組子表欄位：介面識別與用途、呼叫條件、輸入參數、參數存取契約、完成與回傳、狀態與副作用、失敗與部分完成、資源與時間、驗證連結。格式由 module-design-format.md 定義，引用既有介面／型別／狀態／規則／驗證 ID，資料流表引用介面 ID，不另建重複函式說明來源。範例的不得空值、不保存位址、序列化、不自行加鎖、不動態配置皆非通用預設；各介面依需求明定。唯讀借用也須交代其他執行單元能否修改相同底層資料及同步保證。 |

## Decisions
| ID | Decision |
|---|---|
| DEC-001 | 使用者已採用配置策略（三類共同適用），及容量耗盡處理條款。 |
| DEC-002 | 使用者以「採用方案B」選定單一擁有者預設與有條件共享。 |
| DEC-003 | 大小計算、有效範圍、外部長度驗證及失敗狀態目前是候選規則；使用者要求比較其他方案，尚未採用。 |
| DEC-004 | 本輪以 B+C 取代 DEC-003 的檢查策略待選狀態：邊界驗證、內部契約與型別／靜態保證搭配；無法證明處仍執行期檢查。檢查失敗後的狀態政策仍待討論。 |

| DEC-005 | 使用者本輪要求各模組邊界異常產生事件以触發後續 log／異常處理，並要求內外部資料傳送採聚合＋背壓；不是「只回傳錯誤」的選項。 |

| DEC-006 | 使用者以「採用C」確認必要保護立即做、後續處理交事件；事件滿載與高頻聚合政策尚未選定。 |

| DEC-007 | 使用者以「採用方案C」選定首次立即通知、後續重複異常聚合。此決定不等於採用事件出口滿載政策。 |

| DEC-008 | 使用者採用事件滿載方案 B，理由為不論哪個方案都有容量限制；接受可能失去最初原因的事件紀錄，不推定每個事件都能處理或寫入 log。 |

| DEC-009 | 使用者註解「採用有模組狀態」，確認事件可覆寫且持續故障另存有界模組狀態。不推定每個異常需新增待處理項目或一律定期輪詢。 |

| DEC-010 | 使用者以「採用」確認容量門檻或最長等待時間任一達成就送出，Stop 依契約處理剩餘資料；容量與時間由專案決定。 |

| DEC-011 | 使用者本輪明確採用 Stop 方案 C；並報告參考專案過夜測試未見 WiFi 異常，但出現 CSV writer backpressure limit exceeded。後者為使用者實測回報，未取得對應韌體／前端雜湊及完整測量紀錄。 |

| DEC-012 | 使用者明確採用「依情境選擇，並要求明確交代實作方法」，補充多入單出／單入多出，並要求改善只在問題發生後才確認實作方式的流程。此決策僅取代 DEC-005 的無條件聚合背壓部分，保留全模組異常事件要求。 |

| DEC-013 | 使用者指定多入單出的內部執行單元、mutex／sequence 與來源資料；多輸出共享資料、介面互不拖慢，提及相同 baudrate 與類似 RCU；未釐清術語不得自動固化成實作。 |

| DEC-014 | 使用者明確回答「資料頻率相同」，採用設計確認前呈現、實作後核對，並要求每個模組也要有實作設計表。此前候選流程本輪獲採用；不推定慢輸出可以降採樣或丟資料。 |

| DEC-015 | 使用者以 C 選定慢輸出容量耗盡依用途處理，於設計確認前明定各分支政策；承接前輪 A 跳過舊資料、B 停止分支、C 依用途選擇的選項。未替特定專案選定門檻、共享實作或恢復方式。 |

| DEC-016 | 使用者在設定修改與傳送 100 筆已送 60 筆中斷的情境說明後，以 C 確認依操作契約定義失敗結果；此決策補足 DEC-004 保留的失敗狀態問題，不強制所有模組同一處理方式。 |

| DEC-017 | 使用者回答採用，確認必須執行的復原工作須能從持續狀態重新發現與觸發，不能只依賴可覆寫通知；具體機制與期限由專案設計表明定。 |

| DEC-018 | 使用者回答採用，確認不可暫停來源、即時控制與硬體必要 bank 的特殊情境原則；不等於授權無必要 bank、靜默遺失或跳過原安全要求。 |

| DEC-019 | 使用者回答採用，確認新增規則的 MUST／SHOULD／MAY 分級及適用條件，既有強度、例外政策與文件責任分工保持不變。 |

| DEC-020 | 使用者採用模組化設計前契約確認與實作後封裝／可替換性核對，並詢問是否須訂對應文件規範。延伸既有 REQ-019、REQ-020 的設計表要求，具體格式與現有 manifest／視圖的關係須說明，避免另建重複事實來源。 |

| DEC-021 | 使用者在釐清權威來源意指唯一維護來源後，以註解採用十二組欄位及引用既有資料、由唯一維護來源產生文件的安排；不推定文件內容即可證明實作符合。 |

| DEC-022 | 使用者採用前輪依完成程度區分的方案，允許返回前已完成、包含狀態更新的操作同步回傳；未完成工作須另行回報完成／失敗，訂閱者通知及異常要求不被取消。 |

| DEC-023 | 使用者先前在回覆資料流設計表時明確說採用，隨後詢問通用技能與傳值／傳址；本輪補記該既有採用，不把保存延遲視為未決或重新授權。 |
| DEC-024 | 使用者本輪回答採用，確認前輪引數設計四項原則：依語意與成本選傳遞方式、無通用引數數量限制、明定參數契約，以及受限／高頻路徑的 ABI 與成本核對。 |

| DEC-025 | 使用者採用前輪九組公開介面子表格式，作為已採用模組文件的具體化；不將 C 同步範例的參數與實作選項升格為所有介面限制。 |

## Acceptance Criteria
| ID | Requirements | Criterion | Validation Method | Evidence |
|---|---|---|---|---|
| AC-001 | REQ-002 | 示範不同平台與路徑的配置策略，不將 MCU 等同禁 heap 或 PC 等同無限制。 | 規則審查及適用性案例；待建立。 | PASS: artifacts/validation/818416f40f8b41c09815a32cad12628b/AC-001-review.json |
| AC-002 | REQ-003 | 耗盡案例有明確行為，禁止回退違反路徑配置／等待限制。 | 正反案例及適用檢查；待建立。 | PASS: artifacts/validation/818416f40f8b41c09815a32cad12628b/AC-002-review.json |
| AC-003 | REQ-004, REQ-005 | 借用、轉移、共享、取消與非同步逾時案例符合生命週期；不將 shared lifetime 當作寫入權限。 | 規則審查及對應案例；待建立。 | PASS: artifacts/validation/818416f40f8b41c09815a32cad12628b/AC-003-review.json |

| AC-004 | REQ-006 | 涵蓋大小溢位、來源有效長度不足、目的容量不足、靜態保證成立及保證失效重驗；未知情況不得視為安全。 | 正反案例與契約檢查；待建立。 | PASS: artifacts/validation/818416f40f8b41c09815a32cad12628b/AC-004-review.json |

| AC-005 | REQ-007 | 驗證邊界拒絕可產生含來源與原因的事件，後續處理可接收；事件出口滿載或自身失敗需有可驗證處置。 | 模組／父層事件契約與故障注入案例；依 REQ-009 至 REQ-012 的政策；未執行。 | PASS: artifacts/validation/818416f40f8b41c09815a32cad12628b/AC-005-review.json |
| AC-006 | REQ-008 | 驗證慢速接收、暫時拒絕、部分完成、滿載、停止／斷線時資料順序、所有權、容量上限及可觀測性；不得以任意加 bank 遮蔽積壓。 | 資料流契約測試與目標平台所需執行證據；門檻由專案決定。 | PASS: artifacts/validation/818416f40f8b41c09815a32cad12628b/AC-006-review.json |

| AC-007 | REQ-009 | 異常消費者延遲或事件送出失敗時，必要保護仍完成；非法操作不繼續，原路徑不依賴 log／復原完成。 | 事件消費延遲及送出失敗注入；即時路徑依專案驗證時間與阻塞限制。 | PASS: artifacts/validation/818416f40f8b41c09815a32cad12628b/AC-007-review.json |

| AC-008 | REQ-010 | 首次異常立即提交；重複異常累計且依期限通知；每次必要保護不被聚合省略。 | 首次／重複事件及時間邊界案例，驗證次數與保護呼叫；期限依專案提供。 | PASS: artifacts/validation/818416f40f8b41c09815a32cad12628b/AC-008-review.json |

| AC-009 | REQ-011 | 滿載加入新事件後仍不超出容量、最舊待送事件被移除、保留順序與覆寫數可驗證；必要保護仍完成，消費者持有資料不被覆寫。 | 小容量佇列、連續滿載與生產／消費交接案例；並行方式依專案提供。 | PASS: artifacts/validation/818416f40f8b41c09815a32cad12628b/AC-009-review.json |

| AC-010 | REQ-012 | 覆寫故障事件後，查詢仍反映持續故障；唯有擁有者依恢復條件更新才解除；重複故障不造成無界狀態增長，復原流程責任不與模組狀態混淆。 | 故障／事件覆寫／查詢／恢復的狀態轉移與所有權測試；依專案契約建立。 | PASS: artifacts/validation/818416f40f8b41c09815a32cad12628b/AC-010-review.json |

| AC-011 | REQ-013 | 高流量達門檻觸發送出，低流量未滿但達等待期限仍觸發；背壓時不誤報已交付；Stop 的剩餘批次依專案契約處理。 | 可控時間與下游拒收的資料流契約案例；門檻、期限與 Stop 政策由專案提供。 | PASS: artifacts/validation/818416f40f8b41c09815a32cad12628b/AC-011-review.json |

| AC-012 | REQ-014 | Stop 拒絕新資料、期限內排空；下游停滯時依期限回報未完成並安全取消；不釋放仍持有的記憶體。 | 可控時鐘、部分傳送、永久拒收及引用延遲釋放的契約案例，期限由專案提供。 | PASS: artifacts/validation/818416f40f8b41c09815a32cad12628b/AC-012-review.json |

| AC-013 | REQ-015 | 至少涵蓋多命令來源的排序、公平性、回應關聯與滿載，以及 IMU 多輸出之慢消費者、共享生命週期與分支容量；比較具體候選方法，不因拓撲直接要求聚合，不默認所有分支一起阻塞。 | 設計案例與适用性正反測試；具體驗收映射待補全。 | PASS: artifacts/validation/818416f40f8b41c09815a32cad12628b/AC-013-review.json |

| AC-014 | REQ-016, REQ-017, REQ-018 | 多來源可追溯且 sequence 與實際接收順序符合契約；多輸出依相同資料頻率與分支政策驗證共享生命週期，不要求相同 baudrate。 | 多生產者交錯、慢分支、生命週期及頻率契約案例；未執行。 | PASS: artifacts/validation/818416f40f8b41c09815a32cad12628b/AC-014-review.json |

| AC-015 | REQ-018, REQ-019, REQ-020 | 相同資料頻率不被誤寫為相同實體速率；模組與受影響資料流有設計表、可見呈現紀錄、互相引用及程式對照；刻意遺漏方法或增加未宣告複製／緩衝時能指出缺口，不宣稱已完成設計或一致實作。 | 模組覆蓋、文件引用、呈現流程與實作偏差的正反案例；完整映射待補。 | PASS: artifacts/validation/818416f40f8b41c09815a32cad12628b/AC-015-review.json |

| AC-016 | REQ-021 | 模擬慢分支耗盡時依已呈現的用途契約跳過或停止，其他分支持續；缺口／未完成量及異常可觀測，容量不超限，仍被使用的共享資料不被覆寫或提前回收。 | 分支停滯、容量邊界及引用延遲釋放案例；依專案政策映射。 | PASS: artifacts/validation/818416f40f8b41c09815a32cad12628b/AC-016-review.json |

| AC-017 | REQ-022 | 設定驗證失敗時符合保留原狀契約；部分傳送失敗時完成層級、已完成範圍、剩餘處置及事件符合設計表，且不虛報撤回已產生效果。 | 設定非法值與部分完成後故障注入案例，核對狀態、進度、所有權及異常事件；依專案建立驗收映射。 | PASS: artifacts/validation/818416f40f8b41c09815a32cad12628b/AC-017-review.json |

| AC-018 | REQ-023 | 必須執行的復原通知在消費前被覆寫後，未完成狀態仍可被負責單元依契約期限發現並重新觸發；不能因通知遺失誤報完成，不能無界增加狀態或工作。 | 事件覆寫與復原消費延遲注入，核對狀態擁有者、重新觸發與期限；具體映射由專案定義。 | PASS: artifacts/validation/818416f40f8b41c09815a32cad12628b/AC-018-review.json |

| AC-019 | REQ-024 | 不可暫停來源有明確耗盡與缺口／停止處置；即時控制的聚合選擇符合期限；硬體必要 bank 有理由、容量、複製與所有權設計，並驗證使用中緩衝不被覆寫。 | 三類正反設計案例及適用性檢查；具體硬體與時序證據依專案契約提供。 | PASS: artifacts/validation/818416f40f8b41c09815a32cad12628b/AC-019-review.json |

| AC-020 | REQ-001, REQ-025 | 每項新增條款標明強度與適用條件；必要要求不被降為建議，可選方法不豁免 MUST；不採 SHOULD 有理由；程式規則與階段流程各在其文件，既有強度及例外政策未變。 | 逐條對照已採用決策、條款分類及適用性正反案例；完整驗收映射於正式確認前補全。 | PASS: artifacts/validation/818416f40f8b41c09815a32cad12628b/AC-020-review.json |

| AC-021 | REQ-026 | 設計表明列模組責任、共同契約與內部可變部分；故意讓呼叫端按私有演算法分支或讀取私有狀態時能指出違規；宣稱可替換的實作通過共同契約案例，未知或缺少證據不得宣稱符合。 | 模組設計正反案例、依賴及呼叫點審查、參數化共同契約測試；對應文件與工具映射待整理。 | PASS: artifacts/validation/818416f40f8b41c09815a32cad12628b/AC-021-review.json |

| AC-022 | REQ-027 | 十二組欄位及適用子表可呈現，已有資料以 ID 引用且不存在平行手寫來源；修改來源後可重新產生一致文件。未知／不適用／計畫／實作／驗證狀態可區別，刻意製造設計與程式差異不能僅因文件完整而通過。 | schema／引用及生成一致性檢查、適用性正反案例與設計實作偏差審查；具體映射待整理。 | PASS: artifacts/validation/818416f40f8b41c09815a32cad12628b/AC-022-review.json |

| AC-023 | REQ-028 | 同步狀態更新操作在返回前達成契約所定完成狀態並提供有效結果；未完成工作只回報接受且可關聯後續完成／失敗；測試不得把接受誤當完成或把模組完成誤當傳輸完成。必要保護、異常事件及訂閱通知仍依各自契約驗證。 | 同步完成、同步失敗／部分完成、非同步接受後失敗及資料交接案例；更新對應文件、schema、檢查器及測試的適用映射。 | PASS: artifacts/validation/818416f40f8b41c09815a32cad12628b/AC-023-review.json |

| AC-024 | REQ-029 | 八組欄位與步驟子表可呈現且引用一致，區分同步結果、非同步接受、傳輸及遠端完成，無關項目可明示不適用，不暴露私有算法。 | 格式／引用及同步非同步資料交接正反案例。 | PASS: artifacts/validation/818416f40f8b41c09815a32cad12628b/AC-024-review.json |
| AC-025 | REQ-030 | 介面文件明示權限、保存引用與生命週期，無四引數或固定 byte 數的全域硬門檻；同概念分組有語意理由，受限路徑記錄目標 ABI、編譯檢視及必要量測，缺乏證據不宣稱較快或無堆疊成本。 | 值副本、含指標結構、同步借用、非同步持有及不同 ABI 案例的設計／程式審查，成本證據依路徑映射。 | PASS: artifacts/validation/818416f40f8b41c09815a32cad12628b/AC-025-review.json |

| AC-026 | REQ-031 | 公開介面均具九組契約欄位或有理由的不適用標示，可追溯原介面及驗證；同步／非同步、空值／非空、保存／不保存引用等案例可表達。缺少存取期間或並行修改保證不能僅靠 const 宣稱安全，資料流引用與模組介面一致。 | 子表 schema／引用正反案例及介面契約審查；檢查不存在範例值被默認為全域要求。 | PASS: artifacts/validation/818416f40f8b41c09815a32cad12628b/AC-026-review.json |

## Relationships
| Source | Relation | Target | Rationale |
|---|---|---|---|
| REQ-031 | refines | REQ-027 | 具體化模組文件的公開介面子表。 |
| REQ-031 | refines | REQ-030 | 將參數存取與生命週期原則納入介面欄位。 |
| REQ-029 | refines | REQ-019 | 確認資料流具體欄位。 |
| REQ-030 | refines | REQ-027 | 補足模組參數契約及選擇原則。 |
| REQ-028 | refines | REQ-027 | 明定介面完成語意及同步／非同步選擇。 |
| REQ-031 | refines | REQ-027 | 具體化模組文件的公開介面子表。 |
| REQ-031 | refines | REQ-030 | 將參數存取與生命週期原則納入介面欄位。 |
| REQ-029 | refines | REQ-019 | 確認資料流具體欄位。 |
| REQ-030 | refines | REQ-027 | 補足模組參數契約及選擇原則。 |
| REQ-028 | refines | REQ-022 | 同步回傳仍須符合操作失敗與部分完成契約。 |
| REQ-027 | refines | REQ-026 | 確認具體模組設計欄位與唯一維護來源。 |
| REQ-026 | refines | REQ-020 | 將模組化契約與核對明列入模組設計要求。 |
| REQ-025 | refines | REQ-001 | 明定新增規則分級，維持搬移與新增規格分離及既有政策。 |
| REQ-024 | refines | REQ-015 | 補足特殊情境適用方式，維持依情境選擇聚合與背壓。 |
| REQ-023 | refines | REQ-012 | 補足可靠復原觸發，維持事件與模組狀態及復原流程責任分離。 |
| REQ-022 | refines | REQ-006 | 補足邊界驗證失敗後的狀態契約。 |
| DEC-016 | refines | DEC-004 | 保留 B+C 驗證策略，確認失敗狀態採依操作契約選擇。 |
| REQ-021 | refines | REQ-018 | 補足慢分支耗盡政策，正常資料頻率要求維持。 |
| DEC-004 | supersedes | DEC-003 | 本輪使用者以 B+C 選定檢查策略，失敗狀態仍未選定。 |
| REQ-018 | refines | REQ-017 | 使用者釐清 baudrate 為資料頻率。 |
| DEC-014 | refines | DEC-013 | 確認術語及採用提前呈現與模組設計表。 |
| REQ-015 | supersedes | REQ-008 | 取代一律聚合背壓要求，保留容量、所有權、耗盡與避免無必要複製的約束。 |
| DEC-012 | supersedes | DEC-005 | 僅修訂資料流選擇方式，全模組異常事件決策保持有效。 |
本規則集的整合與發布依賴既有規則搬移完成；討論可平行進行。

## Out of Scope
未取得「開始執行」前不修改 Skill、程式、插件設定或執行發布。不將先前舉例視為已採用條款。

## Project-specific Design Inputs
- 各專案依條款適用條件，在模組及資料流設計表明定平台、資源預算、容量、資料頻率、截止時間與停止期限。
- 各專案選定共享與回收、慢分支耗盡及恢復政策、異常分派與聚合、可靠復原的重新發現與觸發機制；不強制 RCU 或統一輪詢。
- 各專案交代不可暫停來源的耗盡處置、即時控制、必要 bank、複製、所有權、在途資料與完成語意。以上為共用規則要求的專案設計輸入，不是本規則集尚未選定的通用政策。

## Specification Preparation
- Codex 須完成逐條分級、文件歸屬、規則編號、引用及验收映射，再呈現完整 SPEC 供確認；這些整理工作不表示已取得實作授權。
- 本輪僅確認分級政策，不新增未討論主題，也不宣稱整份 SPEC 已正式確認。

## Open Decisions
None.

## Modular Design Documentation Plan
- 純程式條款由 coding-standards/rules/module-boundaries.md、type-and-state-ownership.md 等按主題保存四欄規則。
- 架構治理 references/module-design-format.md 與 data-flow-design-format.md 為候選格式檔，規定模組及跨模組設計表欄位。既有 manifest、型別／狀態 catalog 為權威資料者透過 ID 引用；缺少的設計欄位擴充原架構模型或有明確權威的設計紀錄，再產生可讀視圖，不在多份文件重複維護相同事實。
- 模組設計欄位涵蓋 ID／責任／非責任、外部契約、共同不變條件與可變實作、型別／狀態所有權、依賴／禁止依賴、同步及時間資源、錯誤／停止／回收、規則與共同契約測試引用。無多實作的模組註明不適用，不製造假替代實作。
- 資料流設計表引用模組契約，補充跨模組通知、GET／快照關聯、傳遞順序、容量、背壓及取消交接，不重述模組私有邏輯。
- 已選 architecture-design-workflow.md 與 architecture-check-workflow.md 串接何時呈現、何時核對；已選 verification/design-checks.md、static-checks.md、runtime-checks.md 定義判準，rule-verification-map.md 串接規則 ID／模組契約／驗證與證據。
- 文件填齊不代表程式符合；必須核對程式位置與實際呼叫路徑、適用時的共同契約測試及執行證據。架構決策理由需 ADR 時引用共用規範，不要求每個模組都建立 ADR。
## Adopted Module Design Fields
十二組欄位與引用／產生安排已採用；沿用 manifest 為可編輯架構事實的唯一維護來源及生成視圖原則，缺欄位以正式 schema 擴充處理，不另建同內容手寫文件。設計事實與實際程式仍須核對。
| Section | Fields and meaning |
|---|---|
| 識別與範圍 | 模組 ID、名稱、層級、父模組（適用時）、設計／實作狀態、SPEC 引用 |
| 責任與非責任 | 擁有的產品行為、明確不負責事項、交給哪個模組／角色 |
| 外部介面契約 | Port／命令／查詢／事件 ID；輸入輸出語意、單位、範圍、有效性、前置／後置條件、拒絕與完成語意 |
| 共同不變條件 | 各受支援實作都必須維持的行為、事件時機、狀態提交及時間保證 |
| 可變實作與選擇 | 內部可替換部分、實際選用方法、選擇條件、差異如何被共同契約封裝；無多實作時不適用 |
| 型別與狀態所有權 | 引用 Type／State ID，誰讀寫、何時建立／釋放、哪些私有；狀態轉移條件及動作 |
| 內部處理方法 | 必要處理步驟、演算法與 ALG 引用、重要取捨；不複製所有函式內容 |
| 依賴與交互邊界 | 合法依賴、禁止依賴、父層協調／mapping、Flow 引用，不從檔案位置推定責任 |
| 執行與同步 | Execution Profile／Unit 引用、呼叫上下文、同步／非同步、重入及鎖定契約；不預設每模組一 Task |
| 資源與時間 | 適用的容量、配置方式、堆疊／記憶體預算、等待／截止時間與引用來源；沒有數據時標待確認 |
| 異常與生命週期 | 邊界驗證、立即保護、異常事件、持續故障狀態、初始化／Stop／取消／reset／回收及部分完成契約 |
| 實作與驗證追溯 | 程式路徑／公開符號、規則 ID、契約測試與證據引用；計畫／已執行／不適用／缺證據區分 |

介面、狀態轉移、資源預算可用子表呈現。共通章節不省略，無關項目標不適用及理由；未知值不能視為不適用或填零。設計階段的計畫路徑／驗證計畫不得誤報為已實作／已驗證。跨模組 Flow 引用模組契約，模組表不複寫傳輸拓撲。欄位須擴充既有 description/ports/types/state/execution 模型，現有能表達者沿用 ID。
碰撞案例示意：模組負責事件判定與共同鎖定解除契約，模型提供判斷方法，外部發布與編碼依公開契約；相同契約不意味相同算法或將該專案 0.8／50ms 變成通用規則。
## Adopted Data Flow Design Fields
既有資料流設計義務的八組具體欄位已採用，不新增一律使用佇列／聚合的政策。以既有 manifest Flow、Port、Event、Module 與 Execution Profile ID 引用為基礎，必要時擴充 schema，生成視圖不重複維護。
| Group | Contents |
|---|---|
| 識別與目的 | Flow ID、用途、負責協調的模組、需求／SPEC 引用 |
| 起點與完成終點 | 觸發條件、輸入來源、成功定義及明確不包含的後續保證 |
| 路徑與步驟 | 生產者、消費者、介面 ID、順序、條件分支及同步／非同步交接；不攤開模組私有演算法 |
| 資料及關聯 | 本次結果／最新狀態／事件快照、單位／有效性引用、來源與必要 request／event／sequence 關聯 |
| 所有權與緩衝 | 每次副本／借用／轉移／共享、持有期限、回收者、複製位置、每層容量及在途上限；無緩衝則明示 |
| 執行與時間 | 呼叫上下文／執行單元 ID、等待位置、截止時間、資料頻率與突發量；不預設每模組一 Task |
| 傳送與協調 | 聚合是否適用及門檻、背壓方向／觸發、部分接受／完成、多來源排序及多輸出慢分支政策 |
| 異常停止與驗證 | 拒收／失敗／取消／Stop 的處理與責任、保護及異常事件引用、各步驟實作位置、規則及測試／證據引用 |

步驟子表候選欄位為步驟 ID、呼叫者／生產者、被呼叫者／消費者、契約 ID、互動方式、完成判定、資料交接、異常分支。同步 return 不須額外 GET，return 不必代表值副本；借用／引用必須明示。發布接受、transport 接受與遠端收到是不同完成層級；無 ACK 或其他證據不得宣稱遠端收到。
碰撞示例僅供理解：主協調呼叫碰撞模組 Process 同步取得本次結果；觸發時呼叫發布介面，若為接受工作則不等於已送達；傳輸與接收端完成分別依實際契約定義。模組私有 FIR 等算法細節留在模組表。欄位需避免与模組表重复，引用現有契約；無關項目說明不適用，未知項目待確認。
## Routing/Gates
Spec review: PASS
SPEC 確認與「開始執行」授權維持。工作草稿不表示實作授權。驗收情境與工具映射須於正式確認前補全。

## Discussion Context
### DISC-001: 從本對話整理決策
- **Situation:** 先前多輪討論已選定方案 C，並陸續討論新增記憶體規則。
- **Question:** 是否將搬移與新增規則分成不同 SPEC？
- **Options and tradeoffs:** 分開可獨立確認與驗收，新增規則透過搬移後的治理入口發布。
- **User answer:** 本輪明確要求「把搬移寫成一個spec，新增規格寫成另一個spec」。
- **Explicit rationale:** 使用者未另外提供理由；不得推定整份修改方案已確認。
- **Resulting impact:** REQ-001；由本對話可見決策重建摘要，沒有補造過往保存或授權紀錄。

### DISC-002: 大小與邊界檢查策略
- **Situation:** 使用者要求比較其他檢查策略，尚未選定失敗後狀態。
- **Question:** 採 A 每層檢查、B 邊界契約、C 型別靜態保證，或 B+C？
- **Options and tradeoffs:** A 易獨立使用但重複檢查；B 集中邊界驗證但需維護契約；C 靜態限制受語言工具鏈影響，B+C 可搭配並保留必要執行期檢查。
- **User answer:** B+C。
- **Explicit rationale:** 使用者未提供額外理由。
- **Resulting impact:** REQ-006、DEC-004、AC-004；採用檢查策略，不推定失敗後狀態政策。

### DISC-003: 全模組異常事件與內外部聚合背壓
- **Situation:** 前輪在討論執行期邊界檢查失敗，使用者擴大至所有模組與資料流。
- **Question:** 邊界異常如何觸發後續處理，以及大量資料傳送的共用策略？
- **Options and tradeoffs:** 使用者提出事件出口與聚合＋背壓；助理補充事件可靠性、不可暫停來源及硬體 bank 的差異仍須討論。
- **User answer:** 任何模組的邊界驗證都要有異常事件，可觸發 log 或後續處理；內外部資料都應採聚合＋背壓。
- **Explicit rationale:** 使用者觀察 Codex 偏好 bank 複製，引用「調查 live data 長時間偏移」聊天 01a0ebe1-b9d1-7642-ba1e-e63d9a9e3e7c 的 WebSocket／TCP 經驗。
- **Resulting impact:** REQ-007、REQ-008、DEC-005、AC-005、AC-006。已讀該聊天與 env_sensing 的 SPEC-0074、tcp_vd_aggregate_buffer.cpp、Web adapter；TCP 仍有 memcpy，Web 改單一聚合 payload 仍用 WebSocket。既有事件契約先回拒絕、接受後事件的模式需擴充；不把案例6KiB／20ms當全域門檻，也不把尚未實機長測的版本視為已驗收。

### DISC-004: 異常處理採方案 C
- **Situation:** 已確定各模組邊界異常事件需求，討論必要保護與後續處理的執行關係。
- **Question:** 採同步處理、非同步處理，或必要保護立即做並以事件處理後續工作？
- **Options and tradeoffs:** A 同步簡單但可能阻塞／重入；B 全非同步有延遲與滿載風險；C 立即保護，log、通知及後續復原經事件分派。
- **User answer:** 採用C。
- **Explicit rationale:** 使用者未提供額外理由。
- **Resulting impact:** REQ-009、DEC-006、AC-007；採用異常處理分工，不推定事件滿載政策。

### DISC-005: 首次立即通知，後續重複異常聚合
- **Situation:** 全模組異常事件可能因高頻重複異常造成通知及 log 積壓。
- **Question:** A 逐次事件、B 聚合通知、C 首次立即通知後續聚合？
- **Options and tradeoffs:** A 詳細但成本高；B 負擔較小但首次可能延遲；C 兼顧反應與負載，需專案明定聚合識別、期限及結束條件。所有方案每次都執行必要保護。
- **User answer:** 採用方案C。
- **Explicit rationale:** 使用者未提供額外理由。
- **Resulting impact:** REQ-010、DEC-007、AC-008；不推定滿載處理政策已採用。

### DISC-006: 異常事件滿載覆寫最舊
- **Situation:** 首次通知與聚合後的異常事件仍可能填滿出口。
- **Question:** A 拒收新事件、B 覆寫最舊事件、C 按重要性分類？
- **Options and tradeoffs:** A 保留早期原因；B 保留最新事件但可能失去最初原因及未處理通知；C 可分類保留但仍受容量限制且較複雜。
- **User answer:** 我認為採用B就可以了，不管哪個都有容量限制。
- **Explicit rationale:** 所有方案都有容量限制。
- **Resulting impact:** REQ-011、DEC-008、AC-009；採 B 而非分類優先；覆寫紀錄不代表所有後續處理均完成，獨立待處理狀態仍僅候選。

### DISC-007: 持續故障保存模組狀態
- **Situation:** 使用者指出持續故障資訊屬模組狀態；已說明事件、模組狀態與復原流程進度的分工。
- **Question:** 是否採用事件可覆寫、持續故障另存有界狀態？
- **Options and tradeoffs:** 只留事件可能因覆寫失去持續故障資訊；保存有界模組狀態可維持當前事實，但不等於保證每個事件均處理，也不強制替每個瞬時異常建狀態。
- **User answer:** 採用有模組狀態。
- **Explicit rationale:** 使用者先指出此資訊比較像模組狀態，本輪明確採用。
- **Resulting impact:** REQ-012、DEC-009、AC-010；不替專案決定狀態列舉、復原機制或輪詢期限。

### DISC-008: 聚合送出條件
- **Situation:** 聚合既要避免頻繁小批傳送，也不能讓低流量一直等待滿載。
- **Question:** 是否採容量門檻或最長等待時間任一達成就送出，Stop 依契約處理剩餘資料？
- **Options and tradeoffs:** 容量與時間雙條件兼顧批次與等待上限，參數由專案決定；送出觸發仍須遵守背壓，不等同交付完成。
- **User answer:** 採用。
- **Explicit rationale:** 使用者未提供額外理由。
- **Resulting impact:** REQ-013、DEC-010、AC-011；不推定 Stop 須排空或丟棄，也不保證壅塞時在聚合期限內完成交付。

### DISC-009: Stop 限時排空與 CSV 背壓案例核對
- **Situation:** 使用者要求確認參考專案究竟採聚合或背壓，並提供過夜測試的新觀察。
- **Question:** Stop 採何種剩餘資料政策，以及目前實作的方法？
- **Options and tradeoffs:** A 無限期排空、B 取消待送、C 專案期限內排空再依契約安全取消。聚合與背壓可並用，但只限制佇列且超限失敗不等於向來源回饋流控。
- **User answer:** 採用方案C；過夜測試未見 WiFi 異常，但出現 CSV write exceed backpresure。
- **Explicit rationale:** 使用者希望避免聚合與背壓的認知不同。
- **Resulting impact:** REQ-014、DEC-011、AC-012。2026-09-30 讀取 env_sensing 現有程式：Web adapter 在持有／不可寫時保留聚合資料；TCP 以 sent_offset 追蹤部分傳送；controller.js enqueueCsv 在 csvQueue.length >= 256 時 failLive；drainCsv 序列 await writer；live-csv-writer.js 有批次 flush。這條 CSV 路徑未在超限前向來源回饋減速／暫停。未取得部署版本與性能證據，不能推定過夜問題的根因。未修改該專案。

### DISC-010: 依情境選方法，設計時提前揭露
- **Situation:** 使用者指出實作方式往往等問題發生後才逐一確認，並補充多命令來源與 IMU 多輸出。
- **Question:** 如何提前說明資料流的實作選擇？
- **Options and tradeoffs:** 助理候選：在設計確認前呈現每條受影響資料流的拓撲、候選與理由、容量與複製路徑、所有權、聚合條件、背壓方向、分支慢速政策、錯誤與 Stop，以及驗證方式；自動查明既有事實，只詢問影響行為的未決取捨。該設計檢查流程屬階段規範，不放純程式條款；驗收須核對使用者實際看到的設計與實作一致。此具体流程尚待確認，不算已部署。
- **User answer:** 採用依情境選擇，並要求明確交代實作方法；要求改善討論時未告知、發生問題後才確認的情況。
- **Explicit rationale:** 使用者擔心實作方式未在討論時揭露，多入單出與單入多出也需要涵蓋。
- **Resulting impact:** REQ-015、DEC-012、AC-013；多命令匯入不表示允許合併或重排命令，分流不表示所有介面應一起背壓。提前呈現與核對的具體流程保存為候選。

### DISC-011: 多來源排序與共享多輸出
- **Situation:** 使用者補充前輪多入單出及單入多出的具體設計意圖。
- **Question:** 如何解讀 sequence 保護、來源結構與多輸出 baudrate／RCU？
- **Options and tradeoffs:** 若 sequence 決定入列順序，分配序號與提交入列需同一序列化操作；只保護自增仍可能反序。共享不可變資料與延後回收可減少讀者干擾，但慢讀者仍可能耗盡有界池，須另定政策。Linux RCU 官方文件指出舊讀者結束前不能回收，亦不提供逐筆交付保證。
- **User answer:** 接收是產品內部執行單元；mutex 保護 sequence，buffer 結構須帶來源資料。多輸出共享資料、各輸出 baudrate 相同、不可拖住其他介面，類似 RCU。
- **Explicit rationale:** 使用者希望指定可預先討論的多來源／多輸出實作方式。
- **Resulting impact:** REQ-016、REQ-017、DEC-013、AC-014；術語不明處保留待討論。來源為本輪兩則註解；RCU 參考 https://docs.kernel.org/RCU/whatisRCU.html。未採用前輪設計表流程，不補造確認。

### DISC-012: 資料頻率與模組／資料流實作設計表
- **Situation:** 前輪釐清 baudrate 與共享多輸出，同時設計表流程仍是候選。
- **Question:** baudrate 的意思及是否採用提前呈現／事後核對流程？
- **Options and tradeoffs:** 資料頻率與實體線速有不同語意；設計表能提前暴露取捨，但須避免複製同一規則及要求使用者回答可查事實。
- **User answer:** 資料頻率相同；註解採用「設計確認前呈現、實作後核對」；每個模組也要有實作設計表。
- **Explicit rationale:** 使用者要求將可檢視的實作設計擴及每個模組。
- **Resulting impact:** REQ-018、REQ-019、REQ-020、DEC-014、AC-015；新增設計流程義務屬本新增規格範圍，保持 SPEC-0040 搬移不改原語意的邊界；慢分支耗盡政策仍待討論。

### DISC-013: 慢分支依用途處理
- **Situation:** 同頻率多輸出不能被慢分支拖住，且緩衝容量有限。
- **Question:** 慢分支耗盡時採 A 跳過舊資料、B 停止分支，或 C 依用途選擇？
- **Options and tradeoffs:** A 可繼續顯示但有缺口；B 明確停止不完整輸出；C 在設計表依用途明定，例為即時顯示 A、完整記錄 B。
- **User answer:** C。
- **Explicit rationale:** 使用者未補充理由。
- **Resulting impact:** REQ-021、DEC-015、AC-016；補足 REQ-018，保留同頻率、分支隔離及共享生命週期約束，尚未授權實作。

### DISC-014: 操作失敗結果依契約定義
- **Situation:** 使用者對失敗狀態選項不理解，助理先以設定兩欄但一欄非法、100 筆傳送完成 60 筆時斷線說明。
- **Question:** 是否採 C，每種操作預先定義失敗結果，寫入模組／資料流實作設計表？
- **Options and tradeoffs:** A 全部拒絕保留原狀；B 允許部分完成並回報；C 依操作契約決定，一般設定先驗證再修改，串流明定進度與剩餘處置。已完成的外部效果不一定能撤回。
- **User answer:** C。
- **Explicit rationale:** 使用者未補充理由。
- **Resulting impact:** REQ-022、DEC-016、AC-017；補足 REQ-006 與 DEC-004，保持異常事件及必要保護政策，尚未授權實作。

### DISC-015: 必須執行的復原不能只依賴可覆寫事件
- **Situation:** 異常事件可被覆寫，模組故障狀態雖保留，復原仍可能因缺少觸發而不執行。
- **Question:** 對於專案要求必須完成的異常復原，是否採用「不能只依賴可覆寫事件；必須能從持續狀態重新發現未完成工作並重新觸發，具體機制與期限由專案設計表明定」？
- **Options and tradeoffs:** 僅靠通知可能漏掉必要復原；以持續狀態重新發現工作能容忍通知覆寫，但須有負責單元與執行資源預算；不強制輪詢或無限重試。
- **User answer:** 採用
- **Explicit rationale:** 使用者未補充理由。
- **Resulting impact:** REQ-023、DEC-017、AC-018，補足 REQ-012；Q-RECOVERY-001 第 15 版獲回答；尚未授權實作。

### DISC-016: 特殊資料流適用原則
- **Situation:** 聚合與背壓須依硬體及時間限制選擇，避免規則妨礙必要實作。
- **Question:** 是否採用以下特殊情境原則：不可暫停來源須明定容量耗盡與資料遺失處置；即時控制以截止時間判斷是否聚合；硬體必要的 bank 可使用，但须在設計表交代必要性、容量、複製及所有權，並保留原有安全與異常處理要求？
- **Options and tradeoffs:** 情境化原則允許符合硬體及時間要求的實作，但仍須提前揭露容量、複製與所有權；不能用增加 bank 掩蓋無界積壓或默認資料遺失。
- **User answer:** 採用
- **Explicit rationale:** 使用者未補充理由。
- **Resulting impact:** REQ-024、DEC-018、AC-019；回答 Q-SPECIAL-FLOW-001 第 17 版，補足 REQ-015；尚未授權實作。

### DISC-017: 新增規則強度
- **Situation:** 已選定程式規則及設計流程，需明確區分必要要求、最佳化建議與可選方法。
- **Question:** 是否採用新增規則分級：已採用的必要安全、容量、所有權、異常處理及設計呈現／核對要求列為 MUST，依各條款適用條件生效；額外最佳化建議列為 SHOULD，未採用時在設計表說明理由；可選實作方法列為 MAY，但仍須符合 MUST？既有規則強度與例外政策維持，流程要求仍放階段規範。
- **Options and tradeoffs:** 分級使必要要求與可選方法可區別；仍須逐條確認適用條件及保留既有強度，不能將已採用義務降級或把所有實作固定為單一方法。
- **User answer:** 採用
- **Explicit rationale:** 使用者未補充理由。
- **Resulting impact:** REQ-025、DEC-019、AC-020；回答 Q-RULE-STRENGTH-001 第 19 版。已決事項與專案設計輸入移出未決清單；編號及驗收映射由 Codex 整理。尚未確認整份 SPEC 或授權實作。

### DISC-018: 採用模組化補強及對應文件規範
- **Situation:** 引用「規劃碰撞與加速度事件」揭露既有模組化要求未落實，提出設計前確認與實作後核對。
- **Question:** 是否採用模組化設計補強：設計確認前明列每個模組的責任、非責任、共同外部契約、內部可變實作、狀態所有權與外部依賴；未釐清時不得宣稱设计完成或進入相關實作。實作後檢查呼叫端是否依赖內部演算法及私有狀態，對宣稱可替換的實作驗證同一外部契約；不強制相同內部算法、固定參數、檔案數量、GET 或事件佇列。既有義務由 SPEC-0040 搬移，新增的明確檢查與驗收要求由 SPEC-0041 引入？
- **Options and tradeoffs:** 必查模組責任與共同契約可提前揭露內部細節外洩，需格式與證據映射支援；避免僅以文件填寫代替實作核對。
- **User answer:** 採用
- **Explicit rationale:** 使用者另問「這也要訂定相對應的文件規範?」。
- **Resulting impact:** REQ-026、DEC-020、AC-021；回答 Q-MODULAR-DESIGN-001 第 21 版。保存文件分工與欄位規劃，沿用 REQ-019／020 設計表要求；尚未授權實作。

### DISC-019: 採用模組欄位與唯一維護來源
- **Situation:** 已呈現十二組欄位，使用者先詢問權威的意思；助理說明為同一資料的唯一維護來源，並非文件即證明實作。
- **Question:** 是否採用模組設計十二組欄位：識別與範圍、責任與非責任、外部介面契約、共同不變條件、可變實作與選擇、型別與狀態所有權、內部處理方法、依賴與交互邊界、執行與同步、資源與時間、異常與生命週期、實作與驗證追溯；沿用 manifest 及 ID 引用產生文件，必要時擴充 schema，無關項目標不適用與理由，未知事項明示待確認？
- **Options and tradeoffs:** 引用既有 ID 並由來源產生視圖減少重複維護，仍需 schema 擴充及程式對照；不適用與未知分開。
- **User answer:** 採用
- **Explicit rationale:** 使用者引用十二組欄位及由來源產生文件的安排，註解採用。
- **Resulting impact:** REQ-027、DEC-021、AC-022；回答 Q-MODULE-FIELDS-001 第 24 版；候選欄位轉為已採用，仍未授權實作。

### DISC-020: 同步回傳與事件契約銜接
- **Situation:** 使用者指出同步 return 也是模組介面方式；後續釐清完成程度與資料語意。既有 event-contract.md 將接受命令後結果交由事件回報，需要明確修訂。
- **Question:** 是否採用上述區分，允許「返回前已完成、包含狀態更新的操作」同步回傳結果？
- **Options and tradeoffs:** 已完成操作可直接回傳；僅接受未完成工作需後續回報；其他訂閱者的事件另依契約。同步可減少通知與 GET 的交接，但仍需符合等待期限、生命週期與失敗契約。
- **User answer:** 採用
- **Explicit rationale:** 使用者本輪未補充理由；先前指出同步 return 方式應納入。
- **Resulting impact:** REQ-028、DEC-022、AC-023；在 SPEC-0041 修訂完成回報政策，保留異常事件、必要保護與故障狀態要求，不將修改混入 SPEC-0040 純搬移。本題先前只在聊天呈現，無已保存的 question/version，不補造問答追溯；依本輪明確回答記錄。尚未授權實作。
### DISC-021: 補記資料流欄位採用
- **Situation:** 使用者先前已採用資料流八組欄位，同時追問通用技能及參數傳遞；當時僅在聊天確認，未完成保存。
- **Question:** 資料流設計表是否採用八組欄位：識別與目的、起點與完成終點、路徑與步驟、資料及關聯、所有權與緩衝、執行與時間、傳送與協調、異常停止與驗證，並使用步驟子表明列契約引用、同步／非同步方式、完成判定及資料交接；引用模組資料，不重複展開私有演算法？
- **Options and tradeoffs:** 欄位區分跨模組交接與私有實作，避免重複維護及為填表增加機制。
- **User answer:** 採用
- **Explicit rationale:** 來源為先前「採用。現在討論的是通用技能吧?我想知道模組的傳入引數你會用傳值還是傳址的方式?」，本輪補記，不補造當時已保存。
- **Resulting impact:** REQ-029、DEC-023、AC-024；解除 Q-FLOW-FIELDS-001 第 28 版的過期待答狀態，尚未授權實作。

### DISC-022: 採用引數設計原則
- **Situation:** 已討論小型資料、引數暫存器與堆疊、傳值／傳址及 ABI 差異，助理前輪提出四項共用原則。
- **Question:** 是否採用上述引數設計原則？
- **Options and tradeoffs:** 不以固定大小或數量硬限取代語意、生命週期及成本判斷；受限路徑需核對實際 ABI 與證據，避免為減少參數硬包裝或誤認指標必然較快。
- **User answer:** 採用
- **Explicit rationale:** 使用者未补充理由。
- **Resulting impact:** REQ-030、DEC-024、AC-025；納入既有介面文件及檢查。此前引數問題僅在聊天呈現，無已保存 question/version，不補造該紀錄。尚未授權實作。

### DISC-023: 採用公開介面九組子表欄位
- **Situation:** 模組十二組欄位與引數設計原則已採用，前輪提出公開介面的具體子表格式及同步 C 範例。
- **Question:** 是否採用這九組介面欄位，作為模組文件中每個公開介面的子表格式？
- **Options and tradeoffs:** 子表明示用途、呼叫条件、參數、存取契約、完成回傳、副作用、失敗、資源時間與驗證；以 ID 引用避免重複資料，範例值不成通用限制。
- **User answer:** 採用
- **Explicit rationale:** 使用者未補充理由。
- **Resulting impact:** REQ-031、DEC-025、AC-026；本題先前僅聊天呈現，無已保存 question/version，不補造歷史紀錄。尚未授權實作。
## Revision History
- Revision 30: 2026-10-01，採用每個公開介面的九組子表欄位；尚未實作。
- Revision 29: 2026-10-01，採用引數設計原則並補記既有資料流欄位採用；尚未實作。
- Revision 26: 2026-10-01，採用同步已完成操作回傳及非同步接受／完成區分；尚未實作。
- Revision 25: 2026-10-01，採用模組十二組欄位及唯一維護來源產生文件；尚未實作。
- Revision 22: 2026-09-30，採用模組化契約補強，保存對應文件規範規劃；尚未實作。
- Revision 20: 2026-09-30，採用新增規則強度分級，整理專案設計輸入及規格準備工作；尚未授權實作。
- Revision 18: 2026-09-30，採用特殊資料流適用原則；尚未授權實作。
- Revision 16: 2026-09-30，採用可靠復原從持續狀態重新發現及觸發；尚未授權實作。
- Revision 14: 2026-09-30，確認操作失敗狀態採 C 依操作契約定義；尚未授權實作。
- Revision 13: 2026-09-30，採用慢分支耗盡依用途選擇政策；無實作授權。
- Revision 12: 2026-09-30，確認相同資料頻率及模組／資料流設計表呈現核對要求；未取得實作授權。
- Revision 11: 2026-09-30，保存多來源／多輸出需求，優先釐清 baudrate；無實作授權。
- Revision 10: 2026-09-30，採用依情境選方法並納入多入單出／單入多出；提前設計呈現流程為候選，無實作授權。
- Revision 9: 2026-09-30，採用 Stop C 並保存過夜觀察與程式核對；尚未授權實作。
- Revision 8: 2026-09-30，採用聚合容量／時間雙觸發及 Stop 契約；未取得實作授權。
- Revision 7: 2026-09-30，採用有界模組故障狀態與事件分離；未取得實作授權。
- Revision 6: 2026-09-30，採用異常事件滿載方案 B；未取得實作授權。
- Revision 5: 保存首次立即通知／後續聚合決策；尚未取得實作授權。
- Revision 4: 保存方案 C，事件滿載與重複通知仍待討論；無實作授權。
- Revision 3: 記錄本輪跨模組異常事件及內外部聚合背壓需求，保留待決設計；未授權實作。
- Revision 2: 記錄本輪 B+C 選擇，失敗狀態保持待討論；未授權實作。
- Revision 1: 2026-09-29，依本對話建立工作草稿；歷史回合未逐輪保存，本文為可見對話的回顧整理。
| 33 | 2026-10-02 | Reopened before clarification: Bind the legacy unbound specification to its actual current task without changing the adopted contract. |
| 34 | 2026-10-02 | Reopened before clarification: Add the missing Evidence column required by the execution planner; preserve every acceptance criterion and threshold. |
| 36 | 2026-10-02 | Recorded implementation PASS evidence. |


## Implementation preparation — 2026-10-02

本節具體化已採用內容，不新增產品參數或使用者決策。REQ-008 的無條件聚合已由 REQ-015 取代；REQ-017 的 baudrate 已由 REQ-018 的資料頻率澄清；先前「待討論」事項按後續 REQ-009..031 及 DEC-006..025 解讀。原始決策歷史保留。

### 生效與責任

依賴 SPEC-0040 的單一規則治理入口。SPEC-0040 保留原有程式語意；本 SPEC 才新增下列條款，並更新原本將所有 accepted command 完成都要求 output event 的限制。設計/檢查流程與文件格式的義務放相應 references，不混入四欄 rules。

### 新增純程式條款草案

| 規則 ID | 強度 | 適用條件 | 程式要求 |
|---|---|---|---|
| MEM-ALLOC-001 | MUST | 有資源或時間限制的配置路徑 | 配置及釋放符合容量與期限；無法滿足時使用符合限制的預配置、固定容量或適當池，耗盡時不得回退到違反限制的配置。 |
| MEM-CAP-001 | MUST | 有限 buffer、queue、pool | 容量及耗盡行為有明確契約；不得無界擴容或覆寫仍使用的資料。 |
| MEM-OWNER-001 | MUST | 資源及共享資料生命週期 | 預設單一擁有者；轉移、借用、共享明定存活、權限、同步及回收，不將共享存活當共同寫入權。 |
| MEM-LIFE-001 | MUST | 成功、失敗、取消、逾時與非同步持有 | 所有退出路徑均有資源收尾；持有未解除前不得釋放或重用，逾時本身不代表使用已結束。 |
| BND-CHECK-001 | MUST | 外部輸入、跨信任邊界及已失效的內部保證 | 使用前驗證大小計算可表示、有效長度及容量；可證明的型別/靜態保證可取代相應動態檢查，保證失效須重驗。 |
| ERR-PROTECT-001 | MUST | 任何模組的邊界驗證失敗 | 立即停止非法操作並完成契約所需保護；透過結構化異常事件提供後續處理入口，必要保護不依賴 log 或事件被消費。 |
| ERR-REPORT-001 | MUST | 高頻重複異常 | 首次立即嘗試提交；後續同類異常以有界資料累計並按已定期限回報；每次必要保護仍執行。 |
| ERR-QUEUE-001 | MUST | 異常事件待送佇列滿載 | 覆寫最舊待送事件以保留最新事件並計數；不得覆寫消費者持有資料，回報失敗不得形成遞迴事件風暴。 |
| ERR-STATE-001 | MUST | 持續故障 | 有界故障狀態由模組 owner 維護；通知被覆寫不清除狀態，只有實際恢復符合契約才由 owner 更新。 |
| ERR-RECOVER-001 | MUST | 必須完成的後續復原 | 未完成復原能從持續狀態被負責單元重新發現及觸發，符合專案期限，不只依賴可覆寫通知；工作與重試均有界。 |
| ERR-RESULT-001 | MUST | 可能失敗或部分完成的操作 | 失敗結果符合操作契約：狀態、已完成範圍、剩餘資料、可恢復方式及事件一致，不宣稱回滾已產生的外部效果。 |
| FLOW-BOUND-001 | MUST | 跨執行單元或內外部介面資料傳遞 | 每層及在途容量有界；接收、拒絕、部分完成、持有與釋放符合契約，不能藉重複 bank 隱藏無界積壓。 |
| FLOW-BATCH-001 | MUST | 已選聚合的路徑 | 達容量門檻或最長等待時間任一條件即觸發送出嘗試，仍遵守背壓及期限；觸發不等於已交付。 |
| FLOW-STOP-001 | MUST | 已採用 bounded drain 的資料流 Stop | 停止新接收，期限內排空，逾期回報未完成並安全取消；仍被持有資料不得提前回收。 |
| FLOW-FANIN-001 | MUST | 本規範所述多命令來源交同一內部執行單元 | 輸入紀錄包含來源；以 mutex 保護 sequence／接收排序所需共享狀態；編號與入列符合所宣告順序，回覆可關聯來源；mutex 不等於公平性。 |
| FLOW-FANOUT-006 | MUST | 同資料頻率的多介面輸出 | 各分支取得契約要求的資料頻率，慢分支不阻塞其他分支；各自有容量與用途相符的跳過/停止政策、缺口及異常可觀測性。 |
| FLOW-SHARE-001 | MUST | 多消費者共享資料 | 發布、讀取、持有與回收同步明確，任何讀者仍使用時不得重用；慢讀者不使保留量無界增長。 |
| FLOW-SOURCE-001 | MUST | 來源不能暫停或硬體需 bank | 明定不可回壓位置的耗盡、缺口或停止處置；硬體 bank 的容量、複製及所有權符合限制，不能把有 bank 視為已有背壓。 |
| MOD-CONTRACT-001 | MUST | 模組呼叫端與可替換實作 | 呼叫端依共同公開契約；內部算法可變部分不要求呼叫端讀私有狀態或依算法分支才能滿足共同語意。 |
| API-COMPLETE-001 | MUST | 公開呼叫或提交操作 | 在返回前已完成者可同步提供結果；尚未完成者只宣告接受，後續完成/失敗能關聯；模組、傳輸與遠端完成不得混同。 |
| API-ACCESS-001 | MUST | 傳值、傳址、借用及保存引用 | 讀写權限、有效期間、是否保存、所有權與並行修改保證符合介面契約；const 不能代替底層資料的同步保證。 |

本表放入 memory-management、boundary-validation、error-handling、data-flow、module-boundaries、type-and-state-ownership 對應主題；ID 不得重複。一般路徑可用 heap，不設通用 zero-heap、byte 門檻、四引數限制、SIMD 指令或 UART baudrate。聚合、引用塊、copy、queue、pull、credit、水位、RCU 類方法依情境選擇，不能因方法可選而豁免上述 MUST。減少不必要複製/配置屬已採用條件式最佳化偏好；不採用 SHOULD 時記錄理由。

### 選方法時必須呈現的比較

| 情境 | 至少交代的可行方法與成本 | 必須明確的結果 |
|---|---|---|
| 多命令來源→執行單元 | 來源封裝＋有界 queue；sequence 與入列的臨界區；可否同步呼叫 | 接收順序、滿載處置、公平性、reply routing；mutex 不包住漫長執行 |
| 同步小結果 | return 值或呼叫端輸出區；實际 ABI/copy/lifetime | 返回是否完成、修改哪些狀態、錯誤是否部分完成 |
| 高吞吐串流→單輸出 | 直接填聚合區、固定塊引用、scatter/gather（若平台支援）、有界 queue＋credit/水位 | 複製位置、部分完成 offset、誰保留未送資料、信用何時歸還 |
| IMU→多輸出 | 共享不可變 block＋各分支 cursor/hold，或有理由的獨立複製 | 同資料頻率、分支不互阻、最慢持有者、容量耗盡及回收；不強制 RCU |
| 持久化記錄 | 接收至 writer 的容量傳遞及 flush/持久化完成語意 | 背壓覆蓋哪個完成層級；socket 可寫不代表 CSV 已寫完 |
| ISR／不可暫停採樣／即時控制 | 有界 nonblocking handoff、硬體雙緩衝、逐筆或小批 | 不可回壓處的處置；batch latency、交接與即時期限 |

本表是設計交代內容，不是替專案預選技術；所有數值由專案 profile、需求或量測來源給定。

### 格式、來源與生成契約

擴充現有 architecture/manifest.yaml 與 schema，由既有 architecture owner 維護。欄位命名是本次實作提案；不得另建平行手寫 module.md 或 flow.md 真相來源。下表的 refs 指現有 ID catalog，對應欄位已有等價資料時直接引用，不複製。

| 模組十二組 | 欄位內容／來源 |
|---|---|
| 1 識別與範圍 | module_id、level、parent、status、source_sets／paths refs |
| 2 責任與非責任 | responsibilities、non_responsibilities，與 boundary design 共用 |
| 3 公開契約 | interface IDs，引用下列九組介面子表及既有 ports/events/types |
| 4 共同不變條件 | invariants、rule_refs；所有可替換實作共同承諾 |
| 5 可變實作 | implementation_variants、selection_constraints、shared_contract_refs；無變體可 N/A |
| 6 型別與狀態 | type_refs、state_refs；引用既有 owner/lifetime/mutation authority catalog |
| 7 內部方法 | implementation_summary、algorithm_refs、alternatives/rationale；不展開私有算法為頂層 flow |
| 8 依賴與邊界 | depends_on、demand_ports、boundary_mapping_refs，引用既有依賴資料 |
| 9 執行與同步 | execution_unit_refs、call_contexts、serialization、reentrancy、lock scope |
| 10 資源與時間 | profile/workload refs、capacity、inflight、allocation、stack/latency budget 及來源 |
| 11 異常與生命週期 | failure_state、error_event refs、recovery owner、start/stop/cancel/drain 契約 |
| 12 實作與驗證連結 | source/symbol refs、acceptance/test/evidence refs、design/implemented/verified 狀態 |

| 公開介面九組 | 欄位內容／來源 |
|---|---|
| 1 識別與用途 | interface_id、module_id、public_symbol、purpose；port 若適用則引用 |
| 2 呼叫條件 | preconditions、allowed_context、reentrancy、ordering |
| 3 輸入參數 | name/type_ref、meaning、range/unit、value/address、可空性 |
| 4 存取契約 | read/write、owner/borrow/transfer/share、retain、valid_until、concurrent_mutation/synchronization |
| 5 完成與回傳 | synchronous/accepted-only、completion_level、result、correlation/completion event |
| 6 狀態與副作用 | affected_state_refs、commit_point、observable_effects |
| 7 失敗與部分完成 | admission rejection、execution failure、progress、remaining disposition、error_event_refs |
| 8 資源與時間 | bounded allocation/wait/stack/latency、ABI/compiler evidence refs（依適用条件） |
| 9 驗證連結 | contract_case_refs、rule_refs、implementation/evidence_refs |

| 資料流八組 | 欄位內容／來源 |
|---|---|
| 1 識別與目的 | flow_id、L0/L1 owner、purpose、workload refs |
| 2 觸發與完成 | trigger、admission、end_condition、completion_level |
| 3 路徑與步驟 | ordered steps：participants、interface_ref、interaction、completion、handoff、failure |
| 4 資料與關聯 | type/event refs、source、correlation、sequence、valid_length、frequency |
| 5 所有權與緩衝 | buffer owner、capacity、inflight、copy sites、holders、release condition |
| 6 執行與時間 | execution/channel/profile refs、rate/burst、latency、deadline、budget source |
| 7 傳送與協調 | aggregate trigger、backpressure method/reach、partial progress、fanin/fanout/fairness policies |
| 8 異常、停止與驗證 | reject/drop/gap、events/state/recovery refs、bounded drain/cancel、contract cases/evidence |

格式檢查：ID 唯一、引用存在且類型正確、owner/direction 一致、容量/時間單位及來源明確；applicable 值必填，not-applicable 需理由，unknown 需列欠缺內容，不能以空字串冒充不適用。planned、implemented、verified 分別依設計／程式／實際證據，文件完整不自動升為 verified。欄位等價遷移可自動完成，不能從缺欄位猜硬體能力或核准。

### 階段檢查與證據

| 階段 | 檢查 | 可證明與限制 |
|---|---|---|
| SPEC 確認前 | 模組／介面／資料流格式完整、方法與替代方案已向使用者呈現；適用規則與 owner/capacity/failure 語意一致 | 設計有明確契約；不能證明實作已符合 |
| 編碼期間 | 依確認契約寫程式、保護和異常出口同步完成；遇需改契約回 owner 更新 | 不留到最後才選 queue/copy/ownership |
| 實作後靜態與 review | schema/refs/generated views、可支援 AST、所有呼叫點、真實資料路徑與設計比對 | 無 analyzer 的語言標明未自動驗證；MUST 語意仍須審查 |
| 契約測試 | 正常、拒絕、容量邊界、部分完成、取消、通知覆寫、慢分支與恢復 | host fixture 驗證契約與檢查能力；不能替代 target 時間/堆疊/fragmentation 證據 |
| 適用的執行期驗證 | ABI/build、最大資源、延遲/阻塞、長時間負载及觀測成本 | 按專案 profile 與需求選證據；未量測不宣稱無碎片化或較快 |

### 驗收案例對照

| AC | fixture／review 情境及預期 |
|---|---|
| AC-001 | PC 受限路徑與 MCU 非即時路徑交叉示例；由預算/期限決定，不由平台名字禁 heap |
| AC-002 | pool 滿載不得偷偷 fallback heap；queue 飽和仍有界且按契約拒收 |
| AC-003 | shared hold、借用、轉移、取消／逾時後仍有 reader；提前回收必須識別 |
| AC-004 | 加乘溢位、來源長度/目的容量不足、靜態證明與失效重驗，各有正反案 |
| AC-005 | 非記憶體模組的非法命令也有結構化來源/原因事件；滿载接 AC-009 |
| AC-006 | 舊無條件聚合語意以 AC-013 的情境選擇為準；仍測部分傳送、滿載、順序與持有 |
| AC-007 | 故意延遲/拒絕 log 消費者，立即保護照常完成 |
| AC-008 | controllable clock：首次立即提交、重複累計、期限回報、每次保護 |
| AC-009 | 小 queue 連續满載，覆寫 oldest pending 而非 reader-held；計數/順序/容量正確 |
| AC-010 | 故障通知覆寫後狀態仍在，只有 owner 的恢復條件可清除 |
| AC-011 | 高流量達容量與低流量達期限兩種觸發；下游拒收不能算送達 |
| AC-012 | Stop 限時 drain、永久拒收、安全取消、持有未完不能釋放 |
| AC-013 | fanin 指令來源與 IMU fanout；至少比較可行方法，沒有批次需求可不聚合 |
| AC-014 | 兩 producer 交錯取 sequence/入列；按 REQ-018 採資料頻率，不能檢查相同 baudrate |
| AC-015 | 每模組及受影響 flow 的設計與呈現紀錄；偷偷新增 copy/buffer 時 review 必須指出 |
| AC-016 | display 分支跳過與 recorder 停止為兩個明定用途案例；正常分支不互阻，不作全域預設 |
| AC-017 | 設定失敗保留舊值；傳送部分完成記進度與剩餘，不虛報回滾 |
| AC-018 | 復原通知被覆寫，保留狀態仍按期限被負責單元發現，無無界重試 |
| AC-019 | 不可暫停來源、即時逐筆、硬體雙 buffer：容量/期限/在用保護正反案 |
| AC-020 | 四欄條款、強度/條件與 DEC 對照；可選方法不能豁免安全义務 |
| AC-021 | 共同 Process 契約與多實作；caller 私有算法分支/讀私有狀態的反例；不改引用韌體 |
| AC-022 | 十二組 module schema、既有 ID reuse、重生成一致；缺資料與 N/A 分別處理 |
| AC-023 | 同步改狀態 return、accepted 後失敗、部分完成、遠端未完成；不混完成層級 |
| AC-024 | 八組 flow 及 step；引用介面契約，私有算法不變人造 end-to-end flow |
| AC-025 | 小 struct 含 pointer、同步借用、非同步保存、不同 ABI；缺證據不能推成本閾值 |
| AC-026 | 九組 interface；const 底層被他執行單元修改、空值/保存規則明定；範例不升格預設 |

以上為本插件實作的 host fixture／文件與流程審查計畫，不是已執行測試。產品目標的資源/時間/並行安全仍按專案選擇 target 證據；不得把本 SPEC 驗收當成所有使用者程式已符合。

## Acceptance Mapping
```json
{
  "AC-001": {
    "evidence_claims": [
      "host-semantics"
    ],
    "rationale": "Host fixtures and recorded design/source review verify the corresponding governance contract; target resource, timing and device claims require separate project evidence."
  },
  "AC-002": {
    "evidence_claims": [
      "host-semantics"
    ],
    "rationale": "Host fixtures and recorded design/source review verify the corresponding governance contract; target resource, timing and device claims require separate project evidence."
  },
  "AC-003": {
    "evidence_claims": [
      "host-semantics"
    ],
    "rationale": "Host fixtures and recorded design/source review verify the corresponding governance contract; target resource, timing and device claims require separate project evidence."
  },
  "AC-004": {
    "evidence_claims": [
      "host-semantics"
    ],
    "rationale": "Host fixtures and recorded design/source review verify the corresponding governance contract; target resource, timing and device claims require separate project evidence."
  },
  "AC-005": {
    "evidence_claims": [
      "host-semantics"
    ],
    "rationale": "Host fixtures and recorded design/source review verify the corresponding governance contract; target resource, timing and device claims require separate project evidence."
  },
  "AC-006": {
    "evidence_claims": [
      "host-semantics"
    ],
    "rationale": "Host fixtures and recorded design/source review verify the corresponding governance contract; target resource, timing and device claims require separate project evidence."
  },
  "AC-007": {
    "evidence_claims": [
      "host-semantics"
    ],
    "rationale": "Host fixtures and recorded design/source review verify the corresponding governance contract; target resource, timing and device claims require separate project evidence."
  },
  "AC-008": {
    "evidence_claims": [
      "host-semantics"
    ],
    "rationale": "Host fixtures and recorded design/source review verify the corresponding governance contract; target resource, timing and device claims require separate project evidence."
  },
  "AC-009": {
    "evidence_claims": [
      "host-semantics"
    ],
    "rationale": "Host fixtures and recorded design/source review verify the corresponding governance contract; target resource, timing and device claims require separate project evidence."
  },
  "AC-010": {
    "evidence_claims": [
      "host-semantics"
    ],
    "rationale": "Host fixtures and recorded design/source review verify the corresponding governance contract; target resource, timing and device claims require separate project evidence."
  },
  "AC-011": {
    "evidence_claims": [
      "host-semantics"
    ],
    "rationale": "Host fixtures and recorded design/source review verify the corresponding governance contract; target resource, timing and device claims require separate project evidence."
  },
  "AC-012": {
    "evidence_claims": [
      "host-semantics"
    ],
    "rationale": "Host fixtures and recorded design/source review verify the corresponding governance contract; target resource, timing and device claims require separate project evidence."
  },
  "AC-013": {
    "evidence_claims": [
      "host-semantics"
    ],
    "rationale": "Host fixtures and recorded design/source review verify the corresponding governance contract; target resource, timing and device claims require separate project evidence."
  },
  "AC-014": {
    "evidence_claims": [
      "host-semantics"
    ],
    "rationale": "Host fixtures and recorded design/source review verify the corresponding governance contract; target resource, timing and device claims require separate project evidence."
  },
  "AC-015": {
    "evidence_claims": [
      "host-semantics"
    ],
    "rationale": "Host fixtures and recorded design/source review verify the corresponding governance contract; target resource, timing and device claims require separate project evidence."
  },
  "AC-016": {
    "evidence_claims": [
      "host-semantics"
    ],
    "rationale": "Host fixtures and recorded design/source review verify the corresponding governance contract; target resource, timing and device claims require separate project evidence."
  },
  "AC-017": {
    "evidence_claims": [
      "host-semantics"
    ],
    "rationale": "Host fixtures and recorded design/source review verify the corresponding governance contract; target resource, timing and device claims require separate project evidence."
  },
  "AC-018": {
    "evidence_claims": [
      "host-semantics"
    ],
    "rationale": "Host fixtures and recorded design/source review verify the corresponding governance contract; target resource, timing and device claims require separate project evidence."
  },
  "AC-019": {
    "evidence_claims": [
      "host-semantics"
    ],
    "rationale": "Host fixtures and recorded design/source review verify the corresponding governance contract; target resource, timing and device claims require separate project evidence."
  },
  "AC-020": {
    "evidence_claims": [
      "host-semantics"
    ],
    "rationale": "Host fixtures and recorded design/source review verify the corresponding governance contract; target resource, timing and device claims require separate project evidence."
  },
  "AC-021": {
    "evidence_claims": [
      "host-semantics"
    ],
    "rationale": "Host fixtures and recorded design/source review verify the corresponding governance contract; target resource, timing and device claims require separate project evidence."
  },
  "AC-022": {
    "evidence_claims": [
      "host-semantics"
    ],
    "rationale": "Host fixtures and recorded design/source review verify the corresponding governance contract; target resource, timing and device claims require separate project evidence."
  },
  "AC-023": {
    "evidence_claims": [
      "host-semantics"
    ],
    "rationale": "Host fixtures and recorded design/source review verify the corresponding governance contract; target resource, timing and device claims require separate project evidence."
  },
  "AC-024": {
    "evidence_claims": [
      "host-semantics"
    ],
    "rationale": "Host fixtures and recorded design/source review verify the corresponding governance contract; target resource, timing and device claims require separate project evidence."
  },
  "AC-025": {
    "evidence_claims": [
      "host-semantics"
    ],
    "rationale": "Host fixtures and recorded design/source review verify the corresponding governance contract; target resource, timing and device claims require separate project evidence."
  },
  "AC-026": {
    "evidence_claims": [
      "host-semantics"
    ],
    "rationale": "Host fixtures and recorded design/source review verify the corresponding governance contract; target resource, timing and device claims require separate project evidence."
  }
}
```

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



### Source and Revision Audit

```jsonl
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"279724065e094b639e5e54d63fa712b8","event_hash":"eff927ce0f93cbad52a2d96278f89f7a67ebd1578780efbd467bd1b6e416d8f6","event_type":"start","event_version":1,"open_decisions":["大小與邊界規則尚未採用。候選 A：每個函式執行期檢查；B：邊界驗證後以契約傳遞，保證失效時重驗；C：優先型別／靜態保證，無法證明处補執行期檢查。B 可搭配 C 的技術。","具體規則強度、編號、驗收映射與其他新增主題仍待讨论。禁止把未知風險默認安全。"],"previous_event_hash":null,"previous_snapshot_hash":null,"recorded_at":"2026-09-29T10:13:57.729696+00:00","relationships":[],"revision":1,"snapshot_hash":"b5b8132d2a11357b95c74ae7093fcfef3a75ee870bf091a7f98dc77900de1233","verdict":"BLOCKED","working_id":"WORKING-SPEC-b8886a6cd704-memory-coding-rules"}
{"affected_ids":["AC-004","DEC-004","DISC-002","REQ-006"],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":[],"added_ids":["AC-004","DEC-004","DISC-002","REQ-006"],"changed_ids":[],"removed_ids":[]},"epoch":"279724065e094b639e5e54d63fa712b8","event_hash":"041759ebb1a999f5c71eee5eaa8d29664deaa3f7da2ba30c971c765fa55b0a1c","event_type":"reconcile","event_version":1,"open_decisions":["檢查失敗的狀態政策待選：A 原子拒絕且狀態不變；B 明確允許部分完成並回報進度；C 依操作契約選擇，預設修改前拒絕，串流等操作明定部分完成或錯誤狀態。","具體規則強度、編號、驗收映射與其他新增主題仍待讨论。禁止把未知風險默認安全。"],"previous_event_hash":"eff927ce0f93cbad52a2d96278f89f7a67ebd1578780efbd467bd1b6e416d8f6","previous_snapshot_hash":"b5b8132d2a11357b95c74ae7093fcfef3a75ee870bf091a7f98dc77900de1233","recorded_at":"2026-09-29T10:22:40.966902+00:00","relationships":[{"relation":"supersedes","source":"DEC-004","target":"DEC-003"}],"revision":2,"snapshot_hash":"336fb8dc95897d0b2bb45d326e03d0f6dfa61697cd0286ac0312c21b00e93426","verdict":"BLOCKED","working_id":"WORKING-SPEC-b8886a6cd704-memory-coding-rules"}
{"affected_ids":["AC-005","AC-006","DEC-005","DISC-003","REQ-007","REQ-008"],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":[],"added_ids":["AC-005","AC-006","DEC-005","DISC-003","REQ-007","REQ-008"],"changed_ids":[],"removed_ids":[]},"epoch":"279724065e094b639e5e54d63fa712b8","event_hash":"a808c5b7d83699ec55d3713fcc4bd98db82831926e2058caee86c2a8d74974d5","event_type":"reconcile","event_version":1,"open_decisions":["檢查失敗的狀態政策待選：A 原子拒絕且狀態不變；B 明確允許部分完成並回報進度；C 依操作契約選擇，預設修改前拒絕，串流等操作明定部分完成或錯誤狀態。","異常事件應如何分派與避免鎖內重入；高頻異常是否可聚合通知；事件出口滿載的保留、丟棄與緊急處理契約待討論。","聚合／背壓對不可暫停來源、即時控制及硬體必需 bank 的適用方式待確認；聚合容量、最長等待、每層在途資料與完成語意由專案提供。","具體規則強度、編號、驗收映射與其他新增主題仍待讨论。禁止把未知風險默認安全。"],"previous_event_hash":"041759ebb1a999f5c71eee5eaa8d29664deaa3f7da2ba30c971c765fa55b0a1c","previous_snapshot_hash":"336fb8dc95897d0b2bb45d326e03d0f6dfa61697cd0286ac0312c21b00e93426","recorded_at":"2026-09-29T11:46:59.956033+00:00","relationships":[{"relation":"supersedes","source":"DEC-004","target":"DEC-003"}],"revision":3,"snapshot_hash":"2c304c4cd91ebb7d04abfd22645da06ee8fcaa72d588299ad95ffcb28953c48d","verdict":"BLOCKED","working_id":"WORKING-SPEC-b8886a6cd704-memory-coding-rules"}
{"affected_ids":["AC-007","DEC-006","DISC-004","REQ-009"],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":[],"added_ids":["AC-007","DEC-006","DISC-004","REQ-009"],"changed_ids":[],"removed_ids":[]},"epoch":"279724065e094b639e5e54d63fa712b8","event_hash":"30525a5da7393f7eb263ff9e2a8a1bdd743ec5d62fbf1a6417316755f708a50a","event_type":"reconcile","event_version":1,"open_decisions":["檢查失敗的狀態政策待選：A 原子拒絕且狀態不變；B 明確允許部分完成並回報進度；C 依操作契約選擇，預設修改前拒絕，串流等操作明定部分完成或錯誤狀態。","方案 C 已採用。高頻異常是否可聚合通知；事件出口滿載的保留、丟棄與緊急處理契約待討論；具體分派與避免重入措施依專案契約驗證。","聚合／背壓對不可暫停來源、即時控制及硬體必需 bank 的適用方式待確認；聚合容量、最長等待、每層在途資料與完成語意由專案提供。","具體規則強度、編號、驗收映射與其他新增主題仍待讨论。禁止把未知風險默認安全。"],"previous_event_hash":"a808c5b7d83699ec55d3713fcc4bd98db82831926e2058caee86c2a8d74974d5","previous_snapshot_hash":"2c304c4cd91ebb7d04abfd22645da06ee8fcaa72d588299ad95ffcb28953c48d","recorded_at":"2026-09-29T11:59:48.402469+00:00","relationships":[{"relation":"supersedes","source":"DEC-004","target":"DEC-003"}],"revision":4,"snapshot_hash":"3a3ef3bcbe0bb304a552d40ea164d036cb235de47d0254ead20363a828d5493b","verdict":"BLOCKED","working_id":"WORKING-SPEC-b8886a6cd704-memory-coding-rules"}
{"affected_ids":["AC-008","DEC-007","DISC-005","REQ-010"],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":[],"added_ids":["AC-008","DEC-007","DISC-005","REQ-010"],"changed_ids":[],"removed_ids":[]},"epoch":"279724065e094b639e5e54d63fa712b8","event_hash":"3cf0a964aea54a5cb6384645fcc50df79866507afa493617810f9e4fa502f1fc","event_type":"reconcile","event_version":1,"open_decisions":["檢查失敗的狀態政策待選：A 原子拒絕且狀態不變；B 明確允許部分完成並回報進度；C 依操作契約選擇，預設修改前拒絕，串流等操作明定部分完成或錯誤狀態。","立即保護與高頻首次通知／後續聚合均已採用。事件出口滿載的保留、丟棄與緊急處理契約待討論；具體分派與避免重入、聚合識別、期限及結束條件依專案明定。","聚合／背壓對不可暫停來源、即時控制及硬體必需 bank 的適用方式待確認；聚合容量、最長等待、每層在途資料與完成語意由專案提供。","具體規則強度、編號、驗收映射與其他新增主題仍待讨论。禁止把未知風險默認安全。"],"previous_event_hash":"30525a5da7393f7eb263ff9e2a8a1bdd743ec5d62fbf1a6417316755f708a50a","previous_snapshot_hash":"3a3ef3bcbe0bb304a552d40ea164d036cb235de47d0254ead20363a828d5493b","recorded_at":"2026-09-29T12:06:56.643008+00:00","relationships":[{"relation":"supersedes","source":"DEC-004","target":"DEC-003"}],"revision":5,"snapshot_hash":"7aaf7267b3dd8b3d90a1b2209c1d5d05e8e7caeb2e448438aa80f16a28f392f1","verdict":"BLOCKED","working_id":"WORKING-SPEC-b8886a6cd704-memory-coding-rules"}
{"affected_ids":["AC-009","DEC-008","DISC-006","REQ-011"],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":[],"added_ids":["AC-009","DEC-008","DISC-006","REQ-011"],"changed_ids":[],"removed_ids":[]},"epoch":"279724065e094b639e5e54d63fa712b8","event_hash":"7b0898f0f44be0084612bcf2cec636f4f933023916a9a2c45288e5859984063e","event_type":"reconcile","event_version":1,"open_decisions":["檢查失敗的狀態政策待選：A 原子拒絕且狀態不變；B 明確允許部分完成並回報進度；C 依操作契約選擇，預設修改前拒絕，串流等操作明定部分完成或錯誤狀態。","立即保護、高頻首次通知／後續聚合及滿載覆寫最舊待送事件均已採用。待討論：如需保證後續復原最終執行，是否由模組另保存有界待處理狀態供處理者重新檢查；這是候選補充，尚未採用。具體分派、聚合識別、期限及結束條件依專案明定。","聚合／背壓對不可暫停來源、即時控制及硬體必需 bank 的適用方式待確認；聚合容量、最長等待、每層在途資料與完成語意由專案提供。","具體規則強度、編號、驗收映射與其他新增主題仍待讨论。禁止把未知風險默認安全。"],"previous_event_hash":"3cf0a964aea54a5cb6384645fcc50df79866507afa493617810f9e4fa502f1fc","previous_snapshot_hash":"7aaf7267b3dd8b3d90a1b2209c1d5d05e8e7caeb2e448438aa80f16a28f392f1","recorded_at":"2026-09-30T00:38:28.795153+00:00","relationships":[{"relation":"supersedes","source":"DEC-004","target":"DEC-003"}],"revision":6,"snapshot_hash":"f629da117d743b150da73bfba2bbaec244d01c3c097ba75628a87d14e9896fc9","verdict":"BLOCKED","working_id":"WORKING-SPEC-b8886a6cd704-memory-coding-rules"}
{"affected_ids":["AC-010","DEC-009","DISC-007","REQ-012"],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":[],"added_ids":["AC-010","DEC-009","DISC-007","REQ-012"],"changed_ids":[],"removed_ids":[]},"epoch":"279724065e094b639e5e54d63fa712b8","event_hash":"c971a26dea51afd0eba6c63154eb7010bb6d496034946723137372c626647715","event_type":"reconcile","event_version":1,"open_decisions":["檢查失敗的狀態政策待選：A 原子拒絕且狀態不變；B 明確允許部分完成並回報進度；C 依操作契約選擇，預設修改前拒絕，串流等操作明定部分完成或錯誤狀態。","立即保護、高頻首次通知／後續聚合、滿載覆寫最舊事件及持續故障有界模組狀態均已採用。具體分派、聚合識別、期限、結束與恢復條件由專案明定；需要可靠復原的流程須另定觸發機制，尚未採用統一輪詢政策。","聚合／背壓對不可暫停來源、即時控制及硬體必需 bank 的適用方式待確認；聚合容量、最長等待、每層在途資料與完成語意由專案提供。","具體規則強度、編號、驗收映射與其他新增主題仍待讨论。禁止把未知風險默認安全。"],"previous_event_hash":"7b0898f0f44be0084612bcf2cec636f4f933023916a9a2c45288e5859984063e","previous_snapshot_hash":"f629da117d743b150da73bfba2bbaec244d01c3c097ba75628a87d14e9896fc9","recorded_at":"2026-09-30T00:46:15.005813+00:00","relationships":[{"relation":"supersedes","source":"DEC-004","target":"DEC-003"}],"revision":7,"snapshot_hash":"32b4b70aa0f1445913cbd9056ca09bcb59387f38019b78eb3c21e94ab599f6ba","verdict":"BLOCKED","working_id":"WORKING-SPEC-b8886a6cd704-memory-coding-rules"}
{"affected_ids":["AC-011","DEC-010","DISC-008","REQ-013"],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":[],"added_ids":["AC-011","DEC-010","DISC-008","REQ-013"],"changed_ids":[],"removed_ids":[]},"epoch":"279724065e094b639e5e54d63fa712b8","event_hash":"d75e93269718edaed5ecabbd2a15eece8ac2b75f90051819201e4ba996a5cd54","event_type":"reconcile","event_version":1,"open_decisions":["檢查失敗的狀態政策待選：A 原子拒絕且狀態不變；B 明確允許部分完成並回報進度；C 依操作契約選擇，預設修改前拒絕，串流等操作明定部分完成或錯誤狀態。","立即保護、高頻首次通知／後續聚合、滿載覆寫最舊事件及持續故障有界模組狀態均已採用。具體分派、聚合識別、期限、結束與恢復條件由專案明定；需要可靠復原的流程須另定觸發機制，尚未採用統一輪詢政策。","容量門檻或最長聚合等待時間觸發送出已採用，Stop 依專案契約處理。聚合／背壓對不可暫停來源、即時控制及硬體必需 bank 的適用方式待確認；每層在途資料與完成語意由專案提供。Stop 政策的共用預設仍待討論。","具體規則強度、編號、驗收映射與其他新增主題仍待讨论。禁止把未知風險默認安全。"],"previous_event_hash":"c971a26dea51afd0eba6c63154eb7010bb6d496034946723137372c626647715","previous_snapshot_hash":"32b4b70aa0f1445913cbd9056ca09bcb59387f38019b78eb3c21e94ab599f6ba","recorded_at":"2026-09-30T00:48:40.378844+00:00","relationships":[{"relation":"supersedes","source":"DEC-004","target":"DEC-003"}],"revision":8,"snapshot_hash":"88d1b19adbc557cfea989724c598a58161c56279acb8d4d6ad9f0c7227d19280","verdict":"BLOCKED","working_id":"WORKING-SPEC-b8886a6cd704-memory-coding-rules"}
{"affected_ids":["AC-012","DEC-011","DISC-009","REQ-014"],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":[],"added_ids":["AC-012","DEC-011","DISC-009","REQ-014"],"changed_ids":[],"removed_ids":[]},"epoch":"279724065e094b639e5e54d63fa712b8","event_hash":"fee6e1aa1f759bb4504872bef90920c82f40a82c603a2f741482004cbe1e658e","event_type":"reconcile","event_version":1,"open_decisions":["檢查失敗的狀態政策待選：A 原子拒絕且狀態不變；B 明確允許部分完成並回報進度；C 依操作契約選擇，預設修改前拒絕，串流等操作明定部分完成或錯誤狀態。","立即保護、高頻首次通知／後續聚合、滿載覆寫最舊事件及持續故障有界模組狀態均已採用。具體分派、聚合識別、期限、結束與恢復條件由專案明定；需要可靠復原的流程須另定觸發機制，尚未採用統一輪詢政策。","容量／時間雙觸發與 Stop 限時排空已採用。聚合／背壓對不可暫停來源、即時控制及硬體必需 bank 的適用方式待確認；每層在途資料與完成語意由專案提供。CSV 案例顯示須區分局部流控與最終消費端回饋；可靠錄製遇不可暫停來源的政策仍待討論。","具體規則強度、編號、驗收映射與其他新增主題仍待讨论。禁止把未知風險默認安全。"],"previous_event_hash":"d75e93269718edaed5ecabbd2a15eece8ac2b75f90051819201e4ba996a5cd54","previous_snapshot_hash":"88d1b19adbc557cfea989724c598a58161c56279acb8d4d6ad9f0c7227d19280","recorded_at":"2026-09-30T00:58:07.907414+00:00","relationships":[{"relation":"supersedes","source":"DEC-004","target":"DEC-003"}],"revision":9,"snapshot_hash":"882e8e9a25df4811d362b0ac26d0548cdae7098e4dee1d99364c1130ea9f98af","verdict":"BLOCKED","working_id":"WORKING-SPEC-b8886a6cd704-memory-coding-rules"}
{"affected_ids":["AC-013","DEC-012","DISC-010","REQ-015"],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":[],"added_ids":["AC-013","DEC-012","DISC-010","REQ-015"],"changed_ids":[],"removed_ids":[]},"epoch":"279724065e094b639e5e54d63fa712b8","event_hash":"ede3df9fc5f9b26e81d9b86e1ae0243c825d9dde0ed73fc7892e67766fa85566","event_type":"reconcile","event_version":1,"open_decisions":["檢查失敗的狀態政策待選：A 原子拒絕且狀態不變；B 明確允許部分完成並回報進度；C 依操作契約選擇，預設修改前拒絕，串流等操作明定部分完成或錯誤狀態。","立即保護、高頻首次通知／後續聚合、滿載覆寫最舊事件及持續故障有界模組狀態均已採用。具體分派、聚合識別、期限、結束與恢復條件由專案明定；需要可靠復原的流程須另定觸發機制，尚未採用統一輪詢政策。","容量／時間雙觸發與 Stop 限時排空已採用。聚合／背壓對不可暫停來源、即時控制及硬體必需 bank 的適用方式待確認；每層在途資料與完成語意由專案提供。CSV 案例顯示須區分局部流控與最終消費端回饋；可靠錄製遇不可暫停來源的政策仍待討論。","具體規則強度、編號、驗收映射與其他新增主題仍待讨论。禁止把未知風險默認安全。"],"previous_event_hash":"fee6e1aa1f759bb4504872bef90920c82f40a82c603a2f741482004cbe1e658e","previous_snapshot_hash":"882e8e9a25df4811d362b0ac26d0548cdae7098e4dee1d99364c1130ea9f98af","recorded_at":"2026-09-30T02:57:23.395705+00:00","relationships":[{"relation":"supersedes","source":"DEC-004","target":"DEC-003"},{"relation":"supersedes","source":"REQ-015","target":"REQ-008"},{"relation":"supersedes","source":"DEC-012","target":"DEC-005"}],"revision":10,"snapshot_hash":"246f9eae23df4460b6806e0c78a8137bb9349e08ace1329a18b0ccf8d66aa3b8","verdict":"BLOCKED","working_id":"WORKING-SPEC-b8886a6cd704-memory-coding-rules"}
{"affected_ids":["AC-014","DEC-013","DISC-011","REQ-016","REQ-017"],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":[],"added_ids":["AC-014","DEC-013","DISC-011","REQ-016","REQ-017"],"changed_ids":[],"removed_ids":[]},"epoch":"279724065e094b639e5e54d63fa712b8","event_hash":"685be7ddcb76868c7a20a59f61a0b3cc59efbe49dd9ac7dae96906667e4f8237","event_type":"reconcile","event_version":1,"open_decisions":["優先釐清：多輸出 baudrate 相同是同一資料序列／採樣或發布頻率，還是介面實體傳輸速率？多輸出須逐筆保留還是允許跳過舊資料亦待確認。RCU／有界共享區塊／獨立游標的選型尚未完成。","檢查失敗的狀態政策待選：A 原子拒絕且狀態不變；B 明確允許部分完成並回報進度；C 依操作契約選擇，預設修改前拒絕，串流等操作明定部分完成或錯誤狀態。","立即保護、高頻首次通知／後續聚合、滿載覆寫最舊事件及持續故障有界模組狀態均已採用。具體分派、聚合識別、期限、結束與恢復條件由專案明定；需要可靠復原的流程須另定觸發機制，尚未採用統一輪詢政策。","容量／時間雙觸發與 Stop 限時排空已採用。聚合／背壓對不可暫停來源、即時控制及硬體必需 bank 的適用方式待確認；每層在途資料與完成語意由專案提供。CSV 案例顯示須區分局部流控與最終消費端回饋；可靠錄製遇不可暫停來源的政策仍待討論。","具體規則強度、編號、驗收映射與其他新增主題仍待讨论。禁止把未知風險默認安全。"],"previous_event_hash":"ede3df9fc5f9b26e81d9b86e1ae0243c825d9dde0ed73fc7892e67766fa85566","previous_snapshot_hash":"246f9eae23df4460b6806e0c78a8137bb9349e08ace1329a18b0ccf8d66aa3b8","recorded_at":"2026-09-30T03:55:31.632025+00:00","relationships":[{"relation":"supersedes","source":"DEC-004","target":"DEC-003"},{"relation":"supersedes","source":"REQ-015","target":"REQ-008"},{"relation":"supersedes","source":"DEC-012","target":"DEC-005"}],"revision":11,"snapshot_hash":"6685f749e8bee02be3c951b3dbb34b8d6141e3cc2bfcc4e43603716d9f7e9b5c","verdict":"BLOCKED","working_id":"WORKING-SPEC-b8886a6cd704-memory-coding-rules"}
{"affected_ids":["AC-015","DEC-014","DISC-012","REQ-018","REQ-019","REQ-020"],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":[],"added_ids":["AC-015","DEC-014","DISC-012","REQ-018","REQ-019","REQ-020"],"changed_ids":[],"removed_ids":[]},"epoch":"279724065e094b639e5e54d63fa712b8","event_hash":"2fa4f0e05b2fe36226c5630e408ee30bf9dabed323a0e2118c4045aa1fc7a54d","event_type":"reconcile","event_version":1,"open_decisions":["多輸出相同資料頻率已確認。慢分支持有共享資料至容量上限時，是允許跳過舊資料還是停止該分支且回報異常待確認；不預設降採樣，其他分支不得被拖住。RCU／有界共享區塊／獨立游標選型尚未完成。","檢查失敗的狀態政策待選：A 原子拒絕且狀態不變；B 明確允許部分完成並回報進度；C 依操作契約選擇，預設修改前拒絕，串流等操作明定部分完成或錯誤狀態。","立即保護、高頻首次通知／後續聚合、滿載覆寫最舊事件及持續故障有界模組狀態均已採用。具體分派、聚合識別、期限、結束與恢復條件由專案明定；需要可靠復原的流程須另定觸發機制，尚未採用統一輪詢政策。","容量／時間雙觸發與 Stop 限時排空已採用。聚合／背壓對不可暫停來源、即時控制及硬體必需 bank 的適用方式待確認；每層在途資料與完成語意由專案提供。CSV 案例顯示須區分局部流控與最終消費端回饋；可靠錄製遇不可暫停來源的政策仍待討論。","具體規則強度、編號、驗收映射與其他新增主題仍待讨论。禁止把未知風險默認安全。"],"previous_event_hash":"685be7ddcb76868c7a20a59f61a0b3cc59efbe49dd9ac7dae96906667e4f8237","previous_snapshot_hash":"6685f749e8bee02be3c951b3dbb34b8d6141e3cc2bfcc4e43603716d9f7e9b5c","recorded_at":"2026-09-30T04:19:21.629611+00:00","relationships":[{"relation":"supersedes","source":"DEC-004","target":"DEC-003"},{"relation":"refines","source":"REQ-018","target":"REQ-017"},{"relation":"refines","source":"DEC-014","target":"DEC-013"},{"relation":"supersedes","source":"REQ-015","target":"REQ-008"},{"relation":"supersedes","source":"DEC-012","target":"DEC-005"}],"revision":12,"snapshot_hash":"19787d6fe6589d524066b80d1017b64972ffc4fb0a0f2c7d1c46fdbe6910024c","verdict":"BLOCKED","working_id":"WORKING-SPEC-b8886a6cd704-memory-coding-rules"}
{"affected_ids":["AC-016","DEC-015","DISC-013","REQ-021"],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":[],"added_ids":["AC-016","DEC-015","DISC-013","REQ-021"],"changed_ids":[],"removed_ids":[]},"epoch":"279724065e094b639e5e54d63fa712b8","event_hash":"55e57a54a2ca847b25b54cf32188a5fa2f6ac0c848d46042539424d3550e29d7","event_type":"reconcile","event_version":1,"open_decisions":["多輸出相同資料頻率及依用途選慢分支耗盡政策已確認；各專案設計表須說明觸發條件、恢復與共享實作。RCU／有界共享區塊／獨立游標選型依專案條件決定，不作為統一已採用實作。","檢查失敗的狀態政策待選：A 原子拒絕且狀態不變；B 明確允許部分完成並回報進度；C 依操作契約選擇，預設修改前拒絕，串流等操作明定部分完成或錯誤狀態。","立即保護、高頻首次通知／後續聚合、滿載覆寫最舊事件及持續故障有界模組狀態均已採用。具體分派、聚合識別、期限、結束與恢復條件由專案明定；需要可靠復原的流程須另定觸發機制，尚未採用統一輪詢政策。","容量／時間雙觸發與 Stop 限時排空已採用。聚合／背壓對不可暫停來源、即時控制及硬體必需 bank 的適用方式待確認；每層在途資料與完成語意由專案提供。CSV 案例顯示須區分局部流控與最終消費端回饋；可靠錄製遇不可暫停來源的政策仍待討論。","具體規則強度、編號、驗收映射與其他新增主題仍待讨论。禁止把未知風險默認安全。"],"previous_event_hash":"2fa4f0e05b2fe36226c5630e408ee30bf9dabed323a0e2118c4045aa1fc7a54d","previous_snapshot_hash":"19787d6fe6589d524066b80d1017b64972ffc4fb0a0f2c7d1c46fdbe6910024c","recorded_at":"2026-09-30T05:54:04.827803+00:00","relationships":[{"relation":"refines","source":"REQ-021","target":"REQ-018"},{"relation":"supersedes","source":"DEC-004","target":"DEC-003"},{"relation":"refines","source":"REQ-018","target":"REQ-017"},{"relation":"refines","source":"DEC-014","target":"DEC-013"},{"relation":"supersedes","source":"REQ-015","target":"REQ-008"},{"relation":"supersedes","source":"DEC-012","target":"DEC-005"}],"revision":13,"snapshot_hash":"bce47c7bcfc999afe03340f0310503e9e3cb0ef5b226aa6b61a8f8255083847c","verdict":"BLOCKED","working_id":"WORKING-SPEC-b8886a6cd704-memory-coding-rules"}
{"affected_ids":["AC-017","DEC-016","DISC-014","REQ-022"],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":[],"added_ids":["AC-017","DEC-016","DISC-014","REQ-022"],"changed_ids":[],"removed_ids":[]},"epoch":"279724065e094b639e5e54d63fa712b8","event_hash":"105004f8773450b3fc726eb1c36b27445681c178ac4580a1a955013e25f6e289","event_type":"reconcile","event_version":1,"open_decisions":["多輸出相同資料頻率及依用途選慢分支耗盡政策已確認；各專案設計表須說明觸發條件、恢復與共享實作。RCU／有界共享區塊／獨立游標選型依專案條件決定，不作為統一已採用實作。","立即保護、高頻首次通知／後續聚合、滿載覆寫最舊事件及持續故障有界模組狀態均已採用。具體分派、聚合識別、期限、結束與恢復條件由專案明定；需要可靠復原的流程須另定觸發機制，尚未採用統一輪詢政策。","容量／時間雙觸發與 Stop 限時排空已採用。聚合／背壓對不可暫停來源、即時控制及硬體必需 bank 的適用方式待確認；每層在途資料與完成語意由專案提供。CSV 案例顯示須區分局部流控與最終消費端回饋；可靠錄製遇不可暫停來源的政策仍待討論。","具體規則強度、編號、驗收映射與其他新增主題仍待讨论。禁止把未知風險默認安全。"],"previous_event_hash":"55e57a54a2ca847b25b54cf32188a5fa2f6ac0c848d46042539424d3550e29d7","previous_snapshot_hash":"bce47c7bcfc999afe03340f0310503e9e3cb0ef5b226aa6b61a8f8255083847c","recorded_at":"2026-09-30T06:03:18.057687+00:00","relationships":[{"relation":"refines","source":"REQ-022","target":"REQ-006"},{"relation":"refines","source":"DEC-016","target":"DEC-004"},{"relation":"refines","source":"REQ-021","target":"REQ-018"},{"relation":"supersedes","source":"DEC-004","target":"DEC-003"},{"relation":"refines","source":"REQ-018","target":"REQ-017"},{"relation":"refines","source":"DEC-014","target":"DEC-013"},{"relation":"supersedes","source":"REQ-015","target":"REQ-008"},{"relation":"supersedes","source":"DEC-012","target":"DEC-005"}],"revision":14,"snapshot_hash":"827af8eb31facd495c06aa18e5c54d58cafe3e6a97c5c80d4d9588dea5bae405","verdict":"BLOCKED","working_id":"WORKING-SPEC-b8886a6cd704-memory-coding-rules"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":[],"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"279724065e094b639e5e54d63fa712b8","event_hash":"f68a7621071bd4bcad84bfb078a15565ba29df44cfcb46e6bc1586a77a7d4f8f","event_type":"reconcile","event_version":1,"open_decisions":["多輸出相同資料頻率及依用途選慢分支耗盡政策已確認；各專案設計表須說明觸發條件、恢復與共享實作。RCU／有界共享區塊／獨立游標選型依專案條件決定，不作為統一已採用實作。","立即保護、高頻首次通知／後續聚合、滿載覆寫最舊事件及持續故障有界模組狀態均已採用。具體分派、聚合識別、期限、結束與恢復條件由專案明定；需要可靠復原的流程須另定觸發機制，尚未採用統一輪詢政策。","容量／時間雙觸發與 Stop 限時排空已採用。聚合／背壓對不可暫停來源、即時控制及硬體必需 bank 的適用方式待確認；每層在途資料與完成語意由專案提供。CSV 案例顯示須區分局部流控與最終消費端回饋；可靠錄製遇不可暫停來源的政策仍待討論。","具體規則強度、編號、驗收映射與其他新增主題仍待讨论。禁止把未知風險默認安全。","Q-RECOVERY-001@15"],"previous_event_hash":"105004f8773450b3fc726eb1c36b27445681c178ac4580a1a955013e25f6e289","previous_snapshot_hash":"827af8eb31facd495c06aa18e5c54d58cafe3e6a97c5c80d4d9588dea5bae405","recorded_at":"2026-09-30T06:04:45.393200+00:00","relationships":[{"relation":"refines","source":"REQ-022","target":"REQ-006"},{"relation":"refines","source":"DEC-016","target":"DEC-004"},{"relation":"refines","source":"REQ-021","target":"REQ-018"},{"relation":"supersedes","source":"DEC-004","target":"DEC-003"},{"relation":"refines","source":"REQ-018","target":"REQ-017"},{"relation":"refines","source":"DEC-014","target":"DEC-013"},{"relation":"supersedes","source":"REQ-015","target":"REQ-008"},{"relation":"supersedes","source":"DEC-012","target":"DEC-005"}],"revision":15,"snapshot_hash":"4889d3047c5a92d2bdf1f301cef0d1d1a21f1af7c701002b41977e539d8c282e","verdict":"BLOCKED","working_id":"WORKING-SPEC-b8886a6cd704-memory-coding-rules"}
{"affected_ids":["AC-018","DEC-017","DISC-015","REQ-023"],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":[],"added_ids":["AC-018","DEC-017","DISC-015","REQ-023"],"changed_ids":[],"removed_ids":[]},"epoch":"279724065e094b639e5e54d63fa712b8","event_hash":"d5c539017542fd2894d4d0e47a11f1592d4e4835423c1dde498bff65b65e10fa","event_type":"reconcile","event_version":1,"open_decisions":["多輸出相同資料頻率及依用途選慢分支耗盡政策已確認；各專案設計表須說明觸發條件、恢復與共享實作。RCU／有界共享區塊／獨立游標選型依專案條件決定，不作為統一已採用實作。","立即保護、高頻首次通知／後續聚合、滿載覆寫最舊事件及持續故障有界模組狀態均已採用。具體分派、聚合識別、期限、結束與恢復條件由專案明定；可靠復原須能從持續狀態重新發現未完成工作已採用；觸發機制與期限由專案明定，不強制統一輪詢。","容量／時間雙觸發與 Stop 限時排空已採用。聚合／背壓對不可暫停來源、即時控制及硬體必需 bank 的適用方式待確認；每層在途資料與完成語意由專案提供。CSV 案例顯示須區分局部流控與最終消費端回饋；可靠錄製遇不可暫停來源的政策仍待討論。","具體規則強度、編號、驗收映射與其他新增主題仍待讨论。禁止把未知風險默認安全。"],"previous_event_hash":"f68a7621071bd4bcad84bfb078a15565ba29df44cfcb46e6bc1586a77a7d4f8f","previous_snapshot_hash":"4889d3047c5a92d2bdf1f301cef0d1d1a21f1af7c701002b41977e539d8c282e","recorded_at":"2026-09-30T06:13:08.993589+00:00","relationships":[{"relation":"refines","source":"REQ-023","target":"REQ-012"},{"relation":"refines","source":"REQ-022","target":"REQ-006"},{"relation":"refines","source":"DEC-016","target":"DEC-004"},{"relation":"refines","source":"REQ-021","target":"REQ-018"},{"relation":"supersedes","source":"DEC-004","target":"DEC-003"},{"relation":"refines","source":"REQ-018","target":"REQ-017"},{"relation":"refines","source":"DEC-014","target":"DEC-013"},{"relation":"supersedes","source":"REQ-015","target":"REQ-008"},{"relation":"supersedes","source":"DEC-012","target":"DEC-005"}],"revision":16,"snapshot_hash":"6120f55a91b20ae61dec85f9db262edd6e0530c5ee7145029205271178435aa8","verdict":"BLOCKED","working_id":"WORKING-SPEC-b8886a6cd704-memory-coding-rules"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":[],"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"279724065e094b639e5e54d63fa712b8","event_hash":"d4d3e1db7a68e4c13459c1bc31da62e0bea09a9c68653cdb598444b41e3c8869","event_type":"reconcile","event_version":1,"open_decisions":["多輸出相同資料頻率及依用途選慢分支耗盡政策已確認；各專案設計表須說明觸發條件、恢復與共享實作。RCU／有界共享區塊／獨立游標選型依專案條件決定，不作為統一已採用實作。","立即保護、高頻首次通知／後續聚合、滿載覆寫最舊事件及持續故障有界模組狀態均已採用。具體分派、聚合識別、期限、結束與恢復條件由專案明定；可靠復原須能從持續狀態重新發現未完成工作已採用；觸發機制與期限由專案明定，不強制統一輪詢。","容量／時間雙觸發與 Stop 限時排空已採用。聚合／背壓對不可暫停來源、即時控制及硬體必需 bank 的適用方式待確認；每層在途資料與完成語意由專案提供。CSV 案例顯示須區分局部流控與最終消費端回饋；可靠錄製遇不可暫停來源的政策仍待討論。","具體規則強度、編號、驗收映射與其他新增主題仍待讨论。禁止把未知風險默認安全。","Q-SPECIAL-FLOW-001@17"],"previous_event_hash":"d5c539017542fd2894d4d0e47a11f1592d4e4835423c1dde498bff65b65e10fa","previous_snapshot_hash":"6120f55a91b20ae61dec85f9db262edd6e0530c5ee7145029205271178435aa8","recorded_at":"2026-09-30T06:13:27.915142+00:00","relationships":[{"relation":"refines","source":"REQ-023","target":"REQ-012"},{"relation":"refines","source":"REQ-022","target":"REQ-006"},{"relation":"refines","source":"DEC-016","target":"DEC-004"},{"relation":"refines","source":"REQ-021","target":"REQ-018"},{"relation":"supersedes","source":"DEC-004","target":"DEC-003"},{"relation":"refines","source":"REQ-018","target":"REQ-017"},{"relation":"refines","source":"DEC-014","target":"DEC-013"},{"relation":"supersedes","source":"REQ-015","target":"REQ-008"},{"relation":"supersedes","source":"DEC-012","target":"DEC-005"}],"revision":17,"snapshot_hash":"06e59b4b2798257b3b0b1caa1c911ee74c58758f4aa749d795b23cad236e2468","verdict":"BLOCKED","working_id":"WORKING-SPEC-b8886a6cd704-memory-coding-rules"}
{"affected_ids":["AC-019","DEC-018","DISC-016","REQ-024"],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":[],"added_ids":["AC-019","DEC-018","DISC-016","REQ-024"],"changed_ids":[],"removed_ids":[]},"epoch":"279724065e094b639e5e54d63fa712b8","event_hash":"3de3d300c3d3df24acbb5307e671a63b239dd092344c3618774c828353969457","event_type":"reconcile","event_version":1,"open_decisions":["多輸出相同資料頻率及依用途選慢分支耗盡政策已確認；各專案設計表須說明觸發條件、恢復與共享實作。RCU／有界共享區塊／獨立游標選型依專案條件決定，不作為統一已採用實作。","立即保護、高頻首次通知／後續聚合、滿載覆寫最舊事件及持續故障有界模組狀態均已採用。具體分派、聚合識別、期限、結束與恢復條件由專案明定；可靠復原須能從持續狀態重新發現未完成工作已採用；觸發機制與期限由專案明定，不強制統一輪詢。","特殊資料流適用原則已由 REQ-024 確認；各專案明定不可暫停來源的耗盡處置、即時期限、必要 bank 及各層在途資料與完成語意，不再列為本共用規則的待選政策。","具體規則強度、編號、驗收映射與其他新增主題仍待讨论。禁止把未知風險默認安全。"],"previous_event_hash":"d4d3e1db7a68e4c13459c1bc31da62e0bea09a9c68653cdb598444b41e3c8869","previous_snapshot_hash":"06e59b4b2798257b3b0b1caa1c911ee74c58758f4aa749d795b23cad236e2468","recorded_at":"2026-09-30T06:18:45.313395+00:00","relationships":[{"relation":"refines","source":"REQ-024","target":"REQ-015"},{"relation":"refines","source":"REQ-023","target":"REQ-012"},{"relation":"refines","source":"REQ-022","target":"REQ-006"},{"relation":"refines","source":"DEC-016","target":"DEC-004"},{"relation":"refines","source":"REQ-021","target":"REQ-018"},{"relation":"supersedes","source":"DEC-004","target":"DEC-003"},{"relation":"refines","source":"REQ-018","target":"REQ-017"},{"relation":"refines","source":"DEC-014","target":"DEC-013"},{"relation":"supersedes","source":"REQ-015","target":"REQ-008"},{"relation":"supersedes","source":"DEC-012","target":"DEC-005"}],"revision":18,"snapshot_hash":"52f1f5e3782080b25dcc9ba038bd14f59deeec548164dab6526bcd670e742547","verdict":"BLOCKED","working_id":"WORKING-SPEC-b8886a6cd704-memory-coding-rules"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":[],"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"279724065e094b639e5e54d63fa712b8","event_hash":"dac7832b53da5b61a43b32e75fe21905e1d36f5822ca92d2bf9f4c117794175a","event_type":"reconcile","event_version":1,"open_decisions":["多輸出相同資料頻率及依用途選慢分支耗盡政策已確認；各專案設計表須說明觸發條件、恢復與共享實作。RCU／有界共享區塊／獨立游標選型依專案條件決定，不作為統一已採用實作。","立即保護、高頻首次通知／後續聚合、滿載覆寫最舊事件及持續故障有界模組狀態均已採用。具體分派、聚合識別、期限、結束與恢復條件由專案明定；可靠復原須能從持續狀態重新發現未完成工作已採用；觸發機制與期限由專案明定，不強制統一輪詢。","特殊資料流適用原則已由 REQ-024 確認；各專案明定不可暫停來源的耗盡處置、即時期限、必要 bank 及各層在途資料與完成語意，不再列為本共用規則的待選政策。","具體規則強度、編號、驗收映射與其他新增主題仍待讨论。禁止把未知風險默認安全。","Q-RULE-STRENGTH-001@19"],"previous_event_hash":"3de3d300c3d3df24acbb5307e671a63b239dd092344c3618774c828353969457","previous_snapshot_hash":"52f1f5e3782080b25dcc9ba038bd14f59deeec548164dab6526bcd670e742547","recorded_at":"2026-09-30T06:19:02.346140+00:00","relationships":[{"relation":"refines","source":"REQ-024","target":"REQ-015"},{"relation":"refines","source":"REQ-023","target":"REQ-012"},{"relation":"refines","source":"REQ-022","target":"REQ-006"},{"relation":"refines","source":"DEC-016","target":"DEC-004"},{"relation":"refines","source":"REQ-021","target":"REQ-018"},{"relation":"supersedes","source":"DEC-004","target":"DEC-003"},{"relation":"refines","source":"REQ-018","target":"REQ-017"},{"relation":"refines","source":"DEC-014","target":"DEC-013"},{"relation":"supersedes","source":"REQ-015","target":"REQ-008"},{"relation":"supersedes","source":"DEC-012","target":"DEC-005"}],"revision":19,"snapshot_hash":"f83ced0ceb91eb56655049f9f932e5d9a0dd9324026245531da88a90a18adc25","verdict":"BLOCKED","working_id":"WORKING-SPEC-b8886a6cd704-memory-coding-rules"}
{"affected_ids":["AC-020","DEC-019","DISC-017","REQ-025"],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":[],"added_ids":["AC-020","DEC-019","DISC-017","REQ-025"],"changed_ids":[],"removed_ids":[]},"epoch":"279724065e094b639e5e54d63fa712b8","event_hash":"c70160318c0f67d2761b91d49d4e0dead70d382119b3eddc595dce5bd68011d9","event_type":"reconcile","event_version":1,"open_decisions":[],"previous_event_hash":"dac7832b53da5b61a43b32e75fe21905e1d36f5822ca92d2bf9f4c117794175a","previous_snapshot_hash":"f83ced0ceb91eb56655049f9f932e5d9a0dd9324026245531da88a90a18adc25","recorded_at":"2026-09-30T06:22:52.418677+00:00","relationships":[{"relation":"refines","source":"REQ-025","target":"REQ-001"},{"relation":"refines","source":"REQ-024","target":"REQ-015"},{"relation":"refines","source":"REQ-023","target":"REQ-012"},{"relation":"refines","source":"REQ-022","target":"REQ-006"},{"relation":"refines","source":"DEC-016","target":"DEC-004"},{"relation":"refines","source":"REQ-021","target":"REQ-018"},{"relation":"supersedes","source":"DEC-004","target":"DEC-003"},{"relation":"refines","source":"REQ-018","target":"REQ-017"},{"relation":"refines","source":"DEC-014","target":"DEC-013"},{"relation":"supersedes","source":"REQ-015","target":"REQ-008"},{"relation":"supersedes","source":"DEC-012","target":"DEC-005"}],"revision":20,"snapshot_hash":"f7d733286e511fb12b338edf0de76df16b32ce1b10511fc12978ae095c8ffcc7","verdict":"PASS","working_id":"WORKING-SPEC-b8886a6cd704-memory-coding-rules"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":[],"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"279724065e094b639e5e54d63fa712b8","event_hash":"356b7b287cd56f518fa51826d81798d78de10b9eeff13e00424e0961fd9f1687","event_type":"reconcile","event_version":1,"open_decisions":["Q-MODULAR-DESIGN-001@21"],"previous_event_hash":"c70160318c0f67d2761b91d49d4e0dead70d382119b3eddc595dce5bd68011d9","previous_snapshot_hash":"f7d733286e511fb12b338edf0de76df16b32ce1b10511fc12978ae095c8ffcc7","recorded_at":"2026-09-30T10:29:20.202419+00:00","relationships":[{"relation":"refines","source":"REQ-025","target":"REQ-001"},{"relation":"refines","source":"REQ-024","target":"REQ-015"},{"relation":"refines","source":"REQ-023","target":"REQ-012"},{"relation":"refines","source":"REQ-022","target":"REQ-006"},{"relation":"refines","source":"DEC-016","target":"DEC-004"},{"relation":"refines","source":"REQ-021","target":"REQ-018"},{"relation":"supersedes","source":"DEC-004","target":"DEC-003"},{"relation":"refines","source":"REQ-018","target":"REQ-017"},{"relation":"refines","source":"DEC-014","target":"DEC-013"},{"relation":"supersedes","source":"REQ-015","target":"REQ-008"},{"relation":"supersedes","source":"DEC-012","target":"DEC-005"}],"revision":21,"snapshot_hash":"6b28a0747e5b04e2013f38924affeed6f2f2194d8e312e3b4a497e09cb70f147","verdict":"BLOCKED","working_id":"WORKING-SPEC-b8886a6cd704-memory-coding-rules"}
{"affected_ids":["AC-021","DEC-020","DISC-018","REQ-026"],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":[],"added_ids":["AC-021","DEC-020","DISC-018","REQ-026"],"changed_ids":[],"removed_ids":[]},"epoch":"279724065e094b639e5e54d63fa712b8","event_hash":"a26f4fd2e323d71bcb59dba9396301dd84a5cd42a15b7987a8d31bf3b449745f","event_type":"reconcile","event_version":1,"open_decisions":[],"previous_event_hash":"356b7b287cd56f518fa51826d81798d78de10b9eeff13e00424e0961fd9f1687","previous_snapshot_hash":"6b28a0747e5b04e2013f38924affeed6f2f2194d8e312e3b4a497e09cb70f147","recorded_at":"2026-09-30T10:34:25.727983+00:00","relationships":[{"relation":"refines","source":"REQ-026","target":"REQ-020"},{"relation":"refines","source":"REQ-025","target":"REQ-001"},{"relation":"refines","source":"REQ-024","target":"REQ-015"},{"relation":"refines","source":"REQ-023","target":"REQ-012"},{"relation":"refines","source":"REQ-022","target":"REQ-006"},{"relation":"refines","source":"DEC-016","target":"DEC-004"},{"relation":"refines","source":"REQ-021","target":"REQ-018"},{"relation":"supersedes","source":"DEC-004","target":"DEC-003"},{"relation":"refines","source":"REQ-018","target":"REQ-017"},{"relation":"refines","source":"DEC-014","target":"DEC-013"},{"relation":"supersedes","source":"REQ-015","target":"REQ-008"},{"relation":"supersedes","source":"DEC-012","target":"DEC-005"}],"revision":22,"snapshot_hash":"514d97cad942fb110b4f943dabc9e2172065923bddf4822b0be1f90d38db8065","verdict":"PASS","working_id":"WORKING-SPEC-b8886a6cd704-memory-coding-rules"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":[],"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"279724065e094b639e5e54d63fa712b8","event_hash":"c752d41e7fe9f2ee88a02ec66c48c0eda3a9b0738f46714511e6a9c7175e67cd","event_type":"reconcile","event_version":1,"open_decisions":[],"previous_event_hash":"a26f4fd2e323d71bcb59dba9396301dd84a5cd42a15b7987a8d31bf3b449745f","previous_snapshot_hash":"514d97cad942fb110b4f943dabc9e2172065923bddf4822b0be1f90d38db8065","recorded_at":"2026-10-01T00:49:40.510739+00:00","relationships":[{"relation":"refines","source":"REQ-026","target":"REQ-020"},{"relation":"refines","source":"REQ-025","target":"REQ-001"},{"relation":"refines","source":"REQ-024","target":"REQ-015"},{"relation":"refines","source":"REQ-023","target":"REQ-012"},{"relation":"refines","source":"REQ-022","target":"REQ-006"},{"relation":"refines","source":"DEC-016","target":"DEC-004"},{"relation":"refines","source":"REQ-021","target":"REQ-018"},{"relation":"supersedes","source":"DEC-004","target":"DEC-003"},{"relation":"refines","source":"REQ-018","target":"REQ-017"},{"relation":"refines","source":"DEC-014","target":"DEC-013"},{"relation":"supersedes","source":"REQ-015","target":"REQ-008"},{"relation":"supersedes","source":"DEC-012","target":"DEC-005"}],"revision":23,"snapshot_hash":"6ad80edc5af086392513474e27bcddce3667a4a7c0b9d44b455f797346805f47","verdict":"PASS","working_id":"WORKING-SPEC-b8886a6cd704-memory-coding-rules"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":[],"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"279724065e094b639e5e54d63fa712b8","event_hash":"0d529097bdd92fdac849ffea4f4891a6b4f7d2bff396b5f3271d182ff3717c7b","event_type":"reconcile","event_version":1,"open_decisions":["Q-MODULE-FIELDS-001@24"],"previous_event_hash":"c752d41e7fe9f2ee88a02ec66c48c0eda3a9b0738f46714511e6a9c7175e67cd","previous_snapshot_hash":"6ad80edc5af086392513474e27bcddce3667a4a7c0b9d44b455f797346805f47","recorded_at":"2026-10-01T00:50:22.978903+00:00","relationships":[{"relation":"refines","source":"REQ-026","target":"REQ-020"},{"relation":"refines","source":"REQ-025","target":"REQ-001"},{"relation":"refines","source":"REQ-024","target":"REQ-015"},{"relation":"refines","source":"REQ-023","target":"REQ-012"},{"relation":"refines","source":"REQ-022","target":"REQ-006"},{"relation":"refines","source":"DEC-016","target":"DEC-004"},{"relation":"refines","source":"REQ-021","target":"REQ-018"},{"relation":"supersedes","source":"DEC-004","target":"DEC-003"},{"relation":"refines","source":"REQ-018","target":"REQ-017"},{"relation":"refines","source":"DEC-014","target":"DEC-013"},{"relation":"supersedes","source":"REQ-015","target":"REQ-008"},{"relation":"supersedes","source":"DEC-012","target":"DEC-005"}],"revision":24,"snapshot_hash":"50b16a8f244f27d4904c6bc4637a627f87a6026e5242ebf710547d3b1ac25477","verdict":"BLOCKED","working_id":"WORKING-SPEC-b8886a6cd704-memory-coding-rules"}
{"affected_ids":["AC-022","DEC-021","DISC-019","REQ-027"],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":[],"added_ids":["AC-022","DEC-021","DISC-019","REQ-027"],"changed_ids":[],"removed_ids":[]},"epoch":"279724065e094b639e5e54d63fa712b8","event_hash":"7c6d07646f80b69b6e1d7f18cddd75d7beb2f2e6623f936d547e3788615ff7d9","event_type":"reconcile","event_version":1,"open_decisions":[],"previous_event_hash":"0d529097bdd92fdac849ffea4f4891a6b4f7d2bff396b5f3271d182ff3717c7b","previous_snapshot_hash":"50b16a8f244f27d4904c6bc4637a627f87a6026e5242ebf710547d3b1ac25477","recorded_at":"2026-10-01T00:57:25.526204+00:00","relationships":[{"relation":"refines","source":"REQ-027","target":"REQ-026"},{"relation":"refines","source":"REQ-026","target":"REQ-020"},{"relation":"refines","source":"REQ-025","target":"REQ-001"},{"relation":"refines","source":"REQ-024","target":"REQ-015"},{"relation":"refines","source":"REQ-023","target":"REQ-012"},{"relation":"refines","source":"REQ-022","target":"REQ-006"},{"relation":"refines","source":"DEC-016","target":"DEC-004"},{"relation":"refines","source":"REQ-021","target":"REQ-018"},{"relation":"supersedes","source":"DEC-004","target":"DEC-003"},{"relation":"refines","source":"REQ-018","target":"REQ-017"},{"relation":"refines","source":"DEC-014","target":"DEC-013"},{"relation":"supersedes","source":"REQ-015","target":"REQ-008"},{"relation":"supersedes","source":"DEC-012","target":"DEC-005"}],"revision":25,"snapshot_hash":"7f50946ee20c419e66620faac3dfc11fbeffeba3b60c95a970e13a40aef99024","verdict":"PASS","working_id":"WORKING-SPEC-b8886a6cd704-memory-coding-rules"}
{"affected_ids":["AC-023","DEC-022","DISC-020","REQ-028"],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":[],"added_ids":["AC-023","DEC-022","DISC-020","REQ-028"],"changed_ids":[],"removed_ids":[]},"epoch":"279724065e094b639e5e54d63fa712b8","event_hash":"149be444823242c85c5f120379446a3aad4b856973ab82fb17f215e3c618da3e","event_type":"reconcile","event_version":1,"open_decisions":[],"previous_event_hash":"7c6d07646f80b69b6e1d7f18cddd75d7beb2f2e6623f936d547e3788615ff7d9","previous_snapshot_hash":"7f50946ee20c419e66620faac3dfc11fbeffeba3b60c95a970e13a40aef99024","recorded_at":"2026-10-01T01:29:59.188235+00:00","relationships":[{"relation":"refines","source":"REQ-028","target":"REQ-027"},{"relation":"refines","source":"REQ-028","target":"REQ-022"},{"relation":"refines","source":"REQ-027","target":"REQ-026"},{"relation":"refines","source":"REQ-026","target":"REQ-020"},{"relation":"refines","source":"REQ-025","target":"REQ-001"},{"relation":"refines","source":"REQ-024","target":"REQ-015"},{"relation":"refines","source":"REQ-023","target":"REQ-012"},{"relation":"refines","source":"REQ-022","target":"REQ-006"},{"relation":"refines","source":"DEC-016","target":"DEC-004"},{"relation":"refines","source":"REQ-021","target":"REQ-018"},{"relation":"supersedes","source":"DEC-004","target":"DEC-003"},{"relation":"refines","source":"REQ-018","target":"REQ-017"},{"relation":"refines","source":"DEC-014","target":"DEC-013"},{"relation":"supersedes","source":"REQ-015","target":"REQ-008"},{"relation":"supersedes","source":"DEC-012","target":"DEC-005"}],"revision":26,"snapshot_hash":"068d9c15337b6cac23405c6b0e013dd9d3fa4e9ed9f45463f0a21df86fff5eca","verdict":"PASS","working_id":"WORKING-SPEC-b8886a6cd704-memory-coding-rules"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":[],"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"279724065e094b639e5e54d63fa712b8","event_hash":"dd5cea05b266beb666c8dadfe213044e4821b8f5ff4f2a9defc3b94fe154da3a","event_type":"reconcile","event_version":1,"open_decisions":[],"previous_event_hash":"149be444823242c85c5f120379446a3aad4b856973ab82fb17f215e3c618da3e","previous_snapshot_hash":"068d9c15337b6cac23405c6b0e013dd9d3fa4e9ed9f45463f0a21df86fff5eca","recorded_at":"2026-10-01T01:32:12.687726+00:00","relationships":[{"relation":"refines","source":"REQ-028","target":"REQ-027"},{"relation":"refines","source":"REQ-028","target":"REQ-022"},{"relation":"refines","source":"REQ-027","target":"REQ-026"},{"relation":"refines","source":"REQ-026","target":"REQ-020"},{"relation":"refines","source":"REQ-025","target":"REQ-001"},{"relation":"refines","source":"REQ-024","target":"REQ-015"},{"relation":"refines","source":"REQ-023","target":"REQ-012"},{"relation":"refines","source":"REQ-022","target":"REQ-006"},{"relation":"refines","source":"DEC-016","target":"DEC-004"},{"relation":"refines","source":"REQ-021","target":"REQ-018"},{"relation":"supersedes","source":"DEC-004","target":"DEC-003"},{"relation":"refines","source":"REQ-018","target":"REQ-017"},{"relation":"refines","source":"DEC-014","target":"DEC-013"},{"relation":"supersedes","source":"REQ-015","target":"REQ-008"},{"relation":"supersedes","source":"DEC-012","target":"DEC-005"}],"revision":27,"snapshot_hash":"f96e5f34a90f5b28d8cb87f5ada7a79bf1b5fd2e6c2e7e5a18f48f1518d5ebf5","verdict":"PASS","working_id":"WORKING-SPEC-b8886a6cd704-memory-coding-rules"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":[],"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"279724065e094b639e5e54d63fa712b8","event_hash":"c1d6291c8a31b09f0a152552fd25cdc572646606eeee64ab1dde0ec14de4bf62","event_type":"reconcile","event_version":1,"open_decisions":["Q-FLOW-FIELDS-001@28"],"previous_event_hash":"dd5cea05b266beb666c8dadfe213044e4821b8f5ff4f2a9defc3b94fe154da3a","previous_snapshot_hash":"f96e5f34a90f5b28d8cb87f5ada7a79bf1b5fd2e6c2e7e5a18f48f1518d5ebf5","recorded_at":"2026-10-01T01:32:27.284716+00:00","relationships":[{"relation":"refines","source":"REQ-028","target":"REQ-027"},{"relation":"refines","source":"REQ-028","target":"REQ-022"},{"relation":"refines","source":"REQ-027","target":"REQ-026"},{"relation":"refines","source":"REQ-026","target":"REQ-020"},{"relation":"refines","source":"REQ-025","target":"REQ-001"},{"relation":"refines","source":"REQ-024","target":"REQ-015"},{"relation":"refines","source":"REQ-023","target":"REQ-012"},{"relation":"refines","source":"REQ-022","target":"REQ-006"},{"relation":"refines","source":"DEC-016","target":"DEC-004"},{"relation":"refines","source":"REQ-021","target":"REQ-018"},{"relation":"supersedes","source":"DEC-004","target":"DEC-003"},{"relation":"refines","source":"REQ-018","target":"REQ-017"},{"relation":"refines","source":"DEC-014","target":"DEC-013"},{"relation":"supersedes","source":"REQ-015","target":"REQ-008"},{"relation":"supersedes","source":"DEC-012","target":"DEC-005"}],"revision":28,"snapshot_hash":"2cd9ba64812a4cdfecf9eff0a6d0b6f18984f8cdfcd78634f667641d33c62eab","verdict":"BLOCKED","working_id":"WORKING-SPEC-b8886a6cd704-memory-coding-rules"}
{"affected_ids":["AC-024","AC-025","DEC-023","DEC-024","DISC-021","DISC-022","REQ-029","REQ-030"],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":[],"added_ids":["AC-024","AC-025","DEC-023","DEC-024","DISC-021","DISC-022","REQ-029","REQ-030"],"changed_ids":[],"removed_ids":[]},"epoch":"279724065e094b639e5e54d63fa712b8","event_hash":"e22b5d2266e769b02582af75f86a530a1814f7ff757ade065c6a60bef7bfa515","event_type":"reconcile","event_version":1,"open_decisions":[],"previous_event_hash":"c1d6291c8a31b09f0a152552fd25cdc572646606eeee64ab1dde0ec14de4bf62","previous_snapshot_hash":"2cd9ba64812a4cdfecf9eff0a6d0b6f18984f8cdfcd78634f667641d33c62eab","recorded_at":"2026-10-01T01:41:22.593030+00:00","relationships":[{"relation":"refines","source":"REQ-029","target":"REQ-019"},{"relation":"refines","source":"REQ-030","target":"REQ-027"},{"relation":"refines","source":"REQ-028","target":"REQ-027"},{"relation":"refines","source":"REQ-029","target":"REQ-019"},{"relation":"refines","source":"REQ-030","target":"REQ-027"},{"relation":"refines","source":"REQ-028","target":"REQ-022"},{"relation":"refines","source":"REQ-027","target":"REQ-026"},{"relation":"refines","source":"REQ-026","target":"REQ-020"},{"relation":"refines","source":"REQ-025","target":"REQ-001"},{"relation":"refines","source":"REQ-024","target":"REQ-015"},{"relation":"refines","source":"REQ-023","target":"REQ-012"},{"relation":"refines","source":"REQ-022","target":"REQ-006"},{"relation":"refines","source":"DEC-016","target":"DEC-004"},{"relation":"refines","source":"REQ-021","target":"REQ-018"},{"relation":"supersedes","source":"DEC-004","target":"DEC-003"},{"relation":"refines","source":"REQ-018","target":"REQ-017"},{"relation":"refines","source":"DEC-014","target":"DEC-013"},{"relation":"supersedes","source":"REQ-015","target":"REQ-008"},{"relation":"supersedes","source":"DEC-012","target":"DEC-005"}],"revision":29,"snapshot_hash":"072434d87a139b4a2b541254ff5b058c5ab698a942c9c2225396af08bdcc4dcc","verdict":"PASS","working_id":"WORKING-SPEC-b8886a6cd704-memory-coding-rules"}
{"affected_ids":["AC-026","DEC-025","DISC-023","REQ-031"],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":[],"added_ids":["AC-026","DEC-025","DISC-023","REQ-031"],"changed_ids":[],"removed_ids":[]},"epoch":"279724065e094b639e5e54d63fa712b8","event_hash":"efd244e416908e4ea07a6da0f61b6c349f73bd40865a2a04574599011b639d1d","event_type":"reconcile","event_version":1,"open_decisions":[],"previous_event_hash":"e22b5d2266e769b02582af75f86a530a1814f7ff757ade065c6a60bef7bfa515","previous_snapshot_hash":"072434d87a139b4a2b541254ff5b058c5ab698a942c9c2225396af08bdcc4dcc","recorded_at":"2026-10-01T01:50:13.838475+00:00","relationships":[{"relation":"refines","source":"REQ-031","target":"REQ-027"},{"relation":"refines","source":"REQ-031","target":"REQ-030"},{"relation":"refines","source":"REQ-029","target":"REQ-019"},{"relation":"refines","source":"REQ-030","target":"REQ-027"},{"relation":"refines","source":"REQ-028","target":"REQ-027"},{"relation":"refines","source":"REQ-031","target":"REQ-027"},{"relation":"refines","source":"REQ-031","target":"REQ-030"},{"relation":"refines","source":"REQ-029","target":"REQ-019"},{"relation":"refines","source":"REQ-030","target":"REQ-027"},{"relation":"refines","source":"REQ-028","target":"REQ-022"},{"relation":"refines","source":"REQ-027","target":"REQ-026"},{"relation":"refines","source":"REQ-026","target":"REQ-020"},{"relation":"refines","source":"REQ-025","target":"REQ-001"},{"relation":"refines","source":"REQ-024","target":"REQ-015"},{"relation":"refines","source":"REQ-023","target":"REQ-012"},{"relation":"refines","source":"REQ-022","target":"REQ-006"},{"relation":"refines","source":"DEC-016","target":"DEC-004"},{"relation":"refines","source":"REQ-021","target":"REQ-018"},{"relation":"supersedes","source":"DEC-004","target":"DEC-003"},{"relation":"refines","source":"REQ-018","target":"REQ-017"},{"relation":"refines","source":"DEC-014","target":"DEC-013"},{"relation":"supersedes","source":"REQ-015","target":"REQ-008"},{"relation":"supersedes","source":"DEC-012","target":"DEC-005"}],"revision":30,"snapshot_hash":"c6c4feca9f158d34bc676a3a97d120fe2b4a43a3e0dffec1891bb1d03a8fa49f","verdict":"PASS","working_id":"WORKING-SPEC-b8886a6cd704-memory-coding-rules"}
{"affected_ids":["AC-005","AC-014","AC-020","REQ-007","REQ-008"],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":["AC-005","AC-014","AC-020"],"added_ids":[],"changed_ids":["AC-005","AC-014","AC-020","REQ-007","REQ-008"],"removed_ids":[]},"epoch":"279724065e094b639e5e54d63fa712b8","event_hash":"fd97ea5cf04e1b356404e63d60252e94504c597fd778c579eca286265646a16e","event_type":"reconcile","event_version":1,"open_decisions":[],"previous_event_hash":"efd244e416908e4ea07a6da0f61b6c349f73bd40865a2a04574599011b639d1d","previous_snapshot_hash":"c6c4feca9f158d34bc676a3a97d120fe2b4a43a3e0dffec1891bb1d03a8fa49f","recorded_at":"2026-10-02T01:03:34.064513+00:00","relationships":[{"relation":"refines","source":"REQ-031","target":"REQ-027"},{"relation":"refines","source":"REQ-031","target":"REQ-030"},{"relation":"refines","source":"REQ-029","target":"REQ-019"},{"relation":"refines","source":"REQ-030","target":"REQ-027"},{"relation":"refines","source":"REQ-028","target":"REQ-027"},{"relation":"refines","source":"REQ-031","target":"REQ-027"},{"relation":"refines","source":"REQ-031","target":"REQ-030"},{"relation":"refines","source":"REQ-029","target":"REQ-019"},{"relation":"refines","source":"REQ-030","target":"REQ-027"},{"relation":"refines","source":"REQ-028","target":"REQ-022"},{"relation":"refines","source":"REQ-027","target":"REQ-026"},{"relation":"refines","source":"REQ-026","target":"REQ-020"},{"relation":"refines","source":"REQ-025","target":"REQ-001"},{"relation":"refines","source":"REQ-024","target":"REQ-015"},{"relation":"refines","source":"REQ-023","target":"REQ-012"},{"relation":"refines","source":"REQ-022","target":"REQ-006"},{"relation":"refines","source":"DEC-016","target":"DEC-004"},{"relation":"refines","source":"REQ-021","target":"REQ-018"},{"relation":"supersedes","source":"DEC-004","target":"DEC-003"},{"relation":"refines","source":"REQ-018","target":"REQ-017"},{"relation":"refines","source":"DEC-014","target":"DEC-013"},{"relation":"supersedes","source":"REQ-015","target":"REQ-008"},{"relation":"supersedes","source":"DEC-012","target":"DEC-005"}],"revision":31,"snapshot_hash":"acf24d4aa8dac3cbf909c386b5eeef1c7c4302613503b9e67f0e9c77c9f44094","verdict":"PASS","working_id":"WORKING-SPEC-b8886a6cd704-memory-coding-rules"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":[],"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"279724065e094b639e5e54d63fa712b8","event_hash":"1e389f7fb89d094d9d5fac6f826a6ee721fb0d37d46277ec5eb2bf06c3d54e70","event_type":"reconcile","event_version":1,"open_decisions":[],"previous_event_hash":"fd97ea5cf04e1b356404e63d60252e94504c597fd778c579eca286265646a16e","previous_snapshot_hash":"acf24d4aa8dac3cbf909c386b5eeef1c7c4302613503b9e67f0e9c77c9f44094","recorded_at":"2026-10-02T02:10:22.971433+00:00","relationships":[{"relation":"refines","source":"REQ-031","target":"REQ-027"},{"relation":"refines","source":"REQ-031","target":"REQ-030"},{"relation":"refines","source":"REQ-029","target":"REQ-019"},{"relation":"refines","source":"REQ-030","target":"REQ-027"},{"relation":"refines","source":"REQ-028","target":"REQ-027"},{"relation":"refines","source":"REQ-031","target":"REQ-027"},{"relation":"refines","source":"REQ-031","target":"REQ-030"},{"relation":"refines","source":"REQ-029","target":"REQ-019"},{"relation":"refines","source":"REQ-030","target":"REQ-027"},{"relation":"refines","source":"REQ-028","target":"REQ-022"},{"relation":"refines","source":"REQ-027","target":"REQ-026"},{"relation":"refines","source":"REQ-026","target":"REQ-020"},{"relation":"refines","source":"REQ-025","target":"REQ-001"},{"relation":"refines","source":"REQ-024","target":"REQ-015"},{"relation":"refines","source":"REQ-023","target":"REQ-012"},{"relation":"refines","source":"REQ-022","target":"REQ-006"},{"relation":"refines","source":"DEC-016","target":"DEC-004"},{"relation":"refines","source":"REQ-021","target":"REQ-018"},{"relation":"supersedes","source":"DEC-004","target":"DEC-003"},{"relation":"refines","source":"REQ-018","target":"REQ-017"},{"relation":"refines","source":"DEC-014","target":"DEC-013"},{"relation":"supersedes","source":"REQ-015","target":"REQ-008"},{"relation":"supersedes","source":"DEC-012","target":"DEC-005"}],"revision":32,"snapshot_hash":"beb07ff7d387b5f56884f14329ddb32e9e3c52f12f1c6e17fd682a4ea1aa7e72","verdict":"PASS","working_id":"WORKING-SPEC-b8886a6cd704-memory-coding-rules"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"279724065e094b639e5e54d63fa712b8","event_hash":"52828b41b360bf2400506c1bcfa2399c033e7694f6031651329af0cbd225bcef","event_type":"materialize","event_version":1,"open_decisions":[],"previous_event_hash":"1e389f7fb89d094d9d5fac6f826a6ee721fb0d37d46277ec5eb2bf06c3d54e70","previous_snapshot_hash":"beb07ff7d387b5f56884f14329ddb32e9e3c52f12f1c6e17fd682a4ea1aa7e72","recorded_at":"2026-10-02T02:10:57.781135+00:00","relationships":[],"revision":32,"snapshot_hash":"9779227af9f823f34034c578bc33fb11253d40c93adc25f3fa690e30cf813576","verdict":"PASS","working_id":"WORKING-SPEC-b8886a6cd704-memory-coding-rules"}
{"affected_ids":[],"baseline_contract_hash":"495aaecd07c63af06cb8f2b01a9636ff0a9d833560a4ca079161b47c76dcab49","conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"279724065e094b639e5e54d63fa712b8","event_hash":"5bee493b511b8b2b00c740c0c79879e38aa167c919a1d2de87e1f96987cd85e7","event_type":"reopen","event_version":1,"open_decisions":[],"previous_event_hash":"52828b41b360bf2400506c1bcfa2399c033e7694f6031651329af0cbd225bcef","previous_snapshot_hash":"9779227af9f823f34034c578bc33fb11253d40c93adc25f3fa690e30cf813576","recorded_at":"2026-10-02T02:11:24.116227+00:00","relationships":[],"revision":33,"snapshot_hash":"3721a42fa47a4cc9a7bcde04e203b691dbd961f5317f77e137b5afeeccdfed9d","verdict":"BLOCKED","working_id":"WORKING-SPEC-b8886a6cd704-memory-coding-rules"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"279724065e094b639e5e54d63fa712b8","event_hash":"11eea616697bb8488f105adb533fe2c50586c7dfcfce222bc48d608d544718c6","event_type":"materialize","event_version":1,"open_decisions":[],"previous_event_hash":"5bee493b511b8b2b00c740c0c79879e38aa167c919a1d2de87e1f96987cd85e7","previous_snapshot_hash":"3721a42fa47a4cc9a7bcde04e203b691dbd961f5317f77e137b5afeeccdfed9d","recorded_at":"2026-10-02T02:11:59.422649+00:00","relationships":[],"revision":33,"snapshot_hash":"36766d0c254ab4354f5a17ad33650ae192875a2525e9579b180d34f4eba7ccf8","verdict":"PASS","working_id":"WORKING-SPEC-b8886a6cd704-memory-coding-rules"}
{"affected_ids":[],"baseline_contract_hash":"495aaecd07c63af06cb8f2b01a9636ff0a9d833560a4ca079161b47c76dcab49","conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"279724065e094b639e5e54d63fa712b8","event_hash":"7c3cba6a97f43d623129eb8d6dafa2fb023c26bac5c8abb4a1388912a1842f7a","event_type":"reopen","event_version":1,"open_decisions":[],"previous_event_hash":"11eea616697bb8488f105adb533fe2c50586c7dfcfce222bc48d608d544718c6","previous_snapshot_hash":"36766d0c254ab4354f5a17ad33650ae192875a2525e9579b180d34f4eba7ccf8","recorded_at":"2026-10-02T02:15:03.421911+00:00","relationships":[],"revision":34,"snapshot_hash":"e9e5fb072403ad3272f6943602dfa8a1b13db8216f0d8bb2216c60a62f4284a8","verdict":"BLOCKED","working_id":"WORKING-SPEC-b8886a6cd704-memory-coding-rules"}
{"affected_ids":["AC-001","AC-002","AC-003","AC-004","AC-005","AC-006","AC-007","AC-008","AC-009","AC-010","AC-011","AC-012","AC-013","AC-014","AC-015","AC-016","AC-017","AC-018","AC-019","AC-020","AC-021","AC-022","AC-023","AC-024","AC-025","AC-026"],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":[],"added_ids":[],"changed_ids":["AC-001","AC-002","AC-003","AC-004","AC-005","AC-006","AC-007","AC-008","AC-009","AC-010","AC-011","AC-012","AC-013","AC-014","AC-015","AC-016","AC-017","AC-018","AC-019","AC-020","AC-021","AC-022","AC-023","AC-024","AC-025","AC-026"],"removed_ids":[]},"epoch":"279724065e094b639e5e54d63fa712b8","event_hash":"81471ee1fa86ac8d1febeef9ca4def2aa1d7685f01bda53a9fb1ee8ee9aac2bb","event_type":"reconcile","event_version":1,"open_decisions":[],"previous_event_hash":"7c3cba6a97f43d623129eb8d6dafa2fb023c26bac5c8abb4a1388912a1842f7a","previous_snapshot_hash":"e9e5fb072403ad3272f6943602dfa8a1b13db8216f0d8bb2216c60a62f4284a8","recorded_at":"2026-10-02T02:15:04.147568+00:00","relationships":[{"relation":"refines","source":"REQ-031","target":"REQ-027"},{"relation":"refines","source":"REQ-031","target":"REQ-030"},{"relation":"refines","source":"REQ-029","target":"REQ-019"},{"relation":"refines","source":"REQ-030","target":"REQ-027"},{"relation":"refines","source":"REQ-028","target":"REQ-027"},{"relation":"refines","source":"REQ-031","target":"REQ-027"},{"relation":"refines","source":"REQ-031","target":"REQ-030"},{"relation":"refines","source":"REQ-029","target":"REQ-019"},{"relation":"refines","source":"REQ-030","target":"REQ-027"},{"relation":"refines","source":"REQ-028","target":"REQ-022"},{"relation":"refines","source":"REQ-027","target":"REQ-026"},{"relation":"refines","source":"REQ-026","target":"REQ-020"},{"relation":"refines","source":"REQ-025","target":"REQ-001"},{"relation":"refines","source":"REQ-024","target":"REQ-015"},{"relation":"refines","source":"REQ-023","target":"REQ-012"},{"relation":"refines","source":"REQ-022","target":"REQ-006"},{"relation":"refines","source":"DEC-016","target":"DEC-004"},{"relation":"refines","source":"REQ-021","target":"REQ-018"},{"relation":"supersedes","source":"DEC-004","target":"DEC-003"},{"relation":"refines","source":"REQ-018","target":"REQ-017"},{"relation":"refines","source":"DEC-014","target":"DEC-013"},{"relation":"supersedes","source":"REQ-015","target":"REQ-008"},{"relation":"supersedes","source":"DEC-012","target":"DEC-005"}],"revision":35,"snapshot_hash":"fdda17ebad331aa8b265324bffc941b2c036ce4b30e4393f7e0d1d4cfb91d700","verdict":"PASS","working_id":"WORKING-SPEC-b8886a6cd704-memory-coding-rules"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"279724065e094b639e5e54d63fa712b8","event_hash":"8dc2e3237ba0e44d8bc5078c6cde2f56e4f0d303ee395e14ed54f12228d19e6a","event_type":"materialize","event_version":1,"open_decisions":[],"previous_event_hash":"81471ee1fa86ac8d1febeef9ca4def2aa1d7685f01bda53a9fb1ee8ee9aac2bb","previous_snapshot_hash":"fdda17ebad331aa8b265324bffc941b2c036ce4b30e4393f7e0d1d4cfb91d700","recorded_at":"2026-10-02T02:15:04.821613+00:00","relationships":[],"revision":35,"snapshot_hash":"0cfde3f79454317123f150f9fd6ae86f0d7842d72ae0f83f3603a8142ef1ad8d","verdict":"PASS","working_id":"WORKING-SPEC-b8886a6cd704-memory-coding-rules"}
```
<!-- spec-audit:end -->
