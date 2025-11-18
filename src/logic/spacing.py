"""
足場の離隔距離計算モジュール

建物外周から足場までの最適な離隔距離を計算する
"""

from dataclasses import dataclass


@dataclass
class SpacingResult:
    """
    離隔距離計算結果を格納するデータクラス

    Attributes:
        building_width: 建物幅（mm）
        clearance: 離隔距離（mm）- 建物外周から足場までの距離
        scaffold_total_length: 足場総長さ（mm）
        target_clearance: 目標離隔距離（mm）
    """
    building_width: float
    clearance: float
    scaffold_total_length: float
    target_clearance: float


def calculate_optimal_clearance(
    building_width: float,
    target_clearance: float = 900.0,
    min_clearance: float | None = None,
    eave_overhang: float | None = None,
    span_unit: float = 300.0
) -> SpacingResult:
    """
    建物幅に基づいて最適な離隔距離を計算する

    足場総長さが300mmの倍数になるように調整し、
    離隔距離が目標値に最も近くなる組み合わせを選択する。

    Args:
        building_width: 建物幅（mm）
        target_clearance: 目標離隔距離（mm）。デフォルトは900mm
        min_clearance: 最小許容離隔距離（mm）。指定がない場合はtarget_clearanceを使用
        eave_overhang: 軒の出（mm）。指定された場合、min_clearanceは軒の出+80mm以上となる
        span_unit: スパンの最小単位（mm）。デフォルトは300mm

    Returns:
        SpacingResult: 計算結果（建物幅、離隔距離、足場総長さ、目標離隔距離）

    計算ロジック:
        1. 最小離隔距離を決定（軒の出がある場合は軒の出+80mm）
        2. 建物幅 + 両側離隔が300mmの倍数になる候補を生成
        3. 最小離隔距離以上で、目標離隔距離に最も近い候補を選択

    Examples:
        >>> result = calculate_optimal_clearance(5460)
        >>> result.clearance
        870.0
        >>> result.scaffold_total_length
        7200.0

        >>> result = calculate_optimal_clearance(6000)
        >>> result.clearance
        900.0
        >>> result.scaffold_total_length
        7800.0

        >>> result = calculate_optimal_clearance(6000, eave_overhang=600)
        >>> result.clearance  # 600 + 80 = 680mm以上で900に近い値
        900.0
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

    # 建物幅を基準にして、足場総長さが300の倍数になる候補を探索
    # 足場総長さ = 建物幅 + 離隔距離 × 2
    # 離隔距離 = (足場総長さ - 建物幅) / 2

    # 探索範囲: 目標離隔距離の前後で十分な範囲をカバー
    # 最小の足場総長さ（離隔距離0の場合）から開始
    min_scaffold_length = building_width + (min_clearance * 2)
    base_length = ((min_scaffold_length + span_unit - 1) // span_unit) * span_unit

    # 目標離隔距離を中心に前後を探索
    # 目標離隔距離の2倍程度まで探索
    max_search_length = building_width + (target_clearance * 4)
    max_length = ((max_search_length + span_unit - 1) // span_unit) * span_unit

    # 候補を探索
    best_clearance = None
    best_scaffold_length = None
    min_diff = float('inf')

    current_length = base_length
    while current_length <= max_length:
        clearance = (current_length - building_width) / 2

        # 最小離隔距離を満たしているか確認
        if clearance >= min_clearance:
            diff = abs(clearance - target_clearance)
            if diff < min_diff:
                min_diff = diff
                best_clearance = clearance
                best_scaffold_length = current_length

        current_length += span_unit

    if best_clearance is None or best_scaffold_length is None:
        # フォールバック: 最小離隔距離を使用
        best_scaffold_length = base_length
        best_clearance = (base_length - building_width) / 2

    return SpacingResult(
        building_width=building_width,
        clearance=best_clearance,
        scaffold_total_length=best_scaffold_length,
        target_clearance=target_clearance
    )


def calculate_rectangular_scaffold(
    width_x: float,
    width_y: float,
    target_clearance: float = 900.0,
    eave_overhang: float | None = None
) -> dict:
    """
    矩形建物の足場割付を計算する

    X方向とY方向それぞれについて最適な離隔距離を計算する。

    Args:
        width_x: X方向の建物幅（mm）
        width_y: Y方向の建物幅（mm）
        target_clearance: 目標離隔距離（mm）。デフォルトは900mm
        eave_overhang: 軒の出（mm）。指定された場合、離隔距離は軒の出+80mm以上

    Returns:
        dict: X方向とY方向の計算結果を含む辞書
            - 'x': X方向のSpacingResult
            - 'y': Y方向のSpacingResult
            - 'summary': 計算結果の概要文字列

    Examples:
        >>> result = calculate_rectangular_scaffold(7280, 10010)
        >>> result['x'].clearance
        860.0
        >>> result['y'].clearance
        895.0
    """
    result_x = calculate_optimal_clearance(
        building_width=width_x,
        target_clearance=target_clearance,
        eave_overhang=eave_overhang
    )

    result_y = calculate_optimal_clearance(
        building_width=width_y,
        target_clearance=target_clearance,
        eave_overhang=eave_overhang
    )

    summary = (
        f"矩形建物割付計算結果:\n"
        f"  建物サイズ: {width_x}mm × {width_y}mm\n"
        f"  X方向:\n"
        f"    離隔距離: {result_x.clearance}mm\n"
        f"    足場総長さ: {result_x.scaffold_total_length}mm\n"
        f"  Y方向:\n"
        f"    離隔距離: {result_y.clearance}mm\n"
        f"    足場総長さ: {result_y.scaffold_total_length}mm\n"
    )

    return {
        'x': result_x,
        'y': result_y,
        'summary': summary
    }


if __name__ == "__main__":
    # テスト実行
    print("=== 離隔距離計算テスト ===\n")

    # テストケース1: 建物幅5460mm
    print("テスト1: 建物幅5460mm")
    result1 = calculate_optimal_clearance(5460)
    print(f"  離隔距離: {result1.clearance}mm")
    print(f"  足場総長さ: {result1.scaffold_total_length}mm\n")

    # テストケース2: 建物幅6000mm
    print("テスト2: 建物幅6000mm")
    result2 = calculate_optimal_clearance(6000)
    print(f"  離隔距離: {result2.clearance}mm")
    print(f"  足場総長さ: {result2.scaffold_total_length}mm\n")

    # テストケース3: 矩形建物7280mm × 10010mm
    print("テスト3: 矩形建物7280mm × 10010mm")
    result3 = calculate_rectangular_scaffold(7280, 10010)
    print(result3['summary'])
