"""
下屋上に入隅がある建物の足場計算モジュールのテスト
"""

import pytest
import math
import sys
from pathlib import Path

# src/logicをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "logic"))

from shed_with_inside_corner import (
    calculate_shed_with_inside_corner,
    ShedWithInsideCornerEdgeResult
)


class TestCalculateShedWithInsideCorner:
    """下屋上に入隅がある建物計算のテストクラス"""

    def test_normal_case(self):
        """正常系: 標準的な下屋上に入隅がある建物"""
        result = calculate_shed_with_inside_corner(
            width=8400.0,
            total_depth=10000.0,
            inside_corner_x=3000.0,
            main_start_y=7000.0,
            main_end_y=8000.0
        )

        # 外周辺の検証
        # edge1（北辺、X方向の辺）: Y方向に離隔を取る → clearance_y = 1000mm
        assert result['edge1'].building_length == 8400.0
        assert result['edge1'].clearance == 1000.0
        assert result['edge1'].scaffold_length == 10200.0

        # edge2（東辺、Y方向の辺）: X方向に離隔を取る → clearance_x = 900mm
        assert result['edge2'].building_length == 10000.0
        assert result['edge2'].clearance == 900.0
        assert result['edge2'].scaffold_length == 12000.0

        # edge3（南辺、X方向の辺）: Y方向に離隔を取る → clearance_y = 1000mm
        assert result['edge3'].building_length == 8400.0
        assert result['edge3'].clearance == 1000.0
        assert result['edge3'].scaffold_length == 10200.0

        # edge8（西辺、Y方向の辺）: X方向に離隔を取る → clearance_x = 900mm
        assert result['edge8'].building_length == 10000.0
        assert result['edge8'].clearance == 900.0
        assert result['edge8'].scaffold_length == 12000.0

        # 内部境界（入隅）の検証
        # edge10: clearance_x(900) + edge9a_length(3000) - 3000 = 900mm
        assert result['edge10'].building_length == 1000.0
        assert result['edge10'].clearance == 900.0
        assert result['edge10'].scaffold_length == 3000.0

        # edge9b: clearance_y(1000) + edge10_length(1000) - 1200 = 800mm
        assert result['edge9b'].building_length == 5400.0
        assert result['edge9b'].clearance == 800.0
        assert result['edge9b'].scaffold_length == 1200.0

        # edge9a: scaffold_x(10200) - edge9b_scaffold(1200) = 9000mm
        # 離隔はedge10の離隔値を参考値として使用
        assert result['edge9a'].building_length == 3000.0
        assert result['edge9a'].clearance == 900.0  # edge10の離隔値
        assert result['edge9a'].scaffold_length == 9000.0

        # メタ情報の検証
        assert result['scaffold_total_x'] == 10200.0
        assert result['scaffold_total_y'] == 12000.0

    def test_x_direction_total_consistency(self):
        """正確性: X方向の足場総長さの整合性"""
        result = calculate_shed_with_inside_corner(
            width=8400.0,
            total_depth=10000.0,
            inside_corner_x=3000.0,
            main_start_y=7000.0,
            main_end_y=8000.0
        )

        # edge9b + edge9a = X方向の足場総長さ
        x_total_check = (
            result['edge9b'].scaffold_length +
            result['edge9a'].scaffold_length
        )
        assert math.isclose(x_total_check, result['scaffold_total_x'])

    def test_300mm_unit_compliance(self):
        """正確性: 足場長さが300の倍数であることを確認"""
        result = calculate_shed_with_inside_corner(
            width=8400.0,
            total_depth=10000.0,
            inside_corner_x=3000.0,
            main_start_y=7000.0,
            main_end_y=8000.0
        )

        # すべての足場長さが300の倍数
        assert result['scaffold_total_x'] % 300 == 0
        assert result['scaffold_total_y'] % 300 == 0
        assert result['edge1'].scaffold_length % 300 == 0
        assert result['edge2'].scaffold_length % 300 == 0
        assert result['edge3'].scaffold_length % 300 == 0
        assert result['edge8'].scaffold_length % 300 == 0
        assert result['edge10'].scaffold_length % 300 == 0
        assert result['edge9b'].scaffold_length % 300 == 0
        assert result['edge9a'].scaffold_length % 300 == 0

    def test_different_inside_corner_position(self):
        """正常系: 異なる入隅位置での計算"""
        result = calculate_shed_with_inside_corner(
            width=10000.0,
            total_depth=12000.0,
            inside_corner_x=4000.0,
            main_start_y=8000.0,
            main_end_y=10000.0
        )

        # 基本的な整合性確認
        assert result['edge9a'].building_length == 4000.0
        assert result['edge10'].building_length == 2000.0
        assert result['edge9b'].building_length == 6000.0

        # X方向の足場総長さの整合性
        x_total = (
            result['edge9b'].scaffold_length +
            result['edge9a'].scaffold_length
        )
        assert math.isclose(x_total, result['scaffold_total_x'])

    def test_small_inside_corner_vertical(self):
        """エッジケース: 入隅縦辺が小さい場合"""
        result = calculate_shed_with_inside_corner(
            width=8400.0,
            total_depth=10000.0,
            inside_corner_x=3000.0,
            main_start_y=9000.0,  # 入隅縦辺が1000mmから500mmに変更
            main_end_y=9500.0
        )

        assert result['edge10'].building_length == 500.0
        assert result['edge10'].scaffold_length > 0
        # 300の倍数であることを確認
        assert result['edge10'].scaffold_length % 300 == 0

    def test_large_inside_corner_horizontal(self):
        """エッジケース: 入隅横辺が大きい場合"""
        result = calculate_shed_with_inside_corner(
            width=12000.0,
            total_depth=10000.0,
            inside_corner_x=2000.0,  # 入隅横辺が大きくなる
            main_start_y=7000.0,
            main_end_y=8000.0
        )

        assert result['edge9b'].building_length == 10000.0
        assert result['edge9b'].scaffold_length > 0
        # 300の倍数であることを確認
        assert result['edge9b'].scaffold_length % 300 == 0

    def test_invalid_width(self):
        """異常系: 幅が0以下"""
        with pytest.raises(ValueError) as exc_info:
            calculate_shed_with_inside_corner(
                width=0.0,
                total_depth=10000.0,
                inside_corner_x=3000.0,
                main_start_y=7000.0,
                main_end_y=8000.0
            )
        assert "幅は正の値である必要があります" in str(exc_info.value)

    def test_invalid_total_depth(self):
        """異常系: 全体奥行が0以下"""
        with pytest.raises(ValueError) as exc_info:
            calculate_shed_with_inside_corner(
                width=8400.0,
                total_depth=0.0,
                inside_corner_x=3000.0,
                main_start_y=7000.0,
                main_end_y=8000.0
            )
        assert "全体奥行は正の値である必要があります" in str(exc_info.value)

    def test_invalid_inside_corner_x_zero(self):
        """異常系: 入隅X座標が0以下"""
        with pytest.raises(ValueError) as exc_info:
            calculate_shed_with_inside_corner(
                width=8400.0,
                total_depth=10000.0,
                inside_corner_x=0.0,
                main_start_y=7000.0,
                main_end_y=8000.0
            )
        assert "入隅X座標は0より大きく" in str(exc_info.value)

    def test_invalid_inside_corner_x_exceeds_width(self):
        """異常系: 入隅X座標が幅以上"""
        with pytest.raises(ValueError) as exc_info:
            calculate_shed_with_inside_corner(
                width=8400.0,
                total_depth=10000.0,
                inside_corner_x=8400.0,  # 幅と同じ
                main_start_y=7000.0,
                main_end_y=8000.0
            )
        assert "入隅X座標は0より大きく" in str(exc_info.value)

    def test_invalid_main_start_y_zero(self):
        """異常系: 本体開始Y座標が0以下"""
        with pytest.raises(ValueError) as exc_info:
            calculate_shed_with_inside_corner(
                width=8400.0,
                total_depth=10000.0,
                inside_corner_x=3000.0,
                main_start_y=0.0,
                main_end_y=8000.0
            )
        assert "本体開始Y座標は0より大きく" in str(exc_info.value)

    def test_invalid_main_end_y(self):
        """異常系: 本体終了Y座標が開始Y座標以下"""
        with pytest.raises(ValueError) as exc_info:
            calculate_shed_with_inside_corner(
                width=8400.0,
                total_depth=10000.0,
                inside_corner_x=3000.0,
                main_start_y=8000.0,
                main_end_y=8000.0  # 開始と同じ
            )
        assert "本体終了Y座標" in str(exc_info.value)

    def test_custom_target_clearance(self):
        """正常系: カスタム目標離隔距離"""
        result = calculate_shed_with_inside_corner(
            width=8400.0,
            total_depth=10000.0,
            inside_corner_x=3000.0,
            main_start_y=7000.0,
            main_end_y=8000.0,
            target_clearance=1200.0
        )

        # 離隔距離が目標値に近いことを確認
        # （300の倍数制約があるため、完全一致ではない）
        assert result['clearance_x'] >= 900.0  # 最低限の離隔は確保
        assert result['clearance_y'] >= 900.0

    def test_edge_types(self):
        """正常系: 辺の種類の確認"""
        result = calculate_shed_with_inside_corner(
            width=8400.0,
            total_depth=10000.0,
            inside_corner_x=3000.0,
            main_start_y=7000.0,
            main_end_y=8000.0
        )

        # 外周辺
        assert result['edge1'].edge_type == "outer"
        assert result['edge2'].edge_type == "outer"
        assert result['edge3'].edge_type == "outer"
        assert result['edge8'].edge_type == "outer"

        # 入隅辺
        assert result['edge9a'].edge_type == "inside_corner"
        assert result['edge10'].edge_type == "inside_corner"
        assert result['edge9b'].edge_type == "inside_corner"

    def test_precision(self):
        """正確性: 浮動小数点演算の精度確認"""
        result = calculate_shed_with_inside_corner(
            width=8400.0,
            total_depth=10000.0,
            inside_corner_x=3000.0,
            main_start_y=7000.0,
            main_end_y=8000.0
        )

        # X方向の足場長さの再構築
        total_x_reconstructed = (
            result['edge9b'].scaffold_length +
            result['edge9a'].scaffold_length
        )

        # 精度誤差を考慮して検証（相対誤差 1e-9 以下）
        assert math.isclose(
            total_x_reconstructed,
            result['scaffold_total_x'],
            rel_tol=1e-9
        )


class TestShedWithInsideCornerEdgeResult:
    """ShedWithInsideCornerEdgeResultデータクラスのテスト"""

    def test_dataclass_creation(self):
        """データクラスの生成"""
        edge = ShedWithInsideCornerEdgeResult(
            edge_name="edge1",
            building_length=8400.0,
            clearance=900.0,
            scaffold_length=10200.0,
            edge_type="outer"
        )

        assert edge.edge_name == "edge1"
        assert edge.building_length == 8400.0
        assert edge.clearance == 900.0
        assert edge.scaffold_length == 10200.0
        assert edge.edge_type == "outer"

    def test_edge_type_values(self):
        """辺の種類の値テスト"""
        # 外周辺
        outer = ShedWithInsideCornerEdgeResult(
            edge_name="edge1",
            building_length=8400.0,
            clearance=900.0,
            scaffold_length=10200.0,
            edge_type="outer"
        )
        assert outer.edge_type == "outer"

        # 入隅辺
        inside = ShedWithInsideCornerEdgeResult(
            edge_name="edge10",
            building_length=1000.0,
            clearance=1000.0,
            scaffold_length=3000.0,
            edge_type="inside_corner"
        )
        assert inside.edge_type == "inside_corner"


if __name__ == "__main__":
    # テスト実行
    pytest.main([__file__, "-v", "--tb=short"])
