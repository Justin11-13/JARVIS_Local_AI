# PyInstaller onedir specification for the complete Internal Test Core.

from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs, collect_submodules


ROOT = Path(SPECPATH).parent
MODEL_CACHE = (
    Path.home()
    / ".cache"
    / "huggingface"
    / "hub"
    / "models--sentence-transformers--paraphrase-multilingual-MiniLM-L12-v2"
)

datas = []
binaries = []
hiddenimports = [
    "app.api",
    "app.main",
    "services.rag.embedding",
    "services.rag.indexer",
    "services.rag.keyword_store",
    "services.rag.source_registry",
    "services.rag.vector_store",
]


def add_data(source: Path, destination: str) -> None:
    if not source.exists():
        raise SystemExit(f"Required Core resource is missing: {source}")
    datas.append((str(source), destination))


for package_name in (
    "chromadb",
    "chromadb_rust_bindings",
    "sentence_transformers",
    "transformers",
    "onnxruntime",
    "torch",
    "numpy",
    "scipy",
    "sklearn",
    "psutil",
):
    datas.extend(collect_data_files(package_name))
    binaries.extend(collect_dynamic_libs(package_name))

hiddenimports.extend([
    "chromadb.api.rust",
    "chromadb_rust_bindings",
    "sentence_transformers",
    "transformers.models.auto",
    "transformers.models.xlm_roberta",
    "transformers.models.roberta",
    "onnxruntime",
    "torch",
    "numpy",
    "scipy",
    "sklearn",
])

for package_name in ("app", "services", "skills"):
    hiddenimports.extend(collect_submodules(package_name))

add_data(ROOT / "packaging" / "core_defaults" / "config", "config")
add_data(ROOT / "knowledge" / "jarvis", "knowledge/jarvis")
add_data(MODEL_CACHE, "huggingface/hub/" + MODEL_CACHE.name)


analysis = Analysis(
    [str(ROOT / "packaging" / "core_entry.py")],
    pathex=[str(ROOT)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(analysis.pure)
exe = EXE(
    pyz,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name="jarvis-core",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
)
coll = COLLECT(
    exe,
    analysis.binaries,
    analysis.datas,
    strip=False,
    upx=False,
    name="jarvis-core",
)
