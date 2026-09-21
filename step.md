# 專案執行步驟指南 (TeDMMA)

這份指南說明如何執行本專案，從單體架構中提取特徵，並透過 RAG 與 LLM 生成對應的微服務測試腳本 (Karate & Pact)。

---

## Step 0: 準備工作
在開始執行程式前，請確保以下環境與檔案皆已設定完畢：

1. **環境設定**：確認已啟動虛擬環境 (`.venv`)，並已安裝所需套件（包含 `haystack-experimental`, `sentence-transformers-haystack` 等）。
2. **API 密鑰**：確認專案根目錄下存在 `api_key.txt`，且裡面已填入有效的 OpenAI API Key。
3. **建立知識庫資料夾 (RAG Knowledge Base)**：
   為了讓生成的測試腳本格式更精準，建議在根目錄建立以下路徑，並放入對應的參考範例：
   - `./rag_knowledge_base/pact/v3/pass` (放置正確的 Pact V3 JSON 範例)
   - `./rag_knowledge_base/karate` (放置標準的 Karate 腳本範例)

---

## Step 1: 萃取特徵與單體架構分析
此步驟會讀取目標 Java 專案壓縮檔，透過 Tree-sitter 提取 AST（抽象語法樹）特徵與測試案例，並交由 LLM 進行微服務架構分析。

* **執行指令**：
  ```bash
  python .\main.py
  ```

* **預期成果**：執行成功後，系統會自動將結果儲存為以下三個實體檔案：
1. `./monolith_features/spring-petclinic-main_features.txt` (擷取出的元件與欄位特徵)
2. `./monolith_test_case_codes/spring-petclinic-main_test_cases.txt` (舊有單體架構的測試程式碼)
3. `./llm_analysis_result/spring-petclinic-main_analysis_response.txt` (LLM 架構拆分與分析報告)
4. `./spring-petclinic-main_api_test.feature`(第一份Karate API 測試腳本)



---

## Step 2: 限制字數以避免 Token 超載 (重要前置作業)

由於步驟 1 產生的 `_test_cases.txt` 通常非常龐大，直接傳給 LLM 進行生成會導致 `context_length_exceeded` 錯誤。在執行步驟 3 之前，請二擇一進行以下處理：

* **作法 A (程式碼截斷)**：修改 `rag_migrate.py` 約第 96 行，加上字元長度限制：
```python
with open(f"./monolith_test_case_codes/{MIGRATE_PROJECT_NAME}_test_cases.txt", "r", encoding="utf-8") as f:
    test_cases = f.read()[:20000]  # 只讀取前兩萬字

```


* **作法 B (手動清理)**：手動打開 `_test_cases.txt`，刪除與本次遷移目標無關的測試類別，只留下精華的相關測試。

---

## Step 3: 生成微服務 API 與契約測試腳本

透過 Haystack RAG Agent，根據步驟 1 的分析報告以及檢索到的知識庫範例，為特定的微服務生成測試腳本。

* **執行指令**：
    ```bash
    python .\rag_migrate.py
    ```


* **操作步驟**：
1. 程式會先載入 Elasticsearch 向量資料庫（若有警告找不到路徑，可先忽略或參考 Step 0 補齊）。
2. 當終端機出現提示字元 `🧑` 時，輸入你想遷移的目標微服務名稱（例如：`visit-service`），然後按下 Enter。
3. 若要結束對話，請輸入 `Q`。


* **預期成果**：
* 執行visit-service後，LLM 會在終端機直接輸出生成好的 **Karate DSL** (`.feature`) 以及 **Pact V3 Contract** (`.json`)。