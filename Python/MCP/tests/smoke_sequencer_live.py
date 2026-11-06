"""Run against an editor launched with -UE5MCPApiPort=8080.

Creates a uniquely named, unsaved Level Sequence and removes it afterward.
"""

import json
import os
import urllib.error
import urllib.parse
import urllib.request
import uuid


BASE_URL = os.environ.get("UE5_REST_API_URL", "http://127.0.0.1:8080").rstrip("/")


def request(method, route, payload=None, params=None, *, expect_error=False):
    url = BASE_URL + route
    if params:
        url += "?" + urllib.parse.urlencode(params)
    body = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=body, method=method)
    if body is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            result = response.read().decode()
            assert not expect_error, (route, result)
            return json.loads(result) if result.startswith(("{", "[")) else result
    except urllib.error.HTTPError as error:
        result = error.read().decode()
        assert expect_error, (route, error.code, result)
        return result


def main():
    status = request("GET", "/editor/status")
    assert status["editor_available"] and not status["is_playing"]

    name = "LS_MCP_Smoke_" + uuid.uuid4().hex[:8]
    package = f"/Game/UE5MCP_Test/{name}"
    asset_path = f"{package}.{name}"
    child_name = name + "_Child"
    child_package = f"/Game/UE5MCP_Test/{child_name}"
    child_asset = f"{child_package}.{child_name}"
    created = False
    child_created = False
    actor_path = ""
    attenuation_asset_path = ""
    try:
        result = request("POST", "/level-sequences/create", {"AssetPath": package})
        assert result == package, result
        created = True
        assert request("GET", "/level-sequences/inspect", params={"asset_path": asset_path})["binding_count"] == 0

        binding = {"AssetPath": asset_path, "Operation": "add", "Name": "SmokeActor", "ClassPath": "/Script/Engine.CameraActor"}
        assert request("POST", "/level-sequences/bindings", {**binding, "bDryRun": True})["changed"] is False
        assert request("GET", "/level-sequences/bindings", params={"asset_path": asset_path})["bindings"] == []
        guid = request("POST", "/level-sequences/bindings", binding)["binding_guid"]
        assert guid

        track = {"AssetPath": asset_path, "Operation": "add", "BindingGuid": guid, "TrackClass": "transform"}
        assert request("POST", "/level-sequences/tracks", {**track, "bDryRun": True})["changed"] is False
        assert request("GET", "/level-sequences/tracks", params={"asset_path": asset_path})["tracks"] == []
        track_index = request("POST", "/level-sequences/tracks", track)["track_index"]
        assert track_index == 0

        section = {"AssetPath": asset_path, "Operation": "add", "BindingGuid": guid,
                   "TrackIndex": track_index, "Frame": 0, "EndFrame": 30000}
        section_index = request("POST", "/level-sequences/sections", section)["section_index"]
        assert section_index == 0
        scope = {"asset_path": asset_path, "binding_guid": guid,
                 "track_index": track_index, "section_index": section_index}
        assert request("GET", "/level-sequences/keys", params=scope)["keys"] == []

        key = {"AssetPath": asset_path, "Operation": "set", "BindingGuid": guid,
               "TrackIndex": track_index, "SectionIndex": section_index,
               "ChannelIndex": 0, "Frame": 5000, "Value": 12.5}
        key_index = request("POST", "/level-sequences/keys", key)["key_index"]
        keys = request("GET", "/level-sequences/keys", params=scope)["keys"]
        assert len(keys) == 1 and keys[0]["frame"] == 5000 and keys[0]["value"] == 12.5, keys

        visibility_track = {"AssetPath": asset_path, "Operation": "add",
                            "BindingGuid": guid, "TrackClass": "visibility"}
        visibility_track_index = request("POST", "/level-sequences/tracks", visibility_track)["track_index"]
        visibility_section = {"AssetPath": asset_path, "Operation": "add", "BindingGuid": guid,
                              "TrackIndex": visibility_track_index, "Frame": 0, "EndFrame": 30000}
        visibility_section_index = request("POST", "/level-sequences/sections", visibility_section)["section_index"]
        request("POST", "/level-sequences/keys", {
            "AssetPath": asset_path, "Operation": "set", "BindingGuid": guid,
            "TrackIndex": visibility_track_index, "SectionIndex": visibility_section_index,
            "ChannelIndex": 0, "Frame": 5000, "Value": 0})

        float_track = {"AssetPath": asset_path, "Operation": "add", "BindingGuid": guid,
                       "TrackClass": "float_property", "PropertyName": "CustomTimeDilation",
                       "PropertyPath": "CustomTimeDilation"}
        float_track_index = request("POST", "/level-sequences/tracks", float_track)["track_index"]
        float_section = {"AssetPath": asset_path, "Operation": "add", "BindingGuid": guid,
                         "TrackIndex": float_track_index, "Frame": 0, "EndFrame": 30000}
        float_section_index = request("POST", "/level-sequences/sections", float_section)["section_index"]
        request("POST", "/level-sequences/keys", {
            "AssetPath": asset_path, "Operation": "set", "BindingGuid": guid,
            "TrackIndex": float_track_index, "SectionIndex": float_section_index,
            "ChannelIndex": 0, "Frame": 5000, "Value": 0.25})

        source_timing_before = request("GET", "/level-sequences/inspect", params={"asset_path": asset_path})
        evaluation = request("POST", "/level-sequences/evaluate", {
            "AssetPath": asset_path, "BindingGuid": guid, "Frame": 5000})
        assert evaluation["evaluated"] and evaluation["isolated_preview"], evaluation
        assert evaluation["actor_class"] == "/Script/Engine.CameraActor", evaluation
        assert evaluation["tick_frame"] == 5000 and evaluation["transform_key_count"] == 1, evaluation
        assert evaluation["visibility_key_count"] == 1 and evaluation["actor_hidden"], evaluation
        assert evaluation["float_property_key_count"] == 1, evaluation
        assert evaluation["float_property_name"] == "CustomTimeDilation"
        assert abs(evaluation["float_property_value"] - 0.25) < 0.001, evaluation
        assert len(evaluation["evaluated_track_classes"]) == 3, evaluation
        assert 1 <= evaluation["playback_steps"] <= 600, evaluation
        assert evaluation["sampled_display_frame"] >= evaluation["display_frame"] - 0.05, evaluation
        assert evaluation["sampled_display_frame"] - evaluation["display_frame"] <= 1.05, evaluation
        assert abs(evaluation["transform"]["location"]["x"] - 12.5) < 0.001, evaluation
        bindings_after_evaluation = request("GET", "/level-sequences/bindings", params={"asset_path": asset_path})["bindings"]
        assert bindings_after_evaluation[0]["bound_object_paths"] == [], bindings_after_evaluation
        source_timing_after = request("GET", "/level-sequences/inspect", params={"asset_path": asset_path})
        assert source_timing_after["playback_lower"] == source_timing_before["playback_lower"]
        assert source_timing_after["playback_upper"] == source_timing_before["playback_upper"]
        request("POST", "/level-sequences/evaluate", {
            "AssetPath": asset_path, "BindingGuid": "invalid", "Frame": 5000}, expect_error=True)
        request("POST", "/level-sequences/evaluate", {
            "AssetPath": asset_path, "BindingGuid": guid,
            "Frame": 5000, "bPlayOnEditorActor": True}, expect_error=True)

        request("POST", "/level-sequences/sections", {**float_section, "Operation": "remove",
                "SectionIndex": float_section_index, "bConfirm": True})
        request("POST", "/level-sequences/tracks", {**float_track, "Operation": "remove",
                "TrackIndex": float_track_index, "bConfirm": True})
        request("POST", "/level-sequences/sections", {**visibility_section, "Operation": "remove",
                "SectionIndex": visibility_section_index, "bConfirm": True})
        request("POST", "/level-sequences/tracks", {**visibility_track, "Operation": "remove",
                "TrackIndex": visibility_track_index, "bConfirm": True})

        remove_key = {**key, "Operation": "remove", "KeyIndex": key_index}
        request("POST", "/level-sequences/keys", remove_key, expect_error=True)
        assert len(request("GET", "/level-sequences/keys", params=scope)["keys"]) == 1
        assert request("POST", "/level-sequences/keys", {**remove_key, "bDryRun": True})["changed"] is False
        request("POST", "/level-sequences/keys", {**remove_key, "bConfirm": True})
        assert request("GET", "/level-sequences/keys", params=scope)["keys"] == []

        remove_section = {"AssetPath": asset_path, "Operation": "remove", "BindingGuid": guid,
                          "TrackIndex": track_index, "SectionIndex": section_index}
        request("POST", "/level-sequences/sections", {**remove_section, "bConfirm": True})
        remove_track = {"AssetPath": asset_path, "Operation": "remove", "BindingGuid": guid,
                        "TrackIndex": track_index, "bConfirm": True}
        request("POST", "/level-sequences/tracks", remove_track)

        invalid_property = {"AssetPath": asset_path, "Operation": "add", "BindingGuid": guid,
                            "TrackClass": "float_property", "PropertyName": "CustomTimeDilation",
                            "PropertyPath": "MissingProperty"}
        request("POST", "/level-sequences/tracks", invalid_property, expect_error=True)
        for track_class, scope_guid, extra, value, expected in (
            ("visibility", guid, {}, 1.0, True),
            ("float_property", guid,
             {"PropertyName": "CustomTimeDilation", "PropertyPath": "CustomTimeDilation"}, 0.5, 0.5),
            ("fade", "", {}, 0.25, 0.25),
        ):
            t = {"AssetPath": asset_path, "Operation": "add", "BindingGuid": scope_guid,
                 "TrackClass": track_class, **extra}
            ti = request("POST", "/level-sequences/tracks", t)["track_index"]
            s = {"AssetPath": asset_path, "Operation": "add", "BindingGuid": scope_guid,
                 "TrackIndex": ti, "Frame": 0, "EndFrame": 30}
            si = request("POST", "/level-sequences/sections", s)["section_index"]
            k = {"AssetPath": asset_path, "Operation": "set", "BindingGuid": scope_guid,
                 "TrackIndex": ti, "SectionIndex": si, "ChannelIndex": 0,
                 "Frame": 5, "Value": value}
            request("POST", "/level-sequences/keys", k)
            values = request("GET", "/level-sequences/keys", params={
                "asset_path": asset_path, "binding_guid": scope_guid,
                "track_index": ti, "section_index": si})["keys"]
            assert len(values) == 1 and values[0]["value"] == expected, (track_class, values)
            request("POST", "/level-sequences/sections", {**s, "Operation": "remove",
                    "SectionIndex": si, "bConfirm": True})
            request("POST", "/level-sequences/tracks", {**t, "Operation": "remove",
                    "TrackIndex": ti, "bConfirm": True})

        request("POST", "/level-sequences/bindings", {"AssetPath": asset_path,
                "Operation": "remove", "BindingGuid": guid, "bConfirm": True})

        class_spawnable = {"AssetPath": asset_path, "Operation": "add_spawnable",
                           "ClassPath": "/Script/Engine.CameraActor", "Name": "ClassOnlySmokeCamera"}
        assert request("POST", "/level-sequences/bindings", {
            **class_spawnable, "bDryRun": True})["changed"] is False
        request("POST", "/level-sequences/bindings", {
            "AssetPath": asset_path, "Operation": "add_spawnable", "Name": "MissingClass"}, expect_error=True)
        class_spawnable_guid = request("POST", "/level-sequences/bindings", class_spawnable)["binding_guid"]
        class_spawnable_bindings = request("GET", "/level-sequences/bindings", params={"asset_path": asset_path})["bindings"]
        assert any(x["guid"] == class_spawnable_guid and x["binding_type"] == "spawnable"
                   and x["template_class"] == "/Script/Engine.CameraActor"
                   for x in class_spawnable_bindings), class_spawnable_bindings
        request("POST", "/level-sequences/bindings", {"AssetPath": asset_path,
                "Operation": "remove", "BindingGuid": class_spawnable_guid, "bConfirm": True})

        camera_create = {"Operation": "create", "Label": "Smoke Cine Camera",
                         "Location": {"X": 100, "Y": 0, "Z": 200},
                         "Rotation": {"Pitch": 0, "Yaw": 45, "Roll": 0},
                         "MinFocalLength": 24, "MaxFocalLength": 85, "FocalLength": 35,
                         "MinFStop": 1.4, "MaxFStop": 16, "Aperture": 2.8,
                         "SensorWidth": 36, "SensorHeight": 24,
                         "FocusMethod": "manual", "ManualFocusDistance": 150}
        request("POST", "/cinematic/cameras", {**camera_create, "MaxFocalLength": 20}, expect_error=True)
        assert request("POST", "/cinematic/cameras", {**camera_create, "bDryRun": True})["would_create"] is True
        created_camera = request("POST", "/cinematic/cameras", camera_create)
        actor_path = created_camera["actor_path"]
        assert created_camera["focal_length"] == 35 and created_camera["sensor_width"] == 36
        placed_camera = request("GET", "/cinematic/cameras", params={"actor_path": actor_path})
        assert abs(placed_camera["aperture"] - 2.8) < 0.0001 and placed_camera["manual_focus_distance"] == 150, placed_camera
        camera_edit = {"Operation": "set", "ActorPath": actor_path,
                       "FocalLength": 50, "ManualFocusDistance": 200}
        assert request("PATCH", "/cinematic/cameras", {**camera_edit, "bDryRun": True})["changed"] is False
        assert request("GET", "/cinematic/cameras", params={"actor_path": actor_path})["focal_length"] == 35
        request("PATCH", "/cinematic/cameras", camera_edit)
        request("PATCH", "/cinematic/cameras", {**camera_edit, "FocalLength": 200}, expect_error=True)
        assert request("GET", "/cinematic/cameras", params={"actor_path": actor_path})["focal_length"] == 50
        placed_binding = {"AssetPath": asset_path, "Operation": "add", "ActorPath": actor_path}
        placed_guid = request("POST", "/level-sequences/bindings", placed_binding)["binding_guid"]
        bindings = request("GET", "/level-sequences/bindings", params={"asset_path": asset_path})["bindings"]
        assert any(x["guid"] == placed_guid and actor_path in x["bound_object_paths"]
                   for x in bindings), bindings
        placed_track = {"AssetPath": asset_path, "Operation": "add",
                        "BindingGuid": placed_guid, "TrackClass": "transform"}
        placed_track_index = request("POST", "/level-sequences/tracks", placed_track)["track_index"]
        placed_section = {"AssetPath": asset_path, "Operation": "add", "BindingGuid": placed_guid,
                          "TrackIndex": placed_track_index, "Frame": 0, "EndFrame": 30000}
        placed_section_index = request("POST", "/level-sequences/sections", placed_section)["section_index"]
        request("POST", "/level-sequences/keys", {
            "AssetPath": asset_path, "Operation": "set", "BindingGuid": placed_guid,
            "TrackIndex": placed_track_index, "SectionIndex": placed_section_index,
            "ChannelIndex": 0, "Frame": 5000, "Value": 125.0})
        placed_visibility_track = {"AssetPath": asset_path, "Operation": "add",
                                   "BindingGuid": placed_guid, "TrackClass": "visibility"}
        placed_visibility_track_index = request("POST", "/level-sequences/tracks", placed_visibility_track)["track_index"]
        placed_visibility_section = {"AssetPath": asset_path, "Operation": "add", "BindingGuid": placed_guid,
                                     "TrackIndex": placed_visibility_track_index, "Frame": 0, "EndFrame": 30000}
        placed_visibility_section_index = request("POST", "/level-sequences/sections", placed_visibility_section)["section_index"]
        request("POST", "/level-sequences/keys", {
            "AssetPath": asset_path, "Operation": "set", "BindingGuid": placed_guid,
            "TrackIndex": placed_visibility_track_index, "SectionIndex": placed_visibility_section_index,
            "ChannelIndex": 0, "Frame": 5000, "Value": 0})
        placed_float_track = {"AssetPath": asset_path, "Operation": "add", "BindingGuid": placed_guid,
                              "TrackClass": "float_property", "PropertyName": "CustomTimeDilation",
                              "PropertyPath": "CustomTimeDilation"}
        placed_float_track_index = request("POST", "/level-sequences/tracks", placed_float_track)["track_index"]
        placed_float_section = {"AssetPath": asset_path, "Operation": "add", "BindingGuid": placed_guid,
                                "TrackIndex": placed_float_track_index, "Frame": 0, "EndFrame": 30000}
        placed_float_section_index = request("POST", "/level-sequences/sections", placed_float_section)["section_index"]
        request("POST", "/level-sequences/keys", {
            "AssetPath": asset_path, "Operation": "set", "BindingGuid": placed_guid,
            "TrackIndex": placed_float_track_index, "SectionIndex": placed_float_section_index,
            "ChannelIndex": 0, "Frame": 5000, "Value": 0.25})
        placed_camera_before = request("GET", "/cinematic/cameras", params={"actor_path": actor_path})
        placed_evaluation = request("POST", "/level-sequences/evaluate", {
            "AssetPath": asset_path, "BindingGuid": placed_guid,
            "ActorPath": actor_path, "Frame": 5000})
        assert placed_evaluation["source_actor_path"] == actor_path, placed_evaluation
        assert abs(placed_evaluation["transform"]["location"]["x"] - 125.0) < 0.001, placed_evaluation
        assert placed_evaluation["actor_hidden"] and abs(placed_evaluation["float_property_value"] - 0.25) < 0.001, placed_evaluation
        direct_evaluation = request("POST", "/level-sequences/evaluate", {
            "AssetPath": asset_path, "BindingGuid": placed_guid, "ActorPath": actor_path,
            "Frame": 5000, "bPlayOnEditorActor": True})
        assert direct_evaluation["evaluation_mode"] == "editor_actor", direct_evaluation
        assert direct_evaluation["isolated_preview"] is False, direct_evaluation
        assert direct_evaluation["source_actor_unchanged"]
        assert direct_evaluation["source_actor_visibility_restored"]
        assert direct_evaluation["source_actor_float_property_restored"]
        assert direct_evaluation["source_package_dirty_restored"]
        assert abs(direct_evaluation["transform"]["location"]["x"] - 125.0) < 0.001, direct_evaluation
        placed_camera_after = request("GET", "/cinematic/cameras", params={"actor_path": actor_path})
        for field in ("X", "Y", "Z"):
            assert abs(placed_camera_after["location"][field] - placed_camera_before["location"][field]) < 0.001, placed_camera_after
        for field in ("Pitch", "Yaw", "Roll"):
            assert abs(placed_camera_after["rotation"][field] - placed_camera_before["rotation"][field]) < 0.001, placed_camera_after
        request("POST", "/level-sequences/sections", {**placed_float_section, "Operation": "remove",
                "SectionIndex": placed_float_section_index, "bConfirm": True})
        request("POST", "/level-sequences/tracks", {**placed_float_track, "Operation": "remove",
                "TrackIndex": placed_float_track_index, "bConfirm": True})
        request("POST", "/level-sequences/sections", {**placed_visibility_section, "Operation": "remove",
                "SectionIndex": placed_visibility_section_index, "bConfirm": True})
        request("POST", "/level-sequences/tracks", {**placed_visibility_track, "Operation": "remove",
                "TrackIndex": placed_visibility_track_index, "bConfirm": True})
        request("POST", "/level-sequences/sections", {**placed_section, "Operation": "remove",
                "SectionIndex": placed_section_index, "bConfirm": True})
        request("POST", "/level-sequences/tracks", {**placed_track, "Operation": "remove",
                "TrackIndex": placed_track_index, "bConfirm": True})
        request("POST", "/level-sequences/bindings", placed_binding, expect_error=True)
        request("POST", "/level-sequences/bindings", {"AssetPath": asset_path,
                "Operation": "remove", "BindingGuid": placed_guid, "bConfirm": True})

        spawnable = {"AssetPath": asset_path, "Operation": "add_spawnable",
                     "ActorPath": actor_path, "Name": "SmokeSpawnableCamera"}
        assert request("POST", "/level-sequences/bindings", {**spawnable, "bDryRun": True})["changed"] is False
        spawnable_guid = request("POST", "/level-sequences/bindings", spawnable)["binding_guid"]
        bindings = request("GET", "/level-sequences/bindings", params={"asset_path": asset_path})["bindings"]
        assert any(x["guid"] == spawnable_guid and x["binding_type"] == "spawnable"
                   and x["template_class"] == "/Script/CinematicCamera.CineCameraActor" for x in bindings), bindings
        template_camera = request("GET", "/cinematic/cameras", params={
            "asset_path": asset_path, "binding_guid": spawnable_guid})
        assert template_camera["is_template"] and template_camera["focal_length"] == 50, template_camera
        request("PATCH", "/cinematic/cameras", {"Operation": "set", "AssetPath": asset_path,
                "BindingGuid": spawnable_guid, "FocalLength": 70, "ManualFocusDistance": 250})
        assert request("GET", "/cinematic/cameras", params={
            "asset_path": asset_path, "binding_guid": spawnable_guid})["focal_length"] == 70
        assert request("GET", "/cinematic/cameras", params={"actor_path": actor_path})["focal_length"] == 50
        assert request("GET", "/cinematic/camera-cuts", params={"asset_path": asset_path})["camera_cuts"] == []
        cut = {"AssetPath": asset_path, "Operation": "add", "CameraBindingGuid": spawnable_guid,
               "Frame": 0, "Duration": 30}
        request("POST", "/cinematic/camera-cuts", {**cut, "CameraBindingGuid": str(uuid.uuid4())}, expect_error=True)
        assert request("POST", "/cinematic/camera-cuts", {**cut, "bDryRun": True})["changed"] is False
        cut_index = request("POST", "/cinematic/camera-cuts", cut)["section_index"]
        cuts = request("GET", "/cinematic/camera-cuts", params={"asset_path": asset_path})["camera_cuts"]
        assert len(cuts) == 1 and cuts[0]["camera_binding_guid"] == spawnable_guid
        assert cuts[0]["lower"] == 0 and cuts[0]["upper"] == 30, cuts
        request("POST", "/cinematic/camera-cuts", {**cut, "Frame": 15}, expect_error=True)
        request("POST", "/level-sequences/bindings", {"AssetPath": asset_path,
                "Operation": "remove", "BindingGuid": spawnable_guid, "bConfirm": True}, expect_error=True)
        remove_cut = {"AssetPath": asset_path, "Operation": "remove", "SectionIndex": cut_index}
        request("POST", "/cinematic/camera-cuts", remove_cut, expect_error=True)
        assert request("POST", "/cinematic/camera-cuts", {**remove_cut, "bDryRun": True})["changed"] is False
        request("POST", "/cinematic/camera-cuts", {**remove_cut, "bConfirm": True})
        request("POST", "/level-sequences/bindings", {"AssetPath": asset_path,
                "Operation": "remove", "BindingGuid": spawnable_guid, "bConfirm": True})
        request("DELETE", "/editor/actors", {"ActorPath": actor_path, "bConfirm": True})
        actor_path = ""

        skeletal_guid = request("POST", "/level-sequences/bindings", {
            "AssetPath": asset_path, "Operation": "add", "Name": "SmokeSkeletal",
            "ClassPath": "/Script/Engine.SkeletalMeshActor"})["binding_guid"]
        for track_class, scope_guid, source, target_mesh, weight in (
            ("audio", "", "/Engine/EditorSounds/Notifications/CompileSuccess.CompileSuccess", "", 0.8),
            ("skeletal_animation", skeletal_guid,
             "/Game/Characters/Mannequins/Anims/Unarmed/MM_Idle.MM_Idle",
             "/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple.SKM_Manny_Simple", 0.6),
        ):
            t = {"AssetPath": asset_path, "Operation": "add",
                 "BindingGuid": scope_guid, "TrackClass": track_class}
            ti = request("POST", "/level-sequences/tracks", t)["track_index"]
            s = {"AssetPath": asset_path, "Operation": "add", "BindingGuid": scope_guid,
                 "TrackIndex": ti, "Frame": 0, "EndFrame": 30}
            request("POST", "/level-sequences/sections", s, expect_error=True)
            si = request("POST", "/level-sequences/sections", {
                **s, "SourceAssetPath": source,
                "TargetSkeletalMeshPath": target_mesh})["section_index"]
            sections = request("GET", "/level-sequences/sections", params={"asset_path": asset_path})["sections"]
            animation_section = next((x for x in sections if x["binding_guid"] == scope_guid
                                      and x["track_index"] == ti and x["section_index"] == si
                                      and x["source_asset_path"] == source), None)
            assert animation_section, (track_class, sections)
            if track_class == "skeletal_animation":
                animation_settings = {
                    "AssetPath": asset_path, "Operation": "set_animation",
                    "BindingGuid": scope_guid, "TrackIndex": ti, "SectionIndex": si,
                    "bSetAnimationPlayRate": True, "AnimationPlayRate": 0.5,
                    "bSetAnimationReverse": True, "bAnimationReverse": True,
                    "bSetAnimationSlotName": True, "AnimationSlotName": "DefaultSlot",
                    "bSetAnimationSkipNotifiers": True, "bAnimationSkipNotifiers": True,
                    "bSetAnimationForceCustomMode": True, "bAnimationForceCustomMode": True,
                    "bSetAnimationFirstLoopStartOffset": True, "AnimationFirstLoopStartOffset": 10,
                    "bSetAnimationStartOffset": True, "AnimationStartOffset": 20,
                    "bSetAnimationEndOffset": True, "AnimationEndOffset": 30,
                }
                assert request("POST", "/level-sequences/sections", {
                    **animation_settings, "bDryRun": True})["dry_run"] is True
                before_settings = next(x for x in request("GET", "/level-sequences/sections", params={
                    "asset_path": asset_path})["sections"] if x["binding_guid"] == scope_guid
                    and x["track_index"] == ti and x["section_index"] == si)["animation_settings"]
                assert before_settings["reverse"] is False and before_settings["play_rate"] == 1.0, before_settings
                request("POST", "/level-sequences/sections", {
                    **animation_settings, "AnimationPlayRate": 0}, expect_error=True)
                request("POST", "/level-sequences/sections", animation_settings)
                updated_animation_section = next(x for x in request("GET", "/level-sequences/sections", params={
                    "asset_path": asset_path})["sections"] if x["binding_guid"] == scope_guid
                    and x["track_index"] == ti and x["section_index"] == si)
                after_settings = updated_animation_section["animation_settings"]
                assert updated_animation_section["upper"] == 60, updated_animation_section
                assert abs(after_settings["play_rate"] - 0.5) < 0.0001, after_settings
                assert after_settings["reverse"] and after_settings["slot_name"] == "DefaultSlot", after_settings
                assert after_settings["skip_anim_notifiers"] and after_settings["force_custom_mode"], after_settings
                assert after_settings["first_loop_start_offset"] == 10
                assert after_settings["start_offset"] == 20 and after_settings["end_offset"] == 30
            elif track_class == "audio":
                attenuation_package = f"/Game/UE5MCP_Test/{name}_Attenuation"
                attenuation_preview = request("POST", "/audio/attenuations/create", {
                    "AssetPath": attenuation_package, "bDryRun": True})
                assert attenuation_preview["would_create"] is True, attenuation_preview
                attenuation_asset_path = request("POST", "/audio/attenuations/create", {
                    "AssetPath": attenuation_package})
                assert request("POST", "/audio/validate", {
                    "AssetPath": attenuation_asset_path})["valid"] is True
                assert request("GET", "/audio/attenuations/inspect", params={
                    "asset_path": attenuation_asset_path})
                before_audio = next(x for x in request("GET", "/level-sequences/sections", params={
                    "asset_path": asset_path})["sections"] if x["track_index"] == ti
                    and x["section_index"] == si)["audio_settings"]
                target_looping = not before_audio["looping"]
                target_suppress_subtitles = not before_audio["suppress_subtitles"]
                target_override_attenuation = not before_audio["override_attenuation"]
                audio_settings = {
                    "AssetPath": asset_path, "Operation": "set_audio",
                    "BindingGuid": scope_guid, "TrackIndex": ti, "SectionIndex": si,
                    "bSetAudioStartOffset": True, "AudioStartOffset": 1,
                    "bSetAudioLooping": True, "bAudioLooping": target_looping,
                    "bSetAudioSuppressSubtitles": True, "bAudioSuppressSubtitles": target_suppress_subtitles,
                    "bSetAudioOverrideAttenuation": True, "bAudioOverrideAttenuation": target_override_attenuation,
                    "bSetAudioAttenuationSettings": True, "AudioAttenuationPath": attenuation_asset_path,
                }
                assert request("POST", "/level-sequences/sections", {
                    **audio_settings, "bDryRun": True})["dry_run"] is True
                dry_run_audio = next(x for x in request("GET", "/level-sequences/sections", params={
                    "asset_path": asset_path})["sections"] if x["track_index"] == ti
                    and x["section_index"] == si)["audio_settings"]
                assert dry_run_audio == before_audio, dry_run_audio
                assert before_audio["start_offset"] == 0, before_audio
                request("POST", "/level-sequences/sections", {
                    **audio_settings, "AudioStartOffset": 2147483647}, expect_error=True)
                request("POST", "/level-sequences/sections", audio_settings)
                after_audio = next(x for x in request("GET", "/level-sequences/sections", params={
                    "asset_path": asset_path})["sections"] if x["track_index"] == ti
                    and x["section_index"] == si)["audio_settings"]
                assert after_audio["start_offset"] == 1, after_audio
                assert after_audio["looping"] == target_looping, after_audio
                assert after_audio["suppress_subtitles"] == target_suppress_subtitles, after_audio
                assert after_audio["override_attenuation"] == target_override_attenuation, after_audio
                assert after_audio["attenuation_path"] == attenuation_asset_path, after_audio
            k = {"AssetPath": asset_path, "Operation": "set", "BindingGuid": scope_guid,
                 "TrackIndex": ti, "SectionIndex": si, "ChannelIndex": 0,
                 "Frame": 5, "Value": weight}
            request("POST", "/level-sequences/keys", k)
            values = request("GET", "/level-sequences/keys", params={
                "asset_path": asset_path, "binding_guid": scope_guid,
                "track_index": ti, "section_index": si})["keys"]
            assert any(abs(x["value"] - weight) < 0.0001 for x in values), (track_class, values)
            request("POST", "/level-sequences/sections", {**s, "Operation": "remove",
                    "SectionIndex": si, "bConfirm": True})
            request("POST", "/level-sequences/tracks", {**t, "Operation": "remove",
                    "TrackIndex": ti, "bConfirm": True})
            if track_class == "audio" and attenuation_asset_path:
                request("POST", "/assets/delete", {"AssetPath": attenuation_asset_path})
                attenuation_asset_path = ""
        request("POST", "/level-sequences/bindings", {"AssetPath": asset_path,
                "Operation": "remove", "BindingGuid": skeletal_guid, "bConfirm": True})
        assert request("GET", "/level-sequences/bindings", params={"asset_path": asset_path})["bindings"] == []

        assert request("POST", "/level-sequences/create", {"AssetPath": child_package}) == child_package
        child_created = True
        shot = {"AssetPath": asset_path, "Operation": "add", "SequencePath": child_asset,
                "ShotName": 'Shot "One"', "Frame": 0, "Duration": 30, "RowIndex": 0}
        assert request("POST", "/cinematic/shots", {**shot, "bDryRun": True})["changed"] is False
        assert request("GET", "/cinematic/shots", params={"asset_path": asset_path})["shots"] == []
        shot_index = request("POST", "/cinematic/shots", shot)["section_index"]
        shots = request("GET", "/cinematic/shots", params={"asset_path": asset_path})["shots"]
        assert len(shots) == 1 and shots[0]["shot_name"] == 'Shot "One"', shots
        assert shots[0]["sequence_path"] == child_asset, shots
        request("POST", "/cinematic/shots", {"AssetPath": child_asset, "Operation": "add",
                "SequencePath": asset_path, "Frame": 0, "Duration": 20}, expect_error=True)
        request("POST", "/level-sequences/subsequences", {"AssetPath": child_asset,
                "Operation": "add", "SequencePath": asset_path,
                "Frame": 0, "Duration": 20}, expect_error=True)
        request("POST", "/cinematic/shots", {"AssetPath": asset_path, "Operation": "rename",
                "SectionIndex": shot_index, "ShotName": "Shot Two"})
        assert request("GET", "/cinematic/shots", params={"asset_path": asset_path})["shots"][0]["shot_name"] == "Shot Two"
        remove_shot = {"AssetPath": asset_path, "Operation": "remove", "SectionIndex": shot_index}
        request("POST", "/cinematic/shots", remove_shot, expect_error=True)
        assert request("POST", "/cinematic/shots", {**remove_shot, "bDryRun": True})["changed"] is False
        request("POST", "/cinematic/shots", {**remove_shot, "bConfirm": True})
        assert request("GET", "/cinematic/shots", params={"asset_path": asset_path})["shots"] == []
        print("Sequencer live smoke passed")
    finally:
        if child_created:
            request("POST", "/assets/delete", {"AssetPath": child_asset})
        if created:
            request("POST", "/assets/delete", {"AssetPath": asset_path})
        if actor_path:
            request("DELETE", "/editor/actors", {"ActorPath": actor_path, "bConfirm": True})
        if attenuation_asset_path:
            request("POST", "/assets/delete", {"AssetPath": attenuation_asset_path})


if __name__ == "__main__":
    main()
