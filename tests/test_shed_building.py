"""
下屋付き建物の足場計算モジュールのテスト
"""

import pytest
import math
import sys
from pathlib import Path

# src/logicをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "logic"))

from shed_building import calculate_shed_building, ShedBuildingEdgeResult


class TestCalculateShedBuilding:
    """下屋付き建物計算のテストクラス"""

    def test_normal_case(self):
        """正常系: 標準的な下屋付き建物"""
        result = calculate_shed_building(
            width=8400.0,
            total_depth=4510.0,
            main_depth=3600.0,
            shed_depth=910.0
        )

        # edge1（北辺）の検証
        assert result['edge1'].building_length == 8400.0
        assert result['edge1'].clearance == 900.0
        assert result['edge1'].scaffold_length == 10200.0

        # edge3（南辺）の検証
        assert result['edge3'].building_length == 8400.0
        assert result['edge3'].clearance == 900.0
        assert result['edge3'].scaffold_length == 10200.0

        # edge5（内部境界）の検証
        assert result['edge5'].building_length == 8400.0
        assert result['edge5'].clearance == 910.0
        assert result['edge5'].scaffold_length == 10200.0

        # edge2下（下屋部分）の検証
        assert result['edge2_lower'].building_length == 910.0
        assert result['edge2_lower'].scaffold_length == 900.0
        assert result['edge2_lower'].height_section == "lower"

        # edge2上（本体部分）の検証
        assert result['edge2_upper'].building_length == 3600.0
        assert result['edge2_upper'].scaffold_length == 5700.0
        assert result['edge2_upper'].clearance == 1050.0
        assert result['edge2_upper'].height_section == "upper"

        # Y方向の足場総長さ検証
        assert result['scaffold_total_y'] == 6600.0
        # 下部 + 上部 = 総長さ
        total_check = (
            result['edge2_lower'].scaffold_length +
            result['edge2_upper'].scaffold_length
        )
        assert total_check == result['scaffold_total_y']

    def test_different_dimensions(self):
        """正常系: 異なる寸法での計算"""
        result = calculate_shed_building(
            width=6000.0,
            total_depth=3000.0,
            main_depth=2400.0,
            shed_depth=600.0
        )

        # 基本的な整合性確認
        assert result['edge1'].building_length == 6000.0
        assert result['edge3'].building_length == 6000.0
        assert result['edge2_upper'].building_length == 2400.0
        assert result['edge2_lower'].building_length == 600.0

        # Y方向の足場分配確認
        total_y_scaffold = (
            result['edge2_lower'].scaffold_length +
            result['edge2_upper'].scaffold_length
        )
        assert total_y_scaffold == result['scaffold_total_y']

    def test_large_shed(self):
        """エッジケース: 下屋が大きい場合"""
        result = calculate_shed_building(
            width=10000.0,
            total_depth=6000.0,
            main_depth=3000.0,
            shed_depth=3000.0
        )

        # 下屋と本体が同じ奥行
        assert result['edge2_upper'].building_length == 3000.0
        assert result['edge2_lower'].building_length == 3000.0

        # 足場総長さの検証
        total_y = (
            result['edge2_lower'].scaffold_length +
            result['edge2_upper'].scaffold_length
        )
        assert total_y == result['scaffold_total_y']

    def test_small_shed(self):
        """エッジケース: 下屋が小さい場合"""
        result = calculate_shed_building(
            width=8000.0,
            total_depth=5000.0,
            main_depth=4500.0,
            shed_depth=500.0
        )

        # 下屋が小さくても計算が成立
        assert result['edge2_lower'].building_length == 500.0
        assert result['edge2_lower'].scaffold_length > 0

        # 本体部分が大部分を占める
        assert result['edge2_upper'].building_length == 4500.0
        assert result['edge2_upper'].scaffold_length > result['edge2_lower'].scaffold_length

    def test_invalid_width(self):
        """異常系: 幅が0以下"""
        with pytest.raises(ValueError) as exc_info:
            calculate_shed_building(
                width=0.0,
                total_depth=4510.0,
                main_depth=3600.0,
                shed_depth=910.0
            )
        assert "幅は正の値である必要があります" in str(exc_info.value)

        with pytest.raises(ValueError):
            calculate_shed_building(
                width=-100.0,
                total_depth=4510.0,
                main_depth=3600.0,
                shed_depth=910.0
            )

    def test_invalid_total_depth(self):
        """異常系: 全体奥行が0以下"""
        with pytest.raises(ValueError) as exc_info:
            calculate_shed_building(
                width=8400.0,
                total_depth=0.0,
                main_depth=3600.0,
                shed_depth=910.0
            )
        assert "全体奥行は正の値である必要があります" in str(exc_info.value)

    def test_invalid_main_depth(self):
        """異常系: 本体奥行が0以下"""
        with pytest.raises(ValueError) as exc_info:
            calculate_shed_building(
                width=8400.0,
                total_depth=4510.0,
                main_depth=0.0,
                shed_depth=910.0
            )
        assert "本体奥行は正の値である必要があります" in str(exc_info.value)

    def test_invalid_shed_depth(self):
        """異常系: 下屋奥行が0以下"""
        with pytest.raises(ValueError) as exc_info:
            calculate_shed_building(
                width=8400.0,
                total_depth=4510.0,
                main_depth=3600.0,
                shed_depth=0.0
            )
        assert "下屋奥行は正の値である必要があります" in str(exc_info.value)

    def test_depth_mismatch(self):
        """異常系: 全体奥行と本体+下屋の不一致"""
        with pytest.raises(ValueError) as exc_info:
            calculate_shed_building(
                width=8400.0,
                total_depth=5000.0,  # 本体3600 + 下屋910 = 4510と不一致
                main_depth=3600.0,
                shed_depth=910.0
            )
        assert "全体奥行" in str(exc_info.value)
        assert "一致しません" in str(exc_info.value)

    def test_custom_target_clearance(self):
        """正常系: カスタム目標離隔距離"""
        result = calculate_shed_building(
            width=8400.0,
            total_depth=4510.0,
            main_depth=3600.0,
            shed_depth=910.0,
            target_clearance=1200.0
        )

        # 離隔距離が目標値に近いことを確認
        # （300の倍数制約があるため、完全一致ではない）
        assert result['clearance_x'] >= 900.0  # 最低限の離隔は確保
        assert result['clearance_y'] >= 900.0

    def test_300mm_unit_compliance(self):
        """正確性: 足場長さが300の倍数であることを確認"""
        result = calculate_shed_building(
            width=8400.0,
            total_depth=4510.0,
            main_depth=3600.0,
            shed_depth=910.0
        )

        # すべての足場長さが300の倍数
        assert result['scaffold_total_x'] % 300 == 0
        assert result['scaffold_total_y'] % 300 == 0
        assert result['edge2_lower'].scaffold_length % 300 == 0
        assert result['edge2_upper'].scaffold_length % 300 == 0

    def test_precision(self):
        """正確性: 浮動小数点演算の精度確認"""
        result = calculate_shed_building(
            width=8400.0,
            total_depth=4510.0,
            main_depth=3600.0,
            shed_depth=910.0
        )

        # Y方向の足場長さの再構築
        total_y_reconstructed = (
            result['edge2_lower'].scaffold_length +
            result['edge2_upper'].scaffold_length
        )

        # 精度誤差を考慮して検証（相対誤差 1e-9 以下）
        assert math.isclose(
            total_y_reconstructed,
            result['scaffold_total_y'],
            rel_tol=1e-9
        )

    def test_symmetry(self):
        """正確性: 東西辺の対称性確認"""
        result = calculate_shed_building(
            width=8400.0,
            total_depth=4510.0,
            main_depth=3600.0,
            shed_depth=910.0
        )

        # edge2とedge4は対称なので、同じ値になるはず
        assert result['edge2_upper'].scaffold_length == result['edge4_upper'].scaffold_length
        assert result['edge2_lower'].scaffold_length == result['edge4_lower'].scaffold_length
        assert result['edge2_upper'].clearance == result['edge4_upper'].clearance
        assert result['edge2_lower'].clearance == result['edge4_lower'].clearance


class TestShedBuildingEdgeResult:
    """ShedBuildingEdgeResultデータクラスのテスト"""

    def test_dataclass_creation(self):
        """データクラスの生成"""
        edge = ShedBuildingEdgeResult(
            edge_name="edge1",
            building_length=8400.0,
            clearance=900.0,
            scaffold_length=10200.0,
            height_section=None
        )

        assert edge.edge_name == "edge1"
        assert edge.building_length == 8400.0
        assert edge.clearance == 900.0
        assert edge.scaffold_length == 10200.0
        assert edge.height_section is None

    def test_height_section_values(self):
        """高さ区分の値テスト"""
        # 上部
        upper = ShedBuildingEdgeResult(
            edge_name="edge2_upper",
            building_length=3600.0,
            clearance=1050.0,
            scaffold_length=5700.0,
            height_section="upper"
        )
        assert upper.height_section == "upper"

        # 下部
        lower = ShedBuildingEdgeResult(
            edge_name="edge2_lower",
            building_length=910.0,
            clearance=1045.0,
            scaffold_length=900.0,
            height_section="lower"
        )
        assert lower.height_section == "lower"


if __name__ == "__main__":
    # テスト実行
    pytest.main([__file__, "-v", "--tb=short"])
