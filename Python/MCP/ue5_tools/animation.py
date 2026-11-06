"""Skeletons, animation sequences, Blend Spaces, Animation Blueprints and curves."""
import httpx

from . import app
from .app import merged_tool
from .app import mcp, _asset_request, _ext


@mcp.tool()
def add_animation_graph_node(asset_path: str, graph_name: str = "AnimGraph",
                             node_type_name: str = "") -> str:
    """Add a reflected AnimGraph node class to an Animation Blueprint graph."""
    return httpx.post(f"{app.BASE_URL}/graphs/nodes", json={
        "BpPath": asset_path, "GraphName": graph_name,
        "NodeKind": "generic", "NodeTypeName": node_type_name
    }).text


def edit_animation_asset(asset_path: str, operation: str, notify_track: str = "",
                         notify_class: str = "", notify_name: str = "",
                         time: float = 0.0, duration: float = 0.0) -> str:
    """Edit animation notify tracks/events or curves.

    Operations: add, add_state, remove_name, remove_track, add_track,
    remove_notify_track, add_curve, remove_curve.
    """
    response = httpx.post(f"{app.BASE_URL}/animations/notifies", json={
        "AssetPath": asset_path, "Operation": operation,
        "NotifyTrack": notify_track, "NotifyClass": notify_class,
        "NotifyName": notify_name, "Time": time, "Duration": duration
    })
    return response.text


@mcp.tool()
def edit_montage_section(asset_path: str, section_name: str, start_time: float = 0.0,
                         next_section_name: str = "", delete: bool = False) -> str:
    """Create, update, link, or delete an Animation Montage section."""
    response = httpx.patch(f"{app.BASE_URL}/animations/montage-sections", json={
        "AssetPath": asset_path, "SectionName": section_name,
        "StartTime": start_time, "NextSectionName": next_section_name,
        "bDelete": delete
    })
    return response.text


@mcp.tool()
def get_animation_curve(asset_path: str, curve_name: str) -> str:
    """Read float keys from an animation curve."""
    response = httpx.get(f"{app.BASE_URL}/animations/curves", params={
        "asset_path": asset_path, "curve_name": curve_name
    })
    return response.text


def edit_animation_curve(asset_path: str, operation: str, curve_name: str,
                         notify_track: str = "", time: float = 0.0, value: float = 0.0,
                         vector_value: dict | None = None) -> str:
    """Add/remove curves, add float/vector keys, or edit sync markers."""
    vector = vector_value or {"X": 0.0, "Y": 0.0, "Z": 0.0}
    response = httpx.post(f"{app.BASE_URL}/animations/notifies", json={
        "AssetPath": asset_path, "Operation": operation,
        "NotifyName": curve_name, "NotifyTrack": notify_track,
        "Time": time, "Value": value,
        "VectorValue": vector
    })
    return response.text


@mcp.tool()
def inspect_animation_sequence(asset_path: str) -> str:
    """Inspect Animation Sequence timing, source model, compression, and content counts."""
    return httpx.get(f"{app.BASE_URL}/animation-sequences/inspect", params={"asset_path": asset_path}).text


@mcp.tool()
def list_animation_sequence_tracks(asset_path: str) -> str:
    """List source bone tracks and their matching Skeleton bone indices."""
    return httpx.get(f"{app.BASE_URL}/animation-sequences/tracks", params={"asset_path": asset_path}).text


@mcp.tool()
def inspect_animation_bone_track_keys(asset_path: str, bone_name: str,
                                      start_frame: int = 0, count: int = 100) -> str:
    """Read a page of source bone-track transforms by frame."""
    return httpx.get(f"{app.BASE_URL}/animation-sequences/bone-track-keys", params={
        "asset_path": asset_path, "bone_name": bone_name,
        "start_frame": start_frame, "count": count,
    }).text


@mcp.tool()
def edit_animation_bone_track(asset_path: str, operation: str, bone_name: str,
                              frame_index: int = -1, translation: dict | None = None,
                              rotation: dict | None = None, scale: dict | None = None,
                              dry_run: bool = False, save: bool = False) -> str:
    """Add/remove a Skeleton bone track or replace one frame's transform.

    Translation and scale use X/Y/Z; rotation uses Pitch/Yaw/Roll degrees.
    """
    return httpx.patch(f"{app.BASE_URL}/animation-sequences/bone-tracks", json={
        "AssetPath": asset_path, "Operation": operation, "BoneName": bone_name,
        "FrameIndex": frame_index, "Translation": translation or {"X": 0, "Y": 0, "Z": 0},
        "Rotation": rotation or {"Pitch": 0, "Yaw": 0, "Roll": 0},
        "Scale": scale or {"X": 1, "Y": 1, "Z": 1},
        "bDryRun": dry_run, "bSave": save,
    }).text


@mcp.tool()
def edit_animation_sequence_timing(asset_path: str, operation: str,
                                   frame_rate_numerator: int = 30,
                                   frame_rate_denominator: int = 1,
                                   source_frames: int = -1, confirm_trim: bool = False,
                                   dry_run: bool = False, save: bool = False) -> str:
    """Change source frame rate or resize frames with bone-key resampling.

    Use operation set_frame_rate or resize. Shortening requires confirm_trim.
    """
    return httpx.patch(f"{app.BASE_URL}/animation-sequences/timing", json={
        "AssetPath": asset_path, "Operation": operation,
        "FrameRateNumerator": frame_rate_numerator,
        "FrameRateDenominator": frame_rate_denominator,
        "SourceFrames": source_frames, "bConfirmTrim": confirm_trim,
        "bDryRun": dry_run, "bSave": save,
    }).text


@mcp.tool()
def inspect_animation_sequence_timeline(asset_path: str) -> str:
    """List notify tracks/events, sync markers, curves, and animated attributes."""
    return httpx.get(f"{app.BASE_URL}/animation-sequences/timeline", params={"asset_path": asset_path}).text


@mcp.tool()
def list_animation_sequence_attributes(asset_path: str) -> str:
    """List animated bone attributes and their typed keys."""
    return httpx.get(f"{app.BASE_URL}/animation-sequences/attributes", params={"asset_path": asset_path}).text


@mcp.tool()
def edit_animation_sequence_attribute(asset_path: str, operation: str,
                                      attribute_name: str, bone_name: str,
                                      attribute_type: str, time: float = 0.0,
                                      value: str = "", dry_run: bool = False,
                                      save: bool = False) -> str:
    """Add/remove a typed bone attribute or set/remove one key.

    Types include float, integer, string, vector, transform, or a registered
    ScriptStruct path. Vector uses X=,Y=,Z=; transform uses T|R|S triples.
    """
    return httpx.patch(f"{app.BASE_URL}/animation-sequences/attributes", json={
        "AssetPath": asset_path, "Operation": operation,
        "AttributeName": attribute_name, "BoneName": bone_name,
        "AttributeType": attribute_type, "Time": time, "Value": value,
        "bDryRun": dry_run, "bSave": save,
    }).text


@mcp.tool()
def validate_animation_sequence(asset_path: str) -> str:
    """Check Skeleton, source frames, bone tracks, attributes, notifies, and sync markers."""
    return httpx.post(f"{app.BASE_URL}/animation-sequences/validate", json={"AssetPath": asset_path}).text


@mcp.tool()
def create_animation_sequence(asset_path: str, skeleton_path: str,
                              preview_mesh_path: str = "") -> str:
    """Create an empty Animation Sequence from a valid Skeleton asset."""
    return httpx.post(f"{app.BASE_URL}/animation-sequences/create", json={
        "AssetPath": asset_path,
        "SkeletonPath": skeleton_path,
        "PreviewMeshPath": preview_mesh_path
    }).text


@mcp.tool()
def edit_animation_sequence_settings(asset_path: str, properties: dict, save: bool = False) -> str:
    """Edit reflected Animation Sequence settings."""
    return _asset_request("animation-sequences/settings", asset_path, properties, save=save)


@mcp.tool()
def inspect_animation_sequence_compression(asset_path: str) -> str:
    """Inspect bone/curve compression assets, frame stripping, error scale, and cache state."""
    return httpx.get(f"{app.BASE_URL}/animation-sequences/compression", params={"asset_path": asset_path}).text


@mcp.tool()
def edit_animation_sequence_compression(asset_path: str, bone_settings_path: str = "",
                                        curve_settings_path: str = "",
                                        variable_frame_stripping_path: str = "",
                                        allow_frame_stripping: bool | None = None,
                                        error_threshold_scale: float | None = None,
                                        dry_run: bool = False, save: bool = False) -> str:
    """Set validated Animation Sequence compression assets and related options."""
    return httpx.patch(f"{app.BASE_URL}/animation-sequences/compression", json={
        "AssetPath": asset_path, "BoneSettingsPath": bone_settings_path,
        "CurveSettingsPath": curve_settings_path,
        "VariableFrameStrippingPath": variable_frame_stripping_path,
        "bSetAllowFrameStripping": allow_frame_stripping is not None,
        "bAllowFrameStripping": allow_frame_stripping if allow_frame_stripping is not None else False,
        "bSetErrorThresholdScale": error_threshold_scale is not None,
        "ErrorThresholdScale": error_threshold_scale if error_threshold_scale is not None else 1.0,
        "bDryRun": dry_run, "bSave": save,
    }).text


@mcp.tool()
def inspect_blend_space(asset_path: str) -> str:
    """Inspect a Blend Space or Blend Space 1D."""
    return httpx.get(f"{app.BASE_URL}/blend-spaces/inspect", params={"asset_path": asset_path}).text


@mcp.tool()
def validate_blend_space(asset_path: str) -> str:
    """Check Blend Space axes, sample compatibility, coordinates, and interpolation data."""
    return httpx.post(f"{app.BASE_URL}/blend-spaces/validate", json={"AssetPath": asset_path}).text


@mcp.tool()
def list_blend_space_samples(asset_path: str) -> str:
    """List Blend Space sample assets and coordinates."""
    return httpx.get(f"{app.BASE_URL}/blend-spaces/samples", params={"asset_path": asset_path}).text


@mcp.tool()
def list_blend_space_axes(asset_path: str) -> str:
    """List the active axes of a Blend Space or Blend Space 1D."""
    return httpx.get(f"{app.BASE_URL}/blend-spaces/axes", params={"asset_path": asset_path}).text


@mcp.tool()
def edit_blend_space_axis(asset_path: str, axis_index: int,
                          properties: dict[str, str], dry_run: bool = False,
                          save: bool = False) -> str:
    """Edit axis display_name, min, max, grid_num, snap_to_grid, or wrap_input."""
    return httpx.post(f"{app.BASE_URL}/blend-spaces/axes", json={
        "AssetPath": asset_path, "AxisIndex": axis_index,
        "Properties": {key: str(value).lower() if isinstance(value, bool) else str(value)
                       for key, value in properties.items()},
        "bDryRun": dry_run, "bSave": save
    }).text


@mcp.tool()
def rebuild_blend_space(asset_path: str, dry_run: bool = False,
                        save: bool = False) -> str:
    """Rebuild Blend Space segmentation or triangulation from its samples."""
    return httpx.post(f"{app.BASE_URL}/blend-spaces/rebuild", json={
        "AssetPath": asset_path, "bDryRun": dry_run, "bSave": save
    }).text


@mcp.tool()
def preview_blend_space_input(asset_path: str, x: float, y: float = 0.0,
                              z: float = 0.0) -> str:
    """Preview the sampled animation weights at a Blend Space input."""
    return httpx.post(f"{app.BASE_URL}/blend-spaces/preview", json={
        "AssetPath": asset_path, "SampleValue": {"X": x, "Y": y, "Z": z}
    }).text


@mcp.tool()
def edit_blend_space_sample(asset_path: str, operation: str,
                            animation_path: str = "", sample_index: int = -1,
                            x: float = 0.0, y: float = 0.0, z: float = 0.0,
                            dry_run: bool = False, confirm: bool = False,
                            save: bool = False, sample_id: str = "") -> str:
    """Add, update, move, or delete a Blend Space sample by persistent ID or index. Delete requires confirm."""
    return httpx.post(f"{app.BASE_URL}/blend-spaces/samples", json={
        "AssetPath": asset_path, "Operation": operation,
        "AnimationPath": animation_path, "SampleIndex": sample_index,
        "SampleId": sample_id,
        "SampleValue": {"X": x, "Y": y, "Z": z},
        "bDryRun": dry_run, "bConfirm": confirm, "bSave": save
    }).text


@mcp.tool()
def inspect_animation_blueprint(asset_path: str) -> str:
    """Summarize an Animation Blueprint's Skeleton, graphs, states, and status."""
    return httpx.get(f"{app.BASE_URL}/animation-blueprints/inspect", params={"asset_path": asset_path}).text


@mcp.tool()
def list_animation_blueprint_graphs(asset_path: str, graph_path: str = "") -> str:
    """List nested graphs or inspect one graph's nodes, pose pins, and links."""
    return httpx.get(f"{app.BASE_URL}/animation-blueprints/graphs", params={
        "asset_path": asset_path, "graph_path": graph_path,
    }).text


@mcp.tool()
def list_animation_blueprint_state_machines(asset_path: str) -> str:
    """Inspect state machines, states, transitions, rules, and blend settings."""
    return httpx.get(f"{app.BASE_URL}/animation-blueprints/state-machines", params={"asset_path": asset_path}).text


@mcp.tool()
def edit_animation_blueprint_state_machine(asset_path: str, state_machine_graph_path: str,
                                            operation: str, state_name: str = "", node_id: str = "",
                                            from_state_id: str = "", to_state_id: str = "",
                                            always_reset_on_entry: bool = False,
                                            x: int = 0, y: int = 0,
                                            confirm: bool = False, dry_run: bool = False,
                                            save: bool = False) -> str:
    """Add/remove states or transitions, or set the state-machine entry target."""
    return httpx.patch(f"{app.BASE_URL}/animation-blueprints/state-machines", json={
        "AssetPath": asset_path, "StateMachineGraphPath": state_machine_graph_path,
        "Operation": operation, "StateName": state_name, "NodeId": node_id,
        "FromStateId": from_state_id, "ToStateId": to_state_id,
        "bAlwaysResetOnEntry": always_reset_on_entry,
        "X": x, "Y": y, "bConfirm": confirm, "bDryRun": dry_run,
        "bSave": save,
    }).text


@mcp.tool()
def list_animation_blueprint_variables(asset_path: str) -> str:
    """List Animation Blueprint variables with types, categories, and defaults."""
    return httpx.get(f"{app.BASE_URL}/animation-blueprints/variables", params={"asset_path": asset_path}).text


@mcp.tool()
def edit_animation_blueprint_transition(asset_path: str, state_machine_graph_path: str,
                                         transition_id: str, crossfade_duration: float | None = None,
                                         blend_mode: str = "", priority_order: int | None = None,
                                         disabled: bool | None = None,
                                         automatic_rule: bool | None = None,
                                         dry_run: bool = False, save: bool = False) -> str:
    """Edit a state transition by GUID, including blend and priority settings."""
    return httpx.patch(f"{app.BASE_URL}/animation-blueprints/transitions", json={
        "AssetPath": asset_path, "StateMachineGraphPath": state_machine_graph_path,
        "TransitionId": transition_id,
        "bSetCrossfadeDuration": crossfade_duration is not None,
        "CrossfadeDuration": crossfade_duration if crossfade_duration is not None else 0.2,
        "bSetBlendMode": bool(blend_mode), "BlendMode": blend_mode,
        "bSetPriorityOrder": priority_order is not None,
        "PriorityOrder": priority_order if priority_order is not None else 1,
        "bSetDisabled": disabled is not None,
        "bDisabled": disabled if disabled is not None else False,
        "bSetAutomaticRule": automatic_rule is not None,
        "bAutomaticRule": automatic_rule if automatic_rule is not None else False,
        "bDryRun": dry_run, "bSave": save,
    }).text


@mcp.tool()
def edit_animation_blueprint_pose_link(asset_path: str, graph_path: str, operation: str,
                                       output_node_id: str, output_pin_name: str,
                                       input_node_id: str, input_pin_name: str,
                                       confirm_replace: bool = False,
                                       dry_run: bool = False, save: bool = False) -> str:
    """Connect or disconnect pose pins using the Animation Graph schema."""
    return httpx.patch(f"{app.BASE_URL}/animation-blueprints/pose-links", json={
        "AssetPath": asset_path, "GraphPath": graph_path, "Operation": operation,
        "OutputNodeId": output_node_id, "OutputPinName": output_pin_name,
        "InputNodeId": input_node_id, "InputPinName": input_pin_name,
        "bConfirmReplace": confirm_replace, "bDryRun": dry_run, "bSave": save,
    }).text


@mcp.tool()
def layout_animation_blueprint_graph(asset_path: str, graph_path: str,
                                     column_spacing: int = 100, row_spacing: int = 48,
                                     dry_run: bool = False, save: bool = False) -> str:
    """Format an Animation Blueprint graph identified by its full path. The spacings are the gaps between nodes."""
    return httpx.post(f"{app.BASE_URL}/animation-blueprints/layout", json={
        "AssetPath": asset_path, "GraphPath": graph_path,
        "ColumnSpacing": column_spacing, "RowSpacing": row_spacing,
        "bDryRun": dry_run, "bSave": save,
    }).text


@mcp.tool()
def validate_animation_blueprint(asset_path: str) -> str:
    """Check Skeleton, graph links, state-machine wiring, and compile status."""
    return httpx.post(f"{app.BASE_URL}/animation-blueprints/validate", json={"AssetPath": asset_path}).text


@mcp.tool()
def compile_animation_blueprint(asset_path: str, save: bool = False) -> str:
    """Compile an Animation Blueprint and report its resulting status."""
    return httpx.post(f"{app.BASE_URL}/animation-blueprints/compile", json={
        "AssetPath": asset_path, "bSave": save,
    }).text


@mcp.tool()
def inspect_skeleton_structure(asset_path: str) -> str:
    """Inspect registered Skeleton bones, skeleton-owned sockets and virtual bones.

    Includes bounded socket/name/parent/transform and virtual-bone dependency diagnostics.
    Preview entries expose soft asset paths, loaded/registered status and target validity.
    Blend profiles include native modes, owner integrity and bounded per-bone scales.
    Curve metadata includes material/morph flags, native MaxLOD and linked bones.
    Structural validity does not establish animation/runtime validity.
    Bone entries include native local and composed component-space reference transforms,
    using location, scale and XYZW quaternion with finite flags.
    Full asset object path required. Returns <=1024 bones and <=256 sockets/virtual
    bones with truncation, local socket transforms and dirty state. Mesh-only socket
    overrides are not included. Loads asset; does not mutate it.
    """
    return httpx.get(f"{app.BASE_URL}/skeletons/structure", params={
        "asset_path": asset_path
    }, timeout=180).text


@mcp.tool()
def edit_skeleton_socket(asset_path: str, socket_name: str, bone_name: str,
                         operation: str = "create", location: dict | None = None,
                         rotation: dict | None = None, scale: dict | None = None,
                         force_always_animated: bool = True, confirm: bool = False,
                         dry_run: bool = False, save: bool = False) -> str:
    """Create/update a skeleton-owned socket on a /Game Skeleton with native transaction.

    Full object path and confirmation required; PIE must be stopped. Update replaces
    all socket transform/parent settings. Vectors use X/Y/Z; rotation Pitch/Yaw/Roll.
    Defaults are zero translation/rotation and unit scale. Mesh overrides excluded.
    """
    return httpx.post(f"{app.BASE_URL}/skeletons/sockets", json={
        "AssetPath": asset_path, "SocketName": socket_name, "BoneName": bone_name,
        "Operation": operation, "Location": location or {}, "Rotation": rotation or {},
        "Scale": scale if scale is not None else {"X": 1, "Y": 1, "Z": 1},
        "bForceAlwaysAnimated": force_always_animated, "bConfirm": confirm,
        "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def delete_skeleton_socket(asset_path: str, socket_name: str, confirm: bool = False,
                           dry_run: bool = False, save: bool = False) -> str:
    """Delete exactly one skeleton-owned socket and its Skeleton preview attachments.

    Requires confirmed /Game Skeleton full object path and stopped PIE. Dry-run
    validates only. Mesh overrides and external attachment names are not rewritten.
    """
    return httpx.request("DELETE", f"{app.BASE_URL}/skeletons/sockets", json={
        "AssetPath": asset_path, "SocketName": socket_name, "bConfirm": confirm,
        "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def create_skeleton_virtual_bone(asset_path: str, source_bone: str, target_bone: str,
                                 name: str = "", confirm: bool = False,
                                 dry_run: bool = False, save: bool = False) -> str:
    """Create native virtual bone on confirmed /Game Skeleton with stopped PIE.

    Endpoints must exist and differ. Empty name uses native generated VB name;
    explicit names require native VB prefix. Rejects name/pair/socket collisions.
    Native API rebuilds virtual bone data; transaction and optional Skeleton save.
    """
    return httpx.post(f"{app.BASE_URL}/skeletons/virtual-bones", json={
        "AssetPath": asset_path, "SourceBone": source_bone, "TargetBone": target_bone,
        "Name": name, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def delete_skeleton_virtual_bones(asset_path: str, names: list[str], cascade: bool = False,
                                  confirm: bool = False, dry_run: bool = False,
                                  save: bool = False) -> str:
    """Delete virtual bones in dependency order using native Skeleton rebuild.

    Requires confirmed /Game Skeleton, stopped PIE and 1..256 unique existing names.
    cascade includes dependent virtual bones; otherwise missing dependencies reject.
    Attached skeleton sockets must be reparented/deleted first. Matching Skeleton
    preview attachments are removed transactionally. Dry-run returns order/counts.
    External animation/mesh socket references are not rewritten or saved.
    """
    return httpx.request("DELETE", f"{app.BASE_URL}/skeletons/virtual-bones", json={
        "AssetPath": asset_path, "Names": names, "bCascade": cascade,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def rename_skeleton_virtual_bone(asset_path: str, name: str, new_name: str,
                                 confirm: bool = False, dry_run: bool = False,
                                 save: bool = False) -> str:
    """Rename native virtual bone and reparent Skeleton-owned socket attachments.

    Requires confirmed /Game Skeleton and stopped PIE; new name uses native VB prefix.
    Source/target dependencies, Skeleton preview names and socket attachments update transactionally
    before native rebuilding. External animation/mesh-only references are not rewritten.
    """
    return httpx.patch(f"{app.BASE_URL}/skeletons/virtual-bones/name", json={
        "AssetPath": asset_path, "Name": name, "NewName": new_name,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def rename_skeleton_socket(asset_path: str, socket_name: str, new_name: str,
                            confirm: bool = False, dry_run: bool = False,
                            save: bool = False) -> str:
    """Rename Skeleton-owned socket and Skeleton preview attachment names.

    Requires confirmed /Game Skeleton and stopped PIE. Rejects socket/bone collisions;
    uses transaction, dry-run and optional save. External component/Blueprint/mesh-only
    references are not rewritten. Returns affected preview attachment count.
    """
    return httpx.patch(f"{app.BASE_URL}/skeletons/sockets/name", json={
        "AssetPath": asset_path, "SocketName": socket_name, "NewName": new_name,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def edit_skeletal_preview_attachment(asset_path: str, preview_asset_path: str,
                                      attach_name: str, owner_kind: str = "skeleton",
                                      operation: str = "add", confirm: bool = False,
                                      dry_run: bool = False, save: bool = False,
                                      destination_attach_name: str = "") -> str:
    """Add/remove persistent StaticMesh/SkeletalMesh preview attachment metadata.

    owner_kind skeleton/mesh, operation add/remove/move. Move uses destination_attach_name,
    validates target and rejects duplicate destination pair without loading preview assets. Requires confirmed /Game owner,
    stopped PIE. Add requires registered mesh preview asset and existing bone/socket.
    Remove matches stored soft path without loading it; deleted assets/stale targets
    can be cleaned up using paths returned by inspection.
    Native transaction and optional save; does not attach runtime actors or explicitly
    instantiate an active Persona preview component.
    """
    if owner_kind not in {"skeleton", "mesh"}:
        raise ValueError("owner_kind requires skeleton or mesh")
    family = "skeletons" if owner_kind == "skeleton" else "skeletal-meshes"
    return httpx.post(f"{app.BASE_URL}/{family}/preview-attachments", json={
        "AssetPath": asset_path, "PreviewAssetPath": preview_asset_path,
        "SocketName": attach_name, "NewName": destination_attach_name, "Operation": operation, "bConfirm": confirm,
        "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def edit_skeleton_compatibility(asset_path: str, source_path: str, operation: str = "add",
                                 confirm: bool = False, dry_run: bool = False,
                                 save: bool = False) -> str:
    """Add/remove one-way native compatible-Skeleton declaration with transaction.

    Requires stopped PIE and confirmed /Game Skeleton. Add validates source asset;
    remove uses stored soft path and permits missing source. No reciprocal edit,
    hierarchy equivalence proof or animation retargeting. Structure inspector lists refs.
    """
    return httpx.post(f"{app.BASE_URL}/skeletons/compatibility", json={
        "AssetPath": asset_path, "SourcePath": source_path, "Operation": operation,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def compare_skeleton_hierarchies(target_path: str, source_path: str) -> str:
    """Compare registered Skeleton raw bone names, direct parents and local reference poses.

    Loads <=4096-bone Skeletons without mutation; returns directional source coverage,
    counts and <=256 differences. Pose tolerance 0.0001. This is structural evidence,
    not native animation compatibility proof or a retarget/skin deformation preview.
    """
    return httpx.post(f"{app.BASE_URL}/skeletons/compare", json={
        "AssetPath": target_path, "SourcePath": source_path
    }, timeout=180).text


@mcp.tool()
def set_skeleton_blend_profile_scales(asset_path: str, profile_name: str, bones: list[str],
                                      scale: float, children: bool = False,
                                      confirm: bool = False, dry_run: bool = False,
                                      save: bool = False) -> str:
    """Set existing native blend-profile/mask bone scales with transaction.

    Confirmed /Game Skeleton, stopped PIE, <=256 unique raw bones; children expands
    descendants. TimeFactor/BlendMask use [0,1], WeightFactor [0,1000]. Native setters
    create explicit entries when values differ; existing default-equivalent values
    remain unchanged. Reports affected/changed counts; optional Skeleton save.
    """
    return httpx.patch(f"{app.BASE_URL}/skeletons/blend-profiles/scales", json={
        "AssetPath": asset_path, "ProfileName": profile_name, "Bones": bones,
        "Scale": scale, "bChildren": children, "bConfirm": confirm,
        "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def create_skeleton_blend_profile(asset_path: str, profile_name: str,
                                  mode: str = "TimeFactor", confirm: bool = False,
                                  dry_run: bool = False, save: bool = False,
                                  source_profile_name: str = "") -> str:
    """Create owned native blend profile/mask on confirmed /Game Skeleton.

    Modes TimeFactor/WeightFactor/BlendMask. Requires stopped PIE, valid unused object
    name and <64 profiles; initializes native Skeleton ownership. Empty profile uses
    native default scales; author explicit scales separately. source_profile_name
    duplicates an owned source and preserves its mode/scales (mode argument ignored
    after source validation). Transaction/optional save.
    """
    return httpx.post(f"{app.BASE_URL}/skeletons/blend-profiles", json={
        "AssetPath": asset_path, "ProfileName": profile_name, "Mode": mode,
        "SourceProfileName": source_profile_name,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def rename_skeleton_blend_profile(asset_path: str, profile_name: str, new_name: str,
                                   confirm: bool = False, dry_run: bool = False,
                                   save: bool = False) -> str:
    """Rename existing owned blend profile/mask through native Skeleton API.

    Requires confirmed /Game Skeleton, stopped PIE and unused valid object name.
    Preserves profile identity/hard references; transaction/dry-run/optional save.
    Native rename creates no redirector and does not migrate external soft paths/strings.
    """
    return httpx.patch(f"{app.BASE_URL}/skeletons/blend-profiles/name", json={
        "AssetPath": asset_path, "ProfileName": profile_name, "NewName": new_name,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def reset_skeleton_blend_profile_entries(asset_path: str, profile_name: str,
                                          bones: list[str], children: bool = False,
                                          confirm: bool = False, dry_run: bool = False,
                                          save: bool = False) -> str:
    """Remove explicit blend-profile/mask bone entries, restoring native default scale.

    Requires confirmed /Game Skeleton, stopped PIE and <=256 unique raw bone names.
    children expands descendants. Native RemoveEntry, transaction, dry-run/no-op and
    optional save; returns removed-entry count and native default scale.
    """
    return httpx.post(f"{app.BASE_URL}/skeletons/blend-profiles/reset", json={
        "AssetPath": asset_path, "ProfileName": profile_name, "Bones": bones,
        "bChildren": children, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_skeleton_blend_profile_mode(asset_path: str, profile_name: str, mode: str,
                                     confirm: bool = False, dry_run: bool = False,
                                     save: bool = False) -> str:
    """Change native profile interpretation to TimeFactor/WeightFactor/BlendMask.

    Requires confirmed /Game Skeleton and stopped PIE. Existing scales must satisfy
    destination mode bounds; no automatic clamping. Transaction/dry-run/optional save.
    Changes implicit defaults too; consumer graph compatibility is not compiled/proven.
    """
    return httpx.patch(f"{app.BASE_URL}/skeletons/blend-profiles/mode", json={
        "AssetPath": asset_path, "ProfileName": profile_name, "Mode": mode,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def inspect_skeleton_blend_profile_references(asset_path: str, profile_name: str) -> str:
    """Inspect loaded strong profile referencers and Skeleton-wide package dependencies.

    Returns <=256 entries per category, excluding owner/profile from loaded scan.
    Package references are not profile-specific. Unloaded/soft/string references may
    be absent; empty results do not prove deletion safety. Does not mutate assets.
    """
    return httpx.post(f"{app.BASE_URL}/skeletons/blend-profiles/references", json={
        "AssetPath": asset_path, "ProfileName": profile_name
    }, timeout=180).text


@mcp.tool()
def delete_skeleton_blend_profile(asset_path: str, profile_name: str,
                                   allow_referenced: bool = False, confirm: bool = False,
                                   dry_run: bool = False, save: bool = False) -> str:
    """Delete owned profile using native editor-style array removal and garbage marking.

    Confirmed /Game Skeleton, stopped PIE. Blocks loaded strong profile references or
    Skeleton-wide package dependencies unless allow_referenced explicitly true.
    Dry-run reports counts/blocking without deleting. External references are not
    rewritten/saved; missing soft/string/unloaded references cannot be ruled out.
    Transaction/garbage-collection undo behavior remains unverified.
    """
    return httpx.request("DELETE", f"{app.BASE_URL}/skeletons/blend-profiles", json={
        "AssetPath": asset_path, "ProfileName": profile_name,
        "bAllowReferenced": allow_referenced, "bConfirm": confirm,
        "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def inspect_skeleton_blend_profile_scales(asset_path: str, profile_name: str,
                                           bones: list[str] | None = None) -> str:
    """Read native effective profile scales and distinguish explicit entries/defaults.

    Supply <=256 unique raw bone names or omit for first <=256 raw bones with truncation.
    Includes native mode/default scale and explicit entry indices. Does not evaluate
    animation blends or force profile cache refresh. Loads Skeleton without mutation.
    """
    return httpx.post(f"{app.BASE_URL}/skeletons/blend-profiles/scales/query", json={
        "AssetPath": asset_path, "ProfileName": profile_name, "Bones": bones or []
    }, timeout=180).text


@mcp.tool()
def edit_skeleton_curve_metadata(asset_path: str, name: str, operation: str = "create",
                                  material: bool = False, morph_target: bool = False,
                                  linked_bones: list[str] | None = None, max_lod: int = 255,
                                  confirm: bool = False, dry_run: bool = False,
                                  save: bool = False) -> str:
    """Create/update full Skeleton curve metadata settings with native storage APIs.

    Confirmed /Game Skeleton/stopped PIE; <=64 unique linked bones; native uint8 LOD
    [0,255]. Update replaces flags/links/LOD. Owner and metadata storage transaction,
    dry-run/no-op/optional save. Does not create animation curve keys or morph geometry.
    """
    return httpx.post(f"{app.BASE_URL}/skeletons/curve-metadata", json={
        "AssetPath": asset_path, "Name": name, "Operation": operation,
        "bMaterial": material, "bMorphTarget": morph_target, "LinkedBones": linked_bones or [],
        "MaxLOD": max_lod, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def change_skeleton_curve_metadata(asset_path: str, name: str, operation: str,
                                    new_name: str = "", confirm: bool = False,
                                    dry_run: bool = False, save: bool = False) -> str:
    """Rename/remove Skeleton curve metadata through native storage APIs.

    Confirmed /Game Skeleton/stopped PIE; rename requires unused destination.
    Owner/storage transaction, no-op/dry-run/optional save. Animation tracks/keys and
    external references are not renamed/deleted; native collection may recreate metadata.
    """
    return httpx.post(f"{app.BASE_URL}/skeletons/curve-metadata/lifecycle", json={
        "AssetPath": asset_path, "Name": name, "Operation": operation, "NewName": new_name,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def inspect_animation_rich_float_curve(asset_path: str, curve_name: str,
                                        start: int = 0, count: int = 256) -> str:
    """Read paginated native float curve interpolation/tangent/weight/extrapolation data.

    AnimSequence source data model required; count 1..512. Returns numeric native enum
    values and finite-safe rich key fields. Does not evaluate or modify curve keys.
    """
    return httpx.get(f"{app.BASE_URL}/animations/curves/rich", params={
        "asset_path": asset_path, "curve_name": curve_name, "start": start, "count": count
    }, timeout=180).text


@mcp.tool()
def replace_animation_rich_float_curve(asset_path: str, curve_name: str, keys: list[dict],
                                        confirm: bool = False, dry_run: bool = False,
                                        save: bool = False) -> str:
    """Replace <=4096 existing source float curve rich keys through native controller.

    Confirmed /Game AnimSequence/stopped PIE; keys strictly ordered within duration.
    Rows use Time/Value/Interpolation/TangentMode/WeightMode/ArriveTangent/LeaveTangent/
    ArriveWeight/LeaveWeight. Numeric native modes match rich inspection (0..2/0..4/0..3).
    Empty keys clears keys. Native auto tangents may recalculate; extrapolation unchanged.
    """
    return httpx.patch(f"{app.BASE_URL}/animations/curves/rich", json={
        "AssetPath": asset_path, "CurveName": curve_name, "Keys": keys,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_animation_float_curve_extrapolation(asset_path: str, curve_name: str,
                                             pre: int = 4, post: int = 4,
                                             confirm: bool = False, dry_run: bool = False,
                                             save: bool = False) -> str:
    """Set existing source float curve extrapolation without replacing keys.

    Modes: 0 Cycle, 1 CycleWithOffset, 2 Oscillate, 3 Linear, 4 Constant.
    Requires confirmed /Game AnimSequence/stopped PIE; native controller transaction,
    no-op/dry-run and optional save. Rich inspection returns current modes.
    """
    return httpx.patch(f"{app.BASE_URL}/animations/curves/extrapolation", json={
        "AssetPath": asset_path, "CurveName": curve_name,
        "PreExtrapolation": pre, "PostExtrapolation": post,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def evaluate_animation_float_curve(asset_path: str, curve_name: str, times: list[float],
                                     default_value: float = 0) -> str:
    """Evaluate native source rich float curve at <=512 finite bounded times.

    Times may lie outside animation duration to exercise extrapolation. Returns native
    values/finite flags; default follows FRichCurve semantics. No compressed animation,
    runtime curve blending, material/morph evaluation or asset mutation.
    """
    return httpx.post(f"{app.BASE_URL}/animations/curves/evaluate", json={
        "AssetPath": asset_path, "CurveName": curve_name, "Times": times,
        "DefaultValue": default_value
    }, timeout=180).text


@mcp.tool()
def duplicate_animation_float_curve(asset_path: str, curve_name: str, new_name: str,
                                      confirm: bool = False, dry_run: bool = False,
                                      save: bool = False) -> str:
    """Duplicate existing float curve through native animation data controller.

    Confirmed /Game AnimSequence/stopped PIE; unused destination, <1024 curves and
    <=4096 source keys. Preserves native curve data/flags and explicitly copies editor color/comment (<=4096);
    controller transaction,
    dry-run/optional save. Skeleton metadata/external consumers not explicitly copied.
    """
    return httpx.post(f"{app.BASE_URL}/animations/curves/duplicate", json={
        "AssetPath": asset_path, "CurveName": curve_name, "NewName": new_name,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def rename_animation_float_curve(asset_path: str, curve_name: str, new_name: str,
                                   confirm: bool = False, dry_run: bool = False,
                                   save: bool = False) -> str:
    """Rename source float curve through native animation data controller.

    Confirmed /Game AnimSequence/stopped PIE, distinct unused destination and bounded
    source data. Preserves native keys/flags; controller transaction/dry-run/save.
    Skeleton metadata and material/morph/Blueprint consumer names are not migrated.
    """
    return httpx.patch(f"{app.BASE_URL}/animations/curves/name", json={
        "AssetPath": asset_path, "CurveName": curve_name, "NewName": new_name,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_animation_float_curve_flag(asset_path: str, curve_name: str, flag: str,
                                    enabled: bool = True, confirm: bool = False,
                                    dry_run: bool = False, save: bool = False) -> str:
    """Set native Editable/Metadata/Disabled float-curve flag transactionally.

    Requires confirmed /Game AnimSequence/stopped PIE; native controller/no-op/dry-run/save.
    Metadata flag differs from Skeleton curve metadata; native key-data side effects
    apply. Rich inspection returns complete numeric curve_flags.
    """
    return httpx.patch(f"{app.BASE_URL}/animations/curves/flag", json={
        "AssetPath": asset_path, "CurveName": curve_name, "Flag": flag,
        "bFlagEnabled": enabled, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_animation_float_curve_color(asset_path: str, curve_name: str, color: dict,
                                     confirm: bool = False, dry_run: bool = False,
                                     save: bool = False) -> str:
    """Set native float-curve editor display color; channels R/G/B/A in [0,1].

    Confirmed /Game AnimSequence/stopped PIE, existing source curve; native controller
    transaction/no-op/dry-run/save. Rich inspection returns color_rgba. No key changes.
    """
    return httpx.patch(f"{app.BASE_URL}/animations/curves/color", json={
        "AssetPath": asset_path, "CurveName": curve_name, "Color": color,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


def edit_animation_rich_float_key(asset_path: str, curve_name: str, key: dict,
                                   operation: str = "set", confirm: bool = False,
                                   dry_run: bool = False, save: bool = False) -> str:
    """Set/remove one rich float key via native controller; other keys retained.

    Confirmed /Game sequence/stopped PIE. key uses rich replacement row fields;
    remove needs Time only and an existing key at exact native float time.
    Set prepares the full rich-key array with exact float time matching, <=4096 keys;
    native SetCurveKeys preserves supplied rich fields. Auto tangents may change.
    Native transaction/dry-run/optional save; extrapolation unchanged.
    """
    return httpx.post(f"{app.BASE_URL}/animations/curves/key", json={
        "AssetPath": asset_path, "CurveName": curve_name, "Key": key, "Operation": operation,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


def move_animation_rich_float_key(asset_path: str, curve_name: str, time: float,
                                   new_time: float, confirm: bool = False,
                                   dry_run: bool = False, save: bool = False) -> str:
    """Move existing rich float key to unused time, retaining value/tangent/weight fields.

    Exact native float source time; destination within sequence duration. Confirmed
    /Game sequence/stopped PIE, <=4096 keys. Prepared array/native controller transaction,
    dry-run/save. Auto tangent recalculation follows native SetCurveKeys behavior.
    """
    return httpx.post(f"{app.BASE_URL}/animations/curves/key", json={
        "AssetPath": asset_path, "CurveName": curve_name, "Key": {"Time": time},
        "Operation": "move", "NewTime": new_time, "bConfirm": confirm,
        "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def inspect_animation_transform_curve_channel(asset_path: str, curve_name: str,
                                               channel: str = "translation", axis: int = 0,
                                               start: int = 0, count: int = 256) -> str:
    """Read rich keys from one native transform-curve channel, count 1..512.

    channel translation/rotation/scale; axis 0/1/2 indexes native FVectorCurve slots.
    Returns keys/tangents/weights/extrapolation/flags/color. Rotation is stored native
    Euler channel data, not quaternion interpolation. Does not evaluate or mutate poses.
    """
    return httpx.get(f"{app.BASE_URL}/animations/curves/transform-channel", params={
        "asset_path": asset_path, "curve_name": curve_name, "channel": channel,
        "axis": axis, "start": start, "count": count
    }, timeout=180).text


@mcp.tool()
def replace_animation_transform_curve_channel(asset_path: str, curve_name: str,
                                               channel: str, axis: int, keys: list[dict],
                                               confirm: bool = False, dry_run: bool = False,
                                               save: bool = False) -> str:
    """Replace rich keys in one existing transform curve channel via native controller.

    channel translation/rotation/scale; axis 0..2 native slots. <=4096 rich-key rows
    as float replacement, strictly ordered times within duration; empty clears channel.
    Confirmed /Game sequence/stopped PIE; transaction/dry-run/save. Other channels and
    extrapolation retained. Rotation is native Euler data; no bone-track baking.
    """
    return httpx.patch(f"{app.BASE_URL}/animations/curves/transform-channel", json={
        "AssetPath": asset_path, "CurveName": curve_name, "Channel": channel,
        "Axis": axis, "Keys": keys, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def evaluate_animation_transform_curve_channel(asset_path: str, curve_name: str,
                                                channel: str, axis: int, times: list[float],
                                                default_value: float = 0) -> str:
    """Sample one source transform rich channel using native interpolation/extrapolation.

    channel translation/rotation/scale; axis 0..2; <=512 finite times within +/-1e6.
    Returns finite-safe values; fallback follows FRichCurve semantics. Rotation values
    are native Euler channel data. No pose/animation blending or bone-track baking.
    """
    return httpx.post(f"{app.BASE_URL}/animations/curves/transform-channel/evaluate", json={
        "AssetPath": asset_path, "CurveName": curve_name, "Channel": channel,
        "Axis": axis, "Times": times, "DefaultValue": default_value
    }, timeout=180).text


@mcp.tool()
def set_animation_transform_channel_extrapolation(asset_path: str, curve_name: str,
                                                   channel: str, axis: int,
                                                   pre: int = 4, post: int = 4,
                                                   confirm: bool = False,
                                                   dry_run: bool = False, save: bool = False) -> str:
    """Set native extrapolation on one existing transform curve channel.

    channel translation/rotation/scale; axis 0..2; pre/post modes 0 Cycle, 1 CycleWithOffset,
    2 Oscillate, 3 Linear, 4 Constant. Confirmed /Game sequence/stopped PIE; controller
    transaction/no-op/dry-run/save. Channel keys and other channels are preserved.
    """
    return httpx.patch(f"{app.BASE_URL}/animations/curves/transform-channel/extrapolation", json={
        "AssetPath": asset_path, "CurveName": curve_name, "Channel": channel,
        "Axis": axis, "PreExtrapolation": pre, "PostExtrapolation": post,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def evaluate_animation_transform_curve(asset_path: str, curve_name: str, times: list[float],
                                         blend_weight: float = 1) -> str:
    """Sample native full source transform curve, <=256 finite times and weight [0,1].

    Returns finite-safe location/scale/XYZW quaternion with native Euler conversion,
    empty-channel defaults and blend semantics. Not skeleton/component/world pose,
    compressed animation evaluation or bone-track baking. Does not mutate assets.
    """
    return httpx.post(f"{app.BASE_URL}/animations/curves/transform/evaluate", json={
        "AssetPath": asset_path, "CurveName": curve_name, "Times": times,
        "BlendWeight": blend_weight
    }, timeout=180).text


@mcp.tool()
def create_animation_transform_curve(asset_path: str, bone_name: str,
                                       confirm: bool = False, dry_run: bool = False,
                                       save: bool = False) -> str:
    """Create empty native editable drive-track transform curve for existing Skeleton bone.

    Confirmed /Game AnimSequence/stopped PIE, unused transform curve name and <1024
    curves. Native controller transaction/dry-run/save; author channels separately.
    No explicit bone-track bake requested; native derived-data notifications apply.
    """
    return httpx.post(f"{app.BASE_URL}/animations/curves/transform", json={
        "AssetPath": asset_path, "CurveName": bone_name, "bConfirm": confirm,
        "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def remove_animation_transform_curve(asset_path: str, curve_name: str,
                                       confirm: bool = False, dry_run: bool = False,
                                       save: bool = False) -> str:
    """Remove existing source transform curve and all nine channel key sets.

    Confirmed /Game AnimSequence/stopped PIE, native controller transaction/dry-run/save.
    Does not restore previously baked bone tracks or migrate external references.
    Native derived-data notifications apply; dry-run reports key count.
    """
    return httpx.request("DELETE", f"{app.BASE_URL}/animations/curves/transform", json={
        "AssetPath": asset_path, "CurveName": curve_name, "bConfirm": confirm,
        "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def duplicate_animation_transform_curve(asset_path: str, curve_name: str, destination_bone: str,
                                          confirm: bool = False, dry_run: bool = False,
                                          save: bool = False) -> str:
    """Duplicate all nine native transform channels to unused existing Skeleton bone name.

    Confirmed /Game sequence/stopped PIE, <1024 transform curves and <=4096 keys per
    source channel. Native controller transaction/dry-run/save. Copies curve data/flags;
    no explicit bone-track bake or external consumer migration.
    """
    return httpx.post(f"{app.BASE_URL}/animations/curves/transform/duplicate", json={
        "AssetPath": asset_path, "CurveName": curve_name, "NewName": destination_bone,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def rename_animation_transform_curve(asset_path: str, curve_name: str, destination_bone: str,
                                       confirm: bool = False, dry_run: bool = False,
                                       save: bool = False) -> str:
    """Rename native transform curve to distinct unused existing Skeleton bone name.

    Confirmed /Game sequence/stopped PIE, bounded source channels; native controller
    transaction/dry-run/save. Preserves nine-channel curve data; does not migrate
    external names or restore/rebake existing bone tracks explicitly.
    """
    return httpx.patch(f"{app.BASE_URL}/animations/curves/transform/name", json={
        "AssetPath": asset_path, "CurveName": curve_name, "NewName": destination_bone,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_animation_transform_curve_key(asset_path: str, curve_name: str, time: float,
                                       location: dict | None = None, rotation: dict | None = None,
                                       scale: dict | None = None, confirm: bool = False,
                                       dry_run: bool = False, save: bool = False) -> str:
    """Set native whole-transform key on existing curve at in-duration time.

    Confirmed /Game sequence/stopped PIE; finite bounded XYZ/PitchYawRoll values,
    <=4096 keys per channel. Defaults zero location/rotation, unit scale. Native Euler,
    time matching and tangent behavior apply; explicit rich tangents use channel tools.
    Controller transaction/dry-run/save; no explicit bone-track bake.
    """
    return httpx.post(f"{app.BASE_URL}/animations/curves/transform/key", json={
        "AssetPath": asset_path, "CurveName": curve_name, "Key": {"Time": time},
        "Location": location or {}, "Rotation": rotation or {},
        "Scale": scale if scale is not None else {"X": 1, "Y": 1, "Z": 1},
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def remove_animation_transform_curve_key(asset_path: str, curve_name: str, time: float,
                                          confirm: bool = False, dry_run: bool = False,
                                          save: bool = False) -> str:
    """Remove exact-time keys across native transform channels, retaining sparse data.

    Confirmed /Game sequence/stopped PIE, in-duration time, <=4096 keys per channel.
    Requires at least one matching channel; only matches are removed via native child
    controller APIs in one bracket. Returns impact count; dry-run/save supported.
    """
    return httpx.request("DELETE", f"{app.BASE_URL}/animations/curves/transform/key", json={
        "AssetPath": asset_path, "CurveName": curve_name, "Key": {"Time": time},
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_animation_transform_curve_flag(asset_path: str, curve_name: str, flag: str,
                                        enabled: bool = True, confirm: bool = False,
                                        dry_run: bool = False, save: bool = False) -> str:
    """Set native transform-curve Editable/DriveTrack/Disabled flag.

    Confirmed /Game sequence/stopped PIE, existing transform curve; native controller
    transaction/no-op/dry-run/save. DriveTrack affects native track workflows; no
    explicit bone-track bake/restoration requested. Channel inspection returns flags.
    """
    return httpx.patch(f"{app.BASE_URL}/animations/curves/transform/flag", json={
        "AssetPath": asset_path, "CurveName": curve_name, "Flag": flag,
        "bFlagEnabled": enabled, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def replace_animation_transform_curve_keys(asset_path: str, curve_name: str, keys: list[dict],
                                            confirm: bool = False, dry_run: bool = False,
                                            save: bool = False) -> str:
    """Replace all nine transform channel key sets with native complete transform keys.

    Rows: Time, Location {X,Y,Z}, Rotation {Pitch,Yaw,Roll}, Scale {X,Y,Z}.
    <=4096 strictly ordered in-duration finite/bounded keys; empty clears all keys.
    Confirmed /Game sequence/stopped PIE; native controller transaction/dry-run/save.
    Replaces custom rich tangents using native Euler/tangent conventions; no explicit bake.
    """
    return httpx.patch(f"{app.BASE_URL}/animations/curves/transform/keys", json={
        "AssetPath": asset_path, "CurveName": curve_name, "TransformKeys": keys,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def inspect_animation_transform_curve_keys(asset_path: str, curve_name: str,
                                            start: int = 0, count: int = 256,
                                            union_timeline: bool = False) -> str:
    """Read native or union transform-curve key timeline and transforms, count 1..256.

    <=36864 total source channel keys before native GetKeys. Default native GetKeys uses densest channel times. union_timeline includes all
    exact float key times and samples natively; finite-safe transforms returned.
    Rich interpolation metadata remains in per-channel inspector; no asset mutation.
    """
    return httpx.get(f"{app.BASE_URL}/animations/curves/transform/keys", params={
        "asset_path": asset_path, "curve_name": curve_name, "start": start, "count": count,
        "union_timeline": "true" if union_timeline else "false"
    }, timeout=180).text


@mcp.tool()
def move_animation_transform_curve_key(asset_path: str, curve_name: str, time: float,
                                        new_time: float, confirm: bool = False,
                                        dry_run: bool = False, save: bool = False) -> str:
    """Move exact-time keys in matching transform channels, preserving sparse/rich data.

    Confirmed /Game sequence/stopped PIE, duration-bounded times, <=4096 keys/channel.
    Preflights all matching-channel destination collisions; unaffected channels retained.
    Native controller bracket/no-op/dry-run/save; auto tangents follow engine behavior.
    """
    return httpx.patch(f"{app.BASE_URL}/animations/curves/transform/key/time", json={
        "AssetPath": asset_path, "CurveName": curve_name, "Key": {"Time": time},
        "NewTime": new_time, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def resample_animation_transform_curve(asset_path: str, curve_name: str, times: list[float],
                                        confirm: bool = False, dry_run: bool = False,
                                        save: bool = False) -> str:
    """Replace transform curve with native samples at 1..4096 strictly ordered times.

    Confirmed /Game sequence/stopped PIE, times within duration, bounded source keys.
    All samples prepared/validated before controller mutation. Replaces rich tangents
    and sparse timing; native Euler conversion can lose winding. No bone-track bake.
    Transaction/dry-run/save; dry-run still samples native source curves.
    """
    return httpx.post(f"{app.BASE_URL}/animations/curves/transform/resample", json={
        "AssetPath": asset_path, "CurveName": curve_name, "Times": times,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def resample_animation_float_curve(asset_path: str, curve_name: str, times: list[float],
                                    default_value: float = 0, confirm: bool = False,
                                    dry_run: bool = False, save: bool = False) -> str:
    """Replace float curve with linear native samples at 1..4096 ordered times.

    Confirmed /Game sequence/stopped PIE, <=4096 source keys, duration-bounded times.
    Native source samples validated before controller replacement; custom interpolation/
    tangents replaced by linear keys. Extrapolation retained. Transaction/dry-run/save.
    """
    return httpx.post(f"{app.BASE_URL}/animations/curves/resample", json={
        "AssetPath": asset_path, "CurveName": curve_name, "Times": times,
        "DefaultValue": default_value, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def inspect_animation_curve_diagnostics(asset_path: str) -> str:
    """Check source float/transform rich-curve structure, <=1024 channels/65536 keys.

    Reports invalid times/order, nonfinite data, weights/modes and duplicate names;
    <=128 issues with explicit completeness. Outside-duration keys flagged for authoring
    compatibility; structural status is not runtime/compression validity. No mutation.
    """
    return httpx.get(f"{app.BASE_URL}/animations/curves/diagnostics", params={
        "asset_path": asset_path
    }, timeout=180).text


@mcp.tool()
def list_animation_source_curves(asset_path: str, search: str = "", start: int = 0,
                                  count: int = 256) -> str:
    """List sorted source float/transform curve names, flags and channel key counts.

    Search <=128 characters, count 1..256, source catalog <=8192 curves. Transform
    key counts sum all nine channels, not merged times. No evaluation or asset mutation.
    """
    return httpx.get(f"{app.BASE_URL}/animations/curves/catalog", params={
        "asset_path": asset_path, "search": search, "start": start, "count": count
    }, timeout=180).text


@mcp.tool()
def remove_animation_float_curve_key_range(asset_path: str, curve_name: str,
                                            start_time: float, end_time: float,
                                            confirm: bool = False, dry_run: bool = False,
                                            save: bool = False) -> str:
    """Remove keys with inclusive times in ordered in-duration interval.

    Confirmed /Game sequence/stopped PIE, <=4096 source keys. Retains other rich key
    fields via native controller; no boundary samples inserted or outside-range shape
    guarantee. Reports removed/remaining counts; transaction/no-op/dry-run/save.
    """
    return httpx.request("DELETE", f"{app.BASE_URL}/animations/curves/key-range", json={
        "AssetPath": asset_path, "CurveName": curve_name, "RangeStart": start_time,
        "RangeEnd": end_time, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def remove_animation_transform_curve_key_range(asset_path: str, curve_name: str,
                                                start_time: float, end_time: float,
                                                confirm: bool = False, dry_run: bool = False,
                                                save: bool = False) -> str:
    """Remove inclusive-time keys across all nine transform channels.

    Confirmed /Game sequence/stopped PIE; <=4096 keys/channel and ordered in-duration
    range. All retained rich arrays prepared first; changed channels use one native
    controller bracket. Returns per-channel impact; no boundary samples/shape guarantee.
    """
    return httpx.request("DELETE", f"{app.BASE_URL}/animations/curves/transform/key-range", json={
        "AssetPath": asset_path, "CurveName": curve_name, "RangeStart": start_time,
        "RangeEnd": end_time, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def scale_animation_float_curve_time(asset_path: str, curve_name: str, factor: float,
                                      origin: float = 0, confirm: bool = False,
                                      dry_run: bool = False, save: bool = False) -> str:
    """Retime source float curve with native ScaleCurve around origin.

    Confirmed /Game sequence/stopped PIE, <=4096 keys; factor [0.001,1000]. Scratch
    native retiming rejects collisions/out-of-duration keys before controller mutation.
    Native tangent/weight/inverse-undo semantics apply. Other tracks/duration unchanged.
    """
    return httpx.patch(f"{app.BASE_URL}/animations/curves/time-scale", json={
        "AssetPath": asset_path, "CurveName": curve_name, "TimeOrigin": origin,
        "TimeFactor": factor, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_animation_float_curve_comment(asset_path: str, curve_name: str, comment: str,
                                       confirm: bool = False, dry_run: bool = False,
                                       save: bool = False) -> str:
    """Set native editor float-curve comment (<=4096 characters); empty clears.

    Confirmed /Game sequence/stopped PIE; existing float curve, controller transaction,
    no-op/dry-run/save. Rich inspector returns bounded comment with truncation.
    Does not change curve keys or runtime material/morph parameters.
    """
    return httpx.patch(f"{app.BASE_URL}/animations/curves/comment", json={
        "AssetPath": asset_path, "CurveName": curve_name, "Comment": comment,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def inspect_animation_float_curve_range(asset_path: str, curve_name: str) -> str:
    """Read native source float-curve time/value ranges, <=4096 keys.

    Empty/nonfinite source data returns unavailable/null ranges. Native value-range
    semantics apply; not exhaustive extrapolation or weighted-curve extrema proof.
    No curve evaluation at caller times, mutation or compressed animation inspection.
    """
    return httpx.get(f"{app.BASE_URL}/animations/curves/range", params={
        "asset_path": asset_path, "curve_name": curve_name
    }, timeout=180).text


@mcp.tool()
def offset_animation_float_curve_time(asset_path: str, curve_name: str, offset: float,
                                       confirm: bool = False, dry_run: bool = False,
                                       save: bool = False) -> str:
    """Shift all float curve key times, retaining rich fields through native setter.

    Confirmed /Game sequence/stopped PIE; <=4096 keys and bounded finite offset.
    Scratch float-time preflight rejects collisions/out-of-duration results. Native
    auto tangents apply; other tracks/duration/extrapolation unchanged. Dry-run/save.
    """
    return httpx.patch(f"{app.BASE_URL}/animations/curves/time-offset", json={
        "AssetPath": asset_path, "CurveName": curve_name, "TimeOffset": offset,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def offset_animation_transform_curve_time(asset_path: str, curve_name: str, offset: float,
                                           confirm: bool = False, dry_run: bool = False,
                                           save: bool = False) -> str:
    """Shift all nine source transform-channel key timelines with complete preflight.

    Confirmed /Game sequence/stopped PIE, <=4096 keys/channel and finite bounded offset.
    Rejects collisions/out-of-duration results before native setters; retains rich fields,
    sparse timing and extrapolation. Shared controller bracket/no-op/dry-run/save.
    """
    return httpx.patch(f"{app.BASE_URL}/animations/curves/transform/time-offset", json={
        "AssetPath": asset_path, "CurveName": curve_name, "TimeOffset": offset,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def widget_animations(widget_blueprint_path: str, operation: str = "Inspect", animation_path: str = "",
                      name: str = "", start_seconds: float = 0.0, end_seconds: float = 1.0,
                      expected_snapshot: str = "", allow_breaking_references: bool = False,
                      confirm: bool = False, dry_run: bool = True) -> str:
    """UMG Widget Blueprint animations: Inspect/Create/Rename/Delete/SetRange.
    Mutations need confirm and the exact `snapshot` string from a prior Inspect. Create/SetRange use
    start/end seconds (0<=start<end<=3600). Rename replaces graph variable references. Delete of an
    animation referenced in graphs needs allow_breaking_references. No compile/save; tracks not authored. Unverified.
    """
    return _ext("/widgets/animations", {"Operation": operation, "AssetPath": widget_blueprint_path,
        "TargetPath": animation_path, "Name": name, "Numbers": [start_seconds, end_seconds],
        "ExpectedSnapshot": expected_snapshot, "bAllow": allow_breaking_references,
        "bConfirm": confirm, "bDryRun": dry_run})


# Tools listed to clients. Each picks one of the functions above with its variant argument.
edit_animation_data = merged_tool("edit_animation_data", {
    "edit_animation_asset": edit_animation_asset,
    "edit_animation_curve": edit_animation_curve,
})
edit_animation_curve_key = merged_tool("edit_animation_curve_key", {
    "edit_animation_rich_float_key": edit_animation_rich_float_key,
    "move_animation_rich_float_key": move_animation_rich_float_key,
})
