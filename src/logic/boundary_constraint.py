"""
敷地境界線制約を考慮した離隔距離計算モジュール

敷地境界線がある場合、境界線までの距離から安全マージン60mmを引いた値を
最大離隔距離とし、ずらした寸法を反対側で調整する。
"""

from dataclasses import dataclass
from typing import Optional
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.logic.spacing import calculate_optimal_clearance


@dataclass
class BoundaryAdjustedClearance:
    """
    境界線制約を考慮した離隔距離の計算結果

    Attributes:
        boundary_side_clearance: 境界線側の離隔距離（mm）
        opposite_side_clearance: 反対側の離隔距離（mm）
        scaffold_total_length: 足場総長さ（mm）
        adjustment: ずらした寸法（mm）
        boundary_distance: 境界線までの距離（mm）
        max_clearance: 最大許容離隔距離（mm）= 境界線距離 - 60mm
    """
    boundary_side_clearance: float
    opposite_side_clearance: float
    scaffold_total_length: float
    adjustment: float
    boundary_distance: float
    max_clearance: float


def calculate_clearance_with_boundary(
    building_dimension: float,
    boundary_distance: float,
    target_clearance: float = 900.0,
    safety_margin: float = 60.0
) -> BoundaryAdjustedClearance:
    """
    敷地境界線制約を考慮した離隔距離を計算する

    敷地境界線がある場合、境界線までの距離から安全マージンを引いた値を
    最大離隔距離とし、通常の離隔距離との差分を反対側で調整する。
    足場総長さは変わらない。

    Args:
        building_dimension: 建物寸法（mm）
        boundary_distance: 建物から境界線までの距離（mm）
        target_clearance: 目標離隔距離（mm）。デフォルトは900mm
        safety_margin: 境界線からの安全マージン（mm）。デフォルトは60mm

    Returns:
        BoundaryAdjustedClearance: 境界線制約を考慮した計算結果

    計算ロジック:
        1. 通常の離隔距離を計算
           - 目標離隔距離に最も近い値を選択
        2. 最大許容離隔距離を計算
           - 最大離隔 = 境界線距離 - 安全マージン（60mm）
        3. 境界線側の離隔を調整
           - 通常離隔 > 最大離隔の場合、最大離隔に制限
        4. ずらした寸法を計算
           - ずらした寸法 = 通常離隔 - 境界線側離隔
        5. 反対側の離隔を調整
           - 反対側離隔 = 通常離隔 + ずらした寸法
        6. 足場総長さは維持される
           - 総長さ = 境界線側離隔 + 建物寸法 + 反対側離隔

    Example:
        >>> # 建物10000mm、北面に境界線900mm
        >>> result = calculate_clearance_with_boundary(10000, 900)
        >>> result.boundary_side_clearance
        840.0
        >>> result.opposite_side_clearance
        860.0
        >>> result.adjustment
        10.0

    Notes:
        - 境界線制約により、境界線側の離隔が通常より小さくなる
        - ずらした寸法を反対側に加算することで、足場総長さを維持
        - 安全マージン60mmは境界線を超えないための余裕
    """
    # Step 1: 通常の離隔距離を計算
    result = calculate_optimal_clearance(
        building_width=building_dimension,
        target_clearance=target_clearance
    )

    normal_clearance = result.clearance  # 通常の離隔距離（例: 850mm）
    scaffold_total_length = result.scaffold_total_length  # 足場総長さ（例: 11700mm）

    # Step 2: 最大許容離隔距離を計算
    # 境界線までの距離から安全マージン（60mm）を引く
    max_clearance = boundary_distance - safety_margin  # 例: 900 - 60 = 840mm

    # Step 3: 境界線側の離隔を調整
    # 通常の離隔が最大許容離隔を超える場合、最大許容離隔に制限
    boundary_side_clearance = min(normal_clearance, max_clearance)
    # 例: min(850, 840) = 840mm

    # Step 4: ずらした寸法を計算
    # 通常の離隔との差分が、ずらした寸法
    adjustment = normal_clearance - boundary_side_clearance
    # 例: 850 - 840 = 10mm

    # Step 5: 反対側の離隔を調整
    # ずらした寸法を反対側に加算することで、足場総長さを維持
    opposite_side_clearance = normal_clearance + adjustment
    # 例: 850 + 10 = 860mm

    # 検証: 足場総長さが変わらないことを確認
    # boundary_side_clearance + building_dimension + opposite_side_clearance
    # = 840 + 10000 + 860 = 11700mm ✓

    return BoundaryAdjustedClearance(
        boundary_side_clearance=boundary_side_clearance,
        opposite_side_clearance=opposite_side_clearance,
        scaffold_total_length=scaffold_total_length,
        adjustment=adjustment,
        boundary_distance=boundary_distance,
        max_clearance=max_clearance
    )


if __name__ == "__main__":
    # テスト実行
    print("=== 敷地境界線制約を考慮した離隔距離計算 ===\n")

    # テストケース1: 建物10000mm、北面に境界線900mm
    print("テスト1: 建物10000mm、北面に境界線900mm")
    result1 = calculate_clearance_with_boundary(
        building_dimension=10000,
        boundary_distance=900
    )
    print(f"  通常の離隔: 850mm（計算値）")
    print(f"  境界線までの距離: {result1.boundary_distance}mm")
    print(f"  最大許容離隔: {result1.max_clearance}mm（= {result1.boundary_distance} - 60）")
    print(f"  境界線側の離隔: {result1.boundary_side_clearance}mm")
    print(f"  ずらした寸法: {result1.adjustment}mm")
    print(f"  反対側の離隔: {result1.opposite_side_clearance}mm（= 850 + {result1.adjustment}）")
    print(f"  足場総長さ: {result1.scaffold_total_length}mm")
    print()

    # 検算
    calculated_total = (result1.boundary_side_clearance +
                        10000 +
                        result1.opposite_side_clearance)
    print(f"検算: {result1.boundary_side_clearance} + 10000 + "
          f"{result1.opposite_side_clearance} = {calculated_total}mm")
    print(f"一致: {calculated_total == result1.scaffold_total_length}\n")

    # テストケース2: 建物7000mm、境界線800mm
    print("テスト2: 建物7000mm、境界線800mm")
    result2 = calculate_clearance_with_boundary(
        building_dimension=7000,
        boundary_distance=800
    )
    print(f"  境界線側の離隔: {result2.boundary_side_clearance}mm")
    print(f"  反対側の離隔: {result2.opposite_side_clearance}mm")
    print(f"  ずらした寸法: {result2.adjustment}mm")
    print(f"  足場総長さ: {result2.scaffold_total_length}mm")
