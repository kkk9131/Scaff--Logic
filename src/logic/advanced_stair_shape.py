"""
応用スパン寸法に対応した階段形状（連続入隅）計算モジュール

階段形状の建物（連続した入隅）の計算に、応用スパン寸法（355mm, 150mm）で
決定された足場総長さを使用する。
"""

import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.logic.advanced_spacing import calculate_with_advanced_spans
from src.logic.inside_corner import calculate_inside_corner_edge


@dataclass
class AdvancedStairShapeResult:
    """
    応用スパン寸法を考慮した階段形状計算結果

    Attributes:
        outer_edge_clearance: 外周edge離隔（mm）
        inner_edges_clearances: 内側edges離隔のリスト（mm）
        inner_edges_scaffolds: 内側edges足場長のリスト（mm）
        span_355_count: 355mmスパンの使用数
        span_150_count: 150mmスパンの使用数
        adjusted_by_advanced_spans: 応用スパンを使用したか
    """
    outer_edge_clearance: float
    inner_edges_clearances: List[float]
    inner_edges_scaffolds: List[float]
    span_355_count: int
    span_150_count: int
    adjusted_by_advanced_spans: bool


def calculate_stair_shape_with_advanced_spans(
    outer_edge_dimension: float,
    perpendicular_edge_lengths: List[float],
    target_clearance: float = 900.0,
    adjacent_clearances: Optional[List[float]] = None,
    min_clearance: Optional[float] = None,
    max_clearance: Optional[float] = None
) -> AdvancedStairShapeResult:
    """
    階段形状建物の計算に応用スパン寸法を適用

    外周edgeの足場総長さを応用スパンで決定し、
    その離隔値を使って連続した入隅edgesを計算する。

    Args:
        outer_edge_dimension: 外周edgeの建物寸法（mm）
        perpendicular_edge_lengths: 直交するedgesの長さリスト（mm）
        target_clearance: 目標離隔（mm、デフォルト900mm）
        adjacent_clearances: 隣接edgeの離隔値リスト（mm）
        min_clearance: 最小許容離隔（mm）
        max_clearance: 最大許容離隔（mm）

    Returns:
        AdvancedStairShapeResult: 応用スパンを考慮した階段形状計算結果
    """
    # Step 1: 外周edgeの足場総長さを応用スパンで決定
    outer_result = calculate_with_advanced_spans(
        building_dimension=outer_edge_dimension,
        target_clearance=target_clearance,
        min_clearance=min_clearance,
        max_clearance=max_clearance,
        adjacent_clearances=adjacent_clearances
    )

    # Step 2: 外周から内側へ順に計算
    current_clearance = outer_result.clearance
    inner_clearances = []
    inner_scaffolds = []

    for perp_length in perpendicular_edge_lengths:
        # 入隅計算
        inside_clearance, inside_scaffold = calculate_inside_corner_edge(
            same_face_outer_clearance=current_clearance,
            perpendicular_edge_length=perp_length,
            target_clearance=target_clearance
        )
        inner_clearances.append(inside_clearance)
        inner_scaffolds.append(inside_scaffold)

        # 次の計算のため、現在の離隔を更新
        current_clearance = inside_clearance

    return AdvancedStairShapeResult(
        outer_edge_clearance=outer_result.clearance,
        inner_edges_clearances=inner_clearances,
        inner_edges_scaffolds=inner_scaffolds,
        span_355_count=outer_result.span_355_count,
        span_150_count=outer_result.span_150_count,
        adjusted_by_advanced_spans=(
            outer_result.span_355_count > 0 or outer_result.span_150_count > 0
        )
    )


if __name__ == "__main__":
    print("=== 応用スパン寸法 + 階段形状計算 ===\n")

    # テスト: 3段階段形状
    print("テスト: 外周9000mm、段差3000mm×2")
    result = calculate_stair_shape_with_advanced_spans(
        outer_edge_dimension=9000.0,
        perpendicular_edge_lengths=[3000.0, 3000.0]
    )
    print(f"  外周edge離隔: {result.outer_edge_clearance}mm")
    print(f"  内側edges離隔: {result.inner_edges_clearances}")
    print(f"  内側edges足場長: {result.inner_edges_scaffolds}")
    print(f"  355mm使用: {result.span_355_count}個")
    print(f"  150mm使用: {result.span_150_count}個")
    print(f"  応用スパン使用: {result.adjusted_by_advanced_spans}")
