from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path


WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_KARATE_DIR = WORKSPACE_ROOT / "treesitter/karate_feature"
DEFAULT_PACT_DIR = WORKSPACE_ROOT / "treesitter/pact_contract"
DEFAULT_FALLBACK_PACT_DIR = WORKSPACE_ROOT / "docker_sandbox_mock/tests/pact"
DEFAULT_OUTPUT = WORKSPACE_ROOT / "docker_sandbox_mock"


def provider_for_feature(feature: Path) -> str:
    stem = re.sub(r"_api_test(?:_\d+)?$", "", feature.stem)
    if stem == "spring-petclinic-main":
        return "pet-service"
    return stem


def normalize_feature(path: Path) -> str:
    text = path.read_text(encoding="utf-8-sig")
    block = re.search(r"```(?:gherkin|karate|feature)\s*\n(.*?)\n```", text, re.DOTALL | re.IGNORECASE)
    if block:
        text = block.group(1)
    else:
        feature_start = text.find("Feature:")
        if feature_start >= 0:
            text = text[feature_start:]
        text = re.sub(r"\s*```\s*$", "", text)

    if not re.search(r"^Feature:\s*", text, re.MULTILINE):
        raise ValueError(f"Karate file does not contain a Feature declaration: {path}")
    return text.rstrip() + "\n"


def rewrite_karate_urls(text: str, provider: str) -> str:
    stub_host = f"http://{provider}-stub:8080"
    return re.sub(
        r"https?://(?:localhost|127\.0\.0\.1|[A-Za-z0-9.-]+)(?::\d+)?",
        stub_host,
        text,
        flags=re.IGNORECASE,
    )


def load_pact(path: Path) -> str:
    text = path.read_text(encoding="utf-8-sig")
    lines = text.splitlines()
    while lines and re.match(r"^\s*(//|#)", lines[0]):
        lines.pop(0)
    try:
        pact = json.loads("\n".join(lines))
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid Pact JSON: {path}: {error}") from error
    if not pact.get("provider", {}).get("name"):
        raise ValueError(f"Pact has no provider name: {path}")
    return json.dumps(pact, indent=2, ensure_ascii=False) + "\n"


def interaction_count(path: Path) -> int:
    text = path.read_text(encoding="utf-8-sig")
    lines = text.splitlines()
    while lines and re.match(r"^\s*(//|#)", lines[0]):
        lines.pop(0)
    return len(json.loads("\n".join(lines)).get("interactions", []))


def find_pact(provider: str, pact_dir: Path, fallback_dir: Path) -> Path:
    candidates = sorted(pact_dir.glob(f"{provider}_contract*.json"))
    candidates.extend(sorted(fallback_dir.glob(f"{provider}_contract*.json")))
    if not candidates:
        raise FileNotFoundError(
            f"No Pact contract found for provider '{provider}'. "
            f"Checked {pact_dir} and {fallback_dir}."
        )
    return max(candidates, key=interaction_count)


def dockerfile_karate() -> str:
    return """FROM maven:3.9.6-eclipse-temurin-21-jammy
WORKDIR /usr/src/app

RUN wget https://github.com/karatelabs/karate/releases/download/v1.4.1/karate-1.4.1.jar -O karate.jar
RUN echo \"function fn() { return {}; }\" > karate-config.js

COPY karate/ /usr/src/app/
"""


def compose_file(providers: list[str], pact_files: list[str]) -> str:
    lines = ["services:"]
    for provider, pact_file in zip(providers, pact_files):
        service = f"{provider}-stub"
        lines.extend(
            [
                f"  {service}:",
                "    image: pactfoundation/pact-stub-server:latest",
                "    volumes:",
                f"      - ./tests/pact/{pact_file}:/app/pacts/{pact_file}:ro",
                '    command: ["-p", "8080", "-d", "/app/pacts"]',
                "",
            ]
        )

    lines.extend(
        [
            "  karate-runner:",
            "    build:",
            "      context: ./tests",
            "      dockerfile: Dockerfile.karate",
            "    depends_on:",
        ]
    )
    for provider in providers:
        lines.extend(
            [
                f"      {provider}-stub:",
                "        condition: service_started",
            ]
        )
    lines.extend(
        [
            "    volumes:",
            "      - ./test_reports/karate:/usr/src/app/target",
            "    command: >",
            "      bash -c \"",
            "      echo '=== Karate Pact mock tests started ===' > /usr/src/app/target/karate_console.txt &&",
            "      java -jar karate.jar . >> /usr/src/app/target/karate_console.txt 2>&1",
            "      \"",
            "",
        ]
    )
    return "\n".join(lines)


def generate(
    karate_dir: Path,
    pact_dir: Path,
    fallback_pact_dir: Path,
    output: Path,
    clean: bool,
) -> None:
    karate_dir = karate_dir.resolve()
    pact_dir = pact_dir.resolve()
    fallback_pact_dir = fallback_pact_dir.resolve()
    output = output.resolve()

    features = sorted(karate_dir.glob("*.feature"))
    if not features:
        raise FileNotFoundError(f"No .feature files found in {karate_dir}")

    feature_providers = [provider_for_feature(feature) for feature in features]
    providers = list(dict.fromkeys(feature_providers))

    pact_sources = [find_pact(provider, pact_dir, fallback_pact_dir) for provider in providers]
    pact_contents = [load_pact(path) for path in pact_sources]

    if output.exists() and clean:
        shutil.rmtree(output)
    elif output.exists() and any(output.iterdir()):
        raise FileExistsError(
            f"Output directory is not empty: {output}. Use --clean to replace it."
        )

    karate_output = output / "tests/karate"
    pact_output = output / "tests/pact"
    report_output = output / "test_reports/karate"
    karate_output.mkdir(parents=True, exist_ok=True)
    pact_output.mkdir(parents=True, exist_ok=True)
    report_output.mkdir(parents=True, exist_ok=True)

    for feature, provider in zip(features, feature_providers):
        content = rewrite_karate_urls(normalize_feature(feature), provider)
        (karate_output / feature.name).write_text(content, encoding="utf-8")

    pact_names = []
    for source, content in zip(pact_sources, pact_contents):
        pact_name = source.name
        pact_names.append(pact_name)
        (pact_output / pact_name).write_text(content, encoding="utf-8")

    (output / "tests/Dockerfile.karate").write_text(dockerfile_karate(), encoding="utf-8")
    (output / "docker-compose.yml").write_text(
        compose_file(providers, pact_names), encoding="utf-8"
    )
    (output / ".gitignore").write_text("test_reports/\n", encoding="utf-8")

    print(f"Generated Docker mock sandbox: {output}")
    print(f"Karate features: {len(features)}")
    print(f"Pact providers: {', '.join(providers)}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a Pact stub-server and Karate-runner Docker mock sandbox."
    )
    parser.add_argument("--karate-dir", type=Path, default=DEFAULT_KARATE_DIR)
    parser.add_argument("--pact-dir", type=Path, default=DEFAULT_PACT_DIR)
    parser.add_argument("--fallback-pact-dir", type=Path, default=DEFAULT_FALLBACK_PACT_DIR)
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
        arguments.karate_dir,
        arguments.pact_dir,
        arguments.fallback_pact_dir,
        arguments.output,
        arguments.clean,
    )
