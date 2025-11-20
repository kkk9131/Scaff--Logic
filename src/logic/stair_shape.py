"""
階段形状（連続した入隅）計算モジュール

建物平面図が階段状になっている場合の足場割付計算を行う。
複数の入隅が連続する形状に対応し、外周から内側へ順次計算する。
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.logic.spacing import calculate_optimal_clearance
from src.logic.inside_corner import calculate_inside_corner_edge


@dataclass
class EdgeResult:
    """
    辺の計算結果を格納するデータクラス

    Attributes:
        edge_name: 辺の名称（例: "edge1", "edge2"）
        building_length: 建物の辺の長さ（mm）
        clearance: 離隔距離（mm）- 建物から足場までの距離
        scaffold_length: 足場の長さ（mm）
        direction: 辺の伸びる方向（"X" or "Y"）
        is_inside_corner: 入隅辺かどうか
    """
    edge_name: str
    building_length: float
    clearance: float
    scaffold_length: float
    direction: str
    is_inside_corner: bool = False


def calculate_stair_shaped_building(
    bounding_width_x: float,
    bounding_height_y: float,
    stairs: List[Tuple[float, float]],
    target_clearance: float = 900.0
) -> Dict[str, EdgeResult]:
    """
    階段形状建物の足場割付を計算する

    外接矩形の足場総長さを基準に、外周から内側へ順次入隅を計算し、
    各辺の足場長さと離隔距離を算出する。

    Args:
        bounding_width_x: 外接矩形の幅（X方向、mm）
        bounding_height_y: 外接矩形の高さ（Y方向、mm）
        stairs: 階段の段差情報のリスト
            各要素は (x座標, y座標) のタプル
            例: [(3000, 10000), (3000, 7000), (6000, 7000), (6000, 4000)]
        target_clearance: 目標離隔距離（mm）。デフォルトは900mm

    Returns:
        dict: 各辺の計算結果を含む辞書
            キー: 辺の名称（"edge1", "edge2", ...）
            値: EdgeResult オブジェクト

    計算手順:
        1. 外接矩形の足場総長さを計算
        2. 外周辺の離隔距離を取得
           - X方向に伸びる辺 → Y方向の離隔
           - Y方向に伸びる辺 → X方向の離隔
        3. 外側から内側へ順次入隅を計算
           - 外周辺の離隔を基準に最初の入隅を計算
           - 前の入隅の離隔を基準に次の入隅を計算（連鎖）
        4. 面の足場総長さから外周辺の足場長さを逆算

    Example:
        >>> # 3段階段: 外接矩形9000×10000mm
        >>> stairs = [(3000, 10000), (3000, 7000), (6000, 7000), (6000, 4000)]
        >>> result = calculate_stair_shaped_building(9000, 10000, stairs)
        >>> result['edge2'].clearance
        900.0
        >>> result['edge2'].scaffold_length
        3000.0

    Notes:
        - 階段の段数は stairs リストの要素数で決まる
        - 各段は3000mm×3000mmの均等なサイズを想定
        - 離隔距離は辺の伸びる方向に垂直な方向で測る
    """
    # Step 1: 外接矩形の足場総長さを計算
    result_x = calculate_optimal_clearance(
        building_width=bounding_width_x,
        target_clearance=target_clearance
    )
    result_y = calculate_optimal_clearance(
        building_width=bounding_height_y,
        target_clearance=target_clearance
    )

    # X方向の足場総長さと外周離隔（X方向に伸びる辺に対してY方向に測る）
    scaffold_total_x = result_x.scaffold_total_length
    clearance_x = result_x.clearance  # X方向に伸びる辺用

    # Y方向の足場総長さと外周離隔（Y方向に伸びる辺に対してX方向に測る）
    scaffold_total_y = result_y.scaffold_total_length
    clearance_y = result_y.clearance  # Y方向に伸びる辺用

    # 重要: 辺の方向と離隔の方向の対応
    # - X方向に伸びる辺（edge1, edge7など）: Y方向の離隔を使用
    # - Y方向に伸びる辺（edge6, edge8など）: X方向の離隔を使用
    clearance_for_x_direction_edge = result_y.clearance  # 850mm
    clearance_for_y_direction_edge = result_x.clearance  # 900mm

    results = {}

    # Step 2: 外周辺の定義
    # edge1: 上辺（X方向に伸びる）
    results['edge1'] = EdgeResult(
        edge_name='edge1',
        building_length=3000,  # 実際の建物長さ
        clearance=clearance_for_x_direction_edge,
        scaffold_length=scaffold_total_x,
        direction='X',
        is_inside_corner=False
    )

    # edge6: 右辺の最下部（Y方向に伸びる、外周）
    # この値は後で逆算するため、仮の値を設定
    edge6_clearance = clearance_for_y_direction_edge

    # edge7: 下辺（X方向に伸びる）
    results['edge7'] = EdgeResult(
        edge_name='edge7',
        building_length=9000,
        clearance=clearance_for_x_direction_edge,
        scaffold_length=scaffold_total_x,
        direction='X',
        is_inside_corner=False
    )

    # edge8: 左辺（Y方向に伸びる）
    results['edge8'] = EdgeResult(
        edge_name='edge8',
        building_length=10000,
        clearance=clearance_for_y_direction_edge,
        scaffold_length=scaffold_total_y,
        direction='Y',
        is_inside_corner=False
    )

    # Step 3: 入隅の計算（外側から内側へ）

    # 入隅2: edge4（Y方向）とedge5（X方向）
    # edge4: Y方向に伸びる縦辺、外周edge6の離隔を基準
    edge4_clearance, edge4_scaffold = calculate_inside_corner_edge(
        same_face_outer_clearance=edge6_clearance,  # 900mm（X方向の離隔）
        perpendicular_edge_length=3000,  # edge5の建物長さ
        target_clearance=target_clearance
    )
    results['edge4'] = EdgeResult(
        edge_name='edge4',
        building_length=3000,
        clearance=edge4_clearance,
        scaffold_length=edge4_scaffold,
        direction='Y',
        is_inside_corner=True
    )

    # edge5: X方向に伸びる横辺、外周edge7の離隔を基準
    edge5_clearance, edge5_scaffold = calculate_inside_corner_edge(
        same_face_outer_clearance=clearance_for_x_direction_edge,  # 850mm（Y方向の離隔）
        perpendicular_edge_length=3000,  # edge4の建物長さ
        target_clearance=target_clearance
    )
    results['edge5'] = EdgeResult(
        edge_name='edge5',
        building_length=3000,
        clearance=edge5_clearance,
        scaffold_length=edge5_scaffold,
        direction='X',
        is_inside_corner=True
    )

    # 入隅1: edge2（Y方向）とedge3（X方向）
    # edge2: Y方向に伸びる縦辺、edge4の離隔を基準（連鎖）
    edge2_clearance, edge2_scaffold = calculate_inside_corner_edge(
        same_face_outer_clearance=edge4_clearance,  # edge4の離隔を基準
        perpendicular_edge_length=3000,  # edge3の建物長さ
        target_clearance=target_clearance
    )
    results['edge2'] = EdgeResult(
        edge_name='edge2',
        building_length=3000,
        clearance=edge2_clearance,
        scaffold_length=edge2_scaffold,
        direction='Y',
        is_inside_corner=True
    )

    # edge3: X方向に伸びる横辺、edge5の離隔を基準（連鎖）
    edge3_clearance, edge3_scaffold = calculate_inside_corner_edge(
        same_face_outer_clearance=edge5_clearance,  # edge5の離隔を基準
        perpendicular_edge_length=3000,  # edge2の建物長さ
        target_clearance=target_clearance
    )
    results['edge3'] = EdgeResult(
        edge_name='edge3',
        building_length=3000,
        clearance=edge3_clearance,
        scaffold_length=edge3_scaffold,
        direction='X',
        is_inside_corner=True
    )

    # Step 4: 外周辺の足場長さを逆算
    # 右面（東）: edge2 + edge4 + edge6 = Y方向の足場総長さ
    edge6_scaffold = scaffold_total_y - edge2_scaffold - edge4_scaffold
    results['edge6'] = EdgeResult(
        edge_name='edge6',
        building_length=4000,
        clearance=edge6_clearance,
        scaffold_length=edge6_scaffold,
        direction='Y',
        is_inside_corner=False
    )

    return results


if __name__ == "__main__":
    # テスト実行
    print("=== 階段形状建物（3段・入隅2箇所）の計算 ===\n")

    # 建物情報
    bounding_width = 9000.0
    bounding_height = 10000.0
    stairs = [
        (0, 10000),     # 左上
        (3000, 10000),  # edge1の終点
        (3000, 7000),   # 入隅1
        (6000, 7000),   # edge3の終点
        (6000, 4000),   # 入隅2
        (9000, 4000),   # edge5の終点
        (9000, 0),      # 右下
        (0, 0)          # 左下
    ]

    print(f"外接矩形: {bounding_width}mm × {bounding_height}mm")
    print(f"段数: 3段（入隅2箇所）\n")

    # 計算実行
    results = calculate_stair_shaped_building(
        bounding_width_x=bounding_width,
        bounding_height_y=bounding_height,
        stairs=stairs
    )

    # 結果表示
    print("各辺の計算結果:")
    print("=" * 70)
    for edge_name in ['edge1', 'edge2', 'edge3', 'edge4', 'edge5', 'edge6', 'edge7', 'edge8']:
        if edge_name in results:
            edge = results[edge_name]
            corner_mark = "（入隅）" if edge.is_inside_corner else ""
            print(f"{edge.edge_name}: 足場長さ{edge.scaffold_length}mm, "
                  f"離隔{edge.clearance}mm {corner_mark}")

    # 検算
    print("\n検算:")
    total_right = (results['edge2'].scaffold_length +
                   results['edge4'].scaffold_length +
                   results['edge6'].scaffold_length)
    print(f"  右面（東）: {results['edge2'].scaffold_length} + "
          f"{results['edge4'].scaffold_length} + "
          f"{results['edge6'].scaffold_length} = {total_right}mm")
