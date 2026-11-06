"""Dedicated attenuation controls and curves; create/verify phases test reload."""

import argparse
from pathlib import Path

import httpx

PROJECT = Path(__file__).resolve().parents[5]
PACKAGE = "/Game/UE5MCP_Test/SA_MCP_TypedSmoke"
ASSET = PACKAGE + ".SA_MCP_TypedSmoke"
ASSET_FILE = PROJECT / "Content" / "UE5MCP_Test" / "SA_MCP_TypedSmoke.uasset"
EXTERNAL_PACKAGE = "/Game/UE5MCP_Test/SA_MCP_ExternalCurveSmoke"
EXTERNAL_ASSET = EXTERNAL_PACKAGE + ".SA_MCP_ExternalCurveSmoke"
EXTERNAL_FILE = PROJECT / "Content" / "UE5MCP_Test" / "SA_MCP_ExternalCurveSmoke.uasset"
EXTERNAL_CURVE = "/Engine/Tutorial/ContentIntroCurve.ContentIntroCurve"


def call(base, method, route, body=None, **params):
    response = httpx.request(method, base + route, json=body, params=params, timeout=180)
    response.raise_for_status()
    return response.json()


def state(base):
    return call(base, "GET", "/audio/attenuations/settings", asset_path=ASSET)


def reject(base, method, route, body):
    response = httpx.request(method, base + route, json=body, timeout=180)
    assert response.status_code >= 400, response.text


def settings(base, **data):
    return call(base, "PATCH", "/audio/attenuations/settings", {"AssetPath": ASSET} | data)


def curve(base, name, **data):
    return call(base, "POST", "/audio/attenuations/curves", {"AssetPath": ASSET, "CurveName": name} | data)


def gains(base, points):
    result = call(base, "POST", "/audio/attenuations/evaluate", {"AssetPath": ASSET, "Locations": points})
    assert result["evaluation_scope"] == "distance_volume_attenuation_only"
    return [sample["linear_gain"] for sample in result["samples"]]


def keys(midpoint):
    return [{"Time": 0.0, "Value": 1.0}, {"Time": 0.5, "Value": midpoint}, {"Time": 1.0, "Value": 0.0}]


def verify(base):
    saved = state(base)
    assert not saved["dirty"] and ASSET_FILE.exists()
    assert saved["enum_settings"]["distance_algorithm"] == "Custom"
    assert saved["enum_settings"]["reverb_send_method"] == "CustomCurve"
    assert saved["enum_settings"]["priority_attenuation_method"] == "CustomCurve"
    assert saved["enum_settings"]["absorption_method"] == "CustomCurve"
    assert saved["flags"]["occlusion"] and saved["flags"]["air_absorption"] and saved["flags"]["listener_focus"]
    assert abs(saved["numeric_settings"]["occlusion_volume_attenuation"] - 0.5) < 0.001
    assert abs(saved["numeric_settings"]["falloff_distance"] - 900) < 0.001
    assert saved["shape_extents"] == {"x": 100, "y": 0, "z": 0}
    assert saved["curves"]["attenuation"]["key_count"] == 3
    assert abs(saved["curves"]["attenuation"]["keys"][1]["value"] - 0.2) < 0.001
    for name in ["reverb_send", "priority", "lowpass_absorption", "highpass_absorption"]:
        assert saved["curves"][name]["key_count"] == 2
    assert saved["curves"]["reverb_send"]["keys"][0]["interpolation"] == "Cubic"
    assert saved["curves"]["lowpass_absorption"]["keys"][0]["interpolation"] == "Constant"
    assert call(base, "POST", "/audio/attenuations/validate", {"AssetPath": ASSET})["valid"]
    sampled = gains(base, [{"X": x, "Y": 0, "Z": 0} for x in [0, 550, 1000]])
    assert all(abs(a - b) < 0.002 for a, b in zip(sampled, [1, 0.2, 0])), sampled
    external = call(base, "GET", "/audio/attenuations/settings", asset_path=EXTERNAL_ASSET)
    assert external["curves"]["priority"]["external_curve_path"] == EXTERNAL_CURVE
    assert external["curves"]["priority"]["key_count"] > 0 and not external["dirty"]
    assert call(base, "POST", "/audio/attenuations/validate", {"AssetPath": EXTERNAL_ASSET})["valid"]
    assert not call(base, "GET", "/assets/dirty-state", asset_path=EXTERNAL_CURVE)["dirty"]
    print("Attenuation settings, five custom curves, native gain samples, and saved state: OK")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8080")
    parser.add_argument("--phase", choices=["live", "create", "verify"], default="live")
    args = parser.parse_args()
    base = args.base_url
    if args.phase == "verify":
        try:
            verify(base)
        finally:
            call(base, "POST", "/assets/delete", {"AssetPath": ASSET})
            call(base, "POST", "/assets/delete", {"AssetPath": EXTERNAL_ASSET})
        return
    assert not ASSET_FILE.exists(), f"Reserved attenuation fixture exists: {ASSET_FILE}"
    assert not EXTERNAL_FILE.exists(), f"Reserved external curve fixture exists: {EXTERNAL_FILE}"
    created = False
    external_created = False
    succeeded = False
    try:
        response = httpx.post(base + "/audio/attenuations/create", json={"AssetPath": PACKAGE, "bSave": True}, timeout=180)
        response.raise_for_status()
        assert response.text == ASSET, response.text
        created = True
        before = state(base)
        request = {"NumericSettings": {"falloff_distance": 900, "air_absorption_distance_min": 100,
                    "air_absorption_distance_max": 1000, "lowpass_frequency_at_max": 4000,
                    "highpass_frequency_at_max": 500, "occlusion_lowpass_frequency": 1500,
                    "occlusion_volume_attenuation": 0.5, "occlusion_interpolation_time": 0.2,
                    "focus_azimuth": 30, "non_focus_azimuth": 75, "manual_reverb_send_level": 0.35,
                    "priority_distance_min": 100, "priority_distance_max": 1000,
                    "priority_attenuation_min": 0.8, "priority_attenuation_max": 0.2},
                   "Flags": {"attenuate": True, "spatialize": True, "air_absorption": True,
                    "listener_focus": True, "focus_interpolation": True, "occlusion": True,
                    "reverb_send": True, "priority_attenuation": True, "normalize_stereo": True},
                   "EnumSettings": {"distance_algorithm": "Linear", "attenuation_shape": "Sphere",
                    "occlusion_trace_channel": "ECC_Visibility", "reverb_send_method": "Manual"},
                   "bSetShapeExtents": True, "ShapeExtents": {"X": 100, "Y": 0, "Z": 0}}
        dry = settings(base, **request, bDryRun=True, bSave=True)
        assert dry["would_change"] and not dry["changed"] and state(base) == before
        for bad in [{"NumericSettings": {"falloff_distance": -1}},
                    {"NumericSettings": {"not_an_attenuation_field": 1}},
                    {"EnumSettings": {"distance_algorithm": "Unsupported"}},
                    {"Flags": {"air_absorption": True}, "NumericSettings": {"air_absorption_distance_min": 9000, "air_absorption_distance_max": 1}},
                    {"EnumSettings": {"attenuation_shape": "Capsule"}, "bSetShapeExtents": True, "ShapeExtents": {"X": 50, "Y": 100, "Z": 0}}]:
            reject(base, "PATCH", "/audio/attenuations/settings", {"AssetPath": ASSET} | bad)
            assert state(base) == before
        changed = settings(base, **request, bSave=True)
        assert changed["changed"] and changed["saved"] and not state(base)["dirty"]
        assert not settings(base, **request)["would_change"]
        sampled = gains(base, [{"X": x, "Y": 0, "Z": 0} for x in [0, 100, 550, 1000, 2000]])
        assert all(abs(a - b) < 0.002 for a, b in zip(sampled, [1, 1, 0.5, 0, 0])), sampled
        for name, extents in [("Box", (100, 100, 100)), ("Capsule", (200, 100, 0)), ("Cone", (100, 30, 15))]:
            settings(base, EnumSettings={"attenuation_shape": name}, bSetShapeExtents=True,
                     ShapeExtents=dict(zip(["X", "Y", "Z"], extents)))
            sampled = gains(base, [{"X": 1, "Y": 0, "Z": 0}, {"X": 2000, "Y": 0, "Z": 0}])
            assert abs(sampled[0] - 1) < 0.002 and abs(sampled[1]) < 0.002, (name, sampled)
            if name == "Cone":
                rotated = call(base, "POST", "/audio/attenuations/evaluate", {"AssetPath": ASSET,
                    "Origin": {"X": 10, "Y": 20, "Z": 30}, "Rotation": {"Pitch": 0, "Yaw": 90, "Roll": 0},
                    "Locations": [{"X": 10, "Y": 70, "Z": 30}, {"X": 60, "Y": 20, "Z": 30}]})
                assert abs(rotated["samples"][0]["linear_gain"] - 1) < 0.002
                assert abs(rotated["samples"][1]["linear_gain"]) < 0.002
        settings(base, EnumSettings={"attenuation_shape": "Sphere"}, bSetShapeExtents=True,
                 ShapeExtents={"X": 100, "Y": 0, "Z": 0})
        curve(base, "attenuation", Operation="replace_inline", Keys=keys(0.75))
        settings(base, EnumSettings={"distance_algorithm": "Custom"}, bSave=True)
        assert abs(gains(base, [{"X": 550, "Y": 0, "Z": 0}])[0] - 0.75) < 0.002
        replace = {"AssetPath": ASSET, "CurveName": "attenuation", "Operation": "replace_inline", "Keys": keys(0.2)}
        reject(base, "POST", "/audio/attenuations/curves", replace)
        assert curve(base, "attenuation", Operation="replace_inline", Keys=keys(0.2), bDryRun=True)["would_change"]
        curve(base, "attenuation", Operation="replace_inline", Keys=keys(0.2), bConfirm=True, bSave=True)
        for invalid_keys in [[{"Time": -1, "Value": 1}], [{"Time": 0.5, "Value": 1}, {"Time": 0.5, "Value": 0}]]:
            reject(base, "POST", "/audio/attenuations/curves", {"AssetPath": ASSET,
                "CurveName": "attenuation", "Operation": "replace_inline", "Keys": invalid_keys, "bConfirm": True})
        assert not state(base)["dirty"]
        reject(base, "POST", "/audio/attenuations/curves", {"AssetPath": ASSET, "CurveName": "attenuation", "Operation": "clear", "bConfirm": True})
        reject(base, "POST", "/audio/attenuations/curves", {"AssetPath": ASSET, "CurveName": "priority", "Operation": "set_external", "CurvePath": ASSET})
        curve(base, "reverb_send", Operation="replace_inline", Keys=[{"Time": 0, "Value": 0.1}, {"Time": 1, "Value": 0.8}])
        reject(base, "POST", "/audio/attenuations/curves", {"AssetPath": ASSET, "CurveName": "reverb_send", "Operation": "clear"})
        assert curve(base, "reverb_send", Operation="clear", bDryRun=True)["would_change"]
        assert curve(base, "reverb_send", Operation="clear", bConfirm=True)["changed"]
        assert state(base)["curves"]["reverb_send"]["key_count"] == 0
        for name, values in [("reverb_send", (0.1, 0.8)), ("priority", (1, 0.4)),
                             ("lowpass_absorption", (0, 1)), ("highpass_absorption", (0, 1))]:
            mode = "Cubic" if name == "reverb_send" else "Constant" if name == "lowpass_absorption" else "Linear"
            curve(base, name, Operation="replace_inline", Keys=[{"Time": 0, "Value": values[0], "Interpolation": mode}, {"Time": 1, "Value": values[1], "Interpolation": mode}])
        settings(base, EnumSettings={"reverb_send_method": "CustomCurve",
                 "priority_attenuation_method": "CustomCurve", "absorption_method": "CustomCurve"}, bSave=True)
        source_dirty = call(base, "GET", "/assets/dirty-state", asset_path=EXTERNAL_CURVE)["dirty"]
        response = httpx.post(base + "/audio/attenuations/create", json={"AssetPath": EXTERNAL_PACKAGE, "bSave": True}, timeout=180)
        response.raise_for_status()
        assert response.text == EXTERNAL_ASSET
        external_created = True
        call(base, "POST", "/audio/attenuations/curves", {"AssetPath": EXTERNAL_ASSET,
             "CurveName": "priority", "Operation": "set_external", "CurvePath": EXTERNAL_CURVE})
        call(base, "PATCH", "/audio/attenuations/settings", {"AssetPath": EXTERNAL_ASSET,
             "Flags": {"priority_attenuation": True},
             "EnumSettings": {"priority_attenuation_method": "CustomCurve"}, "bSave": True})
        assert call(base, "GET", "/assets/dirty-state", asset_path=EXTERNAL_CURVE)["dirty"] == source_dirty
        verify(base)
        succeeded = True
    finally:
        if created and (args.phase != "create" or not succeeded):
            call(base, "POST", "/assets/delete", {"AssetPath": ASSET})
        if external_created and (args.phase != "create" or not succeeded):
            call(base, "POST", "/assets/delete", {"AssetPath": EXTERNAL_ASSET})


if __name__ == "__main__":
    main()
