# Repository Guidelines

## 言語設定
- **プロジェクト言語**: 日本語
- **コード内コメント**: 日本語で詳細に記述
- **ドキュメント**: 日本語で作成
- **変数名・関数名**: 英語（国際標準に準拠）
- **コメントスタイル**: 将来の保守性を考慮した詳細な日本語説明

## Project Structure & Module Organization
- `src/logic/`: core calculation modules (allocation, inside_corner, spacing, stair, concave, protrusion/shed/balcony). Keep new logic here and export via `__all__` when reused.
- `tests/`: pytest suites (currently `test_shed_building.py`, `test_shed_with_inside_corner.py`). Mirror module names with `test_<module>.py`.
- `docs/`: calculation notes and glossary; update when logic changes to keep formulas in sync.
- Root files: `requirements.txt` (locked), `README.md` (overview), `CLAUDE.md` (agent settings). Avoid cache files in `src/logic/__pycache__/`.

## Build, Test, and Development Commands
```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt        # install pinned deps
python -m pytest                       # run all tests
python -m pytest tests/test_shed_building.py -k normal  # narrow focus
black src/ tests/                      # format
ruff check src/ tests/                 # lint
mypy src/                              # type check (optional but encouraged)
```
Python 3.11+. Run pytest + ruff + black before PR.

## Coding Style & Naming Conventions
- Language: code identifiers in English; comments/docstrings in Japanese to explain domain logic.
- Formatting: `black` defaults; no manual alignment. Lint with `ruff` and fix obvious warnings before commit.
- Types: add type hints to public functions and dataclasses; prefer `float` for mm units and document expected units.
- Naming: snake_case for functions/variables, PascalCase for dataclasses. File names match the shape/algorithm they implement.

## Testing Guidelines
- Framework: `pytest`. Name files `test_<module>.py`; name test functions with behavior (`test_invalid_width`, `test_symmetry`).
- Coverage: hit critical branches (validation errors, geometry splits). Use `pytest --cov=src --cov-report=term-missing` when adding modules.
- Determinism: avoid random inputs; use exact mm values used in docs for reproducibility.

## Commit & Pull Request Guidelines
- Commits: follow conventional prefixes (`feat`, `fix`, `docs`, `test`, `refactor`, `style`, `chore`). Keep messages in Japanese when describing domain behavior.
- Pull Requests: include what changed, why, and how to verify (commands run). Link related issues/tasks; attach logs or short output snippets for test runs. If UI/diagram changes land later, include screenshots or sample JSON I/O.

## Security & Configuration Tips (Optional but Helpful)
- Do not commit `.env` or credentials; this repo currently needs none. If adding APIs, read values via environment variables and document them in `README.md`.
- Keep numeric constants (e.g., span unit 300mm, default clearance 900mm) centralized in each module.
