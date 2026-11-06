"""Native audio format import/reimport matrix; create/verify phases test editor reload.

Supply --sndfile-dll pointing to the installed UE libsndfile DLL. Fixtures use
that encoder, while every import and decoder preflight runs inside UE.
"""

import argparse
import ctypes
import math
import os
from pathlib import Path

import httpx

PROJECT = Path(__file__).resolve().parents[5]
SOURCES = PROJECT / "Saved" / "UE5MCP_AudioFormatsSmoke"
FORMATS = {"wav": 0x010002, "aif": 0x020002, "aiff": 0x020002,
           "flac": 0x170002, "ogg": 0x200060, "opus": 0x200064, "mp3": 0x230082}


class SFInfo(ctypes.Structure):
    _fields_ = [("frames", ctypes.c_int64), ("samplerate", ctypes.c_int),
                ("channels", ctypes.c_int), ("format", ctypes.c_int),
                ("sections", ctypes.c_int), ("seekable", ctypes.c_int)]


class Encoder:
    def __init__(self, path):
        self.directory = os.add_dll_directory(str(path.parent))
        self.lib = ctypes.CDLL(str(path))
        self.lib.sf_format_check.argtypes = [ctypes.POINTER(SFInfo)]
        self.lib.sf_open.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.POINTER(SFInfo)]
        self.lib.sf_open.restype = ctypes.c_void_p
        self.lib.sf_writef_float.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_float), ctypes.c_int64]
        self.lib.sf_writef_float.restype = ctypes.c_int64
        self.lib.sf_close.argtypes = [ctypes.c_void_p]
        self.lib.sf_strerror.argtypes = [ctypes.c_void_p]
        self.lib.sf_strerror.restype = ctypes.c_char_p

    def write(self, extension, duration):
        path = SOURCES / f"source.{extension}"
        info = SFInfo(0, 48000, 2, FORMATS[extension], 0, 0)
        assert self.lib.sf_format_check(ctypes.byref(info)), f"Encoder lacks {extension}"
        handle = self.lib.sf_open(str(path).encode("utf-8"), 0x20, ctypes.byref(info))
        assert handle, self.lib.sf_strerror(None).decode()
        frames = round(48000 * duration)
        data = (ctypes.c_float * (frames * 2))()
        for frame in range(frames):
            data[frame * 2] = 0.2 * math.sin(2 * math.pi * 440 * frame / 48000)
            data[frame * 2 + 1] = 0.2 * math.sin(2 * math.pi * 660 * frame / 48000)
        try:
            assert self.lib.sf_writef_float(handle, data, frames) == frames
        finally:
            assert self.lib.sf_close(handle) == 0
        return path


def asset(extension):
    name = f"SW_MCP_FormatSmoke_{extension}"
    return f"/Game/UE5MCP_Test/{name}.{name}"


def asset_file(extension):
    return PROJECT / "Content" / "UE5MCP_Test" / f"SW_MCP_FormatSmoke_{extension}.uasset"


def call(base, method, route, body=None, **params):
    response = httpx.request(method, base + route, json=body, params=params, timeout=180)
    response.raise_for_status()
    return response.json()


def settings(base, extension):
    return call(base, "GET", "/audio/waves/settings", asset_path=asset(extension))


def expected_source(extension):
    return SOURCES / ("source.wav" if extension == "flac" else "source.flac")


def verify(base):
    for extension in FORMATS:
        state = settings(base, extension)
        source = call(base, "GET", "/audio/waves/source", asset_path=asset(extension))
        assert state["looping"] and state["compression_quality"] == 57, (extension, state)
        assert not state["dirty"] and asset_file(extension).exists()
        assert source["channels"] == 2 and source["imported_sample_rate"] == 48000
        assert abs(source["imported_duration_seconds"] - 0.2) < 0.03
        assert Path(source["source_files"][0]["path"]).resolve() == expected_source(extension).resolve()
        assert source["source_files"][0]["format"] == expected_source(extension).suffix[1:]
        print(f"{extension}: saved source, metadata, looping, and compression quality verified")


def cleanup(base, extensions):
    failures = []
    for extension in extensions:
        try:
            call(base, "POST", "/assets/delete", {"AssetPath": asset(extension)})
        except Exception as error:
            failures.append(f"{extension}: {error}")
    if failures:
        raise RuntimeError("Fixture asset cleanup failed: " + "; ".join(failures))
    for name in [f"source.{extension}" for extension in FORMATS] + ["invalid.flac", "unsupported.bin"]:
        (SOURCES / name).unlink(missing_ok=True)
    if SOURCES.exists() and not any(SOURCES.iterdir()):
        SOURCES.rmdir()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sndfile-dll", type=Path)
    parser.add_argument("--base-url", default="http://127.0.0.1:8080")
    parser.add_argument("--phase", choices=["live", "create", "verify"], default="live")
    args = parser.parse_args()
    base = args.base_url
    if args.phase == "verify":
        try:
            verify(base)
        finally:
            cleanup(base, list(FORMATS))
        return
    assert args.sndfile_dll and args.sndfile_dll.is_file(), "Provide --sndfile-dll"
    assert not SOURCES.exists(), f"Reserved fixture source directory exists: {SOURCES}"
    for extension in FORMATS:
        assert not asset_file(extension).exists(), f"Reserved fixture asset exists: {asset_file(extension)}"
    catalog = call(base, "GET", "/audio/waves/import-formats")
    assert set(FORMATS) <= {entry["extension"] for entry in catalog["formats"]}, catalog
    SOURCES.mkdir(parents=True)
    encoder = Encoder(args.sndfile_dll.resolve())
    created = []
    succeeded = False
    try:
        for extension in FORMATS:
            encoder.write(extension, 0.1)
        for invalid in ["invalid.flac", "unsupported.bin"]:
            path = SOURCES / invalid
            path.write_bytes(b"Not an audio source")
            response = httpx.post(base + "/audio/waves/import", json={
                "SourceFilePath": str(path), "DestinationPath": "/Game/UE5MCP_Test",
                "AssetName": "SW_MCP_RejectInvalid", "bDryRun": True}, timeout=180)
            assert response.status_code >= 400, response.text

        for extension in FORMATS:
            source = SOURCES / f"source.{extension}"
            request = {"SourceFilePath": str(source), "DestinationPath": "/Game/UE5MCP_Test",
                       "AssetName": f"SW_MCP_FormatSmoke_{extension}"}
            dry = call(base, "POST", "/audio/waves/import", request | {"bDryRun": True})
            assert dry["dry_run"] and not dry["changed"] and not asset_file(extension).exists()
            result = call(base, "POST", "/audio/waves/import", request | {"bSave": True})
            created.append(extension)
            assert result["source_format"] == extension and result["saved"]
            assert result["channels"] == 2 and result["imported_sample_rate"] == 48000
            assert abs(result["duration_seconds"] - 0.1) < 0.03
            call(base, "PATCH", "/audio/waves/settings", {"AssetPath": asset(extension),
                "bSetLooping": True, "bLooping": True, "bSetCompressionQuality": True,
                "CompressionQuality": 57, "bSave": True})
            encoder.write(extension, 0.2)
            reimport = {"AssetPath": asset(extension), "bConfirmReimport": True}
            dry = call(base, "POST", "/audio/waves/reimport", reimport | {"bDryRun": True})
            assert not dry["changed"] and not settings(base, extension)["dirty"]
            result = call(base, "POST", "/audio/waves/reimport", reimport | {"bSave": True})
            assert result["changed"] and abs(result["imported_duration_seconds"] - 0.2) < 0.03, result
            assert settings(base, extension)["compression_quality"] == 57
            print(f"{extension}: native import, dry-run, and same-file reimport passed")

        for extension in FORMATS:
            request = {"AssetPath": asset(extension), "SourceFilePath": str(expected_source(extension)),
                       "bConfirmReimport": True}
            rejected = httpx.post(base + "/audio/waves/reimport", json=request, timeout=180)
            assert rejected.status_code >= 400
            switched = call(base, "POST", "/audio/waves/reimport", request | {
                "bConfirmSourceChange": True, "bSave": True})
            assert switched["changed"] and switched["saved"]
        verify(base)
        succeeded = True
        print("Native audio format matrix and confirmed cross-format reimport: OK")
    finally:
        if args.phase != "create" or not succeeded:
            cleanup(base, created)


if __name__ == "__main__":
    main()
