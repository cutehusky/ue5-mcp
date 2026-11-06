"""Level Sequences, camera cuts and takes."""
import httpx

from . import app
from .app import merged_tool
from .app import mcp, _asset_request


@mcp.tool()
def inspect_level_sequence(asset_path: str) -> str:
    """Inspect a Level Sequence's Movie Scene timing, bindings, tracks, and sections."""
    return httpx.get(f"{app.BASE_URL}/level-sequences/inspect", params={"asset_path": asset_path}).text


@mcp.tool()
def create_level_sequence(asset_path: str) -> str:
    """Create an empty Level Sequence asset."""
    return httpx.post(f"{app.BASE_URL}/level-sequences/create", json={"AssetPath": asset_path}).text


@mcp.tool()
def edit_level_sequence_settings(asset_path: str, properties: dict, save: bool = False) -> str:
    """Edit reflected Movie Scene settings such as playback range or display rate."""
    return _asset_request("level-sequences/settings", asset_path, properties, save=save)


@mcp.tool()
def list_level_sequence_bindings(asset_path: str) -> str:
    """List Level Sequence object bindings and their track counts."""
    return httpx.get(f"{app.BASE_URL}/level-sequences/bindings", params={"asset_path": asset_path}).text


@mcp.tool()
def list_level_sequence_tracks(asset_path: str) -> str:
    """List master and object-bound Level Sequence tracks with section counts."""
    return httpx.get(f"{app.BASE_URL}/level-sequences/tracks", params={"asset_path": asset_path}).text


@mcp.tool()
def list_level_sequence_sections(asset_path: str) -> str:
    """List Level Sequence sections, frame ranges, rows, bindings, and channel counts."""
    return httpx.get(f"{app.BASE_URL}/level-sequences/sections", params={"asset_path": asset_path}).text


@mcp.tool()
def list_level_sequence_camera_cuts(asset_path: str) -> str:
    """List Level Sequence camera-cut sections and referenced camera bindings."""
    return httpx.get(f"{app.BASE_URL}/cinematic/camera-cuts", params={"asset_path": asset_path}).text


@mcp.tool()
def inspect_cinematic_camera(actor_path: str = "", asset_path: str = "",
                             binding_guid: str = "") -> str:
    """Inspect a placed CineCameraActor or a Level Sequence camera binding/template."""
    return httpx.get(f"{app.BASE_URL}/cinematic/cameras", params={
        "actor_path": actor_path, "asset_path": asset_path,
        "binding_guid": binding_guid
    }).text


@mcp.tool()
def create_cinematic_camera(location: dict | None = None, rotation: dict | None = None,
                            label: str = "", focal_length: float = -1.0,
                            aperture: float = -1.0, min_focal_length: float = -1.0,
                            max_focal_length: float = -1.0, min_f_stop: float = -1.0,
                            max_f_stop: float = -1.0, sensor_width: float = -1.0,
                            sensor_height: float = -1.0, manual_focus_distance: float = -1.0,
                            focus_method: str = "", focus_actor_path: str = "",
                            dry_run: bool = False, save: bool = False) -> str:
    """Create a placed CineCameraActor with validated lens, filmback, and focus settings."""
    return httpx.post(f"{app.BASE_URL}/cinematic/cameras", json={
        "Operation": "create", "Location": location or {"X": 0, "Y": 0, "Z": 0},
        "Rotation": rotation or {"Pitch": 0, "Yaw": 0, "Roll": 0},
        "Label": label, "FocalLength": focal_length, "Aperture": aperture,
        "MinFocalLength": min_focal_length, "MaxFocalLength": max_focal_length,
        "MinFStop": min_f_stop, "MaxFStop": max_f_stop,
        "SensorWidth": sensor_width, "SensorHeight": sensor_height,
        "ManualFocusDistance": manual_focus_distance,
        "FocusMethod": focus_method, "FocusActorPath": focus_actor_path,
        "bDryRun": dry_run, "bSave": save
    }).text


@mcp.tool()
def edit_cinematic_camera(actor_path: str = "", asset_path: str = "",
                          binding_guid: str = "", label: str = "",
                          location: dict | None = None, rotation: dict | None = None,
                          focal_length: float = -1.0, aperture: float = -1.0,
                          min_focal_length: float = -1.0, max_focal_length: float = -1.0,
                          min_f_stop: float = -1.0, max_f_stop: float = -1.0,
                          sensor_width: float = -1.0, sensor_height: float = -1.0,
                          manual_focus_distance: float = -1.0, focus_method: str = "",
                          focus_actor_path: str = "", dry_run: bool = False,
                          save: bool = False) -> str:
    """Edit a placed or sequence-template CineCameraActor; pass asset_path and binding_guid for a template."""
    return httpx.patch(f"{app.BASE_URL}/cinematic/cameras", json={
        "Operation": "set", "ActorPath": actor_path, "AssetPath": asset_path,
        "BindingGuid": binding_guid, "Label": label,
        "Location": location or {"X": 0, "Y": 0, "Z": 0},
        "Rotation": rotation or {"Pitch": 0, "Yaw": 0, "Roll": 0},
        "bSetTransform": location is not None or rotation is not None,
        "FocalLength": focal_length, "Aperture": aperture,
        "MinFocalLength": min_focal_length, "MaxFocalLength": max_focal_length,
        "MinFStop": min_f_stop, "MaxFStop": max_f_stop,
        "SensorWidth": sensor_width, "SensorHeight": sensor_height,
        "ManualFocusDistance": manual_focus_distance,
        "FocusMethod": focus_method, "FocusActorPath": focus_actor_path,
        "bDryRun": dry_run, "bSave": save
    }).text


@mcp.tool()
def list_level_sequence_subsequences(asset_path: str) -> str:
    """List nested Level Sequence sections and their timing ranges."""
    return httpx.get(f"{app.BASE_URL}/level-sequences/subsequences", params={"asset_path": asset_path}).text


@mcp.tool()
def edit_level_sequence_binding(asset_path: str, operation: str,
                                name: str = "", class_path: str = "",
                                binding_guid: str = "", actor_path: str = "",
                                save: bool = False,
                                dry_run: bool = False, confirm: bool = False) -> str:
    """Add a possessable, add_spawnable from an actor class or placed actor, or remove either binding. Removal requires confirm."""
    return httpx.post(f"{app.BASE_URL}/level-sequences/bindings", json={
        "AssetPath": asset_path, "Operation": operation, "Name": name,
        "ClassPath": class_path, "BindingGuid": binding_guid,
        "ActorPath": actor_path,
        "bSave": save, "bDryRun": dry_run, "bConfirm": confirm
    }).text


@mcp.tool()
def edit_level_sequence_track(asset_path: str, operation: str,
                              binding_guid: str = "", track_class: str = "",
                              track_index: int = -1, property_name: str = "",
                              property_path: str = "", save: bool = False,
                              dry_run: bool = False, confirm: bool = False) -> str:
    """Add or remove a track. Bound: transform, visibility, float_property, byte_property, integer_property, object_property (top-level property_name=property_path of matching type; byte keeps the enum, object keeps the property class), skeletal_animation, audio, event; master: audio/fade/event. Native event sections are trigger sections; event continuation unverified. Removal requires confirm."""
    return httpx.post(f"{app.BASE_URL}/level-sequences/tracks", json={
        "AssetPath": asset_path, "Operation": operation,
        "BindingGuid": binding_guid, "TrackClass": track_class,
        "TrackIndex": track_index, "PropertyName": property_name,
        "PropertyPath": property_path, "bSave": save,
        "bDryRun": dry_run, "bConfirm": confirm
    }).text


@mcp.tool()
def edit_level_sequence_section(asset_path: str, operation: str,
                                track_index: int, binding_guid: str = "",
                                section_index: int = -1, frame: int = 0,
                                end_frame: int = 1, row_index: int = 0,
                                source_asset_path: str = "",
                                target_skeletal_mesh_path: str = "",
                                animation_play_rate: float | None = None,
                                animation_reverse: bool | None = None,
                                animation_slot_name: str | None = None,
                                animation_skip_notifiers: bool | None = None,
                                animation_force_custom_mode: bool | None = None,
                                animation_first_loop_start_offset: int | None = None,
                                animation_start_offset: int | None = None,
                                animation_end_offset: int | None = None,
                                audio_start_offset: int | None = None,
                                audio_looping: bool | None = None,
                                audio_suppress_subtitles: bool | None = None,
                                audio_override_attenuation: bool | None = None,
                                audio_attenuation_path: str | None = None,
                                save: bool = False, dry_run: bool = False,
                                confirm: bool = False, event_section_type: str = "") -> str:
    """Add/remove a section or edit skeletal-animation and audio section settings. Event add accepts event_section_type trigger (default) or repeater. Removal requires confirm."""
    payload = {
        "AssetPath": asset_path, "Operation": operation,
        "BindingGuid": binding_guid, "TrackIndex": track_index,
        "SectionIndex": section_index, "Frame": frame,
        "EndFrame": end_frame, "RowIndex": row_index, "EventSectionType": event_section_type,
        "SourceAssetPath": source_asset_path,
        "TargetSkeletalMeshPath": target_skeletal_mesh_path,
        "bSave": save, "bDryRun": dry_run, "bConfirm": confirm
    }
    optional_animation_settings = (
        ("bSetAnimationPlayRate", "AnimationPlayRate", animation_play_rate),
        ("bSetAnimationReverse", "bAnimationReverse", animation_reverse),
        ("bSetAnimationSlotName", "AnimationSlotName", animation_slot_name),
        ("bSetAnimationSkipNotifiers", "bAnimationSkipNotifiers", animation_skip_notifiers),
        ("bSetAnimationForceCustomMode", "bAnimationForceCustomMode", animation_force_custom_mode),
        ("bSetAnimationFirstLoopStartOffset", "AnimationFirstLoopStartOffset", animation_first_loop_start_offset),
        ("bSetAnimationStartOffset", "AnimationStartOffset", animation_start_offset),
        ("bSetAnimationEndOffset", "AnimationEndOffset", animation_end_offset),
        ("bSetAudioStartOffset", "AudioStartOffset", audio_start_offset),
        ("bSetAudioLooping", "bAudioLooping", audio_looping),
        ("bSetAudioSuppressSubtitles", "bAudioSuppressSubtitles", audio_suppress_subtitles),
        ("bSetAudioOverrideAttenuation", "bAudioOverrideAttenuation", audio_override_attenuation),
        ("bSetAudioAttenuationSettings", "AudioAttenuationPath", audio_attenuation_path),
    )
    for set_flag, field_name, value in optional_animation_settings:
        if value is not None:
            payload[set_flag] = True
            payload[field_name] = value
    return httpx.post(f"{app.BASE_URL}/level-sequences/sections", json=payload).text


@mcp.tool()
def list_level_sequence_keys(asset_path: str, track_index: int,
                             section_index: int, binding_guid: str = "") -> str:
    """List float, transform, visibility, audio, or skeletal-animation channel keys in a Level Sequence section."""
    return httpx.get(f"{app.BASE_URL}/level-sequences/keys", params={
        "asset_path": asset_path, "binding_guid": binding_guid,
        "track_index": track_index, "section_index": section_index
    }).text


@mcp.tool()
def edit_level_sequence_key(asset_path: str, operation: str,
                            track_index: int, section_index: int,
                            channel_index: int, binding_guid: str = "",
                            key_index: int = -1, frame: int = 0,
                            value: float = 0.0, interpolation: str = "auto",
                            save: bool = False, dry_run: bool = False,
                            confirm: bool = False) -> str:
    """Set or remove a key in a supported float, transform, visibility, audio, or animation channel. Removal requires confirm."""
    return httpx.post(f"{app.BASE_URL}/level-sequences/keys", json={
        "AssetPath": asset_path, "Operation": operation,
        "BindingGuid": binding_guid, "TrackIndex": track_index,
        "SectionIndex": section_index, "ChannelIndex": channel_index,
        "KeyIndex": key_index, "Frame": frame, "Value": value,
        "Interpolation": interpolation, "bSave": save,
        "bDryRun": dry_run, "bConfirm": confirm
    }).text


@mcp.tool()
def edit_level_sequence_camera_cut(asset_path: str, operation: str,
                                   camera_binding_guid: str = "", frame: int = 0,
                                   duration: int = 1, section_index: int = -1,
                                   save: bool = False, dry_run: bool = False,
                                   confirm: bool = False) -> str:
    """Add or remove a nonoverlapping camera cut for an existing camera binding. Removal requires confirm."""
    return httpx.post(f"{app.BASE_URL}/cinematic/camera-cuts", json={
        "AssetPath": asset_path, "Operation": operation,
        "CameraBindingGuid": camera_binding_guid, "Frame": frame,
        "Duration": duration, "SectionIndex": section_index,
        "bSave": save, "bDryRun": dry_run, "bConfirm": confirm
    }).text


@mcp.tool()
def edit_level_sequence_subsequence(asset_path: str, operation: str,
                                    sequence_path: str = "", frame: int = 0,
                                    duration: int = 1, row_index: int = 0,
                                    section_index: int = -1, save: bool = False,
                                    dry_run: bool = False, confirm: bool = False) -> str:
    """Add or remove a nested Level Sequence section. Removal requires confirm."""
    return httpx.post(f"{app.BASE_URL}/level-sequences/subsequences", json={
        "AssetPath": asset_path, "Operation": operation,
        "SequencePath": sequence_path, "Frame": frame, "Duration": duration,
        "RowIndex": row_index, "SectionIndex": section_index,
        "bSave": save, "bDryRun": dry_run, "bConfirm": confirm
    }).text


@mcp.tool()
def list_cinematic_shots(asset_path: str) -> str:
    """List named shot sections, nested sequences, rows, and frame ranges."""
    return httpx.get(f"{app.BASE_URL}/cinematic/shots", params={"asset_path": asset_path}).text


@mcp.tool()
def edit_cinematic_shot(asset_path: str, operation: str,
                        sequence_path: str = "", shot_name: str = "",
                        frame: int = 0, duration: int = 1,
                        row_index: int = 0, section_index: int = -1,
                        save: bool = False, dry_run: bool = False,
                        confirm: bool = False) -> str:
    """Add, rename, or remove a Level Sequence shot. Cycles are rejected; removal requires confirm."""
    return httpx.post(f"{app.BASE_URL}/cinematic/shots", json={
        "AssetPath": asset_path, "Operation": operation,
        "SequencePath": sequence_path, "ShotName": shot_name,
        "Frame": frame, "Duration": duration, "RowIndex": row_index,
        "SectionIndex": section_index, "bSave": save,
        "bDryRun": dry_run, "bConfirm": confirm
    }).text


@mcp.tool()
def validate_level_sequence(asset_path: str) -> str:
    """Validate Level Sequence Movie Scene timing and basic track structure."""
    return httpx.post(f"{app.BASE_URL}/level-sequences/validate", json={"AssetPath": asset_path}).text


@mcp.tool()
def evaluate_level_sequence_frame(asset_path: str, binding_guid: str,
                                 frame: int = 0, actor_path: str = "",
                                 play_on_editor_actor: bool = False) -> str:
    """Play transform plus optional visibility/float tracks in preview or direct mode, restoring the bound editor actor afterward."""
    return httpx.post(f"{app.BASE_URL}/level-sequences/evaluate", json={
        "AssetPath": asset_path, "BindingGuid": binding_guid,
        "Frame": frame, "ActorPath": actor_path,
        "bPlayOnEditorActor": play_on_editor_actor
    }).text


@mcp.tool()
def level_sequence_channel_extrapolation(asset_path: str, section_path: str, channel_type: str,
                                         channel_index: int, operation: str = "Inspect", value: int = 0,
                                         expected_value: int = 0, expected_section_class_path: str = "",
                                         expected_channel_snapshot: str = "", confirm: bool = False,
                                         dry_run: bool = True) -> str:
    """Inspect/Edit Float/Double Movie Scene channel PreInfinity/PostInfinity enum policy.
    Exact current sequence-track-section/type-index/class/full native channel snapshot/prior policy/unlocked state.
    Native enum choices from inspect, keys/tangents/default retained. Transactions/MarkAsChanged/dry-run,
    no sequence evaluation/playhead movement/render/load/save. Cache/UI/undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/level-sequences/channels/extrapolation", json={
        "AssetPath": asset_path, "ExpressionPath": section_path, "Name": channel_type,
        "Start": channel_index, "FieldName": operation, "Value": value, "ExpectedValue": expected_value,
        "ExpectedClassPath": expected_section_class_path, "ExpectedAssetSnapshot": expected_channel_snapshot,
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


def level_sequence_channel_default(asset_path: str, section_path: str, channel_type: str,
                                    channel_index: int, operation: str = "Inspect", value: float = 0,
                                    expected_exists: bool = False, expected_value: float = 0,
                                    expected_section_class_path: str = "", expected_channel_snapshot: str = "",
                                    confirm: bool = False, dry_run: bool = True) -> str:
    """Inspect/SetDefault/ClearDefault Float/Double/Bool/Byte/Integer channel fallback, keys retained.
    Bool0or1/byte0..255/int32 limits; byte enum channels require current visible enum choice.
    Exact current section/type-index/class/full native snapshot/prior default existence-value/unlocked state.
    Finite native float/double range, quantization; transaction/MarkAsChanged/readback/no-op/dry-run.
    No key erase/sequence evaluation/playhead movement/load/save; cache/UI/undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/level-sequences/channels/default", json={
        "AssetPath": asset_path, "ExpressionPath": section_path, "Name": channel_type,
        "Start": channel_index, "FieldName": operation, "Value": value,
        "bExpectedEnabled": expected_exists, "ExpectedValue": expected_value,
        "ExpectedClassPath": expected_section_class_path, "ExpectedAssetSnapshot": expected_channel_snapshot,
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


def discover_level_sequence_numeric_channels(asset_path: str, section_path: str,
                                              start: int = 0, count: int = 64) -> str:
    """Discover Float/Double/Bool/Byte/Integer/Object/Event channels/pages1..128/typed indices/snapshots.
    Exact current track-section membership, combined float/double/bool/byte/integer/object/event order; proxy rebuild may shift indices.
    Snapshots returned only<=64KiB edit budget, native serialization unbounded before cap.
    No evaluation/playhead movement/compile/load/save/mutation; unverified.
    """
    return httpx.post(f"{app.BASE_URL}/level-sequences/channels/discover", json={
        "AssetPath": asset_path, "ExpressionPath": section_path, "Start": start, "Count": count}, timeout=180).text


def level_sequence_object_channel_default(asset_path: str, section_path: str, channel_index: int,
                                           operation: str = "Inspect", object_path: str = "",
                                           expected_soft_path: str = "", expected_section_class_path: str = "",
                                           expected_channel_snapshot: str = "", confirm: bool = False,
                                           dry_run: bool = True) -> str:
    """Inspect/SetDefault/ClearDefault native Object path channel fallback, keys retained.
    Loaded persistent asset/current-editor-world object/property-class compatibility or empty clear.
    Exact prior soft path/section class/type-index/full channel snapshot/unlocked state.
    Null/clear same native state; transaction/MarkAsChanged/dry-run, no load/evaluation/save. Unverified.
    """
    return httpx.post(f"{app.BASE_URL}/level-sequences/channels/default", json={
        "AssetPath": asset_path, "ExpressionPath": section_path, "Name": "Object",
        "Start": channel_index, "FieldName": operation, "SourceTexturePath": object_path,
        "ExpectedTargetPath": expected_soft_path, "ExpectedClassPath": expected_section_class_path,
        "ExpectedAssetSnapshot": expected_channel_snapshot, "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


def level_sequence_numeric_key_policy(asset_path: str, section_path: str, channel_type: str, channel_index: int,
                                       operation: str = "Keys", key_index: int = 0, expected_frame: int = 0,
                                       value: int = 0, expected_mode: int = -1, expected_section_class_path: str = "",
                                       expected_channel_snapshot: str = "", start: int = 0, count: int = 64,
                                       confirm: bool = False, dry_run: bool = True) -> str:
    """Float/Double Keys page1..128 or KeyInterpolation/KeyTangentMode edit using native enums.
    Exact section/class/type-index/full channel snapshot/key index-frame/prior mode/unlocked state.
    Native AutoSetTangents may update neighboring auto tangents; expected full channel copy/readback,
    key times/values retained. Transactions/dry-run/no evaluation/load/save; unverified.
    """
    return httpx.post(f"{app.BASE_URL}/level-sequences/channels/key-policy", json={
        "AssetPath": asset_path, "ExpressionPath": section_path, "Name": channel_type, "Start": channel_index,
        "FieldName": operation, "MipIndex": key_index, "ExpectedSizeX": expected_frame,
        "Value": value, "ExpectedFormat": expected_mode, "ExpectedClassPath": expected_section_class_path,
        "ExpectedAssetSnapshot": expected_channel_snapshot, "BlockIndex": start, "Count": count,
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


def set_level_sequence_key_tangents(asset_path: str, section_path: str, channel_type: str,
                                    channel_index: int, key_index: int, expected_frame: int,
                                    components: list[float], expected_components: list[float],
                                    weight_mode: int, expected_weight_mode: int,
                                    expected_section_class_path: str, expected_channel_snapshot: str,
                                    confirm: bool = False, dry_run: bool = True) -> str:
    """Set Float/Double cubic User/Break key [arrive slope,leave slope,arrive weight,leave weight].
    Finite native floats/nonnegative weights; User requires equal slopes, Break permits independent slopes.
    Native weight mode0None/1Arrive/2Leave/3Both, exact prior components/mode/frame/full channel snapshot.
    No auto tangent recalculation for manual edit, preserves sibling keys; transaction/dry-run, unverified.
    No evaluation/playhead movement/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/level-sequences/channels/key-policy", json={
        "AssetPath": asset_path, "ExpressionPath": section_path, "Name": channel_type, "Start": channel_index,
        "FieldName": "KeyTangents", "MipIndex": key_index, "ExpectedSizeX": expected_frame,
        "Color": components, "ExpectedColor": expected_components,
        "Value": weight_mode, "ExpectedFormat": expected_weight_mode,
        "ExpectedClassPath": expected_section_class_path, "ExpectedAssetSnapshot": expected_channel_snapshot,
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


def move_level_sequence_numeric_key(asset_path: str, section_path: str, channel_type: str,
                                     channel_index: int, key_index: int, expected_frame: int,
                                     new_frame: int, expected_section_class_path: str,
                                     expected_channel_snapshot: str, confirm: bool = False,
                                     dry_run: bool = True) -> str:
    """Move native Float/Double key in tick-resolution frame units, occupied destination rejected.
    Exact current section/type-index/class/full channel snapshot/key index-old frame/unlocked bounds.
    Native MoveKey/sorting/AutoSetTangents may update auto tangents, expected full channel readback.
    No section resize/key deletion/evaluation/playhead movement/load/save; transaction/dry-run, unverified.
    """
    return httpx.post(f"{app.BASE_URL}/level-sequences/channels/key-policy", json={
        "AssetPath": asset_path, "ExpressionPath": section_path, "Name": channel_type, "Start": channel_index,
        "FieldName": "KeyMove", "MipIndex": key_index, "ExpectedSizeX": expected_frame, "SizeX": new_frame,
        "ExpectedClassPath": expected_section_class_path, "ExpectedAssetSnapshot": expected_channel_snapshot,
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


def set_level_sequence_numeric_key_value(asset_path: str, section_path: str, channel_type: str,
                                          channel_index: int, key_index: int, expected_frame: int,
                                          value: float, expected_value: float, expected_section_class_path: str,
                                          expected_channel_snapshot: str, confirm: bool = False,
                                          dry_run: bool = True) -> str:
    """Set native Float/Double key value/exact previous native value/frame/full channel snapshot.
    Finite native range/quantization, retains times/order/handles; AutoSetTangents may update auto neighbors.
    Transaction/expected full channel readback/dry-run; no evaluation/playhead/load/save, unverified.
    """
    return httpx.post(f"{app.BASE_URL}/level-sequences/channels/key-policy", json={
        "AssetPath": asset_path, "ExpressionPath": section_path, "Name": channel_type, "Start": channel_index,
        "FieldName": "KeyValue", "MipIndex": key_index, "ExpectedSizeX": expected_frame,
        "Value": value, "ExpectedValue": expected_value, "ExpectedClassPath": expected_section_class_path,
        "ExpectedAssetSnapshot": expected_channel_snapshot, "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


def edit_level_sequence_numeric_key(asset_path: str, section_path: str, channel_type: str,
                                     channel_index: int, operation: str,
                                     expected_section_class_path: str, expected_channel_snapshot: str,
                                     frame: int = 0, value: float = 0, key_index: int = 0,
                                     expected_frame: int = 0, expected_value: float = 0,
                                     confirm: bool = False, dry_run: bool = True) -> str:
    """KeyAdd/KeyDelete native Float/Double channel, full snapshot/current section/type/class/unlocked guards.
    Add vacant tick frame within section/finite value/native cubic-auto key defaults. Delete exact index/frame/value.
    Native AddKey/RemoveKey/AutoSetTangents expected readback; auto neighbors may change, fallback retained.
    Transactions/dry-run/no evaluation/playhead/load/save; unverified.
    """
    return httpx.post(f"{app.BASE_URL}/level-sequences/channels/key-policy", json={
        "AssetPath": asset_path, "ExpressionPath": section_path, "Name": channel_type, "Start": channel_index,
        "FieldName": operation, "SizeX": frame, "Value": value, "MipIndex": key_index,
        "ExpectedSizeX": expected_frame, "ExpectedValue": expected_value,
        "ExpectedClassPath": expected_section_class_path, "ExpectedAssetSnapshot": expected_channel_snapshot,
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


def level_sequence_discrete_keys(asset_path: str, section_path: str, channel_type: str, channel_index: int,
                                  operation: str = "Keys", key_index: int = 0, frame: int = 0, value: int = 0,
                                  expected_frame: int = 0, expected_value: int = 0,
                                  expected_section_class_path: str = "", expected_channel_snapshot: str = "",
                                  start: int = 0, count: int = 64, confirm: bool = False, dry_run: bool = True) -> str:
    """Bool/Byte/Integer Keys page1..128 or KeyAdd/KeyDelete/KeyMove/KeyValue native edits.
    Exact section/type-index/class/full snapshot/selected prior index-frame-value/unlocked state.
    Native ranges/byte enum choices, vacant destination tick frame inside section, no duplicate merge.
    Transaction/full expected channel readback/dry-run; no evaluation/playhead/load/save, unverified.
    """
    return httpx.post(f"{app.BASE_URL}/level-sequences/channels/key-policy", json={
        "AssetPath": asset_path, "ExpressionPath": section_path, "Name": channel_type, "Start": channel_index,
        "FieldName": operation, "MipIndex": key_index, "SizeX": frame, "Value": value,
        "ExpectedSizeX": expected_frame, "ExpectedValue": expected_value,
        "ExpectedClassPath": expected_section_class_path, "ExpectedAssetSnapshot": expected_channel_snapshot,
        "BlockIndex": start, "Count": count, "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


def level_sequence_object_keys(asset_path: str, section_path: str, channel_index: int,
                                operation: str = "Keys", key_index: int = 0, frame: int = 0,
                                object_path: str = "", expected_frame: int = 0, expected_soft_path: str = "",
                                expected_section_class_path: str = "", expected_channel_snapshot: str = "",
                                start: int = 0, count: int = 64, confirm: bool = False, dry_run: bool = True) -> str:
    """Object channel Keys page1..128/KeyAdd/KeyDelete/KeyMove/KeyValue, exact prior index-frame-soft path.
    Full channel snapshot/class/current section/type-index/unlocked state; loaded asset/current-world object/
    property class compatibility or explicit null. Vacant tick frame inside section, no merge/default erase.
    Native soft-hard key data/transaction/expected readback/dry-run, no loading/evaluation/save; unverified.
    """
    return httpx.post(f"{app.BASE_URL}/level-sequences/channels/key-policy", json={
        "AssetPath": asset_path, "ExpressionPath": section_path, "Name": "Object", "Start": channel_index,
        "FieldName": operation, "MipIndex": key_index, "SizeX": frame, "SourceTexturePath": object_path,
        "ExpectedSizeX": expected_frame, "ExpectedTargetPath": expected_soft_path,
        "ExpectedClassPath": expected_section_class_path, "ExpectedAssetSnapshot": expected_channel_snapshot,
        "BlockIndex": start, "Count": count, "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


def level_sequence_event_keys(asset_path: str, section_path: str, channel_index: int,
                               operation: str = "Keys", key_index: int = 0, expected_frame: int = 0,
                               new_frame: int = 0, expected_section_class_path: str = "",
                               expected_channel_snapshot: str = "", start: int = 0, count: int = 64,
                               confirm: bool = False, dry_run: bool = True) -> str:
    """Native event-trigger Keys page1..128/KeyAdd empty event or KeyMove/KeyDelete/KeyDuplicate existing data.
    Exact section/type-index/class/full channel snapshot/key index-frame/unlocked/vacant destination bounds.
    KeyAdd creates unbound native event at vacant new_frame; index/prior frame ignored for Add.
    Duplicate shares endpoint/function and copies payload; use separate endpoint creation/binding tools.
    No event invocation/evaluation/compile/playhead/load/save; transaction/dry-run, unverified.
    """
    return httpx.post(f"{app.BASE_URL}/level-sequences/channels/key-policy", json={
        "AssetPath": asset_path, "ExpressionPath": section_path, "Name": "Event", "Start": channel_index,
        "FieldName": operation, "MipIndex": key_index, "ExpectedSizeX": expected_frame, "SizeX": new_frame,
        "ExpectedClassPath": expected_section_class_path, "ExpectedAssetSnapshot": expected_channel_snapshot,
        "BlockIndex": start, "Count": count, "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


def discover_level_sequence_channels(asset_path: str, section_path: str, start: int = 0, count: int = 64) -> str:
    """Discover Float/Double/Bool/Byte/Integer/Object/Event typed section channels/page1..128/snapshots.
    Type-local indices and current section lock states; events support no fallback default.
    Native full snapshot exported before64KiB return/edit cap; no evaluation/event firing/compile/load/save.
    Proxy rebuilds may shift indices; unverified.
    """
    return httpx.post(f"{app.BASE_URL}/level-sequences/channels/discover", json={
        "AssetPath": asset_path, "ExpressionPath": section_path, "Start": start, "Count": count}, timeout=180).text


@mcp.tool()
def discover_level_sequence_event_endpoints(asset_path: str, start: int = 0, count: int = 64) -> str:
    """Discover loaded sequence director Blueprint custom-event/function-entry nodes/GUIDs/pins/page1..128.
    Returns director path/GUID; no director creation/endpoint binding/signature proof/compile/event invocation.
    Pins up to128 per node, native graph scans/sort unbounded. No load/save/mutation; unverified.
    """
    return httpx.post(f"{app.BASE_URL}/level-sequences/events/endpoints/discover", json={
        "AssetPath": asset_path, "Start": start, "Count": count}, timeout=180).text


def bind_level_sequence_event_endpoint(asset_path: str, section_path: str, channel_index: int,
                                       key_index: int, expected_frame: int, expected_section_class_path: str,
                                       expected_channel_snapshot: str, expected_endpoint_path: str,
                                       director_blueprint_path: str, director_blueprint_guid: str,
                                       endpoint_path: str = "", endpoint_guid: str = "", endpoint_snapshot: str = "",
                                       bound_object_pin: str = "", bound_object_pin_guid: str = "",
                                       confirm: bool = False, dry_run: bool = True) -> str:
    """Bind/clear existing event key with native SetEndpoint/section-Blueprint extension then director compile.
    Exact channel snapshot/key frame/prior endpoint/director path-GUID/discovered node GUID-pin snapshot;
    optional scalar by-value output object/interface pin name-GUID. Empty endpoint clears binding.
    Native compile can prune payloads/update other sections/dependencies; failure leaves partial state.
    Transaction/readback/dry-run, no event invocation/evaluation/load/save; unverified.
    """
    return httpx.post(f"{app.BASE_URL}/level-sequences/channels/key-policy", json={
        "AssetPath": asset_path, "ExpressionPath": section_path, "Name": "Event", "Start": channel_index,
        "FieldName": "BindEndpoint", "MipIndex": key_index, "ExpectedSizeX": expected_frame,
        "ExpectedClassPath": expected_section_class_path, "ExpectedAssetSnapshot": expected_channel_snapshot,
        "ExpectedTargetPath": expected_endpoint_path, "OwnerAssetPath": director_blueprint_path,
        "ActorGuid": director_blueprint_guid, "SourceTexturePath": endpoint_path,
        "ExpectedSourceId": endpoint_guid, "ExpectedDestinationSnapshot": endpoint_snapshot,
        "OutputName": bound_object_pin, "ExpectedOtherSourceId": bound_object_pin_guid,
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=1800).text


def edit_level_sequence_event_payload(asset_path: str, section_path: str, channel_index: int,
                                      key_index: int, expected_frame: int, payload_name: str, operation: str,
                                      expected_section_class_path: str, expected_channel_snapshot: str,
                                      director_blueprint_path: str, director_blueprint_guid: str,
                                      endpoint_guid: str, endpoint_snapshot: str, pin_guid: str = "",
                                      value_text: str = "", object_path: str = "", expected_exists: bool = False,
                                      expected_text: str = "", expected_object_path: str = "",
                                      confirm: bool = False, dry_run: bool = True) -> str:
    """PayloadSet/PayloadRemove existing event scalar by-value endpoint pin, full channel/endpoint guards.
    Set native K2 default validation/text<=4096 or loaded object with empty text; no containers/refs/bound pin.
    Exact prior existence/text/object and node-pin/director identities; native director compile/readback.
    Compiler can prune stale payloads/update other sections, failure partial. No event invocation/load/save.
    Transactions/dry-run/runtime-cook behavior unverified.
    """
    return httpx.post(f"{app.BASE_URL}/level-sequences/channels/key-policy", json={
        "AssetPath": asset_path, "ExpressionPath": section_path, "Name": "Event", "Start": channel_index,
        "FieldName": operation, "MipIndex": key_index, "ExpectedSizeX": expected_frame,
        "ExpectedClassPath": expected_section_class_path, "ExpectedAssetSnapshot": expected_channel_snapshot,
        "OwnerAssetPath": director_blueprint_path, "ActorGuid": director_blueprint_guid,
        "ExpectedSourceId": endpoint_guid, "ExpectedDestinationSnapshot": endpoint_snapshot,
        "ExpectedOtherSourceId": pin_guid, "ExpectedLabel": payload_name, "OutputName": value_text,
        "SourceTexturePath": object_path, "bExpectedEnabled": expected_exists,
        "ExpectedOutputName": expected_text, "ExpectedTargetPath": expected_object_path,
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=1800).text


def create_level_sequence_event_endpoint(asset_path: str, section_path: str, channel_index: int,
                                         key_index: int, expected_frame: int, expected_section_class_path: str,
                                         expected_channel_snapshot: str, expected_endpoint_path: str = "None",
                                         expected_director_exists: bool = False, director_blueprint_path: str = "",
                                         director_blueprint_guid: str = "", replace_existing_endpoint: bool = False,
                                         confirm: bool = False, dry_run: bool = True) -> str:
    """Create/bind native blank custom-event endpoint for existing event key; create director if absent.
    Exact channel/key/class/snapshot/prior endpoint/director existence-path-GUID/unlocked guards.
    Replacement opt-in leaves old node. Native unique name/binding-derived pin/director compile/callable readback.
    Dry-run loads editor module/provider only. Native compilation can clean payloads/other sections; failures
    partial, creation undo unverified. No key creation/body wiring/event invocation/evaluation/asset save.
    """
    return httpx.post(f"{app.BASE_URL}/level-sequences/channels/key-policy", json={
        "AssetPath": asset_path, "ExpressionPath": section_path, "Name": "Event", "Start": channel_index,
        "FieldName": "CreateEndpoint", "MipIndex": key_index, "ExpectedSizeX": expected_frame,
        "ExpectedClassPath": expected_section_class_path, "ExpectedAssetSnapshot": expected_channel_snapshot,
        "ExpectedTargetPath": expected_endpoint_path, "bExpectedEnabled": expected_director_exists,
        "OwnerAssetPath": director_blueprint_path, "ActorGuid": director_blueprint_guid,
        "bEnabled": replace_existing_endpoint, "bConfirm": confirm, "bDryRun": dry_run}, timeout=1800).text


@mcp.tool()
def level_sequence_event_track_policy(asset_path: str, track_path: str, field_name: str = "Inspect",
                                       value: int = 0, expected_value: int = 0,
                                       expected_class_path: str = "", expected_track_snapshot: str = "",
                                       confirm: bool = False, dry_run: bool = True) -> str:
    """Inspect/edit native event track bFireEventsWhenForwards/Backwards bool0or1 or EventPosition enum.
    Current master/binding ownership/full signature-policy-section snapshot/class/prior value guards.
    Native choices, transaction/property callback/MarkAsChanged/sibling checks/dry-run.
    No event firing/evaluation/playhead/director compile/load/save; unverified.
    """
    return httpx.post(f"{app.BASE_URL}/level-sequences/events/track-policy", json={
        "AssetPath": asset_path, "ExpressionPath": track_path, "FieldName": field_name,
        "Value": value, "ExpectedValue": expected_value, "ExpectedClassPath": expected_class_path,
        "ExpectedAssetSnapshot": expected_track_snapshot, "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


def inspect_level_sequence_event_repeater(asset_path: str, section_path: str, payload_start: int = 0, count: int = 64) -> str:
    """Inspect repeater event and sorted payload page (count1..128), text/object values and matching pin metadata.
    Reports missing/orphaned/bound pins and truncates text at4096; no signature or runtime validation.
    Current sequence-track-section ownership; no event channel/default/key semantics invented.
    No binding/compile/event invocation/evaluation/playhead/load/save/mutation; unverified.
    """
    return httpx.post(f"{app.BASE_URL}/level-sequences/events/repeater", json={
        "AssetPath": asset_path, "ExpressionPath": section_path, "FieldName": "Inspect",
        "BlockIndex": payload_start, "Count": count}, timeout=180).text


def level_sequence_event_repeater_endpoint(asset_path: str, section_path: str, operation: str,
                                           expected_section_class_path: str, expected_repeater_snapshot: str,
                                           expected_endpoint_path: str = "None", expected_director_exists: bool = True,
                                           director_blueprint_path: str = "", director_blueprint_guid: str = "",
                                           endpoint_path: str = "", endpoint_guid: str = "", endpoint_snapshot: str = "",
                                           bound_object_pin: str = "", bound_object_pin_guid: str = "",
                                           replace_existing_endpoint: bool = False,
                                           confirm: bool = False, dry_run: bool = True) -> str:
    """Repeater CreateEndpoint or BindEndpoint/empty-clear via native event utils/director compiler.
    Exact range-event snapshot/class/prior endpoint/director existence-path-GUID/discovered node-pin guards.
    Create can initialize director/blank endpoint, replacement opt-in. Native compile may prune payloads/update
    other sections, failure partial. No event firing/evaluation/load/save; transaction/dry-run, unverified.
    """
    return httpx.post(f"{app.BASE_URL}/level-sequences/events/repeater", json={
        "AssetPath": asset_path, "ExpressionPath": section_path, "FieldName": operation,
        "ExpectedClassPath": expected_section_class_path, "ExpectedAssetSnapshot": expected_repeater_snapshot,
        "ExpectedTargetPath": expected_endpoint_path, "bExpectedEnabled": expected_director_exists,
        "OwnerAssetPath": director_blueprint_path, "ActorGuid": director_blueprint_guid,
        "SourceTexturePath": endpoint_path, "ExpectedSourceId": endpoint_guid,
        "ExpectedDestinationSnapshot": endpoint_snapshot, "OutputName": bound_object_pin,
        "ExpectedOtherSourceId": bound_object_pin_guid, "bEnabled": replace_existing_endpoint,
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=1800).text


def edit_level_sequence_repeater_payload(asset_path: str, section_path: str, payload_name: str, operation: str,
                                         expected_section_class_path: str, expected_repeater_snapshot: str,
                                         director_blueprint_path: str, director_blueprint_guid: str,
                                         endpoint_guid: str, endpoint_snapshot: str, pin_guid: str = "",
                                         value_text: str = "", object_path: str = "", expected_exists: bool = False,
                                         expected_text: str = "", expected_object_path: str = "",
                                         confirm: bool = False, dry_run: bool = True) -> str:
    """Repeater PayloadSet/PayloadRemove, exact repeater range-event/director-node-pin snapshots/identity.
    Native K2 validation/scalar by-value nonexec/nonbound pin/text<=4096 or loaded object; no containers/refs/FText.
    Native director compile/selected payload readback may prune stale payloads/update other sections; failures partial.
    Transactions/dry-run/no event firing/evaluation/load/save, unverified.
    """
    return httpx.post(f"{app.BASE_URL}/level-sequences/events/repeater", json={
        "AssetPath": asset_path, "ExpressionPath": section_path, "FieldName": operation,
        "ExpectedClassPath": expected_section_class_path, "ExpectedAssetSnapshot": expected_repeater_snapshot,
        "OwnerAssetPath": director_blueprint_path, "ActorGuid": director_blueprint_guid,
        "ExpectedSourceId": endpoint_guid, "ExpectedDestinationSnapshot": endpoint_snapshot,
        "ExpectedOtherSourceId": pin_guid, "ExpectedLabel": payload_name, "OutputName": value_text,
        "SourceTexturePath": object_path, "bExpectedEnabled": expected_exists,
        "ExpectedOutputName": expected_text, "ExpectedTargetPath": expected_object_path,
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=1800).text


@mcp.tool()
def add_level_sequence_event_endpoint_pin(asset_path: str, director_blueprint_path: str,
                                          director_blueprint_guid: str, endpoint_path: str, endpoint_guid: str,
                                          endpoint_snapshot: str, pin_name: str, pin_type: str,
                                          subtype_path: str = "", confirm: bool = False, dry_run: bool = True) -> str:
    """Native endpoint output parameter pin/new unique identifier; exact director/node identities/full pin snapshot.
    Scalar Bool/Int/Int64/Byte/Float/Double/Name/String or loaded Object/Class/Interface/Struct/Enum subtype.
    Native editable-pin validation/CreateUserDefinedPin/director compile/type-GUID readback/transaction/dry-run.
    Compile may rebuild event sections/clean payloads; failure partial, existing call sites not explicitly rewired.
    No binding/payload default/body wiring/event invocation/load/save; unverified.
    """
    return httpx.post(f"{app.BASE_URL}/level-sequences/events/endpoints/pins/add", json={
        "AssetPath": asset_path, "OwnerAssetPath": director_blueprint_path, "ActorGuid": director_blueprint_guid,
        "SourceTexturePath": endpoint_path, "ExpectedSourceId": endpoint_guid,
        "ExpectedDestinationSnapshot": endpoint_snapshot, "OutputName": pin_name, "Name": pin_type,
        "PathFilter": subtype_path, "bConfirm": confirm, "bDryRun": dry_run}, timeout=1800).text


@mcp.tool()
def remove_level_sequence_event_endpoint_pin(asset_path: str, director_blueprint_path: str,
                                             director_blueprint_guid: str, endpoint_path: str, endpoint_guid: str,
                                             endpoint_snapshot: str, pin_name: str, pin_guid: str,
                                             expected_linked_pin_ids: list[str] = [], expected_event_ids: list[str] = [],
                                             expected_event_snapshots: list[str] = [], allow_breakage: bool = False,
                                             confirm: bool = False, dry_run: bool = True) -> str:
    """Preflight/remove native user output parameter pin, exact director/node/pin snapshot identities.
    Dry-run reports direct linked pin IDs/loaded affected event IDs-snapshots; apply exact sets/explicit breakage
    opt-in when used. Foreign/locked/transient event refs block. Native unlink/pin removal/payload-bound cleanup/
    director compile/transaction/readback; incomplete unloaded/call-site audit, errors partial. No event firing/save.
    Unverified.
    """
    return httpx.post(f"{app.BASE_URL}/level-sequences/events/endpoints/pins/remove", json={
        "AssetPath": asset_path, "OwnerAssetPath": director_blueprint_path, "ActorGuid": director_blueprint_guid,
        "SourceTexturePath": endpoint_path, "ExpectedSourceId": endpoint_guid,
        "ExpectedDestinationSnapshot": endpoint_snapshot, "OutputName": pin_name,
        "ExpectedOtherSourceId": pin_guid, "ExpectedComponentPaths": expected_linked_pin_ids,
        "ExpectedSourcePaths": expected_event_ids, "ExpectedSettingTexts": expected_event_snapshots,
        "bEnabled": allow_breakage, "bConfirm": confirm, "bDryRun": dry_run}, timeout=1800).text


def sample_level_sequence_numeric_channel(asset_path: str, section_path: str, channel_type: str,
                                          channel_index: int, expected_section_class_path: str,
                                          expected_channel_snapshot: str, tick_frames: list[int],
                                          subframes: list[float] = []) -> str:
    """Sample native Float/Double curve at1..128 explicit tick frames, optional matching subframes[0,1).
    Exact discovered class/channel snapshot required. Returns native float subframe, has_value/finite,
    value or null, section-frame membership and tick/display rates. Defaults and extrapolation apply.
    Raw channel values ignore section activation, blending, easing, hierarchy and final properties.
    No sequence playback/evaluation, event dispatch, playhead movement, render or asset mutation.
    Unverified; native channel Evaluate is executed only when this tool is explicitly invoked.
    """
    return httpx.post(f"{app.BASE_URL}/level-sequences/channels/sample", json={
        "AssetPath": asset_path, "ExpressionPath": section_path, "Name": channel_type,
        "Start": channel_index, "ExpectedClassPath": expected_section_class_path,
        "ExpectedAssetSnapshot": expected_channel_snapshot, "SourceOrder": tick_frames,
        "Color": subframes}, timeout=180).text


def sample_level_sequence_discrete_channel(asset_path: str, section_path: str, channel_type: str,
                                           channel_index: int, expected_section_class_path: str,
                                           expected_channel_snapshot: str, tick_frames: list[int],
                                           subframes: list[float] = []) -> str:
    """Sample native Bool/Byte/Integer curve at1..128 tick frames and matching optional subframes[0,1).
    Requires discovered section class/full channel snapshot. Bool returns boolean; Byte numeric;
    Integer returns exact int64 integer_decimal string with numeric value null to avoid precision loss.
    has_value distinguishes empty/default-less curves. Native discrete evaluation/default rules apply.
    Raw channel sampling ignores section gating, blending, hierarchy and final property application.
    No sequence playback/events/playhead/render/asset mutation. Implementation unverified.
    """
    return httpx.post(f"{app.BASE_URL}/level-sequences/channels/sample", json={
        "AssetPath": asset_path, "ExpressionPath": section_path, "Name": channel_type,
        "Start": channel_index, "ExpectedClassPath": expected_section_class_path,
        "ExpectedAssetSnapshot": expected_channel_snapshot, "SourceOrder": tick_frames,
        "Color": subframes}, timeout=180).text


@mcp.tool()
def level_sequence_integer_interpolation(asset_path: str, section_path: str, channel_index: int,
                                          operation: str = "Inspect", enabled: bool = False,
                                          expected_enabled: bool = False, expected_section_class_path: str = "",
                                          expected_channel_snapshot: str = "", confirm: bool = False,
                                          dry_run: bool = True) -> str:
    """Inspect/Set native Integer bInterpolateLinearKeys policy. Set requires exact prior bool,
    discovered section class/full channel snapshot, confirmation and unlocked current section.
    Preserves int32 authored keys/default; native evaluated results use int64. Transaction/dirty/dry-run.
    No sampling/playback/events/playhead/render/compile/load/save. Unverified.
    """
    if operation not in ("Inspect", "Set"):
        raise ValueError("operation must be Inspect or Set")
    return httpx.post(f"{app.BASE_URL}/level-sequences/channels/integer-interpolation", json={
        "AssetPath": asset_path, "ExpressionPath": section_path, "Start": channel_index,
        "FieldName": f"IntegerInterpolation{operation}", "bEnabled": enabled,
        "bExpectedEnabled": expected_enabled, "ExpectedClassPath": expected_section_class_path,
        "ExpectedAssetSnapshot": expected_channel_snapshot, "bConfirm": confirm,
        "bDryRun": dry_run}, timeout=180).text


def sample_level_sequence_object_channel(asset_path: str, section_path: str, channel_index: int,
                                         expected_section_class_path: str, expected_channel_snapshot: str,
                                         tick_frames: list[int], subframes: list[float] = [],
                                         confirm: bool = False, dry_run: bool = True) -> str:
    """Sample native Object channel at1..128 explicit tick frames, optional matching subframes[0,1).
    Requires confirm for native synchronous asset loading and hard-reference cache effects.
    Dry-run returns metadata only. Actual sampling may load packages/run callbacks without undo.
    Returns has_value separately from resolved validity; null key/unresolved reference can both be null.
    Raw channel ignores activation/blending/hierarchy/final properties; no player/events/playhead/save.
    Exact discovered class/full snapshot required. Loading/cache/runtime behavior unverified.
    """
    return httpx.post(f"{app.BASE_URL}/level-sequences/channels/sample", json={
        "AssetPath": asset_path, "ExpressionPath": section_path, "Name": "Object",
        "Start": channel_index, "ExpectedClassPath": expected_section_class_path,
        "ExpectedAssetSnapshot": expected_channel_snapshot, "SourceOrder": tick_frames,
        "Color": subframes, "bConfirm": confirm, "bDryRun": dry_run}, timeout=1800).text


@mcp.tool()
def offset_level_sequence_channel_keys(asset_path: str, section_path: str, channel_type: str,
                                        channel_index: int, offset_tick_frames: int,
                                        expected_section_class_path: str, expected_channel_snapshot: str,
                                        confirm: bool = False, dry_run: bool = True) -> str:
    """Offset every key in one Float/Double/Bool/Byte/Integer/Object/Event channel using native Offset.
    Requires exact discovered class/full snapshot, confirmation, unlocked section and <=4096 keys.
    Rejects overflow, duplicate/unsorted times or destinations outside current section; no range resize.
    Preserves native key values/defaults/tangents/event payloads/bindings; sibling channels stay separate.
    Native expected-copy/full readback/transaction/dirty/dry-run. No evaluation/resolve/events/save.
    Tick frames, not display frames. Handles/cache/undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/level-sequences/channels/offset", json={
        "AssetPath": asset_path, "ExpressionPath": section_path, "Name": channel_type,
        "Start": channel_index, "SizeX": offset_tick_frames, "ExpectedClassPath": expected_section_class_path,
        "ExpectedAssetSnapshot": expected_channel_snapshot, "bConfirm": confirm,
        "bDryRun": dry_run}, timeout=180).text


@mcp.tool()
def duplicate_level_sequence_channel_key(asset_path: str, section_path: str, channel_type: str,
                                         channel_index: int, source_key_index: int, expected_source_frame: int,
                                         destination_tick_frame: int, expected_section_class_path: str,
                                         expected_channel_snapshot: str, confirm: bool = False,
                                         dry_run: bool = True) -> str:
    """Duplicate full native Float/Double/Bool/Byte/Integer/Object/Event key into vacant section tick frame.
    Exact class/full snapshot/source index-frame, confirmation/unlocked/budget4096 guards required.
    Copies numeric tangent modes/weights verbatim without recomputing neighbors. Event payload copied,
    endpoint/function shared. Object refs copied without resolving. Insertion shifts indices: re-inspect.
    Transaction/native expected-copy readback/dirty/dry-run; no evaluation/events/compile/load/save.
    Native handles/tangent policy/undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/level-sequences/channels/duplicate-key", json={
        "AssetPath": asset_path, "ExpressionPath": section_path, "Name": channel_type,
        "Start": channel_index, "MipIndex": source_key_index, "ExpectedSizeX": expected_source_frame,
        "SizeX": destination_tick_frame, "ExpectedClassPath": expected_section_class_path,
        "ExpectedAssetSnapshot": expected_channel_snapshot, "bConfirm": confirm,
        "bDryRun": dry_run}, timeout=180).text


@mcp.tool()
def level_sequence_section_blend_type(asset_path: str, section_path: str, operation: str = "Inspect",
                                      blend_type: int = 1, expected_has_blend_type: bool = False,
                                      expected_blend_type: int = 0, expected_section_class_path: str = "",
                                      expected_blend_snapshot: str = "", confirm: bool = False,
                                      dry_run: bool = True) -> str:
    """Inspect/Set native section blend type using reported supported values (not enum ordinals).
    Set requires exact class/authored range-row-active-lock-blend-support snapshot/prior validity-value,
    confirmation/unlocked section. Does not support clearing optional blend type to unset.
    Native setter/transaction/MarkAsChanged/context readback/dirty/dry-run; snapshot excludes channels.
    No easing/key edits/evaluation/events/playhead/render/compile/load/save. Unverified.
    """
    if operation not in ("Inspect", "Set"):
        raise ValueError("operation must be Inspect or Set")
    return httpx.post(f"{app.BASE_URL}/level-sequences/sections/blend-type", json={
        "AssetPath": asset_path, "ExpressionPath": section_path, "FieldName": f"Blend{operation}",
        "Value": blend_type, "bExpectedEnabled": expected_has_blend_type,
        "ExpectedValue": expected_blend_type, "ExpectedClassPath": expected_section_class_path,
        "ExpectedAssetSnapshot": expected_blend_snapshot, "bConfirm": confirm,
        "bDryRun": dry_run}, timeout=180).text


@mcp.tool()
def level_sequence_section_completion_mode(asset_path: str, section_path: str, operation: str = "Inspect",
                                            completion_mode: int = 0, expected_completion_mode: int = 0,
                                            expected_section_class_path: str = "",
                                            expected_completion_snapshot: str = "", confirm: bool = False,
                                            dry_run: bool = True) -> str:
    """Inspect/Set native section completion mode using reported enum values.
    Set respects native bCanEditCompletionMode; requires exact class/context-eval-options snapshot,
    prior mode, confirmation and unlocked section. ProjectDefault remains symbolic, not resolved.
    Transaction/MarkAsChanged/readback/dirty/dry-run; no preanimated-state capture/restoration.
    No playback/evaluation/events/playhead/render/compile/load/save. Unverified.
    """
    if operation not in ("Inspect", "Set"):
        raise ValueError("operation must be Inspect or Set")
    return httpx.post(f"{app.BASE_URL}/level-sequences/sections/completion-mode", json={
        "AssetPath": asset_path, "ExpressionPath": section_path, "FieldName": f"Completion{operation}",
        "Value": completion_mode, "ExpectedValue": expected_completion_mode,
        "ExpectedClassPath": expected_section_class_path, "ExpectedAssetSnapshot": expected_completion_snapshot,
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


@mcp.tool()
def level_sequence_section_easing(asset_path: str, section_path: str, operation: str = "Inspect",
                                  duration_tick_frames: int = 0, expected_section_class_path: str = "",
                                  expected_easing_snapshot: str = "", confirm: bool = False,
                                  dry_run: bool = True) -> str:
    """Inspect native section easing or set manual In/Out duration in tick frames.
    Native track support, exact class/full easing-context snapshot, confirmation/unlocked guards.
    Sets selected side manual flag=true. Duration0..discrete bounded section length; sides may overlap.
    Preserves opposite side/automatic durations/function objects. No track-wide auto recalculation.
    Transaction/readback/dirty/dry-run; no easing callback/evaluation/playback/events/load/save.
    Native editor-length behavior/undo/persistence unverified.
    """
    if operation not in ("Inspect", "In", "Out"):
        raise ValueError("operation must be Inspect, In or Out")
    return httpx.post(f"{app.BASE_URL}/level-sequences/sections/easing", json={
        "AssetPath": asset_path, "ExpressionPath": section_path, "FieldName": f"Easing{operation}",
        "SizeX": duration_tick_frames, "ExpectedClassPath": expected_section_class_path,
        "ExpectedAssetSnapshot": expected_easing_snapshot, "bConfirm": confirm,
        "bDryRun": dry_run}, timeout=180).text


@mcp.tool()
def level_sequence_section_builtin_easing(asset_path: str, section_path: str, operation: str = "Inspect",
                                          preset: int = 0, expected_function_path: str = "None",
                                          expected_section_class_path: str = "", expected_easing_snapshot: str = "",
                                          allow_custom_replacement: bool = False, confirm: bool = False,
                                          dry_run: bool = True) -> str:
    """Inspect native easing presets or assign selected In/Out side to reported built-in preset.
    Requires exact class/full easing-context snapshot/prior function path, native support and confirmation.
    Creates fresh transactional section-owned function on change; retains old object for undo.
    Replacing custom/external function requires explicit opt-in. Custom preset is excluded.
    Preserves durations/manual flags/opposite side; no function invocation/evaluation/load/save.
    Snapshot includes built-in type/external curve path, not custom bodies. Unverified.
    """
    if operation not in ("Inspect", "In", "Out"):
        raise ValueError("operation must be Inspect, In or Out")
    return httpx.post(f"{app.BASE_URL}/level-sequences/sections/easing/built-in", json={
        "AssetPath": asset_path, "ExpressionPath": section_path, "FieldName": f"BuiltIn{operation}",
        "Value": preset, "ExpectedTargetPath": expected_function_path,
        "ExpectedClassPath": expected_section_class_path, "ExpectedAssetSnapshot": expected_easing_snapshot,
        "bEnabled": allow_custom_replacement, "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


@mcp.tool()
def level_sequence_section_external_easing(asset_path: str, section_path: str, operation: str = "Inspect",
                                           curve_path: str = "", expected_curve_snapshot: str = "",
                                           expected_function_path: str = "None", expected_section_class_path: str = "",
                                           expected_easing_snapshot: str = "", allow_function_replacement: bool = False,
                                           confirm: bool = False, dry_run: bool = True) -> str:
    """Inspect/assign native external CurveFloat easing to In/Out side. Inspect optional persistent curve
    returns destination snapshot. Assignment requires exact class/easing-context/prior function path,
    destination rich-curve snapshot, native side support, confirmation and unlocked section.
    Creates fresh transactional section-owned function; non-external replacement requires opt-in.
    Preserves durations/manual flags/opposite side/source curve; no shape normalization or evaluation.
    Native CurveFloat only, <=4096 keys/64KiB snapshot; loads the curve asset; no compile/playback/save.
    """
    if operation not in ("Inspect", "In", "Out"):
        raise ValueError("operation must be Inspect, In or Out")
    return httpx.post(f"{app.BASE_URL}/level-sequences/sections/easing/external-curve", json={
        "AssetPath": asset_path, "ExpressionPath": section_path, "FieldName": f"External{operation}",
        "SourceTexturePath": curve_path, "ExpectedDestinationSnapshot": expected_curve_snapshot,
        "ExpectedTargetPath": expected_function_path, "ExpectedClassPath": expected_section_class_path,
        "ExpectedAssetSnapshot": expected_easing_snapshot, "bEnabled": allow_function_replacement,
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


@mcp.tool()
def level_sequence_section_automatic_easing(asset_path: str, section_path: str, operation: str = "Inspect",
                                            automatic: bool = True, expected_automatic: bool = True,
                                            expected_section_class_path: str = "", expected_track_easing_snapshot: str = "",
                                            confirm: bool = False, dry_run: bool = True) -> str:
    """Inspect track easing or toggle In/Out automatic mode and run native track-wide UpdateEasing.
    Exact class/full ordered track easing-context/playback-bounds snapshot/prior mode required.
    All <=128 sections writable/unlocked, rows0..128/bounds+-100M; native mode support enforced.
    Transaction covers siblings; native automatic durations/unsupported manual flags may change.
    Recomputes even if flag matches. Dry-run validates intent without predicting derived results.
    Preserves authored ranges/blend/completion/functions/manual durations via readback; errors non-atomic.
    No playback/evaluation/events/playhead/render/compile/load/save. Unverified.
    """
    if operation not in ("Inspect", "In", "Out"):
        raise ValueError("operation must be Inspect, In or Out")
    return httpx.post(f"{app.BASE_URL}/level-sequences/sections/easing/automatic", json={
        "AssetPath": asset_path, "ExpressionPath": section_path, "FieldName": f"AutoEasing{operation}",
        "bEnabled": automatic, "bExpectedEnabled": expected_automatic,
        "ExpectedClassPath": expected_section_class_path, "ExpectedAssetSnapshot": expected_track_easing_snapshot,
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


@mcp.tool()
def level_sequence_section_pre_post_roll(asset_path: str, section_path: str, operation: str = "Inspect",
                                         pre_roll_tick_frames: int = 0, post_roll_tick_frames: int = 0,
                                         expected_pre_roll_tick_frames: int = 0, expected_post_roll_tick_frames: int = 0,
                                         expected_section_class_path: str = "", expected_roll_snapshot: str = "",
                                         confirm: bool = False, dry_run: bool = True) -> str:
    """Inspect/Set native paired section pre/post-roll durations0..1M tick frames.
    Requires exact class/full roll-context snapshot/prior pair, confirmation and unlocked section.
    Rejects expanded native frame-bound overflow; retains section range/keys/easing/open bounds.
    Track/subsequence flags and section-specific roll support remain separate; no warmup guarantee.
    Transaction/MarkAsChanged/readback/dirty/dry-run; no playback/evaluation/events/load/save. Unverified.
    """
    if operation not in ("Inspect", "Set"):
        raise ValueError("operation must be Inspect or Set")
    return httpx.post(f"{app.BASE_URL}/level-sequences/sections/pre-post-roll", json={
        "AssetPath": asset_path, "ExpressionPath": section_path, "FieldName": f"Roll{operation}",
        "SizeX": pre_roll_tick_frames, "SizeY": post_roll_tick_frames,
        "ExpectedSizeX": expected_pre_roll_tick_frames, "ExpectedSizeY": expected_post_roll_tick_frames,
        "ExpectedClassPath": expected_section_class_path, "ExpectedAssetSnapshot": expected_roll_snapshot,
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


@mcp.tool()
def level_sequence_track_evaluation_policy(asset_path: str, track_path: str, field: str = "Inspect",
                                           enabled: bool = False, expected_enabled: bool = False,
                                           expected_track_class_path: str = "", expected_evaluation_snapshot: str = "",
                                           confirm: bool = False, dry_run: bool = True) -> str:
    """Inspect/edit native track bEvalNearestSection/bEvaluateInPreroll/bEvaluateInPostroll.
    Nearest editing respects native capability. Exact current class/full EvalOptions+section-path
    snapshot/prior bool, confirmation/writable scene/native editability required; empty tracks supported.
    Transaction/property callbacks/MarkAsChanged/readback/dirty/dry-run; snapshot excludes section bodies.
    Parent subsequence roll/native track semantics apply; no warmup guarantee/evaluation/load/save.
    Callback propagation/cache/undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/level-sequences/tracks/evaluation-policy", json={
        "AssetPath": asset_path, "ExpressionPath": track_path, "FieldName": field,
        "bEnabled": enabled, "bExpectedEnabled": expected_enabled,
        "ExpectedClassPath": expected_track_class_path, "ExpectedAssetSnapshot": expected_evaluation_snapshot,
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


@mcp.tool()
def level_sequence_section_overlap_priority(asset_path: str, section_path: str, operation: str = "Inspect",
                                             priority: int = 0, expected_priority: int = 0,
                                             expected_section_class_path: str = "", expected_priority_snapshot: str = "",
                                             confirm: bool = False, dry_run: bool = True) -> str:
    """Inspect/Set native int32 overlap priority (higher wins per native API), with peer diagnostics.
    Exact class/full selected-context+ordered peer-context/priorities snapshot/prior value required.
    Confirmation/unlocked section; <=128 owned peers. Reports range overlap/same-row/active,
    without predicting final blend or tie resolution. No peer reorder/auto-easing recalculation.
    Transaction/MarkAsChanged/readback/dirty/dry-run; no evaluation/events/load/save. Unverified.
    """
    if operation not in ("Inspect", "Set"):
        raise ValueError("operation must be Inspect or Set")
    return httpx.post(f"{app.BASE_URL}/level-sequences/sections/overlap-priority", json={
        "AssetPath": asset_path, "ExpressionPath": section_path, "FieldName": f"Priority{operation}",
        "Value": priority, "ExpectedValue": expected_priority, "ExpectedClassPath": expected_section_class_path,
        "ExpectedAssetSnapshot": expected_priority_snapshot, "bConfirm": confirm,
        "bDryRun": dry_run}, timeout=180).text


@mcp.tool()
def level_sequence_track_mute(asset_path: str, track_path: str, operation: str = "Inspect", row_index: int = 0,
                               disabled: bool = False, expected_disabled: bool = False,
                               expected_track_class_path: str = "", expected_mute_snapshot: str = "",
                               confirm: bool = False, dry_run: bool = True) -> str:
    """Inspect or set persistent Track/Row native evaluation disable flag. Rows0..4096/disabled arrays256.
    Exact class/full persistent-local mute/options/ordered section-row snapshot/prior persistent bool required.
    Local editor mute/solo state is inspected/preserved; persistent unmute may remain effectively disabled.
    Future unused rows allowed; orphaned disabled rows can be cleared. Confirmation/writable scene guards.
    Transaction/MarkAsChanged/readback/dirty/dry-run; no solo rebuild/activation/evaluation/load/save. Unverified.
    """
    if operation not in ("Inspect", "Track", "Row"):
        raise ValueError("operation must be Inspect, Track or Row")
    return httpx.post(f"{app.BASE_URL}/level-sequences/tracks/mute", json={
        "AssetPath": asset_path, "ExpressionPath": track_path, "FieldName": operation, "Start": row_index,
        "bEnabled": disabled, "bExpectedEnabled": expected_disabled, "ExpectedClassPath": expected_track_class_path,
        "ExpectedAssetSnapshot": expected_mute_snapshot, "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


def level_sequence_marked_frames(asset_path: str, operation: str = "Inspect", start: int = 0, count: int = 64,
                                  source_index: int = 0, expected_source_tick_frame: int = 0,
                                  expected_source_label: str = "", destination_tick_frame: int = 0,
                                  label: str = "", comment: str = "", expected_sequence_class_path: str = "",
                                  expected_marked_frames_snapshot: str = "", confirm: bool = False,
                                  dry_run: bool = True) -> str:
    """Inspect native marker pages or Add/Move/Delete. Tick frames may be negative/outside playback.
    Exact sequence class/full ordered marker-lock-tick snapshot, source index-frame-label for Move/Delete,
    confirmation/writable unlocked marker list required. Add explicit unique label<=128/comment<=4096.
    Max4096 markers/page128/snapshot256KiB; rejects unsorted/duplicate frames and occupied destinations.
    Native default color/fence on Add; Move retains full metadata. Indices shift: re-inspect.
    Native transaction/MarkAsChanged/readback/dirty/dry-run; no evaluation/playhead/load/save. Unverified.
    """
    return httpx.post(f"{app.BASE_URL}/level-sequences/marked-frames", json={
        "AssetPath": asset_path, "FieldName": operation, "BlockIndex": start, "Count": count,
        "MipIndex": source_index, "ExpectedSizeX": expected_source_tick_frame,
        "ExpectedLabel": expected_source_label, "SizeX": destination_tick_frame, "Name": label,
        "OutputName": comment, "ExpectedClassPath": expected_sequence_class_path,
        "ExpectedAssetSnapshot": expected_marked_frames_snapshot, "bConfirm": confirm,
        "bDryRun": dry_run}, timeout=180).text


def set_level_sequence_marker_metadata(asset_path: str, marker_index: int, expected_tick_frame: int,
                                        expected_label: str, label: str, comment: str,
                                        use_custom_color: bool, linear_rgba: list[float],
                                        determinism_fence: bool, inclusive_time: bool,
                                        expected_sequence_class_path: str, expected_marked_frames_snapshot: str,
                                        confirm: bool = False, dry_run: bool = True) -> str:
    """Set full native marker metadata, retaining frame/order/deprecated fields.
    Exact full marker snapshot/class/source index-frame-label/confirmation/writable unlocked guards.
    Unique nonempty label<=128/comment<=4096/linear RGBA0..1. Fence/inclusive affect future evaluation.
    Native typed struct-array assignment/transaction/MarkAsChanged/full readback/dirty/dry-run.
    No evaluation/playhead/events/load/save. Metadata/fence semantics/undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/level-sequences/marked-frames", json={
        "AssetPath": asset_path, "FieldName": "Metadata", "MipIndex": marker_index,
        "ExpectedSizeX": expected_tick_frame, "ExpectedLabel": expected_label, "Name": label,
        "OutputName": comment, "Color": linear_rgba,
        "SourceOrder": [int(use_custom_color), int(determinism_fence), int(inclusive_time)],
        "ExpectedClassPath": expected_sequence_class_path, "ExpectedAssetSnapshot": expected_marked_frames_snapshot,
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


def set_level_sequence_markers_locked(asset_path: str, locked: bool, expected_locked: bool,
                                       expected_sequence_class_path: str, expected_marked_frames_snapshot: str,
                                       confirm: bool = False, dry_run: bool = True) -> str:
    """Set native marker-list lock including explicit unlock, guarded by full marker snapshot/class/prior lock.
    Requires confirmation/writable scene; transaction/MarkAsChanged/full array readback/dirty/dry-run.
    No marker changes/evaluation/load/save. Native UI/undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/level-sequences/marked-frames", json={
        "AssetPath": asset_path, "FieldName": "Lock", "bEnabled": locked, "bExpectedEnabled": expected_locked,
        "ExpectedClassPath": expected_sequence_class_path, "ExpectedAssetSnapshot": expected_marked_frames_snapshot,
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


def level_sequence_folders(asset_path: str, operation: str = "Inspect", start: int = 0, count: int = 64,
                            parent_folder_path: str = "", name: str = "", expected_sequence_class_path: str = "",
                            expected_folder_snapshot: str = "", confirm: bool = False, dry_run: bool = True) -> str:
    """Inspect bounded native folder tree or Create empty root/child folder (empty parent=root).
    Exact sequence class/full ordered tree snapshot/confirmation/writable scene required for Create.
    Unique sibling FName<=128, trim/control/path separators rejected; tree256/depth32/members256/pages128.
    Native transaction/delegates/existing tree readback/dirty/dry-run; reports member paths/GUIDs,
    not full member validity. No moves/content assignment/evaluation/load/save. Unverified.
    """
    return httpx.post(f"{app.BASE_URL}/level-sequences/folders", json={
        "AssetPath": asset_path, "FieldName": operation, "BlockIndex": start, "Count": count,
        "OwnerAssetPath": parent_folder_path, "Name": name, "ExpectedClassPath": expected_sequence_class_path,
        "ExpectedAssetSnapshot": expected_folder_snapshot, "bConfirm": confirm,
        "bDryRun": dry_run}, timeout=180).text


def edit_level_sequence_folder_settings(asset_path: str, folder_path: str, operation: str,
                                         expected_sequence_class_path: str, expected_folder_snapshot: str,
                                         name: str = "", expected_name: str = "", rgba_bytes: list[int] = [],
                                         expected_rgba_bytes: list[int] = [], sorting_order: int = 0,
                                         expected_sorting_order: int = 0, confirm: bool = False,
                                         dry_run: bool = True) -> str:
    """Rename/Color/Sort native sequence folder with full tree snapshot/class/current-folder/prior-field guards.
    Rename: trimmed unique sibling non-None FName<=128. Color: exact RGBA bytes0..255. Sort: native int32 hint,
    higher appears further down; native arrays are not reordered. Confirmation/writable scene required.
    Transaction/native setters/full hierarchy readback/dirty/dry-run preserves parent/members/siblings.
    No evaluation/load/save. Native UI/undo/persistence unverified.
    """
    if operation not in ("Rename", "Color", "Sort"):
        raise ValueError("operation must be Rename, Color or Sort")
    return httpx.post(f"{app.BASE_URL}/level-sequences/folders", json={
        "AssetPath": asset_path, "ExpressionPath": folder_path, "FieldName": operation,
        "Name": name, "ExpectedLabel": expected_name, "Color": rgba_bytes, "ExpectedColor": expected_rgba_bytes,
        "Value": sorting_order, "ExpectedValue": expected_sorting_order,
        "ExpectedClassPath": expected_sequence_class_path, "ExpectedAssetSnapshot": expected_folder_snapshot,
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


def move_or_remove_level_sequence_folder(asset_path: str, folder_path: str, operation: str,
                                          expected_parent_folder_path: str, expected_sequence_class_path: str,
                                          expected_folder_snapshot: str, destination_parent_folder_path: str = "",
                                          confirm: bool = False, dry_run: bool = True) -> str:
    """Move folder subtree or RemoveEmpty using exact current folder/source parent/full hierarchy snapshot.
    Expected parent='None' for root; empty destination=root. Rejects self/descendant cycles, resulting
    depth>32 and destination sibling name collisions. RemoveEmpty requires no child folders/tracks/bindings.
    Native reparent/root detach-add/remove, transaction covers all folders/native delegates, full virtual
    hierarchy readback/dirty/no-op/dry-run. Removed UObject retained for undo; no asset deletion/content loss.
    No evaluation/load/save. Native delegate propagation/undo/persistence unverified; errors non-atomic.
    """
    if operation not in ("Move", "RemoveEmpty"):
        raise ValueError("operation must be Move or RemoveEmpty")
    return httpx.post(f"{app.BASE_URL}/level-sequences/folders", json={
        "AssetPath": asset_path, "ExpressionPath": folder_path, "FieldName": operation,
        "ExpectedTargetPath": expected_parent_folder_path, "OwnerAssetPath": destination_parent_folder_path,
        "ExpectedClassPath": expected_sequence_class_path, "ExpectedAssetSnapshot": expected_folder_snapshot,
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


def assign_level_sequence_folder_content(asset_path: str, member_type: str, expected_source_folder_path: str,
                                          expected_sequence_class_path: str, expected_folder_snapshot: str,
                                          destination_folder_path: str = "", master_track_path: str = "",
                                          expected_track_signature: str = "", binding_guid: str = "",
                                          confirm: bool = False, dry_run: bool = True) -> str:
    """Assign Track/Binding to folder or unfile (empty destination). Expected source='None' when unfiled.
    Track must be current native master track with exact signature; object-bound tracks stay under binding.
    Binding requires current scene GUID. Exact class/full tree snapshot/unique source occurrence required.
    Native AddChildTrack/AddChildObjectBinding removes prior folder membership; transaction covers all folders,
    full virtual membership readback/dirty/no-op/dry-run. Member cap256. No binding-body edits/evaluation/load/save.
    Native delegates/cache/UI/undo/persistence unverified; errors non-atomic.
    """
    if member_type not in ("Track", "Binding"):
        raise ValueError("member_type must be Track or Binding")
    return httpx.post(f"{app.BASE_URL}/level-sequences/folders", json={
        "AssetPath": asset_path, "FieldName": f"Assign{member_type}", "OwnerAssetPath": destination_folder_path,
        "ExpectedTargetPath": expected_source_folder_path, "SourceTexturePath": master_track_path,
        "ExpectedSourceId": expected_track_signature, "ActorGuid": binding_guid,
        "ExpectedClassPath": expected_sequence_class_path, "ExpectedAssetSnapshot": expected_folder_snapshot,
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


def level_sequence_binding_tags(asset_path: str, operation: str = "Inspect", start: int = 0, count: int = 64,
                                  tag_name: str = "", binding_guid: str = "", expected_tag_exists: bool = False,
                                  expected_sequence_class_path: str = "", expected_binding_tags_snapshot: str = "",
                                  allow_populated_tag_removal: bool = False, confirm: bool = False,
                                  dry_run: bool = True) -> str:
    """Inspect/Create/TagRootBinding/UntagRootBinding/RemoveTag native tag groups.
    Root operations treat selected sequence as root, require existing local GUID; no hierarchy remapping.
    Exact class/full group-name+serialized-IDs snapshot/prior group existence/confirmation/writable guards.
    Create rejects existing groups (native API otherwise overwrites); untag last member deletes group.
    Populated group removal needs breakage opt-in; no complete external/name consumer audit.
    Groups/members256/page128/snapshot256KiB; transaction/readback/dirty/dry-run, no evaluation/load/save.
    Native binding ID semantics/UI/cache/undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/level-sequences/bindings/tags", json={
        "AssetPath": asset_path, "FieldName": operation, "BlockIndex": start, "Count": count,
        "Name": tag_name, "ActorGuid": binding_guid, "bExpectedEnabled": expected_tag_exists,
        "ExpectedClassPath": expected_sequence_class_path, "ExpectedAssetSnapshot": expected_binding_tags_snapshot,
        "bEnabled": allow_populated_tag_removal, "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


def rename_level_sequence_binding_tag(asset_path: str, tag_name: str, new_tag_name: str,
                                       expected_sequence_class_path: str, expected_binding_tags_snapshot: str,
                                       allow_name_consumer_breakage: bool = False, confirm: bool = False,
                                       dry_run: bool = True) -> str:
    """Rename native binding tag, preserving full serialized member IDs including nested/relative contexts.
    Exact sequence class/full tag snapshot/existing source/absent destination/confirmation/writable guards.
    Native non-None trimmed names<=128; case-equivalent FName is no-op. Explicit name-consumer breakage
    opt-in required for actual rename; external consumers are not found/migrated. Native remove-create plus
    checked typed reflected group copy/transaction/full readback/dirty/dry-run; no evaluation/load/save.
    Reflection/name resolution/UI/cache/undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/level-sequences/bindings/tags", json={
        "AssetPath": asset_path, "FieldName": "RenameTag", "Name": tag_name, "OutputName": new_tag_name,
        "bExpectedEnabled": True, "ExpectedClassPath": expected_sequence_class_path,
        "ExpectedAssetSnapshot": expected_binding_tags_snapshot, "bEnabled": allow_name_consumer_breakage,
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


@mcp.tool()
def validate_level_sequence_folders(asset_path: str, issue_start: int = 0, count: int = 64) -> str:
    """Bounded reachable native folder structural validation; does not repair or evaluate.
    Checks folder ownership/loading/class/repeated membership/cycles/sibling names; master-track and
    binding GUID validity/duplicate content memberships. Budgets256 folders/depth32/members per folder256,
    retained issues256/pages128; skipped branches force incomplete/invalid. No detached-orphan/dependency,
    binding-body/player/cook/runtime/persistence proof. Read-only/no loads/save. Implementation unverified.
    """
    return httpx.post(f"{app.BASE_URL}/level-sequences/folders/validate", json={
        "AssetPath": asset_path, "BlockIndex": issue_start, "Count": count}, timeout=180).text


@mcp.tool()
def level_sequence_subsection_parameters(asset_path: str, section_path: str, operation: str = "Inspect",
                                          value: float = 0, expected_value: float = 0, enabled: bool = False,
                                          expected_enabled: bool = False, expected_nested_sequence_path: str = "None",
                                          expected_section_class_path: str = "", expected_subsection_snapshot: str = "",
                                          confirm: bool = False, dry_run: bool = True) -> str:
    """Inspect/Bias/Flags/Loop/StartOffset/EndOffset/FirstLoopOffset/FixedPlayRate/FixedTime native subsection/shot params.
    Exact class/full native parameter+section-context+inner timing snapshot/prior field+nested path guards.
    Flags mask0..15: KeepState1/RestoreState2 exclusive, IgnoreBias4/BlendBias8. Loop uses enabled/prior enabled.
    Offsets native inner tick frames0..1M (direct native arithmetic); end/first requires existing loop.
    Clip retains at least one inner display frame; first-loop offset fits clip. No silent range extension.
    FixedTime value is raw native int32 warp frame, not final composed source frame; enabled replaces other modes.
    Existing FixedTime prior uses expected_value; warp changes invalidate native channel proxy.
    FixedPlayRate abs0.0001..1000, enabled opt-in replaces nonconstant warp; constant prior uses expected_value.
    Transaction/native callbacks/readback/dirty/dry-run; no custom getter/evaluation/load/save. Unverified.
    """
    allowed = ("Inspect", "Bias", "Flags", "Loop", "StartOffset", "EndOffset", "FirstLoopOffset", "FixedPlayRate", "FixedTime")
    if operation not in allowed:
        raise ValueError(f"operation must be one of {allowed}")
    return httpx.post(f"{app.BASE_URL}/level-sequences/subsections/parameters", json={
        "AssetPath": asset_path, "ExpressionPath": section_path, "FieldName": f"Sub{operation}",
        "Value": value, "ExpectedValue": expected_value, "bEnabled": enabled, "bExpectedEnabled": expected_enabled,
        "ExpectedTargetPath": expected_nested_sequence_path, "ExpectedClassPath": expected_section_class_path,
        "ExpectedAssetSnapshot": expected_subsection_snapshot, "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


@mcp.tool()
def level_sequence_subsection_origin(asset_path: str, section_path: str, operation: str = "Inspect",
                                      axis: int = 0, value: float = 0, expected_value: float = 0,
                                      expected_has_default: bool = False, expected_nested_sequence_path: str = "None",
                                      expected_section_class_path: str = "", expected_origin_snapshot: str = "",
                                      confirm: bool = False, dry_run: bool = True) -> str:
    """Inspect/Mask/DefaultSet/DefaultClear native subsection transform origin; axis0..5=translationXYZ/rotationXYZ.
    Mask bits1,2,4,8,16,32; no scale/weight. Defaults native units/degrees without normalization, abs<=1e9.
    Exact class/full subsection+mask+six-channel snapshot/prior field/nested path/confirmation/unlocked guards.
    Reads checked native arrays without custom warp getter/proxy construction. Mask resets proxy natively;
    fallback default edits retain keys/mask and can author disabled axes. Transaction/readback/dirty/dry-run.
    No gizmo/transform evaluation/scene placement/events/load/save. Native composition/undo/persistence unverified.
    """
    if operation not in ("Inspect", "Mask", "DefaultSet", "DefaultClear"):
        raise ValueError("operation must be Inspect, Mask, DefaultSet or DefaultClear")
    return httpx.post(f"{app.BASE_URL}/level-sequences/subsections/origin", json={
        "AssetPath": asset_path, "ExpressionPath": section_path, "FieldName": f"Origin{operation}",
        "MipIndex": axis, "Value": value, "ExpectedValue": expected_value,
        "bExpectedEnabled": expected_has_default, "ExpectedTargetPath": expected_nested_sequence_path,
        "ExpectedClassPath": expected_section_class_path, "ExpectedAssetSnapshot": expected_origin_snapshot,
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


@mcp.tool()
def level_sequence_subsection_reference(asset_path: str, section_path: str, operation: str = "Inspect",
                                         candidate_sequence_path: str = "", expected_nested_sequence_path: str = "None",
                                         expected_section_class_path: str = "", expected_subsection_snapshot: str = "",
                                         expected_destination_graph_snapshot: str = "", allow_replacement: bool = False,
                                         confirm: bool = False, dry_run: bool = True) -> str:
    """Inspect/Set native subsection/shot sequence reference; empty candidate clears.
    Inspect candidate obtains loaded-native-LevelSequence hierarchy snapshot/cycle+compatibility checks.
    Set requires exact class/full source-context/prior reference/destination graph snapshots, confirmation,
    unlocked section, replacement-clear opt-in. Bounds256 sequences/depth32/tracks-bindings256/sections4096.
    Native setter/delegate/transaction/readback/dirty/dry-run preserves params/range; no retiming/binding-ID repair.
    No hierarchy compilation/player evaluation/load/save. Native callbacks/cache/undo/persistence unverified.
    """
    if operation not in ("Inspect", "Set"):
        raise ValueError("operation must be Inspect or Set")
    return httpx.post(f"{app.BASE_URL}/level-sequences/subsections/reference", json={
        "AssetPath": asset_path, "ExpressionPath": section_path, "FieldName": f"Reference{operation}",
        "SourceTexturePath": candidate_sequence_path, "ExpectedTargetPath": expected_nested_sequence_path,
        "ExpectedClassPath": expected_section_class_path, "ExpectedAssetSnapshot": expected_subsection_snapshot,
        "ExpectedDestinationSnapshot": expected_destination_graph_snapshot, "bEnabled": allow_replacement,
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


@mcp.tool()
def cinematic_shot_metadata(asset_path: str, section_path: str, operation: str = "Inspect",
                              name: str = "", expected_authored_name: str = "", thumbnail_offset_seconds: float = 0,
                              expected_thumbnail_offset_seconds: float = 0, expected_section_class_path: str = "",
                              expected_shot_metadata_snapshot: str = "", confirm: bool = False,
                              dry_run: bool = True) -> str:
    """Inspect/Name/Thumbnail native cinematic shot metadata. Name<=256/no controls; empty restores
    sequence-name fallback (does not rename asset). Prior guard uses authored name, not effective fallback.
    Thumbnail offset native float seconds from inclusive shot start,0..86400/within bounded shot duration.
    Exact class/full subsection-origin+metadata snapshot/prior field/confirmation/unlocked guards.
    Transaction/native setters/full readback/dirty/dry-run; no explicit thumbnail capture/render/playhead,
    evaluation/load/save. Editor may refresh previews later. Native UI/cache/undo/persistence unverified.
    """
    if operation not in ("Inspect", "Name", "Thumbnail"):
        raise ValueError("operation must be Inspect, Name or Thumbnail")
    return httpx.post(f"{app.BASE_URL}/cinematic/shots/metadata", json={
        "AssetPath": asset_path, "ExpressionPath": section_path, "FieldName": f"Shot{operation}",
        "Name": name, "ExpectedLabel": expected_authored_name, "Value": thumbnail_offset_seconds,
        "ExpectedValue": expected_thumbnail_offset_seconds, "ExpectedClassPath": expected_section_class_path,
        "ExpectedAssetSnapshot": expected_shot_metadata_snapshot, "bConfirm": confirm,
        "bDryRun": dry_run}, timeout=180).text


@mcp.tool()
def cinematic_camera_cut_metadata(asset_path: str, section_path: str, operation: str = "Inspect",
                                    local_binding_guid: str = "", enabled: bool = False, expected_enabled: bool = False,
                                    thumbnail_offset_seconds: float = 0, expected_thumbnail_offset_seconds: float = 0,
                                    expected_section_class_path: str = "", expected_camera_cut_snapshot: str = "",
                                    confirm: bool = False, dry_run: bool = True) -> str:
    """Inspect/Binding/LockPrevious/Thumbnail native dedicated camera-cut metadata.
    Binding authors existing local relative GUID or empty clear; enabled opt-in replaces existing binding.
    Existence is not camera-component resolution proof; no nested ID authoring/player/viewport switch.
    LockPrevious uses enabled/prior enabled. Thumbnail native float seconds0..86400/within bounded duration.
    Exact class/full metadata-context snapshot/confirmation/unlocked guards. Transaction/readback/dirty/dry-run.
    No camera activation/thumbnail capture/render/evaluation/playhead/load/save. Unverified.
    """
    if operation not in ("Inspect", "Binding", "LockPrevious", "Thumbnail"):
        raise ValueError("operation must be Inspect, Binding, LockPrevious or Thumbnail")
    return httpx.post(f"{app.BASE_URL}/cinematic/camera-cuts/metadata", json={
        "AssetPath": asset_path, "ExpressionPath": section_path, "FieldName": f"Cut{operation}",
        "ActorGuid": local_binding_guid, "bEnabled": enabled, "bExpectedEnabled": expected_enabled,
        "Value": thumbnail_offset_seconds, "ExpectedValue": expected_thumbnail_offset_seconds,
        "ExpectedClassPath": expected_section_class_path, "ExpectedAssetSnapshot": expected_camera_cut_snapshot,
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


@mcp.tool()
def cinematic_camera_cut_track_policy(asset_path: str, track_path: str, operation: str = "Inspect",
                                        enabled: bool = False, expected_enabled: bool = False,
                                        expected_track_class_path: str = "", expected_camera_track_snapshot: str = "",
                                        allow_layout_changes: bool = False, confirm: bool = False,
                                        dry_run: bool = True) -> str:
    """Inspect/CanBlend/AutoManage/Rearrange native camera-cut track. Disabling blend or enabling auto-manage
    calls native RearrangeAllSections, which can reorder/resize cuts, snap boundaries, clear easing durations.
    Exact class/full track layout snapshot/prior flag/confirmation/writable guards; all cuts transactional.
    Layout requires explicit opt-in, <=128 native row0 bounded inclusive-exclusive cuts/bounds+-100M.
    Dry-run reports intent without native rearrangement/prediction. Identity/metadata/range readback/dirty.
    No camera activation/player/render/evaluation/playhead/load/save. Native layout/undo/persistence unverified.
    """
    if operation not in ("Inspect", "CanBlend", "AutoManage", "Rearrange"):
        raise ValueError("operation must be Inspect, CanBlend, AutoManage or Rearrange")
    return httpx.post(f"{app.BASE_URL}/cinematic/camera-cuts/track-policy", json={
        "AssetPath": asset_path, "ExpressionPath": track_path, "FieldName": operation,
        "bEnabled": enabled, "bExpectedEnabled": expected_enabled, "SourceOrder": [int(allow_layout_changes)],
        "ExpectedClassPath": expected_track_class_path, "ExpectedAssetSnapshot": expected_camera_track_snapshot,
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


@mcp.tool()
def set_cinematic_camera_cut_range(asset_path: str, section_path: str, lower_tick_frame: int,
                                    upper_tick_frame: int, expected_lower_tick_frame: int,
                                    expected_upper_tick_frame: int, expected_section_class_path: str,
                                    expected_camera_track_snapshot: str, allow_layout_changes: bool = False,
                                    confirm: bool = False, dry_run: bool = True) -> str:
    """Set native cut inclusive-exclusive range and call OnSectionMoved ValueSet cleanup/UpdateEasing.
    Native track policy can resize neighbors, detach fully covered cuts and reorder/recompute easing.
    Requires explicit layout-change opt-in/full track snapshot/class/prior range/confirmation/all cuts writable.
    All <=128 native row0 cuts pre-modified for undo; bounded nonempty ranges+-100M. Detached objects retained.
    Returns removed cut paths/native layout; preserves binding/camera/roll/completion metadata via readback.
    Dry-run reports intent without predicting cleanup. No player/render/evaluation/load/save. Unverified.
    """
    return httpx.post(f"{app.BASE_URL}/cinematic/camera-cuts/range", json={
        "AssetPath": asset_path, "ExpressionPath": section_path, "SizeX": lower_tick_frame, "SizeY": upper_tick_frame,
        "ExpectedSizeX": expected_lower_tick_frame, "ExpectedSizeY": expected_upper_tick_frame,
        "ExpectedClassPath": expected_section_class_path, "ExpectedAssetSnapshot": expected_camera_track_snapshot,
        "SourceOrder": [int(allow_layout_changes)], "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


def cinematic_take_metadata(asset_path: str, operation: str = "Inspect", metadata_path: str = "",
                              expected_metadata_exists: bool = False, expected_sequence_class_path: str = "",
                              expected_take_metadata_snapshot: str = "", text: str = "", number: int = 1,
                              enabled: bool = False, confirm: bool = False, dry_run: bool = True) -> str:
    """Native Take Recorder metadata Inspect/Create/Slate/TakeNumber/Description/Lock/FrameRateFromTimecode.
    Exact class/full authored metadata+registry snapshot/prior existence/object path/confirmation/writable guards.
    Locked metadata only allows explicit Lock=False unlock. Slate<=256/description<=4096/take1..1M.
    Native slate/number setters broadcast global delegates; transaction/readback/dirty/dry-run, failures non-atomic.
    Creation native config/app-timecode defaults; does not access most-recent/global metadata or resolve soft refs.
    No recorder start/stop/media capture/naming tokens/evaluation/load/save/config-save. Unverified.
    """
    return httpx.post(f"{app.BASE_URL}/cinematic/takes/metadata", json={
        "AssetPath": asset_path, "FieldName": operation, "ExpressionPath": metadata_path,
        "bExpectedEnabled": expected_metadata_exists, "ExpectedClassPath": expected_sequence_class_path,
        "ExpectedAssetSnapshot": expected_take_metadata_snapshot, "OutputName": text, "Value": number,
        "bEnabled": enabled, "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


def set_cinematic_take_timing_metadata(asset_path: str, metadata_path: str, operation: str,
                                        expected_sequence_class_path: str, expected_take_metadata_snapshot: str,
                                        rate_numerator: int = 24, rate_denominator: int = 1,
                                        duration_frames: int = 0, subframe: float = 0,
                                        timecode_hmsf: list[int] = [], drop_frame: bool = False,
                                        confirm: bool = False, dry_run: bool = True) -> str:
    """Set native take FrameRate/Duration/TimecodeIn/TimecodeOut with exact class/full metadata-registry snapshot.
    Existing unlocked metadata/confirmation required. Manual rate/timecode requires from-timecode disabled first.
    Rate numerator-denominator1..1M/fps0.001..1000; duration0..1B integer frames plus native float subframe[0,1).
    Timecode HMSF hours0..23/minutes-seconds0..59/nominal frame, supported drop-frame rates/skipped labels checked.
    Does not synchronize sequence playback range/duration/timecode pair. Native GetFrameRate can overwrite authored
    rate if from-timecode is later enabled; inspector avoids that mutating getter. No recorder/evaluation/save.
    Transaction/native setter/full readback/dirty/dry-run; timing/undo/persistence unverified.
    """
    if operation not in ("FrameRate", "Duration", "TimecodeIn", "TimecodeOut"):
        raise ValueError("operation must be FrameRate, Duration, TimecodeIn or TimecodeOut")
    return httpx.post(f"{app.BASE_URL}/cinematic/takes/metadata", json={
        "AssetPath": asset_path, "ExpressionPath": metadata_path, "FieldName": operation,
        "bExpectedEnabled": True, "ExpectedClassPath": expected_sequence_class_path,
        "ExpectedAssetSnapshot": expected_take_metadata_snapshot,
        "SizeX": rate_numerator if operation == "FrameRate" else duration_frames,
        "SizeY": rate_denominator, "Value": subframe, "SourceOrder": timecode_hmsf,
        "bEnabled": drop_frame, "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


def set_cinematic_take_provenance_metadata(asset_path: str, metadata_path: str, operation: str,
                                            expected_sequence_class_path: str, expected_take_metadata_snapshot: str,
                                            value: str = "", expected_prior_origin_path: str = "",
                                            allow_state_change: bool = False,
                                            confirm: bool = False, dry_run: bool = True) -> str:
    """Set native take Timestamp/PresetOrigin/LevelOrigin with exact class/full metadata-registry snapshot.
    Timestamp: ISO-8601 (offset normalized to UTC) years1970..9999, empty clears to FDateTime(0); changing
    native Recorded() presence requires allow_state_change. Authored provenance only, not proof of a recording.
    PresetOrigin: exact loaded persistent TakePreset asset path; LevelOrigin: exact loaded persistent editor map
    UWorld path (stores its PersistentLevel). Empty clears. Origins need expected_prior_origin_path (current soft
    path, empty if none); replacing/clearing an existing reference requires allow_state_change. Inspector
    (cinematic_take_metadata) reports timestamp and origin soft paths without loading them. Existing unlocked
    metadata/confirmation required; transaction/native setter/full readback/dirty/dry-run. No load/save. Unverified.
    """
    if operation not in ("Timestamp", "PresetOrigin", "LevelOrigin"):
        raise ValueError("operation must be Timestamp, PresetOrigin or LevelOrigin")
    return httpx.post(f"{app.BASE_URL}/cinematic/takes/metadata", json={
        "AssetPath": asset_path, "ExpressionPath": metadata_path, "FieldName": operation,
        "bExpectedEnabled": True, "ExpectedClassPath": expected_sequence_class_path,
        "ExpectedAssetSnapshot": expected_take_metadata_snapshot, "OutputName": value,
        "ExpectedOutputName": expected_prior_origin_path, "SourceOrder": [1] if allow_state_change else [],
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


def remove_cinematic_take_metadata(asset_path: str, metadata_path: str,
                                     expected_sequence_class_path: str, expected_take_metadata_snapshot: str,
                                     allow_metadata_discard: bool = False, confirm: bool = False,
                                     dry_run: bool = True) -> str:
    """Detach native take metadata from sequence; retains UObject for undo, no asset deletion.
    Exact class/full authored metadata-registry snapshot/existing path/confirmation/writable scene,
    unlocked metadata and explicit discard opt-in required. Remaining registry full readback/transaction/dirty.
    External references not migrated; recording provenance/asset-registry labels may disappear on refresh.
    No recorder/player/evaluation/load/save. Native undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/cinematic/takes/metadata", json={
        "AssetPath": asset_path, "ExpressionPath": metadata_path, "FieldName": "Remove",
        "bExpectedEnabled": True, "ExpectedClassPath": expected_sequence_class_path,
        "ExpectedAssetSnapshot": expected_take_metadata_snapshot, "SourceOrder": [int(allow_metadata_discard)],
        "bConfirm": confirm, "bDryRun": dry_run}, timeout=180).text


@mcp.tool()
def inspect_cinematic_take_sources(asset_path: str, start: int = 0, count: int = 64) -> str:
    """Inspect existing native take source-list metadata/basic source identities, enabled/take/tint fields.
    Max128 owned unique sources/page128. Does not invoke custom readiness/display/Initialize callbacks,
    construct sources, record, resolve presets or load/save assets. Snapshot excludes custom configuration.
    Native source metadata/runtime readiness unverified.
    """
    return httpx.post(f"{app.BASE_URL}/cinematic/takes/sources/inspect", json={
        "AssetPath": asset_path, "BlockIndex": start, "Count": count}, timeout=180).text


# Tools listed to clients. Each picks one of the functions above with its variant argument.
level_sequence_channel_defaults = merged_tool("level_sequence_channel_defaults", {
    "level_sequence_channel_default": level_sequence_channel_default,
    "level_sequence_object_channel_default": level_sequence_object_channel_default,
})
discover_level_sequence_channel_info = merged_tool("discover_level_sequence_channel_info", {
    "discover_level_sequence_numeric_channels": discover_level_sequence_numeric_channels,
    "discover_level_sequence_channels": discover_level_sequence_channels,
})
level_sequence_channel_keys = merged_tool("level_sequence_channel_keys", {
    "level_sequence_numeric_key_policy": level_sequence_numeric_key_policy,
    "set_level_sequence_key_tangents": set_level_sequence_key_tangents,
    "move_level_sequence_numeric_key": move_level_sequence_numeric_key,
    "set_level_sequence_numeric_key_value": set_level_sequence_numeric_key_value,
    "edit_level_sequence_numeric_key": edit_level_sequence_numeric_key,
    "level_sequence_discrete_keys": level_sequence_discrete_keys,
    "level_sequence_object_keys": level_sequence_object_keys,
    "level_sequence_event_keys": level_sequence_event_keys,
    "bind_level_sequence_event_endpoint": bind_level_sequence_event_endpoint,
    "edit_level_sequence_event_payload": edit_level_sequence_event_payload,
    "create_level_sequence_event_endpoint": create_level_sequence_event_endpoint,
})
level_sequence_event_repeater = merged_tool("level_sequence_event_repeater", {
    "inspect_level_sequence_event_repeater": inspect_level_sequence_event_repeater,
    "level_sequence_event_repeater_endpoint": level_sequence_event_repeater_endpoint,
    "edit_level_sequence_repeater_payload": edit_level_sequence_repeater_payload,
})
sample_level_sequence_channel = merged_tool("sample_level_sequence_channel", {
    "sample_level_sequence_numeric_channel": sample_level_sequence_numeric_channel,
    "sample_level_sequence_discrete_channel": sample_level_sequence_discrete_channel,
    "sample_level_sequence_object_channel": sample_level_sequence_object_channel,
})
level_sequence_markers = merged_tool("level_sequence_markers", {
    "level_sequence_marked_frames": level_sequence_marked_frames,
    "set_level_sequence_marker_metadata": set_level_sequence_marker_metadata,
    "set_level_sequence_markers_locked": set_level_sequence_markers_locked,
})
level_sequence_folder = merged_tool("level_sequence_folder", {
    "level_sequence_folders": level_sequence_folders,
    "edit_level_sequence_folder_settings": edit_level_sequence_folder_settings,
    "move_or_remove_level_sequence_folder": move_or_remove_level_sequence_folder,
    "assign_level_sequence_folder_content": assign_level_sequence_folder_content,
})
level_sequence_binding_tag = merged_tool("level_sequence_binding_tag", {
    "level_sequence_binding_tags": level_sequence_binding_tags,
    "rename_level_sequence_binding_tag": rename_level_sequence_binding_tag,
})
cinematic_take_metadata_edit = merged_tool("cinematic_take_metadata_edit", {
    "cinematic_take_metadata": cinematic_take_metadata,
    "set_cinematic_take_timing_metadata": set_cinematic_take_timing_metadata,
    "set_cinematic_take_provenance_metadata": set_cinematic_take_provenance_metadata,
    "remove_cinematic_take_metadata": remove_cinematic_take_metadata,
})
