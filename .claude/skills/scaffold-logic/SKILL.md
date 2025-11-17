---
name: scaffold-logic
description: 足場計算の自然言語ロジックをPythonコードに変換する専用スキル。ユーザーが日本語で足場の割付計算、間隔計算、検証ロジックなどを説明した際に、それを構造化された型安全なPythonコード（詳細な日本語コメント付き）に変換する。API化やMCP統合を前提とした実装を行う。
---

# 足場ロジック変換スキル (Scaffold Logic Converter)

## 概要

このスキルは、足場図面作図の自動化において、自然言語で説明された計算ロジックを高品質なPythonコードに変換する。ユーザーが日本語で「スパンの長さを1800mmで割って...」のように説明したロジックを、型ヒント・バリデーション・詳細な日本語コメント付きのコードに自動変換する。

## ワークフロー決定木

ユーザーの入力内容に応じて、適切なワークフローを選択する：

```
ユーザー入力を受け取る
    │
    ├─ 新しいロジックの説明？
    │   └─> [フェーズ1: 自然言語ロジック解析]
    │       └─> [フェーズ2: 計算式への変換]
    │           └─> [フェーズ3: Pythonコード生成]
    │               └─> [フェーズ4: 検証とテスト]
    │
    ├─ 既存コードの修正依頼？
    │   └─> [修正ワークフロー]
    │
    └─ API/MCP統合の依頼？
        └─> [統合ワークフロー]
```

---

## フェーズ1: 自然言語ロジック解析

### 目的
ユーザーの日本語説明から、計算ロジックの構造を抽出・整理する

### 手順

#### 1.1 ロジックの受け取りと確認
ユーザーが説明するロジックを受け取り、以下を確認：

```
✅ チェックリスト:
□ 入力値は何か？（スパン長、階高、間隔など）
□ 出力値は何か？（分割数、間隔、配置位置など）
□ 単位は明確か？（mm、m、度など）
□ 計算ステップは明確か？
□ 条件分岐はあるか？
□ エッジケース（境界値）は想定されているか？
```

#### 1.2 ロジックの構造化

自然言語を以下の形式に構造化：

**例：ユーザー入力**
```
「スパンの長さを1800mmで割って、余りが出たら1つ追加する。
その後、実際のスパン長を分割数で割って均等な間隔を出す」
```

**構造化後**
```yaml
目的: スパン長から均等な足場間隔を計算

入力:
  - span_length: float (スパンの長さ、mm)
  - standard_spacing: float (標準間隔、デフォルト1800mm)

計算ステップ:
  1. 分割数の算出:
     - 計算式: span_length ÷ standard_spacing
     - 処理: 小数点以下切り上げ (ceil)

  2. 均等間隔の算出:
     - 計算式: span_length ÷ 分割数
     - 処理: 実数値として保持

出力:
  - divisions: int (分割数)
  - spacing: float (均等間隔、mm)

エッジケース:
  - span_length = 0 → エラー
  - span_length < 0 → エラー
  - span_length < standard_spacing → divisions = 1
```

#### 1.3 曖昧点の明確化

構造化中に曖昧な点があれば、ユーザーに質問：

**質問例**:
- 「スパン長が0または負の値の場合、エラーにしますか？」
- 「間隔の最小値・最大値の制約はありますか？」
- 「計算結果は小数点以下何桁まで必要ですか？」

---

## フェーズ2: 計算式への変換

### 目的
構造化されたロジックを数学的表現と疑似コードに変換

### 手順

#### 2.1 数学的表現の記述

各計算ステップを数式で表現：

```
分割数の算出:
  divisions = ⌈span_length / standard_spacing⌉

均等間隔の算出:
  spacing = span_length / divisions
```

記号の意味:
- `⌈x⌉`: 天井関数（切り上げ）
- `⌊x⌋`: 床関数（切り捨て）
- `round(x)`: 四捨五入

#### 2.2 制約条件の定式化

入力値の制約を明確にする：

```
制約条件:
  - span_length > 0
  - standard_spacing > 0
  - span_length / standard_spacing < 1000 (現実的な上限)
```

#### 2.3 疑似コード作成

Pythonに近い形式の疑似コードを作成：

```python
関数名: calculate_scaffold_spacing

入力:
  - span_length: 正の実数（mm）
  - standard_spacing: 正の実数（mm、デフォルト1800）

処理:
  1. 入力値検証:
     もし span_length <= 0 ならエラー
     もし standard_spacing <= 0 ならエラー

  2. 分割数計算:
     divisions = ceil(span_length / standard_spacing)

  3. 均等間隔計算:
     spacing = span_length / divisions

出力:
  - divisions: 整数
  - spacing: 実数（mm）
```

---

## フェーズ3: Pythonコード生成

### 目的
疑似コードから本番品質のPythonコードを生成

### コーディング規約

以下の規約に必ず従う：

#### 3.1 関数定義のテンプレート

```python
from typing import Tuple
import math

def calculate_scaffold_spacing(
    span_length: float,
    standard_spacing: float = 1800.0
) -> Tuple[int, float]:
    """
    スパン長から足場の均等な割付間隔を計算する

    この関数は、与えられたスパン長を標準間隔で分割し、
    均等な足場の配置間隔を算出する。建築基準法および
    労働安全衛生規則に準拠した計算を行う。

    Args:
        span_length: スパンの長さ（mm）
            - 正の実数値を指定
            - 通常は建物の柱間距離
        standard_spacing: 標準の足場間隔（mm、デフォルト1800mm）
            - 一般的な足場の最大許容間隔
            - 労働安全衛生規則に基づく

    Returns:
        Tuple[int, float]: 以下の2要素を含むタプル
            - divisions (int): 必要な分割数
            - spacing (float): 均等な間隔（mm）

    Raises:
        ValueError: span_lengthまたはstandard_spacingが0以下の場合

    Example:
        >>> divisions, spacing = calculate_scaffold_spacing(5400.0)
        >>> print(f"分割数: {divisions}, 間隔: {spacing}mm")
        分割数: 3, 間隔: 1800.0mm

        >>> divisions, spacing = calculate_scaffold_spacing(5500.0)
        >>> print(f"分割数: {divisions}, 間隔: {spacing}mm")
        分割数: 4, 間隔: 1375.0mm

    Notes:
        - 計算結果の間隔は、必ず標準間隔以下になる
        - 余りが出る場合は分割数を増やして均等化する
        - 浮動小数点演算による誤差に注意
    """
    # 入力値の検証
    if span_length <= 0:
        raise ValueError(
            f"スパン長は正の値である必要があります: {span_length}mm"
        )
    if standard_spacing <= 0:
        raise ValueError(
            f"標準間隔は正の値である必要があります: {standard_spacing}mm"
        )

    # 必要な分割数を計算（切り上げ）
    # 例: 5400mm ÷ 1800mm = 3.0 → 3分割
    #     5500mm ÷ 1800mm = 3.055... → 4分割
    divisions = math.ceil(span_length / standard_spacing)

    # 均等な間隔を計算
    # 分割数で等分することで、標準間隔以下の均等な間隔を得る
    spacing = span_length / divisions

    return divisions, spacing
```

#### 3.2 コメント記述ルール

**必須コメント**:
1. **関数docstring**: Google形式で詳細に記述（日本語）
2. **計算ロジック**: 各計算の意図と具体例
3. **条件分岐**: なぜその条件が必要か
4. **エッジケース**: 境界値での動作

**コメントの質を高めるポイント**:
```python
# ❌ 悪い例
# 割り算する
result = a / b

# ✅ 良い例
# スパン長を分割数で割り、均等な間隔を算出
# 例: 5400mm ÷ 3 = 1800mm（標準間隔と同じ）
#     5500mm ÷ 4 = 1375mm（標準間隔より小さい均等間隔）
spacing = span_length / divisions
```

#### 3.3 型ヒントの徹底

すべての関数・メソッドに型ヒントを付与：

```python
from typing import List, Tuple, Dict, Optional, Union
from decimal import Decimal

# ✅ 型ヒント付き
def calculate_positions(
    start: float,
    end: float,
    spacing: float
) -> List[float]:
    """開始位置から終了位置までの配置座標を計算"""
    positions: List[float] = []
    current = start
    while current <= end:
        positions.append(current)
        current += spacing
    return positions

# ❌ 型ヒントなし（避ける）
def calculate_positions(start, end, spacing):
    positions = []
    # ...
```

#### 3.4 バリデーション実装

Pydanticを使った入力バリデーション：

```python
from pydantic import BaseModel, Field, validator

class ScaffoldSpacingInput(BaseModel):
    """足場間隔計算の入力パラメータ"""

    span_length: float = Field(
        ...,
        gt=0,
        description="スパンの長さ（mm）"
    )
    standard_spacing: float = Field(
        default=1800.0,
        gt=0,
        le=3000.0,
        description="標準間隔（mm）"
    )

    @validator('span_length')
    def validate_span_length(cls, v):
        """スパン長の妥当性を検証"""
        if v > 100000:  # 100m以上は非現実的
            raise ValueError(
                f"スパン長が大きすぎます: {v}mm（上限: 100000mm）"
            )
        return v

    class Config:
        # 設定例を提供
        schema_extra = {
            "example": {
                "span_length": 5400.0,
                "standard_spacing": 1800.0
            }
        }
```

---

## フェーズ4: 検証とテスト

### 目的
生成したコードの正確性と堅牢性を確認

### 手順

#### 4.1 ユニットテストの生成

pytest形式のテストコードを自動生成：

```python
import pytest
import math
from decimal import Decimal

def test_calculate_scaffold_spacing_normal_case():
    """正常系: 標準的なスパン長でのテスト"""
    # 5400mm（1800mmで割り切れる）
    divisions, spacing = calculate_scaffold_spacing(5400.0)
    assert divisions == 3
    assert spacing == 1800.0

def test_calculate_scaffold_spacing_with_remainder():
    """正常系: 余りが出るケース"""
    # 5500mm（1800mmで割ると余りが出る）
    divisions, spacing = calculate_scaffold_spacing(5500.0)
    assert divisions == 4  # 切り上げで4分割
    assert spacing == pytest.approx(1375.0)  # 5500/4

def test_calculate_scaffold_spacing_small_span():
    """エッジケース: 標準間隔より小さいスパン"""
    # 1000mm（標準間隔1800mmより小さい）
    divisions, spacing = calculate_scaffold_spacing(1000.0)
    assert divisions == 1
    assert spacing == 1000.0

def test_calculate_scaffold_spacing_zero_span():
    """異常系: スパン長が0"""
    with pytest.raises(ValueError) as exc_info:
        calculate_scaffold_spacing(0.0)
    assert "正の値である必要があります" in str(exc_info.value)

def test_calculate_scaffold_spacing_negative_span():
    """異常系: スパン長が負の値"""
    with pytest.raises(ValueError):
        calculate_scaffold_spacing(-100.0)

def test_calculate_scaffold_spacing_custom_standard():
    """正常系: カスタム標準間隔"""
    divisions, spacing = calculate_scaffold_spacing(
        span_length=6000.0,
        standard_spacing=2000.0
    )
    assert divisions == 3
    assert spacing == 2000.0

def test_calculate_scaffold_spacing_precision():
    """正確性: 浮動小数点演算の精度確認"""
    # 割り切れない値での精度テスト
    divisions, spacing = calculate_scaffold_spacing(5555.5)

    # 再構築して元の値と一致するか確認
    reconstructed = divisions * spacing
    assert reconstructed == pytest.approx(5555.5, rel=1e-9)
```

#### 4.2 テストカテゴリ

生成するテストは以下のカテゴリを網羅：

```yaml
正常系テスト:
  - 標準的な入力値
  - 境界値（最小・最大）
  - 割り切れる値
  - 割り切れない値

異常系テスト:
  - 0や負の値
  - 極端に大きい値
  - 型が異なる入力（文字列など）

エッジケーステスト:
  - 浮動小数点の精度限界
  - 標準間隔より小さいスパン
  - 丸め誤差の影響
```

#### 4.3 実行と検証

テストを実行して結果を確認：

```bash
# テスト実行
pytest tests/test_spacing.py -v

# カバレッジ確認
pytest tests/test_spacing.py --cov=src.logic --cov-report=term-missing
```

#### 4.4 ロジック検証チェックリスト

```
検証項目:
✅ 入力値のバリデーション
✅ 計算ロジックの正確性
✅ エッジケースの処理
✅ エラーメッセージの明確性（日本語）
✅ 型ヒントの正確性
✅ docstringの完全性
✅ コメントの分かりやすさ
✅ テストカバレッジ（80%以上）
✅ 実行速度（パフォーマンス）
```

---

## API化ワークフロー

### 目的
生成したロジックをFastAPIでRESTful APIとして公開

### 手順

#### 1. FastAPIエンドポイント作成

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Tuple

app = FastAPI(
    title="足場計算API",
    description="足場図面作図のための各種計算API",
    version="1.0.0"
)

class ScaffoldSpacingRequest(BaseModel):
    """足場間隔計算のリクエスト"""
    span_length: float = Field(
        ...,
        gt=0,
        description="スパンの長さ（mm）",
        example=5400.0
    )
    standard_spacing: float = Field(
        default=1800.0,
        gt=0,
        description="標準間隔（mm）",
        example=1800.0
    )

class ScaffoldSpacingResponse(BaseModel):
    """足場間隔計算のレスポンス"""
    divisions: int = Field(
        ...,
        description="分割数"
    )
    spacing: float = Field(
        ...,
        description="均等な間隔（mm）"
    )
    calculation_notes: str = Field(
        ...,
        description="計算の根拠"
    )

@app.post(
    "/api/v1/scaffold/spacing",
    response_model=ScaffoldSpacingResponse,
    summary="足場間隔計算",
    description="スパン長から最適な足場の配置間隔を計算"
)
async def calculate_spacing(
    request: ScaffoldSpacingRequest
) -> ScaffoldSpacingResponse:
    """
    足場の均等な配置間隔を計算するAPI

    建築基準法および労働安全衛生規則に準拠した計算を行い、
    安全で効率的な足場配置を提案します。
    """
    try:
        # ロジック実行
        divisions, spacing = calculate_scaffold_spacing(
            span_length=request.span_length,
            standard_spacing=request.standard_spacing
        )

        # 計算根拠の説明文を生成
        notes = (
            f"スパン長 {request.span_length}mm を "
            f"標準間隔 {request.standard_spacing}mm で分割。"
            f"切り上げにより {divisions} 分割とし、"
            f"均等間隔 {spacing:.2f}mm を算出。"
        )

        return ScaffoldSpacingResponse(
            divisions=divisions,
            spacing=spacing,
            calculation_notes=notes
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"入力値エラー: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"計算エラー: {str(e)}"
        )
```

---

## MCP統合ワークフロー

### 目的
ロジックをMCP Serverとして実装し、LLMが直接利用可能にする

### 手順

#### 1. MCP Server実装

```python
from mcp import FastMCP
from pydantic import BaseModel, Field

# MCPサーバー初期化
mcp = FastMCP("足場計算サーバー")

class SpacingInput(BaseModel):
    """足場間隔計算の入力"""
    span_length: float = Field(
        description="スパンの長さ（mm）。正の実数値を指定。"
    )
    standard_spacing: float = Field(
        default=1800.0,
        description="標準間隔（mm）。デフォルトは1800mm。"
    )

@mcp.tool(
    description=(
        "スパン長から足場の最適な配置間隔を計算します。"
        "建築基準法および労働安全衛生規則に準拠した計算を行います。"
    )
)
def calculate_scaffold_spacing_tool(
    input_data: SpacingInput
) -> dict:
    """
    足場間隔計算ツール

    LLMがこのツールを呼び出すことで、足場の最適な配置間隔を
    自動計算できます。
    """
    try:
        divisions, spacing = calculate_scaffold_spacing(
            span_length=input_data.span_length,
            standard_spacing=input_data.standard_spacing
        )

        return {
            "success": True,
            "divisions": divisions,
            "spacing": spacing,
            "unit": "mm",
            "explanation": (
                f"スパン長{input_data.span_length}mmを"
                f"{divisions}分割し、"
                f"均等間隔{spacing:.2f}mmで配置します。"
            )
        }

    except ValueError as e:
        return {
            "success": False,
            "error": str(e),
            "suggestion": "入力値を確認してください。"
        }

if __name__ == "__main__":
    # MCPサーバー起動
    mcp.run()
```

---

## リファレンス

### scripts/
このディレクトリには、ロジック実装をサポートするユーティリティスクリプトを配置

**使用例**:
- `validate_logic.py`: ロジックの数学的妥当性を検証
- `generate_tests.py`: テストケースの自動生成
- `benchmark.py`: パフォーマンス測定

### references/
詳細な技術仕様やガイドラインを配置

**使用例**:
- `calculation_standards.md`: 建築基準法に基づく計算基準
- `safety_regulations.md`: 労働安全衛生規則の要件
- `api_design.md`: API設計ガイドライン

### assets/
必要に応じてテンプレートやサンプルデータを配置

---

## まとめ

このスキルは以下のワークフローで動作：

1. **解析**: 自然言語ロジックを構造化
2. **変換**: 計算式と疑似コードに変換
3. **生成**: 本番品質のPythonコード生成
4. **検証**: テストと品質確認
5. **統合**: API/MCP化

各フェーズで品質を確保し、将来の保守性を重視した実装を行う。
