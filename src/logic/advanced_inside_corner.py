"""
応用スパン寸法に対応した入隅（L字型建物）計算モジュール

L字型建物の入隅計算に、応用スパン寸法（355mm, 150mm）で
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
class AdvancedInsideCornerResult:
    """
    応用スパン寸法を考慮した入隅計算結果

    Attributes:
        edge_clearance: 入隅edgeの離隔（mm）
        edge_scaffold_length: 入隅edgeの足場総長（mm）
        same_face_outer_clearance: 同じ面の外周辺離隔（mm）
        span_355_count: 355mmスパンの使用数
        span_150_count: 150mmスパンの使用数
        adjusted_by_advanced_spans: 応用スパンを使用したか
    """
    edge_clearance: float
    edge_scaffold_length: float
    same_face_outer_clearance: float
    span_355_count: int
    span_150_count: int
    adjusted_by_advanced_spans: bool


def calculate_inside_corner_with_advanced_spans(
    same_face_outer_dimension: float,
    perpendicular_edge_length: float,
    target_clearance: float = 900.0,
    adjacent_clearances: Optional[List[float]] = None,
    min_clearance: Optional[float] = None,
    max_clearance: Optional[float] = None
) -> AdvancedInsideCornerResult:
    """
    入隅計算に応用スパン寸法を適用

    同じ面の外周辺の足場総長さを応用スパンで決定し、
    その離隔値を使って入隅edgeの計算を行う。

    Args:
        same_face_outer_dimension: 同じ面の外周辺の建物寸法（mm）
        perpendicular_edge_length: 直交するedgeの長さ（mm）
        target_clearance: 目標離隔（mm、デフォルト900mm）
        adjacent_clearances: 隣接edgeの離隔値リスト（mm）
        min_clearance: 最小許容離隔（mm）
        max_clearance: 最大許容離隔（mm）

    Returns:
        AdvancedInsideCornerResult: 応用スパンを考慮した入隅計算結果
    """
    # Step 1: 外周辺の足場総長さを応用スパンで決定
    outer_result = calculate_with_advanced_spans(
        building_dimension=same_face_outer_dimension,
        target_clearance=target_clearance,
        min_clearance=min_clearance,
        max_clearance=max_clearance,
        adjacent_clearances=adjacent_clearances
    )

    # Step 2: 外周辺の離隔値を使って入隅計算
    inside_clearance, inside_scaffold = calculate_inside_corner_edge(
        same_face_outer_clearance=outer_result.clearance,
        perpendicular_edge_length=perpendicular_edge_length,
        target_clearance=target_clearance
    )

    return AdvancedInsideCornerResult(
        edge_clearance=inside_clearance,
        edge_scaffold_length=inside_scaffold,
        same_face_outer_clearance=outer_result.clearance,
        span_355_count=outer_result.span_355_count,
        span_150_count=outer_result.span_150_count,
        adjusted_by_advanced_spans=(
            outer_result.span_355_count > 0 or outer_result.span_150_count > 0
        )
    )


if __name__ == "__main__":
    print("=== 応用スパン寸法 + 入隅計算 ===\n")

    # テスト: L字型建物の入隅
    print("テスト: 外周辺7000mm、直交edge 4000mm")
    result = calculate_inside_corner_with_advanced_spans(
        same_face_outer_dimension=7000.0,
        perpendicular_edge_length=4000.0
    )
    print(f"  入隅edge離隔: {result.edge_clearance}mm")
    print(f"  入隅edge足場長: {result.edge_scaffold_length}mm")
    print(f"  外周辺離隔: {result.same_face_outer_clearance}mm")
    print(f"  355mm使用: {result.span_355_count}個")
    print(f"  150mm使用: {result.span_150_count}個")
    print(f"  応用スパン使用: {result.adjusted_by_advanced_spans}")
