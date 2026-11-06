"""Attenuation sends and plugin references; start UE with -EnablePlugins=Spatialization.

Use --phase create, restart with the same plugin enabled, then --phase verify.
The test creates disposable attenuation/plugin assets and only references Engine assets.
"""

import argparse
from pathlib import Path

import httpx

PROJECT = Path(__file__).resolve().parents[5]
PACKAGE = "/Game/UE5MCP_Test/SA_MCP_RoutingSmoke"
ASSET = PACKAGE + ".SA_MCP_RoutingSmoke"
PLUGIN_PACKAGE = "/Game/UE5MCP_Test/PS_MCP_RoutingSmoke"
PLUGIN_ASSET = PLUGIN_PACKAGE + ".PS_MCP_RoutingSmoke"
PLUGIN_CLASS = "/Script/Spatialization.ITDSpatializationSourceSettings"
SUBMIXES = [f"/Engine/EngineSounds/Submixes/{name}.{name}" for name in
            ["MasterSubmixDefault", "MasterEQSubmixDefault", "MasterReverbSubmixDefault"]]
CURVE = "/Engine/Tutorial/ContentIntroCurve.ContentIntroCurve"


def call(base, method, route, body=None, **params):
    response = httpx.request(method, base + route, json=body, params=params, timeout=180)
    response.raise_for_status()
    return response.json()


def state(base):
    return call(base, "GET", "/audio/attenuations/settings", asset_path=ASSET)


def send(base, destination, **data):
    return call(base, "POST", "/audio/attenuations/submix-sends", {
        "AssetPath": ASSET, "SubmixPath": destination, "Operation": "upsert"} | data)


def plugin(base, operation, **data):
    return call(base, "POST", "/audio/attenuations/plugins", {
        "AssetPath": ASSET, "PluginType": "spatialization", "SettingsPath": PLUGIN_ASSET,
        "Operation": operation} | data)


def reject(base, method, route, data):
    response = httpx.request(method, base + route, json=data, timeout=180)
    assert response.status_code >= 400, response.text


def verify(base):
    stored = state(base)
    assert not stored["dirty"] and stored["flags"]["submix_sends"]
    assert len(stored["submix_sends"]) == 3
    by_path = {entry["submix_path"]: entry for entry in stored["submix_sends"]}
    assert by_path[SUBMIXES[0]]["control_method"] == "Manual"
    assert by_path[SUBMIXES[0]]["disable_manual_send_clamp"]
    assert abs(by_path[SUBMIXES[0]]["send_level"] - 1.5) < 0.001
    assert by_path[SUBMIXES[1]]["control_method"] == "Linear"
    assert abs(by_path[SUBMIXES[1]]["min_send_distance"] - 100) < 0.001
    assert abs(by_path[SUBMIXES[1]]["max_send_level"] - 0.7) < 0.001
    assert by_path[SUBMIXES[2]]["control_method"] == "CustomCurve"
    assert by_path[SUBMIXES[2]]["external_curve_path"] == CURVE
    assert by_path[SUBMIXES[2]]["curve_key_count"] == 3
    assert stored["plugin_settings"]["spatialization"] == [{"settings_path": PLUGIN_ASSET, "class_path": PLUGIN_CLASS}]
    assert not call(base, "GET", "/assets/dirty-state", asset_path=PLUGIN_ASSET)["dirty"]
    assert call(base, "POST", "/audio/attenuations/validate", {"AssetPath": ASSET})["valid"]
    for path in SUBMIXES + [CURVE]:
        assert not call(base, "GET", "/assets/dirty-state", asset_path=path)["dirty"]
    print("Manual/linear/custom sends, compatible plugin references, saved state, and source preservation: OK")


def cleanup(base, assets):
    for path in assets:
        call(base, "POST", "/assets/delete", {"AssetPath": path})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8080")
    parser.add_argument("--phase", choices=["live", "create", "verify"], default="live")
    args = parser.parse_args()
    base = args.base_url
    if args.phase == "verify":
        try:
            verify(base)
            reject(base, "POST", "/audio/attenuations/plugins", {"AssetPath": ASSET,
                   "PluginType": "spatialization", "SettingsPath": PLUGIN_ASSET, "Operation": "remove"})
            assert plugin(base, "remove", bDryRun=True)["would_change"]
            assert plugin(base, "remove", bConfirm=True, bSave=True)["changed"]
            for path in SUBMIXES:
                reject(base, "POST", "/audio/attenuations/submix-sends", {"AssetPath": ASSET, "SubmixPath": path, "Operation": "remove"})
                assert send(base, path, Operation="remove", bDryRun=True)["would_change"]
                assert send(base, path, Operation="remove", bConfirm=True, bSave=True)["changed"]
            send(base, SUBMIXES[0], ControlMethod="Manual", bSetSendLevel=True, SendLevel=0.4)
            assert call(base, "POST", "/audio/attenuations/submix-sends", {
                "AssetPath": ASSET, "Operation": "clear", "bConfirm": True, "bSave": True})["changed"]
            assert not state(base)["submix_sends"] and not state(base)["dirty"]
        finally:
            cleanup(base, [ASSET, PLUGIN_ASSET])
        return
    for name in ["SA_MCP_RoutingSmoke", "PS_MCP_RoutingSmoke"]:
        assert not (PROJECT / "Content" / "UE5MCP_Test" / f"{name}.uasset").exists()
    classes = call(base, "GET", "/audio/plugin-settings/classes")["classes"]
    assert any(entry["class_path"] == PLUGIN_CLASS and entry["plugin_type"] == "spatialization" for entry in classes), "Launch UE with -EnablePlugins=Spatialization"
    created = []
    succeeded = False
    try:
        response = httpx.post(base + "/audio/attenuations/create", json={"AssetPath": PACKAGE, "bSave": True}, timeout=180)
        response.raise_for_status()
        assert response.text == ASSET
        created.append(ASSET)
        for class_path in ["/Script/Engine.SoundAttenuation", "/Script/AudioExtensions.SpatializationPluginSourceSettingsBase"]:
            reject(base, "POST", "/audio/plugin-settings/create", {"AssetPath": PLUGIN_PACKAGE, "SettingsClass": class_path})
        request = {"AssetPath": PLUGIN_PACKAGE, "SettingsClass": PLUGIN_CLASS}
        assert call(base, "POST", "/audio/plugin-settings/create", request | {"bDryRun": True})["would_create"]
        result = call(base, "POST", "/audio/plugin-settings/create", request | {"bSave": True})
        created.append(PLUGIN_ASSET)
        assert result["asset_path"] == PLUGIN_ASSET and result["saved"]
        before = state(base)
        assert plugin(base, "add", bDryRun=True)["would_change"] and state(base) == before
        for family, path in [("spatialization", SUBMIXES[0]), ("occlusion", PLUGIN_ASSET)]:
            reject(base, "POST", "/audio/attenuations/plugins", {"AssetPath": ASSET, "PluginType": family, "SettingsPath": path, "Operation": "add"})
        assert plugin(base, "add", bSave=True)["changed"]
        assert not plugin(base, "add")["would_change"]
        reject(base, "POST", "/audio/attenuations/plugins", {"AssetPath": ASSET, "PluginType": "spatialization", "Operation": "clear"})
        assert plugin(base, "clear", bDryRun=True)["would_change"]
        assert plugin(base, "clear", bConfirm=True)["changed"]
        plugin(base, "add", bSave=True)
        manual = {"ControlMethod": "Manual", "bSetSendLevel": True, "SendLevel": 0.4}
        before = state(base)
        assert send(base, SUBMIXES[0], **manual, bDryRun=True)["would_change"] and state(base) == before
        reject(base, "POST", "/audio/attenuations/submix-sends", {"AssetPath": ASSET, "SubmixPath": ASSET, "Operation": "upsert"})
        send(base, SUBMIXES[0], **manual, bSave=True)
        assert not send(base, SUBMIXES[0], **manual)["would_change"]
        reject(base, "POST", "/audio/attenuations/submix-sends", {"AssetPath": ASSET, "SubmixPath": SUBMIXES[0], "Operation": "upsert", "bSetSendLevel": True, "SendLevel": 1.5})
        send(base, SUBMIXES[0], bSetDisableManualSendClamp=True, bDisableManualSendClamp=True,
             bSetSendLevel=True, SendLevel=1.5, bSave=True)
        linear = {"ControlMethod": "Linear", "bSetMinSendLevel": True, "MinSendLevel": 0.2,
                  "bSetMaxSendLevel": True, "MaxSendLevel": 0.7, "bSetMinSendDistance": True,
                  "MinSendDistance": 100, "bSetMaxSendDistance": True, "MaxSendDistance": 1000}
        reject(base, "POST", "/audio/attenuations/submix-sends", {"AssetPath": ASSET, "SubmixPath": SUBMIXES[1], "Operation": "upsert"} | linear | {"MinSendDistance": 2000})
        send(base, SUBMIXES[1], **linear, bSave=True)
        custom = {"ControlMethod": "CustomCurve", "bSetMinSendDistance": True, "MinSendDistance": 100,
                  "bSetMaxSendDistance": True, "MaxSendDistance": 1000, "bSetCurveKeys": True,
                  "Keys": [{"Time": 0, "Value": 0.1}, {"Time": 1, "Value": 0.8}]}
        send(base, SUBMIXES[2], **custom, bSave=True)
        reject(base, "POST", "/audio/attenuations/submix-sends", {"AssetPath": ASSET, "SubmixPath": SUBMIXES[2], "Operation": "upsert"} | custom)
        send(base, SUBMIXES[2], bSetExternalCurve=True, CurvePath=CURVE, bSave=True)
        reject(base, "POST", "/audio/attenuations/submix-sends", {"AssetPath": ASSET, "SubmixPath": SUBMIXES[2], "Operation": "upsert"} | custom)
        send(base, SUBMIXES[2], **custom, bConfirm=True, bSave=True)
        send(base, SUBMIXES[2], bSetExternalCurve=True, CurvePath=CURVE, bSave=True)
        reject(base, "POST", "/audio/attenuations/submix-sends", {"AssetPath": ASSET, "Operation": "clear"})
        assert call(base, "POST", "/audio/attenuations/submix-sends", {"AssetPath": ASSET, "Operation": "clear", "bDryRun": True})["would_change"]
        reject(base, "PATCH", "/audio/attenuations/settings", {"AssetPath": ASSET, "bSetAudioLinkSettings": True, "AudioLinkSettingsPath": PLUGIN_ASSET})
        call(base, "PATCH", "/audio/attenuations/settings", {"AssetPath": ASSET,
             "Flags": {"submix_sends": True, "send_to_audio_link": False, "source_data_override": False},
             "bSetAudioLinkSettings": True, "AudioLinkSettingsPath": "", "bSave": True})
        verify(base)
        succeeded = True
    finally:
        if args.phase != "create" or not succeeded:
            cleanup(base, created)


if __name__ == "__main__":
    main()
