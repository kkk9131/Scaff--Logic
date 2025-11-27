"""
応用スパン寸法に対応した両面境界線制約計算モジュール

両側に敷地境界線がある場合の足場離隔距離計算に、
応用スパン寸法（355mm, 150mm）を適用する。
"""

import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.logic.advanced_spacing import calculate_with_advanced_spans


@dataclass
class AdvancedDualBoundaryResult:
    """
    応用スパン寸法を考慮した両面境界線制約計算結果

    Attributes:
        building_dimension: 建物寸法（mm）
        side1_clearance: 片側の離隔（mm）
        side2_clearance: 反対側の離隔（mm）
        total_scaffold_length: 足場総長さ（mm）
        boundary1: 片側の境界線距離（mm）
        boundary2: 反対側の境界線距離（mm）
        span_355_count: 355mmスパンの使用数
        span_150_count: 150mmスパンの使用数
        adjusted: 足場総長さを調整したか
        adjusted_by_advanced_spans: 応用スパンを使用したか
    """
    building_dimension: float
    side1_clearance: float
    side2_clearance: float
    total_scaffold_length: float
    boundary1: float
    boundary2: float
    span_355_count: int
    span_150_count: int
    adjusted: bool
    adjusted_by_advanced_spans: bool


def calculate_with_dual_boundaries_and_advanced_spans(
    building_dimension: float,
    boundary_distance_side1: float,
    boundary_distance_side2: float,
    target_clearance: float = 900.0,
    safety_margin: float = 60.0,
    adjacent_clearances: Optional[List[float]] = None
) -> AdvancedDualBoundaryResult:
    """
    両面境界線制約と応用スパン寸法を考慮した離隔距離計算

    両側の境界線制約を満たすため、応用スパン寸法を活用して
    より柔軟な調整を行う。

    Args:
        building_dimension: 建物寸法（mm）
        boundary_distance_side1: 片側の境界線距離（mm）
        boundary_distance_side2: 反対側の境界線距離（mm）
        target_clearance: 目標離隔（mm、デフォルト900mm）
        safety_margin: 安全マージン（mm、デフォルト60mm）
        adjacent_clearances: 隣接edgeの離隔値リスト（mm）

    Returns:
        AdvancedDualBoundaryResult: 応用スパンを考慮した計算結果
    """
    # 両面の最大許容離隔
    max_clearance_1 = boundary_distance_side1 - safety_margin
    max_clearance_2 = boundary_distance_side2 - safety_margin

    # より厳しい制約を使用
    max_clearance = min(max_clearance_1, max_clearance_2)

    # 応用スパンを使用した計算
    adv_result = calculate_with_advanced_spans(
        building_dimension=building_dimension,
        target_clearance=target_clearance,
        min_clearance=0.0,
        max_clearance=max_clearance,
        adjacent_clearances=adjacent_clearances
    )

    # 両面の境界線制約を適用
    # 小さい方を優先
    if boundary_distance_side1 <= boundary_distance_side2:
        priority_clearance = min(adv_result.clearance, max_clearance_1)
        shift = adv_result.clearance - priority_clearance
        opposite_clearance = adv_result.clearance + shift

        # 反対側も制約チェック
        if opposite_clearance > max_clearance_2:
            # 両方の制約を満たせない → 均等配分
            new_clearance = (adv_result.total_scaffold_length - building_dimension) / 2
            side1_clearance = new_clearance
            side2_clearance = new_clearance
            adjusted = True
        else:
            side1_clearance = priority_clearance
            side2_clearance = opposite_clearance
            adjusted = False
    else:
        priority_clearance = min(adv_result.clearance, max_clearance_2)
        shift = adv_result.clearance - priority_clearance
        opposite_clearance = adv_result.clearance + shift

        # 反対側も制約チェック
        if opposite_clearance > max_clearance_1:
            # 両方の制約を満たせない → 均等配分
            new_clearance = (adv_result.total_scaffold_length - building_dimension) / 2
            side1_clearance = new_clearance
            side2_clearance = new_clearance
            adjusted = True
        else:
            side1_clearance = opposite_clearance
            side2_clearance = priority_clearance
            adjusted = False

    return AdvancedDualBoundaryResult(
        building_dimension=building_dimension,
        side1_clearance=side1_clearance,
        side2_clearance=side2_clearance,
        total_scaffold_length=adv_result.total_scaffold_length,
        boundary1=boundary_distance_side1,
        boundary2=boundary_distance_side2,
        span_355_count=adv_result.span_355_count,
        span_150_count=adv_result.span_150_count,
        adjusted=adjusted,
        adjusted_by_advanced_spans=(
            adv_result.span_355_count > 0 or adv_result.span_150_count > 0
        )
    )


if __name__ == "__main__":
    print("=== 応用スパン寸法 + 両面境界線制約計算 ===\n")

    # テスト: 北面900mm、南面800mm境界
    print("テスト: 建物10000mm、北面900mm境界、南面800mm境界")
    result = calculate_with_dual_boundaries_and_advanced_spans(
        building_dimension=10000.0,
        boundary_distance_side1=900.0,
        boundary_distance_side2=800.0
    )
    print(f"  side1離隔: {result.side1_clearance}mm")
    print(f"  side2離隔: {result.side2_clearance}mm")
    print(f"  総長: {result.total_scaffold_length}mm")
    print(f"  355mm使用: {result.span_355_count}個")
    print(f"  150mm使用: {result.span_150_count}個")
    print(f"  応用スパン使用: {result.adjusted_by_advanced_spans}")
    print(f"  調整済み: {result.adjusted}")
    print()

    # 検算
    total = result.side1_clearance + result.building_dimension + result.side2_clearance
    print(f"検算: {result.side1_clearance} + {result.building_dimension} + "
          f"{result.side2_clearance} = {total}mm")
    print(f"一致: {total == result.total_scaffold_length}")
