"""
下屋付き建物の足場割付計算モジュール（後方互換性のため維持）

このモジュールは後方互換性のために維持されています。
新しいコードでは protrusion_building モジュールの使用を推奨します。
"""

import sys
from pathlib import Path

# インポート処理（相対インポートと絶対インポートの両対応）
try:
    from .protrusion_building import (
        ProtrusionBuildingEdgeResult as ShedBuildingEdgeResult,
        calculate_shed_building
    )
except ImportError:
    # 直接実行時のパス設定
    sys.path.insert(0, str(Path(__file__).parent))
    from protrusion_building import (
        ProtrusionBuildingEdgeResult as ShedBuildingEdgeResult,
        calculate_shed_building
    )

__all__ = ['ShedBuildingEdgeResult', 'calculate_shed_building']
