import shutil
import sys
from pathlib import Path


ASSETS_DIR = Path(__file__).resolve().parent / "assets"
ENGLISH_MODEL_VERSION = "ppocr_v4"


def _fail_missing_submodule() -> None:
    print(
        'Please clone this repository completely, don’t miss "--recursive", '
        "and don’t download the zip package!"
    )
    print('请完整克隆本仓库，不要漏掉 "--recursive"，也不要下载 zip 包！')
    raise SystemExit(1)


def _configure_resource(resource_name: str, chinese_model_version: str) -> None:
    common_ocr = ASSETS_DIR / "MaaCommonAssets" / "OCR"
    chinese_source = common_ocr / chinese_model_version / "zh_cn"
    english_source = common_ocr / ENGLISH_MODEL_VERSION / "en_us"
    if not chinese_source.is_dir() or not english_source.is_dir():
        _fail_missing_submodule()

    model_dir = ASSETS_DIR / "resource" / resource_name / "model"
    ocr_dir = model_dir / "ocr"
    marker_path = model_dir / ".maayuan-ocr"
    expected_marker = f"{chinese_model_version}\n{ENGLISH_MODEL_VERSION}\n"
    try:
        current_marker = marker_path.read_text(encoding="utf-8")
    except OSError:
        current_marker = None
    if (
        current_marker == expected_marker
        and ocr_dir.is_dir()
        and (ocr_dir / "en").is_dir()
    ):
        print(f"Found current OCR models for {resource_name}; skipping.")
        return

    print(
        f"Installing {chinese_model_version}/zh_cn and "
        f"{ENGLISH_MODEL_VERSION}/en_us OCR models for {resource_name}."
    )
    if ocr_dir.exists():
        shutil.rmtree(ocr_dir)
    shutil.copytree(chinese_source, ocr_dir)
    shutil.copytree(english_source, ocr_dir / "en")

    model_dir.mkdir(parents=True, exist_ok=True)
    marker_path.write_text(expected_marker, encoding="utf-8")


def configure_ocr_model() -> None:
    chinese_model_version = "ppocr_v4" if sys.platform == "darwin" else "ppocr_v5"
    print(f"OCR model selection: zh_cn={chinese_model_version}, en_us=ppocr_v4")
    for resource_name in ("base", "zh_tw"):
        _configure_resource(resource_name, chinese_model_version)


if __name__ == "__main__":
    configure_ocr_model()
    print("OCR model configured.")
