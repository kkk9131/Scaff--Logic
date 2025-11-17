# 足場図面作図自動化プロジェクト (Scaff-logic)

足場図面の完全自動化を実現するための割付計算ロジックAPI

## 概要

このプロジェクトは、足場図面作図の自動化において、自然言語で説明された計算ロジックをPythonコードに変換し、API化することで、LLMが直接利用可能な形式で提供します。

## プロジェクト目標

1. **割付計算ロジックのAPI化**
   - 自然言語で説明されたロジックをPython等でコード化
   - RESTful APIまたはMCP Serverとして実装
   - LLMが使用可能な形式で提供

2. **自動化の実現**
   - 完全自動での足場図面作図
   - 計算精度の保証
   - 拡張可能なアーキテクチャ

3. **LLM統合**
   - MCP (Model Context Protocol) での提供
   - Tool/Function Calling対応
   - 自然言語インターフェース

## 技術スタック

- **Python 3.11+**: メイン開発言語
- **FastAPI**: REST API実装
- **Pydantic**: データバリデーション
- **MCP Python SDK**: MCP Server実装
- **pytest**: ユニットテスト

## プロジェクト構造

```
Scaff-logic/
├── CLAUDE.md                    # プロジェクト設定
├── README.md                    # このファイル
├── requirements.txt             # Python依存関係
├── .claude/                     # Claude Code設定
│   └── skills/
│       └── scaffold-logic/      # 足場ロジック変換Skill
├── src/                         # ソースコード
│   ├── logic/                   # 計算ロジック
│   │   ├── allocation.py        # 割付計算
│   │   ├── spacing.py           # 間隔計算
│   │   └── validation.py        # 検証ロジック
│   ├── api/                     # API実装
│   │   ├── main.py             # FastAPI メインファイル
│   │   └── routes/             # APIルート
│   └── mcp/                     # MCP Server実装
│       └── server.py           # MCPサーバー
├── tests/                       # テストコード
│   ├── test_logic.py           # ロジックテスト
│   └── test_api.py             # APIテスト
└── docs/                        # ドキュメント
    ├── logic/                   # ロジック説明書
    └── api/                     # API仕様書
```

## セットアップ

### 1. Python環境のセットアップ

```bash
# Python 3.11以上が必要
python3 --version

# 仮想環境の作成
python3 -m venv venv

# 仮想環境の有効化
source venv/bin/activate  # macOS/Linux
# または
venv\Scripts\activate  # Windows

# 依存関係のインストール
pip install -r requirements.txt
```

### 2. 開発環境のセットアップ

```bash
# コードフォーマッターの実行
black src/ tests/

# 型チェックの実行
mypy src/

# リンターの実行
ruff check src/ tests/
```

## 使用方法

### カスタムSkillの使用

このプロジェクトには、自然言語ロジックをPythonコードに変換する専用Skillが含まれています：

```bash
# Claude Code で使用
# 自然言語でロジックを説明すると、自動的にscaffold-logic skillが起動し、
# 構造化されたPythonコードに変換されます
```

### ロジックの実装例

```python
# ユーザーの説明:
# 「スパンの長さを1800mmで割って、余りが出たら1つ追加する。
#  その後、実際のスパン長を分割数で割って均等な間隔を出す」

# 生成されるコード:
from typing import Tuple
import math

def calculate_scaffold_spacing(
    span_length: float,
    standard_spacing: float = 1800.0
) -> Tuple[int, float]:
    """スパン長から足場の均等な割付間隔を計算する"""
    
    # 入力値の検証
    if span_length <= 0:
        raise ValueError(f"スパン長は正の値である必要があります: {span_length}mm")
    if standard_spacing <= 0:
        raise ValueError(f"標準間隔は正の値である必要があります: {standard_spacing}mm")
    
    # 必要な分割数を計算（切り上げ）
    divisions = math.ceil(span_length / standard_spacing)
    
    # 均等な間隔を計算
    spacing = span_length / divisions
    
    return divisions, spacing
```

## テスト

```bash
# すべてのテストを実行
pytest

# カバレッジレポート付きで実行
pytest --cov=src --cov-report=term-missing

# 特定のテストファイルを実行
pytest tests/test_spacing.py -v
```

## API起動（今後実装予定）

```bash
# FastAPI開発サーバーの起動
uvicorn src.api.main:app --reload

# APIドキュメントの確認
# http://localhost:8000/docs
```

## MCP Server起動（今後実装予定）

```bash
# MCP Serverの起動
python src/mcp/server.py
```

## 開発ガイドライン

### コーディング規約

- **言語**: プロジェクト全体は日本語
- **コメント**: 日本語で詳細に記述
- **変数名・関数名**: 英語（国際標準に準拠）
- **型ヒント**: すべての関数に必須
- **docstring**: Google形式で日本語で記述
- **単位**: 明確に記述（mm、m、度など）

### コミット規約

```
feat: 新機能の追加
fix: バグ修正
docs: ドキュメントの変更
test: テストの追加・修正
refactor: リファクタリング
style: フォーマット変更
chore: ビルド・設定の変更
```

## ライセンス

このプロジェクトは私的利用のためのものです。

## 関連リソース

- [MCP公式ドキュメント](https://modelcontextprotocol.io/)
- [FastAPI公式ドキュメント](https://fastapi.tiangolo.com/)
- [Pydantic公式ドキュメント](https://docs.pydantic.dev/)
- [pytest公式ドキュメント](https://docs.pytest.org/)

## サポート

質問や問題がある場合は、GitHubのIssueを作成してください。
# Scaff--Logic
