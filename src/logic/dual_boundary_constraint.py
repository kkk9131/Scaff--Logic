"""
両面境界線制約を考慮した離隔距離計算モジュール

建物の両側に敷地境界線がある場合の足場離隔距離を計算する。
両面の境界線制約を守りながら、必要に応じて足場総長さを縮小する。
"""

import sys
from pathlib import Path
from dataclasses import dataclass

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.logic.spacing import calculate_optimal_clearance


@dataclass
class DualBoundaryResult:
    """
    両面境界線制約計算結果を格納するデータクラス

    Attributes:
        building_dimension: 建物寸法（mm）
        side1_clearance: 片側の離隔距離（mm）
        side2_clearance: 反対側の離隔距離（mm）
        total_scaffold_length: 足場総長さ（mm）
        boundary1: 片側の境界線距離（mm）
        boundary2: 反対側の境界線距離（mm）
        adjusted: 足場総長さを縮小したかどうか
        adjustment_amount: 縮小した寸法（mm）
    """
    building_dimension: float
    side1_clearance: float
    side2_clearance: float
    total_scaffold_length: float
    boundary1: float
    boundary2: float
    adjusted: bool
    adjustment_amount: float


def calculate_clearance_with_dual_boundaries(
    building_dimension: float,
    boundary_distance_side1: float,
    boundary_distance_side2: float,
    target_clearance: float = 900.0,
    safety_margin: float = 60.0,
    span_unit: float = 300.0
) -> DualBoundaryResult:
    """
    両面に境界線がある場合の離隔距離を計算する

    両側の敷地境界線制約を考慮し、必要に応じて足場総長さを縮小して
    両方の制約を満たす離隔距離を算出する。

    計算の流れ:
        1. 通常の離隔距離を計算（境界線なしの場合）
        2. 境界線距離が小さい方の面を優先して制約を適用
        3. ずらした寸法を反対側に振り分け
        4. 反対側も境界線制約を満たすか検証
        5. 満たさない場合、足場総長さを300mm縮小
        6. 新しい総長さで均等に離隔を再計算

    Args:
        building_dimension: 建物寸法（mm）
        boundary_distance_side1: 片側の境界線距離（mm）
            建物外周から境界線までの距離
        boundary_distance_side2: 反対側の境界線距離（mm）
            建物外周から境界線までの距離
        target_clearance: 目標離隔距離（mm、デフォルト900mm）
        safety_margin: 安全マージン（mm、デフォルト60mm）
            境界線までの距離から差し引く余裕
        span_unit: スパン単位（mm、デフォルト300mm）
            足場総長さの調整単位

    Returns:
        DualBoundaryResult: 両面境界線制約を考慮した計算結果

    Example:
        >>> # 建物10000mm、北面900mm境界、南面800mm境界
        >>> result = calculate_clearance_with_dual_boundaries(
        ...     building_dimension=10000.0,
        ...     boundary_distance_side1=900.0,
        ...     boundary_distance_side2=800.0
        ... )
        >>> print(f"片側離隔: {result.side1_clearance}mm")
        片側離隔: 700.0mm
        >>> print(f"反対側離隔: {result.side2_clearance}mm")
        反対側離隔: 700.0mm
        >>> print(f"総長さ: {result.total_scaffold_length}mm")
        総長さ: 11400.0mm
        >>> print(f"縮小: {result.adjusted}")
        縮小: True

    Notes:
        - 境界線距離が小さい方を優先して制約を適用
        - 両方の制約を満たせない場合、足場総長さを300mm単位で縮小
        - 縮小後は均等に離隔を配分
        - 足場総長さは常に300mmの倍数を維持
    """
    # Step 1: 通常の離隔距離を計算（境界線制約なし）
    normal_result = calculate_optimal_clearance(
        building_width=building_dimension,
        target_clearance=target_clearance,
        min_clearance=0.0
    )
    normal_clearance = normal_result.clearance
    original_total_length = normal_result.scaffold_total_length

    # Step 2: 境界線距離が小さい方を優先面として特定
    # 小さい方の境界線制約が厳しいため、先に適用する
    if boundary_distance_side1 <= boundary_distance_side2:
        # side1が優先（小さい）
        priority_boundary = boundary_distance_side1
        opposite_boundary = boundary_distance_side2
        side1_is_priority = True
    else:
        # side2が優先（小さい）
        priority_boundary = boundary_distance_side2
        opposite_boundary = boundary_distance_side1
        side1_is_priority = False

    # Step 3: 優先面に境界線制約を適用
    # 最大離隔 = 境界線距離 - 安全マージン
    max_clearance_priority = priority_boundary - safety_margin
    priority_clearance = min(normal_clearance, max_clearance_priority)

    # Step 4: ずらした寸法を計算
    # 優先面で制約により減らした分
    shift_amount = normal_clearance - priority_clearance

    # Step 5: 反対側に調整を振り分け
    # 優先面で減らした分を反対側に加える
    opposite_clearance = normal_clearance + shift_amount

    # Step 6: 反対側が境界線制約を守っているか検証
    max_clearance_opposite = opposite_boundary - safety_margin

    if opposite_clearance > max_clearance_opposite:
        # 制約違反: 反対側も境界線を超えてしまう
        # Step 7: 足場総長さを300mm縮小
        new_total_length = original_total_length - span_unit
        adjusted = True
        adjustment_amount = span_unit

        # Step 8: 新しい総長さで均等に離隔を再計算
        # 総長さ = 離隔1 + 建物寸法 + 離隔2
        # 両側の離隔合計 = 総長さ - 建物寸法
        total_clearance = new_total_length - building_dimension
        new_clearance = total_clearance / 2

        # 両側とも同じ離隔
        side1_clearance = new_clearance
        side2_clearance = new_clearance
        total_length = new_total_length

    else:
        # 制約OK: 調整された離隔をそのまま使用
        adjusted = False
        adjustment_amount = 0.0

        # 優先面と反対面の離隔を確定
        if side1_is_priority:
            side1_clearance = priority_clearance
            side2_clearance = opposite_clearance
        else:
            side1_clearance = opposite_clearance
            side2_clearance = priority_clearance

        total_length = original_total_length

    return DualBoundaryResult(
        building_dimension=building_dimension,
        side1_clearance=side1_clearance,
        side2_clearance=side2_clearance,
        total_scaffold_length=total_length,
        boundary1=boundary_distance_side1,
        boundary2=boundary_distance_side2,
        adjusted=adjusted,
        adjustment_amount=adjustment_amount
    )


if __name__ == "__main__":
    print("=== 両面境界線制約を考慮した離隔距離計算 ===\n")

    # テスト1: 建物10000mm、北面900mm境界、南面800mm境界
    print("テスト1: 建物10000mm、北面900mm境界、南面800mm境界")
    result1 = calculate_clearance_with_dual_boundaries(
        building_dimension=10000.0,
        boundary_distance_side1=900.0,  # 北面
        boundary_distance_side2=800.0   # 南面
    )

    print(f"  北面境界線: {result1.boundary1}mm")
    print(f"  南面境界線: {result1.boundary2}mm")
    print(f"  北面離隔: {result1.side1_clearance}mm")
    print(f"  南面離隔: {result1.side2_clearance}mm")
    print(f"  足場総長さ: {result1.total_scaffold_length}mm")
    print(f"  総長さ縮小: {result1.adjusted}")
    if result1.adjusted:
        print(f"  縮小量: {result1.adjustment_amount}mm")
    print()

    # 検算
    total = result1.side1_clearance + result1.building_dimension + result1.side2_clearance
    print(f"検算: {result1.side1_clearance} + {result1.building_dimension} + {result1.side2_clearance} = {total}mm")
    print(f"一致: {total == result1.total_scaffold_length}")
    print()

    # テスト2: 境界線に余裕がある場合（縮小不要）
    print("テスト2: 建物10000mm、両面1000mm境界（余裕あり）")
    result2 = calculate_clearance_with_dual_boundaries(
        building_dimension=10000.0,
        boundary_distance_side1=1000.0,
        boundary_distance_side2=1000.0
    )

    print(f"  両面境界線: {result2.boundary1}mm")
    print(f"  side1離隔: {result2.side1_clearance}mm")
    print(f"  side2離隔: {result2.side2_clearance}mm")
    print(f"  足場総長さ: {result2.total_scaffold_length}mm")
    print(f"  総長さ縮小: {result2.adjusted}")
    print()

    # テスト3: 片側のみ厳しい制約
    print("テスト3: 建物10000mm、片側850mm境界、反対側1100mm境界")
    result3 = calculate_clearance_with_dual_boundaries(
        building_dimension=10000.0,
        boundary_distance_side1=850.0,
        boundary_distance_side2=1100.0
    )

    print(f"  side1境界線: {result3.boundary1}mm")
    print(f"  side2境界線: {result3.boundary2}mm")
    print(f"  side1離隔: {result3.side1_clearance}mm")
    print(f"  side2離隔: {result3.side2_clearance}mm")
    print(f"  足場総長さ: {result3.total_scaffold_length}mm")
    print(f"  総長さ縮小: {result3.adjusted}")
