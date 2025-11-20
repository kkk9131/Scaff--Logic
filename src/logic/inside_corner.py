"""
入隅（内角）計算モジュール

L字型建物などの入隅部分の足場割付計算を行う
"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class InsideCornerResult:
    """
    入隅辺の計算結果を格納するデータクラス

    Attributes:
        edge_name: 辺の名称（例: "edge4", "edge5"）
        building_length: 建物の辺の長さ（mm）
        clearance: 離隔距離（mm）- 建物から足場までの距離
        scaffold_length: 足場の長さ（mm）
    """
    edge_name: str
    building_length: float
    clearance: float
    scaffold_length: float


def calculate_inside_corner_edge(
    same_face_outer_clearance: float,
    perpendicular_edge_length: float,
    target_clearance: float = 900.0,
    min_clearance: float | None = None,
    eave_overhang: float | None = None,
    span_unit: float = 300.0
) -> tuple[float, float]:
    """
    入隅辺の離隔距離と足場長さを計算する

    入隅の辺は、同じ面の外周辺の離隔距離を基準とし、
    垂直方向の入隅辺の長さを加算した後、300の倍数を引いて
    目標離隔距離に最も近づける。

    Args:
        same_face_outer_clearance: 同じ面の外周辺の離隔距離（mm）
        perpendicular_edge_length: 垂直方向の入隅辺の建物長さ（mm）
        target_clearance: 目標離隔距離（mm）。デフォルトは900mm
        min_clearance: 最小許容離隔距離（mm）。指定がない場合は0
        eave_overhang: 軒の出（mm）。指定された場合、min_clearanceは軒の出+80mm以上となる
        span_unit: スパンの最小単位（mm）。デフォルトは300mm

    Returns:
        tuple[float, float]: (入隅辺の離隔距離（mm）, 入隅辺の足場長さ（mm）)

    計算ロジック:
        1. 最小離隔距離を決定（軒の出がある場合は軒の出+80mm）
        2. 同じ面の外周辺の離隔 + 垂直方向の入隅辺の建物長さ を計算
        3. そこから300の倍数を引いて、目標離隔距離に最も近い離隔を求める
        4. 引いた300の倍数が、この入隅辺の足場長さとなる

    Examples:
        >>> # edge4の計算: edge6の離隔850mm + edge5の建物長さ4000mm
        >>> clearance, scaffold_len = calculate_inside_corner_edge(850, 4000)
        >>> clearance
        950.0
        >>> scaffold_len
        3900.0

        >>> # edge5に軒の出1000mmがある場合
        >>> clearance, scaffold_len = calculate_inside_corner_edge(850, 4000, eave_overhang=1000)
        >>> clearance
        1250.0
        >>> scaffold_len
        3600.0
    """
    # 最小離隔距離の決定
    if eave_overhang is not None:
        # 軒の出がある場合: 軒の出 + 80mm 以上
        eave_min = eave_overhang + 80.0
        if min_clearance is not None:
            min_clearance = max(min_clearance, eave_min)
        else:
            min_clearance = eave_min

    if min_clearance is None:
        # デフォルトは0（制約なし）
        min_clearance = 0.0

    # 基準値を計算: 同じ面の外周辺の離隔 + 垂直方向の入隅辺の建物長さ
    base_value = same_face_outer_clearance + perpendicular_edge_length

    # 300の倍数を引いて、目標離隔距離に最も近い値を探索
    best_clearance = None
    best_subtract_value = None  # 引いた値 = 入隅辺の足場長さ
    min_diff = float('inf')

    # 探索範囲: 0から base_value まで、300の倍数ごとに
    # base_value - (300 * n) の形で探索
    max_multiplier = int(base_value / span_unit) + 1

    for n in range(max_multiplier + 1):
        subtract_value = span_unit * n
        candidate_clearance = base_value - subtract_value

        # 負の値は除外
        if candidate_clearance < 0:
            continue

        # 最小離隔距離を満たしているか確認
        if candidate_clearance >= min_clearance:
            diff = abs(candidate_clearance - target_clearance)
            if diff < min_diff:
                min_diff = diff
                best_clearance = candidate_clearance
                best_subtract_value = subtract_value

    # 候補が見つからない場合（通常はありえないが念のため）
    if best_clearance is None or best_subtract_value is None:
        # 最小離隔距離を満たす最小の値を使用
        best_clearance = max(min_clearance, 0.0)
        best_subtract_value = base_value - best_clearance

    # 入隅辺の足場長さ = 引いた300の倍数
    inside_corner_scaffold_length = best_subtract_value

    return best_clearance, inside_corner_scaffold_length


def calculate_l_shaped_building(
    bounding_width_x: float,
    bounding_height_y: float,
    notch_width: float,
    notch_height: float,
    outer_clearance_x: float,
    outer_clearance_y: float,
    scaffold_total_x: float,
    scaffold_total_y: float,
    target_clearance: float = 900.0,
    edge5_eave_overhang: float | None = None
) -> Dict[str, InsideCornerResult | float]:
    """
    L字型建物の入隅計算を実行する

    外接矩形の足場総長さと外周辺の離隔距離から、
    入隅辺と外周辺それぞれの足場長さと離隔距離を計算する。

    Args:
        bounding_width_x: 外接矩形の幅（X方向、mm）
        bounding_height_y: 外接矩形の高さ（Y方向、mm）
        notch_width: 切り欠き幅（mm）
        notch_height: 切り欠き高さ（mm）
        outer_clearance_x: X方向外周辺の離隔距離（mm）
        outer_clearance_y: Y方向外周辺の離隔距離（mm）
        scaffold_total_x: X方向（東西）の足場総長さ（mm）
        scaffold_total_y: Y方向（南北）の足場総長さ（mm）
        target_clearance: 目標離隔距離（mm）。デフォルトは900mm
        edge5_eave_overhang: edge5の軒の出（mm）。指定された場合、離隔距離は軒の出+80mm以上

    Returns:
        dict: 各辺の計算結果を含む辞書
            - 'edge1': 上辺の計算結果
            - 'edge2': 右辺の計算結果
            - 'edge3': 下辺（右側）の計算結果
            - 'edge4': 入隅縦辺の計算結果
            - 'edge5': 入隅横辺の計算結果
            - 'edge6': 左辺の計算結果

    計算手順:
        1. 外接矩形の足場総長さと外周辺の離隔距離が与えられる
        2. 入隅辺の離隔距離と足場長さを計算:
           - edge4（左面の入隅辺）: edge6の離隔 + edge5の建物長さ - 300の倍数
           - edge5（下面の入隅辺）: edge3の離隔 + edge4の建物長さ - 300の倍数
        3. 面の足場総長さから外周辺の足場長さを逆算:
           - edge3の足場長さ = 南面総長さ - edge5の足場長さ
           - edge6の足場長さ = 西面総長さ - edge4の足場長さ

    Example:
        >>> # L字型建物: 7000mm × 10000mm、切り欠き4000mm × 4000mm
        >>> result = calculate_l_shaped_building(
        ...     bounding_width_x=7000,
        ...     bounding_height_y=10000,
        ...     notch_width=4000,
        ...     notch_height=4000,
        ...     outer_clearance_x=850,
        ...     outer_clearance_y=850,
        ...     scaffold_total_x=8700,
        ...     scaffold_total_y=11700
        ... )
        >>> result['edge4'].clearance
        950.0
        >>> result['edge4'].scaffold_length
        3900.0
    """
    # 各辺の建物長さを計算
    edge1_length = bounding_width_x  # 上辺: 7000mm
    edge2_length = bounding_height_y  # 右辺: 10000mm
    edge3_length = bounding_width_x - notch_width  # 下辺右側: 3000mm
    edge4_length = notch_height  # 入隅縦: 4000mm
    edge5_length = notch_width  # 入隅横: 4000mm
    edge6_length = bounding_height_y - notch_height  # 左辺: 6000mm

    # edge1（上面）の計算
    # 外周辺なので、単純に離隔 + 建物長さ + 離隔
    edge1_scaffold_length = scaffold_total_x
    edge1 = InsideCornerResult(
        edge_name="edge1",
        building_length=edge1_length,
        clearance=outer_clearance_x,
        scaffold_length=edge1_scaffold_length
    )

    # edge2（右面）の計算
    edge2_scaffold_length = scaffold_total_y
    edge2 = InsideCornerResult(
        edge_name="edge2",
        building_length=edge2_length,
        clearance=outer_clearance_y,
        scaffold_length=edge2_scaffold_length
    )

    # edge4（左面の入隅辺）の計算
    # 同じ左面の外周辺edge6の離隔 + 垂直方向のedge5の建物長さ - 300の倍数
    edge4_clearance, edge4_scaffold_length = calculate_inside_corner_edge(
        same_face_outer_clearance=outer_clearance_y,  # edge6の離隔
        perpendicular_edge_length=edge5_length,  # edge5の建物長さ
        target_clearance=target_clearance
    )
    edge4 = InsideCornerResult(
        edge_name="edge4",
        building_length=edge4_length,
        clearance=edge4_clearance,
        scaffold_length=edge4_scaffold_length
    )

    # edge5（下面の入隅辺）の計算
    # 同じ下面の外周辺edge3の離隔 + 垂直方向のedge4の建物長さ - 300の倍数
    edge5_clearance, edge5_scaffold_length = calculate_inside_corner_edge(
        same_face_outer_clearance=outer_clearance_x,  # edge3の離隔
        perpendicular_edge_length=edge4_length,  # edge4の建物長さ
        target_clearance=target_clearance,
        eave_overhang=edge5_eave_overhang
    )
    edge5 = InsideCornerResult(
        edge_name="edge5",
        building_length=edge5_length,
        clearance=edge5_clearance,
        scaffold_length=edge5_scaffold_length
    )

    # edge3（下面の外周辺）の足場長さを逆算
    # 南面（下面）の足場総長さ = edge3の足場長さ + edge5の足場長さ
    edge3_scaffold_length = scaffold_total_x - edge5_scaffold_length
    edge3 = InsideCornerResult(
        edge_name="edge3",
        building_length=edge3_length,
        clearance=outer_clearance_x,  # edge3はedge2側の離隔を使用
        scaffold_length=edge3_scaffold_length
    )

    # edge6（左面の外周辺）の足場長さを逆算
    # 西面（左面）の足場総長さ = edge4の足場長さ + edge6の足場長さ
    edge6_scaffold_length = scaffold_total_y - edge4_scaffold_length
    edge6 = InsideCornerResult(
        edge_name="edge6",
        building_length=edge6_length,
        clearance=outer_clearance_y,  # edge6はedge3側の離隔を使用
        scaffold_length=edge6_scaffold_length
    )

    return {
        'edge1': edge1,
        'edge2': edge2,
        'edge3': edge3,
        'edge4': edge4,
        'edge5': edge5,
        'edge6': edge6
    }


if __name__ == "__main__":
    # テスト実行
    print("=== L字型建物の入隅計算テスト ===\n")

    # L字型建物: 7000mm × 10000mm、切り欠き4000mm × 4000mm
    print("建物形状: L字型")
    print("外接矩形: 7000mm × 10000mm")
    print("切り欠き: 4000mm × 4000mm\n")

    # 外接矩形の足場計算結果（既に計算済みの値）
    outer_clearance_x = 850.0
    outer_clearance_y = 850.0
    scaffold_total_x = 8700.0
    scaffold_total_y = 11700.0

    print(f"外接矩形の計算結果:")
    print(f"  X方向: 離隔{outer_clearance_x}mm、足場総長さ{scaffold_total_x}mm")
    print(f"  Y方向: 離隔{outer_clearance_y}mm、足場総長さ{scaffold_total_y}mm\n")

    # 入隅計算実行
    result = calculate_l_shaped_building(
        bounding_width_x=7000,
        bounding_height_y=10000,
        notch_width=4000,
        notch_height=4000,
        outer_clearance_x=outer_clearance_x,
        outer_clearance_y=outer_clearance_y,
        scaffold_total_x=scaffold_total_x,
        scaffold_total_y=scaffold_total_y
    )

    print("各辺の計算結果:")
    for edge_name in ['edge1', 'edge2', 'edge3', 'edge4', 'edge5', 'edge6']:
        edge = result[edge_name]
        print(f"\n{edge.edge_name}:")
        print(f"  建物長さ: {edge.building_length}mm")
        print(f"  離隔距離: {edge.clearance}mm")
        print(f"  足場長さ: {edge.scaffold_length}mm")

    # edge5に軒の出1000mmがある場合のテスト
    print("\n\n=== edge5に軒の出1000mmがある場合 ===\n")
    result_with_eave = calculate_l_shaped_building(
        bounding_width_x=7000,
        bounding_height_y=10000,
        notch_width=4000,
        notch_height=4000,
        outer_clearance_x=outer_clearance_x,
        outer_clearance_y=outer_clearance_y,
        scaffold_total_x=scaffold_total_x,
        scaffold_total_y=scaffold_total_y,
        edge5_eave_overhang=1000
    )

    print(f"edge5:")
    print(f"  建物長さ: {result_with_eave['edge5'].building_length}mm")
    print(f"  離隔距離: {result_with_eave['edge5'].clearance}mm (最小1080mm以上)")
    print(f"  足場長さ: {result_with_eave['edge5'].scaffold_length}mm")
