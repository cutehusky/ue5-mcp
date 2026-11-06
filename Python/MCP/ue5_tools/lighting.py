"""Lights, sky, fog, clouds, post-process, reflections and decals."""
import httpx

from . import app
from .app import merged_tool
from .app import mcp


@mcp.tool()
def inspect_post_process_volume(actor_path: str) -> str:
    """Read authored enabled/unbound/priority/radius/weight and up to64 blendable references.
    Not full settings overrides or camera/final-render evaluation; no load/save/mutation.
    """
    return httpx.post(f"{app.BASE_URL}/volumes/post-process/inspect", json={"ActorPath": actor_path}, timeout=60).text


@mcp.tool()
def set_post_process_volume_control(actor_path: str, field: str, expected_value: float,
                                      scalar_value: float = 0, bool_value: bool = False,
                                      confirm: bool = False, dry_run: bool = False) -> str:
    """Set Priority(+/-1e6), BlendRadius(0..1e6), BlendWeight(0..1), Enabled/Unbound(bool).
    Exact inspected current control guard (bool0/1), native float, transaction/editor
    notification/readback/dry-run/no-op/no save. Final renderer behavior unverified.
    """
    return httpx.post(f"{app.BASE_URL}/volumes/post-process/control", json={
        "ActorPath": actor_path, "FieldName": field, "ExpectedScalarValue": expected_value,
        "ScalarValue": scalar_value, "bBoolValue": bool_value, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_post_process_blendable_weight(actor_path: str, expected_entry_count: int, entry_index: int,
                                       expected_object_path: str, expected_weight: float, weight: float,
                                       confirm: bool = False, dry_run: bool = False) -> str:
    """Set existing blendable weight0..1 with inspected count/index/object/weight guards.
    Empty object path means null; retains references/order. Native float/transaction/
    Settings notification/dry-run/no-op/no load/save; renderer/undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/volumes/post-process/blendable-weight", json={
        "ActorPath": actor_path, "ExpectedEntryCount": expected_entry_count, "EntryIndex": entry_index,
        "ExpectedObjectPath": expected_object_path, "ExpectedScalarValue": expected_weight,
        "ScalarValue": weight, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def remove_post_process_blendable(actor_path: str, expected_entry_count: int, entry_index: int,
                                   expected_object_path: str, expected_weight: float,
                                   confirm: bool = False, dry_run: bool = False) -> str:
    """Remove one inspected blendable with count/index/object/weight guards, max64 entries.
    Empty path means null; remaining order/weights/references retained and checked.
    Referenced object not destroyed. Transaction/notification/dry-run/no save; unverified.
    """
    return httpx.post(f"{app.BASE_URL}/volumes/post-process/blendable-remove", json={
        "ActorPath": actor_path, "ExpectedEntryCount": expected_entry_count, "EntryIndex": entry_index,
        "ExpectedObjectPath": expected_object_path, "ExpectedScalarValue": expected_weight,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def add_post_process_blendable(actor_path: str, expected_entry_count: int, object_path: str,
                                weight: float = 1, confirm: bool = False, dry_run: bool = False) -> str:
    """Append unique loaded persistent blendable-interface object, inspected count<64/weight0..1.
    Existing table preserved/read back; count is not full content revision guard.
    Transaction/notification/dry-run/no load/save; renderer/undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/volumes/post-process/blendable-add", json={
        "ActorPath": actor_path, "ExpectedEntryCount": expected_entry_count, "ObjectPath": object_path,
        "ScalarValue": weight, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_post_process_setting_fields(actor_path: str, field_start: int = 0, field_count: int = 64) -> str:
    """Page native settings schema/override flags1..128 fields; scalar/bool/object/color/vector values.
    Integers decimal strings, composite values schema only; reflection order version-dependent.
    No recursive export/load/render evaluation/save/mutation.
    """
    return httpx.post(f"{app.BASE_URL}/volumes/post-process/fields", json={
        "ActorPath": actor_path, "EntryStart": field_start, "EntryCount": field_count
    }, timeout=60).text


@mcp.tool()
def set_post_process_setting_override(actor_path: str, field: str, expected_enabled: bool,
                                        enabled: bool, confirm: bool = False, dry_run: bool = False) -> str:
    """Set native setting's override flag; use field name without bOverride_ prefix.
    Exact inspected current flag guard; adapter retains stored setting value.
    Transaction/Settings notification/readback/dry-run/no-op/no save; unverified.
    """
    return httpx.post(f"{app.BASE_URL}/volumes/post-process/override", json={
        "ActorPath": actor_path, "FieldName": field, "bExpectedBoolValue": expected_enabled,
        "bBoolValue": enabled, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


def set_post_process_setting_scalar(actor_path: str, field: str, expected_value: float,
                                      expected_override: bool, value: float,
                                      confirm: bool = False, dry_run: bool = False) -> str:
    """Set native floating setting with exact current value/override guards; override retained.
    Finite +/-1e9/native float precision and ClampMin/ClampMax checks, no cross-field validation.
    Transaction/Settings notification/readback/dry-run/no-op/no save; renderer effects unverified.
    """
    return httpx.post(f"{app.BASE_URL}/volumes/post-process/scalar", json={
        "ActorPath": actor_path, "FieldName": field, "ExpectedScalarValue": expected_value,
        "bExpectedBoolValue": expected_override, "ScalarValue": value,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


def set_post_process_setting_bool(actor_path: str, field: str, expected_value: bool,
                                    expected_override: bool, value: bool,
                                    confirm: bool = False, dry_run: bool = False) -> str:
    """Edit native boolean setting with inspected value/override guards; override retained.
    Supports native b-prefixed field/override naming. Transaction/notification/readback/
    dry-run/no-op/no save; renderer/callbacks/undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/volumes/post-process/bool", json={
        "ActorPath": actor_path, "FieldName": field, "bExpectedBoolValue": expected_value,
        "bExpectedOverride": expected_override, "bBoolValue": value,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


def set_post_process_setting_enum(actor_path: str, field: str, expected_name: str,
                                    expected_override: bool, name: str,
                                    confirm: bool = False, dry_run: bool = False) -> str:
    """Set native enum choice with inspected short current name/override guards.
    Visible nonsentinel choice required; override retained. Transaction/notification/
    dry-run/no-op/no save; platform/renderer/undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/volumes/post-process/enum", json={
        "ActorPath": actor_path, "FieldName": field, "ExpectedEnumValue": expected_name,
        "bExpectedOverride": expected_override, "EnumValue": name,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_post_process_setting_object(actor_path: str, field: str, expected_object_path: str,
                                      expected_override: bool, object_path: str,
                                      confirm: bool = False, dry_run: bool = False) -> str:
    """Assign loaded compatible persistent hard object reference, or empty to clear if allowed.
    Exact inspected current object/override guards; override retained. No referenced
    object mutation/load/save. Transaction/notification/dry-run/no-op; unverified.
    """
    return httpx.post(f"{app.BASE_URL}/volumes/post-process/object", json={
        "ActorPath": actor_path, "FieldName": field, "ExpectedObjectPath": expected_object_path,
        "bExpectedOverride": expected_override, "ObjectPath": object_path,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


def set_post_process_setting_vector(actor_path: str, field: str, expected_channels: list[float],
                                      expected_override: bool, channels: list[float],
                                      confirm: bool = False, dry_run: bool = False) -> str:
    """Set native LinearColor RGBA or Vector4 XYZW with full current-channel/override guards.
    Four finite channels+/-1e6, native precision/clamp metadata, no sRGB conversion.
    Override retained; transaction/notification/dry-run/no-op/no save; unverified.
    """
    if len(channels) != 4 or len(expected_channels) != 4:
        raise ValueError("Expected/new values require four channels")
    return httpx.post(f"{app.BASE_URL}/volumes/post-process/vector", json={
        "ActorPath": actor_path, "FieldName": field, "ExpectedChannels": expected_channels,
        "bExpectedOverride": expected_override, "Channels": channels,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


def set_post_process_setting_integer(actor_path: str, field: str, expected_value: int,
                                       expected_override: bool, value: int,
                                       confirm: bool = False, dry_run: bool = False) -> str:
    """Set native int32 non-enum setting with inspected current value/override guards.
    Exact integer/native clamp metadata; override retained. Transaction/notification/
    dry-run/no-op/no save; cross-field/render effects/undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/volumes/post-process/integer", json={
        "ActorPath": actor_path, "FieldName": field, "ExpectedScalarValue": expected_value,
        "bExpectedBoolValue": expected_override, "ScalarValue": value,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


def reset_post_process_setting_scalar(actor_path: str, field: str, expected_value: float,
                                        expected_override: bool, confirm: bool = False,
                                        dry_run: bool = False) -> str:
    """Restore native FPostProcessSettings constructor scalar default, retaining override.
    Exact current value/override guards and existing scalar setter checks/transaction.
    Not project/camera/subclass defaults. Dry-run/no-op/no save; unverified.
    """
    return httpx.post(f"{app.BASE_URL}/volumes/post-process/scalar/reset", json={
        "ActorPath": actor_path, "FieldName": field, "ExpectedScalarValue": expected_value,
        "bExpectedBoolValue": expected_override, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


def reset_post_process_setting_integer(actor_path: str, field: str, expected_value: int,
                                        expected_override: bool, confirm: bool = False,
                                        dry_run: bool = False) -> str:
    """Restore native FPostProcessSettings constructor integer default, retaining override.
    Exact current value/override guards and existing signed-int32 setter checks/transaction.
    Not project/camera/subclass defaults. Dry-run/no-op/no save; unverified.
    """
    return httpx.post(f"{app.BASE_URL}/volumes/post-process/integer/reset", json={
        "ActorPath": actor_path, "FieldName": field, "ExpectedScalarValue": expected_value,
        "bExpectedBoolValue": expected_override, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


def reset_post_process_setting_bool(actor_path: str, field: str, expected_value: bool,
                                     expected_override: bool, confirm: bool = False,
                                     dry_run: bool = False) -> str:
    """Restore native boolean setting default while retaining current override state.
    Exact inspected value/override guards; native constructor, not project/subclass defaults.
    Existing boolean setter transaction/notification/dry-run/no-op/no save; unverified.
    """
    return httpx.post(f"{app.BASE_URL}/volumes/post-process/bool/reset", json={
        "ActorPath": actor_path, "FieldName": field, "bExpectedBoolValue": expected_value,
        "bExpectedOverride": expected_override, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


def reset_post_process_setting_vector(actor_path: str, field: str, expected_channels: list[float],
                                       expected_override: bool, confirm: bool = False,
                                       dry_run: bool = False) -> str:
    """Restore native LinearColor RGBA/Vector4 XYZW defaults, preserving override.
    Four inspected channel/current override guards; existing vector setter checks.
    Native constructor, not project/subclass defaults. Transaction/dry-run/no save; unverified.
    """
    if len(expected_channels) != 4:
        raise ValueError("Expected value requires four channels")
    return httpx.post(f"{app.BASE_URL}/volumes/post-process/vector/reset", json={
        "ActorPath": actor_path, "FieldName": field, "ExpectedChannels": expected_channels,
        "bExpectedOverride": expected_override, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


def reset_post_process_setting_enum(actor_path: str, field: str, expected_name: str,
                                     expected_override: bool, confirm: bool = False,
                                     dry_run: bool = False) -> str:
    """Restore native enum constructor default, preserving override/current-name guards.
    Uses existing enum setter eligibility/transaction; not project/subclass defaults.
    Dry-run/no-op/no save; native hidden defaults may be rejected; unverified.
    """
    return httpx.post(f"{app.BASE_URL}/volumes/post-process/enum/reset", json={
        "ActorPath": actor_path, "FieldName": field, "ExpectedEnumValue": expected_name,
        "bExpectedOverride": expected_override, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def reset_post_process_setting_object(actor_path: str, field: str, expected_object_path: str,
                                       expected_override: bool, confirm: bool = False,
                                       dry_run: bool = False) -> str:
    """Restore native hard object-reference default with inspected object/override guards.
    Uses existing compatibility/NoClear checks, retains override. No load/referenced-object
    mutation/save; native constructor defaults, transaction/dry-run/no-op; unverified.
    """
    return httpx.post(f"{app.BASE_URL}/volumes/post-process/object/reset", json={
        "ActorPath": actor_path, "FieldName": field, "ExpectedObjectPath": expected_object_path,
        "bExpectedOverride": expected_override, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_world_reflection_captures() -> str:
    """Read up to128 current-world reflection captures and authored source/brightness/offset.
    Influence bounds/build GUID do not prove capture freshness or render readiness.
    No recapture/upload/build/load/save/mutation; nonfinite channels null.
    """
    return httpx.post(f"{app.BASE_URL}/reflection-captures/inspect", json={}, timeout=60).text


@mcp.tool()
def set_reflection_capture_scalar(actor_path: str, component_path: str, field: str,
                                   expected_value: float, value: float,
                                   confirm: bool = False, dry_run: bool = False) -> str:
    """Set Brightness/SourceCubemapAngle or shape InfluenceRadius/BoxTransitionDistance/InfluenceRadiusScale.
    Exact inspected value guard, native float0..1e6(angle0..360), transaction/notification.
    Angle queues native recapture; no explicit processing/save. Dry-run/no-op; unverified.
    """
    return httpx.post(f"{app.BASE_URL}/reflection-captures/scalar", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "FieldName": field,
        "ExpectedValue": expected_value, "Value": value, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_reflection_capture_offset(actor_path: str, component_path: str, expected_offset: list[float],
                                   offset: list[float], confirm: bool = False, dry_run: bool = False) -> str:
    """Set native world-space capture offset with inspected vector guard, XYZ+/-1e9.
    Transaction/property notification/readback/dry-run/no-op, no explicit recapture/save.
    Native callback/render freshness/undo/persistence unverified.
    """
    if len(offset) != 3 or len(expected_offset) != 3:
        raise ValueError("Expected/new offset requires XYZ triples")
    return httpx.post(f"{app.BASE_URL}/reflection-captures/offset", json={
        "ActorPath": actor_path, "ComponentPath": component_path,
        "ExpectedOffset": dict(zip(("X", "Y", "Z"), expected_offset)),
        "Offset": dict(zip(("X", "Y", "Z"), offset)), "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_reflection_capture_source(actor_path: str, component_path: str, expected_source_type: int,
                                   expected_cubemap_path: str, source_type: str, cubemap_path: str = "",
                                   confirm: bool = False, dry_run: bool = False) -> str:
    """Set CapturedScene/SpecifiedCubemap and cubemap with inspected current pair guards.
    SpecifiedCubemap needs loaded persistent cube; empty clears for CapturedScene.
    Native notification queues recapture/GUID change; transaction/dry-run/no-op,
    no explicit processing/load/save. Capture readiness/undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/reflection-captures/source", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ExpectedSourceType": expected_source_type,
        "ExpectedCubemapPath": expected_cubemap_path, "SourceType": source_type, "CubemapPath": cubemap_path,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def queue_reflection_capture_recapture(actor_path: str, component_path: str, expected_build_data_id: str,
                                        confirm: bool = False, dry_run: bool = False) -> str:
    """Queue native recapture for registered visible capture with inspected build GUID guard.
    Generates new GUID; editor may process later after shader/texture readiness.
    No synchronous processing/completion proof/save; transaction/dry-run, resource undo unverified.
    """
    return httpx.post(f"{app.BASE_URL}/reflection-captures/queue-recapture", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ExpectedBuildDataId": expected_build_data_id,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_reflection_capture_visible(actor_path: str, component_path: str, expected_visible: bool,
                                    visible: bool, confirm: bool = False, dry_run: bool = False) -> str:
    """Set native capture visibility with inspected current flag guard; no child propagation.
    Transaction/render-state notification/dry-run/no-op, no explicit recapture/save.
    Renderer contribution/queue completion/undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/reflection-captures/visible", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "bExpectedVisible": expected_visible,
        "bVisible": visible, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def create_reflection_capture(shape: str, name: str, location: list[float],
                                confirm: bool = False, dry_run: bool = False) -> str:
    """Create native Sphere/Box capture in ordinary persistent map with native defaults.
    Unique name1..128 letters/digits/underscore, XYZ location+/-1e9, identity rotation/unit scale.
    Registration may queue capture work; transaction/dry-run/no explicit processing/save; unverified.
    """
    if len(location) != 3:
        raise ValueError("Location requires XYZ triple")
    return httpx.post(f"{app.BASE_URL}/reflection-captures/create", json={
        "Shape": shape, "Name": name, "Location": dict(zip(("X", "Y", "Z"), location)),
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def delete_reflection_capture(actor_path: str, component_path: str, expected_build_data_id: str,
                                confirm: bool = False, dry_run: bool = False) -> str:
    """Delete persistent-level capture actor with inspected component/build GUID guards.
    Ordinary map/no attached actors required. Native transaction/destruction/dry-run,
    no render sync/save; capture queues/resources/references/undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/reflection-captures/delete", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ExpectedBuildDataId": expected_build_data_id,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_world_planar_reflections() -> str:
    """Read up to128 native planar reflection components and authored quality/fade controls.
    Distinct from abstract legacy plane capture actors; renderer capability not proven.
    No capture/update/load/save/mutation; nonfinite controls null.
    """
    return httpx.post(f"{app.BASE_URL}/planar-reflections/inspect", json={}, timeout=60).text


def set_planar_reflection_scalar(actor_path: str, component_path: str, field: str,
                                  expected_value: float, value: float,
                                  confirm: bool = False, dry_run: bool = False) -> str:
    """Set NormalDistortionStrength/PrefilterRoughness/PrefilterRoughnessDistance/ExtraFOV,
    DistanceFromPlaneFadeoutStart/End or AngleFromPlaneFadeStart/End.
    Exact inspected value guard; ordered fades, angles/FOV0..90, roughness0..1,
    others0..1e6. Transaction/notification/dry-run/no-op/no save; renderer/undo unverified.
    """
    return httpx.post(f"{app.BASE_URL}/planar-reflections/scalar", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "FieldName": field,
        "ExpectedValue": expected_value, "Value": value, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_planar_reflection_screen_percentage(actor_path: str, component_path: str,
                                             expected_value: int, value: int,
                                             confirm: bool = False, dry_run: bool = False) -> str:
    """Set integer planar screen percentage25..100 with inspected current value guard.
    Native editor notification may rebuild render resources. Transaction/dry-run/no-op/
    no capture processing/save; visual/GPU/undo/persistence behavior unverified.
    """
    return httpx.post(f"{app.BASE_URL}/planar-reflections/screen-percentage", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ExpectedValue": expected_value,
        "Value": value, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


def set_planar_reflection_bool(actor_path: str, component_path: str, field: str,
                                expected_value: bool, value: bool,
                                confirm: bool = False, dry_run: bool = False) -> str:
    """Set bRenderSceneTwoSided/bShowPreviewPlane with inspected current flag guard.
    Native property notification/transaction/readback/dry-run/no-op/no save.
    Renderer/project capability/preview/undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/planar-reflections/bool", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "FieldName": field,
        "bExpectedVisible": expected_value, "bVisible": value, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def create_planar_reflection(name: str, location: list[float], confirm: bool = False,
                              dry_run: bool = False) -> str:
    """Create native planar reflection actor in ordinary persistent map with native defaults.
    Unique name1..128 letters/digits/underscore, XYZ+/-1e9, identity rotation/unit scale.
    Does not configure project clip-plane/render support. Transaction/dry-run/no save; unverified.
    """
    if len(location) != 3:
        raise ValueError("Location requires XYZ triple")
    return httpx.post(f"{app.BASE_URL}/planar-reflections/create", json={
        "Name": name, "Location": dict(zip(("X", "Y", "Z"), location)),
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def delete_planar_reflection(actor_path: str, component_path: str, confirm: bool = False,
                              dry_run: bool = False) -> str:
    """Delete native planar actor with exact inspected actor/component identities.
    Ordinary persistent map/no attached actors, transaction/dry-run/no save.
    Render resources/external references/callbacks/undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/planar-reflections/delete", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_planar_reflection_visible(actor_path: str, component_path: str, expected_visible: bool,
                                   visible: bool, confirm: bool = False, dry_run: bool = False) -> str:
    """Set planar component visibility with inspected current flag guard; children unchanged.
    Native transaction/render notification/readback/dry-run/no-op/no save.
    Renderer capability/resource lifecycle/undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/planar-reflections/visible", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "bExpectedVisible": expected_visible,
        "bVisible": visible, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_planar_reflection_transform(actor_path: str, component_path: str,
                                     expected_location: list[float], expected_rotation: list[float],
                                     expected_scale: list[float], location: list[float],
                                     rotation: list[float], scale: list[float],
                                     confirm: bool = False, dry_run: bool = False) -> str:
    """Set unattached planar component world transform; inspected transform guard.
    XYZ position+/-1e9, normalized quaternion XYZW, nonzero scale abs<=1000.
    Native no-sweep teleport/preview update, children follow; transaction/dry-run/no save; unverified.
    """
    def transform(p, q, s):
        if len(p) != 3 or len(q) != 4 or len(s) != 3:
            raise ValueError("Transform requires XYZ position/scale and XYZW quaternion")
        return {"Translation": dict(zip(("X", "Y", "Z"), p)),
                "Rotation": dict(zip(("X", "Y", "Z", "W"), q)),
                "Scale3D": dict(zip(("X", "Y", "Z"), s))}
    return httpx.post(f"{app.BASE_URL}/planar-reflections/transform", json={
        "ActorPath": actor_path, "ComponentPath": component_path,
        "ExpectedTransform": transform(expected_location, expected_rotation, expected_scale),
        "Transform": transform(location, rotation, scale), "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_reflection_capture_transform(actor_path: str, component_path: str,
                                     expected_location: list[float], expected_rotation: list[float],
                                     expected_scale: list[float], location: list[float],
                                     rotation: list[float], scale: list[float],
                                     confirm: bool = False, dry_run: bool = False) -> str:
    """Set unattached capture component world transform; inspected transform guard.
    XYZ position+/-1e9, normalized quaternion XYZW, nonzero scale abs<=1000.
    Native no-sweep teleport/preview update/recapture queue when visible, children follow; transaction/dry-run/no save; unverified.
    """
    def transform(p, q, s):
        if len(p) != 3 or len(q) != 4 or len(s) != 3:
            raise ValueError("Transform requires XYZ position/scale and XYZW quaternion")
        return {"Translation": dict(zip(("X", "Y", "Z"), p)),
                "Rotation": dict(zip(("X", "Y", "Z", "W"), q)),
                "Scale3D": dict(zip(("X", "Y", "Z"), s))}
    return httpx.post(f"{app.BASE_URL}/reflection-captures/transform", json={
        "ActorPath": actor_path, "ComponentPath": component_path,
        "ExpectedTransform": transform(expected_location, expected_rotation, expected_scale),
        "Transform": transform(location, rotation, scale), "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_world_light_components() -> str:
    """Read up to128 current-world light components, identities/mobility/visibility/shadows/color/intensity.
    Intensity units class-dependent; sky lights excluded. No build/render sync/load/save/mutation.
    Authored settings do not prove rendered contribution; nonfinite channels null.
    """
    return httpx.post(f"{app.BASE_URL}/lighting/components/inspect", json={}, timeout=60).text


def set_light_scalar(actor_path: str, component_path: str, field: str, expected_value: float,
                       value: float, confirm: bool = False, dry_run: bool = False) -> str:
    """Edit Intensity0..1e9 (local EV units allow -100..100), Temperature1000..40000, local AttenuationRadius,
    point SourceRadius/SoftSourceRadius/SourceLength0..1e6, LightFalloffExponent(0..1000 positive),
    or spot InnerConeAngle/OuterConeAngle.
    Rect SourceWidth/SourceHeight0..100000, BarnDoorAngle0..90/BarnDoorLength0..1e6;
    directional LightSourceAngle/LightSourceSoftAngle0..90.
    IndirectLightingIntensity/VolumetricScatteringIntensity0..1000, ShadowResolutionScale0..64,
    ShadowBias/ShadowSlopeBias/ShadowSharpen0..1; IESBrightnessScale/DisabledBrightness0..1000,
    LightFunctionFadeDistance0..1e6; ContactShadowLength0..1(screen) or0..1e6(world),
    ContactShadowCastingIntensity/ContactShadowNonCastingIntensity0..1;
    MaxDrawDistance/MaxDistanceFadeRange0..1e6 (zero max distance=unlimited).
    Type-specific guards,0<=inner<=outer<90; exact inspected current value required.
    Intensity units configuration-dependent; temperature enable unchanged. Native editor
    notification/transaction/readback/dry-run/no-op/no build/save; renderer/undo unverified.
    """
    return httpx.post(f"{app.BASE_URL}/lighting/scalar", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "FieldName": field,
        "ExpectedValue": expected_value, "Value": value, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


def set_light_bool(actor_path: str, component_path: str, field: str, expected_value: bool,
                     value: bool, confirm: bool = False, dry_run: bool = False) -> str:
    """Edit CastShadows/CastStaticShadows/CastDynamicShadows/bCastVolumetricShadow/
    CastTranslucentShadows/bUseTemperature, directional bAtmosphereSunLight,
    point/spot bUseInverseSquaredFalloff, bUseIESBrightness or ContactShadowLengthInWS
    with current flag guard.
    Enabling IES brightness requires an assigned IES profile.
    Intensity/temperature/color retained; native editor notification/transaction/
    readback/dry-run/no-op/no build/save; renderer/callbacks/undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/lighting/bool", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "FieldName": field,
        "bExpectedValue": expected_value, "bValue": value, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_light_stored_color(actor_path: str, component_path: str, expected_color: list[int],
                            color: list[int], confirm: bool = False, dry_run: bool = False) -> str:
    """Set native stored RGBA bytes0..255 with exact stored_color_rgba inspection guard.
    No linear/sRGB conversion; intensity/temperature retained. Transaction/editor notification/
    readback/dry-run/no-op/no build/save; color/render/undo/persistence unverified.
    """
    if len(color) != 4 or len(expected_color) != 4:
        raise ValueError("Expected/new color requires RGBA quadruples")
    return httpx.post(f"{app.BASE_URL}/lighting/color", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ExpectedColor": expected_color,
        "Color": color, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_world_sky_lights() -> str:
    """Read up to128 native sky lights and authored source/capture/hemisphere settings.
    Real-time flag not capture freshness/platform/render proof. No recapture/build/
    render sync/load/save/mutation; nonfinite channels null.
    """
    return httpx.post(f"{app.BASE_URL}/lighting/sky/inspect", json={}, timeout=60).text


def set_sky_light_scalar(actor_path: str, component_path: str, field: str, expected_value: float,
                           value: float, confirm: bool = False, dry_run: bool = False) -> str:
    """Edit sky Intensity/SkyDistanceThreshold0..1e9, SourceCubemapAngle0..360,
    or IndirectLightingIntensity/VolumetricScatteringIntensity0..1000.
    Exact inspected current value guard; transaction/native notification may queue capture.
    No explicit queue processing/build/save, dry-run/no-op; renderer/undo unverified.
    """
    return httpx.post(f"{app.BASE_URL}/lighting/sky/scalar", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "FieldName": field,
        "ExpectedValue": expected_value, "Value": value, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


def set_sky_light_bool(actor_path: str, component_path: str, field: str, expected_value: bool,
                         value: bool, confirm: bool = False, dry_run: bool = False) -> str:
    """Edit bRealTimeCapture/bLowerHemisphereIsBlack with inspected current flag guard.
    Native notification may queue capture/resources; real-time mode adds recurring GPU work
    when supported. Transaction/dry-run/no-op/no build/save; renderer/undo unverified.
    """
    return httpx.post(f"{app.BASE_URL}/lighting/sky/bool", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "FieldName": field,
        "bExpectedValue": expected_value, "bValue": value, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_sky_light_source(actor_path: str, component_path: str, expected_source_type: int,
                           expected_cubemap_path: str, source_type: str, cubemap_path: str = "",
                           confirm: bool = False, dry_run: bool = False) -> str:
    """Set CapturedScene/SpecifiedCubemap pair with inspected source/cubemap guards.
    Specified source requires loaded persistent cube; optional/empty for captured scene.
    Transaction/native notification may queue capture, dry-run/no-op/no load/build/save; unverified.
    """
    return httpx.post(f"{app.BASE_URL}/lighting/sky/source", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ExpectedSourceType": expected_source_type,
        "ExpectedCubemapPath": expected_cubemap_path, "SourceType": source_type, "CubemapPath": cubemap_path,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_light_visible(actor_path: str, component_path: str, expected_visible: bool,
                        visible: bool, confirm: bool = False, dry_run: bool = False) -> str:
    """Set native ordinary/sky light visibility with current flag guard, no child propagation.
    Does not remove already baked lighting. Transaction/readback/dry-run/no-op/no save;
    renderer/callbacks/undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/lighting/visible", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "bExpectedValue": expected_visible,
        "bValue": visible, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def create_light_actor(light_type: str, name: str, location: list[float],
                         confirm: bool = False, dry_run: bool = False) -> str:
    """Create native Point/Spot/Rect/Directional/Sky light in ordinary persistent map.
    Unique name1..128 letters/digits/underscore, XYZ+/-1e9, native mobility/settings defaults.
    Registration may queue sky capture/render work; transaction/dry-run/no build/save; unverified.
    """
    if len(location) != 3:
        raise ValueError("Location requires XYZ triple")
    return httpx.post(f"{app.BASE_URL}/lighting/create", json={
        "LightType": light_type, "Name": name, "Location": dict(zip(("X", "Y", "Z"), location)),
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def delete_light_actor(actor_path: str, component_path: str, expected_class_path: str,
                         confirm: bool = False, dry_run: bool = False) -> str:
    """Delete native ordinary/sky light actor with inspected actor class/component guards.
    Ordinary persistent map/no attached actors. Transaction/dry-run/no build/save;
    baked lighting/render teardown/references/undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/lighting/delete", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ExpectedClassPath": expected_class_path,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_sky_light_hemisphere_color(actor_path: str, component_path: str,
                                     expected_color: list[float], color: list[float],
                                     confirm: bool = False, dry_run: bool = False) -> str:
    """Set lower-hemisphere linear RGBA0..1000 with full inspected current-color guard.
    Native float/no sRGB conversion, hemisphere enable mode retained. Transaction/
    notification/dry-run/no-op/no build/save; capture/renderer/undo unverified.
    """
    if len(color) != 4 or len(expected_color) != 4:
        raise ValueError("Expected/new color requires linear RGBA quadruples")
    return httpx.post(f"{app.BASE_URL}/lighting/sky/hemisphere-color", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ExpectedLinearColor": expected_color,
        "LinearColor": color, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_light_transform(actor_path: str, component_path: str,
                                     expected_location: list[float], expected_rotation: list[float],
                                     expected_scale: list[float], location: list[float],
                                     rotation: list[float], scale: list[float],
                                     confirm: bool = False, dry_run: bool = False) -> str:
    """Set unattached ordinary/sky light component world transform; inspected transform guard.
    XYZ position+/-1e9, normalized quaternion XYZW, nonzero scale abs<=1000.
    Native no-sweep teleport/transform notification, children follow; transaction/dry-run/no save; unverified.
    """
    def transform(p, q, s):
        if len(p) != 3 or len(q) != 4 or len(s) != 3:
            raise ValueError("Transform requires XYZ position/scale and XYZW quaternion")
        return {"Translation": dict(zip(("X", "Y", "Z"), p)),
                "Rotation": dict(zip(("X", "Y", "Z", "W"), q)),
                "Scale3D": dict(zip(("X", "Y", "Z"), s))}
    return httpx.post(f"{app.BASE_URL}/lighting/transform", json={
        "ActorPath": actor_path, "ComponentPath": component_path,
        "ExpectedTransform": transform(expected_location, expected_rotation, expected_scale),
        "Transform": transform(location, rotation, scale), "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_light_mobility(actor_path: str, component_path: str, expected_mobility: int,
                         mobility: str, confirm: bool = False, dry_run: bool = False) -> str:
    """Set Static/Stationary/Movable with inspected native ordinal0/1/2 guard.
    Parent/children must be detached to isolate hierarchy changes. Native setter/
    transaction/readback/dry-run/no-op/no build/save; baked/render/undo effects unverified.
    """
    return httpx.post(f"{app.BASE_URL}/lighting/mobility", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ExpectedMobility": expected_mobility,
        "Mobility": mobility, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_directional_light_atmosphere_index(actor_path: str, component_path: str, expected_index: int,
                                            index: int, confirm: bool = False, dry_run: bool = False) -> str:
    """Set native atmosphere sun slot0/1 with inspected current index guard.
    Atmosphere-enable flag retained, no competing-light conflict resolution.
    Transaction/editor notification/dry-run/no-op/no build/save; renderer/undo unverified.
    """
    return httpx.post(f"{app.BASE_URL}/lighting/atmosphere-index", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ExpectedValue": expected_index,
        "Value": index, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_local_light_units_intensity(actor_path: str, component_path: str, expected_units: int,
                                      expected_intensity: float, units: str, intensity: float,
                                      confirm: bool = False, dry_run: bool = False) -> str:
    """Set Unitless/Candelas/Lumens/EV/Nits plus explicit intensity with current pair guards.
    Intensity0..1e9, EV-100..100. No brightness-preserving conversion implied.
    Transaction/editor notification/readback/dry-run/no-op/no build/save; renderer/undo unverified.
    """
    return httpx.post(f"{app.BASE_URL}/lighting/units-intensity", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ExpectedUnits": expected_units,
        "ExpectedValue": expected_intensity, "Units": units, "Value": intensity,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_light_channels(actor_path: str, component_path: str, expected_channels: list[int],
                         channels: list[int], confirm: bool = False, dry_run: bool = False) -> str:
    """Set channel0/1/2 flags (three0/1 values) with full inspected current-channel guard.
    All-off allowed; primitive channels unchanged. Native transaction/notification/
    readback/dry-run/no-op/no build/save; renderer/material/mobility support unverified.
    """
    if len(channels) != 3 or len(expected_channels) != 3:
        raise ValueError("Expected/new channels require three0/1 flags")
    return httpx.post(f"{app.BASE_URL}/lighting/channels", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ExpectedChannels": expected_channels,
        "Channels": channels, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def queue_sky_light_capture(actor_path: str, component_path: str, expected_source_type: int,
                              expected_cubemap_path: str, expected_real_time: bool,
                              confirm: bool = False, dry_run: bool = False) -> str:
    """Invoke native dirty-capture request with inspected source/cube/real-time guards.
    Registered visible affecting-world non-real-time sky required; native static policy may skip.
    Invocation is not queue acceptance/completion proof. No synchronous capture/save;
    transient queue/resource work not undoable; unverified.
    """
    return httpx.post(f"{app.BASE_URL}/lighting/sky/queue-capture", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ExpectedSourceType": expected_source_type,
        "ExpectedCubemapPath": expected_cubemap_path, "bExpectedValue": expected_real_time,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_light_function_scale(actor_path: str, component_path: str, expected_scale: list[float],
                               scale: list[float], confirm: bool = False, dry_run: bool = False) -> str:
    """Set native projection XYZ scale with full inspected vector guard; material retained.
    Finite requested abs1e-6..1e6, X/Y perpendicular/Z along light direction.
    Transaction/notification/readback/dry-run/no-op/no build/save; render/undo unverified.
    """
    if len(scale) != 3 or len(expected_scale) != 3:
        raise ValueError("Expected/new scale requires XYZ triples")
    return httpx.post(f"{app.BASE_URL}/lighting/function-scale", json={
        "ActorPath": actor_path, "ComponentPath": component_path,
        "ExpectedScale": dict(zip(("X", "Y", "Z"), expected_scale)),
        "Scale": dict(zip(("X", "Y", "Z"), scale)), "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_world_height_fog() -> str:
    """Read up to128 native height-fog components and authored first-layer/volumetric controls.
    Second layer/colors/local fog not covered; renderer/scalability contribution not proven.
    No render update/load/save/mutation; nonfinite values null.
    """
    return httpx.post(f"{app.BASE_URL}/fog/height/inspect", json={}, timeout=60).text


def set_height_fog_scalar(actor_path: str, component_path: str, field: str, expected_value: float,
                            value: float, confirm: bool = False, dry_run: bool = False) -> str:
    """Set FogDensity0..10/FogHeightFalloff0..2/FogMaxOpacity0..1,
    StartDistance/FogCutoffDistance/VolumetricFogDistance0..1e9 (native world clamps also apply),
    VolumetricFogScatteringDistribution-0.99..0.99/VolumetricFogExtinctionScale0..1000.
    InscatteringColorCubemapAngle0..360, DirectionalInscatteringExponent0..1000,
    DirectionalInscatteringStartDistance0..1e9, ordered FullyDirectionalInscatteringColorDistance/
    NonDirectionalInscatteringColorDistance (native world bounds).
    EndDistance/VolumetricFogStartDistance/VolumetricFogNearFadeInDistance0..1e9;
    EndDistance also respects native world clamp, zero disables end distance.
    VolumetricFogStaticLightingScatteringIntensity0..1000 (adapter cap; native UI max10).
    Exact current value guard, native float/transaction/notification/dry-run/no-op/no save; unverified.
    """
    return httpx.post(f"{app.BASE_URL}/fog/height/scalar", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "FieldName": field,
        "ExpectedValue": expected_value, "Value": value, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_height_fog_volumetric_enabled(actor_path: str, component_path: str, expected_enabled: bool,
                                        enabled: bool, confirm: bool = False, dry_run: bool = False) -> str:
    """Set native volumetric-fog enable with inspected current flag guard; scalar settings retained.
    Native editor notification may allocate renderer resources/recurring GPU work.
    Transaction/dry-run/no-op/no build/save; scalability/render/undo effects unverified.
    """
    return httpx.post(f"{app.BASE_URL}/fog/height/volumetric-enabled", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "bExpectedValue": expected_enabled,
        "bValue": enabled, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_height_fog_render_flag(actor_path: str, component_path: str, field: str, expected_enabled: bool,
                                        enabled: bool, confirm: bool = False, dry_run: bool = False) -> str:
    """Set bOverrideLightColorsWithFogInscatteringColors/bHoldout/bRenderInMainPass.
    Exact inspected flag/actor/component guard, transaction/notification/no-op/dry-run.
    Override requires appropriate volumetric/sun settings; holdout requires project alpha support.
    No project setting edits/build/save; rendering/callbacks/undo unverified.
    """
    return httpx.post(f"{app.BASE_URL}/fog/height/bool", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "bExpectedValue": expected_enabled,
        "FieldName": field, "bValue": enabled, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_height_fog_second_layer(actor_path: str, component_path: str, expected_values: list[float],
                                  values: list[float], confirm: bool = False, dry_run: bool = False) -> str:
    """Set second-layer [density,falloff,height offset] with full current triple guard.
    Density0..10/falloff0..2/offset+/-1e9 relative actor Z; density0 disables layer.
    Native float/transaction/notification/readback/dry-run/no-op/no save; renderer/undo unverified.
    """
    if len(values) != 3 or len(expected_values) != 3:
        raise ValueError("Expected/new layer requires density/falloff/offset triples")
    return httpx.post(f"{app.BASE_URL}/fog/height/second-layer", json={
        "ActorPath": actor_path, "ComponentPath": component_path,
        "ExpectedSecondLayer": dict(zip(("X", "Y", "Z"), expected_values)),
        "SecondLayer": dict(zip(("X", "Y", "Z"), values)), "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def create_height_fog(name: str, location: list[float], confirm: bool = False,
                        dry_run: bool = False) -> str:
    """Create native height-fog actor in ordinary persistent map with native defaults.
    Unique name1..128 letters/digits/underscore, finite XYZ+/-1e9.
    Transaction/dry-run/no build/save; registration/render selection/undo unverified.
    """
    if len(location) != 3:
        raise ValueError("Location requires XYZ triple")
    return httpx.post(f"{app.BASE_URL}/fog/height/create", json={
        "Name": name, "Location": dict(zip(("X", "Y", "Z"), location)),
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def delete_height_fog(actor_path: str, component_path: str, confirm: bool = False,
                        dry_run: bool = False) -> str:
    """Delete native height-fog actor with inspected actor/component identity guards.
    Ordinary persistent map/no attached actors. Transaction/dry-run/no save;
    renderer teardown/references/callbacks/undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/fog/height/delete", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_height_fog_visible(actor_path: str, component_path: str, expected_visible: bool,
                             visible: bool, confirm: bool = False, dry_run: bool = False) -> str:
    """Set fog component visibility with inspected flag guard; no child propagation.
    Actor replicated enable flag/settings retained; later replication may overwrite visibility.
    Transaction/readback/dry-run/no-op/no save; renderer/undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/fog/height/visible", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "bExpectedValue": expected_visible,
        "bValue": visible, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


def set_height_fog_color(actor_path: str, component_path: str, field: str,
                           expected_color: list[float], color: list[float],
                           confirm: bool = False, dry_run: bool = False) -> str:
    """Set FogInscatteringLuminance/DirectionalInscatteringLuminance/
    VolumetricFogEmissive/InscatteringTextureTint/SkyAtmosphereAmbientContributionColorScale
    linear RGBA0..1000; atmosphere contribution requires native support cvar.
    Exact full current-color guard/native float/no sRGB conversion. Transaction/
    notification/dry-run/no-op/no save; cvars/render/undo effects unverified.
    """
    if len(color) != 4 or len(expected_color) != 4:
        raise ValueError("Expected/new color requires linear RGBA quadruples")
    return httpx.post(f"{app.BASE_URL}/fog/height/color", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "FieldName": field,
        "ExpectedColor": expected_color, "Color": color, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_height_fog_albedo(actor_path: str, component_path: str, expected_color: list[int],
                            color: list[int], confirm: bool = False, dry_run: bool = False) -> str:
    """Set stored volumetric albedo RGBA bytes0..255 with full inspected color guard.
    No linear/sRGB conversion; enable/scalar fog settings retained. Transaction/
    notification/readback/dry-run/no-op/no save; renderer/undo/persistence unverified.
    """
    if len(color) != 4 or len(expected_color) != 4:
        raise ValueError("Expected/new albedo requires RGBA quadruples")
    return httpx.post(f"{app.BASE_URL}/fog/height/albedo", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ExpectedColor": expected_color,
        "Color": color, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_height_fog_cubemap(actor_path: str, component_path: str, expected_cubemap_path: str,
                             cubemap_path: str, confirm: bool = False, dry_run: bool = False) -> str:
    """Assign loaded persistent fog-inscattering cubemap or empty to clear, current asset guard.
    Native cube can override effective color/directional scattering. Transaction/notification/
    readback/dry-run/no-op/no asset load/save; renderer/undo behavior unverified.
    """
    return httpx.post(f"{app.BASE_URL}/fog/height/cubemap", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ExpectedCubemapPath": expected_cubemap_path,
        "CubemapPath": cubemap_path, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_height_fog_transform(actor_path: str, component_path: str,
                                     expected_location: list[float], expected_rotation: list[float],
                                     expected_scale: list[float], location: list[float],
                                     rotation: list[float], scale: list[float],
                                     confirm: bool = False, dry_run: bool = False) -> str:
    """Set unattached height-fog component world transform; inspected transform guard.
    XYZ position+/-1e9, normalized quaternion XYZW, nonzero scale abs<=1000.
    Height-fog contribution depends on elevation; scale/rotation may not affect integration.
    Native no-sweep teleport/transform notification, children follow; transaction/dry-run/no save; unverified.
    """
    def transform(p, q, s):
        if len(p) != 3 or len(q) != 4 or len(s) != 3:
            raise ValueError("Transform requires XYZ position/scale and XYZW quaternion")
        return {"Translation": dict(zip(("X", "Y", "Z"), p)),
                "Rotation": dict(zip(("X", "Y", "Z", "W"), q)),
                "Scale3D": dict(zip(("X", "Y", "Z"), s))}
    return httpx.post(f"{app.BASE_URL}/fog/height/transform", json={
        "ActorPath": actor_path, "ComponentPath": component_path,
        "ExpectedTransform": transform(expected_location, expected_rotation, expected_scale),
        "Transform": transform(location, rotation, scale), "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_world_local_fog() -> str:
    """Inspect up to128 loaded current-world local fog components and authored controls.
    Native renderer uses maximum axis scale times base size500 for uniform sphere scale.
    Nonfinite values null; global iteration unbounded, no update/load/save; unverified.
    """
    return httpx.post(f"{app.BASE_URL}/fog/local/inspect", json={}, timeout=60).text


def set_local_fog_scalar(actor_path: str, component_path: str, field: str, expected_value: float,
                         value: float, confirm: bool = False, dry_run: bool = False) -> str:
    """Set RadialFogExtinction/HeightFogExtinction0..1000, HeightFogFalloff1..1e6,
    HeightFogOffset+/-1e6 or FogPhaseG0..0.999. Non-native maxima are adapter caps.
    Exact inspected value/actor/component guard, transaction/notification/readback/dry-run/no save.
    Renderer/callbacks/undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/fog/local/scalar", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "FieldName": field,
        "ExpectedValue": expected_value, "Value": value, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_local_fog_visible(actor_path: str, component_path: str, expected_visible: bool,
                             visible: bool, confirm: bool = False, dry_run: bool = False) -> str:
    """Set fog component visibility with inspected flag guard; no child propagation.
    Actor replicated enable flag/settings retained; later replication may overwrite visibility.
    Transaction/readback/dry-run/no-op/no save; renderer/undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/fog/local/visible", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "bExpectedValue": expected_visible,
        "bValue": visible, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_local_fog_transform(actor_path: str, component_path: str,
                                     expected_location: list[float], expected_rotation: list[float],
                                     expected_scale: list[float], location: list[float],
                                     rotation: list[float], scale: list[float],
                                     confirm: bool = False, dry_run: bool = False) -> str:
    """Set unattached local-fog component world transform; inspected transform guard.
    XYZ position+/-1e9, normalized quaternion XYZW, nonzero scale abs<=1000.
    Native renderer uses max-axis scale times base size500 for a uniform sphere.
    Native no-sweep teleport/transform notification, children follow; transaction/dry-run/no save; unverified.
    """
    def transform(p, q, s):
        if len(p) != 3 or len(q) != 4 or len(s) != 3:
            raise ValueError("Transform requires XYZ position/scale and XYZW quaternion")
        return {"Translation": dict(zip(("X", "Y", "Z"), p)),
                "Rotation": dict(zip(("X", "Y", "Z", "W"), q)),
                "Scale3D": dict(zip(("X", "Y", "Z"), s))}
    return httpx.post(f"{app.BASE_URL}/fog/local/transform", json={
        "ActorPath": actor_path, "ComponentPath": component_path,
        "ExpectedTransform": transform(expected_location, expected_rotation, expected_scale),
        "Transform": transform(location, rotation, scale), "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


def set_local_fog_color(actor_path: str, component_path: str, field: str,
                           expected_color: list[float], color: list[float],
                           confirm: bool = False, dry_run: bool = False) -> str:
    """Set local FogAlbedo/FogEmissive linear RGBA0..1, matching native metadata.
    Exact full inspected current RGBA/actor/component guard; native float/no sRGB conversion.
    Transaction/notification/readback/no-op/dry-run/no save; renderer/undo unverified.
    """
    if len(color) != 4 or len(expected_color) != 4:
        raise ValueError("Expected/new color requires linear RGBA quadruples")
    return httpx.post(f"{app.BASE_URL}/fog/local/color", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "FieldName": field,
        "ExpectedColor": expected_color, "Color": color, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_local_fog_priority(actor_path: str, component_path: str, expected_priority: int,
                           priority: int, confirm: bool = False, dry_run: bool = False) -> str:
    """Set local-fog native sort priority-127..127 with exact inspected integer guard.
    Lower priority draws behind higher priority, overriding distance sort.
    Transaction/notification/readback/no-op/dry-run/no save; renderer/undo unverified.
    """
    return httpx.post(f"{app.BASE_URL}/fog/local/priority", json={
        "ActorPath": actor_path, "ComponentPath": component_path,
        "ExpectedValue": expected_priority, "Value": priority,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def create_local_fog(name: str, location: list[float], confirm: bool = False,
                        dry_run: bool = False) -> str:
    """Create native local-fog actor in ordinary persistent map with native defaults.
    Unique name1..128 letters/digits/underscore, finite XYZ+/-1e9.
    Transaction/dry-run/no build/save; registration/render policy/undo unverified.
    """
    if len(location) != 3:
        raise ValueError("Location requires XYZ triple")
    return httpx.post(f"{app.BASE_URL}/fog/local/create", json={
        "Name": name, "Location": dict(zip(("X", "Y", "Z"), location)),
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def delete_local_fog(actor_path: str, component_path: str, confirm: bool = False,
                        dry_run: bool = False) -> str:
    """Delete native local-fog actor with inspected actor/component identity guards.
    Ordinary persistent map/no attached actors. Transaction/dry-run/no save;
    renderer teardown/references/callbacks/undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/fog/local/delete", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_world_volumetric_clouds() -> str:
    """Inspect up to128 current-world volumetric clouds, native scalar/flag names/material soft path.
    Native distances kilometers, no asset load/render update; contribution/eligibility unverified.
    """
    return httpx.post(f"{app.BASE_URL}/clouds/inspect", json={}, timeout=60).text


def set_volumetric_cloud_scalar(actor_path: str, component_path: str, field: str,
                                expected_value: float, value: float,
                                confirm: bool = False, dry_run: bool = False) -> str:
    """Set inspected cloud layer/tracing/planet/quality/aerial-perspective native scalar.
    Distances kilometers; native clamp metadata respected; sample scales0.05..8 adapter cap.
    Other unspecified caps1e6, LayerBottomAltitude allows negative; PlanetRadius0.1..10000.
    Exact inspected value/identities, transaction/notification/readback/no-op/dry-run/no save.
    Quality changes can increase GPU work; renderer/callbacks/undo unverified.
    """
    return httpx.post(f"{app.BASE_URL}/clouds/scalar", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "FieldName": field,
        "ExpectedValue": expected_value, "Value": value, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


def set_volumetric_cloud_bool(actor_path: str, component_path: str, field: str,
                              expected_value: bool, value: bool,
                              confirm: bool = False, dry_run: bool = False) -> str:
    """Set bUsePerSampleAtmosphericLightTransmittance/bVisibleInRealTimeSkyCaptures/
    bHoldout/bRenderInMainPass, exact inspected flag guard. Holdout requires project alpha support.
    Transaction/notification/readback/no-op/dry-run/no save; renderer/undo unverified.
    """
    return httpx.post(f"{app.BASE_URL}/clouds/bool", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "FieldName": field,
        "bExpectedValue": expected_value, "bValue": value, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_volumetric_cloud_ground_albedo(actor_path: str, component_path: str,
                                       expected_color: list[int], color: list[int],
                                       confirm: bool = False, dry_run: bool = False) -> str:
    """Set stored cloud ground-albedo RGBA bytes0..255 with exact full inspected-color guard.
    No sRGB conversion; effect requires cloud material GroundContribution enabled.
    Transaction/notification/readback/no-op/dry-run/no save; renderer/undo unverified.
    """
    if len(color) != 4 or len(expected_color) != 4:
        raise ValueError("Expected/new stored RGBA bytes require quadruples")
    return httpx.post(f"{app.BASE_URL}/clouds/ground-albedo", json={
        "ActorPath": actor_path, "ComponentPath": component_path,
        "ExpectedColor": expected_color, "Color": color, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_volumetric_cloud_visible(actor_path: str, component_path: str,
                                 expected_visible: bool, visible: bool,
                                 confirm: bool = False, dry_run: bool = False) -> str:
    """Set cloud component visibility with exact inspected flag/identities, no child propagation.
    Transaction/native setter/readback/no-op/dry-run/no save; renderer/undo unverified.
    """
    return httpx.post(f"{app.BASE_URL}/clouds/visible", json={
        "ActorPath": actor_path, "ComponentPath": component_path,
        "bExpectedValue": expected_visible, "bValue": visible,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_volumetric_cloud_tracing_mode(actor_path: str, component_path: str,
                                      expected_mode: int, mode: int,
                                      confirm: bool = False, dry_run: bool = False) -> str:
    """Set tracing max-distance mode0 cloud-layer entry point /1 point of view.
    Exact inspected ordinal/identities; distances retained. Transaction/notification/
    readback/no-op/dry-run/no save; renderer/callbacks/undo unverified.
    """
    return httpx.post(f"{app.BASE_URL}/clouds/tracing-mode", json={
        "ActorPath": actor_path, "ComponentPath": component_path,
        "ExpectedValue": expected_mode, "Value": mode, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def create_volumetric_cloud(name: str, location: list[float], confirm: bool = False,
                        dry_run: bool = False) -> str:
    """Create native volumetric-cloud actor in ordinary persistent map with native defaults.
    Unique name1..128 letters/digits/underscore, finite XYZ+/-1e9.
    Transaction/dry-run/no build/save; registration can synchronously load default material/precache PSOs; renderer/undo unverified.
    """
    if len(location) != 3:
        raise ValueError("Location requires XYZ triple")
    return httpx.post(f"{app.BASE_URL}/clouds/create", json={
        "Name": name, "Location": dict(zip(("X", "Y", "Z"), location)),
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def delete_volumetric_cloud(actor_path: str, component_path: str, confirm: bool = False,
                        dry_run: bool = False) -> str:
    """Delete native volumetric-cloud actor with inspected actor/component identity guards.
    Ordinary persistent map/no attached actors. Transaction/dry-run/no save;
    renderer teardown/references/callbacks/undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/clouds/delete", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_world_sky_atmospheres() -> str:
    """Inspect up to128 current-world sky-atmosphere components, native scalar/color/flag names.
    Includes native absorption tent and transform mode; distances kilometers, angles degrees.
    No update/load/build/save; renderer eligibility/contribution unverified.
    """
    return httpx.post(f"{app.BASE_URL}/atmosphere/inspect", json={}, timeout=60).text


def set_sky_atmosphere_scalar(actor_path: str, component_path: str, field: str,
                              expected_value: float, value: float,
                              confirm: bool = False, dry_run: bool = False) -> str:
    """Set inspected native atmosphere radius/height/scattering/distribution/art-direction scalar.
    Native clamp ranges, trace scale0.25..8 adapter cap, other unspecified maxima1e6.
    Kilometer distances/degree elevation angle. Exact inspected guard/transaction/notification/
    readback/no-op/dry-run/no build/save; native callback may invalidate static lighting GUIDs.
    Renderer/undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/atmosphere/scalar", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "FieldName": field,
        "ExpectedValue": expected_value, "Value": value, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


def set_sky_atmosphere_bool(actor_path: str, component_path: str, field: str,
                            expected_value: bool, value: bool,
                            confirm: bool = False, dry_run: bool = False) -> str:
    """Set bHoldout/bRenderInMainPass with exact inspected flag/actor/component guard.
    Holdout requires project alpha/renderer support; project settings unchanged.
    Transaction/notification/readback/no-op/dry-run/no build/save; renderer/undo unverified.
    """
    return httpx.post(f"{app.BASE_URL}/atmosphere/bool", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "FieldName": field,
        "bExpectedValue": expected_value, "bValue": value, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


def set_sky_atmosphere_color(actor_path: str, component_path: str, field: str,
                             expected_color: list[float], color: list[float],
                             confirm: bool = False, dry_run: bool = False) -> str:
    """Set RayleighScattering/MieScattering/MieAbsorption/OtherAbsorption/
    SkyLuminanceFactor/SkyAndAerialPerspectiveLuminanceFactor linear RGBA0..1000 adapter cap.
    Exact full inspected RGBA/actor/component guard, native float/no sRGB conversion.
    Transaction/notification/readback/no-op/dry-run/no build/save; static GUID changes/
    native callbacks/rendering/undo unverified, separate scale controls retained.
    """
    if len(color) != 4 or len(expected_color) != 4:
        raise ValueError("Expected/new linear RGBA require quadruples")
    return httpx.post(f"{app.BASE_URL}/atmosphere/color", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "FieldName": field,
        "ExpectedColor": expected_color, "Color": color, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_sky_atmosphere_ground_albedo(actor_path: str, component_path: str,
                                     expected_color: list[int], color: list[int],
                                     confirm: bool = False, dry_run: bool = False) -> str:
    """Set native stored GroundAlbedo RGBA bytes0..255 with full inspected current-color guard.
    No color-space conversion; effective contribution requires MultiScatteringFactor>0.
    Transaction/notification/readback/no-op/dry-run/no build/save; renderer/undo unverified.
    """
    if len(color) != 4 or len(expected_color) != 4:
        raise ValueError("Expected/new stored RGBA bytes require quadruples")
    return httpx.post(f"{app.BASE_URL}/atmosphere/ground-albedo", json={
        "ActorPath": actor_path, "ComponentPath": component_path,
        "ExpectedColor": expected_color, "Color": color, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_sky_atmosphere_absorption_tent(actor_path: str, component_path: str,
                                      expected_tent: list[float], tent: list[float],
                                      confirm: bool = False, dry_run: bool = False) -> str:
    """Set native absorption tent triple [tip altitude km, tip value, width km].
    Exact inspected full triple guard; altitude+/-1e6/value0..1e6/width0..1e6 adapter caps.
    Zero width native-metadata valid but render semantics unverified; native floats.
    Transaction/notification/readback/no-op/dry-run/no build/save; GUID/callbacks/undo unverified.
    """
    if len(tent) != 3 or len(expected_tent) != 3:
        raise ValueError("Expected/new tent requires altitude/value/width triples")
    return httpx.post(f"{app.BASE_URL}/atmosphere/absorption-tent", json={
        "ActorPath": actor_path, "ComponentPath": component_path,
        "ExpectedTent": dict(zip(("X", "Y", "Z"), expected_tent)),
        "Tent": dict(zip(("X", "Y", "Z"), tent)), "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_sky_atmosphere_visible(actor_path: str, component_path: str,
                               expected_visible: bool, visible: bool,
                               confirm: bool = False, dry_run: bool = False) -> str:
    """Set sky-atmosphere component visibility with exact inspected flag/identity guards.
    Native SetVisibility(no child propagation)/transaction/readback/no-op/dry-run/no save.
    Renderer selection/callbacks/undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/atmosphere/visible", json={
        "ActorPath": actor_path, "ComponentPath": component_path,
        "bExpectedValue": expected_visible, "bValue": visible,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_sky_atmosphere_transform_mode(actor_path: str, component_path: str,
                                      expected_mode: int, mode: int,
                                      confirm: bool = False, dry_run: bool = False) -> str:
    """Set native planet placement mode0 top at absolute world origin,
    1 top at component transform,2 center at component transform; component transform retained.
    Exact inspected ordinal/actor/component guards, transaction/notification/readback/no-op/dry-run.
    Native callback may invalidate static GUIDs/change effective planet placement; no build/save.
    Renderer/callbacks/undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/atmosphere/transform-mode", json={
        "ActorPath": actor_path, "ComponentPath": component_path,
        "ExpectedValue": expected_mode, "Value": mode, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def create_sky_atmosphere(name: str, location: list[float],
                           confirm: bool = False, dry_run: bool = False) -> str:
    """Create native ASkyAtmosphere in ordinary persistent map with native defaults.
    Unique bounded identifier1..128/XYZ+/-1e9; default transform mode may ignore actor location.
    Transaction/registration readback/dry-run/no build/save; renderer selection/undo unverified.
    """
    if len(location) != 3:
        raise ValueError("Location requires XYZ triple")
    return httpx.post(f"{app.BASE_URL}/atmosphere/create", json={
        "Name": name, "Location": dict(zip(("X", "Y", "Z"), location)),
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def delete_sky_atmosphere(actor_path: str, component_path: str,
                           confirm: bool = False, dry_run: bool = False) -> str:
    """Delete native sky-atmosphere actor with exact inspected actor/component identity guards.
    Ordinary persistent map/no attached actors; level/actor/component transaction/native destruction.
    Dry-run/no build/save; native sky selection/resource teardown/references/undo unverified.
    """
    return httpx.post(f"{app.BASE_URL}/atmosphere/delete", json={
        "ActorPath": actor_path, "ComponentPath": component_path,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_sky_atmosphere_transform(actor_path: str, component_path: str, expected_mode: int,
                                     expected_location: list[float], expected_rotation: list[float],
                                     expected_scale: list[float], location: list[float],
                                     rotation: list[float], scale: list[float],
                                     confirm: bool = False, dry_run: bool = False) -> str:
    """Set unattached sky-atmosphere world transform with inspected transform/mode guard.
    XYZ+/-1e9/normalized XYZW quaternion/nonzero scale abs<=1000, native no-sweep teleport.
    Native mode0 absolute origin may ignore translation; rotation/scale do not create ellipsoid.
    Children follow; transaction/readback/no-op/dry-run/no build/save, renderer/undo unverified.
    """
    def transform(p, q, s):
        if len(p) != 3 or len(q) != 4 or len(s) != 3:
            raise ValueError("Transform requires XYZ position/scale and XYZW quaternion")
        return {"Translation": dict(zip(("X", "Y", "Z"), p)),
                "Rotation": dict(zip(("X", "Y", "Z", "W"), q)),
                "Scale3D": dict(zip(("X", "Y", "Z"), s))}
    return httpx.post(f"{app.BASE_URL}/atmosphere/transform", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ExpectedMode": expected_mode,
        "ExpectedTransform": transform(expected_location, expected_rotation, expected_scale),
        "Transform": transform(location, rotation, scale), "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_volumetric_cloud_transform(actor_path: str, component_path: str,
                                     expected_location: list[float], expected_rotation: list[float],
                                     expected_scale: list[float], location: list[float],
                                     rotation: list[float], scale: list[float],
                                     confirm: bool = False, dry_run: bool = False) -> str:
    """Set unattached cloud authored world transform with inspected full transform guard.
    XYZ+/-1e9/normalized XYZW quaternion/nonzero scale abs<=1000, native no-sweep teleport.
    Cloud geometry uses layer/planet/material controls; transform does not prove rendered movement.
    Children follow; transaction/readback/no-op/dry-run/no build/save; renderer/undo unverified.
    """
    def transform(p, q, s):
        if len(p) != 3 or len(q) != 4 or len(s) != 3:
            raise ValueError("Transform requires XYZ position/scale and XYZW quaternion")
        return {"Translation": dict(zip(("X", "Y", "Z"), p)),
                "Rotation": dict(zip(("X", "Y", "Z", "W"), q)),
                "Scale3D": dict(zip(("X", "Y", "Z"), s))}
    return httpx.post(f"{app.BASE_URL}/clouds/transform", json={
        "ActorPath": actor_path, "ComponentPath": component_path,
        "ExpectedTransform": transform(expected_location, expected_rotation, expected_scale),
        "Transform": transform(location, rotation, scale), "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_planar_reflection_actor_lists(actor_path: str, component_path: str, start: int = 0, count: int = 64) -> str:
    """Inspect inherited hidden/show-only actor references in independent pages1..128.
    Authored lists only; planar renderer support/effective visibility unverified, no capture/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/reflection-captures/planar/actor-lists/inspect", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "Start": start, "Count": count
    }, timeout=180).text


@mcp.tool()
def set_planar_reflection_actor_list(actor_path: str, component_path: str, actor_guid: str, expected_label: str,
                                      field_name: str, expected_actor_paths: list[str], actor_paths: list[str],
                                      confirm: bool = False, dry_run: bool = True) -> str:
    """Replace inherited HiddenActors or ShowOnlyActors<=64 with full ordered prior-path guard.
    Unique loaded persistent current-world targets, empty clears; preserves other lists/render mode.
    Native transaction/events/readback; planar renderer support/effective visibility unverified.
    No ordinary actor visibility edits, explicit capture, renderer synchronization, load or save.
    """
    return httpx.post(f"{app.BASE_URL}/reflection-captures/planar/actor-lists/set", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ActorGuid": actor_guid,
        "ExpectedLabel": expected_label, "FieldName": field_name,
        "ExpectedActorPaths": expected_actor_paths, "ActorPaths": actor_paths,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_planar_reflection_capture_policy(actor_path: str, component_path: str, actor_guid: str, expected_label: str,
                                          field_name: str, expected_value: float, value: float,
                                          confirm: bool = False, dry_run: bool = True) -> str:
    """Set inherited PrimitiveRenderMode0 Legacy/1 RenderScenePrimitives/2 UseShowOnlyList,
    bCaptureEveryFrame/bCaptureOnMovement/bAlwaysPersistRenderingState/bExcludeFromSceneTextureExtents0..1.
    Exact current field guard, preserves all actor/component lists and sibling policies.
    Native planar renderer use/effective result unverified; normal renderer updates may capture.
    No explicit capture/render synchronization/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/reflection-captures/planar/capture-policy", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ActorGuid": actor_guid,
        "ExpectedLabel": expected_label, "FieldName": field_name, "ExpectedValue": expected_value,
        "Value": value, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_planar_reflection_component_lists(actor_path: str, component_path: str, start: int = 0, count: int = 64) -> str:
    """Inspect hidden/show-only weak primitive-component refs in independent pages1..128.
    Stale/null refs export None path; no loading, capture or effective visibility evaluation.
    """
    return httpx.post(f"{app.BASE_URL}/reflection-captures/planar/component-lists/inspect", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "Start": start, "Count": count
    }, timeout=180).text


@mcp.tool()
def set_planar_reflection_component_list(actor_path: str, component_path: str, actor_guid: str, expected_label: str,
                                          field_name: str, expected_component_paths: list[str], component_paths: list[str],
                                          confirm: bool = False, dry_run: bool = True) -> str:
    """Replace HiddenComponents/ShowOnlyComponents<=64 with full prior-path guard.
    Unique loaded persistent current-world primitive components, empty clears; weak refs retained.
    Preserves opposite component list/actor lists/render mode. Stale/null paths are None and not unique handle IDs.
    Native transaction/events/readback; no visibility edits/capture/render sync/load/save, renderer support unverified.
    """
    return httpx.post(f"{app.BASE_URL}/reflection-captures/planar/component-lists/set", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ActorGuid": actor_guid,
        "ExpectedLabel": expected_label, "FieldName": field_name,
        "ExpectedComponentPaths": expected_component_paths, "ComponentPaths": component_paths,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_planar_reflection_capture_numeric(actor_path: str, component_path: str, actor_guid: str, expected_label: str,
                                           field_name: str, expected_value: float, value: float,
                                           confirm: bool = False, dry_run: bool = True) -> str:
    """Set LODDistanceFactor0.1..10, MaxViewDistanceOverride-1..1e9cm, CaptureSortPriority signed int32.
    Nonpositive maximum distance disables override; native priority setter used.
    Exact current field guard/preservation/readback; renderer effects unverified, no explicit capture/sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/reflection-captures/planar/capture-numeric", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ActorGuid": actor_guid,
        "ExpectedLabel": expected_label, "FieldName": field_name, "ExpectedValue": expected_value,
        "Value": value, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_planar_reflection_show_flags(actor_path: str, component_path: str, start: int = 0, count: int = 64,
                                         query_names: list[str] | None = None) -> str:
    """Page stored flag overrides1..128 and query up to128 named current component bits.
    Component bits are not final renderer/project output; no capture/flag update/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/reflection-captures/planar/show-flags/inspect", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "Start": start, "Count": count,
        "ShowFlagNames": query_names or []
    }, timeout=180).text


@mcp.tool()
def set_planar_reflection_show_flags(actor_path: str, component_path: str, actor_guid: str, expected_label: str,
                                     expected_names: list[str], expected_enabled: list[bool],
                                     names: list[str], enabled: list[bool], confirm: bool = False, dry_run: bool = True) -> str:
    """Replace full ordered native show-flag overrides<=128 with exact previous name/bool guard.
    Unique recognized native flag indices, empty clears overrides using native setter/archetype inheritance.
    Stored flags may differ from renderer/fixed flags; no visual proof/explicit capture/sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/reflection-captures/planar/show-flags/set", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ActorGuid": actor_guid,
        "ExpectedLabel": expected_label, "ExpectedShowFlagNames": expected_names,
        "ExpectedShowFlagValues": expected_enabled, "ShowFlagNames": names, "ShowFlagValues": enabled,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def discover_planar_reflection_show_flags(actor_path: str, component_path: str, name_filter: str = "",
                                          start: int = 0, count: int = 64) -> str:
    """Discover native engine/custom show flags in name-sorted pages1..128 with substring filter.
    Includes editor group/current component bit/stored override counts; no mutability/renderer output guarantee.
    Registry changes can shift offsets; no registration, flag updates, capture, load or save.
    """
    return httpx.post(f"{app.BASE_URL}/reflection-captures/planar/show-flags/discover", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "Name": name_filter,
        "Start": start, "Count": count
    }, timeout=180).text


@mcp.tool()
def inspect_reflection_captures_page(start: int = 0, count: int = 64, shape: str = "All", actor_path: str = "") -> str:
    """Inspect component-path sorted loaded persistent current-world captures in pages1..128.
    Shape All/Sphere/Box/Plane/Custom and optional exact owner filter; GUID/label/dirty/native fields.
    Scene changes can shift offsets; no recapture/render synchronization/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/reflection-captures/inspect-page", json={
        "Start": start, "Count": count, "Shape": shape, "ActorPath": actor_path
    }, timeout=180).text


@mcp.tool()
def inspect_planar_reflections_page(start: int = 0, count: int = 64, actor_path: str = "") -> str:
    """Inspect component-path sorted loaded persistent current-world planar captures in pages1..128.
    Optional exact owner filter; includes GUID/label/dirty/native settings, no capture/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/reflection-captures/planar/inspect-page", json={
        "Start": start, "Count": count, "ActorPath": actor_path
    }, timeout=180).text


@mcp.tool()
def inspect_light_advanced_policy(actor_path: str, component_path: str) -> str:
    """Inspect contribution/ray-end bias/MegaLights/cinematic-cached shadow policy and edit metadata.
    No renderer eligibility evaluation, build, load or save.
    """
    return httpx.post(f"{app.BASE_URL}/lights/advanced-policy/inspect", json={
        "ActorPath": actor_path, "ComponentPath": component_path
    }, timeout=180).text


@mcp.tool()
def set_light_advanced_policy(actor_path: str, component_path: str, actor_guid: str, expected_label: str,
                               field_name: str, expected_value: float, value: float,
                               confirm: bool = False, dry_run: bool = True) -> str:
    """Set SpecularScale/DiffuseScale0..1, RayEndBias0..1e6, MegaLightsShadowMethod0 Default/1 RayTracing/2 VSM,
    bOverrideRayEndBias/bAllowMegaLights/bCastShadowsFromCinematicObjectsOnly/bForceCachedShadowsForMovablePrimitives0..1.
    Exact current value/GUID/label guard, native setters/events/readback; inactive fields allowed.
    Renderer/project support unverified; no build/render sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/lights/advanced-policy/set", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ActorGuid": actor_guid,
        "ExpectedLabel": expected_label, "FieldName": field_name, "ExpectedValue": expected_value,
        "Value": value, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_light_lightmass_settings(actor_path: str, component_path: str) -> str:
    """Inspect stored local/directional light Lightmass fields and full native snapshot.
    Directional baked LightSourceAngle differs from runtime source angle; no bake/evaluation/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/lights/lightmass/inspect", json={
        "ActorPath": actor_path, "ComponentPath": component_path
    }, timeout=180).text


@mcp.tool()
def set_light_lightmass_setting(actor_path: str, component_path: str, actor_guid: str, expected_label: str,
                                 expected_settings_text: str, field_name: str, expected_value: float, value: float,
                                 confirm: bool = False, dry_run: bool = True) -> str:
    """Edit IndirectLightingSaturation0..4, ShadowExponent0.1..4, bUseAreaShadowsForStationaryLight0..1,
    or directional baked LightSourceAngle0.0001..5 degrees with full native snapshot/current value guard.
    Native struct preservation/nested events/readback, no lighting bake/output evaluation/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/lights/lightmass/set", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ActorGuid": actor_guid,
        "ExpectedLabel": expected_label, "ExpectedSettingsText": expected_settings_text,
        "FieldName": field_name, "ExpectedValue": expected_value, "Value": value,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_directional_light_shadows(actor_path: str, component_path: str) -> str:
    """Inspect native directional cascade/far/distance-field/ray shadow/forward priority settings and adapter bounds."""
    return httpx.post(f"{app.BASE_URL}/lights/directional-shadows/inspect", json={
        "ActorPath": actor_path, "ComponentPath": component_path
    }, timeout=180).text


@mcp.tool()
def set_directional_light_shadow_setting(actor_path: str, component_path: str, actor_guid: str, expected_label: str,
                                          field_name: str, expected_value: float, value: float,
                                          confirm: bool = False, dry_run: bool = True) -> str:
    """Set inspected native directional shadow/forward-priority field within reported adapter bounds.
    Exact current scalar/GUID/label guards; preserves supported siblings, enabled far cascades require
    far distance>=current mobility-selected dynamic distance. Inactive settings accepted.
    Renderer counts/eligibility/effects unverified; no output evaluation/build/render sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/lights/directional-shadows/set", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ActorGuid": actor_guid,
        "ExpectedLabel": expected_label, "FieldName": field_name, "ExpectedValue": expected_value,
        "Value": value, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_directional_light_clouds(actor_path: str, component_path: str) -> str:
    """Inspect native directional atmosphere/cloud shadow flags/strength/bias/extent/resolution/sample controls.
    Extent radius in kilometers; renderer/scalability/project effects unverified, no evaluation/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/lights/directional-clouds/inspect", json={
        "ActorPath": actor_path, "ComponentPath": component_path
    }, timeout=180).text


@mcp.tool()
def set_directional_light_cloud_setting(actor_path: str, component_path: str, actor_guid: str, expected_label: str,
                                         field_name: str, expected_value: float, value: float,
                                         confirm: bool = False, dry_run: bool = True) -> str:
    """Set inspected atmosphere/cloud shadow flag/scalar within reported adapter bounds.
    Exact current scalar/GUID/label guards and supported-sibling preservation/readback.
    Extent radius uses kilometers, not centimeters. Sun-light index1 disables opaque shadows onto clouds.
    Inactive fields accepted; no renderer output proof/evaluation/build/render sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/lights/directional-clouds/set", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ActorGuid": actor_guid,
        "ExpectedLabel": expected_label, "FieldName": field_name, "ExpectedValue": expected_value,
        "Value": value, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_directional_light_luminance_color(actor_path: str, component_path: str, actor_guid: str, expected_label: str,
                                           field_name: str, expected_rgba: list[float], rgba: list[float],
                                           confirm: bool = False, dry_run: bool = True) -> str:
    """Set AtmosphereSunDiskColorScale or CloudScatteredLuminanceScale linear RGBA0..1000.
    Exact full inspected RGBA guard; no sRGB conversion, alpha stored though native editor hides it.
    Preserves other color/cloud policies/mobility/sun context; native setter/events/readback.
    No image evaluation/build/render sync/load/save; renderer eligibility/output unverified.
    """
    return httpx.post(f"{app.BASE_URL}/lights/directional-clouds/color", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ActorGuid": actor_guid,
        "ExpectedLabel": expected_label, "FieldName": field_name,
        "ExpectedLinearColor": expected_rgba, "LinearColor": rgba, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_light_shaft_settings(actor_path: str, component_path: str) -> str:
    """Inspect light-shaft bloom/directional occlusion fields, stored tint bytes and direction override.
    No screen-space evaluation/build/render synchronization/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/lights/shafts/inspect", json={
        "ActorPath": actor_path, "ComponentPath": component_path
    }, timeout=180).text


@mcp.tool()
def set_light_shaft_setting(actor_path: str, component_path: str, actor_guid: str, expected_label: str,
                             field_name: str, expected_value: float, value: float,
                             confirm: bool = False, dry_run: bool = True) -> str:
    """Set native bEnableLightShaftBloom0..1/BloomScale0..10/BloomThreshold0..4/BloomMaxBrightness0..100,
    directional bEnableLightShaftOcclusion0..1/OcclusionMaskDarkness0..1/OcclusionDepthRange0..1e9cm.
    Exact current value/GUID/label guards, native setters/full shaft sibling readback; inactive allowed.
    No renderer output evaluation/build/render synchronization/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/lights/shafts/set", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ActorGuid": actor_guid,
        "ExpectedLabel": expected_label, "FieldName": field_name, "ExpectedValue": expected_value,
        "Value": value, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


def set_light_shaft_bloom_tint(actor_path: str, component_path: str, actor_guid: str, expected_label: str,
                               expected_rgba_bytes: list[int], rgba_bytes: list[int],
                               confirm: bool = False, dry_run: bool = True) -> str:
    """Set native BloomTint RGBA bytes0..255 with full exact current tint guard, no color-space conversion.
    Native setter/events/readback preserves shaft policies; no image evaluation/build/render sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/lights/shafts/appearance", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ActorGuid": actor_guid,
        "ExpectedLabel": expected_label, "FieldName": "BloomTint",
        "ExpectedColor": expected_rgba_bytes, "Color": rgba_bytes, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


def set_directional_light_shaft_override_direction(actor_path: str, component_path: str, actor_guid: str,
                                                    expected_label: str, expected_direction: list[float], direction: list[float],
                                                    confirm: bool = False, dry_run: bool = True) -> str:
    """Set non-normalized shaft override vector+/-1e6 with exact current vector guard.
    Zero restores actual light direction, does not rotate light. Native setter/readback preserves shaft policies.
    No screen-space evaluation/build/render sync/load/save; renderer outcome unverified.
    """
    if len(expected_direction) != 3 or len(direction) != 3:
        raise ValueError("Directions require XYZ triples")
    return httpx.post(f"{app.BASE_URL}/lights/shafts/appearance", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ActorGuid": actor_guid,
        "ExpectedLabel": expected_label, "FieldName": "LightShaftOverrideDirection",
        "ExpectedDirection": dict(zip(("X", "Y", "Z"), expected_direction)),
        "Direction": dict(zip(("X", "Y", "Z"), direction)), "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_light_view_channels(actor_path: str, component_path: str) -> str:
    """Inspect five native view-lighting bits/mask and separate three object-lighting channels.
    Matching view/renderer support not evaluated; no build/render sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/lights/view-channels/inspect", json={
        "ActorPath": actor_path, "ComponentPath": component_path
    }, timeout=180).text


@mcp.tool()
def set_light_view_channels(actor_path: str, component_path: str, actor_guid: str, expected_label: str,
                              expected_channels: list[int], channels: list[int],
                              confirm: bool = False, dry_run: bool = True) -> str:
    """Set all five view-lighting bits0..1 with full exact prior-bit/GUID/label guard, zero mask allowed.
    Preserves three object-lighting channels; native transaction/events/readback, no matching view edits.
    Renderer output unverified, no build/render sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/lights/view-channels/set", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ActorGuid": actor_guid,
        "ExpectedLabel": expected_label, "ExpectedChannels": expected_channels, "Channels": channels,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_light_ray_policy(actor_path: str, component_path: str) -> str:
    """Inspect ray shadow policy/sample count/deep shadow/transmission/translucent/reflection/GI flags.
    Stored policy only, no active hardware/renderer proof or render evaluation/build/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/lights/ray-policy/inspect", json={
        "ActorPath": actor_path, "ComponentPath": component_path
    }, timeout=180).text


@mcp.tool()
def set_light_ray_policy(actor_path: str, component_path: str, actor_guid: str, expected_label: str,
                           field_name: str, expected_value: float, value: float,
                           confirm: bool = False, dry_run: bool = True) -> str:
    """Set CastRaytracedShadow0 Disabled/1 UseProjectSetting/2 Enabled, SamplesPerPixel1..1024,
    DeepShadowLayerDistribution0..1, bAffectTranslucentLighting/bTransmission/bCastDeepShadow/
    bAffectReflection/bAffectGlobalIllumination0..1. Exact current/GUID/label guard and sibling readback.
    Inactive accepted, does not enable hardware/project ray tracing; no render evaluation/build/sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/lights/ray-policy/set", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ActorGuid": actor_guid,
        "ExpectedLabel": expected_label, "FieldName": field_name, "ExpectedValue": expected_value,
        "Value": value, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_local_light_exposure(actor_path: str, component_path: str) -> str:
    """Inspect authored inverse exposure blend/intensity/units/IES/mobility, no exposure or renderer evaluation."""
    return httpx.post(f"{app.BASE_URL}/lights/local-exposure/inspect", json={
        "ActorPath": actor_path, "ComponentPath": component_path
    }, timeout=180).text


@mcp.tool()
def set_local_light_exposure_blend(actor_path: str, component_path: str, actor_guid: str, expected_label: str,
                                    expected_value: float, value: float, confirm: bool = False, dry_run: bool = True) -> str:
    """Set native local-light InverseExposureBlend0..1 with exact current value/GUID/label guard.
    Preserves intensity/units/radius/IES/mobility; native editor events/readback, no brightness compensation.
    No exposure/render evaluation/build/render synchronization/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/lights/local-exposure/set", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ActorGuid": actor_guid,
        "ExpectedLabel": expected_label, "ExpectedValue": expected_value, "Value": value,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_lights_page(start: int = 0, count: int = 64, light_type: str = "All", actor_path: str = "") -> str:
    """Page loaded persistent current-world lights in component-path order1..128.
    Type All/Point/Spot/Rect/Directional/Custom, optional exact owner; GUID/label/dirty/native settings.
    Scene changes shift offsets; no rendering evaluation/build/capture/render sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/lights/inspect-page", json={
        "Start": start, "Count": count, "LightType": light_type, "ActorPath": actor_path
    }, timeout=180).text


@mcp.tool()
def inspect_sky_lights_page(start: int = 0, count: int = 64, actor_path: str = "") -> str:
    """Page loaded persistent current-world skylights in component-path order1..128 with optional exact owner.
    GUID/label/dirty/native settings; processed texture is not freshness proof, no capture/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/lights/sky/inspect-page", json={
        "Start": start, "Count": count, "ActorPath": actor_path
    }, timeout=180).text


@mcp.tool()
def inspect_sky_light_occlusion(actor_path: str, component_path: str) -> str:
    """Inspect native skylight DFAO/cloud-AO fields/bounds/tint bytes, no rendering support or output evaluation."""
    return httpx.post(f"{app.BASE_URL}/lights/sky/occlusion/inspect", json={
        "ActorPath": actor_path, "ComponentPath": component_path
    }, timeout=180).text


@mcp.tool()
def set_sky_light_occlusion(actor_path: str, component_path: str, actor_guid: str, expected_label: str,
                             field_name: str, expected_value: float, value: float,
                             confirm: bool = False, dry_run: bool = True) -> str:
    """Set inspected native skylight DFAO/cloud-AO scalar/flag/combine mode within reported bounds.
    OcclusionCombineMode0 Minimum/1 Multiply, DFAO max distance centimeters, cloud extent radius kilometers.
    Exact current value/GUID/label guards, full supported sibling/tint readback; inactive fields accepted.
    Callbacks may queue capture; no explicit processing/rendering evaluation/build/render sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/lights/sky/occlusion/set", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ActorGuid": actor_guid,
        "ExpectedLabel": expected_label, "FieldName": field_name, "ExpectedValue": expected_value,
        "Value": value, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_sky_light_occlusion_tint(actor_path: str, component_path: str, actor_guid: str, expected_label: str,
                                 expected_rgba_bytes: list[int], rgba_bytes: list[int],
                                 confirm: bool = False, dry_run: bool = True) -> str:
    """Set native OcclusionTint RGBA bytes0..255 with full current-byte/GUID/label guard.
    No color-space conversion; preserves occlusion policies/source/cubemap/intensity/mobility.
    Editor events/readback, no explicit capture processing/render evaluation/build/render sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/lights/sky/occlusion/tint", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ActorGuid": actor_guid,
        "ExpectedLabel": expected_label, "ExpectedColor": expected_rgba_bytes, "Color": rgba_bytes,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_sky_light_capture_policy(actor_path: str, component_path: str) -> str:
    """Inspect emissive-only/realtime capture and inherited ray/deep-shadow/contribution policy plus resolution.
    Resolution read-only; no capture processing/render evaluation/build/render sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/lights/sky/capture-policy/inspect", json={
        "ActorPath": actor_path, "ComponentPath": component_path
    }, timeout=180).text


@mcp.tool()
def set_sky_light_capture_policy(actor_path: str, component_path: str, actor_guid: str, expected_label: str,
                                  field_name: str, expected_value: float, value: float,
                                  confirm: bool = False, dry_run: bool = True) -> str:
    """Set inspected skylight bCaptureEmissiveOnly/bRealTimeCapture and inherited contribution/ray policy.
    Exact current/GUID/label guards, full supported sibling/source/cubemap/resolution/intensity readback.
    Native editability enforced; other inactive settings accepted, renderer/hardware support unverified.
    Resolution not editable here; no explicit capture processing/render evaluation/build/sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/lights/sky/capture-policy/set", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ActorGuid": actor_guid,
        "ExpectedLabel": expected_label, "FieldName": field_name, "ExpectedValue": expected_value,
        "Value": value, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


def set_sky_light_color(actor_path: str, component_path: str, actor_guid: str, expected_label: str,
                          expected_rgba_bytes: list[int], rgba_bytes: list[int],
                          confirm: bool = False, dry_run: bool = True) -> str:
    """Set skylight base LightColor RGBA bytes0..255 with full exact previous-byte/GUID/label guard.
    No color-space conversion; preserves hemisphere/occlusion colors/policy/source/intensity/mobility.
    Native editor transaction/events/readback, no explicit capture processing/render evaluation/build/sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/lights/sky/color", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ActorGuid": actor_guid,
        "ExpectedLabel": expected_label, "ExpectedColor": expected_rgba_bytes, "Color": rgba_bytes,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_light_world_influence(actor_path: str, component_path: str) -> str:
    """Inspect light/skylight editor bAffectsWorld gate plus visibility/registration/render-state metadata.
    Distinct from visibility; no rendered-result proof or build/capture/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/lights/world-influence/inspect", json={
        "ActorPath": actor_path, "ComponentPath": component_path
    }, timeout=180).text


@mcp.tool()
def set_light_world_influence(actor_path: str, component_path: str, actor_guid: str, expected_label: str,
                                expected_affects_world: bool, affects_world: bool,
                                confirm: bool = False, dry_run: bool = True) -> str:
    """Edit light/skylight bAffectsWorld with exact flag/GUID/label guard; can unbuild baked lighting.
    Retains visibility/intensity/color/mobility/shadow flags; native callbacks can recreate scene resources/queue capture.
    Component retained, no lighting build/explicit capture processing/render sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/lights/world-influence/set", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ActorGuid": actor_guid,
        "ExpectedLabel": expected_label, "bExpectedValue": expected_affects_world, "bValue": affects_world,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_height_fog_page(start: int = 0, count: int = 64, actor_path: str = "") -> str:
    """Page loaded persistent current-world UExponentialHeightFogComponent components in path order1..128.
    Optional exact owner filter; native settings/GUID/label/level/dirty, offsets shift with scene changes.
    No renderer evaluation/capture/build/render synchronization/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/fog/inspect-page", json={
        "Start": start, "Count": count, "ActorPath": actor_path
    }, timeout=180).text


@mcp.tool()
def inspect_local_fog_page(start: int = 0, count: int = 64, actor_path: str = "") -> str:
    """Page loaded persistent current-world ULocalFogVolumeComponent components in path order1..128.
    Optional exact owner filter; native settings/GUID/label/level/dirty, offsets shift with scene changes.
    No renderer evaluation/capture/build/render synchronization/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/fog/local/inspect-page", json={
        "Start": start, "Count": count, "ActorPath": actor_path
    }, timeout=180).text


@mcp.tool()
def inspect_volumetric_clouds_page(start: int = 0, count: int = 64, actor_path: str = "") -> str:
    """Page loaded persistent current-world UVolumetricCloudComponent components in path order1..128.
    Optional exact owner filter; native settings/GUID/label/level/dirty, offsets shift with scene changes.
    No renderer evaluation/capture/build/render synchronization/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/clouds/inspect-page", json={
        "Start": start, "Count": count, "ActorPath": actor_path
    }, timeout=180).text


@mcp.tool()
def inspect_sky_atmospheres_page(start: int = 0, count: int = 64, actor_path: str = "") -> str:
    """Page loaded persistent current-world USkyAtmosphereComponent components in path order1..128.
    Optional exact owner filter; native settings/GUID/label/level/dirty, offsets shift with scene changes.
    No renderer evaluation/capture/build/render synchronization/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/atmosphere/inspect-page", json={
        "Start": start, "Count": count, "ActorPath": actor_path
    }, timeout=180).text


@mcp.tool()
def inspect_decals_page(start: int = 0, count: int = 64, actor_path: str = "") -> str:
    """Page native loaded persistent current-world decals1..128, path sorted/optional owner filter.
    Authored material/size/color/render-fade settings/GUID/label/dirty; no timer/renderer evaluation/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/decals/inspect-page", json={
        "Start": start, "Count": count, "ActorPath": actor_path
    }, timeout=180).text


@mcp.tool()
def set_decal_setting(actor_path: str, component_path: str, actor_guid: str, expected_label: str,
                        field_name: str, expected_value: float, value: float,
                        confirm: bool = False, dry_run: bool = True) -> str:
    """Set SortOrder int32, FadeScreenSize0..1, FadeStartDelay/FadeDuration/FadeInStartDelay/FadeInDuration0..100000s,
    bDestroyOwnerAfterFade0..1. Exact current/GUID/label guard, native transaction/events/full sibling readback.
    Authored fade values only, no timers/simulation started; destroy flag can delete owner in later gameplay.
    No current deletion/render evaluation/build/render sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/decals/setting", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ActorGuid": actor_guid,
        "ExpectedLabel": expected_label, "FieldName": field_name, "ExpectedValue": expected_value,
        "Value": value, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


def set_decal_local_size(actor_path: str, component_path: str, actor_guid: str, expected_label: str,
                           expected_size: list[float], size: list[float],
                           confirm: bool = False, dry_run: bool = True) -> str:
    """Set native DecalSize XYZ0.001..1e6 with exact current triple/GUID/label guard, excludes component scale.
    Preserves material/color/render-fade/transform/visibility/mobility, native events/readback/render-state dirty.
    No timers/material edits/render evaluation/build/render synchronization/load/save.
    """
    if len(expected_size) != 3 or len(size) != 3:
        raise ValueError("Sizes require XYZ triples")
    return httpx.post(f"{app.BASE_URL}/decals/appearance", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ActorGuid": actor_guid,
        "ExpectedLabel": expected_label, "FieldName": "DecalSize",
        "ExpectedSize": dict(zip(("X", "Y", "Z"), expected_size)), "Size": dict(zip(("X", "Y", "Z"), size)),
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


def set_decal_linear_color(actor_path: str, component_path: str, actor_guid: str, expected_label: str,
                             expected_rgba: list[float], rgba: list[float],
                             confirm: bool = False, dry_run: bool = True) -> str:
    """Set DecalColor linear RGBA0..1000 with full exact previous color/GUID/label guard, no sRGB conversion.
    Consumed by material Decal Color node; preserves size/material/render-fade/transform/visibility/mobility.
    Native setter/events/readback; no shader output evaluation/build/render sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/decals/appearance", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ActorGuid": actor_guid,
        "ExpectedLabel": expected_label, "FieldName": "DecalColor", "ExpectedColor": expected_rgba, "Color": rgba,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


def set_decal_visible(actor_path: str, component_path: str, actor_guid: str, expected_label: str,
                        expected_visible: bool, visible: bool, confirm: bool = False, dry_run: bool = True) -> str:
    """Set decal component visibility with exact flag/GUID/label guard, no child visibility propagation.
    Preserves transform/size/color/material/render-fade settings; no render evaluation/build/sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/decals/placement", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ActorGuid": actor_guid,
        "ExpectedLabel": expected_label, "FieldName": "Visible", "bExpectedVisible": expected_visible,
        "bVisible": visible, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


def set_decal_world_transform(actor_path: str, component_path: str, actor_guid: str, expected_label: str,
                                expected_transform: dict, transform: dict,
                                confirm: bool = False, dry_run: bool = True) -> str:
    """Set unattached decal world FTransform with full current transform/GUID/label guard.
    FTransform uses Translation XYZ/Rotation XYZW normalized quaternion/Scale3D XYZ; location+/-1e9,
    scale abs0.001..1000, negative allowed. Native children follow, root component moves owning actor.
    Preserves local DecalSize/other authoring; no sweep/timers/render evaluation/build/sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/decals/placement", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ActorGuid": actor_guid,
        "ExpectedLabel": expected_label, "FieldName": "Transform", "ExpectedTransform": expected_transform,
        "Transform": transform, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def create_decal_actor(world_path: str, name: str, location: list[float], confirm: bool = False, dry_run: bool = True) -> str:
    """Create exact native decal actor/default root in exact ordinary unlocked persistent world.
    Unique alphanumeric-underscore name/location+/-1e9, zero actor rotation/unit scale/native defaults.
    Constructor/editor resources/PSO registration may run; no automatic material assignment/render proof/build/save.
    """
    if len(location) != 3:
        raise ValueError("Location requires XYZ triple")
    return httpx.post(f"{app.BASE_URL}/decals/create", json={
        "WorldPath": world_path, "Name": name, "Location": dict(zip(("X", "Y", "Z"), location)),
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def delete_decal_actor(world_path: str, actor_path: str, component_path: str, actor_guid: str, expected_label: str,
                          expected_material_path: str, confirm: bool = False, dry_run: bool = True) -> str:
    """Delete exact native persistent decal actor/root with world/GUID/label/material guards.
    Requires no attached parent/children or nonnative components; material asset retained.
    Native transaction/destruction/readback, external references not fully discovered; no render sync/build/save.
    """
    return httpx.post(f"{app.BASE_URL}/decals/delete", json={
        "WorldPath": world_path, "ActorPath": actor_path, "ComponentPath": component_path,
        "ActorGuid": actor_guid, "ExpectedLabel": expected_label, "ExpectedMaterialPath": expected_material_path,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_decal_receivers_page(start: int = 0, count: int = 64, actor_path: str = "", component_path: str = "") -> str:
    """Page loaded persistent current-world primitive receives-decals flags1..128/path sorted.
    Optional exact owner/component filters; flag does not prove projected overlap/material/renderer support.
    No material traversal/render evaluation/build/render sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/decals/receivers/inspect-page", json={
        "Start": start, "Count": count, "ActorPath": actor_path, "ComponentPath": component_path
    }, timeout=180).text


@mcp.tool()
def set_primitive_receives_decals(actor_path: str, component_path: str, actor_guid: str, expected_label: str,
                                   expected_receives_decals: bool, receives_decals: bool,
                                   confirm: bool = False, dry_run: bool = True) -> str:
    """Set primitive bReceivesDecals with exact current flag/GUID/label guard and native setter/readback.
    Preserves transform/attachment/visibility/mobility/cast-shadow settings; no material/projector edits.
    Not material compatibility/overlap/output proof; no render evaluation/build/render sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/decals/receivers/set", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ActorGuid": actor_guid,
        "ExpectedLabel": expected_label, "bExpectedReceivesDecals": expected_receives_decals,
        "bReceivesDecals": receives_decals, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_decal_mobility(actor_path: str, component_path: str, actor_guid: str, expected_label: str,
                         expected_mobility: int, mobility: int, expected_direct_child_count: int,
                         confirm: bool = False, dry_run: bool = True, expected_hierarchy: list[dict] | None = None) -> str:
    """Set native decal mobility0 Static/1 Stationary/2 Movable with current/GUID/label/direct-child-count guards.
    Movable propagates through up to256 descendants, including other actors; all affected components/owners transacted.
    Optional full hierarchy from inspect_decal_mobility rejects same-count attachment/mobility changes.
    Compatible parent required; hierarchy/authoring readback, no render evaluation/build/render sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/decals/mobility", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "ActorGuid": actor_guid,
        "ExpectedLabel": expected_label, "ExpectedValue": expected_mobility, "Value": mobility,
        "ExpectedHierarchyPaths": [n["component_path"] for n in expected_hierarchy or []],
        "ExpectedHierarchyParents": [n["parent_path"] for n in expected_hierarchy or []],
        "ExpectedHierarchyMobilities": [n["mobility"] for n in expected_hierarchy or []],
        "bRequireHierarchySnapshot": expected_hierarchy is not None,
        "ExpectedChildCount": expected_direct_child_count, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_decal_mobility(actor_path: str, component_path: str) -> str:
    """Inspect root-plus-descendant native attachment mobility hierarchy<=256 in breadth-first order.
    Return hierarchy may be passed to set_decal_mobility(expected_hierarchy=...) as full ordered stale guard.
    Other actors/editor visualization included, no reregistration/rendering/build/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/decals/mobility/inspect", json={
        "ActorPath": actor_path, "ComponentPath": component_path
    }, timeout=180).text


# Tools listed to clients. Each picks one of the functions above with its variant argument.
set_light_shaft_appearance = merged_tool("set_light_shaft_appearance", {
    "set_light_shaft_bloom_tint": set_light_shaft_bloom_tint,
    "set_directional_light_shaft_override_direction": set_directional_light_shaft_override_direction,
})
set_decal_appearance = merged_tool("set_decal_appearance", {
    "set_decal_local_size": set_decal_local_size,
    "set_decal_linear_color": set_decal_linear_color,
})
set_decal_placement = merged_tool("set_decal_placement", {
    "set_decal_visible": set_decal_visible,
    "set_decal_world_transform": set_decal_world_transform,
})
set_post_process_setting = merged_tool("set_post_process_setting", {
    "scalar": set_post_process_setting_scalar,
    "bool": set_post_process_setting_bool,
    "enum": set_post_process_setting_enum,
    "vector": set_post_process_setting_vector,
    "integer": set_post_process_setting_integer,
})
reset_post_process_setting = merged_tool("reset_post_process_setting", {
    "scalar": reset_post_process_setting_scalar,
    "integer": reset_post_process_setting_integer,
    "bool": reset_post_process_setting_bool,
    "vector": reset_post_process_setting_vector,
    "enum": reset_post_process_setting_enum,
})
set_planar_reflection = merged_tool("set_planar_reflection", {
    "scalar": set_planar_reflection_scalar,
    "bool": set_planar_reflection_bool,
})
set_light = merged_tool("set_light", {
    "scalar": set_light_scalar,
    "bool": set_light_bool,
})
set_sky_light = merged_tool("set_sky_light", {
    "scalar": set_sky_light_scalar,
    "bool": set_sky_light_bool,
    "color": set_sky_light_color,
})
set_height_fog = merged_tool("set_height_fog", {
    "scalar": set_height_fog_scalar,
    "color": set_height_fog_color,
})
set_local_fog = merged_tool("set_local_fog", {
    "scalar": set_local_fog_scalar,
    "color": set_local_fog_color,
})
set_volumetric_cloud = merged_tool("set_volumetric_cloud", {
    "scalar": set_volumetric_cloud_scalar,
    "bool": set_volumetric_cloud_bool,
})
set_sky_atmosphere = merged_tool("set_sky_atmosphere", {
    "scalar": set_sky_atmosphere_scalar,
    "bool": set_sky_atmosphere_bool,
    "color": set_sky_atmosphere_color,
})
