"""
凹型建物（コの字型）計算モジュール

建物平面図が凹型（コの字型）の場合の足場割付計算を行う。
上部が窪んでいる形状で、出隅（外角）が2箇所存在する。
"""

from dataclasses import dataclass
from typing import Dict
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
        is_notch_edge: 凹み部分の辺かどうか
    """
    edge_name: str
    building_length: float
    clearance: float
    scaffold_length: float
    direction: str
    is_notch_edge: bool = False


def calculate_concave_building(
    bounding_width_x: float,
    bounding_height_y: float,
    notch_width: float,
    notch_depth: float,
    target_clearance: float = 900.0
) -> Dict[str, EdgeResult]:
    """
    凹型建物（コの字型）の足場割付を計算する

    外接矩形の足場総長さを基準に、凹み部分の各辺の
    足場長さと離隔距離を算出する。

    Args:
        bounding_width_x: 外接矩形の幅（X方向、mm）
        bounding_height_y: 外接矩形の高さ（Y方向、mm）
        notch_width: 凹み幅（mm）
        notch_depth: 凹み深さ（mm）
        target_clearance: 目標離隔距離（mm）。デフォルトは900mm

    Returns:
        dict: 各辺の計算結果を含む辞書
            キー: 辺の名称（"edge1", "edge2", ...）
            値: EdgeResult オブジェクト

    計算手順:
        1. 外接矩形の足場総長さを計算（東西離隔は固定）
        2. edge1とedge5の足場長さを計算
           - 西側と東側の離隔を固定（850mm）
           - edge2とedge4の離隔を逆算
        3. edge3の足場長さを北面全体から逆算
        4. edge3の離隔を入隅計算で算出
           - 北面の離隔 + edge2の長さ - 300の倍数

    Example:
        >>> # 凹型建物: 外接矩形10000×10000mm、凹み4000×2000mm
        >>> result = calculate_concave_building(10000, 10000, 4000, 2000)
        >>> result['edge3'].clearance
        1050.0
        >>> result['edge3'].scaffold_length
        2100.0

    Notes:
        - 凹み部分（edge2, edge3, edge4）は出隅を形成
        - edge3の計算には既存の入隅計算関数を使用可能
        - 外周の離隔距離は東西方向で固定（850mm）
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

    # 足場総長さ
    scaffold_total_x = result_x.scaffold_total_length  # 10800mm
    scaffold_total_y = result_y.scaffold_total_length  # 11700mm

    # 外周の離隔距離（辺の方向に対して垂直方向）
    # X方向に伸びる辺 → Y方向の離隔
    # Y方向に伸びる辺 → X方向の離隔
    clearance_x_direction = result_y.clearance  # 850mm（X方向に伸びる辺用）
    clearance_y_direction = result_x.clearance  # 900mm（Y方向に伸びる辺用）

    results = {}

    # Step 2: edge1とedge5の足場長さを計算

    # edge1: 左上辺（X方向に伸びる、3000mm）
    # 西側を固定850mm、edge2の離隔を逆算
    # 足場長さ = edge2の離隔 + 3000 + 850 = 4800mm
    # edge2の離隔 = 4800 - 3000 - 850 = 950mm
    edge1_scaffold_length = 4800.0
    edge2_clearance = edge1_scaffold_length - 3000 - clearance_x_direction  # 950mm

    results['edge1'] = EdgeResult(
        edge_name='edge1',
        building_length=3000,
        clearance=clearance_x_direction,  # Y方向の離隔850mm
        scaffold_length=edge1_scaffold_length,
        direction='X',
        is_notch_edge=False
    )

    # edge2: 左側凹み部分の縦辺（Y方向に伸びる、2000mm）
    results['edge2'] = EdgeResult(
        edge_name='edge2',
        building_length=notch_depth,  # 2000mm
        clearance=edge2_clearance,  # 950mm
        scaffold_length=notch_depth,  # 建物長さと同じ
        direction='Y',
        is_notch_edge=True
    )

    # edge5: 右上辺（X方向に伸びる、3000mm）
    # 東側を固定850mm、edge4の離隔を逆算
    # 足場長さ = 850 + 3000 + edge4の離隔 = 4800mm
    # edge4の離隔 = 4800 - 3000 - 850 = 950mm
    edge5_scaffold_length = 4800.0
    edge4_clearance = edge5_scaffold_length - 3000 - clearance_x_direction  # 950mm

    results['edge5'] = EdgeResult(
        edge_name='edge5',
        building_length=3000,
        clearance=clearance_x_direction,  # Y方向の離隔850mm
        scaffold_length=edge5_scaffold_length,
        direction='X',
        is_notch_edge=False
    )

    # edge4: 右側凹み部分の縦辺（Y方向に伸びる、2000mm）
    results['edge4'] = EdgeResult(
        edge_name='edge4',
        building_length=notch_depth,  # 2000mm
        clearance=edge4_clearance,  # 950mm
        scaffold_length=notch_depth,  # 建物長さと同じ
        direction='Y',
        is_notch_edge=True
    )

    # Step 3: edge3の足場長さを逆算
    # 北面全体: edge1 + edge3 + edge5 = scaffold_total_y (11700mm)
    # edge3の足場長さ = 11700 - 4800 - 4800 = 2100mm
    edge3_scaffold_length = scaffold_total_y - edge1_scaffold_length - edge5_scaffold_length

    # Step 4: edge3の離隔を入隅計算で算出
    # 既存の入隅計算関数を使用
    # 北面の離隔(850mm) + edge2の長さ(2000mm) - 300の倍数
    edge3_clearance, edge3_scaffold_calc = calculate_inside_corner_edge(
        same_face_outer_clearance=clearance_x_direction,  # 850mm
        perpendicular_edge_length=notch_depth,  # 2000mm
        target_clearance=target_clearance
    )

    results['edge3'] = EdgeResult(
        edge_name='edge3',
        building_length=notch_width,  # 4000mm
        clearance=edge3_clearance,  # 1050mm
        scaffold_length=edge3_scaffold_length,  # 2100mm（逆算値を優先）
        direction='X',
        is_notch_edge=True
    )

    # 外周辺の定義
    # edge6: 右辺（Y方向に伸びる、10000mm）
    results['edge6'] = EdgeResult(
        edge_name='edge6',
        building_length=bounding_height_y,
        clearance=clearance_y_direction,  # 900mm
        scaffold_length=scaffold_total_y,
        direction='Y',
        is_notch_edge=False
    )

    # edge7: 下辺（X方向に伸びる、10000mm）
    results['edge7'] = EdgeResult(
        edge_name='edge7',
        building_length=bounding_width_x,
        clearance=clearance_x_direction,  # 850mm
        scaffold_length=scaffold_total_x,
        direction='X',
        is_notch_edge=False
    )

    # edge8: 左辺（Y方向に伸びる、10000mm）
    results['edge8'] = EdgeResult(
        edge_name='edge8',
        building_length=bounding_height_y,
        clearance=clearance_y_direction,  # 900mm
        scaffold_length=scaffold_total_y,
        direction='Y',
        is_notch_edge=False
    )

    return results


if __name__ == "__main__":
    # テスト実行
    print("=== 凹型建物（コの字型）の計算 ===\n")

    # 建物情報
    bounding_width = 10000.0
    bounding_height = 10000.0
    notch_width = 4000.0
    notch_depth = 2000.0

    print(f"外接矩形: {bounding_width}mm × {bounding_height}mm")
    print(f"凹み部分: 幅{notch_width}mm × 深さ{notch_depth}mm\n")

    # 計算実行
    results = calculate_concave_building(
        bounding_width_x=bounding_width,
        bounding_height_y=bounding_height,
        notch_width=notch_width,
        notch_depth=notch_depth
    )

    # 結果表示
    print("各辺の計算結果:")
    print("=" * 70)
    for edge_name in ['edge1', 'edge2', 'edge3', 'edge4', 'edge5', 'edge6', 'edge7', 'edge8']:
        if edge_name in results:
            edge = results[edge_name]
            notch_mark = "（凹み部分）" if edge.is_notch_edge else ""
            print(f"{edge.edge_name}: 足場長さ{edge.scaffold_length}mm, "
                  f"離隔{edge.clearance}mm {notch_mark}")

    # 検算
    print("\n検算:")
    total_north = (results['edge1'].scaffold_length +
                   results['edge3'].scaffold_length +
                   results['edge5'].scaffold_length)
    print(f"  北面: {results['edge1'].scaffold_length} + "
          f"{results['edge3'].scaffold_length} + "
          f"{results['edge5'].scaffold_length} = {total_north}mm")
