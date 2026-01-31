import pandas as pd

import pytest

from services.utils.export_generator import export_dataframe_to_file, export_report


def test_export_csv_json_creates_files(tmp_path):
    df = pd.DataFrame(
        [
            {"name": "Alpha", "value": 10},
            {"name": "Beta", "value": 20},
        ]
    )

    export_dir = tmp_path / "exports"
    csv_path = export_dir / "data.csv"
    json_path = export_dir / "data.json"

    export_dataframe_to_file(df, "csv", str(csv_path))
    export_dataframe_to_file(df, "json", str(json_path))

    assert csv_path.exists()
    assert json_path.exists()
    assert csv_path.read_text(encoding="utf-8").strip()
    assert json_path.read_text(encoding="utf-8").strip()


def test_docx_export_is_unavailable():
    with pytest.raises(ValueError):
        export_report({}, {}, "docx")
