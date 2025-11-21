"""
下屋付き建物の足場割付計算モジュール

下屋（軒の出、庇、ポーチなど）が接続している建物の足場計算を行う。
平面的には矩形だが、高さに段差がある形状に対応。
"""

from dataclasses import dataclass
from typing import Dict
import math
import sys
from pathlib import Path

# インポート処理（相対インポートと絶対インポートの両対応）
try:
    from .inside_corner import calculate_inside_corner_edge
except ImportError:
    # 直接実行時のパス設定
    sys.path.insert(0, str(Path(__file__).parent))
    from inside_corner import calculate_inside_corner_edge


@dataclass
class ShedBuildingEdgeResult:
    """
    下屋付き建物の辺の計算結果を格納するデータクラス

    Attributes:
        edge_name: 辺の名称（例: "edge1", "edge2_upper"）
        building_length: 建物の辺の長さ（mm）
        clearance: 離隔距離（mm）- 建物から足場までの距離
        scaffold_length: 足場の長さ（mm）
        height_section: 高さ区分（"upper": 本体部分, "lower": 下屋部分, None: 区分なし）
    """
    edge_name: str
    building_length: float
    clearance: float
    scaffold_length: float
    height_section: str | None = None


def calculate_shed_building(
    width: float,
    total_depth: float,
    main_depth: float,
    shed_depth: float,
    target_clearance: float = 900.0,
    span_unit: float = 300.0
) -> Dict[str, ShedBuildingEdgeResult]:
    """
    下屋付き建物の足場割付を計算する

    平面的には矩形だが、高さに段差がある下屋付き建物の
    各辺の足場長さと離隔距離を計算する。

    計算方針:
        1. 外周edge（edge1, edge2, edge3, edge4）を通常の矩形として計算
        2. edge5（内部境界）を入隅計算ロジックで計算
        3. Y方向の足場を下屋部分と本体部分に分配

    Args:
        width: 建物の全体幅（X方向、mm）
        total_depth: 建物の全体奥行（Y方向、mm）
        main_depth: 本体部分の奥行（H1、mm）
        shed_depth: 下屋部分の奥行（H2、mm）
        target_clearance: 目標離隔距離（mm）。デフォルトは900mm
        span_unit: スパンの最小単位（mm）。デフォルトは300mm

    Returns:
        dict: 各辺の計算結果を含む辞書
            - 'edge1': 北辺（本体）
            - 'edge2_upper': 東辺上部（本体部分）
            - 'edge2_lower': 東辺下部（下屋部分）
            - 'edge3': 南辺（下屋）
            - 'edge4_upper': 西辺上部（本体部分）
            - 'edge4_lower': 西辺下部（下屋部分）
            - 'edge5': 内部境界（本体南面）

    Raises:
        ValueError: 入力値が不正な場合

    Example:
        >>> result = calculate_shed_building(
        ...     width=8400.0,
        ...     total_depth=4510.0,
        ...     main_depth=3600.0,
        ...     shed_depth=910.0
        ... )
        >>> result['edge5'].clearance
        910.0
        >>> result['edge2_lower'].scaffold_length
        900.0

    Notes:
        - total_depth = main_depth + shed_depth であることを前提とする
        - edge2とedge4は高さで上下に分割される
        - edge5は本体と下屋の境界線
    """
    # 入力値の検証
    if width <= 0:
        raise ValueError(f"幅は正の値である必要があります: {width}mm")
    if total_depth <= 0:
        raise ValueError(f"全体奥行は正の値である必要があります: {total_depth}mm")
    if main_depth <= 0:
        raise ValueError(f"本体奥行は正の値である必要があります: {main_depth}mm")
    if shed_depth <= 0:
        raise ValueError(f"下屋奥行は正の値である必要があります: {shed_depth}mm")
    if not math.isclose(total_depth, main_depth + shed_depth, rel_tol=1e-9):
        raise ValueError(
            f"全体奥行（{total_depth}mm）が本体奥行（{main_depth}mm）+ "
            f"下屋奥行（{shed_depth}mm）と一致しません"
        )

    # Step 1: X方向（edge1とedge3）の外周計算
    # 目標足場長さ = 建物幅 + 両側の離隔距離
    target_scaffold_x = width + 2 * target_clearance
    # 300の倍数に切り上げ
    scaffold_x = math.ceil(target_scaffold_x / span_unit) * span_unit
    # 実際の離隔距離を計算
    clearance_x = (scaffold_x - width) / 2

    # Step 2: Y方向（edge2とedge4）の外周計算
    # 目標足場長さ = 全体奥行 + 両側の離隔距離
    target_scaffold_y = total_depth + 2 * target_clearance
    # 300の倍数に切り上げ
    scaffold_y = math.ceil(target_scaffold_y / span_unit) * span_unit
    # 実際の離隔距離を計算
    clearance_y = (scaffold_y - total_depth) / 2

    # Step 3: edge5（内部境界）の離隔計算（入隅計算ロジックを使用）
    # edge3の離隔 + 下屋奥行 - 300の倍数 = edge5の離隔
    edge5_clearance, shed_scaffold_length = calculate_inside_corner_edge(
        same_face_outer_clearance=clearance_x,  # edge3の離隔値
        perpendicular_edge_length=shed_depth,    # 下屋奥行
        target_clearance=target_clearance,
        span_unit=span_unit
    )

    # Step 4: Y方向の足場を下屋部分と本体部分に分配
    # 下屋部分の足場長さ = edge5計算で引いた300の倍数
    scaffold_edge2_lower = shed_scaffold_length
    scaffold_edge4_lower = shed_scaffold_length

    # 本体部分の足場長さ = Y方向総長さ - 下屋部分
    scaffold_edge2_upper = scaffold_y - scaffold_edge2_lower
    scaffold_edge4_upper = scaffold_y - scaffold_edge4_lower

    # 本体部分の離隔距離を計算
    clearance_edge2_upper = (scaffold_edge2_upper - main_depth) / 2
    clearance_edge4_upper = (scaffold_edge4_upper - main_depth) / 2

    # 各辺の結果を構築
    # edge1: 北辺（本体）
    edge1 = ShedBuildingEdgeResult(
        edge_name="edge1",
        building_length=width,
        clearance=clearance_x,
        scaffold_length=scaffold_x,
        height_section=None  # 高さ区分なし（本体のみ）
    )

    # edge2上: 東辺上部（本体部分）
    edge2_upper = ShedBuildingEdgeResult(
        edge_name="edge2_upper",
        building_length=main_depth,
        clearance=clearance_edge2_upper,
        scaffold_length=scaffold_edge2_upper,
        height_section="upper"
    )

    # edge2下: 東辺下部（下屋部分）
    edge2_lower = ShedBuildingEdgeResult(
        edge_name="edge2_lower",
        building_length=shed_depth,
        clearance=clearance_y,  # 南側の離隔
        scaffold_length=scaffold_edge2_lower,
        height_section="lower"
    )

    # edge3: 南辺（下屋）
    edge3 = ShedBuildingEdgeResult(
        edge_name="edge3",
        building_length=width,
        clearance=clearance_x,
        scaffold_length=scaffold_x,
        height_section=None  # 高さ区分なし（下屋のみ）
    )

    # edge4上: 西辺上部（本体部分）
    edge4_upper = ShedBuildingEdgeResult(
        edge_name="edge4_upper",
        building_length=main_depth,
        clearance=clearance_edge4_upper,
        scaffold_length=scaffold_edge4_upper,
        height_section="upper"
    )

    # edge4下: 西辺下部（下屋部分）
    edge4_lower = ShedBuildingEdgeResult(
        edge_name="edge4_lower",
        building_length=shed_depth,
        clearance=clearance_y,  # 南側の離隔
        scaffold_length=scaffold_edge4_lower,
        height_section="lower"
    )

    # edge5: 内部境界（本体南面、下屋との接続部）
    edge5 = ShedBuildingEdgeResult(
        edge_name="edge5",
        building_length=width,
        clearance=edge5_clearance,
        scaffold_length=scaffold_x,
        height_section=None  # 境界線
    )

    return {
        'edge1': edge1,
        'edge2_upper': edge2_upper,
        'edge2_lower': edge2_lower,
        'edge3': edge3,
        'edge4_upper': edge4_upper,
        'edge4_lower': edge4_lower,
        'edge5': edge5,
        # メタ情報も返す
        'scaffold_total_x': scaffold_x,
        'scaffold_total_y': scaffold_y,
        'clearance_x': clearance_x,
        'clearance_y': clearance_y
    }


if __name__ == "__main__":
    # テスト実行
    print("=== 下屋付き建物の足場計算テスト ===\n")

    # 下屋付き建物: 8400mm × 4510mm
    # 本体: 8400mm × 3600mm
    # 下屋: 8400mm × 910mm
    print("建物形状: 下屋付き建物（南面に下屋）")
    print("全体寸法: 8400mm × 4510mm")
    print("  本体: 8400mm × 3600mm")
    print("  下屋: 8400mm × 910mm\n")

    # 計算実行
    result = calculate_shed_building(
        width=8400.0,
        total_depth=4510.0,
        main_depth=3600.0,
        shed_depth=910.0
    )

    print("各辺の計算結果:")
    print("-" * 60)

    # 外周edge
    print(f"\n【外周edge】")
    print(f"edge1（北辺）:")
    print(f"  建物長さ: {result['edge1'].building_length}mm")
    print(f"  離隔距離: {result['edge1'].clearance}mm")
    print(f"  足場長さ: {result['edge1'].scaffold_length}mm")

    print(f"\nedge3（南辺）:")
    print(f"  建物長さ: {result['edge3'].building_length}mm")
    print(f"  離隔距離: {result['edge3'].clearance}mm")
    print(f"  足場長さ: {result['edge3'].scaffold_length}mm")

    # 東西辺（上下分割）
    print(f"\n【東西辺（高さで分割）】")
    print(f"edge2上（東辺・本体部分）:")
    print(f"  建物長さ: {result['edge2_upper'].building_length}mm")
    print(f"  離隔距離: {result['edge2_upper'].clearance}mm")
    print(f"  足場長さ: {result['edge2_upper'].scaffold_length}mm")

    print(f"\nedge2下（東辺・下屋部分）:")
    print(f"  建物長さ: {result['edge2_lower'].building_length}mm")
    print(f"  離隔距離: {result['edge2_lower'].clearance}mm（南側）")
    print(f"  足場長さ: {result['edge2_lower'].scaffold_length}mm")

    print(f"\nedge4上（西辺・本体部分）:")
    print(f"  建物長さ: {result['edge4_upper'].building_length}mm")
    print(f"  離隔距離: {result['edge4_upper'].clearance}mm")
    print(f"  足場長さ: {result['edge4_upper'].scaffold_length}mm")

    print(f"\nedge4下（西辺・下屋部分）:")
    print(f"  建物長さ: {result['edge4_lower'].building_length}mm")
    print(f"  離隔距離: {result['edge4_lower'].clearance}mm（南側）")
    print(f"  足場長さ: {result['edge4_lower'].scaffold_length}mm")

    # 内部境界
    print(f"\n【内部境界】")
    print(f"edge5（本体南面・下屋との接続部）:")
    print(f"  建物長さ: {result['edge5'].building_length}mm")
    print(f"  離隔距離: {result['edge5'].clearance}mm")
    print(f"  足場長さ: {result['edge5'].scaffold_length}mm")

    # サマリー
    print(f"\n【サマリー】")
    print(f"X方向足場総長さ: {result['scaffold_total_x']}mm")
    print(f"Y方向足場総長さ: {result['scaffold_total_y']}mm")
    print(f"  下屋部分: {result['edge2_lower'].scaffold_length}mm")
    print(f"  本体部分: {result['edge2_upper'].scaffold_length}mm")
