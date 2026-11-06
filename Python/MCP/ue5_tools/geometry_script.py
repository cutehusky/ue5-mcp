"""Geometry Script meshes."""
import httpx

from . import app
from .app import mcp


@mcp.tool()
def inspect_geometry_script_world_meshes() -> str:
    """Inspect <=128 loaded current-world Dynamic Mesh components/native topology counts.
    Component/actor/mesh identities, vertex/triangle/edge counts, compactness and
    attribute flags. Stopped editor world; no mesh copy/operation/collision rebuild.
    """
    return httpx.post(f"{app.BASE_URL}/geometry-script/components/inspect", json={}, timeout=180).text


@mcp.tool()
def add_geometry_script_mesh_component(actor_path: str, component_name: str,
                                         confirm: bool = False, dry_run: bool = False) -> str:
    """Create/register empty Dynamic Mesh component on existing editor-world actor.
    Unique bounded name, <=64 dynamic mesh components, confirmed stopped PIE,
    transaction/ownership/registration readback. Attaches to root or becomes root.
    No map save or explicit geometry operation; callback/undo lifecycle unverified.
    """
    return httpx.post(f"{app.BASE_URL}/geometry-script/components", json={
        "ActorPath": actor_path, "Name": component_name,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def append_geometry_script_box(actor_path: str, component_path: str, mesh_path: str,
                                 dimensions: dict, transform: dict,
                                 origin: str = "Base", material_id: int = 0,
                                 flip_orientation: bool = False,
                                 confirm: bool = False, dry_run: bool = False) -> str:
    """Append native unsubdivided box to owned current-world Dynamic Mesh component.
    Dimensions XYZ positive<=1e6; transform Translation/Rotation/Scale3D bounded,
    quaternion normalized/nonzero scale. Base/Center origin, material0..255.
    <=100k mesh vertices/triangles, temporary-copy operation, native replacement
    command undo/readback. Callbacks may rebuild render/collision; no save.
    """
    if set(dimensions) != {"X", "Y", "Z"}:
        raise ValueError("dimensions requires X,Y,Z")
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/append-box", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "Dimensions": dimensions, "Transform": transform, "Origin": origin,
        "MaterialId": material_id, "bFlipOrientation": flip_orientation,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def append_geometry_script_sphere(actor_path: str, component_path: str, mesh_path: str,
                                    transform: dict, radius: float = 50,
                                    steps_phi: int = 10, steps_theta: int = 16,
                                    origin: str = "Center", material_id: int = 0,
                                    flip_orientation: bool = False,
                                    confirm: bool = False, dry_run: bool = False) -> str:
    """Append native latitude-longitude sphere on temporary mesh then commit with undo.
    Radius positive<=1e6/tessellation3..128, bounded normalized transform, material0..255.
    Current actor/component/mesh identities, <=100k input mesh vertices/triangles,
    native replacement command/count readback. No map save; callbacks may rebuild collision.
    """
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/append-sphere", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "Transform": transform, "Radius": radius, "StepsPhi": steps_phi,
        "StepsTheta": steps_theta, "Origin": origin, "MaterialId": material_id,
        "bFlipOrientation": flip_orientation, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def transform_geometry_script_mesh(actor_path: str, component_path: str, mesh_path: str,
                                      transform: dict, fix_negative_scale_orientation: bool = True,
                                      confirm: bool = False, dry_run: bool = False) -> str:
    """Transform existing component-local mesh on temporary copy, commit with native undo.
    Finite translation +/-1e9, scale +/-1000/nonzero, normalized quaternion;
    <=100k input vertices/triangles. Native unchanged topology-count readback.
    Current identities/confirmed stopped PIE; callbacks may rebuild render/collision, no save.
    """
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/transform", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "Transform": transform, "bFixNegativeScaleOrientation": fix_negative_scale_orientation,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def clear_geometry_script_mesh(actor_path: str, component_path: str, mesh_path: str,
                                 confirm: bool = False, dry_run: bool = False) -> str:
    """Clear geometry while retaining Dynamic Mesh component; native replacement undo.
    Current identities/confirmed stopped PIE, <=100k vertices/triangles copy budget,
    empty topology readback/no-op/dry-run. Render/collision callbacks may run;
    already empty geometry leaves empty attribute layers, no generator reset/map save.
    """
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/clear", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def recompute_geometry_script_normals(actor_path: str, component_path: str, mesh_path: str,
                                        angle_weighted: bool = True, area_weighted: bool = True,
                                        confirm: bool = False, dry_run: bool = False) -> str:
    """Recompute normals natively on staged copy, preserving native hard-edge sharing.
    Current mesh identities/confirmed stopped PIE, <=100k vertices/triangles,
    unchanged topology-count readback/native replacement undo. Render/collision
    callbacks may run; normal quality/visual result unverified, no map save.
    """
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/recompute-normals", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "bAngleWeighted": angle_weighted, "bAreaWeighted": area_weighted,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def split_geometry_script_normals(actor_path: str, component_path: str, mesh_path: str,
                                    opening_angle: float = 30, split_by_angle: bool = True,
                                    split_by_face_group: bool = False,
                                    angle_weighted: bool = True, area_weighted: bool = True,
                                    confirm: bool = False, dry_run: bool = False, polygroup_layer: int = -1) -> str:
    """Group layer -1(default) or existing extended0..7 for group-dependent operation.
    Generate native split normals on staged copy using angle0..180/default face groups.
    Current identities/confirmed stopped PIE, mesh copy budget/topology-count checks,
    native replacement undo. Normal quality/callbacks unverified; no map save.
    """
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/split-normals", json={
        "PolygroupLayerIndex": polygroup_layer, "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "OpeningAngle": opening_angle, "bSplitByOpeningAngle": split_by_angle,
        "bSplitByFaceGroup": split_by_face_group, "bAngleWeighted": angle_weighted,
        "bAreaWeighted": area_weighted, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def compute_geometry_script_tangents(actor_path: str, component_path: str, mesh_path: str,
                                       method: str = "FastMikkT", uv_layer: int = 0,
                                       confirm: bool = False, dry_run: bool = False) -> str:
    """Compute FastMikkT/PerTriangle/StandardMikkT tangents on staged mesh copy.
    Existing normal/selected UV0..7 overlays, bounded mesh/current identities,
    native tangent-overlay/count readback/replacement undo. Component rendering
    tangent mode unchanged; StandardMikkT platform fallback possible, no map save.
    """
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/compute-tangents", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "TangentType": method, "UVLayer": uv_layer,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def project_geometry_script_uvs(actor_path: str, component_path: str, mesh_path: str,
                                  transform: dict, projection: str = "Box", uv_layer: int = 0,
                                  min_island_triangles: int = 2,
                                  confirm: bool = False, dry_run: bool = False,
        selected_triangles: list[int] | None = None,
        expected_vertices: list[list[int]] | None = None) -> str:
    """Optional inspected face selection; empty retains native whole-mesh behavior.
    Shared UV elements/island processing may affect adjacent unselected faces.
    Project whole mesh UVs using native Box/Planar projection frame.
    Existing UV0..7, finite normalized bounded transform/nonzero scale, bounded mesh,
    current identities/confirmed stopped PIE. Staged copy/overlay-count readback/
    native replacement undo. Tangents/layout quality unverified; no map save.
    """
    selected_triangles = selected_triangles or []
    expected_vertices = expected_vertices or []
    if len(selected_triangles) > 256 or len(expected_vertices) != len(selected_triangles) or any(len(v) != 3 for v in expected_vertices):
        raise ValueError("Up to256 selected IDs and matching vertex triples required")
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/project-uvs", json={
        "SelectedTriangles": selected_triangles,
        "ExpectedSelectedTriangles": [dict(zip(("X", "Y", "Z"), v)) for v in expected_vertices],
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "Transform": transform, "Projection": projection, "UVLayer": uv_layer,
        "MinIslandTriangles": min_island_triangles, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_geometry_script_uv_channel_count(actor_path: str, component_path: str, mesh_path: str,
                                           count: int, confirm: bool = False,
                                           dry_run: bool = False) -> str:
    """Set native UV channel count1..8; reducing count discards removed channels.
    Current identities/confirmed stopped PIE, bounded staged mesh copy, native
    channel/topology-count readback/replacement undo/no-op. No map save.
    """
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/uv-channel-count", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "UVChannelCount": count, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def clear_geometry_script_uv_channel(actor_path: str, component_path: str, mesh_path: str,
                                       uv_layer: int = 0, confirm: bool = False,
                                       dry_run: bool = False) -> str:
    """Clear selected UV0..7 overlay elements without deleting channel/mesh topology.
    Existing channel/current mesh identities, bounded staged copy, native empty-overlay/
    topology/count readback/replacement undo/no-op. Confirmed stopped PIE, no map save.
    """
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/clear-uv-channel", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "UVLayer": uv_layer, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_geometry_script_topology(actor_path: str, component_path: str, mesh_path: str,
                                       vertex_start_id: int = 0, triangle_start_id: int = 0,
                                       id_span: int = 64) -> str:
    """Read native vertex positions/triangle vertex IDs over <=256-ID spans each.
    Current owned component/mesh identities, stopped editor world. Sparse ID holes
    omitted, nonfinite coordinates null; topology may change across requests.
    No copy, topology validation or mutation.
    """
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/topology", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "VertexStartId": vertex_start_id, "TriangleStartId": triangle_start_id, "IdSpan": id_span
    }, timeout=180).text


@mcp.tool()
def validate_geometry_script_mesh(actor_path: str, component_path: str, mesh_path: str,
                                    allow_nonmanifold_vertices: bool = False,
                                    allow_reversed_adjacent_faces: bool = False) -> str:
    """Native internal mesh validity/finite-position diagnostics on bounded copy.
    <=100k vertices/triangles/max IDs200k, current identities/stopped editor world.
    ReturnOnly mode, closed state only when structurally valid. No repair,
    self-intersection/degenerate-area/UV quality or rendering proof.
    """
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/validate", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "bAllowNonManifoldVertices": allow_nonmanifold_vertices,
        "bAllowReversedAdjacentFaces": allow_reversed_adjacent_faces
    }, timeout=180).text


@mcp.tool()
def copy_geometry_script_mesh(actor_path: str, component_path: str, mesh_path: str,
                                source_actor_path: str, source_component_path: str,
                                source_mesh_path: str, confirm: bool = False,
                                dry_run: bool = False) -> str:
    """Copy full native local mesh geometry/attributes between current-world components.
    Separate source/destination identities, bounded mesh copies, replacement undo/
    count readback. Source unchanged; actor transforms/material slots not copied.
    Confirmed stopped PIE, no map save; destination render/collision callbacks may run.
    """
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/copy", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "SourceActorPath": source_actor_path, "SourceComponentPath": source_component_path,
        "SourceMeshPath": source_mesh_path, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def append_geometry_script_cylinder(actor_path: str, component_path: str, mesh_path: str,
                                      transform: dict, radius: float = 50, height: float = 100,
                                      radial_steps: int = 16, height_steps: int = 0,
                                      capped: bool = True, origin: str = "Base",
                                      material_id: int = 0, flip_orientation: bool = False,
                                      confirm: bool = False, dry_run: bool = False) -> str:
    """Append native cylinder to staged mesh; radius/height positive<=1e6.
    Radial3..128/height0..128 steps, caps/origin/material/orientation controls,
    bounded normalized transform/current identities/copy budget/native replacement
    undo/count readback. Confirmed stopped PIE, no map save.
    """
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/append-cylinder", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "Transform": transform, "Radius": radius, "Height": height,
        "RadialSteps": radial_steps, "HeightSteps": height_steps, "bCapped": capped,
        "Origin": origin, "MaterialId": material_id, "bFlipOrientation": flip_orientation,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_geometry_script_vertex_position(actor_path: str, component_path: str, mesh_path: str,
                                           vertex_id: int, expected_position: dict,
                                           position: dict, confirm: bool = False,
                                           dry_run: bool = False) -> str:
    """Set existing native vertex using exact inspected position guard, finite XYZ +/-1e9.
    Current mesh identities/bounded staged copy, native position/topology readback/
    replacement undo/no-op. Normals/tangents not recomputed; no map save.
    """
    if set(expected_position) != {"X", "Y", "Z"} or set(position) != {"X", "Y", "Z"}:
        raise ValueError("positions require X,Y,Z")
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/vertex-position", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "VertexId": vertex_id, "ExpectedPosition": expected_position, "Position": position,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def add_geometry_script_vertex(actor_path: str, component_path: str, mesh_path: str,
                                 position: dict, confirm: bool = False,
                                 dry_run: bool = False) -> str:
    """Append native isolated vertex, returning ID; finite XYZ +/-1e9.
    Current mesh identities/bounded staged copy/native position/count readback/
    replacement undo. No triangles/overlay elements added, no map save.
    """
    if set(position) != {"X", "Y", "Z"}:
        raise ValueError("position requires X,Y,Z")
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/add-vertex", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "Position": position, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def add_geometry_script_triangle(actor_path: str, component_path: str, mesh_path: str,
                                   vertex_a: int, vertex_b: int, vertex_c: int,
                                   group: int = 0, confirm: bool = False,
                                   dry_run: bool = False) -> str:
    """Append triangle from distinct existing native vertex IDs, group0..1e6.
    Native duplicate/nonmanifold rejection stays on staged copy, returned triangle
    ID/order/count readback/replacement undo. Overlay triangle assignments not
    populated explicitly; geometry validity unverified, no map save.
    """
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/add-triangle", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "Triangle": {"X": vertex_a, "Y": vertex_b, "Z": vertex_c}, "TriangleGroup": group,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def delete_geometry_script_triangle(actor_path: str, component_path: str, mesh_path: str,
                                      triangle_id: int, expected_a: int, expected_b: int,
                                      expected_c: int, confirm: bool = False,
                                      dry_run: bool = False) -> str:
    """Delete native triangle with exact inspected vertex-order guard.
    Native removal may delete up to3 newly isolated vertices. Bounded staged copy,
    absence/count readback/replacement undo. Normals/tangents not recomputed;
    confirmed stopped PIE/current mesh identities, no map save.
    """
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/delete-triangle", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "TriangleId": triangle_id, "Triangle": {"X": expected_a, "Y": expected_b, "Z": expected_c},
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_geometry_script_material_ids(actor_path: str, component_path: str, mesh_path: str,
                                       material_id: int, confirm: bool = False,
                                       dry_run: bool = False) -> str:
    """Assign native triangle material ID0..255 across whole staged mesh.
    Current identities/bounded copy, all-triangle ID/topology-count readback/native
    replacement undo. Component material slots unchanged; assigned slot may be absent.
    Confirmed stopped PIE, no map save.
    """
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/material-ids", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "MaterialId": material_id, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def flip_geometry_script_normals(actor_path: str, component_path: str, mesh_path: str,
                                 confirm: bool = False, dry_run: bool = False) -> str:
    """Reverse whole-mesh winding and normals through native Geometry Script.
    Stages <=100k vertices/triangles, checks reversed triangle winding and counts,
    commits with replacement undo. Tangents are not recomputed. Requires current
    mesh identities and confirmed stopped editor; callbacks may rebuild collision.
    No map save. Native rendering/undo behavior remains unverified.
    """
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/flip-normals", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_geometry_script_triangle_material_id(actor_path: str, component_path: str, mesh_path: str,
                                             triangle_id: int, expected_vertices: list[int],
                                             expected_material_id: int, material_id: int,
                                             confirm: bool = False, dry_run: bool = False) -> str:
    """Assign one triangle material ID with inspected vertex-order/current ID guards.
    Existing material attributes required; requested ID0..255. Staged bounded copy,
    checks all other triangle material IDs remain unchanged, replacement undo.
    Component material slots unchanged; rendering/collision callbacks may run.
    """
    if len(expected_vertices) != 3 or triangle_id < 0 or not 0 <= material_id <= 255:
        raise ValueError("Triangle ID, three expected vertex IDs and material ID0..255 required")
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/triangle-material-id", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "TriangleId": triangle_id, "Triangle": dict(zip(("X", "Y", "Z"), expected_vertices)),
        "ExpectedMaterialId": expected_material_id, "MaterialId": material_id,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def remap_geometry_script_material_ids(actor_path: str, component_path: str, mesh_path: str,
                                      from_material_id: int, to_material_id: int,
                                      confirm: bool = False, dry_run: bool = False) -> str:
    """Replace one material ID across an existing dynamic mesh, preserving other IDs.
    IDs0..255, existing material attributes, confirmed stopped editor/current mesh
    identities. Reports matching triangles; staged bounded copy/per-triangle
    readback/replacement undo. Component material slots unchanged; no map save.
    """
    if not 0 <= from_material_id <= 255 or not 0 <= to_material_id <= 255:
        raise ValueError("Source and destination material IDs must be0..255")
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/remap-material-ids", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "FromMaterialId": from_material_id, "MaterialId": to_material_id,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def compact_geometry_script_mesh(actor_path: str, component_path: str, mesh_path: str,
                                 confirm: bool = False, dry_run: bool = False) -> str:
    """Compact sparse dynamic-mesh IDs through native Geometry Script.
    Vertex/triangle/edge IDs may change: inspect topology again before ID edits.
    No remapping table. Staged <=100k vertices/triangles, compactness/count
    readback, replacement undo, already-compact no-op. Requires confirmed stopped
    editor/current owned mesh identities. Callbacks may rebuild collision; no save.
    """
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/compact", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def remove_geometry_script_unused_vertices(actor_path: str, component_path: str, mesh_path: str,
                                           confirm: bool = False, dry_run: bool = False) -> str:
    """Remove vertices unused by triangles, preserving remaining IDs/connectivity.
    Reports unused count, stages bounded copy, checks vertex-count reduction and
    retained referenced positions/triangle IDs, replacement undo and dry-run.
    Requires confirmed stopped editor/current mesh identities; no ID compaction
    or map save. Native callbacks and attribute preservation remain unverified.
    """
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/remove-unused-vertices", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_geometry_script_normal_mode(actor_path: str, component_path: str, mesh_path: str,
                                    normal_mode: str = "Repair", confirm: bool = False,
                                    dry_run: bool = False) -> str:
    """Repair winding or generate PerVertex smooth / PerFace split normal overlays.
    Repair runs native connected-component/global orientation solving; outward
    orientation is unproven for open/intersecting geometry. Tangents unchanged.
    Staged bounded mesh copy, retained positions/connectivity readback, reversal
    count, replacement undo. Native algorithm work is not strictly bounded.
    Requires confirmed stopped editor/current owned mesh identities; no map save.
    """
    if normal_mode not in ("Repair", "PerVertex", "PerFace"):
        raise ValueError("Normal mode must be Repair, PerVertex or PerFace")
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/normal-mode", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "NormalMode": normal_mode, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def transform_geometry_script_uvs(actor_path: str, component_path: str, mesh_path: str,
                                  uv_layer: int = 0, scale_x: float = 1, scale_y: float = 1,
                                  rotation_degrees: float = 0, origin_x: float = 0,
                                  origin_y: float = 0, translation_x: float = 0,
                                  translation_y: float = 0, confirm: bool = False,
                                  dry_run: bool = False,
                                        selected_triangles: list[int] | None = None,
                                        expected_vertices: list[list[int]] | None = None) -> str:
    """Optional inspected face selection limits native affected vertices/UV elements.
    Shared boundary vertices/UV elements can affect adjacent unselected faces.
    Scale then rotate a whole UV channel about shared origin, then translate.
    Existing channel0..7, finite bounded inputs; zero/negative scale allowed.
    Staged bounded copy, channel/element/topology-count and finite UV readback,
    replacement undo/dry-run. Tangents not regenerated; no map save. Requires
    confirmed stopped editor/current owned mesh identities; callbacks may run.
    """
    selected_triangles = selected_triangles or []
    expected_vertices = expected_vertices or []
    if len(selected_triangles) > 256 or len(expected_vertices) != len(selected_triangles) or any(len(v) != 3 for v in expected_vertices):
        raise ValueError("Up to256 selected triangle IDs with matching expected vertex triples required")
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/transform-uvs", json={
        "SelectedTriangles": selected_triangles,
        "ExpectedSelectedTriangles": [dict(zip(("X", "Y", "Z"), v)) for v in expected_vertices],
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "UVLayer": uv_layer, "UVScale": {"X": scale_x, "Y": scale_y},
        "UVRotation": rotation_degrees, "UVOrigin": {"X": origin_x, "Y": origin_y},
        "UVTranslation": {"X": translation_x, "Y": translation_y},
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_geometry_script_uvs(actor_path: str, component_path: str, mesh_path: str,
                                uv_layer: int = 0, element_start_id: int = 0,
                                triangle_start_id: int = 0, id_span: int = 64) -> str:
    """Read UV coordinates and per-triangle overlay element assignments in ID spans.
    Channel0..7, span1..256, holes omitted; unassigned triangles explicit and
    nonfinite UVs null. Returns continuation IDs/more flags. Read-only current
    owned mesh/stopped editor; no copy/validation. IDs may change between calls.
    """
    if not 0 <= uv_layer <= 7 or min(element_start_id, triangle_start_id) < 0 or not 1 <= id_span <= 256:
        raise ValueError("Channel0..7, nonnegative start IDs and span1..256 required")
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/uvs/inspect", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "UVLayer": uv_layer, "UVElementStartId": element_start_id,
        "TriangleStartId": triangle_start_id, "IdSpan": id_span
    }, timeout=60).text


@mcp.tool()
def copy_geometry_script_uv_channel(actor_path: str, component_path: str, mesh_path: str,
                                    source_uv_layer: int, destination_uv_layer: int,
                                    confirm: bool = False, dry_run: bool = False) -> str:
    """Overwrite an existing UV channel with another channel on the same mesh.
    Both channels0..7 must exist. Same channel no-op. Staged bounded copy,
    triangle UV assignment/corner-coordinate readback, replacement undo/dry-run.
    Overlay IDs may change; tangents not regenerated. Requires confirmed stopped
    editor/current owned mesh identities. No map save; callbacks may run.
    """
    if not 0 <= source_uv_layer <= 7 or not 0 <= destination_uv_layer <= 7:
        raise ValueError("Existing source and destination UV channels0..7 required")
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/copy-uv-channel", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "SourceUVLayer": source_uv_layer, "UVLayer": destination_uv_layer,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_geometry_script_triangle_uvs(actor_path: str, component_path: str, mesh_path: str,
                                     triangle_id: int, expected_vertices: list[int],
                                     uv0: list[float], uv1: list[float], uv2: list[float],
                                     uv_layer: int = 0, confirm: bool = False,
                                     dry_run: bool = False) -> str:
    """Assign three UV corners as a new isolated UV island on an existing face.
    Expected triangle vertex order guards stale IDs; existing channel0..7.
    Creates new elements even for identical UVs. Staged bounded copy/coordinate
    readback/replacement undo/dry-run; tangents unchanged. No map save.
    """
    if len(expected_vertices) != 3 or any(len(v) != 2 for v in (uv0, uv1, uv2)):
        raise ValueError("Three expected vertex IDs and three two-coordinate UVs required")
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/triangle-uvs", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "TriangleId": triangle_id, "Triangle": dict(zip(("X", "Y", "Z"), expected_vertices)),
        "UVLayer": uv_layer, "UV0": dict(zip(("X", "Y"), uv0)),
        "UV1": dict(zip(("X", "Y"), uv1)), "UV2": dict(zip(("X", "Y"), uv2)),
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def generate_geometry_script_polygroups(actor_path: str, component_path: str, mesh_path: str,
                                        mode: str = "Components", uv_layer: int = 0,
                                        crease_angle: float = 30, minimum_group_size: int = 2,
                                        confirm: bool = False, dry_run: bool = False,
                                        respect_uv_seams: bool = True, respect_hard_normals: bool = False,
                                        quad_adjacency_weight: float = 1, quad_metric_clamp: float = 1,
                                        polygon_search_rounds: int = 1,
                                        polygroup_layer: int = -1) -> str:
    """Target polygroup layer -1(default) or existing extended0..7.
    Polygons mode detects adjacent triangle pairs with seam/normal/metric controls.
    Overwrite default triangle groups by Components, UVIslands, Angle or Polygons partition.
    Enables default groups; UVIslands requires existing channel0..7. Angle mode
    uses crease angle0..180/minimum group size1..100000. Staged bounded copy,
    unchanged geometry readback/group count/replacement undo. Requested layer overwritten; default groups checked unchanged for extended target. Requires confirmed stopped editor/current mesh identities.
    No map save; native grouping quality/callback behavior unverified.
    """
    if mode not in ("Components", "UVIslands", "Angle", "Polygons"):
        raise ValueError("Mode must be Components, UVIslands, Angle or Polygons")
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/generate-polygroups", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "bRespectUVSeams": respect_uv_seams, "bRespectHardNormals": respect_hard_normals,
        "QuadAdjacencyWeight": quad_adjacency_weight, "QuadMetricClamp": quad_metric_clamp,
        "PolygonSearchRounds": polygon_search_rounds, "PolygroupLayerIndex": polygroup_layer, "PolygroupMode": mode, "UVLayer": uv_layer, "OpeningAngle": crease_angle,
        "MinIslandTriangles": minimum_group_size, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def smooth_geometry_script_mesh(actor_path: str, component_path: str, mesh_path: str,
                                 iterations: int = 10, alpha: float = 0.2,
                                 confirm: bool = False, dry_run: bool = False,
                                        selected_triangles: list[int] | None = None,
                                        expected_vertices: list[list[int]] | None = None) -> str:
    """Optional inspected face selection limits native affected vertices/UV elements.
    Shared boundary vertices/UV elements can affect adjacent unselected faces.
    Apply native whole-mesh iterative smoothing; can shrink/lose mesh detail.
    Iterations1..100, alpha0..1; zero-alpha/empty no-op. Staged bounded mesh copy,
    finite positions/preserved IDs-connectivity/count readback, replacement undo.
    Boundary/normal handling follows native behavior; tangents not explicitly
    regenerated. Requires confirmed stopped editor/current mesh identities.
    No map save; native algorithm/callback work is not strictly bounded.
    """
    selected_triangles = selected_triangles or []
    expected_vertices = expected_vertices or []
    if len(selected_triangles) > 256 or len(expected_vertices) != len(selected_triangles) or any(len(v) != 3 for v in expected_vertices):
        raise ValueError("Up to256 selected triangle IDs with matching expected vertex triples required")
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/smooth", json={
        "SelectedTriangles": selected_triangles,
        "ExpectedSelectedTriangles": [dict(zip(("X", "Y", "Z"), v)) for v in expected_vertices],
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "SmoothingIterations": iterations, "SmoothingAlpha": alpha,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def simplify_geometry_script_mesh(actor_path: str, component_path: str, mesh_path: str,
                                   target_triangles: int = 1000, method: str = "AttributeAware",
                                   allow_seam_collapse: bool = True, allow_seam_smoothing: bool = True,
                                   allow_seam_splits: bool = True, preserve_vertex_positions: bool = False,
                                   auto_compact: bool = True, confirm: bool = False,
                                   dry_run: bool = False) -> str:
    """Simplify toward triangle count with native QEM/volume/attribute-aware method.
    Target1..100000; native constraints may prevent target, reported separately.
    Seam options and position preservation follow native behavior. IDs/topology
    may change: inspect again. Staged bounded copy/finite output/count checks,
    replacement undo. Requires confirmed stopped editor/current mesh identities.
    No map save; algorithm/callback work not strictly bounded or quality proven.
    """
    if method not in ("AttributeAware", "StandardQEM", "VolumePreserving") or not 1 <= target_triangles <= 100000:
        raise ValueError("Supported method and target triangles1..100000 required")
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/simplify", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "TargetTriangleCount": target_triangles, "SimplifyMethod": method,
        "bAllowSeamCollapse": allow_seam_collapse, "bAllowSeamSmoothing": allow_seam_smoothing,
        "bAllowSeamSplits": allow_seam_splits, "bPreserveVertexPositions": preserve_vertex_positions,
        "bAutoCompact": auto_compact, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def simplify_geometry_script_regions(actor_path: str, component_path: str, mesh_path: str,
                                      mode: str = "Planar", angle_threshold: float = 0.001,
                                      auto_compact: bool = True, confirm: bool = False,
                                      dry_run: bool = False, polygroup_layer: int = -1) -> str:
    """Group layer -1(default) or existing extended0..7 for group-dependent operation.
    Simplify planar regions or reduce to existing default-polygroup topology.
    Native angle threshold0.00001..180; no count target. IDs/topology/attributes
    may change; inspect again afterward. Staged bounded mesh copy, finite output
    and nonincreasing count readback, replacement undo/dry-run. Requires confirmed
    stopped editor/current mesh identities; no save. Native quality unverified.
    """
    if mode not in ("Planar", "Polygroups"):
        raise ValueError("Mode must be Planar or Polygroups")
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/simplify-regions", json={
        "PolygroupLayerIndex": polygroup_layer, "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "RegionSimplifyMode": mode, "RegionAngleThreshold": angle_threshold,
        "bAutoCompact": auto_compact, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_geometry_script_edges(actor_path: str, component_path: str, mesh_path: str,
                                  edge_start_id: int = 0, id_span: int = 64) -> str:
    """Read edge endpoint/incident triangle IDs and boundary flags in ID spans.
    Nonnegative start/span1..256, sparse holes omitted. Missing second triangle
    uses native negative sentinel. Boundary count covers page only; continuation
    ID/more flag included. Current owned mesh/stopped editor, no copy/mutation.
    """
    if edge_start_id < 0 or not 1 <= id_span <= 256:
        raise ValueError("Nonnegative edge start and ID span1..256 required")
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/edges/inspect", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "EdgeStartId": edge_start_id, "IdSpan": id_span
    }, timeout=60).text


@mcp.tool()
def fill_geometry_script_holes(actor_path: str, component_path: str, mesh_path: str,
                               method: str = "Automatic", delete_isolated_triangles: bool = False,
                               confirm: bool = False, dry_run: bool = False) -> str:
    """Fill native boundary loops, report filled/failed counts; partial results commit.
    Methods Automatic/MinimalFill/PolygonTriangulation/TriangleFan/PlanarProjection.
    Isolated triangles deleted only if requested. Staged bounded input/output copy,
    finite output checks/replacement undo. IDs/topology/attributes may change;
    inspect again afterward. Closure/manifold/visual quality unproven. Confirmed
    stopped editor/current mesh identities; no save, algorithm work unbounded.
    """
    if method not in ("Automatic", "MinimalFill", "PolygonTriangulation", "TriangleFan", "PlanarProjection"):
        raise ValueError("Unsupported hole fill method")
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/fill-holes", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "HoleFillMethod": method, "bDeleteIsolatedTriangles": delete_isolated_triangles,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def remove_geometry_script_small_components(actor_path: str, component_path: str, mesh_path: str,
                                             min_volume: float = 0, min_area: float = 0,
                                             min_triangles: int = 1, confirm: bool = False,
                                             dry_run: bool = False) -> str:
    """Remove disconnected components below any native volume/area/count threshold.
    Native implementation preserves exactly one connected component regardless
    of thresholds; with multiple components all may be removed. Volume/open-surface
    semantics follow native queries. Staged bounded copy/retained geometry checks,
    removed counts/replacement undo. Confirmed stopped editor/current identities.
    No map save; algorithm/callback/attribute behavior unverified.
    """
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/remove-small-components", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "MinComponentVolume": min_volume, "MinComponentArea": min_area,
        "MinComponentTriangles": min_triangles, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def weld_geometry_script_edges(actor_path: str, component_path: str, mesh_path: str,
                               tolerance: float = 0.000001, only_unique_pairs: bool = True,
                               confirm: bool = False, dry_run: bool = False) -> str:
    """Weld coincident boundary edges with native tolerance/unique-pair controls.
    Positive tolerance<=1e6. Staged bounded copy; native error diagnostics reject
    result. Reports boundary counts; no promise all seams welded/manifold output.
    IDs/connectivity/attributes may change; inspect again. Finite-position/count
    checks/replacement undo/dry-run. Confirmed stopped editor/current identities;
    no map save. Native algorithm/callback work not strictly bounded.
    """
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/weld-edges", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "WeldTolerance": tolerance, "bOnlyUniquePairs": only_unique_pairs,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def repair_geometry_script_boundaries(actor_path: str, component_path: str, mesh_path: str,
                                      mode: str = "Snap", tolerance: float = 0.001,
                                      snap_to_edges: bool = True, iterations: int = 5,
                                      confirm: bool = False, dry_run: bool = False) -> str:
    """Snap open boundaries or resolve TJunctions through native mesh repair.
    Native distance uses twice tolerance. Snap iterations1..100/edge snapping;
    TJunctions may add vertices/triangles. Staged bounded input/output copy,
    native error rejection/finite positions/boundary counts/replacement undo.
    IDs/topology/attributes may change; no manifold/closure guarantee. Confirmed
    stopped editor/current identities; no save. Algorithm work not strictly bounded.
    """
    if mode not in ("Snap", "TJunctions"):
        raise ValueError("Mode must be Snap or TJunctions")
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/repair-boundaries", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "BoundaryRepairMode": mode, "WeldTolerance": tolerance, "bSnapToEdges": snap_to_edges,
        "BoundarySnapIterations": iterations, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def cut_geometry_script_mesh_with_plane(actor_path: str, component_path: str, mesh_path: str,
                                         cut_frame: dict, fill_holes: bool = True,
                                         fill_spans: bool = True, flip_cut_side: bool = False,
                                         hole_material_id: int = -1, uv_world_dimension: float = 1,
                                         confirm: bool = False, dry_run: bool = False) -> str:
    """Cut by component-local frame origin/Z normal, optionally fill cut boundaries.
    Frame uses normalized quaternion/unit scale. Native side convention/flip.
    Staged bounded mesh/finite output/debug checks/replacement undo; empty output
    allowed. Native cut/fill success not exposed; no closure guarantee. IDs/topology
    may change. Confirmed stopped editor/current identities; no save.
    """
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/plane-cut", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "Transform": cut_frame, "bFillHoles": fill_holes, "bFillSpans": fill_spans,
        "bFlipCutSide": flip_cut_side, "HoleFillMaterialId": hole_material_id,
        "UVWorldDimension": uv_world_dimension, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def model_geometry_script_mesh_with_plane(actor_path: str, component_path: str, mesh_path: str,
                                           plane_frame: dict, mode: str = "Slice",
                                           gap_width: float = 0.01, fill_holes: bool = True,
                                           fill_spans: bool = True, hole_material_id: int = -1,
                                           uv_world_dimension: float = 1, apply_plane_cut: bool = True,
                                           flip_cut_side: bool = False, weld_along_plane: bool = True,
                                           confirm: bool = False, dry_run: bool = False) -> str:
    """Slice into halves in one mesh or mirror about local frame origin/Z plane.
    Slice uses gap/fill/material/UV options; Mirror uses cut/flip/weld options.
    Normalized quaternion/unit frame scale. Staged bounded input/output, finite
    positions/debug error checks/replacement undo. IDs/topology may change;
    native cut/fill/weld completeness unproven. Confirmed stopped editor/current
    identities; no map save. Native work not strictly bounded.
    """
    if mode not in ("Slice", "Mirror"):
        raise ValueError("Mode must be Slice or Mirror")
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/plane-model", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "Transform": plane_frame, "PlaneModelMode": mode, "SliceGapWidth": gap_width,
        "bFillHoles": fill_holes, "bFillSpans": fill_spans, "HoleFillMaterialId": hole_material_id,
        "UVWorldDimension": uv_world_dimension, "bApplyPlaneCut": apply_plane_cut,
        "bFlipCutSide": flip_cut_side, "bWeldAlongPlane": weld_along_plane,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def boolean_geometry_script_meshes(actor_path: str, component_path: str, mesh_path: str,
                                    source_actor_path: str, source_component_path: str,
                                    source_mesh_path: str, operation: str = "Union",
                                    fill_holes: bool = True, simplify_output: bool = True,
                                    planar_tolerance: float = 0.01, allow_empty_result: bool = False,
                                    confirm: bool = False, dry_run: bool = False) -> str:
    """Boolean/trim/polygroup classification using component transforms in world space.
    Operations include TrimInside/TrimOutside/NewPolyGroupInside/NewPolyGroupOutside;
    native inside/outside convention, group modes may split intersection geometry.
    Distinct owned current-world meshes; result target-local, source unchanged.
    Both meshes staged/bounded; native debug errors reject result, finite output
    and output budgets checked. IDs/topology/attributes may change; material slots
    not merged. Replacement undo/dry-run, confirmed stopped editor; no map save.
    Boolean quality/closure unproven; native algorithm work not strictly bounded.
    """
    if operation not in ("Union", "Intersection", "Subtract", "TrimInside", "TrimOutside",
                         "NewPolyGroupInside", "NewPolyGroupOutside"):
        raise ValueError("Unsupported Boolean/trim/polygroup operation")
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/boolean", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "SourceActorPath": source_actor_path, "SourceComponentPath": source_component_path,
        "SourceMeshPath": source_mesh_path, "BooleanOperation": operation,
        "bFillHoles": fill_holes, "bBooleanSimplifyOutput": simplify_output,
        "BooleanPlanarTolerance": planar_tolerance, "bAllowEmptyResult": allow_empty_result,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def self_union_geometry_script_mesh(actor_path: str, component_path: str, mesh_path: str,
                                    fill_holes: bool = True, trim_flaps: bool = True,
                                    simplify_output: bool = True, planar_tolerance: float = 0.01,
                                    winding_threshold: float = 0.5, confirm: bool = False,
                                    dry_run: bool = False) -> str:
    """Apply native self-union for overlapping/self-intersecting mesh geometry.
    Winding threshold0..1, fill/trim-flaps/simplify options. Native implementation
    ignores internal success flag: finite/budget/debug checks do not prove repair
    or closure. Staged bounded copy/replacement undo/dry-run; IDs/topology may
    change, empty output allowed. Confirmed stopped editor/current identities;
    no save. Native algorithm work not strictly bounded.
    """
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/self-union", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "bFillHoles": fill_holes, "bTrimFlaps": trim_flaps,
        "bBooleanSimplifyOutput": simplify_output, "BooleanPlanarTolerance": planar_tolerance,
        "WindingThreshold": winding_threshold, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def remesh_geometry_script_mesh(actor_path: str, component_path: str, mesh_path: str,
                                 target_type: str = "TriangleCount", target_triangles: int = 1000,
                                 target_edge_length: float = 1, iterations: int = 20,
                                 smoothing: str = "Mixed", smoothing_rate: float = 0.25,
                                 mesh_boundary: str = "Free", group_boundary: str = "Free",
                                 material_boundary: str = "Free", discard_attributes: bool = False,
                                 reproject: bool = True, allow_flips: bool = True,
                                 allow_splits: bool = True, allow_collapses: bool = True,
                                 prevent_normal_flips: bool = True, prevent_tiny_triangles: bool = True,
                                 full_passes: bool = False, auto_compact: bool = True,
                                 confirm: bool = False, dry_run: bool = False) -> str:
    """Native uniform remesh by approximate triangle count or target edge length.
    Smoothing Mixed/Uniform/UVPreserving, constraints Fixed/Refine/Free/Ignore.
    DiscardAttributes removes authored attributes; density/shape not guaranteed,
    results may be nondeterministic. Staged bounded input/output/finite positions/
    debug checks/replacement undo. IDs/topology may change; confirmed stopped
    editor/current identities. No save; algorithm/allocation work not bounded.
    """
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/remesh", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "RemeshTarget": target_type, "TargetTriangleCount": target_triangles,
        "TargetEdgeLength": target_edge_length, "RemeshIterations": iterations,
        "RemeshSmoothing": smoothing, "SmoothingAlpha": smoothing_rate,
        "MeshBoundaryConstraint": mesh_boundary, "GroupBoundaryConstraint": group_boundary,
        "MaterialBoundaryConstraint": material_boundary, "bDiscardAttributes": discard_attributes,
        "bReprojectToInputMesh": reproject, "bAllowFlips": allow_flips,
        "bAllowSplits": allow_splits, "bAllowCollapses": allow_collapses,
        "bPreventNormalFlips": prevent_normal_flips, "bPreventTinyTriangles": prevent_tiny_triangles,
        "bUseFullRemeshPasses": full_passes, "bAutoCompact": auto_compact,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def auto_generate_geometry_script_uvs(actor_path: str, component_path: str, mesh_path: str,
                                       uv_layer: int = 0, method: str = "XAtlas", iterations: int = 2,
                                       initial_patch_count: int = 100, minimum_patch_size: int = 2,
                                       respect_input_groups: bool = False, auto_pack: bool = True,
                                       confirm: bool = False, dry_run: bool = False) -> str:
    """Replace existing UV channel with native XAtlas or PatchBuilder layout.
    Iterations apply to XAtlas; patch count/size/group respect/packing to PatchBuilder.
    Uses native patch metric/packing defaults. Staged bounded mesh/debug/finite UV
    and topology count checks, assignment count/replacement undo/dry-run. UV quality
    unproven; tangents not regenerated. Confirmed stopped editor/current identities;
    no save, native algorithm work not strictly bounded.
    """
    if method not in ("XAtlas", "PatchBuilder"):
        raise ValueError("Method must be XAtlas or PatchBuilder")
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/auto-generate-uvs", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "UVLayer": uv_layer, "UVGenerationMethod": method, "UVGenerationIterations": iterations,
        "InitialPatchCount": initial_patch_count, "MinIslandTriangles": minimum_patch_size,
        "bRespectInputGroups": respect_input_groups, "bAutoPack": auto_pack,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def repack_geometry_script_uvs(actor_path: str, component_path: str, mesh_path: str,
                               uv_layer: int = 0, resolution: int = 512,
                               optimize_island_rotation: bool = True,
                               confirm: bool = False, dry_run: bool = False) -> str:
    """Repack existing UV islands with native image-width/rotation controls.
    Existing channel0..7, resolution16..8192; native spacing defaults. Staged
    bounded mesh copy, finite UV/retained overlay assignment/count checks,
    native debug errors/replacement undo/dry-run. Overlap/gutter quality unproven;
    tangents unchanged. Confirmed stopped editor/current mesh identities; no save.
    """
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/repack-uvs", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "UVLayer": uv_layer, "UVPackingResolution": resolution,
        "bOptimizeIslandRotation": optimize_island_rotation,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def tessellate_geometry_script_mesh(actor_path: str, component_path: str, mesh_path: str,
                                    method: str = "Uniform", level: int = 1,
                                    recompute_pn_normals: bool = True,
                                    confirm: bool = False, dry_run: bool = False) -> str:
    """Subdivide linearly with Uniform or curved PN tessellation, level1..6.
    Conservative triangle growth budget <=100k; bounded input/output staged mesh,
    native debug errors/finite positions/replacement undo. PN optional normals.
    IDs/topology/attributes may change, interpolation quality unproven. Confirmed
    stopped editor/current mesh identities; no save, algorithm work not bounded.
    """
    if method not in ("Uniform", "PN") or not 1 <= level <= 6:
        raise ValueError("Method Uniform/PN and level1..6 required")
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/tessellate", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "TessellationMethod": method, "TessellationLevel": level,
        "bRecomputeTessellationNormals": recompute_pn_normals,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def measure_geometry_script_mesh(actor_path: str, component_path: str, mesh_path: str) -> str:
    """Read native area/signed volume/center/bounds/closed/boundary edge-loop counts.
    Component-local units, native float area/volume precision. Open/inconsistent/
    degenerate mesh volume-center may be meaningless; nonfinite outputs null.
    Closed flag is no manifold/intersection proof, loop ambiguity explicit.
    Bounded finite input scan/current owned mesh/stopped editor; no copy/mutation.
    """
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/measure", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path
    }, timeout=60).text


@mcp.tool()
def copy_static_mesh_to_geometry_script_mesh(actor_path: str, component_path: str, mesh_path: str,
                                              asset_path: str, lod_type: str = "SourceModel",
                                              lod_index: int = 0, apply_build_settings: bool = True,
                                              request_tangents: bool = True, ignore_remove_degenerates: bool = True,
                                              use_build_scale: bool = True, use_section_materials: bool = True,
                                              confirm: bool = False, dry_run: bool = False) -> str:
    """Replace Dynamic Mesh with persistent Static Mesh SourceModel/RenderData LOD0..7.
    Exact LOD availability checked; no native clamping. Staged native extraction
    outcome/debug/finite/output-budget checks/replacement undo. Extraction work
    and allocation precede output budget. Asset unchanged, component slots not
    copied. Confirmed stopped editor/current owned mesh identities; no save.
    """
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/copy-from-static-mesh", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "AssetPath": asset_path, "LODType": lod_type, "LODIndex": lod_index,
        "bApplyBuildSettings": apply_build_settings, "bRequestTangents": request_tangents,
        "bIgnoreRemoveDegenerates": ignore_remove_degenerates, "bUseBuildScale": use_build_scale,
        "bUseSectionMaterials": use_section_materials, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def write_geometry_script_mesh_to_static_mesh(actor_path: str, component_path: str, mesh_path: str,
                                               asset_path: str, lod_index: int = 0,
                                               recompute_normals: bool = False, recompute_tangents: bool = False,
                                               remove_degenerates: bool = False, original_vertex_order: bool = False,
                                               use_build_scale: bool = True, use_section_materials: bool = True,
                                               lightmap_uv_mode: str = "Match", save: bool = False,
                                               confirm: bool = False, dry_run: bool = False) -> str:
    """Overwrite existing loaded /Game Static Mesh source LOD from Dynamic Mesh.
    Staged bounded source copy; native outcome/debug/LOD-validity readback and
    asset undo transaction. Source unchanged; native PostEditChange rebuilds asset
    and may update dependents/collision. Material/Nanite replacement disabled.
    Lightmap mode Match/Generate/Disable; inverse build scale follows native option.
    Save only when requested. Requires confirmed stopped editor/current identities.
    """
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/copy-to-static-mesh", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "AssetPath": asset_path, "LODIndex": lod_index, "bEnableRecomputeNormals": recompute_normals,
        "bEnableRecomputeTangents": recompute_tangents, "bEnableRemoveDegenerates": remove_degenerates,
        "bUseOriginalVertexOrder": original_vertex_order, "bUseBuildScale": use_build_scale,
        "bUseSectionMaterials": use_section_materials, "LightmapUVMode": lightmap_uv_mode,
        "bSave": save, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def generate_geometry_script_collision(actor_path: str, component_path: str, mesh_path: str,
                                        method: str = "MinVolumeShapes", max_shapes: int = 32,
                                        max_convex_hulls: int = 1, convex_hull_faces: int = 25,
                                        min_thickness: float = 1, simplify_hulls: bool = True,
                                        detect_spheres: bool = True, detect_boxes: bool = True,
                                        detect_capsules: bool = True, confirm: bool = False,
                                        dry_run: bool = False) -> str:
    """Replace Dynamic Mesh component simple collision from staged mesh geometry.
    Methods AlignedBoxes/OrientedBoxes/MinimalSpheres/Capsules/ConvexHulls/
    SweptHulls/MinVolumeShapes/LevelSets. Shape limit1..128, bounded input geometry.
    Native errors/shape count checks, component/body transaction, physics update.
    Does not enable collision or change complex-as-simple settings. Cooking may
    be asynchronous; undo/physics behavior unverified. No save/simulation.
    """
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/generate-collision", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "CollisionMethod": method, "MaxCollisionShapes": max_shapes, "MaxConvexHulls": max_convex_hulls,
        "ConvexHullFaces": convex_hull_faces, "CollisionMinThickness": min_thickness,
        "bSimplifyCollisionHulls": simplify_hulls, "bAutoDetectSpheres": detect_spheres,
        "bAutoDetectBoxes": detect_boxes, "bAutoDetectCapsules": detect_capsules,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_geometry_script_collision(actor_path: str, component_path: str, mesh_path: str) -> str:
    """Read authored simple collision counts by shape type and component settings.
    No aggregate copy/physics query/cooking. Counts do not prove cooked physics
    currentness/validity. Current owned mesh/stopped editor required; read-only.
    """
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/collision/inspect", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path
    }, timeout=60).text


@mcp.tool()
def clear_geometry_script_collision(actor_path: str, component_path: str, mesh_path: str,
                                     confirm: bool = False, dry_run: bool = False) -> str:
    """Clear authored simple collision with native physics update/undo/dry-run.
    Geometry and complex collision/enable settings unchanged. Zero shape readback
    does not prove asynchronous cooking complete. Current owned mesh/confirmed
    stopped editor required; undo/resource lifetime unverified, no save/simulation.
    """
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/collision/clear", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def generate_static_mesh_collision_from_geometry_script_mesh(actor_path: str, component_path: str,
        mesh_path: str, asset_path: str, method: str = "MinVolumeShapes", max_shapes: int = 32,
        max_convex_hulls: int = 1, convex_hull_faces: int = 25, min_thickness: float = 1,
        simplify_hulls: bool = True, mark_customized: bool = True, save: bool = False,
        confirm: bool = False, dry_run: bool = False) -> str:
    """Generate/overwrite loaded /Game Static Mesh simple collision from Dynamic Mesh.
    Source coordinates map directly to asset-local; no component transform/build
    scale compensation. Source component unchanged; native shape methods/default
    primitive detection, bounded input/generated shapes. Native errors/count and
    customization readback, asset/body undo, optional explicit save/dry-run.
    Cooking/dependent physics work unbounded; undo/physics behavior unverified.
    """
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/generate-static-mesh-collision", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "AssetPath": asset_path, "CollisionMethod": method, "MaxCollisionShapes": max_shapes,
        "MaxConvexHulls": max_convex_hulls, "ConvexHullFaces": convex_hull_faces,
        "CollisionMinThickness": min_thickness, "bSimplifyCollisionHulls": simplify_hulls,
        "bMarkCollisionCustomized": mark_customized, "bSave": save,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_geometry_script_materials(actor_path: str, component_path: str, mesh_path: str) -> str:
    """Read up to64 component base material slots; null is empty path, truncation explicit.
    Render override/secondary materials may supersede base slots. No load/mutation.
    """
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/materials/inspect", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path
    }, timeout=60).text


@mcp.tool()
def set_geometry_script_material(actor_path: str, component_path: str, mesh_path: str,
                                 material_index: int, expected_material_count: int,
                                 expected_material_path: str, material_path: str,
                                 confirm: bool = False, dry_run: bool = False) -> str:
    """Set/clear existing base slot or append next slot0..63 with count/value guards.
    Persistent material or empty path; null expected path empty. Component
    undo/readback/dry-run; triangle IDs unchanged. Native render/physical-material
    callbacks may run; overrides may supersede assignment. No load/map save.
    """
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/materials/set", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "MaterialIndex": material_index, "ExpectedMaterialCount": expected_material_count,
        "ExpectedMaterialPath": expected_material_path, "MaterialPath": material_path,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_geometry_script_vertex_color(actor_path: str, component_path: str, mesh_path: str,
                                      red: float = 1, green: float = 1, blue: float = 1, alpha: float = 1,
                                      set_red: bool = True, set_green: bool = True,
                                      set_blue: bool = True, set_alpha: bool = True,
                                      clear_existing: bool = False, confirm: bool = False,
                                      dry_run: bool = False) -> str:
    """Set constant linear RGBA0..1 on vertex color overlay with channel masks.
    Creating/clearing overlay initializes ALL channels regardless of masks and
    can remove color seams. Existing overlay applies selected channels. Staged
    bounded copy/selected-channel readback/replacement undo/dry-run. Material must
    consume vertex colors for visibility. Confirmed stopped editor/current identities.
    """
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/vertex-color", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "VertexColor": {"R": red, "G": green, "B": blue, "A": alpha},
        "bColorRed": set_red, "bColorGreen": set_green, "bColorBlue": set_blue,
        "bColorAlpha": set_alpha, "bClearExistingColors": clear_existing,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_geometry_script_vertex_colors(actor_path: str, component_path: str, mesh_path: str,
                                           element_start_id: int = 0, triangle_start_id: int = 0,
                                           id_span: int = 64) -> str:
    """Read primary color overlay RGBA and triangle assignments in ID spans1..256.
    Sparse holes omitted, unassigned faces explicit, nonfinite channels null.
    Returns continuation IDs/more flags. Current owned mesh/stopped editor;
    no copy/mutation. Overlay IDs and assignments may change between calls.
    """
    if min(element_start_id, triangle_start_id) < 0 or not 1 <= id_span <= 256:
        raise ValueError("Nonnegative starts and span1..256 required")
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/vertex-colors/inspect", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "ColorElementStartId": element_start_id, "TriangleStartId": triangle_start_id,
        "IdSpan": id_span
    }, timeout=60).text


@mcp.tool()
def warp_geometry_script_mesh(actor_path: str, component_path: str, mesh_path: str,
                               frame: dict, mode: str = "Bend", angle_degrees: float = 45,
                               extent: float = 50, lower_extent: float = 10,
                               symmetric_extents: bool = True, bidirectional: bool = True,
                               confirm: bool = False, dry_run: bool = False) -> str:
    """Bend/Twist mesh using component-local normalized/unit-scale frame.
    Degrees +/-3600, positive extent<=1e6; asymmetric lower extent>=0.
    Native lower bound is negative lower_extent; bidirectional false locks bottom.
    Staged bounded copy/native debug/finite output/retained connectivity checks,
    replacement undo/dry-run. Severe angles may self-intersect; tangents not
    explicitly regenerated. Confirmed stopped editor/current identities; no save.
    """
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/warp", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "Transform": frame, "WarpMode": mode, "WarpAngle": angle_degrees,
        "WarpExtent": extent, "WarpLowerExtent": lower_extent,
        "bSymmetricWarpExtents": symmetric_extents, "bBidirectionalWarp": bidirectional,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def flare_geometry_script_mesh(actor_path: str, component_path: str, mesh_path: str,
                                frame: dict, percent_x: float = 0, percent_y: float = 0,
                                profile: str = "Sin", extent: float = 50, lower_extent: float = 10,
                                symmetric_extents: bool = True, confirm: bool = False,
                                dry_run: bool = False) -> str:
    """Flare/bulge local frame axes using Sin/SinSquared/Triangle profile.
    Percentages +/-1000, positive extent<=1e6; normalized/unit-scale local frame.
    Negative/large values may collapse/invert/self-intersect geometry. Staged
    bounded copy/native debug/finite output/connectivity readback, replacement
    undo/dry-run. Current mesh/confirmed stopped editor; no save.
    """
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/flare", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "Transform": frame, "FlarePercentX": percent_x, "FlarePercentY": percent_y,
        "FlareProfile": profile, "WarpExtent": extent, "WarpLowerExtent": lower_extent,
        "bSymmetricWarpExtents": symmetric_extents, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def wave_geometry_script_mesh(actor_path: str, component_path: str, mesh_path: str,
                               frame: dict, wave_type: str = "SinWave1D", magnitude: float = 5,
                               frequency: float = 0.25, frequency_shift: float = 0,
                               confirm: bool = False, dry_run: bool = False) -> str:
    """Apply native SinWave1D/2D warp in normalized/unit-scale local frame (UE has no SinWave3D implementation).
    Finite magnitude/frequency/shift +/-1e6; native sine frequency convention.
    Staged bounded mesh/debug/finite output/connectivity checks/replacement undo.
    May self-intersect/distort; normals/tangents not explicitly recomputed.
    Confirmed stopped editor/current owned mesh identities; no map save.
    """
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/wave", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "Transform": frame, "WaveType": wave_type, "WaveMagnitude": magnitude,
        "WaveFrequency": frequency, "WaveShift": frequency_shift,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def apply_geometry_script_perlin_noise(actor_path: str, component_path: str, mesh_path: str,
                                       magnitude: float = 5, frequency: float = 0.25,
                                       seed: int = 0, shift_x: float = 0, shift_y: float = 0,
                                       shift_z: float = 0, along_normal: bool = True,
                                       confirm: bool = False, dry_run: bool = False,
                                        selected_triangles: list[int] | None = None,
                                        expected_vertices: list[list[int]] | None = None) -> str:
    """Optional inspected face selection limits native affected vertices/UV elements.
    Shared boundary vertices/UV elements can affect adjacent unselected faces.
    Apply native seeded Perlin noise along computed normals or XYZ directions.
    Component-local coordinates, finite magnitude/frequency/shift +/-1e6.
    Staged bounded mesh/debug/finite output/connectivity checks/replacement undo.
    Native normal direction computed for displacement, final normal/tangent
    overlays not explicitly regenerated. Confirmed stopped editor/current identities;
    no save, geometry quality/seed reproducibility across versions unverified.
    """
    selected_triangles = selected_triangles or []
    expected_vertices = expected_vertices or []
    if len(selected_triangles) > 256 or len(expected_vertices) != len(selected_triangles) or any(len(v) != 3 for v in expected_vertices):
        raise ValueError("Up to256 selected triangle IDs with matching expected vertex triples required")
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/perlin-noise", json={
        "SelectedTriangles": selected_triangles,
        "ExpectedSelectedTriangles": [dict(zip(("X", "Y", "Z"), v)) for v in expected_vertices],
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "WaveMagnitude": magnitude, "WaveFrequency": frequency, "NoiseSeed": seed,
        "NoiseFrequencyShift": {"X": shift_x, "Y": shift_y, "Z": shift_z},
        "bNoiseAlongNormal": along_normal, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def replace_geometry_script_mesh_with_convex_hull(actor_path: str, component_path: str, mesh_path: str,
                                                  prefilter_vertices: bool = True, grid_resolution: int = 128,
                                                  simplify_faces: int = 0, confirm: bool = False,
                                                  dry_run: bool = False) -> str:
    """Replace mesh with native convex hull, generated attributes/per-face normals.
    Grid32..512, simplification0(disabled) or5..100000. Four finite vertices needed;
    degeneracy errors reject native fallback cube. Staged bounded input/output,
    debug/finite/nonempty checks/replacement undo. Exact containment may change
    with prefilter/simplification. Confirmed stopped editor/current identities; no save.
    """
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/convex-hull", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "bHullPrefilter": prefilter_vertices, "HullGridResolution": grid_resolution,
        "HullSimplifyFaces": simplify_faces, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def replace_geometry_script_mesh_with_swept_hull(actor_path: str, component_path: str, mesh_path: str,
                                                 projection_frame: dict, min_thickness: float = 0.01,
                                                 simplify: bool = True, min_edge_length: float = 0.1,
                                                 simplify_tolerance: float = 0.1, confirm: bool = False,
                                                 dry_run: bool = False) -> str:
    """Replace mesh with hull of XY-plane projection swept along frame Z extents.
    Normalized/unit-scale component-local frame; finite nonnegative thickness/
    edge/tolerance<=1e6. Staged bounded input/output/native debug failure rejection/
    finite nonempty output/replacement undo. Authored attributes replaced; exact
    containment/quality unproven. Confirmed stopped editor/current identities; no save.
    """
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/swept-hull", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "Transform": projection_frame, "SweptMinThickness": min_thickness,
        "bSweptSimplify": simplify, "SweptMinEdgeLength": min_edge_length,
        "SweptSimplifyTolerance": simplify_tolerance, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def decompose_geometry_script_mesh_into_convex_hulls(actor_path: str, component_path: str, mesh_path: str,
                                                     hulls: int = 2, search_factor: float = 0.5,
                                                     error_tolerance: float = 0, min_part_thickness: float = 0.1,
                                                     simplify_faces: int = 0, confirm: bool = False,
                                                     dry_run: bool = False) -> str:
    """Replace mesh with combined convex decomposition pieces, target hulls1..64.
    Search factor0..1, error/thickness>=0, simplification0 or5..100000 faces.
    Native count/containment/overlap approximate; generated attributes replace
    original content. Staged bounded input/output/native error rejection/finite
    nonempty output/replacement undo. Confirmed stopped editor/current identities;
    no save; native allocation/algorithm work not strictly bounded.
    """
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/convex-decomposition", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "DecompositionHulls": hulls, "DecompositionSearchFactor": search_factor,
        "DecompositionError": error_tolerance, "DecompositionMinThickness": min_part_thickness,
        "HullSimplifyFaces": simplify_faces, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def append_geometry_script_mesh(actor_path: str, component_path: str, mesh_path: str,
                                 source_actor_path: str, source_component_path: str, source_mesh_path: str,
                                 combine_attributes: str = "EnableAllMatching", confirm: bool = False,
                                 dry_run: bool = False) -> str:
    """Append distinct mesh using current component transforms; uniform target scale.
    Attribute modes EnableAllMatching/UseTarget/UseSource; no welding or Boolean
    repair, material slots not merged. Staged bounded copies/native errors/exact
    combined counts/finite output/replacement undo. Source unchanged. Confirmed
    stopped editor/current identities; no save, geometry quality unverified.
    """
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/append-mesh", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "SourceActorPath": source_actor_path, "SourceComponentPath": source_component_path,
        "SourceMeshPath": source_mesh_path, "CombineAttributes": combine_attributes,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_geometry_script_normals(actor_path: str, component_path: str, mesh_path: str,
                                    normal_layer: int = 0, element_start_id: int = 0,
                                    triangle_start_id: int = 0, id_span: int = 64) -> str:
    """Read normal/tangent overlay vectors and triangle assignments in ID spans.
    Existing layer0..7: native0 normals/1 tangents/2 bitangents. Span1..256,
    sparse holes omitted/unassigned explicit/nonfinite channels null, pagination.
    No normalization/orthogonality proof. Current owned mesh/stopped editor,
    read-only without copy/mutation; overlay IDs may change between calls.
    """
    if not 0 <= normal_layer <= 7 or min(element_start_id, triangle_start_id) < 0 or not 1 <= id_span <= 256:
        raise ValueError("Layer0..7, nonnegative starts and span1..256 required")
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/normals/inspect", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "NormalLayer": normal_layer, "NormalElementStartId": element_start_id,
        "TriangleStartId": triangle_start_id, "IdSpan": id_span
    }, timeout=60).text


@mcp.tool()
def extrude_geometry_script_mesh(actor_path: str, component_path: str, mesh_path: str,
                                  distance: float = 1, direction_x: float = 0, direction_y: float = 0,
                                  direction_z: float = 1, direction_mode: str = "FixedDirection",
                                  uv_scale: float = 1, solids_to_shells: bool = True,
                                  confirm: bool = False, dry_run: bool = False,
                                  area_mode: str = "EntireSelection",
                                        selected_triangles: list[int] | None = None,
                                        expected_vertices: list[list[int]] | None = None) -> str:
    """Linear-extrude all faces, preserve native group defaults.
    Area modes EntireSelection/PerPolygroup/PerTriangle; per-group requires existing groups.
    FixedDirection/AverageFaceNormal with normalized fallback direction, finite
    distance +/-1e6/positive UV scale. Closed solids use native shell option.
    Staged bounded input/output/debug/finite checks/replacement undo/dry-run.
    IDs/topology/attributes may change; quality/closure unproven. Confirmed stopped
    editor/current identities; no save, native work not strictly bounded.
    """
    selected_triangles = selected_triangles or []
    expected_vertices = expected_vertices or []
    if len(selected_triangles) > 256 or len(expected_vertices) != len(selected_triangles) or any(len(v) != 3 for v in expected_vertices):
        raise ValueError("Up to256 selected triangle IDs with matching expected vertex triples required")
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/extrude", json={
        "SelectedTriangles": selected_triangles,
        "ExpectedSelectedTriangles": [dict(zip(("X", "Y", "Z"), v)) for v in expected_vertices],
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "ExtrudeAreaMode": area_mode, "ExtrudeDistance": distance, "ExtrudeDirection": {"X": direction_x, "Y": direction_y, "Z": direction_z},
        "ExtrudeDirectionMode": direction_mode, "ExtrudeUVScale": uv_scale,
        "bSolidsToShells": solids_to_shells, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def offset_or_shell_geometry_script_mesh(actor_path: str, component_path: str, mesh_path: str,
                                          mode: str = "Offset", distance: float = 1,
                                          solve_steps: int = 5, smoothing: float = 0.1,
                                          fixed_boundary: bool = False, reproject_smoothing: bool = False,
                                          boundary_alpha: float = 0.2, confirm: bool = False,
                                          dry_run: bool = False) -> str:
    """Offset along averaged normals or create thickened Shell with original surface.
    Native solver steps1..100, smoothing0..1, boundary alpha0..0.9; distance +/-1e6.
    Staged bounded input/output/debug/finite checks/replacement undo/dry-run.
    Thickness/closure/intersection quality unproven; IDs/topology may change.
    Confirmed stopped editor/current mesh identities; no save.
    """
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/offset-shell", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "OffsetMode": mode, "OffsetDistance": distance, "OffsetSolveSteps": solve_steps,
        "SmoothingAlpha": smoothing, "bOffsetFixedBoundary": fixed_boundary,
        "bOffsetReproject": reproject_smoothing, "OffsetBoundaryAlpha": boundary_alpha,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inset_outset_geometry_script_faces(actor_path: str, component_path: str, mesh_path: str,
                                        distance: float = 1, area_mode: str = "EntireSelection",
                                        reproject: bool = True, boundary_only: bool = False,
                                        softness: float = 0, area_scale: float = 1, uv_scale: float = 1,
                                        confirm: bool = False, dry_run: bool = False,
                                        selected_triangles: list[int] | None = None,
                                        expected_vertices: list[list[int]] | None = None) -> str:
    """Inset/outset all faces with native signed-distance convention.
    Areas EntireSelection/PerPolygroup/PerTriangle; reproject/boundary/softness/
    area-scale controls. Staged bounded input/output/debug/finite checks and undo.
    IDs/topology/attributes may change; intersection/UV quality unproven.
    Confirmed stopped editor/current identities; no save.
    """
    selected_triangles = selected_triangles or []
    expected_vertices = expected_vertices or []
    if len(selected_triangles) > 256 or len(expected_vertices) != len(selected_triangles) or any(len(v) != 3 for v in expected_vertices):
        raise ValueError("Up to256 selected triangle IDs with matching expected vertex triples required")
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/inset-outset", json={
        "SelectedTriangles": selected_triangles,
        "ExpectedSelectedTriangles": [dict(zip(("X", "Y", "Z"), v)) for v in expected_vertices],
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "ExtrudeDistance": distance, "InsetAreaMode": area_mode, "bInsetReproject": reproject,
        "bInsetBoundaryOnly": boundary_only, "InsetSoftness": softness,
        "InsetAreaScale": area_scale, "ExtrudeUVScale": uv_scale,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def bevel_geometry_script_polygroups(actor_path: str, component_path: str, mesh_path: str,
                                      distance: float = 1, subdivisions: int = 0, round_weight: float = 1,
                                      infer_material: bool = False, material_id: int = 0,
                                      confirm: bool = False, dry_run: bool = False) -> str:
    """Bevel native default-polygroup topology edges without spatial filter.
    Existing groups, distance>0<=1e6/subdivisions0..16/roundness0..10/material0..255.
    Staged bounded input/output/debug/finite checks/replacement undo/dry-run.
    IDs/topology/attributes may change; material slots unchanged, bevel quality
    unproven. Confirmed stopped editor/current owned identities; no save.
    """
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/bevel-polygroups", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "BevelDistance": distance, "BevelSubdivisions": subdivisions,
        "BevelRoundWeight": round_weight, "bBevelInferMaterial": infer_material,
        "MaterialId": material_id, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def offset_geometry_script_faces(actor_path: str, component_path: str, mesh_path: str,
                                   distance: float = 1, offset_type: str = "ParallelFaceOffset",
                                   area_mode: str = "EntireSelection", uv_scale: float = 1,
                                   solids_to_shells: bool = True, confirm: bool = False,
                                   dry_run: bool = False,
                                        selected_triangles: list[int] | None = None,
                                        expected_vertices: list[list[int]] | None = None) -> str:
    """Offset faces by VertexNormal/FaceNormal/ParallelFaceOffset native modeling.
    Areas EntireSelection/PerPolygroup/PerTriangle, existing groups for PerPolygroup.
    Bounded distance/UV scale, shell option; staged input/output/debug/finite checks,
    replacement undo/dry-run. Topology/IDs may change, quality unproven.
    Confirmed stopped editor/current owned identities; no save.
    """
    selected_triangles = selected_triangles or []
    expected_vertices = expected_vertices or []
    if len(selected_triangles) > 256 or len(expected_vertices) != len(selected_triangles) or any(len(v) != 3 for v in expected_vertices):
        raise ValueError("Up to256 selected triangle IDs with matching expected vertex triples required")
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/offset-faces", json={
        "SelectedTriangles": selected_triangles,
        "ExpectedSelectedTriangles": [dict(zip(("X", "Y", "Z"), v)) for v in expected_vertices],
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "ExtrudeDistance": distance, "FaceOffsetType": offset_type, "ExtrudeAreaMode": area_mode,
        "ExtrudeUVScale": uv_scale, "bSolidsToShells": solids_to_shells,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def delete_geometry_script_triangles(actor_path: str, component_path: str, mesh_path: str,
                                      selected_triangles: list[int], expected_vertices: list[list[int]],
                                      confirm: bool = False, dry_run: bool = False) -> str:
    """Delete1..256 unique inspected faces with matching expected vertex-order triples.
    Native deletion can remove newly isolated vertices. Staged bounded copy/exact
    deleted count/face absence/readback/replacement undo/dry-run. Normals/tangents
    not recomputed; current owned mesh/confirmed stopped editor, no save.
    """
    if not 1 <= len(selected_triangles) <= 256 or len(expected_vertices) != len(selected_triangles) or any(len(v) != 3 for v in expected_vertices):
        raise ValueError("1..256 selected triangle IDs and matching vertex triples required")
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/delete-triangles", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "SelectedTriangles": selected_triangles,
        "ExpectedSelectedTriangles": [dict(zip(("X", "Y", "Z"), v)) for v in expected_vertices],
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def flip_geometry_script_selected_normals(actor_path: str, component_path: str, mesh_path: str,
                                           selected_triangles: list[int], expected_vertices: list[list[int]],
                                           flip_winding: bool = True, flip_normals: bool = True,
                                           confirm: bool = False, dry_run: bool = False) -> str:
    """Reverse inspected selected face winding and/or normal direction.
    Nonempty1..256 unique IDs/expected vertex-order triples. Shared normals may
    affect adjacent unselected faces; tangents unchanged. Staged bounded copy,
    selected/unselected winding checks/replacement undo/dry-run; no save.
    """
    if not 1 <= len(selected_triangles) <= 256 or len(expected_vertices) != len(selected_triangles) or any(len(v) != 3 for v in expected_vertices):
        raise ValueError("1..256 selected IDs and matching vertex triples required")
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/flip-selected-normals", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "SelectedTriangles": selected_triangles,
        "ExpectedSelectedTriangles": [dict(zip(("X", "Y", "Z"), v)) for v in expected_vertices],
        "bFlipSelectedWinding": flip_winding, "bFlipSelectedNormals": flip_normals,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_geometry_script_selected_vertex_color(actor_path: str, component_path: str, mesh_path: str,
        selected_triangles: list[int], expected_vertices: list[list[int]],
        red: float = 1, green: float = 1, blue: float = 1, alpha: float = 1,
        set_red: bool = True, set_green: bool = True, set_blue: bool = True, set_alpha: bool = True,
        create_seam: bool = False, confirm: bool = False, dry_run: bool = False) -> str:
    """Color1..256 inspected faces; seam mode isolates colors and ignores channel masks.
    Without seam, shared overlay elements may affect adjacent unselected faces.
    New overlay initializes white. Staged bounded copy/selected-corner readback/
    replacement undo/dry-run. Confirmed stopped editor/current identities; no save.
    """
    if not 1 <= len(selected_triangles) <= 256 or len(expected_vertices) != len(selected_triangles) or any(len(v) != 3 for v in expected_vertices):
        raise ValueError("Selected IDs and matching vertex triples required")
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/selected-vertex-color", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "SelectedTriangles": selected_triangles,
        "ExpectedSelectedTriangles": [dict(zip(("X", "Y", "Z"), v)) for v in expected_vertices],
        "VertexColor": {"R": red, "G": green, "B": blue, "A": alpha},
        "bColorRed": set_red, "bColorGreen": set_green, "bColorBlue": set_blue, "bColorAlpha": set_alpha,
        "bCreateColorSeam": create_seam, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_geometry_script_selected_polygroup(actor_path: str, component_path: str, mesh_path: str,
        selected_triangles: list[int], expected_vertices: list[list[int]], group_id: int = 0,
        generate_new: bool = False, confirm: bool = False, dry_run: bool = False, polygroup_layer: int = -1) -> str:
    """Polygroup layer -1 is default;0..7 selects an existing extended layer.
    Assign default polygroup to1..256 inspected faces, explicit ID or native new ID.
    Enables groups when absent (unselected faces0); otherwise retains unselected
    groups. Staged bounded copy/group-connectivity readback/replacement undo.
    Dry-run does not allocate new ID; current identities/confirmed stopped editor.
    """
    if not 1 <= len(selected_triangles) <= 256 or len(expected_vertices) != len(selected_triangles) or any(len(v) != 3 for v in expected_vertices):
        raise ValueError("Selected IDs and matching vertex triples required")
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/selected-polygroup", json={
        "PolygroupLayerIndex": polygroup_layer, "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "SelectedTriangles": selected_triangles,
        "ExpectedSelectedTriangles": [dict(zip(("X", "Y", "Z"), v)) for v in expected_vertices],
        "TriangleGroup": group_id, "bGenerateNewPolygroup": generate_new,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_geometry_script_selected_material_ids(actor_path: str, component_path: str, mesh_path: str,
        selected_triangles: list[int], expected_vertices: list[list[int]], material_id: int,
        confirm: bool = False, dry_run: bool = False) -> str:
    """Assign material ID0..255 to1..256 inspected faces, retaining other IDs.
    Enables material attribute if absent, initializing other faces0. Component
    slots unchanged. Staged bounded copy/selected-unselected ID/connectivity
    checks/replacement undo/dry-run. Confirmed stopped editor/current identities.
    """
    if not 1 <= len(selected_triangles) <= 256 or len(expected_vertices) != len(selected_triangles) or any(len(v) != 3 for v in expected_vertices):
        raise ValueError("Selected IDs and matching vertex triples required")
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/selected-material-ids", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "SelectedTriangles": selected_triangles,
        "ExpectedSelectedTriangles": [dict(zip(("X", "Y", "Z"), v)) for v in expected_vertices],
        "MaterialId": material_id, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_geometry_script_polygroups(actor_path: str, component_path: str, mesh_path: str,
                                        page_start: int = 0, page_size: int = 64, polygroup_layer: int = -1) -> str:
    """Summarize default(-1) or existing extended(0..7) polygroups by sorted ID with triangle counts/sample face.
    Page ordinal start>=0/size1..256, full bounded triangle scan each call. Groups
    may be disconnected; sample is one face, no topology proof. Current owned mesh/
    stopped editor/read-only/no copy. Ordering may change between requests.
    """
    if page_start < 0 or not 1 <= page_size <= 256:
        raise ValueError("Nonnegative page start and size1..256 required")
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/polygroups/inspect", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "PolygroupLayerIndex": polygroup_layer, "GroupPageStart": page_start, "GroupPageSize": page_size
    }, timeout=60).text


@mcp.tool()
def find_geometry_script_region_faces(actor_path: str, component_path: str, mesh_path: str,
                                       filter_type: str = "Polygroup", filter_id: int = 0,
                                       triangle_start_id: int = 0, result_limit: int = 64, polygroup_layer: int = -1) -> str:
    """Polygroup layer -1 is default;0..7 selects an existing extended layer.
    Find faces by exact Polygroup or Material ID, returning guarded vertex triples.
    Limit1..256 matches, bounded remaining native-ID scan; sparse holes omitted.
    Continuation flag means IDs remain, not necessarily matching faces. Current
    owned mesh/stopped editor, read-only/no copy. No stable revision across calls.
    """
    if filter_type not in ("Polygroup", "Material") or triangle_start_id < 0 or not 1 <= result_limit <= 256:
        raise ValueError("Polygroup/Material, nonnegative start and limit1..256 required")
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/faces/find", json={
        "PolygroupLayerIndex": polygroup_layer, "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "FaceFilter": filter_type, "TriangleGroup": filter_id, "MaterialId": filter_id,
        "TriangleStartId": triangle_start_id, "IdSpan": result_limit
    }, timeout=60).text


@mcp.tool()
def set_geometry_script_polygroup_layer_count(actor_path: str, component_path: str, mesh_path: str,
                                               layer_count: int, confirm: bool = False,
                                               dry_run: bool = False) -> str:
    """Set extended polygroup layers0..8; reducing count discards removed layers.
    Default groups unchanged. Staged bounded copy/layer-count-topology readback/
    replacement undo/dry-run. Inspect polygroups returns up to8 layer names.
    Confirmed stopped editor/current owned identities required; no map save.
    """
    if not 0 <= layer_count <= 8:
        raise ValueError("Extended polygroup layer count0..8 required")
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/polygroup-layer-count", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "PolygroupLayerCount": layer_count, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def copy_geometry_script_polygroup_layer(actor_path: str, component_path: str, mesh_path: str,
                                          source_layer: int, destination_layer: int,
                                          confirm: bool = False, dry_run: bool = False) -> str:
    """Overwrite group values between existing layers -1(default) or extended0..7.
    Same-layer no-op, names/counts unchanged. Staged bounded copy/per-triangle
    source-target group readback/replacement undo/dry-run. Current owned mesh/
    confirmed stopped editor; no save, native callbacks/undo unverified.
    """
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/copy-polygroup-layer", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "SourcePolygroupLayerIndex": source_layer, "PolygroupLayerIndex": destination_layer,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def add_geometry_script_named_polygroup_layer(actor_path: str, component_path: str, mesh_path: str,
                                               name: str, confirm: bool = False,
                                               dry_run: bool = False) -> str:
    """Add named extended polygroup layer or reuse matching native FName (case-insensitive).
    Up to8 layers/name1..128. Existing-name no-op; dry-run new layer has no index.
    Staged bounded copy/index-name-count readback/replacement undo. Native existing
    flag unused due to implementation omission; adapter determines reuse itself.
    Confirmed stopped editor/current identities; no save.
    """
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/polygroup-layers/add-named", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "Name": name, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def clear_geometry_script_polygroup_layer(actor_path: str, component_path: str, mesh_path: str,
                                           layer: int = -1, clear_value: int = 0,
                                           confirm: bool = False, dry_run: bool = False) -> str:
    """Reset all group values in existing default(-1)/extended0..7 layer.
    Clear value0..1000000, all-same no-op. Layer names/counts retained. Staged
    bounded mesh/per-triangle reset readback/replacement undo/dry-run.
    Current owned identities/confirmed stopped editor required; no map save.
    """
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/clear-polygroup-layer", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "PolygroupLayerIndex": layer, "TriangleGroup": clear_value,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def measure_geometry_script_uvs(actor_path: str, component_path: str, mesh_path: str,
                                 uv_layer: int = 0, only_valid_uv_triangles: bool = True) -> str:
    """Read whole-channel mesh/UV area and bounds, including unset UV flag.
    Existing channel0..7/bounded geometry; component-local mesh measurements.
    Option excludes invalid UV triangles from 3D measurements. UV area is no
    overlap/distortion/packing proof, nonfinite results null. Stopped editor/current
    owned mesh/read-only/no copy or mutation.
    """
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/uvs/measure", json={
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "UVLayer": uv_layer, "bOnlyValidUVTriangles": only_valid_uv_triangles
    }, timeout=60).text


@mcp.tool()
def scale_geometry_script_texel_density(actor_path: str, component_path: str, mesh_path: str,
        uv_layer: int = 0, mode: str = "ApplyToIslands", target_world_units: float = 100,
        target_pixel_count: float = 1024, texture_resolution: int = 1024,
        confirm: bool = False, dry_run: bool = False,
        selected_triangles: list[int] | None = None,
        expected_vertices: list[list[int]] | None = None) -> str:
    """Optional inspected face selection; empty retains native whole-mesh behavior.
    Shared UV elements/island processing may affect adjacent unselected faces.
    Scale UV density by ApplyToIslands/ApplyToWhole/Normalize native modes.
    Existing channel0..7, component-local surface units, positive world/pixel
    dimensions and resolution16..8192. No UDIM-specific layout or repacking.
    Staged bounded copy/finite UV/assignment checks/replacement undo/dry-run.
    Density/visual quality unproven; confirmed stopped editor/current identities.
    """
    selected_triangles = selected_triangles or []
    expected_vertices = expected_vertices or []
    if len(selected_triangles) > 256 or len(expected_vertices) != len(selected_triangles) or any(len(v) != 3 for v in expected_vertices):
        raise ValueError("Up to256 selected IDs and matching vertex triples required")
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/texel-density", json={
        "SelectedTriangles": selected_triangles,
        "ExpectedSelectedTriangles": [dict(zip(("X", "Y", "Z"), v)) for v in expected_vertices],
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "UVLayer": uv_layer, "TexelMode": mode, "TexelWorldUnits": target_world_units,
        "TexelPixelCount": target_pixel_count, "UVPackingResolution": texture_resolution,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def recompute_geometry_script_uvs(actor_path: str, component_path: str, mesh_path: str,
        uv_layer: int = 0, method: str = "SpectralConformal", island_source: str = "UVIslands",
        polygroup_layer: int = -1, normal_smoothing_rounds: int = 0, smoothing_alpha: float = 0.25,
        preserve_irregularity: bool = True, auto_align: bool = True,
        confirm: bool = False, dry_run: bool = False,
        selected_triangles: list[int] | None = None,
        expected_vertices: list[list[int]] | None = None) -> str:
    """Optional inspected face selection; empty retains native whole-mesh behavior.
    Shared UV elements/island processing may affect adjacent unselected faces.
    Reunwrap existing UV channel by ExpMap/Conformal/SpectralConformal.
    Islands from UVIslands or existing PolyGroups layer-1/default or0..7 extended.
    ExpMap normal smoothing/spectral irregularity/axis alignment options. No repack.
    Staged bounded copy/debug/finite UV/assignment report/replacement undo/dry-run.
    Quality unproven; tangents unchanged; confirmed stopped editor/current identities.
    """
    selected_triangles = selected_triangles or []
    expected_vertices = expected_vertices or []
    if len(selected_triangles) > 256 or len(expected_vertices) != len(selected_triangles) or any(len(v) != 3 for v in expected_vertices):
        raise ValueError("Up to256 selected IDs and matching vertex triples required")
    return httpx.post(f"{app.BASE_URL}/geometry-script/meshes/recompute-uvs", json={
        "SelectedTriangles": selected_triangles,
        "ExpectedSelectedTriangles": [dict(zip(("X", "Y", "Z"), v)) for v in expected_vertices],
        "ActorPath": actor_path, "ComponentPath": component_path, "MeshPath": mesh_path,
        "UVLayer": uv_layer, "UVFlattenMethod": method, "UVIslandSource": island_source,
        "PolygroupLayerIndex": polygroup_layer, "UVNormalSmoothingRounds": normal_smoothing_rounds,
        "SmoothingAlpha": smoothing_alpha, "bPreserveUVRegularity": preserve_irregularity,
        "bAutoAlignUVIslands": auto_align, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text
