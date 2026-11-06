"""Verify saved Level Sequence bindings, keys, templates, and section settings survive an editor restart.

This starts two command-line editor sessions on port 8080 and deletes the
uniquely named test asset after verification. Run only when that port is free.
"""

import os
from pathlib import Path
import subprocess
import time
import urllib.error
import uuid

from smoke_sequencer_live import request


PROJECT = Path(__file__).resolve().parents[5]
EDITOR = Path(os.environ.get(
    "UE5_EDITOR_CMD",
    r"C:\Programs\Unreal\UE_5.7\Engine\Binaries\Win64\UnrealEditor-Cmd.exe",
))


def editor_status():
    try:
        return request("GET", "/editor/status")
    except (urllib.error.URLError, TimeoutError, OSError):
        return None


def start_editor():
    process = subprocess.Popen(
        [str(EDITOR), str(PROJECT / "DemoForPlugin.uproject"),
         "-nullrhi", "-unattended", "-nop4", "-nosplash", "-UE5MCPApiPort=8080"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    deadline = time.monotonic() + 120
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"Editor exited before API startup: {process.returncode}")
        if editor_status():
            return process
        time.sleep(0.5)
    process.terminate()
    process.wait(timeout=10)
    raise TimeoutError("Editor API did not start within 120 seconds")


def stop_editor(process):
    if process is None or process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=15)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=10)
    deadline = time.monotonic() + 10
    while editor_status() and time.monotonic() < deadline:
        time.sleep(0.25)


def main():
    assert editor_status() is None, "Port 8080 already has an Unreal API listener"
    name = "LS_MCP_Persist_" + uuid.uuid4().hex[:8]
    package = f"/Game/UE5MCP_Test/{name}"
    asset_path = f"{package}.{name}"
    asset_file = PROJECT / "Content" / "UE5MCP_Test" / f"{name}.uasset"
    process = None
    created = False
    camera_source = ""
    attenuation_asset_path = ""
    try:
        process = start_editor()
        actors = request("GET", "/editor/actors", params={"limit": 300})
        assert actors, "No placed actor is available for persistence verification"
        actor = next((x for x in actors if x["class"] == "/Script/Engine.PlayerStart"), actors[0])
        actor_path = actor["path"]

        assert request("POST", "/level-sequences/create", {"AssetPath": package}) == package
        created = True
        guid = request("POST", "/level-sequences/bindings", {
            "AssetPath": asset_path, "Operation": "add", "ActorPath": actor_path})["binding_guid"]
        track_index = request("POST", "/level-sequences/tracks", {
            "AssetPath": asset_path, "Operation": "add", "BindingGuid": guid,
            "TrackClass": "transform"})["track_index"]
        section_index = request("POST", "/level-sequences/sections", {
            "AssetPath": asset_path, "Operation": "add", "BindingGuid": guid,
            "TrackIndex": track_index, "Frame": 0, "EndFrame": 30})["section_index"]
        request("POST", "/level-sequences/keys", {
            "AssetPath": asset_path, "Operation": "set", "BindingGuid": guid,
            "TrackIndex": track_index, "SectionIndex": section_index,
            "ChannelIndex": 0, "Frame": 5, "Value": 31.25})
        animation_guid = request("POST", "/level-sequences/bindings", {
            "AssetPath": asset_path, "Operation": "add", "Name": "PersistenceSkeletalActor",
            "ClassPath": "/Script/Engine.SkeletalMeshActor"})["binding_guid"]
        animation_track_index = request("POST", "/level-sequences/tracks", {
            "AssetPath": asset_path, "Operation": "add", "BindingGuid": animation_guid,
            "TrackClass": "skeletal_animation"})["track_index"]
        animation_section_index = request("POST", "/level-sequences/sections", {
            "AssetPath": asset_path, "Operation": "add", "BindingGuid": animation_guid,
            "TrackIndex": animation_track_index, "Frame": 0, "EndFrame": 30000,
            "SourceAssetPath": "/Game/Characters/Mannequins/Anims/Unarmed/MM_Idle.MM_Idle",
            "TargetSkeletalMeshPath": "/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple.SKM_Manny_Simple"})["section_index"]
        animation_settings = {
            "AssetPath": asset_path, "Operation": "set_animation", "BindingGuid": animation_guid,
            "TrackIndex": animation_track_index, "SectionIndex": animation_section_index,
            "bSetAnimationPlayRate": True, "AnimationPlayRate": 0.75,
            "bSetAnimationReverse": True, "bAnimationReverse": True,
            "bSetAnimationSlotName": True, "AnimationSlotName": "DefaultSlot",
            "bSetAnimationSkipNotifiers": True, "bAnimationSkipNotifiers": True,
            "bSetAnimationForceCustomMode": True, "bAnimationForceCustomMode": True,
            "bSetAnimationFirstLoopStartOffset": True, "AnimationFirstLoopStartOffset": 10,
            "bSetAnimationStartOffset": True, "AnimationStartOffset": 20,
            "bSetAnimationEndOffset": True, "AnimationEndOffset": 30,
            "bSave": True,
        }
        request("POST", "/level-sequences/sections", animation_settings)
        audio_track_index = request("POST", "/level-sequences/tracks", {
            "AssetPath": asset_path, "Operation": "add", "TrackClass": "audio"})["track_index"]
        audio_section_index = request("POST", "/level-sequences/sections", {
            "AssetPath": asset_path, "Operation": "add", "TrackIndex": audio_track_index,
            "Frame": 0, "EndFrame": 30000,
            "SourceAssetPath": "/Engine/EditorSounds/Notifications/CompileSuccess.CompileSuccess"})["section_index"]
        initial_audio_section = next(x for x in request("GET", "/level-sequences/sections", params={
            "asset_path": asset_path})["sections"] if x["binding_guid"] == ""
            and x["track_index"] == audio_track_index and x["section_index"] == audio_section_index)
        initial_audio_settings = initial_audio_section["audio_settings"]
        attenuation_asset_path = request("POST", "/audio/attenuations/create", {
            "AssetPath": package + "_Attenuation", "bSave": True})
        persisted_audio_settings = {
            "AssetPath": asset_path, "Operation": "set_audio", "TrackIndex": audio_track_index,
            "SectionIndex": audio_section_index,
            "bSetAudioStartOffset": True, "AudioStartOffset": 1,
            "bSetAudioLooping": True, "bAudioLooping": not initial_audio_settings["looping"],
            "bSetAudioSuppressSubtitles": True,
            "bAudioSuppressSubtitles": not initial_audio_settings["suppress_subtitles"],
            "bSetAudioOverrideAttenuation": True,
            "bAudioOverrideAttenuation": not initial_audio_settings["override_attenuation"],
            "bSetAudioAttenuationSettings": True,
            "AudioAttenuationPath": attenuation_asset_path,
            "bSave": True,
        }
        request("POST", "/level-sequences/sections", persisted_audio_settings)
        camera_source = request("POST", "/cinematic/cameras", {
            "Operation": "create", "Label": "Persistence Cine Camera",
            "MinFocalLength": 24, "MaxFocalLength": 85, "FocalLength": 35,
            "MinFStop": 1.4, "MaxFStop": 16, "Aperture": 2.8,
            "SensorWidth": 36, "SensorHeight": 24,
            "FocusMethod": "manual", "ManualFocusDistance": 150})["actor_path"]
        camera_guid = request("POST", "/level-sequences/bindings", {
            "AssetPath": asset_path, "Operation": "add_spawnable",
            "ActorPath": camera_source, "Name": "PersistenceCamera"})["binding_guid"]
        class_spawnable_guid = request("POST", "/level-sequences/bindings", {
            "AssetPath": asset_path, "Operation": "add_spawnable",
            "ClassPath": "/Script/Engine.CameraActor", "Name": "ClassOnlyPersistenceCamera"})["binding_guid"]
        request("PATCH", "/cinematic/cameras", {"Operation": "set",
                "AssetPath": asset_path, "BindingGuid": camera_guid,
                "FocalLength": 70, "ManualFocusDistance": 250})
        request("POST", "/cinematic/camera-cuts", {
            "AssetPath": asset_path, "Operation": "add", "CameraBindingGuid": camera_guid,
            "Frame": 0, "Duration": 30, "bSave": True})
        request("DELETE", "/editor/actors", {"ActorPath": camera_source, "bConfirm": True})
        camera_source = ""
        assert asset_file.exists(), f"Sequence was not saved: {asset_file}"

        stop_editor(process)
        process = start_editor()
        bindings = request("GET", "/level-sequences/bindings", params={"asset_path": asset_path})["bindings"]
        assert any(x["guid"] == guid and actor_path in x["bound_object_paths"]
                   for x in bindings), bindings
        assert any(x["guid"] == camera_guid and x["binding_type"] == "spawnable"
                   and x["template_class"] == "/Script/CinematicCamera.CineCameraActor" for x in bindings), bindings
        assert any(x["guid"] == class_spawnable_guid and x["binding_type"] == "spawnable"
                   and x["template_class"] == "/Script/Engine.CameraActor" for x in bindings), bindings
        animation_sections = request("GET", "/level-sequences/sections", params={"asset_path": asset_path})["sections"]
        animation_section = next(x for x in animation_sections if x["binding_guid"] == animation_guid
                                 and x["track_index"] == animation_track_index
                                 and x["section_index"] == animation_section_index)
        assert animation_section["upper"] == 40000, animation_section
        settings = animation_section["animation_settings"]
        assert abs(settings["play_rate"] - 0.75) < 0.0001, settings
        assert settings["reverse"] and settings["slot_name"] == "DefaultSlot", settings
        assert settings["skip_anim_notifiers"] and settings["force_custom_mode"], settings
        assert settings["first_loop_start_offset"] == 10
        assert settings["start_offset"] == 20 and settings["end_offset"] == 30
        persisted_audio_section = next(x for x in animation_sections if x["binding_guid"] == ""
                                       and x["track_index"] == audio_track_index
                                       and x["section_index"] == audio_section_index)
        audio_settings = persisted_audio_section["audio_settings"]
        assert audio_settings["start_offset"] == 1, audio_settings
        assert audio_settings["looping"] == persisted_audio_settings["bAudioLooping"], audio_settings
        assert audio_settings["suppress_subtitles"] == persisted_audio_settings["bAudioSuppressSubtitles"], audio_settings
        assert audio_settings["override_attenuation"] == persisted_audio_settings["bAudioOverrideAttenuation"], audio_settings
        assert audio_settings["attenuation_path"] == attenuation_asset_path, audio_settings
        assert request("POST", "/audio/validate", {
            "AssetPath": attenuation_asset_path})["valid"] is True
        camera = request("GET", "/cinematic/cameras", params={
            "asset_path": asset_path, "binding_guid": camera_guid})
        assert camera["is_template"] and camera["focal_length"] == 70
        assert camera["manual_focus_distance"] == 250 and camera["sensor_width"] == 36, camera
        keys = request("GET", "/level-sequences/keys", params={
            "asset_path": asset_path, "binding_guid": guid,
            "track_index": track_index, "section_index": section_index})["keys"]
        assert any(x["frame"] == 5 and x["value"] == 31.25 for x in keys), keys
        cuts = request("GET", "/cinematic/camera-cuts", params={"asset_path": asset_path})["camera_cuts"]
        assert len(cuts) == 1 and cuts[0]["camera_binding_guid"] == camera_guid
        assert cuts[0]["lower"] == 0 and cuts[0]["upper"] == 30, cuts
        request("POST", "/assets/delete", {"AssetPath": asset_path})
        created = False
        assert not asset_file.exists(), f"Test asset was not deleted: {asset_file}"
        request("POST", "/assets/delete", {"AssetPath": attenuation_asset_path})
        attenuation_asset_path = ""
        print("Sequencer persistence smoke passed")
    finally:
        if camera_source and process is not None and process.poll() is None:
            try:
                request("DELETE", "/editor/actors", {"ActorPath": camera_source, "bConfirm": True})
            except Exception as error:
                print(f"Source camera cleanup failed: {camera_source}: {error}")
        if created and process is not None and process.poll() is None:
            try:
                request("POST", "/assets/delete", {"AssetPath": asset_path})
            except Exception as error:
                print(f"Test asset cleanup failed: {asset_path}: {error}")
        if attenuation_asset_path and process is not None and process.poll() is None:
            try:
                request("POST", "/assets/delete", {"AssetPath": attenuation_asset_path})
            except Exception as error:
                print(f"Attenuation cleanup failed: {attenuation_asset_path}: {error}")
        stop_editor(process)


if __name__ == "__main__":
    main()
