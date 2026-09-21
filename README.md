# TeDMMA

TeDMMA 是一套將單體 Java/Spring Boot 專案分析成微服務測試素材的工具。系統會讀取 Java 原始碼與既有測試，透過 Tree-sitter、RAG 與 LLM 產生微服務 API 測試，並使用 Karate 與 Pact 在 Docker sandbox 中驗證服務行為。

## 系統流程

```text
Java 原始碼
    |
    v
Tree-sitter 分析 -> 單體特徵、測試案例、LLM 架構分析
    |
    v
RAG + LLM -> Karate feature、Pact contract
    |
    v
Docker sandbox -> 啟動 Spring Boot、執行 Karate/Pact、輸出報告
```

## 專案結構

### 根目錄

| 路徑 | 用途 |
|---|---|
| `step.md` | 舊版操作步驟與整體流程說明。 |
| `.venv/` | Python 虛擬環境，放置本專案 Python 套件。 |
| `.vscode/` | VS Code 工作區設定。 |
| `docker_sandbox/` | 目前使用的 Docker 測試環境。由生成器產生或供手動調整。 |
| `docker_sandbox_00/` | 舊版或備份用 Docker sandbox，通常不作為主要入口。 |
| `treesitter/` | 主要 Python 程式、分析結果、知識庫與生成測試。 |

### `treesitter/` 程式檔案

| 檔案 | 用途 |
|---|---|
| `generate_docker_sandbox.py` | 自動複製 Java 專案、Karate、Pact，並產生完整 Docker sandbox。 |
| `main.py` | 讀取 Java 專案並執行 Tree-sitter 特徵擷取與單體分析流程。 |
| `rag_migrate.py` | 使用 RAG/LLM 根據分析結果生成指定微服務的測試腳本。 |
| `feature_capture.py` | 擷取 Java 專案中的特徵與結構資訊。 |
| `api_test_generate.py` | 產生 API 測試相關內容。 |
| `text_processor.py` | 處理、整理與切分文字資料。 |
| `prettify_sexp.py` | 將 Tree-sitter S-expression 整理成較易讀格式。 |
| `test_ast_capture.py` | AST 擷取相關測試。 |
| `test_visit_service.py` | visit-service 相關測試。 |
| `api_key.txt` | LLM API key。屬於敏感資料，不應提交到版本控制。 |

### `treesitter/` 輸入、知識庫與輸出

| 路徑 | 用途 |
|---|---|
| `temp_project_source/` | 放置待分析的 Java/Spring Boot 原始專案。 |
| `generated_tests/` | LLM 或其他流程產生的 Karate/Pact 測試與測試結果。 |
| `karate_feature/` | Karate 測試腳本相關素材。 |
| `rag_knowledge_base/karate/` | Karate 範例知識庫，供 RAG 檢索。 |
| `rag_knowledge_base/pact/` | Pact 範例知識庫，供 RAG 檢索。 |
| `monolith_features/` | 單體專案擷取出的元件、欄位與結構特徵。 |
| `monolith_test_case_codes/` | 單體專案既有測試程式碼。 |
| `llm_analysis_result/` | LLM 產生的微服務拆分與架構分析結果。 |
| `expected_microservice_endpoint/` | 預期微服務 API endpoint 定義。 |
| `migrate_project/` | 遷移流程使用的專案資料。 |
| `tree-sitter-venv/` | Tree-sitter 專用 Python 虛擬環境。 |

### 目前測試輸入

| 路徑 | 用途 |
|---|---|
| `treesitter/temp_project_source/spring-petclinic-main/` | 目前的 Java 專案來源；實際 Maven 專案位於其下的 `keelungsights-java-main/`。 |
| `treesitter/generated_tests/visit-service/visit-service_api_test_1.feature` | visit-service 的 Karate API 測試。 |
| `treesitter/generated_tests/visit-service/visit-service_contract_1.json` | visit-service 的 Pact V3 合約。 |

## Docker sandbox 結構

執行生成器後，預期會產生：

```text
docker_sandbox/
├── visit-service/
│   ├── src/                 # Spring Boot 原始碼
│   ├── pom.xml              # Maven 設定
│   ├── .env                 # 可選，MongoDB 等環境變數，不應提交
│   └── Dockerfile           # 建置 Spring Boot 映像
├── tests/
│   ├── karate/              # Karate feature 檔案
│   ├── pact/                # Pact JSON 合約
│   └── Dockerfile.karate    # Karate 執行環境
├── test_reports/
│   ├── karate/              # Karate console、HTML 與 JSON 報告
│   └── pact/                # Pact console 報告
├── docker-compose.yml       # 啟動服務與測試容器
└── .gitignore               # 忽略 .env 與 test_reports/
```

## 環境需求

- Windows PowerShell
- Python 3
- Docker Desktop 與 Docker Compose
- Maven/Java 不必安裝在主機上，後端建置使用 Docker image
- 若執行分析與 RAG 流程，需要 Python 虛擬環境及有效的 LLM API key
- 若 Spring Boot 使用 MongoDB，需準備有效的 `MONGODB_URI`、`MONGODB_USERNAME` 與 `MONGODB_PASSWORD`

## 快速使用

### 1. 啟用 Python 虛擬環境

在專案根目錄執行：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

若使用 Tree-sitter 專用環境：

```powershell
.\treesitter\tree-sitter-venv\Scripts\Activate.ps1
```

### 2. 產生單體分析結果

```powershell
cd .\treesitter
python .\main.py
```

常見輸出：

- `monolith_features/*_features.txt`
- `monolith_test_case_codes/*_test_cases.txt`
- `llm_analysis_result/*_analysis_response.txt`
- API 測試 feature 檔案

### 3. 產生微服務測試

```powershell
python .\rag_migrate.py
```

依照終端機提示輸入微服務名稱，例如 `visit-service`。產物通常會放在：

```text
generated_tests/<service-name>/
├── <service>_api_test_*.feature
└── <service>_contract_*.json
```

輸入 `Q` 可結束互動流程。

### 4. 生成 Docker 測試 sandbox

可從任何目前工作目錄執行，預設會使用本 README 所列的來源：

```powershell
cd <專案根目錄>
python .\treesitter\generate_docker_sandbox.py --clean
```

生成器會自動：

1. 找到來源目錄下真正包含 `pom.xml` 的 Maven 專案。
2. 複製 `src/`、`pom.xml` 與可選的 `.env`。
3. 複製 Karate 與 Pact 檔案，並依實際檔名更新 compose 指令。
4. 將 Karate 中的 `localhost` 或 `127.0.0.1` 改成 `http://visit-service:8080`。
5. 移除 Pact JSON 開頭的 `//` 或 `#` 註解後驗證 JSON 格式。
6. 產生兩個 Dockerfile、`docker-compose.yml` 與 `.gitignore`。

### 5. 使用不同來源檔案

```powershell
python .\treesitter\generate_docker_sandbox.py `
  --source .\treesitter\temp_project_source\another-project `
  --karate .\treesitter\generated_tests\another-api.feature `
  --pact .\treesitter\generated_tests\another-contract.json `
  --output .\docker_sandbox `
  --clean
```

`--clean` 會刪除並重建輸出目錄；不使用它時，若輸出目錄不是空的，程式會停止以避免意外覆蓋檔案。

### 6. 建置並執行測試

```powershell
cd .\docker_sandbox
docker compose up --build --abort-on-container-exit
```

若主機的 8080 已被其他程式使用，這份 sandbox 預設將主機的 `8081` 對應到容器的 `8080`：

```text
主機：http://localhost:8081
容器內：http://visit-service:8080
```

## 執行結果

### 成功啟動時

- `visit-service` 容器啟動 Spring Boot。
- Docker healthcheck 使用 `nc` 檢查 8080 port 是否開啟，不依賴 HTTP 200。
- Karate tester 連線到 `http://visit-service:8080`。
- Pact verifier 連線到同一個容器名稱與 port。
- 測試輸出會寫入 `test_reports/`，不只顯示在終端機。

### 報告位置

| 報告 | 路徑 | 說明 |
|---|---|---|
| Karate console | `docker_sandbox/test_reports/karate/karate_console.txt` | Karate 執行紀錄與錯誤。 |
| Karate HTML | `docker_sandbox/test_reports/karate/karate-reports*/karate-summary.html` | Karate 網頁報告。 |
| Karate JSON/Log | `docker_sandbox/test_reports/karate/` | 測試明細與執行 log。 |
| Pact console | `docker_sandbox/test_reports/pact/pact_console.txt` | Pact 合約比對結果。 |

也可以單獨產生完整 Karate HTML 報告：

```powershell
docker compose up -d visit-service
docker compose run --rm karate-tester
docker compose down
```

## 測試失敗時怎麼看

1. 先開啟 `test_reports/karate/karate_console.txt` 與 `test_reports/pact/pact_console.txt`。
2. 若服務未達健康狀態，先執行：

   ```powershell
   docker compose ps -a
   docker compose logs visit-service
   ```

3. 若看到 `404`，通常代表目標服務尚未實作測試要求的 endpoint，例如 `/sights`。
4. 若看到 MongoDB connection string 錯誤，檢查 `visit-service/.env` 是否存在，以及 `MONGODB_URI` 是否以 `mongodb://` 或 `mongodb+srv://` 開頭。
5. 若看到 port bind 錯誤，確認主機 8081 是否也被占用，再調整 compose 的主機端 port。

## 安全注意事項

- 不要提交 `treesitter/api_key.txt`。
- 不要提交 `docker_sandbox/visit-service/.env`。
- 不要把 MongoDB 帳號密碼貼到公開 issue、README 或測試報告。
- `test_reports/` 是執行產物，通常不需要提交。

## 常用清理指令

```powershell
cd .\docker_sandbox
docker compose down
```

移除測試容器、網路與 volume：

```powershell
docker compose down --volumes --remove-orphans
```

## 目前限制

- Pact provider state 目前沒有連接 provider-state setup API，因此 Pact 會略過 state 的自動資料準備；測試資料必須已存在於後端資料庫，或由服務啟動流程準備。
- `docker compose up --abort-on-container-exit` 在某個測試容器先結束時會停止其他測試容器；若需要完整 Karate HTML 報告，請依上方方式單獨執行 Karate。
- 測試是否通過取決於目前 Java Controller、MongoDB 資料與生成的 Karate/Pact 合約是否一致。
