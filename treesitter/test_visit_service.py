import os
import shutil
import zipfile

def setup_docker_sandbox():
    base_dir = os.getcwd()
    
    # 原始檔案路徑
    zip_path = os.path.join(base_dir, "migrate_project", "spring-petclinic-main.zip")
    karate_src = os.path.join(base_dir, "generated_tests", "visit-service", "visit-service_api_test_1.feature")
    pact_src = os.path.join(base_dir, "generated_tests", "visit-service", "visit-service_contract_1.json")
    
    # 目標沙槽路徑
    sandbox_dir = os.path.join(base_dir, "docker_sandbox")
    visit_service_dir = os.path.join(sandbox_dir, "visit-service")
    tests_dir = os.path.join(sandbox_dir, "tests")
    karate_dest_dir = os.path.join(tests_dir, "karate")
    pact_dest_dir = os.path.join(tests_dir, "pact")
    reports_dir = os.path.join(sandbox_dir, "test_reports")
    
    # 1. 建立目錄結構
    print("📂 建立沙槽與報告目錄結構...")
    for d in [visit_service_dir, karate_dest_dir, pact_dest_dir, reports_dir]:
        os.makedirs(d, exist_ok=True)
        
    # 2. 解壓縮 Spring Boot 專案
    print(f"📦 解壓縮後端專案: {zip_path}")
    if os.path.exists(zip_path):
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(sandbox_dir)
            
        extracted_folders = [f for f in os.listdir(sandbox_dir) if os.path.isdir(os.path.join(sandbox_dir, f)) and f not in ["visit-service", "tests", "test_reports"]]
        if extracted_folders:
            inner_folder = os.path.join(sandbox_dir, extracted_folders[0])
            for item in os.listdir(inner_folder):
                shutil.move(os.path.join(inner_folder, item), visit_service_dir)
            os.rmdir(inner_folder)
    else:
        print(f"⚠️ 找不到專案壓縮檔: {zip_path}")

    # 3. 處理 Karate 腳本 (替換 localhost 為 Docker 內部網址)
    print("📝 配置 Karate 測試腳本...")
    if os.path.exists(karate_src):
        with open(karate_src, 'r', encoding='utf-8') as f:
            karate_content = f.read()
        karate_content = karate_content.replace("localhost:8080", "visit-service:8080")
        with open(os.path.join(karate_dest_dir, "visit-service_api_test.feature"), 'w', encoding='utf-8') as f:
            f.write(karate_content)

    # 4. 複製 Pact 腳本
    print("📝 配置 Pact 契約測試...")
    if os.path.exists(pact_src):
        shutil.copy(pact_src, os.path.join(pact_dest_dir, "visit-service_contract.json"))

    # 5. 生成 visit-service 的 Dockerfile
    print("🐳 生成後端 Dockerfile...")
    with open(os.path.join(visit_service_dir, "Dockerfile"), "w", encoding="utf-8") as f:
        f.write("""FROM maven:3.9.4-eclipse-temurin-17 AS builder
WORKDIR /app
COPY pom.xml .
COPY src ./src
RUN mvn clean package -DskipTests

FROM eclipse-temurin:17-jre-alpine
WORKDIR /app
COPY --from=builder /app/target/*.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]
""")

    # 6. 生成 Karate 測試的 Dockerfile
    print("🥋 生成測試環境 Dockerfile.karate...")
    with open(os.path.join(tests_dir, "Dockerfile.karate"), "w", encoding="utf-8") as f:
        f.write("""FROM eclipse-temurin:17-jre-alpine
WORKDIR /usr/src/app
RUN wget https://github.com/karatelabs/karate/releases/download/v1.4.1/karate-1.4.1.jar -O karate.jar
COPY karate/ /usr/src/app/
""")

    # 7. 生成最終版 docker-compose.yml (內建原生輸出導向)
    print("🔗 生成最終版 docker-compose.yml...")
    with open(os.path.join(sandbox_dir, "docker-compose.yml"), "w", encoding="utf-8") as f:
        f.write("""version: '3.8'

services:
  visit-service:
    build: 
      context: ./visit-service
    ports:
      - "8080:8080"
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:8080/"]
      interval: 10s
      timeout: 5s
      retries: 6
      start_period: 30s

  karate-tester:
    build:
      context: ./tests
      dockerfile: Dockerfile.karate
    depends_on:
      visit-service:
        condition: service_healthy
    volumes:
      - ./test_reports:/usr/src/app/target
    command: sh -c "java -jar karate.jar . > /usr/src/app/target/karate_result.txt 2>&1"

  pact-verifier:
    image: pactfoundation/pact-cli:latest
    depends_on:
      visit-service:
        condition: service_healthy
    volumes:
      - ./tests/pact:/app/pact
      - ./test_reports:/app/reports
    entrypoint: ["/bin/sh", "-c"]
    command: "pact verify --provider-base-url http://visit-service:8080 --pact-urls /app/pact/visit-service_contract.json > /app/reports/pact_result.txt 2>&1"
""")

    print(f"\n✅ 測試沙槽建置完畢！")
    print(f"👉 請在終端機輸入: cd docker_sandbox")
    print(f"👉 然後輸入最乾淨的原生指令: docker-compose up --build --abort-on-container-exit")
    print(f"👉 執行完畢後，你的報告跟 .txt 成績單就會自動安安靜靜地躺在 docker_sandbox/test_reports 裡面了！")

if __name__ == "__main__":
    setup_docker_sandbox()