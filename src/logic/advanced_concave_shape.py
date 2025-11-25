"""
応用スパン寸法に対応した凹型（コの字型）建物計算モジュール

凹型建物（コの字型）の計算に、応用スパン寸法（355mm, 150mm）で
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
class AdvancedConcaveShapeResult:
    """
    応用スパン寸法を考慮した凹型建物計算結果

    Attributes:
        outer_edges_clearances: 外周edgesの離隔リスト（mm）
        outer_edges_scaffolds: 外周edgesの足場長リスト（mm）
        notch_edge_clearance: 窪みedgeの離隔（mm）
        notch_edge_scaffold: 窪みedgeの足場長（mm）
        total_scaffold_length: 足場総長さ（mm）
        span_355_count: 355mmスパンの使用数
        span_150_count: 150mmスパンの使用数
        adjusted_by_advanced_spans: 応用スパンを使用したか
    """
    outer_edges_clearances: List[float]
    outer_edges_scaffolds: List[float]
    notch_edge_clearance: float
    notch_edge_scaffold: float
    total_scaffold_length: float
    span_355_count: int
    span_150_count: int
    adjusted_by_advanced_spans: bool


def calculate_concave_shape_with_advanced_spans(
    outer_dimension: float,
    notch_depth: float,
    target_clearance: float = 900.0,
    adjacent_clearances: Optional[List[float]] = None,
    min_clearance: Optional[float] = None,
    max_clearance: Optional[float] = None
) -> AdvancedConcaveShapeResult:
    """
    凹型建物の計算に応用スパン寸法を適用

    外周edgesの足場総長さを応用スパンで決定し、
    その総長さを使って各edgeの離隔と窪みedgeを計算する。

    Args:
        outer_dimension: 外枠の建物寸法（mm）
        notch_depth: 窪みの深さ（mm）
        target_clearance: 目標離隔（mm、デフォルト900mm）
        adjacent_clearances: 隣接edgeの離隔値リスト（mm）
        min_clearance: 最小許容離隔（mm）
        max_clearance: 最大許容離隔（mm）

    Returns:
        AdvancedConcaveShapeResult: 応用スパンを考慮した凹型建物計算結果
    """
    # Step 1: 外枠の足場総長さを応用スパンで決定
    outer_result = calculate_with_advanced_spans(
        building_dimension=outer_dimension,
        target_clearance=target_clearance,
        min_clearance=min_clearance,
        max_clearance=max_clearance,
        adjacent_clearances=adjacent_clearances
    )

    # Step 2: 外周edgesの離隔は固定（応用スパンで決定された値）
    outer_clearance = outer_result.clearance

    # 外周2つのedgeの足場長を計算（対称として扱う）
    # 実際には個別の計算が必要だが、ここでは簡略化
    outer_scaffold_1 = outer_result.total_scaffold_length  # 仮
    outer_scaffold_2 = outer_result.total_scaffold_length  # 仮

    # Step 3: 窪みedgeの計算（入隅ロジックを使用）
    notch_clearance, notch_scaffold = calculate_inside_corner_edge(
        same_face_outer_clearance=outer_clearance,
        perpendicular_edge_length=notch_depth,
        target_clearance=target_clearance
    )

    return AdvancedConcaveShapeResult(
        outer_edges_clearances=[outer_clearance, outer_clearance],
        outer_edges_scaffolds=[outer_scaffold_1, outer_scaffold_2],
        notch_edge_clearance=notch_clearance,
        notch_edge_scaffold=notch_scaffold,
        total_scaffold_length=outer_result.total_scaffold_length,
        span_355_count=outer_result.span_355_count,
        span_150_count=outer_result.span_150_count,
        adjusted_by_advanced_spans=(
            outer_result.span_355_count > 0 or outer_result.span_150_count > 0
        )
    )


if __name__ == "__main__":
    print("=== 応用スパン寸法 + 凹型建物計算 ===\n")

    # テスト: コの字型建物
    print("テスト: 外枠10000mm、窪み2000mm")
    result = calculate_concave_shape_with_advanced_spans(
        outer_dimension=10000.0,
        notch_depth=2000.0
    )
    print(f"  外周edges離隔: {result.outer_edges_clearances}")
    print(f"  窪みedge離隔: {result.notch_edge_clearance}mm")
    print(f"  窪みedge足場長: {result.notch_edge_scaffold}mm")
    print(f"  足場総長: {result.total_scaffold_length}mm")
    print(f"  355mm使用: {result.span_355_count}個")
    print(f"  150mm使用: {result.span_150_count}個")
    print(f"  応用スパン使用: {result.adjusted_by_advanced_spans}")
