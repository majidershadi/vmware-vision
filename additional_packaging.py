"""Keep the app navigation and visibility after UCC generates its configuration UI."""

from pathlib import Path
import shutil
import re


def compatible_python(text):
    """Declare both supported runtimes and retain the Python 3.9 fallback."""
    text = re.sub(r"^\s*python\.required\s*=.*\n?", "", text, flags=re.M)
    return re.sub(
        r"^(\s*python\.version\s*=).*$",
        r"\1 python3.9\npython.required = 3.9, 3.13",
        text,
        flags=re.M,
    )


def cleanup_output_files(output_path, addon_name):
    root = Path(__file__).parent
    target = Path(output_path) / addon_name
    if not target.is_dir():
        target = Path(output_path)
    shutil.copy2(
        root / "package/default/data/ui/nav/default.xml",
        target / "default/data/ui/nav/default.xml",
    )
    config = target / "default/app.conf"
    text = config.read_text()
    text = text.replace("is_visible = false", "is_visible = true").replace(
        "is_visible = 0", "is_visible = 1"
    )
    config.write_text(text)
    for name in ("transforms.conf", "restmap.conf"):
        path = target / "default" / name
        if path.exists():
            path.write_text(compatible_python(path.read_text()))
    shutil.copytree(root / "docs", target / "README" / "docs", dirs_exist_ok=True)
    target = target.resolve()
    for cache in target.rglob("__pycache__"):
        if cache.resolve().is_relative_to(target):
            shutil.rmtree(cache)
    for artifact in target.rglob("*"):
        if artifact.suffix.lower() in (".so", ".pyd", ".dll", ".dylib"):
            raise RuntimeError(
                "Platform-specific dependency in package: " + str(artifact)
            )
