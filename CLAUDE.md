# 足場図面作図自動化プロジェクト

## プロジェクト概要

足場図面の作図を完全自動化するため、割付計算ロジックをAPI化し、将来的にLLMがMCPまたはToolとして使用できる形で実装する。

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

## 開発方針

### 言語設定
- **プロジェクト言語**: 日本語
- **コード内コメント**: 日本語で詳細に記述
- **ドキュメント**: 日本語で作成
- **変数名・関数名**: 英語（国際標準に準拠）
- **コメントスタイル**: 将来の保守性を考慮した詳細な日本語説明

### 開発フロー

```
自然言語でのロジック説明
    ↓
ロジック分析・構造化
    ↓
計算式への変換
    ↓
Pythonコード実装
    ↓
API化（FastAPI/MCP）
    ↓
テスト・検証
    ↓
LLM統合（MCPまたはTool）
```

### コーディング規約

**コメント記述ルール**:
```python
# ❌ 悪い例
def calc(x, y):
    return x + y

# ✅ 良い例
def calculate_scaffold_spacing(span_length: float, max_spacing: float) -> float:
    """
    スパン長に基づいて足場の割付間隔を計算する

    Args:
        span_length: スパンの長さ（mm）
        max_spacing: 最大許容間隔（mm）

    Returns:
        最適な割付間隔（mm）

    計算ロジック:
        1. スパン長を最大間隔で割り、必要な分割数を算出
        2. 分割数を切り上げて均等な間隔を計算
        3. 安全係数を考慮した最終間隔を返す
    """
    # スパン長から必要な分割数を計算（切り上げ）
    divisions = math.ceil(span_length / max_spacing)

    # 均等な間隔を計算
    optimal_spacing = span_length / divisions

    return optimal_spacing
```

## プロジェクト構造

```
Scaff-logic/
├── CLAUDE.md                    # このファイル（プロジェクト設定）
├── .claude/                     # Claude Code設定
│   └── skills/                  # カスタムSkills
│       ├── scaffold-logic/      # 足場ロジック変換Skill
│       └── mcp-builder/         # MCP作成Skill
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
├── docs/                        # ドキュメント
│   ├── logic/                   # ロジック説明書
│   └── api/                     # API仕様書
└── requirements.txt             # Python依存関係
```

## 使用技術スタック

### バックエンド
- **Python 3.11+**: メイン開発言語
- **FastAPI**: REST API実装
- **Pydantic**: データバリデーション
- **MCP Python SDK**: MCP Server実装

### テスト・品質管理
- **pytest**: ユニットテスト
- **black**: コードフォーマッター
- **mypy**: 型チェック

### ドキュメント
- **Markdown**: ドキュメント記述
- **docstring**: コード内ドキュメント（日本語）

## カスタムSkill: scaffold-logic

### 目的
自然言語で説明された足場計算ロジックを、構造化されたPythonコードに変換する専用Skill

### 機能
1. **自然言語ロジックの解析**
   - 日本語での説明を受け取り
   - 計算ステップを抽出
   - 依存関係を特定

2. **計算式への変換**
   - 数学的表現への変換
   - エッジケースの特定
   - 制約条件の明確化

3. **Pythonコード生成**
   - 型ヒント付き関数定義
   - 詳細な日本語コメント
   - テストケースの生成

4. **検証**
   - ロジックの正確性確認
   - エッジケースのテスト
   - パフォーマンス確認

### ワークフロー例

```
入力: "スパンの長さを1800mmで割って、余りが出たら1つ追加する"

↓ 解析

ステップ1: スパン長 ÷ 1800mm
ステップ2: 余りの確認
ステップ3: 余りがある場合は分割数+1

↓ 計算式化

divisions = ceil(span_length / 1800)

↓ コード生成

def calculate_divisions(span_length: float, standard_spacing: float = 1800.0) -> int:
    """
    スパン長に基づいて必要な分割数を計算

    Args:
        span_length: スパンの長さ（mm）
        standard_spacing: 標準間隔（mm、デフォルト1800mm）

    Returns:
        必要な分割数
    """
    # スパン長を標準間隔で割り、切り上げて分割数を算出
    divisions = math.ceil(span_length / standard_spacing)
    return divisions
```

## 知識・ロジックの記録方針

### ドキュメント化ルール

ユーザーが説明する内容で今後も使用する可能性がある情報は、**即座にドキュメント化**する。

#### 記録すべき内容
1. **計算ロジック**: 足場の割付・配置・検証に関する計算方法
2. **業界知識**: 建築基準法、労働安全衛生規則、業界慣習
3. **実務ノウハウ**: 現場での実践的な判断基準やコツ
4. **用語定義**: 専門用語や略語の意味
5. **エッジケース**: 特殊な状況での処理方法
6. **制約条件**: 物理的・法的・実務的な制約

#### 記録場所と形式

```yaml
計算ロジック:
  場所: docs/logic/[分類名].md
  形式: Markdown（数式・図表含む）
  例: docs/logic/spacing_calculation.md

業界知識・規則:
  場所: .claude/skills/scaffold-logic/references/
  形式: Markdown（参照しやすい構造）
  例: references/construction_standards.md

実装済みコード:
  場所: src/logic/[機能名].py
  形式: Python（詳細な日本語コメント）
  例: src/logic/allocation.py

用語集:
  場所: docs/glossary.md
  形式: Markdown（アルファベット順）
```

#### ドキュメント更新フロー

```
ユーザーが新しい知識・ロジックを説明
    ↓
該当する既存ドキュメントを確認
    ↓
    ├─ 既存ドキュメントがある → 内容を追記・更新
    └─ 新規トピック → 新しいドキュメントを作成
    ↓
関連ドキュメントへのリンクを追加
    ↓
CLAUDE.mdの「記録済み知識一覧」を更新
```

### 記録済み知識一覧

現在記録されている知識・ドキュメント：

#### 計算基準
- ✅ `references/calculation_standards.md`: 建築基準法に基づく基本的な計算基準
  - 標準間隔: 1800mm
  - 割付計算の基本ルール
  - 制約条件

#### 実装予定のロジック
- ⏳ スパン割付計算
- ⏳ 階高計算
- ⏳ 端部処理ロジック
- ⏳ 干渉チェック
- ⏳ 強度計算

---

## 開発ガイドライン

### 1. ロジック実装時の注意点
- 単位を明確にする（mm、m、度など）
- 浮動小数点演算の精度を考慮
- エッジケース（0、負の数、極端に大きい値）を処理
- 日本の建築基準法・労働安全衛生規則に準拠

### 2. API設計原則
- RESTful設計
- バリデーション必須
- エラーメッセージは日本語で明確に
- レスポンスに計算根拠を含める

### 3. MCP統合
- ツール名は英語（例: `calculate_scaffold_spacing`）
- 説明文は日本語と英語の両方を提供
- 入力スキーマは厳格に定義
- エラーハンドリングを充実

## 次のステップ

1. ✅ CLAUDE.mdの作成（ドキュメント化方針を含む）
2. ✅ scaffold-logic Skillの作成
3. ✅ プロジェクト構造の整備
4. ✅ 用語集テンプレートの作成
5. ⏳ 最初の計算ロジックの実装（ユーザーからのロジック説明待ち）
6. ⏳ API基盤の構築
7. ⏳ MCP Server実装
8. ⏳ テスト・検証

## 関連リソース

- [MCP公式ドキュメント](https://modelcontextprotocol.io/)
- [FastAPI公式ドキュメント](https://fastapi.tiangolo.com/)
- [Pydantic公式ドキュメント](https://docs.pydantic.dev/)
