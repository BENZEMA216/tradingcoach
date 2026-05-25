"""
测试增量导入历史类型

input: IncrementalImporter 内部状态
output: 导入历史展示用 file_type
pos: 单元测试 - 验证 adapter 模式不会在导入历史里被误标成 CN

一旦我被更新，务必更新我所属文件夹的 README.md
"""

from src.importers.incremental_importer import IncrementalImporter


def test_history_file_type_uses_broker_id_for_adapter_mode():
    importer = IncrementalImporter("dummy.csv", dry_run=True)
    importer.file_language = "adapter"
    importer.result.broker_id = "futu_en"

    assert importer._get_history_file_type() == "futu_en"


def test_history_file_type_keeps_legacy_language():
    importer = IncrementalImporter("dummy.csv", dry_run=True)
    importer.file_language = "english"

    assert importer._get_history_file_type() == "english"
