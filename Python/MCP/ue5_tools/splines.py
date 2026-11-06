"""Splines and spline meshes."""
import httpx

from . import app
from .app import mcp


@mcp.tool()
def inspect_world_spline_components() -> str:
    """Discover up to128 loaded stopped-editor-world spline components/subclasses.
    Actor/component identities, point count/closed-loop/registration; read-only.
    Global object iteration/custom getter work unbounded, no update/save/mutation.
    """
    return httpx.post(f"{app.BASE_URL}/splines/components/inspect", json={}, timeout=60).text


@mcp.tool()
def inspect_spline_points(actor_path: str, component_path: str, point_start: int = 0,
                           point_count: int = 64) -> str:
    """Read native spline points in local coordinates, pages1..128.
    Position/arrive-leave tangents/scale/rotation Euler roll-pitch-yaw degrees,
    input key/type ordinal, continuation fields. Nonfinite values null, indices
    may change after edits/construction scripts. Current identities/stopped editor.
    """
    return httpx.post(f"{app.BASE_URL}/splines/points/inspect", json={
        "ActorPath": actor_path, "ComponentPath": component_path,
        "PointStart": point_start, "PointCount": point_count
    }, timeout=60).text


@mcp.tool()
def set_spline_point_position(actor_path: str, component_path: str, point_index: int,
                               expected_point_count: int, expected_position: list[float],
                               position: list[float], confirm: bool = False, dry_run: bool = False) -> str:
    """Move inspected spline point in local coordinates with exact count/position guard.
    <=4096 points/finite XYZ +/-1e9, native spline update/component undo/dry-run.
    Derived tangents/reparameterization may change; no explicit construction rerun.
    Construction-generated data may overwrite later; no map save, undo unverified.
    """
    if len(expected_position) != 3 or len(position) != 3:
        raise ValueError("Expected and new positions require XYZ triples")
    return httpx.post(f"{app.BASE_URL}/splines/points/position", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "PointIndex": point_index,
        "ExpectedPointCount": expected_point_count,
        "ExpectedPosition": dict(zip(("X", "Y", "Z"), expected_position)),
        "Position": dict(zip(("X", "Y", "Z"), position)), "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_spline_point_type(actor_path: str, component_path: str, point_index: int,
                           expected_point_count: int, expected_type: int, point_type: str = "Curve",
                           confirm: bool = False, dry_run: bool = False) -> str:
    """Set Linear/Curve/Constant/CurveClamped/CurveCustomTangent point type.
    Exact inspected point count/type ordinal guards, <=4096 points, native update/
    component undo/readback/dry-run. Derived tangents/reparameterization may change;
    construction scripts may overwrite later, no explicit construction rerun/save.
    """
    return httpx.post(f"{app.BASE_URL}/splines/points/type", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "PointIndex": point_index,
        "ExpectedPointCount": expected_point_count, "ExpectedPointType": expected_type,
        "PointType": point_type, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_spline_point_tangents(actor_path: str, component_path: str, point_index: int,
        expected_point_count: int, expected_type: int, expected_arrive: list[float],
        expected_leave: list[float], arrive: list[float], leave: list[float],
        confirm: bool = False, dry_run: bool = False) -> str:
    """Set local arrive/leave tangents; native setter switches to CurveCustomTangent.
    Count/current tangent/type guards, finite XYZ +/-1e9, <=4096 points. Native
    update/component undo/readback/dry-run; construction may overwrite later, no save.
    """
    if any(len(v) != 3 for v in (expected_arrive, expected_leave, arrive, leave)):
        raise ValueError("All tangents require XYZ triples")
    return httpx.post(f"{app.BASE_URL}/splines/points/tangents", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "PointIndex": point_index,
        "ExpectedPointCount": expected_point_count, "ExpectedPointType": expected_type,
        "ExpectedArriveTangent": dict(zip(("X", "Y", "Z"), expected_arrive)),
        "ExpectedLeaveTangent": dict(zip(("X", "Y", "Z"), expected_leave)),
        "ArriveTangent": dict(zip(("X", "Y", "Z"), arrive)),
        "LeaveTangent": dict(zip(("X", "Y", "Z"), leave)),
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_spline_closed_loop(actor_path: str, component_path: str, expected_point_count: int,
                            expected_closed_loop: bool, closed_loop: bool,
                            confirm: bool = False, dry_run: bool = False) -> str:
    """Open/close spline with current count/loop-state guards and native update.
    <=4096 points, closing requires >=2. Component undo/readback/dry-run; derived
    tangents/reparameterization may change. Construction may overwrite later;
    no explicit construction rerun/map save, runtime shape unverified.
    """
    return httpx.post(f"{app.BASE_URL}/splines/closed-loop", json={
        "ActorPath": actor_path, "ComponentPath": component_path,
        "ExpectedPointCount": expected_point_count, "bExpectedClosedLoop": expected_closed_loop,
        "bClosedLoop": closed_loop, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def insert_spline_point(actor_path: str, component_path: str, point_index: int,
                         expected_point_count: int, expected_anchor_position: list[float],
                         position: list[float], confirm: bool = False, dry_run: bool = False) -> str:
    """Insert local point at index0..count; index=count appends, resulting count<=4096.
    Anchor is existing insertion-index point or last point when appending; empty
    spline has no anchor (send0,0,0). Native defaults initialize other properties;
    indices/input keys/tangents may shift. Component undo/readback/dry-run/no save.
    """
    if len(expected_anchor_position) != 3 or len(position) != 3:
        raise ValueError("Anchor/new positions require XYZ triples")
    return httpx.post(f"{app.BASE_URL}/splines/points/insert", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "PointIndex": point_index,
        "ExpectedPointCount": expected_point_count,
        "ExpectedPosition": dict(zip(("X", "Y", "Z"), expected_anchor_position)),
        "Position": dict(zip(("X", "Y", "Z"), position)), "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def remove_spline_point(actor_path: str, component_path: str, point_index: int,
                         expected_point_count: int, expected_position: list[float],
                         confirm: bool = False, dry_run: bool = False) -> str:
    """Remove inspected spline point with count/current local position guards.
    <=4096 points, native reindexing/input-key/tangent update. Closed spline must
    retain>=2 points; open it first to remove further. Component undo/count readback/
    dry-run; construction may overwrite later, no explicit construction rerun/save.
    """
    if len(expected_position) != 3:
        raise ValueError("Expected position requires XYZ triple")
    return httpx.post(f"{app.BASE_URL}/splines/points/remove", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "PointIndex": point_index,
        "ExpectedPointCount": expected_point_count,
        "ExpectedPosition": dict(zip(("X", "Y", "Z"), expected_position)),
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_spline_point_scale(actor_path: str, component_path: str, point_index: int,
                            expected_point_count: int, expected_scale: list[float],
                            scale: list[float], confirm: bool = False, dry_run: bool = False) -> str:
    """Set point scale XYZ +/-1000, including zero/negative values, with current guards.
    <=4096 points/count-current scale check/native update/component undo/readback.
    No dependent spline-mesh rebuild or construction rerun/save explicitly requested.
    """
    if len(expected_scale) != 3 or len(scale) != 3:
        raise ValueError("Expected/new scales require XYZ triples")
    return httpx.post(f"{app.BASE_URL}/splines/points/scale", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "PointIndex": point_index,
        "ExpectedPointCount": expected_point_count, "ExpectedScale": dict(zip(("X", "Y", "Z"), expected_scale)),
        "Scale": dict(zip(("X", "Y", "Z"), scale)), "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_spline_point_rotation(actor_path: str, component_path: str, point_index: int,
        expected_point_count: int, expected_quaternion: list[float], quaternion: list[float],
        confirm: bool = False, dry_run: bool = False) -> str:
    """Set normalized local XYZW quaternion with inspected count/orientation guards.
    Native setter aligns up vector/rotates tangents preserving magnitudes, switches
    to custom tangent. Nonzero leave tangent required; readback tolerance1e-4.
    Component transaction/update/dry-run; no construction rerun/map save.
    """
    if len(expected_quaternion) != 4 or len(quaternion) != 4:
        raise ValueError("Expected/new quaternions require XYZW values")
    return httpx.post(f"{app.BASE_URL}/splines/points/rotation", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "PointIndex": point_index,
        "ExpectedPointCount": expected_point_count,
        "ExpectedRotation": dict(zip(("X", "Y", "Z", "W"), expected_quaternion)),
        "Rotation": dict(zip(("X", "Y", "Z", "W"), quaternion)),
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def sample_spline_by_distance(actor_path: str, component_path: str, distance_start: float = 0,
                               distance_end: float = -1, sample_count: int = 16, space: str = "Local") -> str:
    """Sample native distance table at1..128 equally spaced inclusive distances.
    End-1 uses native length; no wrapping, one sample=start. Local/World position,
    tangent/quaternion; scale remains authored point scale. Requires2..4096 points.
    Native reparameterization/scale semantics are not exact world arc-length proof.
    Nonfinite samples null; current identities/stopped editor/read-only/no update.
    """
    return httpx.post(f"{app.BASE_URL}/splines/sample-distance", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "DistanceStart": distance_start,
        "DistanceEnd": distance_end, "SampleCount": sample_count, "Space": space
    }, timeout=60).text


@mcp.tool()
def add_spline_actor_component(actor_path: str, name: str, confirm: bool = False,
                                dry_run: bool = False) -> str:
    """Create/register native instance Spline component on existing persistent actor.
    Unique identifier name1..128/<=64 actor spline components; native default points.
    Attaches to actor root or becomes root. Actor/component transaction/readback/
    dry-run, native registration callbacks may run. No map save/point edits.
    """
    return httpx.post(f"{app.BASE_URL}/splines/components/add", json={
        "ActorPath": actor_path, "Name": name, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def clear_spline_points(actor_path: str, component_path: str, expected_point_count: int,
                         confirm: bool = False, dry_run: bool = False) -> str:
    """Clear all spline points using inspected count<=4096 guard/native update.
    Empty no-op, native loop flag not explicitly changed. Component transaction/
    zero-count readback/dry-run. Count is not full content revision; construction
    may overwrite later, no explicit construction rerun/save.
    """
    return httpx.post(f"{app.BASE_URL}/splines/points/clear", json={
        "ActorPath": actor_path, "ComponentPath": component_path,
        "ExpectedPointCount": expected_point_count, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def find_spline_closest_point(actor_path: str, component_path: str, world_position: list[float]) -> str:
    """Native closest input-key query and world frame/distance-table readback.
    Requires2..4096 points/finite XYZ +/-1e9. Returns input key/distance along spline/
    query distance/world position-tangent-quaternion. Native approximation not global
    nearest/exact world arc-length proof; current identities/stopped editor/read-only.
    """
    if len(world_position) != 3:
        raise ValueError("World position requires XYZ triple")
    return httpx.post(f"{app.BASE_URL}/splines/closest-point", json={
        "ActorPath": actor_path, "ComponentPath": component_path,
        "QueryPosition": dict(zip(("X", "Y", "Z"), world_position))
    }, timeout=60).text


@mcp.tool()
def replace_spline_point_positions(actor_path: str, component_path: str, expected_point_count: int,
                                     positions: list[list[float]], confirm: bool = False,
                                     dry_run: bool = False) -> str:
    """Replace all spline positions0..4096, reset native point properties/metadata.
    Positions local finite XYZ +/-1e9, closed spline requires>=2. Same positions
    still reset keys/type/tangents/rotation/scale. Count guard is not full revision.
    Component/metadata transactions/native update/position readback/dry-run; no save.
    """
    if len(positions) > 4096 or any(len(v) != 3 for v in positions):
        raise ValueError("Up to4096 XYZ point positions required")
    return httpx.post(f"{app.BASE_URL}/splines/points/replace", json={
        "ActorPath": actor_path, "ComponentPath": component_path,
        "ExpectedPointCount": expected_point_count,
        "Positions": [dict(zip(("X", "Y", "Z"), v)) for v in positions],
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_spline_settings(actor_path: str, component_path: str) -> str:
    """Read spline duration/reparameterization steps/stationary endpoints/local up.
    Point/segment/loop and metadata availability; current identities/stopped editor.
    Native configuration is no table accuracy/freshness proof, no rebuild/mutation.
    """
    return httpx.post(f"{app.BASE_URL}/splines/settings/inspect", json={
        "ActorPath": actor_path, "ComponentPath": component_path
    }, timeout=60).text


@mcp.tool()
def set_spline_setting(actor_path: str, component_path: str, expected_point_count: int,
                         field: str, expected_value: float, scalar_value: float = 0,
                         bool_value: bool = False, confirm: bool = False, dry_run: bool = False) -> str:
    """Set Duration(>0<=1e6), ReparamStepsPerSegment(integer4..100), StationaryEndpoints(bool).
    Expected scalar value guards current field; use0/1 for expected bool. Stationary
    applies only open spline. Count<=4096/native update/component-metadata transaction/
    readback/dry-run; derived tables/tangents may change, no construction rerun/save.
    """
    return httpx.post(f"{app.BASE_URL}/splines/settings", json={
        "ActorPath": actor_path, "ComponentPath": component_path,
        "ExpectedPointCount": expected_point_count, "FieldName": field,
        "ExpectedScalarValue": expected_value, "ScalarValue": scalar_value,
        "bBoolValue": bool_value, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_spline_default_up_vector(actor_path: str, component_path: str, expected_point_count: int,
                                  expected_up: list[float], up: list[float],
                                  confirm: bool = False, dry_run: bool = False) -> str:
    """Set normalized local default up vector with inspected count/current vector guards.
    Native update broadcasts OnSplineChanged; listeners may rebuild world state.
    Component/metadata transaction/readback/dry-run, no explicit map save.
    """
    if len(expected_up) != 3 or len(up) != 3:
        raise ValueError("Expected/new up vectors require XYZ triples")
    return httpx.post(f"{app.BASE_URL}/splines/default-up", json={
        "ActorPath": actor_path, "ComponentPath": component_path,
        "ExpectedPointCount": expected_point_count, "ExpectedUpVector": dict(zip(("X", "Y", "Z"), expected_up)),
        "UpVector": dict(zip(("X", "Y", "Z"), up)), "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def sample_spline_by_time(actor_path: str, component_path: str, time_start: float = 0,
                           time_end: float = -1, sample_count: int = 16, space: str = "Local",
                           constant_velocity: bool = False) -> str:
    """Sample1..128 times within0..authored duration; end-1 uses duration.
    Native constant-velocity distance table or input-key timing, inclusive endpoints/
    single=start/no wrapping. Local/World position-tangent-quaternion/authored scale.
    Constant velocity not exact world-speed proof under scale; read-only/no update.
    """
    return httpx.post(f"{app.BASE_URL}/splines/sample-time", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "TimeStart": time_start,
        "TimeEnd": time_end, "SampleCount": sample_count, "Space": space,
        "bConstantVelocity": constant_velocity
    }, timeout=60).text


@mcp.tool()
def inspect_world_spline_mesh_components() -> str:
    """Discover up to128 loaded current editor-world spline mesh components.
    Actor/component/mesh identities, local endpoint-tangents/scales, rolls radians,
    native forward-axis ordinal. No inferred source spline/deformed vertex sampling.
    Nonfinite values null; read-only/no mesh-collision update/load/save/mutation.
    """
    return httpx.post(f"{app.BASE_URL}/splines/meshes/inspect", json={}, timeout=60).text


@mcp.tool()
def set_spline_mesh_endpoints(actor_path: str, component_path: str, asset_path: str,
                              expected_start_position: list[float], expected_end_position: list[float],
                              expected_start_tangent: list[float], expected_end_tangent: list[float],
                              start_position: list[float], end_position: list[float],
                              start_tangent: list[float], end_tangent: list[float],
                              confirm: bool = False, dry_run: bool = False) -> str:
    """Set component-local spline mesh endpoints/tangents together, with inspected asset/four-vector guards.
    XYZ triples finite within +/-1e9; native render/collision update on changes.
    Transaction/dry-run/no-op support; cooking/undo/persistence unverified, no save.
    """
    vectors = {
        "ExpectedStartPosition": expected_start_position, "ExpectedEndPosition": expected_end_position,
        "ExpectedStartTangent": expected_start_tangent, "ExpectedEndTangent": expected_end_tangent,
        "StartPosition": start_position, "EndPosition": end_position,
        "StartTangent": start_tangent, "EndTangent": end_tangent,
    }
    if any(len(v) != 3 for v in vectors.values()):
        raise ValueError("All expected/new endpoint and tangent vectors require XYZ triples")
    payload = {key: dict(zip(("X", "Y", "Z"), value)) for key, value in vectors.items()}
    payload.update(ActorPath=actor_path, ComponentPath=component_path, AssetPath=asset_path,
                   bConfirm=confirm, bDryRun=dry_run)
    return httpx.post(f"{app.BASE_URL}/splines/meshes/endpoints", json=payload, timeout=180).text


@mcp.tool()
def set_spline_mesh_scales(actor_path: str, component_path: str, asset_path: str,
                           expected_start_scale: list[float], expected_end_scale: list[float],
                           start_scale: list[float], end_scale: list[float],
                           confirm: bool = False, dry_run: bool = False) -> str:
    """Set local cross-section XY scale pairs with inspected scale/asset identity guards.
    Finite +/-1000, zero/negative allowed; native render/collision update on changes.
    Transaction/dry-run/no-op, no save; cooking/undo/persistence unverified.
    """
    vectors = {"ExpectedStartScale": expected_start_scale, "ExpectedEndScale": expected_end_scale,
               "StartScale": start_scale, "EndScale": end_scale}
    if any(len(v) != 2 for v in vectors.values()):
        raise ValueError("Expected/new cross-section scales require XY pairs")
    payload = {key: dict(zip(("X", "Y"), value)) for key, value in vectors.items()}
    payload.update(ActorPath=actor_path, ComponentPath=component_path, AssetPath=asset_path,
                   bConfirm=confirm, bDryRun=dry_run)
    return httpx.post(f"{app.BASE_URL}/splines/meshes/scales", json=payload, timeout=180).text


@mcp.tool()
def set_spline_mesh_rolls(actor_path: str, component_path: str, asset_path: str,
                          expected_start_roll: float, expected_end_roll: float,
                          start_roll: float, end_roll: float,
                          confirm: bool = False, dry_run: bool = False) -> str:
    """Set start/end roll in radians with inspected exact roll/asset identity guards.
    Finite +/-1000 radians; requested values use native float precision.
    Transaction/dry-run/no-op and explicit render/collision update, no save.
    Cooking/undo/persistence unverified; construction may overwrite edits.
    """
    return httpx.post(f"{app.BASE_URL}/splines/meshes/rolls", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "AssetPath": asset_path,
        "ExpectedStartRoll": expected_start_roll, "ExpectedEndRoll": expected_end_roll,
        "StartRoll": start_roll, "EndRoll": end_roll, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_spline_mesh_forward_axis(actor_path: str, component_path: str, asset_path: str,
                                 expected_forward_axis: int, forward_axis: str,
                                 confirm: bool = False, dry_run: bool = False) -> str:
    """Set longitudinal mesh axis X/Y/Z with inspected native ordinal (0/1/2) guard.
    Requires current actor/component/noncompiling assigned mesh identity.
    Transaction/dry-run/no-op, explicit render/collision update, no save.
    Deformation, cooking, undo and persistence remain unverified.
    """
    return httpx.post(f"{app.BASE_URL}/splines/meshes/forward-axis", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "AssetPath": asset_path,
        "ExpectedForwardAxis": expected_forward_axis, "ForwardAxis": forward_axis,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_spline_mesh_up_direction(actor_path: str, component_path: str, asset_path: str,
                                 expected_up: list[float], up: list[float],
                                 confirm: bool = False, dry_run: bool = False) -> str:
    """Set normalized local spline mesh up direction with inspected vector/asset guards.
    Native normalization and explicit render/collision update; does not prove frame
    nonsingularity throughout the mesh. Transaction/dry-run/no-op, no save.
    Cooking/undo/persistence remain unverified.
    """
    if len(expected_up) != 3 or len(up) != 3:
        raise ValueError("Expected/new up directions require XYZ triples")
    return httpx.post(f"{app.BASE_URL}/splines/meshes/up-direction", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "AssetPath": asset_path,
        "ExpectedUpVector": dict(zip(("X", "Y", "Z"), expected_up)),
        "UpVector": dict(zip(("X", "Y", "Z"), up)), "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_spline_mesh_offsets(actor_path: str, component_path: str, asset_path: str,
                           expected_start_offset: list[float], expected_end_offset: list[float],
                           start_offset: list[float], end_offset: list[float],
                           confirm: bool = False, dry_run: bool = False) -> str:
    """Set local cross-section XY offset pairs with inspected offset/asset identity guards.
    Finite +/-1e9 local distances; native render/collision update on changes.
    Transaction/dry-run/no-op, no save; cooking/undo/persistence unverified.
    """
    vectors = {"ExpectedStartOffset": expected_start_offset, "ExpectedEndOffset": expected_end_offset,
               "StartOffset": start_offset, "EndOffset": end_offset}
    if any(len(v) != 2 for v in vectors.values()):
        raise ValueError("Expected/new cross-section offsets require XY pairs")
    payload = {key: dict(zip(("X", "Y"), value)) for key, value in vectors.items()}
    payload.update(ActorPath=actor_path, ComponentPath=component_path, AssetPath=asset_path,
                   bConfirm=confirm, bDryRun=dry_run)
    return httpx.post(f"{app.BASE_URL}/splines/meshes/offsets", json=payload, timeout=180).text


@mcp.tool()
def set_spline_mesh_boundaries(actor_path: str, component_path: str, asset_path: str,
                               expected_min: float, expected_max: float,
                               boundary_min: float, boundary_max: float,
                               confirm: bool = False, dry_run: bool = False) -> str:
    """Set spline mesh longitudinal bounds with inspected current min/max guards.
    Finite +/-1e9, native float precision; zero uses native automatic mesh bounds.
    Overrides may reverse mapping; no ordering constraint is imposed.
    Transaction/dry-run/no-op, native mesh update, no save; unverified.
    """
    return httpx.post(f"{app.BASE_URL}/splines/meshes/boundaries", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "AssetPath": asset_path,
        "ExpectedBoundaryMin": expected_min, "ExpectedBoundaryMax": expected_max,
        "BoundaryMin": boundary_min, "BoundaryMax": boundary_max,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def sample_spline_mesh_slices(actor_path: str, component_path: str, asset_path: str,
                              alpha_start: float = 0, alpha_end: float = 1,
                              sample_count: int = 16) -> str:
    """Read1..128 native local deformation slice transforms over ordered alpha0..1.
    Inclusive endpoints/single=start, quaternion XYZW/translation/scale.
    Native offset/roll/scale/up/axis semantics, not arc length or final vertices.
    Nonfinite channels null; no mesh update/load/save/mutation.
    """
    return httpx.post(f"{app.BASE_URL}/splines/meshes/sample-slices", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "AssetPath": asset_path,
        "AlphaStart": alpha_start, "AlphaEnd": alpha_end, "SampleCount": sample_count
    }, timeout=60).text


@mcp.tool()
def add_spline_mesh_actor_component(actor_path: str, name: str, asset_path: str,
                                    confirm: bool = False, dry_run: bool = False) -> str:
    """Create a native spline mesh instance component on an existing persistent actor.
    Unique name1..128 letters/digits/underscore, max64 spline meshes per actor;
    loaded persistent noncompiling static mesh required. Native deformation defaults,
    attaches to existing root or becomes root. Transaction/dry-run, no save.
    Registration/collision/undo/persistence unverified; no source spline association.
    """
    return httpx.post(f"{app.BASE_URL}/splines/meshes/add", json={
        "ActorPath": actor_path, "Name": name, "AssetPath": asset_path,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_spline_mesh_asset(actor_path: str, component_path: str, expected_asset_path: str,
                          new_asset_path: str, confirm: bool = False, dry_run: bool = False) -> str:
    """Assign a loaded persistent noncompiling mesh with inspected current asset guard.
    Existing deformation parameters retained; native bounds/material/collision may change.
    Transaction/dry-run/no-op, explicit UpdateMesh, no save. Undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/splines/meshes/asset", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "AssetPath": expected_asset_path,
        "NewAssetPath": new_asset_path, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_spline_mesh_smooth_interpolation(actor_path: str, component_path: str, asset_path: str,
                                         expected_enabled: bool, enabled: bool,
                                         confirm: bool = False, dry_run: bool = False) -> str:
    """Set native eased versus linear roll/scale/offset interpolation with current flag guard.
    Exact actor/component/noncompiling assigned asset identity; transaction/dry-run/no-op.
    Marks mesh dirty and updates native render/collision. No save; unverified.
    """
    return httpx.post(f"{app.BASE_URL}/splines/meshes/smooth-interpolation", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "AssetPath": asset_path,
        "bExpectedBoolValue": expected_enabled, "bBoolValue": enabled,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def remove_spline_mesh_actor_component(actor_path: str, component_path: str,
                                       expected_asset_path: str, confirm: bool = False,
                                       dry_run: bool = False) -> str:
    """Remove inspected actor instance spline mesh; nonroot/no attached children required.
    Expected asset empty means unassigned. Native transactional destruction/unregister,
    dry-run support/no save; references, undo and persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/splines/meshes/remove", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "AssetPath": expected_asset_path,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def fit_spline_mesh_to_segment(actor_path: str, component_path: str, asset_path: str,
                                source_actor_path: str, source_component_path: str,
                                expected_source_point_count: int, expected_source_closed_loop: bool, segment_index: int,
                                expected_start_position: list[float], expected_end_position: list[float],
                                expected_start_tangent: list[float], expected_end_tangent: list[float],
                                confirm: bool = False, dry_run: bool = False) -> str:
    """Fit existing mesh endpoints to source spline segment, including the closing segment.
    Source count/closed-state guards; samples current source geometry. Constant segments rejected.
    Converts world positions/tangents into target local coordinates; curved tangents
    scaled by native input-key span (including closing key), linear segments use endpoint delta. Does not copy
    roll/scale/up/offset or create a persistent association. Target four-vector stale
    guards, transaction/dry-run, no save; geometry/collision/undo unverified.
    """
    vectors = {"ExpectedStartPosition": expected_start_position, "ExpectedEndPosition": expected_end_position,
               "ExpectedStartTangent": expected_start_tangent, "ExpectedEndTangent": expected_end_tangent}
    if any(len(v) != 3 for v in vectors.values()):
        raise ValueError("Expected target positions/tangents require XYZ triples")
    payload = {key: dict(zip(("X", "Y", "Z"), value)) for key, value in vectors.items()}
    payload.update(ActorPath=actor_path, ComponentPath=component_path, AssetPath=asset_path,
                   SourceActorPath=source_actor_path, SourceComponentPath=source_component_path,
                   ExpectedSourcePointCount=expected_source_point_count, bExpectedClosedLoop=expected_source_closed_loop,
                   SegmentIndex=segment_index,
                   bConfirm=confirm, bDryRun=dry_run)
    return httpx.post(f"{app.BASE_URL}/splines/meshes/fit-segment", json=payload, timeout=180).text


@mcp.tool()
def inspect_spline_segments(actor_path: str, component_path: str, segment_start: int = 0,
                            segment_count: int = 64, space: str = "Local") -> str:
    """Read native segment pages1..128, Local/World, including closing-loop key span.
    Returns endpoints, raw derivatives and unit-interval Hermite tangents; linear
    uses endpoint delta, Constant has no continuous fit tangents. Fit flag checks
    interpolation/key span only. Nonfinite channels null; no update/save/mutation.
    """
    return httpx.post(f"{app.BASE_URL}/splines/segments/inspect", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "PointStart": segment_start,
        "PointCount": segment_count, "Space": space
    }, timeout=60).text


@mcp.tool()
def set_spline_closing_key(actor_path: str, component_path: str, expected_point_count: int,
                            expected_closing_key: float, closing_key: float,
                            confirm: bool = False, dry_run: bool = False) -> str:
    """Set closing parameter on an already closed spline with inspected count/key guards.
    Use closing segment end_key from segment inspection. Native float key must be
    greater than last point key, span<=1e6 and absolute value<=1e9.
    Transaction/update/readback/dry-run; callback/undo/persistence unverified, no save.
    Same effective key is no-op, preserving existing override policy.
    """
    return httpx.post(f"{app.BASE_URL}/splines/closing-key", json={
        "ActorPath": actor_path, "ComponentPath": component_path,
        "ExpectedPointCount": expected_point_count, "ExpectedScalarValue": expected_closing_key,
        "ScalarValue": closing_key, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def reset_spline_closing_key(actor_path: str, component_path: str, expected_point_count: int,
                              expected_closing_key: float, confirm: bool = False,
                              dry_run: bool = False) -> str:
    """Restore automatic closing key on an already closed spline with inspected count/key guards.
    Native SetClosedLoop(true) clears override and updates even if effective key
    already matches. Last key+1 must be representably greater in float precision.
    Transaction/dry-run/no save; callbacks/undo/persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/splines/closing-key/reset", json={
        "ActorPath": actor_path, "ComponentPath": component_path,
        "ExpectedPointCount": expected_point_count, "ExpectedScalarValue": expected_closing_key,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def remove_spline_actor_component(actor_path: str, component_path: str,
                                   expected_point_count: int, expected_closed_loop: bool,
                                   confirm: bool = False, dry_run: bool = False) -> str:
    """Remove inspected ordinary spline instance component; nonroot/no children required.
    Count<=4096/current loop-state guard; does not identify all point data revisions.
    Native transactional destruction/unregister with metadata, dry-run/no save.
    External references, undo recreation and persistence unverified.
    """
    return httpx.post(f"{app.BASE_URL}/splines/components/remove", json={
        "ActorPath": actor_path, "ComponentPath": component_path,
        "ExpectedPointCount": expected_point_count, "bExpectedClosedLoop": expected_closed_loop,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text
