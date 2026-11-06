"""Dialogue voice/wave authoring and native context resolution; create/verify tests reload."""

import argparse
import json
from pathlib import Path

import httpx

PROJECT = Path(__file__).resolve().parents[5]
NAMES = ["DV_MCP_SpeakerSmoke", "DV_MCP_TargetASmoke", "DV_MCP_TargetBSmoke", "DW_MCP_DialogueSmoke"]
PATHS = [f"/Game/UE5MCP_Test/{name}.{name}" for name in NAMES]
SPEAKER, TARGET_A, TARGET_B, WAVE = PATHS
SOUND = "/Engine/EngineSounds/1kSineTonePing.1kSineTonePing"
INVALID = "/Engine/EngineSounds/Master.Master"
MANIFEST = PROJECT / "Saved" / "UE5MCP_DialogueSmoke.json"


def call(base, method, route, body=None, **params):
    response = httpx.request(method, base + route, json=body, params=params, timeout=180)
    response.raise_for_status()
    return response.json()


def reject(base, method, route, body):
    response = httpx.request(method, base + route, json=body, timeout=180)
    assert response.status_code >= 400, response.text


def voice(base, path):
    return call(base, "GET", "/audio/dialogue/voices/settings", asset_path=path)


def wave(base):
    return call(base, "GET", "/audio/dialogue/waves/settings", asset_path=WAVE)


def mapping(base, **data):
    return call(base, "POST", "/audio/dialogue/contexts", {"AssetPath": WAVE} | data)


def resolve(base, **data):
    return call(base, "POST", "/audio/dialogue/resolve", {"AssetPath": WAVE} | data)


def validate(base):
    return call(base, "POST", "/audio/dialogue/validate", {"AssetPath": WAVE})


def verify(base, expected):
    stored = wave(base)
    assert stored["localization_guid"] == expected["wave_guid"] and not stored["dirty"]
    assert stored["spoken_text"] == "Hello again" and stored["subtitle_override"] == "Welcome back"
    assert stored["override_subtitle"] and stored["mature"]
    assert stored["voice_actor_direction"] == "Calm and clear — a quiet greeting."
    assert len(stored["contexts"]) == 2
    assert {context["context_id"] for context in stored["contexts"]} == set(expected["context_ids"])
    for path, guid in expected["voice_guids"].items():
        state = voice(base, path)
        assert state["localization_guid"] == guid and not state["dirty"]
        assert call(base, "POST", "/audio/dialogue/validate", {"AssetPath": path})["ready_for_context_use"]
    assert voice(base, SPEAKER)["gender"] == "Mixed" and voice(base, SPEAKER)["plurality"] == "Plural"
    result = resolve(base, ContextId=expected["context_ids"][0])
    assert result["found"] and result["supports_context"] and result["playable"]
    assert result["sound_wave_path"] == SOUND and "DialogueSoundWaveProxy" in result["proxy_class"]
    assert result["localized_spoken_text"] == "Hello again" and result["localized_subtitle"] == "Welcome back"
    assert result["localization_key"] == expected["localization_key"] and result["duration_seconds"] > 0
    assert result["recorded_audio_filename"]
    exact = resolve(base, SpeakerPath=SPEAKER, TargetPaths=[TARGET_A, TARGET_B])
    assert exact["context_id"] == result["context_id"] and exact["playable"]
    assert not resolve(base, SpeakerPath=SPEAKER, TargetPaths=[TARGET_B, TARGET_A])["found"]
    assert not resolve(base, ContextId="NOT_PRESENT")["found"]
    report = validate(base)
    assert report["valid"] and report["ready_for_playback"]
    assert call(base, "POST", "/audio/validate", {"AssetPath": WAVE})["ready_for_playback"]
    assert not call(base, "GET", "/assets/dirty-state", asset_path=SOUND)["dirty"]
    print("Dialogue metadata, stable localization identities, contexts, native proxies/subtitles, and saved state: OK")


def cleanup(base, paths):
    for path in reversed(paths):
        call(base, "POST", "/assets/delete", {"AssetPath": path})
    MANIFEST.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8080")
    parser.add_argument("--phase", choices=["live", "create", "verify"], default="live")
    args = parser.parse_args()
    base = args.base_url
    if args.phase == "verify":
        expected = json.loads(MANIFEST.read_text(encoding="utf-8"))
        try:
            verify(base, expected)
            temporary = mapping(base, SpeakerPath=TARGET_B, bSetSpeaker=True, TargetPaths=[TARGET_A],
                bSetTargets=True, bSetSoundWave=True, SoundWavePath=SOUND, bSave=True)["context_id"]
            replaced = mapping(base, ContextId=temporary, bSetSpeaker=True, SpeakerPath=TARGET_A,
                bSetTargets=True, TargetPaths=[], bSave=True)["context_id"]
            assert replaced != temporary and not resolve(base, ContextId=temporary)["found"]
            assert resolve(base, ContextId=replaced)["playable"]
            mapping(base, Operation="remove", ContextId=replaced, bConfirm=True, bSave=True)
            procedural = call(base, "POST", "/metasounds/create", {
                "AssetPath": "/Game/UE5MCP_Test/MS_MCP_DialogueRejectSmoke", "AssetType": "source"})["asset_path"]
            try:
                before = wave(base)
                reject(base, "POST", "/audio/dialogue/contexts", {"AssetPath": WAVE,
                    "ContextId": expected["context_ids"][0], "bSetSoundWave": True, "SoundWavePath": procedural})
                assert wave(base) == before
            finally:
                call(base, "POST", "/assets/delete", {"AssetPath": procedural})
            secondary = expected["context_ids"][1]
            request = {"AssetPath": WAVE, "Operation": "remove", "ContextId": secondary}
            reject(base, "POST", "/audio/dialogue/contexts", request)
            assert mapping(base, Operation="remove", ContextId=secondary, bDryRun=True)["would_change"]
            assert mapping(base, Operation="remove", ContextId=secondary, bConfirm=True, bSave=True)["changed"]
            assert not resolve(base, ContextId=secondary)["found"]
            reject(base, "POST", "/audio/dialogue/contexts", {"AssetPath": WAVE, "Operation": "clear"})
            assert mapping(base, Operation="clear", bDryRun=True)["would_change"]
            assert mapping(base, Operation="clear", bConfirm=True, bSave=True)["changed"]
            assert validate(base)["valid"] and not validate(base)["ready_for_playback"]
        finally:
            cleanup(base, PATHS)
        return
    assert not MANIFEST.exists(), f"Reserved fixture manifest exists: {MANIFEST}"
    for name in NAMES:
        assert not (PROJECT / "Content" / "UE5MCP_Test" / f"{name}.uasset").exists()
    created = []
    succeeded = False
    try:
        for name, path in zip(NAMES, PATHS):
            package = path.split(".")[0]
            request = {"AssetPath": package, "AssetType": "wave" if name.startswith("DW_") else "voice"}
            dry = call(base, "POST", "/audio/dialogue/create", request | {"bDryRun": True})
            assert dry["would_create"] and not dry["created"]
            result = call(base, "POST", "/audio/dialogue/create", request | {"bSave": True})
            created.append(path)
            assert result["asset_path"] == path and result["saved"]
        guids = {path: voice(base, path)["localization_guid"] for path in PATHS[:3]}
        wave_guid = wave(base)["localization_guid"]
        assert len(set(guids.values())) == 3
        assert validate(base)["valid"] and not validate(base)["ready_for_playback"]
        before_voice = voice(base, SPEAKER)
        voice_edit = {"AssetPath": SPEAKER, "Gender": "Feminine", "Plurality": "Plural"}
        assert call(base, "PATCH", "/audio/dialogue/voices/settings", voice_edit | {"bDryRun": True})["would_change"]
        assert voice(base, SPEAKER) == before_voice
        reject(base, "PATCH", "/audio/dialogue/voices/settings", voice_edit | {"Gender": "Invalid"})
        call(base, "PATCH", "/audio/dialogue/voices/settings", voice_edit | {"bSave": True})
        text = {"AssetPath": WAVE, "bSetSpokenText": True, "SpokenText": "Hello there",
                "bSetSubtitleOverride": True, "SubtitleOverride": "Greetings", "bSetOverrideSubtitle": True,
                "bOverrideSubtitle": True, "bSetVoiceActorDirection": True,
                "VoiceActorDirection": "Calm and clear — a quiet greeting.", "bSetMature": True, "bMature": True}
        before = wave(base)
        assert call(base, "PATCH", "/audio/dialogue/waves/settings", text | {"bDryRun": True})["would_change"]
        assert wave(base) == before
        call(base, "PATCH", "/audio/dialogue/waves/settings", text | {"bSave": True})
        primary = {"SpeakerPath": SPEAKER, "bSetSpeaker": True, "TargetPaths": [TARGET_A, TARGET_B],
                   "bSetTargets": True, "bSetSoundWave": True, "SoundWavePath": SOUND}
        before = wave(base)
        assert mapping(base, **primary, bDryRun=True)["would_change"] and wave(base) == before
        for invalid in [primary | {"SpeakerPath": INVALID}, primary | {"TargetPaths": [TARGET_A, TARGET_A]},
                        primary | {"SoundWavePath": INVALID}, primary | {"bSetLocalizationKeyFormat": True, "LocalizationKeyFormat": "bad_{Unknown}"}]:
            reject(base, "POST", "/audio/dialogue/contexts", {"AssetPath": WAVE} | invalid)
            assert wave(base) == before
        first = mapping(base, **primary, bSave=True)["context_id"]
        assert len(wave(base)["contexts"]) == 1 and wave(base)["contexts"][0]["proxy_available"]
        assert not mapping(base, **primary)["would_change"]
        assert resolve(base, ContextId=first)["localized_subtitle"] == "Greetings"
        second = mapping(base, **(primary | {"TargetPaths": [TARGET_A]}), bSave=True)["context_id"]
        assert first != second
        assert mapping(base, ContextId=first, bSetLocalizationKeyFormat=True, LocalizationKeyFormat="shared", bSave=True)["changed"]
        reject(base, "POST", "/audio/dialogue/contexts", {"AssetPath": WAVE, "ContextId": second,
               "bSetLocalizationKeyFormat": True, "LocalizationKeyFormat": "shared"})
        mapping(base, ContextId=first, bSetLocalizationKeyFormat=True, LocalizationKeyFormat="{ContextHash}", bSave=True)
        reject(base, "POST", "/audio/dialogue/contexts", {"AssetPath": WAVE} | primary | {"TargetPaths": [TARGET_B, TARGET_A]})
        mapping(base, ContextId=first, bSetSoundWave=True, SoundWavePath="", bSave=True)
        assert not validate(base)["ready_for_playback"] and not resolve(base, ContextId=first)["playable"]
        mapping(base, ContextId=first, bSetSoundWave=True, SoundWavePath=SOUND, bSave=True)
        call(base, "PATCH", "/audio/dialogue/waves/settings", {"AssetPath": WAVE, "bSetSpokenText": True,
             "SpokenText": "Hello again", "bSetOverrideSubtitle": True, "bOverrideSubtitle": False, "bSave": True})
        assert resolve(base, ContextId=first)["localized_subtitle"] == "Hello again"
        call(base, "PATCH", "/audio/dialogue/waves/settings", {"AssetPath": WAVE, "bSetSubtitleOverride": True,
             "SubtitleOverride": "Welcome back", "bSetOverrideSubtitle": True, "bOverrideSubtitle": True, "bSave": True})
        call(base, "PATCH", "/audio/dialogue/voices/settings", {"AssetPath": SPEAKER, "Gender": "Mixed", "bSave": True})
        expected = {"voice_guids": guids, "wave_guid": wave_guid, "context_ids": [first, second],
                    "localization_key": resolve(base, ContextId=first)["localization_key"]}
        verify(base, expected)
        if args.phase == "create":
            MANIFEST.write_text(json.dumps(expected, ensure_ascii=False, indent=2), encoding="utf-8")
        succeeded = True
    finally:
        if args.phase != "create" or not succeeded:
            cleanup(base, created)


if __name__ == "__main__":
    main()
