"""
張り出し付き建物の足場割付計算モジュール

下屋やバルコニーなど、建物本体から張り出した部分を持つ建物の足場計算を行う。
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
class ProtrusionBuildingEdgeResult:
    """
    張り出し付き建物の辺の計算結果を格納するデータクラス

    Attributes:
        edge_name: 辺の名称（例: "edge1", "edge2_upper"）
        building_length: 建物の辺の長さ（mm）
        clearance: 離隔距離（mm）- 建物から足場までの距離
        scaffold_length: 足場の長さ（mm）
        height_section: 高さ区分（"upper": 本体部分, "lower": 張り出し部分, None: 区分なし）
    """
    edge_name: str
    building_length: float
    clearance: float
    scaffold_length: float
    height_section: str | None = None


def _calculate_protrusion_building(
    width: float,
    total_depth: float,
    main_depth: float,
    protrusion_depth: float,
    protrusion_name: str,
    target_clearance: float = 900.0,
    span_unit: float = 300.0
) -> Dict[str, ProtrusionBuildingEdgeResult]:
    """
    張り出し付き建物の足場割付を計算する（内部共通関数）

    下屋、バルコニーなど、建物本体から張り出した部分を持つ建物の
    各辺の足場長さと離隔距離を計算する。

    計算方針:
        1. 外周edge（edge1, edge2, edge3, edge4）を通常の矩形として計算
        2. edge5（内部境界）を入隅計算ロジックで計算
        3. Y方向の足場を張り出し部分と本体部分に分配

    Args:
        width: 建物の全体幅（X方向、mm）
        total_depth: 建物の全体奥行（Y方向、mm）
        main_depth: 本体部分の奥行（H1、mm）
        protrusion_depth: 張り出し部分の奥行（H2、mm）
        protrusion_name: 張り出しの種類名（"shed", "balcony"等、エラーメッセージ用）
        target_clearance: 目標離隔距離（mm）。デフォルトは900mm
        span_unit: スパンの最小単位（mm）。デフォルトは300mm

    Returns:
        dict: 各辺の計算結果を含む辞書
            - 'edge1': 北辺（本体）
            - 'edge2_upper': 東辺上部（本体部分）
            - 'edge2_lower': 東辺下部（張り出し部分）
            - 'edge3': 南辺（張り出し部分）
            - 'edge4_upper': 西辺上部（本体部分）
            - 'edge4_lower': 西辺下部（張り出し部分）
            - 'edge5': 内部境界（本体南面）

    Raises:
        ValueError: 入力値が不正な場合

    Notes:
        - total_depth = main_depth + protrusion_depth であることを前提とする
        - edge2とedge4は高さで上下に分割される
        - edge5は本体と張り出し部分の境界線
    """
    # 入力値の検証
    if width <= 0:
        raise ValueError(f"幅は正の値である必要があります: {width}mm")
    if total_depth <= 0:
        raise ValueError(f"全体奥行は正の値である必要があります: {total_depth}mm")
    if main_depth <= 0:
        raise ValueError(f"本体奥行は正の値である必要があります: {main_depth}mm")
    if protrusion_depth <= 0:
        raise ValueError(
            f"{protrusion_name}奥行は正の値である必要があります: {protrusion_depth}mm"
        )
    if not math.isclose(total_depth, main_depth + protrusion_depth, rel_tol=1e-9):
        raise ValueError(
            f"全体奥行（{total_depth}mm）が本体奥行（{main_depth}mm）+ "
            f"{protrusion_name}奥行（{protrusion_depth}mm）と一致しません"
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
    # edge3の離隔 + 張り出し奥行 - 300の倍数 = edge5の離隔
    edge5_clearance, protrusion_scaffold_length = calculate_inside_corner_edge(
        same_face_outer_clearance=clearance_x,  # edge3の離隔値
        perpendicular_edge_length=protrusion_depth,    # 張り出し奥行
        target_clearance=target_clearance,
        span_unit=span_unit
    )

    # Step 4: Y方向の足場を張り出し部分と本体部分に分配
    # 張り出し部分の足場長さ = edge5計算で引いた300の倍数
    scaffold_edge2_lower = protrusion_scaffold_length
    scaffold_edge4_lower = protrusion_scaffold_length

    # 本体部分の足場長さ = Y方向総長さ - 張り出し部分
    scaffold_edge2_upper = scaffold_y - scaffold_edge2_lower
    scaffold_edge4_upper = scaffold_y - scaffold_edge4_lower

    # 本体部分の離隔距離を計算
    clearance_edge2_upper = (scaffold_edge2_upper - main_depth) / 2
    clearance_edge4_upper = (scaffold_edge4_upper - main_depth) / 2

    # 各辺の結果を構築
    # edge1: 北辺（本体）
    edge1 = ProtrusionBuildingEdgeResult(
        edge_name="edge1",
        building_length=width,
        clearance=clearance_x,
        scaffold_length=scaffold_x,
        height_section=None  # 高さ区分なし（本体のみ）
    )

    # edge2上: 東辺上部（本体部分）
    edge2_upper = ProtrusionBuildingEdgeResult(
        edge_name="edge2_upper",
        building_length=main_depth,
        clearance=clearance_edge2_upper,
        scaffold_length=scaffold_edge2_upper,
        height_section="upper"
    )

    # edge2下: 東辺下部（張り出し部分）
    edge2_lower = ProtrusionBuildingEdgeResult(
        edge_name="edge2_lower",
        building_length=protrusion_depth,
        clearance=clearance_y,  # 南側の離隔
        scaffold_length=scaffold_edge2_lower,
        height_section="lower"
    )

    # edge3: 南辺（張り出し部分）
    edge3 = ProtrusionBuildingEdgeResult(
        edge_name="edge3",
        building_length=width,
        clearance=clearance_x,
        scaffold_length=scaffold_x,
        height_section=None  # 高さ区分なし（張り出し部分のみ）
    )

    # edge4上: 西辺上部（本体部分）
    edge4_upper = ProtrusionBuildingEdgeResult(
        edge_name="edge4_upper",
        building_length=main_depth,
        clearance=clearance_edge4_upper,
        scaffold_length=scaffold_edge4_upper,
        height_section="upper"
    )

    # edge4下: 西辺下部（張り出し部分）
    edge4_lower = ProtrusionBuildingEdgeResult(
        edge_name="edge4_lower",
        building_length=protrusion_depth,
        clearance=clearance_y,  # 南側の離隔
        scaffold_length=scaffold_edge4_lower,
        height_section="lower"
    )

    # edge5: 内部境界（本体南面、張り出し部分との接続部）
    edge5 = ProtrusionBuildingEdgeResult(
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


def calculate_shed_building(
    width: float,
    total_depth: float,
    main_depth: float,
    shed_depth: float,
    target_clearance: float = 900.0,
    span_unit: float = 300.0
) -> Dict[str, ProtrusionBuildingEdgeResult]:
    """
    下屋付き建物の足場割付を計算する

    平面的には矩形だが、高さに段差がある下屋付き建物の
    各辺の足場長さと離隔距離を計算する。

    Args:
        width: 建物の全体幅（X方向、mm）
        total_depth: 建物の全体奥行（Y方向、mm）
        main_depth: 本体部分の奥行（H1、mm）
        shed_depth: 下屋部分の奥行（H2、mm）
        target_clearance: 目標離隔距離（mm）。デフォルトは900mm
        span_unit: スパンの最小単位（mm）。デフォルトは300mm

    Returns:
        dict: 各辺の計算結果を含む辞書

    Example:
        >>> result = calculate_shed_building(
        ...     width=8400.0,
        ...     total_depth=4510.0,
        ...     main_depth=3600.0,
        ...     shed_depth=910.0
        ... )
        >>> result['edge5'].clearance
        910.0
    """
    return _calculate_protrusion_building(
        width=width,
        total_depth=total_depth,
        main_depth=main_depth,
        protrusion_depth=shed_depth,
        protrusion_name="下屋",
        target_clearance=target_clearance,
        span_unit=span_unit
    )


def calculate_balcony_building(
    width: float,
    total_depth: float,
    main_depth: float,
    balcony_depth: float,
    target_clearance: float = 900.0,
    span_unit: float = 300.0
) -> Dict[str, ProtrusionBuildingEdgeResult]:
    """
    バルコニー付き建物の足場割付を計算する

    平面的には矩形だが、高さに段差があるバルコニー付き建物の
    各辺の足場長さと離隔距離を計算する。

    Args:
        width: 建物の全体幅（X方向、mm）
        total_depth: 建物の全体奥行（Y方向、mm）
        main_depth: 本体部分の奥行（H1、mm）
        balcony_depth: バルコニー部分の奥行（H2、mm）
        target_clearance: 目標離隔距離（mm）。デフォルトは900mm
        span_unit: スパンの最小単位（mm）。デフォルトは300mm

    Returns:
        dict: 各辺の計算結果を含む辞書

    Example:
        >>> result = calculate_balcony_building(
        ...     width=8400.0,
        ...     total_depth=4510.0,
        ...     main_depth=3600.0,
        ...     balcony_depth=910.0
        ... )
        >>> result['edge5'].clearance
        910.0
    """
    return _calculate_protrusion_building(
        width=width,
        total_depth=total_depth,
        main_depth=main_depth,
        protrusion_depth=balcony_depth,
        protrusion_name="バルコニー",
        target_clearance=target_clearance,
        span_unit=span_unit
    )


if __name__ == "__main__":
    # テスト実行
    print("=" * 60)
    print("下屋付き建物の足場計算テスト")
    print("=" * 60)

    result_shed = calculate_shed_building(
        width=8400.0,
        total_depth=4510.0,
        main_depth=3600.0,
        shed_depth=910.0
    )

    print(f"\nedge5の離隔値: {result_shed['edge5'].clearance}mm")
    print(f"下屋部分の足場長さ: {result_shed['edge2_lower'].scaffold_length}mm")
    print(f"本体部分の足場長さ: {result_shed['edge2_upper'].scaffold_length}mm")

    print("\n" + "=" * 60)
    print("バルコニー付き建物の足場計算テスト")
    print("=" * 60)

    result_balcony = calculate_balcony_building(
        width=8400.0,
        total_depth=4510.0,
        main_depth=3600.0,
        balcony_depth=910.0
    )

    print(f"\nedge5の離隔値: {result_balcony['edge5'].clearance}mm")
    print(f"バルコニー部分の足場長さ: {result_balcony['edge2_lower'].scaffold_length}mm")
    print(f"本体部分の足場長さ: {result_balcony['edge2_upper'].scaffold_length}mm")

    print("\n✅ 下屋とバルコニーは同じ計算結果になります")
