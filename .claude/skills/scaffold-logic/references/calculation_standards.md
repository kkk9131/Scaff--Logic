# 足場計算基準

## 建築基準法に基づく計算基準

このドキュメントは、足場図面作図における計算ロジックの基準を定義します。

### 1. 基本単位

すべての計算において、以下の単位系を使用します：

- **長さ**: ミリメートル (mm)
- **角度**: 度 (degree)
- **荷重**: キロニュートン (kN)

### 2. 標準寸法

#### 2.1 足場の基本間隔

- **標準間隔**: 1800mm（最も一般的）
- **許容範囲**: 1500mm - 2000mm
- **最小間隔**: 900mm（特殊な場合）
- **最大間隔**: 2400mm（一般的な上限）

#### 2.2 階高

- **標準階高**: 3000mm - 4000mm
- **一般的な値**: 3300mm, 3600mm, 4000mm

### 3. 割付計算ルール

#### 3.1 均等分割の原則

スパンを均等に分割する際は、以下の原則に従います：

1. **切り上げ原則**: 分割数は常に切り上げ
   - 例: 5500mm ÷ 1800mm = 3.055... → 4分割

2. **均等化**: 分割後の間隔は均等に配分
   - 例: 5500mm ÷ 4 = 1375mm（各間隔）

3. **安全係数**: 計算結果は標準間隔以下に抑える

#### 3.2 端部処理

- **開始端**: 通常は建物の端から開始
- **終了端**: 最後の間隔が極端に短い場合は調整が必要
- **最小端部間隔**: 300mm以上を確保

### 4. 制約条件

#### 4.1 構造上の制約

```yaml
スパン長:
  最小値: 1000mm
  最大値: 100000mm (100m)
  理由: 現実的な建物のスパン範囲

間隔:
  最小値: 900mm
  最大値: 2400mm
  推奨値: 1800mm
  理由: 労働安全衛生規則に基づく

分割数:
  最小値: 1
  最大値: 1000
  理由: 計算の実用範囲
```

#### 4.2 安全基準

労働安全衛生規則に基づく要件：

- 作業床の幅: 400mm以上
- 手すりの高さ: 850mm以上
- 中桟の設置: 350mm以上450mm以下の位置
- 足場の最大高さ: 45m（それ以上は特別な設計が必要）

### 5. 計算式

#### 5.1 基本的な割付計算

```python
# 分割数の計算
divisions = ceil(span_length / standard_spacing)

# 均等間隔の計算
spacing = span_length / divisions

# 検証
assert spacing <= standard_spacing, "間隔が標準を超えています"
assert spacing >= minimum_spacing, "間隔が最小値未満です"
```

#### 5.2 端部調整を含む計算

```python
# 端部の余裕を考慮
effective_span = span_length - 2 * end_margin

# 内部の分割数を計算
internal_divisions = ceil(effective_span / standard_spacing)

# 内部の均等間隔
internal_spacing = effective_span / internal_divisions

# 全体の配置
positions = [
    end_margin,  # 開始端
    *[end_margin + i * internal_spacing for i in range(1, internal_divisions)],
    span_length - end_margin  # 終了端
]
```

### 6. エラー処理

#### 6.1 入力値の検証

すべての入力値は以下を満たす必要があります：

```python
# スパン長
if not (1000 <= span_length <= 100000):
    raise ValueError(f"スパン長が範囲外です: {span_length}mm")

# 標準間隔
if not (900 <= standard_spacing <= 2400):
    raise ValueError(f"標準間隔が範囲外です: {standard_spacing}mm")
```

#### 6.2 計算結果の検証

計算結果は以下を満たす必要があります：

```python
# 間隔の検証
if spacing < 900:
    raise ValueError(f"計算された間隔が最小値未満です: {spacing}mm")

if spacing > standard_spacing:
    raise ValueError(f"計算された間隔が標準を超えています: {spacing}mm")
```

### 7. 参考文献

- 建築基準法施行令
- 労働安全衛生規則（足場関連）
- 建築工事標準仕様書
- 足場の組立て等作業主任者技能講習テキスト

### 8. 更新履歴

- 2025-01-15: 初版作成
