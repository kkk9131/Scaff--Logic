"""
下屋上に入隅がある建物の足場割付計算モジュール

全体の外周は単純な矩形だが、下屋のライン（内部境界）にL字型の入隅がある形状。
外周は通常の矩形として計算し、内部境界は入隅計算ロジックを適用する。

【重要】このコードはscaffold-logic Skillで生成されました
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
class ShedWithInsideCornerEdgeResult:
    """
    下屋上に入隅がある建物の辺の計算結果を格納するデータクラス

    Attributes:
        edge_name: 辺の名称（例: "edge1", "edge9a"）
        building_length: 建物の辺の長さ（mm）
        clearance: 離隔距離（mm）- 建物から足場までの距離
        scaffold_length: 足場の長さ（mm）
        edge_type: 辺の種類（"outer": 外周辺, "inside_corner": 入隅辺）
    """
    edge_name: str
    building_length: float
    clearance: float
    scaffold_length: float
    edge_type: str = "outer"


def calculate_shed_with_inside_corner(
    width: float,
    total_depth: float,
    inside_corner_x: float,
    main_start_y: float,
    main_end_y: float,
    target_clearance: float = 900.0,
    span_unit: float = 300.0
) -> Dict[str, ShedWithInsideCornerEdgeResult | float]:
    """
    下屋上に入隅がある建物の足場割付を計算する

    【重要】このコードはscaffold-logic Skillで生成されました

    全体の外周は単純な矩形（width × total_depth）だが、
    下屋のライン（内部境界）にL字型の入隅がある形状。

    建物形状の定義:
        - 外周: 単純な矩形
        - 本体部分: X座標inside_corner_x～width、Y座標main_end_y～total_depth
        - 下屋部分: X座標0～width、Y座標0～main_start_y（全幅）
        - 入隅位置: (inside_corner_x, main_start_y)

    計算方針:
        1. 外周edge（edge1, edge2, edge3, edge8）を通常の矩形として計算
        2. edge9a（下屋上の西側横辺）を南面の入隅辺として計算
        3. edge9b（本体南面の横辺）を南面の入隅辺として計算
        4. edge2の下屋部分を南面の入隅辺として計算
        5. edge8の下屋部分はedge9aの計算で求めた値
        6. edge10（入隅縦辺）の足場長さをedge2とedge8の差分で計算

    Args:
        width: 建物の全体幅（X方向、mm）
        total_depth: 建物の全体奥行（Y方向、mm）
        inside_corner_x: 入隅のX座標（mm）
        main_start_y: 下屋の高さ（mm）= 入隅のY座標
        main_end_y: 本体の下端Y座標（mm）
        target_clearance: 目標離隔距離（mm）。デフォルトは900mm
        span_unit: スパンの最小単位（mm）。デフォルトは300mm

    Returns:
        dict: 各辺の計算結果を含む辞書
            - 'edge1': 北辺（本体）
            - 'edge2': 東辺（全体）
            - 'edge3': 南辺（下屋）
            - 'edge8': 西辺（全体）
            - 'edge9a': 内部境界左側横辺（下屋上、Y=main_start_y）
            - 'edge10': 入隅縦辺（X=inside_corner_x、Y=main_start_y～main_end_y）
            - 'edge9b': 入隅横辺（本体南面、Y=main_end_y）
            - 'edge2_lower': edge2の下屋部分（Y=0～main_start_y）
            - 'edge8_lower': edge8の下屋部分（Y=0～main_start_y）
            - 'scaffold_total_x': X方向の足場総長さ（mm）
            - 'scaffold_total_y': Y方向の足場総長さ（mm）
            - 'clearance_x': X方向の離隔距離（mm）
            - 'clearance_y': Y方向の離隔距離（mm）

    Raises:
        ValueError: 入力値が不正な場合

    Example:
        >>> result = calculate_shed_with_inside_corner(
        ...     width=8400.0,
        ...     total_depth=10000.0,
        ...     inside_corner_x=3000.0,
        ...     main_start_y=7000.0,
        ...     main_end_y=8000.0
        ... )
        >>> result['edge9a'].clearance  # 800.0
        >>> result['edge10'].scaffold_length  # 900.0

    計算例（width=8400, total_depth=10000, inside_corner_x=3000, main_start_y=7000, main_end_y=8000）:
        - clearance_x = 900mm, clearance_y = 1000mm
        - edge9aの離隔 = 1000 + 7000 - 7200 = 800mm
        - edge9bの離隔 = 1000 + 1000 - 1200 = 800mm
        - edge2下屋部分の足場 = (1000 + 8000) - 900 = 8100mm
        - edge8下屋部分の足場 = 7200mm（edge9aの計算から）
        - edge10の足場 = 8100 - 7200 = 900mm
    """
    # 入力値の検証
    if width <= 0:
        raise ValueError(f"幅は正の値である必要があります: {width}mm")
    if total_depth <= 0:
        raise ValueError(f"全体奥行は正の値である必要があります: {total_depth}mm")
    if inside_corner_x <= 0 or inside_corner_x >= width:
        raise ValueError(
            f"入隅X座標は0より大きく幅（{width}mm）より小さい必要があります: {inside_corner_x}mm"
        )
    if main_start_y <= 0 or main_start_y >= total_depth:
        raise ValueError(
            f"本体開始Y座標は0より大きく全体奥行（{total_depth}mm）より小さい必要があります: {main_start_y}mm"
        )
    if main_end_y <= main_start_y or main_end_y > total_depth:
        raise ValueError(
            f"本体終了Y座標（{main_end_y}mm）は本体開始Y座標（{main_start_y}mm）より大きく、"
            f"全体奥行（{total_depth}mm）以下である必要があります"
        )

    # 各辺の建物長さを計算
    edge1_length = width  # 北辺: 8400mm
    edge2_length = total_depth  # 東辺: 10000mm
    edge3_length = width  # 南辺: 8400mm
    edge8_length = total_depth  # 西辺: 10000mm

    edge9a_length = inside_corner_x  # 左側横辺: 3000mm
    edge10_length = main_end_y - main_start_y  # 入隅縦辺: 1000mm (8000-7000)
    edge9b_length = width - inside_corner_x  # 右側横辺: 5400mm (8400-3000)

    # Step 1: X方向（edge1とedge3）の外周計算
    # 目標足場長さ = 建物幅 + 両側の離隔距離
    target_scaffold_x = width + 2 * target_clearance
    # 300の倍数に切り上げ
    scaffold_x = math.ceil(target_scaffold_x / span_unit) * span_unit
    # 実際の離隔距離を計算
    clearance_x = (scaffold_x - width) / 2

    # Step 2: Y方向（edge2とedge8）の外周計算
    # 目標足場長さ = 全体奥行 + 両側の離隔距離
    target_scaffold_y = total_depth + 2 * target_clearance
    # 300の倍数に切り上げ
    scaffold_y = math.ceil(target_scaffold_y / span_unit) * span_unit
    # 実際の離隔距離を計算
    clearance_y = (scaffold_y - total_depth) / 2

    # Step 3: edge9a（下屋上の西側横辺）の離隔計算
    # edge9aは南面の入隅辺として計算
    # edge3の離隔値 + edge9aまでの距離（Y方向、main_start_y） - 足場長さ = edge9aの離隔
    edge9a_clearance, edge9a_scaffold_length = calculate_inside_corner_edge(
        same_face_outer_clearance=clearance_y,  # edge3の離隔（Y方向）
        perpendicular_edge_length=main_start_y,  # edge9aまでの距離（下屋の高さ）
        target_clearance=target_clearance,
        span_unit=span_unit
    )

    edge9a = ShedWithInsideCornerEdgeResult(
        edge_name="edge9a",
        building_length=edge9a_length,
        clearance=edge9a_clearance,
        scaffold_length=edge9a_scaffold_length,
        edge_type="inside_corner"
    )

    # Step 4: edge9b（本体南面の横辺）の離隔計算
    # edge9bも南面の入隅辺として計算
    # edge3の離隔値 + edge10の建物長さ - 足場長さ = edge9bの離隔
    edge9b_clearance, edge9b_scaffold_length = calculate_inside_corner_edge(
        same_face_outer_clearance=clearance_y,  # edge3の離隔（Y方向）
        perpendicular_edge_length=edge10_length,  # edge10の建物長さ
        target_clearance=target_clearance,
        span_unit=span_unit
    )

    edge9b = ShedWithInsideCornerEdgeResult(
        edge_name="edge9b",
        building_length=edge9b_length,
        clearance=edge9b_clearance,
        scaffold_length=edge9b_scaffold_length,
        edge_type="inside_corner"
    )

    # Step 5: edge2の下屋部分の足場長さを計算
    # edge2の下屋部分も南面の入隅辺として計算
    # edge3の離隔値 + edge9bまでの距離（Y方向、main_end_y） - 足場長さ
    edge2_lower_clearance, edge2_lower_scaffold = calculate_inside_corner_edge(
        same_face_outer_clearance=clearance_y,  # edge3の離隔（Y方向）
        perpendicular_edge_length=main_end_y,  # edge9bまでの距離
        target_clearance=target_clearance,
        span_unit=span_unit
    )

    edge2_lower = ShedWithInsideCornerEdgeResult(
        edge_name="edge2_lower",
        building_length=main_end_y,  # Y座標0～main_end_y
        clearance=edge2_lower_clearance,
        scaffold_length=edge2_lower_scaffold,
        edge_type="inside_corner"
    )

    # Step 6: edge8の下屋部分の足場長さ
    # edge9aの計算で求めた足場長さと同じ
    edge8_lower_scaffold = edge9a_scaffold_length
    edge8_lower_clearance = edge9a_clearance

    edge8_lower = ShedWithInsideCornerEdgeResult(
        edge_name="edge8_lower",
        building_length=main_start_y,  # Y座標0～main_start_y
        clearance=edge8_lower_clearance,
        scaffold_length=edge8_lower_scaffold,
        edge_type="inside_corner"
    )

    # Step 7: edge10（入隅縦辺）の足場長さを計算
    # edge2の下屋部分の足場長さ - edge8の下屋部分の足場長さ
    edge10_scaffold_length = edge2_lower_scaffold - edge8_lower_scaffold

    # edge10の離隔値は、edge10が西面に属するため、edge8の離隔（X方向）と同じ
    edge10_clearance = clearance_x

    edge10 = ShedWithInsideCornerEdgeResult(
        edge_name="edge10",
        building_length=edge10_length,
        clearance=edge10_clearance,
        scaffold_length=edge10_scaffold_length,
        edge_type="inside_corner"
    )

    # 外周辺の構築
    # edge1: 北辺（本体）
    # X方向の辺なので、Y方向（北側）に離隔を取る
    edge1 = ShedWithInsideCornerEdgeResult(
        edge_name="edge1",
        building_length=edge1_length,
        clearance=clearance_y,  # Y方向の離隔
        scaffold_length=scaffold_x,
        edge_type="outer"
    )

    # edge2: 東辺（全体）
    # Y方向の辺なので、X方向（東側）に離隔を取る
    edge2 = ShedWithInsideCornerEdgeResult(
        edge_name="edge2",
        building_length=edge2_length,
        clearance=clearance_x,  # X方向の離隔
        scaffold_length=scaffold_y,
        edge_type="outer"
    )

    # edge3: 南辺（下屋）
    # X方向の辺なので、Y方向（南側）に離隔を取る
    edge3 = ShedWithInsideCornerEdgeResult(
        edge_name="edge3",
        building_length=edge3_length,
        clearance=clearance_y,  # Y方向の離隔
        scaffold_length=scaffold_x,
        edge_type="outer"
    )

    # edge8: 西辺（全体）
    # Y方向の辺なので、X方向（西側）に離隔を取る
    edge8 = ShedWithInsideCornerEdgeResult(
        edge_name="edge8",
        building_length=edge8_length,
        clearance=clearance_x,  # X方向の離隔
        scaffold_length=scaffold_y,
        edge_type="outer"
    )

    return {
        'edge1': edge1,
        'edge2': edge2,
        'edge3': edge3,
        'edge8': edge8,
        'edge9a': edge9a,
        'edge10': edge10,
        'edge9b': edge9b,
        'edge2_lower': edge2_lower,
        'edge8_lower': edge8_lower,
        # メタ情報
        'scaffold_total_x': scaffold_x,
        'scaffold_total_y': scaffold_y,
        'clearance_x': clearance_x,
        'clearance_y': clearance_y
    }


if __name__ == "__main__":
    # テスト実行
    print("=" * 60)
    print("下屋上に入隅がある建物の足場計算テスト")
    print("=" * 60)

    # 建物形状
    print("\n建物形状:")
    print("  全体幅: 8400mm")
    print("  全体奥行: 10000mm")
    print("  本体部分: X座標3000-8400mm、Y座標8000-10000mm")
    print("  下屋部分: 全幅、Y座標0-7000mm")
    print("  入隅位置: (3000, 7000)")
    print("  入隅縦辺の長さ: 1000mm (7000-8000mm)")

    result = calculate_shed_with_inside_corner(
        width=8400.0,
        total_depth=10000.0,
        inside_corner_x=3000.0,
        main_start_y=7000.0,
        main_end_y=8000.0
    )

    print("\n" + "=" * 60)
    print("外周辺の計算結果")
    print("=" * 60)

    for edge_name in ['edge1', 'edge2', 'edge3', 'edge8']:
        edge = result[edge_name]
        print(f"\n{edge.edge_name}:")
        print(f"  建物長さ: {edge.building_length}mm")
        print(f"  離隔距離: {edge.clearance}mm")
        print(f"  足場長さ: {edge.scaffold_length}mm")

    print("\n" + "=" * 60)
    print("内部境界（入隅）の計算結果")
    print("=" * 60)

    for edge_name in ['edge9a', 'edge10', 'edge9b']:
        edge = result[edge_name]
        print(f"\n{edge.edge_name}:")
        print(f"  建物長さ: {edge.building_length}mm")
        print(f"  離隔距離: {edge.clearance}mm")
        print(f"  足場長さ: {edge.scaffold_length}mm")

    print("\n" + "=" * 60)
    print("下屋部分の計算結果")
    print("=" * 60)

    for edge_name in ['edge2_lower', 'edge8_lower']:
        edge = result[edge_name]
        print(f"\n{edge.edge_name}:")
        print(f"  建物長さ: {edge.building_length}mm")
        print(f"  離隔距離: {edge.clearance}mm")
        print(f"  足場長さ: {edge.scaffold_length}mm")

    print("\n" + "=" * 60)
    print("メタ情報")
    print("=" * 60)
    print(f"\nX方向の足場総長さ: {result['scaffold_total_x']}mm")
    print(f"Y方向の足場総長さ: {result['scaffold_total_y']}mm")
    print(f"X方向の離隔距離: {result['clearance_x']}mm")
    print(f"Y方向の離隔距離: {result['clearance_y']}mm")

    # 検証
    print("\n" + "=" * 60)
    print("検証")
    print("=" * 60)

    # 300の倍数確認
    print(f"\n300の倍数確認:")
    print(f"  scaffold_total_x: {result['scaffold_total_x']}mm → {result['scaffold_total_x'] % 300 == 0}")
    print(f"  scaffold_total_y: {result['scaffold_total_y']}mm → {result['scaffold_total_y'] % 300 == 0}")
    print(f"  edge10 scaffold: {result['edge10'].scaffold_length}mm → {result['edge10'].scaffold_length % 300 == 0}")
    print(f"  edge9b scaffold: {result['edge9b'].scaffold_length}mm → {result['edge9b'].scaffold_length % 300 == 0}")
    print(f"  edge9a scaffold: {result['edge9a'].scaffold_length}mm → {result['edge9a'].scaffold_length % 300 == 0}")

    # edge10の計算検証
    print(f"\nedge10の足場長さ検証:")
    print(f"  edge2_lower - edge8_lower = {result['edge2_lower'].scaffold_length} - {result['edge8_lower'].scaffold_length} = {result['edge2_lower'].scaffold_length - result['edge8_lower'].scaffold_length}mm")
    print(f"  edge10 scaffold: {result['edge10'].scaffold_length}mm")
    print(f"  一致: {result['edge10'].scaffold_length == result['edge2_lower'].scaffold_length - result['edge8_lower'].scaffold_length}")
