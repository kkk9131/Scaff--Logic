"""
応用スパン寸法に対応した離隔距離計算モジュール

従来の300mm倍数（1800, 1500, 1200, 900, 600）に加えて、
応用スパン寸法（355mm, 150mm）を使用した離隔距離計算を行う。
これにより、複数の制約を同時に満たすことが可能になる。
"""

import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List
import math

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.logic.spacing import calculate_optimal_clearance


@dataclass
class AdvancedSpacingResult:
    """
    応用スパン寸法を考慮した離隔距離計算結果

    Attributes:
        building_dimension: 建物寸法（mm）
        clearance: 離隔距離（mm）
        total_scaffold_length: 足場総長さ（mm）
        span_355_count: 355mmスパンの使用数
        span_150_count: 150mmスパンの使用数
        adjustment_amount: 従来計算からの調整量（mm）
        constraints_satisfied: 制約を満たしているか
        calculation_notes: 計算の説明
    """
    building_dimension: float
    clearance: float
    total_scaffold_length: float
    span_355_count: int
    span_150_count: int
    adjustment_amount: float
    constraints_satisfied: bool
    calculation_notes: str


def check_adjacent_edge_constraint(
    adjacent_clearances: List[float],
    min_clearance: float = 450.0,
    max_clearance: float = 700.0
) -> bool:
    """
    隣接edgeの離隔値が355mm使用条件を満たすかチェック

    355mmスパンは、隣接する全てのedgeの離隔値が
    450〜700mmの範囲内にある場合のみ使用可能。

    Args:
        adjacent_clearances: 隣接edgeの離隔値リスト（mm）
        min_clearance: 最小許容離隔（mm、デフォルト450mm）
        max_clearance: 最大許容離隔（mm、デフォルト700mm）

    Returns:
        bool: 全ての隣接edgeが条件を満たす場合True

    Example:
        >>> check_adjacent_edge_constraint([600.0, 650.0])
        True
        >>> check_adjacent_edge_constraint([850.0, 900.0])
        False
    """
    if not adjacent_clearances:
        return False

    # 全ての隣接edgeが範囲内かチェック
    return all(
        min_clearance <= clearance <= max_clearance
        for clearance in adjacent_clearances
    )


def calculate_with_advanced_spans(
    building_dimension: float,
    target_clearance: float = 900.0,
    min_clearance: Optional[float] = None,
    max_clearance: Optional[float] = None,
    adjacent_clearances: Optional[List[float]] = None,
    eave_overhang: Optional[float] = None,
    span_unit: float = 300.0
) -> AdvancedSpacingResult:
    """
    応用スパン寸法を考慮した離隔距離を計算

    従来の300mm倍数に加えて、355mmと150mmの応用スパンを試行し、
    制約を満たす最適な組み合わせを選択する。

    計算の流れ:
        1. 従来計算（300mm倍数のみ）を実行
        2. 各種制約（最小離隔、最大離隔）をチェック
        3. 制約違反がある場合、応用スパンを試行:
           a. 隣接edgeの離隔値が450〜700mmなら355mm優先
           b. そうでなければ150mmのみ
           c. 併用も試行
        4. 最適な組み合わせを選択

    Args:
        building_dimension: 建物寸法（mm）
        target_clearance: 目標離隔距離（mm、デフォルト900mm）
        min_clearance: 最小許容離隔（mm）
            - 軒の出がある場合: eave_overhang + 80mm
            - 境界線がある場合: boundary_distance - 60mm（最大離隔）
        max_clearance: 最大許容離隔（mm）
            - 境界線制約がある場合に使用
        adjacent_clearances: 隣接edgeの離隔値リスト（mm）
            - 355mm使用判定に使用
            - 矩形の場合は直交する方向の離隔値
        eave_overhang: 軒の出（mm）
            - 指定された場合、min_clearanceは軒の出+80mm以上
        span_unit: スパン基本単位（mm、デフォルト300mm）

    Returns:
        AdvancedSpacingResult: 応用スパンを考慮した計算結果

    Example:
        >>> # 境界線制約で従来計算では解なし
        >>> result = calculate_with_advanced_spans(
        ...     building_dimension=10000.0,
        ...     min_clearance=880.0,  # 軒の出800 + 80
        ...     max_clearance=990.0,  # 境界1050 - 60
        ...     adjacent_clearances=[880.0]  # 東面離隔
        ... )
        >>> # 150mmを追加して制約を満たす
        >>> result.span_150_count
        1
        >>> result.constraints_satisfied
        True
    """
    # Step 1: 従来計算（300mm倍数のみ）
    # 注意: ベースライン取得のため、制約なしで計算
    normal_result = calculate_optimal_clearance(
        building_width=building_dimension,
        target_clearance=target_clearance,
        min_clearance=0.0,  # 制約なしでベースラインを取得
        eave_overhang=None  # 制約なし
    )

    # 制約の確認
    effective_min = min_clearance if min_clearance is not None else 0.0
    effective_max = max_clearance if max_clearance is not None else float('inf')

    # Step 2: 制約チェック
    # 従来計算の結果が制約を満たすかチェック
    constraints_ok = (
        effective_min <= normal_result.clearance <= effective_max
    )

    if constraints_ok:
        # 制約を満たしている場合、従来計算をそのまま返す
        return AdvancedSpacingResult(
            building_dimension=building_dimension,
            clearance=normal_result.clearance,
            total_scaffold_length=normal_result.scaffold_total_length,
            span_355_count=0,
            span_150_count=0,
            adjustment_amount=0.0,
            constraints_satisfied=True,
            calculation_notes=(
                f"従来計算で制約を満たしています。"
                f"離隔: {normal_result.clearance}mm、"
                f"総長: {normal_result.scaffold_total_length}mm"
            )
        )

    # Step 3: 制約違反 → 応用スパンを試行
    # 隣接edgeの制約チェック（355mm使用可能か）
    can_use_355 = False
    if adjacent_clearances is not None:
        can_use_355 = check_adjacent_edge_constraint(adjacent_clearances)

    # 試行する組み合わせのリスト
    # (355mm数, 150mm数, 優先度)
    trials = []

    if can_use_355:
        # 隣接edge制約内: 355mm優先
        trials = [
            (1, 0, 1),  # 355mm × 1
            (2, 0, 2),  # 355mm × 2
            (0, 1, 3),  # 150mm × 1
            (1, 1, 4),  # 355mm × 1 + 150mm × 1
            (2, 1, 5),  # 355mm × 2 + 150mm × 1
        ]
    else:
        # 隣接edge制約外: 150mmのみ
        trials = [
            (0, 1, 1),  # 150mm × 1
        ]

    # 各組み合わせを試行
    best_result = None
    best_priority = float('inf')

    for span_355, span_150, priority in trials:
        # 調整量を計算
        adjustment = span_355 * 355 + span_150 * 150

        # 新しい足場総長さ
        new_total_length = normal_result.scaffold_total_length + adjustment

        # 新しい離隔距離（均等配分）
        new_clearance = (new_total_length - building_dimension) / 2

        # 制約チェック
        if effective_min <= new_clearance <= effective_max:
            # 制約を満たす → 優先度が高い方を採用
            if priority < best_priority:
                best_priority = priority
                best_result = AdvancedSpacingResult(
                    building_dimension=building_dimension,
                    clearance=new_clearance,
                    total_scaffold_length=new_total_length,
                    span_355_count=span_355,
                    span_150_count=span_150,
                    adjustment_amount=adjustment,
                    constraints_satisfied=True,
                    calculation_notes=(
                        f"応用スパン使用: 355mm×{span_355}, 150mm×{span_150}。"
                        f"調整量: +{adjustment}mm、"
                        f"新離隔: {new_clearance}mm、"
                        f"新総長: {new_total_length}mm"
                    )
                )

    # Step 4: 応用スパンでも解が見つからない場合
    if best_result is None:
        # 300mm増減を試行（従来の方法）
        # とりあえず+300mmを試す
        adjustment_300 = span_unit
        new_total_300 = normal_result.scaffold_total_length + adjustment_300
        new_clearance_300 = (new_total_300 - building_dimension) / 2

        constraints_ok_300 = (
            effective_min <= new_clearance_300 <= effective_max
        )

        return AdvancedSpacingResult(
            building_dimension=building_dimension,
            clearance=new_clearance_300,
            total_scaffold_length=new_total_300,
            span_355_count=0,
            span_150_count=0,
            adjustment_amount=adjustment_300,
            constraints_satisfied=constraints_ok_300,
            calculation_notes=(
                f"応用スパンでは解なし。300mm調整を実施。"
                f"調整量: +{adjustment_300}mm、"
                f"新離隔: {new_clearance_300}mm、"
                f"制約: {'満たす' if constraints_ok_300 else '満たさない'}"
            )
        )

    return best_result


if __name__ == "__main__":
    print("=== 応用スパン寸法に対応した離隔距離計算 ===\n")

    # テスト1: 従来計算で制約を満たすケース
    print("テスト1: 従来計算で制約を満たすケース")
    print("  建物: 10000mm、制約なし")
    result1 = calculate_with_advanced_spans(
        building_dimension=10000.0,
        target_clearance=900.0
    )
    print(f"  離隔: {result1.clearance}mm")
    print(f"  総長: {result1.total_scaffold_length}mm")
    print(f"  355mm使用: {result1.span_355_count}個")
    print(f"  150mm使用: {result1.span_150_count}個")
    print(f"  制約満たす: {result1.constraints_satisfied}")
    print(f"  説明: {result1.calculation_notes}")
    print()

    # テスト2: 軒の出と境界線の複合制約（150mm必要）
    print("テスト2: 軒の出と境界線の複合制約")
    print("  建物: 10000mm")
    print("  軒の出: 800mm → 最小離隔880mm")
    print("  境界線: 1050mm → 最大離隔990mm")
    print("  隣接edge離隔: 880mm（範囲外）")
    result2 = calculate_with_advanced_spans(
        building_dimension=10000.0,
        min_clearance=880.0,  # 800 + 80
        max_clearance=990.0,  # 1050 - 60
        adjacent_clearances=[880.0]  # 範囲外
    )
    print(f"  離隔: {result2.clearance}mm")
    print(f"  総長: {result2.total_scaffold_length}mm")
    print(f"  355mm使用: {result2.span_355_count}個")
    print(f"  150mm使用: {result2.span_150_count}個")
    print(f"  調整量: +{result2.adjustment_amount}mm")
    print(f"  制約満たす: {result2.constraints_satisfied}")
    print(f"  説明: {result2.calculation_notes}")
    print()

    # テスト3: 355mm使用可能なケース
    print("テスト3: 355mm使用可能なケース")
    print("  建物: 10000mm")
    print("  最小離隔: 880mm")
    print("  最大離隔: 990mm")
    print("  隣接edge離隔: 600mm, 650mm（範囲内）")
    result3 = calculate_with_advanced_spans(
        building_dimension=10000.0,
        min_clearance=880.0,
        max_clearance=990.0,
        adjacent_clearances=[600.0, 650.0]  # 範囲内
    )
    print(f"  離隔: {result3.clearance}mm")
    print(f"  総長: {result3.total_scaffold_length}mm")
    print(f"  355mm使用: {result3.span_355_count}個")
    print(f"  150mm使用: {result3.span_150_count}個")
    print(f"  調整量: +{result3.adjustment_amount}mm")
    print(f"  制約満たす: {result3.constraints_satisfied}")
    print(f"  説明: {result3.calculation_notes}")
