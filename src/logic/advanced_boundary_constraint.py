"""
応用スパン寸法に対応した片側境界線制約計算モジュール

片側に敷地境界線がある場合の足場離隔距離計算に、
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
from src.logic.boundary_constraint import calculate_clearance_with_boundary


@dataclass
class AdvancedBoundaryResult:
    """
    応用スパン寸法を考慮した境界線制約計算結果

    Attributes:
        building_dimension: 建物寸法（mm）
        boundary_side_clearance: 境界線側の離隔（mm）
        opposite_side_clearance: 反対側の離隔（mm）
        total_scaffold_length: 足場総長さ（mm）
        boundary_distance: 境界線距離（mm）
        span_355_count: 355mmスパンの使用数
        span_150_count: 150mmスパンの使用数
        adjustment_amount: 調整量（mm）
        adjusted_by_advanced_spans: 応用スパンを使用したか
    """
    building_dimension: float
    boundary_side_clearance: float
    opposite_side_clearance: float
    total_scaffold_length: float
    boundary_distance: float
    span_355_count: int
    span_150_count: int
    adjustment_amount: float
    adjusted_by_advanced_spans: bool


def calculate_with_boundary_and_advanced_spans(
    building_dimension: float,
    boundary_distance: float,
    target_clearance: float = 900.0,
    safety_margin: float = 60.0,
    adjacent_clearances: Optional[List[float]] = None
) -> AdvancedBoundaryResult:
    """
    境界線制約と応用スパン寸法を考慮した離隔距離計算

    片側に境界線がある場合、応用スパン寸法を使用することで
    より柔軟に制約を満たすことが可能になる。

    Args:
        building_dimension: 建物寸法（mm）
        boundary_distance: 境界線までの距離（mm）
        target_clearance: 目標離隔（mm、デフォルト900mm）
        safety_margin: 安全マージン（mm、デフォルト60mm）
        adjacent_clearances: 隣接edgeの離隔値リスト（mm）

    Returns:
        AdvancedBoundaryResult: 応用スパンを考慮した計算結果
    """
    # 最大許容離隔
    max_clearance = boundary_distance - safety_margin

    # 応用スパンを使用した計算
    adv_result = calculate_with_advanced_spans(
        building_dimension=building_dimension,
        target_clearance=target_clearance,
        min_clearance=0.0,
        max_clearance=max_clearance,
        adjacent_clearances=adjacent_clearances
    )

    # 境界線側の制約適用と反対側への調整
    boundary_side = min(adv_result.clearance, max_clearance)
    shift = adv_result.clearance - boundary_side
    opposite_side = adv_result.clearance + shift

    return AdvancedBoundaryResult(
        building_dimension=building_dimension,
        boundary_side_clearance=boundary_side,
        opposite_side_clearance=opposite_side,
        total_scaffold_length=adv_result.total_scaffold_length,
        boundary_distance=boundary_distance,
        span_355_count=adv_result.span_355_count,
        span_150_count=adv_result.span_150_count,
        adjustment_amount=adv_result.adjustment_amount,
        adjusted_by_advanced_spans=(
            adv_result.span_355_count > 0 or adv_result.span_150_count > 0
        )
    )


if __name__ == "__main__":
    print("=== 応用スパン寸法 + 境界線制約計算 ===\n")

    # テスト: 境界線900mm
    print("テスト: 建物10000mm、境界線900mm")
    result = calculate_with_boundary_and_advanced_spans(
        building_dimension=10000.0,
        boundary_distance=900.0
    )
    print(f"  境界線側: {result.boundary_side_clearance}mm")
    print(f"  反対側: {result.opposite_side_clearance}mm")
    print(f"  総長: {result.total_scaffold_length}mm")
    print(f"  355mm使用: {result.span_355_count}個")
    print(f"  150mm使用: {result.span_150_count}個")
    print(f"  応用スパン使用: {result.adjusted_by_advanced_spans}")
    print()

    # 検算
    total = (result.boundary_side_clearance + result.building_dimension +
             result.opposite_side_clearance)
    print(f"検算: {result.boundary_side_clearance} + {result.building_dimension} + "
          f"{result.opposite_side_clearance} = {total}mm")
    print(f"一致: {total == result.total_scaffold_length}")
