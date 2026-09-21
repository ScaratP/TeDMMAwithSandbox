from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path


WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE = WORKSPACE_ROOT / "treesitter/temp_project_source/spring-petclinic-main"
DEFAULT_KARATE = (
    WORKSPACE_ROOT
    / "treesitter/generated_tests/visit-service/visit-service_api_test_1.feature"
)
DEFAULT_PACT = (
    WORKSPACE_ROOT
    / "treesitter/generated_tests/visit-service/visit-service_contract_1.json"
)
DEFAULT_OUTPUT = WORKSPACE_ROOT / "docker_sandbox"


def resolve_project_root(source: Path) -> Path:
    source = source.resolve()
    if not source.is_dir():
        raise FileNotFoundError(f"Source directory does not exist: {source}")

    if (source / "pom.xml").is_file():
        return source

    candidates = [path.parent for path in source.rglob("pom.xml")]
    if len(candidates) != 1:
        names = ", ".join(str(path) for path in candidates) or "none"
        raise ValueError(
            "Expected exactly one pom.xml below the source directory; "
            f"found {len(candidates)} ({names})"
        )
    return candidates[0]


def clean_json_header(path: Path) -> str:
    text = path.read_text(encoding="utf-8-sig")
    lines = text.splitlines()
    while lines and re.match(r"^\s*(//|#)", lines[0]):
        lines.pop(0)
    json.loads("\n".join(lines))
    return "\n".join(lines) + "\n"


def rewrite_karate_url(path: Path) -> str:
    text = path.read_text(encoding="utf-8-sig")
    rewritten = re.sub(
        r"https?://(?:localhost|127\.0\.0\.1)(?::\d+)?",
        "http://visit-service:8080",
        text,
        flags=re.IGNORECASE,
    )
    if rewritten == text and "visit-service:8080" not in text:
        raise ValueError(
            f"Could not find a localhost URL to rewrite in Karate file: {path}"
        )
    return rewritten


def dockerfile_backend() -> str:
    return """FROM maven:3.9.4-eclipse-temurin-17 AS builder
WORKDIR /app
COPY pom.xml .
COPY src ./src
RUN mvn clean package -DskipTests

FROM eclipse-temurin:17-jre-alpine
RUN apk add --no-cache netcat-openbsd
WORKDIR /app
COPY --from=builder /app/target/*.jar app.jar
EXPOSE 8080
ENTRYPOINT [\"java\", \"-jar\", \"app.jar\"]
"""


def dockerfile_karate() -> str:
    return """FROM eclipse-temurin:17-jre
WORKDIR /usr/src/app

RUN wget https://github.com/karatelabs/karate/releases/download/v1.4.1/karate-1.4.1.jar -O karate.jar
RUN echo \"function fn() { return {}; }\" > karate-config.js

COPY karate/ /usr/src/app/
"""


def compose_file(karate_name: str, pact_name: str, has_env: bool) -> str:
    env_file = "    env_file:\n      - ./visit-service/.env\n" if has_env else ""
    return f"""services:
  visit-service:
    build:
      context: ./visit-service
{env_file}    ports:
    - \"8081:8080\"
    healthcheck:
      test: [\"CMD\", \"nc\", \"-z\", \"localhost\", \"8080\"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 20s

  karate-tester:
    build:
      context: ./tests
      dockerfile: Dockerfile.karate
    depends_on:
      visit-service:
        condition: service_healthy
    volumes:
      - ./test_reports/karate:/usr/src/app/target
    command: >
      bash -c \"
      echo '=== Karate tests started ===' > /usr/src/app/target/karate_console.txt &&
      java -jar karate.jar {karate_name} >> /usr/src/app/target/karate_console.txt 2>&1
      \"

  pact-verifier:
    image: pactfoundation/pact-cli:latest
    depends_on:
      visit-service:
        condition: service_healthy
    volumes:
      - ./tests/pact:/app/pact
      - ./test_reports/pact:/app/reports
    entrypoint: [\"/bin/sh\", \"-c\"]
    command: >
      \"pact verify
      --provider-base-url http://visit-service:8080
      --pact-urls /app/pact/{pact_name} > /app/reports/pact_console.txt 2>&1\"
"""


def copy_source(project_root: Path, destination: Path) -> None:
    (destination / "src").mkdir(parents=True)
    shutil.copytree(project_root / "src", destination / "src", dirs_exist_ok=True)
    pom_text = (project_root / "pom.xml").read_text(encoding="utf-8")
    pom_text = re.sub(
        r"(<java\.version>)(\d+)(</java\.version>)",
        lambda match: f"{match.group(1)}17{match.group(3)}"
        if int(match.group(2)) > 17
        else match.group(0),
        pom_text,
    )
    (destination / "pom.xml").write_text(pom_text, encoding="utf-8")
    env_file = project_root / ".env"
    if env_file.is_file():
        shutil.copy2(env_file, destination / ".env")


def generate(source: Path, karate: Path, pact: Path, output: Path, clean: bool) -> None:
    source = source.resolve()
    karate = karate.resolve()
    pact = pact.resolve()
    output = output.resolve()

    for path in (karate, pact):
        if not path.is_file():
            raise FileNotFoundError(f"Test file does not exist: {path}")

    project_root = resolve_project_root(source)
    has_env = (project_root / ".env").is_file()
    if output.exists() and clean:
        shutil.rmtree(output)
    elif output.exists() and any(output.iterdir()):
        raise FileExistsError(
            f"Output directory is not empty: {output}. Use --clean to replace it."
        )

    service_dir = output / "visit-service"
    tests_dir = output / "tests"
    reports_dir = output / "test_reports"
    (tests_dir / "karate").mkdir(parents=True, exist_ok=True)
    (tests_dir / "pact").mkdir(parents=True, exist_ok=True)
    (reports_dir / "karate").mkdir(parents=True, exist_ok=True)
    (reports_dir / "pact").mkdir(parents=True, exist_ok=True)

    copy_source(project_root, service_dir)
    karate_name = karate.name
    pact_name = pact.name
    (tests_dir / "karate" / karate_name).write_text(
        rewrite_karate_url(karate), encoding="utf-8"
    )
    (tests_dir / "pact" / pact_name).write_text(
        clean_json_header(pact), encoding="utf-8"
    )
    (service_dir / "Dockerfile").write_text(dockerfile_backend(), encoding="utf-8")
    (tests_dir / "Dockerfile.karate").write_text(
        dockerfile_karate(), encoding="utf-8"
    )
    (output / "docker-compose.yml").write_text(
        compose_file(karate_name, pact_name, has_env), encoding="utf-8"
    )
    (output / ".gitignore").write_text(".env\ntest_reports/\n", encoding="utf-8")

    print(f"Generated Docker sandbox: {output}")
    print(f"Backend project: {project_root}")
    print(f"Karate test: {karate_name}")
    print(f"Pact contract: {pact_name}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a Docker sandbox for Karate and Pact tests."
    )
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--karate", type=Path, default=DEFAULT_KARATE)
    parser.add_argument("--pact", type=Path, default=DEFAULT_PACT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Replace an existing output directory.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    generate(
        arguments.source,
        arguments.karate,
        arguments.pact,
        arguments.output,
        arguments.clean,
    )