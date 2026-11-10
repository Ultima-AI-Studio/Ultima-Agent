"""Current source13 binding for seven original-profile helper interfaces.

No CLI, authority issuer, process launcher or default RootControls is exposed.
The private legacy module is trusted reuse, not a Python security boundary.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys

HERE = Path(__file__).resolve().parent
C = Path('C:/Users/Administrator/.codex/worktrees/jarvis-e03-source13/UltimaAgent')
CANDIDATE = '269aca511d88412dbb9c15d23911138469a37aa2'
PY = Path('H:/UltimaAI/UltimaAgent/tools/venv-openjarvis/Scripts/python.exe')
MODEL_DIGEST = '6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330'
RUNTIME_MANIFEST = HERE / 'inputs/candidate-runtime-manifest.json'
EXPECTED_MANIFEST_SHA = '957669cb3463eab549df80f0b8fc6345c244daa2f613925abe8622d0aab3d9d3'
LEGACY = HERE.parent / 'navigation-source10-validation-20261103-inert2/harness/adapter.py'
LEGACY_SHA = '27100afd246c9fb58579ed0389412731b4f029f1c5073ecce9e0cdd8b89d09ed'
LEGACY_MANIFEST = LEGACY.parent.parent / 'source10-candidate-manifest.json'
LEGACY_MANIFEST_SHA = 'cdfbfb059f889ef9e92221c503dffe2ca7fa08106ebf4968bcc26037f214be50'
_cached = None


def _need(value, message):
    if not value:
        raise ValueError(message)


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check_inputs():
    _need(Path(sys.executable).resolve() == PY.resolve(), 'Fixed interpreter')
    _need(sys.flags.dont_write_bytecode and sys.flags.utf8_mode and not sys.flags.optimize, 'Fixed Python flags')
    _need(_sha(RUNTIME_MANIFEST) == EXPECTED_MANIFEST_SHA, 'Current runtime manifest drift')
    manifest = json.loads(RUNTIME_MANIFEST.read_bytes())
    _need(manifest['candidate'] == CANDIDATE and Path(manifest['candidate_root']) == C, 'Current candidate binding')
    _need(manifest['model']['digest'] == MODEL_DIGEST and manifest['model']['only_current8b'] is True, 'Current8B binding')
    _need(manifest['actual_release'] is False, 'Preparation input only')
    files = dict(manifest['source_files'], **manifest['dependencies'])
    for component in manifest['sdk_components'].values():
        files.update({str(Path(component['root']) / name): digest for name, digest in component['files'].items()})
    model = manifest['model']
    files[model['policy_path']] = model['policy_sha256']
    files[model['local_manifest_path']] = model['local_manifest_observed_sha256']
    for name, digest in files.items():
        _need(_sha(name) == digest, 'Current bound input drift')
    _need(_sha(LEGACY) == LEGACY_SHA and _sha(LEGACY_MANIFEST) == LEGACY_MANIFEST_SHA, 'Legacy helper source drift')
    return files


def _legacy():
    global _cached
    check_inputs()
    if _cached is None:
        spec = importlib.util.spec_from_file_location('source13_private_profile_helpers', LEGACY)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.C = C
        module.check_inputs = check_inputs
        _cached = module
    return _cached


def check_import_origins():
    # The fixed 22 SDK origins are unchanged; the helper's candidate origin uses C above.
    return _legacy().check_import_origins()


def corpus():
    return _legacy().corpus()


def load_p4():
    return _legacy().load_p4()


def install_browser_fixture():
    return _legacy().install_browser_fixture()


def install_trusted_exports(folder):
    return _legacy().install_trusted_exports(folder)


def verify_exports(folder, result, p4, *, readonly=False):
    return _legacy().verify_exports(folder, result, p4, readonly=readonly)
