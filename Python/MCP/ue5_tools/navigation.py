"""Navigation meshes, areas and smart links."""
import httpx

from . import app
from .app import merged_tool
from .app import mcp


@mcp.tool()
def control_navigation_agent(probe_id: str, operation: str = "create", pie_instance: int = -1,
                               location: dict | None = None, destination: dict | None = None,
                               speed: float = 300, duration_seconds: float = 30,
                               acceptance_radius: float = 20, filter_class: str = "",
                               smart_link_path: str = "", allow_partial: bool = False, project_goal: bool = True,
                               dry_run: bool = False) -> str:
    """Control an owned transient native character/controller probe in selected PIE.

    Operations: create/move/stop/pause/resume/release/watch_link/unwatch_link/resume_link. Create projects a feet location
    and uses the default nav-data agent's capsule dimensions. Speed is 10-1200;
    wall-clock lifetime 0.2-120 seconds. Move uses native AIController pathfinding,
    optional filter/partial path policy and acceptance radius 0-2000. There is no
    teleport or control of existing user actors. Native completion events are polled
    separately. Up to 16 retained probes/world, 128 global, 256 retained events/probe.
    Expiry destroys owned actors and retains final state until release; PIE cleanup
    removes records. Dry-run preflights without spawning or submitting movement.
    watch_link observes one relevant selected-PIE proxy via its multicast delegate.
    Poll smart_link_reached events; resume_link resumes only this pawn while native
    path following uses the watched link. This clears native custom-link use; it does
    not resume a separately paused request. Reached events do not auto-pause movement.
    Existing Blueprint callbacks remain active.
    Stop/resume a used link before unwatching. This supplies no jump animation.
    """
    return httpx.post(f"{app.BASE_URL}/navigation/agents", json={
        "ProbeId": probe_id, "Operation": operation, "PIEInstance": pie_instance,
        "Location": location or {"X": 0, "Y": 0, "Z": 0},
        "Destination": destination or {"X": 0, "Y": 0, "Z": 0}, "Speed": speed,
        "DurationSeconds": duration_seconds, "AcceptanceRadius": acceptance_radius,
        "FilterClass": filter_class, "SmartLinkPath": smart_link_path, "bAllowPartial": allow_partial,
        "bProjectGoal": project_goal, "bDryRun": dry_run
    }).text


@mcp.tool()
def inspect_navigation_agent(probe_id: str, pie_instance: int = -1,
                              after_sequence: int = 0, limit: int = 100) -> str:
    """Poll native probe position/velocity, path status/request and paged completion/link events.

    after_sequence is an exclusive cursor; limit is 1-256. oldest_sequence reveals
    event eviction. Expired probes report frozen final position and dead actors.
    Completion result/flags come from native path following, not inferred distance.
    """
    return httpx.get(f"{app.BASE_URL}/navigation/agents", params={
        "probe_id": probe_id, "pie_instance": pie_instance,
        "after_sequence": after_sequence, "limit": limit
    }).text


@mcp.tool()
def inspect_navigation_links(actor_path: str = "", world_context: str = "editor", pie_instance: int = -1) -> str:
    """Inspect native proxies in editor or selected PIE world; ambiguous PIE worlds require an explicit index."""
    return httpx.get(f"{app.BASE_URL}/navigation/links", params={
        "actor_path": actor_path, "world_context": world_context, "pie_instance": pie_instance
    }).text


def set_smart_navigation_link(operation: str, actor_path: str = "", left: dict | None = None,
                               right: dict | None = None, direction: str = "BothWays",
                               enabled_area_class: str = "/Script/NavigationSystem.NavArea_Default",
                               disabled_area_class: str = "/Script/NavigationSystem.NavArea_Null",
                               relevant: bool = True, enabled: bool = True,
                               agent_indices: list[int] | None = None,
                               location: dict | None = None, rotation: dict | None = None,
                               label: str = "", world_path: str = "", confirm: bool = False,
                               dry_run: bool = False, save: bool = False) -> str:
    """Create/update/delete a smart-only native proxy in an ordinary persistent editor map.

    Update supplies complete actor transform, local endpoints, direction, enabled/
    disabled areas and relevance/enabled state. Agent indices None preserves; []
    selects no agents. Existing simple/segment links and custom proxy classes are
    excluded from mutation. Creation removes the native default simple link so it
    cannot bypass the smart link. Native component setters, preflight, dry-run/no-op,
    transactions and optional map save are used. Stop PIE/simulation before authoring.
    Geometry/relevance changes need generation; traversal callbacks are separate.
    """
    return httpx.post(f"{app.BASE_URL}/navigation/smart-links", json={
        "Operation": operation, "ActorPath": actor_path,
        "SmartLeft": left or {"X": -100, "Y": 0, "Z": 0},
        "SmartRight": right or {"X": 100, "Y": 0, "Z": 0},
        "SmartDirection": direction, "EnabledAreaClass": enabled_area_class,
        "DisabledAreaClass": disabled_area_class, "bSmartLinkRelevant": relevant, "bEnabled": enabled,
        "bSetSmartAgents": agent_indices is not None, "SmartAgentIndices": agent_indices or [],
        "Location": location or {"X": 0, "Y": 0, "Z": 0},
        "Rotation": rotation or {"Pitch": 0, "Yaw": 0, "Roll": 0}, "Label": label,
        "WorldPath": world_path, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }).text


def set_runtime_smart_link_enabled(actor_path: str, enabled: bool, pie_instance: int = -1,
                                   dry_run: bool = False) -> str:
    """Toggle a relevant native smart link in a selected PIE world without saving editor assets.

    Use inspect_navigation_links(world_context='pie') to get its actual PIE actor
    path; editor-world paths are rejected. Uses UE's native enabled/disabled area
    update and preserves existing movement delegates. Dry-run and no-op are supported.
    Confirm connectivity with query_navigation(world_context='pie'). This does not
    install traversal callbacks or move agents across the link.
    """
    return httpx.post(f"{app.BASE_URL}/navigation/smart-links", json={
        "Operation": "set_enabled", "ActorPath": actor_path, "WorldContext": "pie",
        "PIEInstance": pie_instance, "bEnabled": enabled, "bDryRun": dry_run
    }).text


@mcp.tool()
def set_navigation_links(operation: str, point_links: list[dict] | None = None,
                          actor_path: str = "", location: dict | None = None,
                          rotation: dict | None = None, label: str = "", world_path: str = "",
                          confirm: bool = False, dry_run: bool = False, save: bool = False) -> str:
    """Create/update/delete a native simple-link proxy in an ordinary persistent editor level.

    Update replaces the full point-link list and actor translation/rotation, using
    unit scale. [] clears links. Up to 64 rows use actor-local Left/Right (X/Y/Z),
    Direction (BothWays/LeftToRight/RightToLeft), AreaClass, SnapRadius/SnapHeight,
    bUseSnapHeight, bSnapToCheapestArea, LeftProjectHeight/RightProjectHeight and
    optional bSetSupportedAgents/SupportedAgentIndices (unique 0-15).
    Stop PIE/simulation. Delete requires confirmation. Supports preflight, dry-run,
    no-op, native transactions and optional persistent-map save. Relevant smart
    links, segment links and derived/custom proxy classes are excluded from mutation. Rebuild and query to verify
    generated connectivity; off_mesh_connection flags identify actual path links.
    This does not implement smart-link callbacks or AI movement across links.
    """
    return httpx.post(f"{app.BASE_URL}/navigation/links", json={
        "Operation": operation, "ActorPath": actor_path, "PointLinks": point_links or [],
        "Location": location or {"X": 0, "Y": 0, "Z": 0},
        "Rotation": rotation or {"Pitch": 0, "Yaw": 0, "Roll": 0}, "Label": label,
        "WorldPath": world_path, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }).text


@mcp.tool()
def inspect_navigation_area(asset_path: str) -> str:
    """Inspect a direct-native-parent NavArea Blueprint's costs, color, agents and validation."""
    return httpx.get(f"{app.BASE_URL}/navigation/areas", params={"asset_path": asset_path}).text


@mcp.tool()
def set_navigation_area(asset_path: str, operation: str = "update", default_cost: float = -1,
                        entering_cost: float = -1, draw_color: list[int] | None = None,
                        supported_agent_indices: list[int] | None = None,
                        dry_run: bool = False, save: bool = False) -> str:
    """Create/update a Blueprint whose direct native parent is NavArea.

    Costs accept -1 to preserve or [0,1e6]. Color is four RGBA bytes; None preserves.
    Agent indices are unique 0-15 and refer to project agent definitions; None
    preserves, [] disables all agents. Native area flags are read-only. Supports
    whole-request preflight, dry-run/no-op, compile, undo/redo refresh and optional
    asset save. Stop PIE/simulation before mutation; inspection works during PIE.
    Use returned area_class with navigation modifiers/filters. Native registration
    updates live systems; rebuild navigation to verify painted-region behavior.
    Custom/inherited native area bases and agent-definition editing remain separate.
    """
    return httpx.post(f"{app.BASE_URL}/navigation/areas", json={
        "AssetPath": asset_path, "Operation": operation, "DefaultCost": default_cost,
        "EnteringCost": entering_cost, "DrawColor": draw_color or [],
        "bSetSupportedAgents": supported_agent_indices is not None,
        "SupportedAgentIndices": supported_agent_indices or [], "bDryRun": dry_run, "bSave": save
    }).text


@mcp.tool()
def inspect_navigation_filter(asset_path: str) -> str:
    """Inspect a compiled /Game Blueprint with direct native NavigationQueryFilter parent."""
    return httpx.get(f"{app.BASE_URL}/navigation/filters", params={"asset_path": asset_path}).text


@mcp.tool()
def set_navigation_filter(asset_path: str, operation: str = "update",
                           areas: list[dict] | None = None, include_flags: int = -1,
                           exclude_flags: int = -1, dry_run: bool = False,
                           save: bool = False) -> str:
    """Create/update a native NavigationQueryFilter Blueprint and compile its defaults.

    operation is create or update. areas=None preserves rows; [] clears them. Up to
    64 unique rows use AreaClass, bExcluded, bOverrideTravelCost, TravelCost [1,1e6],
    bOverrideEnteringCost, EnteringCost [0,1e6]. AreaClass is a concrete compatible
    NavArea class path. Include/exclude masks are 16-bit; -1 preserves a mask.
    Whole-request preflight, dry-run, clean no-op, native transactions/cache
    invalidation and optional asset save are supported. Stop PIE/simulation first.
    Inspect returns filter_class for query_navigation. Effects depend on the selected
    nav data's registered areas; this does not author area classes or nav modifiers.
    Only filters with the direct native parent are edited; inherited/custom filters
    require their own adapter. Dry-run returns current defaults and would_change.
    """
    return httpx.post(f"{app.BASE_URL}/navigation/filters", json={
        "AssetPath": asset_path, "Operation": operation, "bSetAreas": areas is not None,
        "Areas": areas or [], "IncludeFlags": include_flags, "ExcludeFlags": exclude_flags,
        "bDryRun": dry_run, "bSave": save
    }).text


@mcp.tool()
def inspect_navigation() -> str:
    """Inspect active editor-world native navigation data, bounded bounds rows and native build/task state."""
    return httpx.get(f"{app.BASE_URL}/navigation/inspect").text


@mcp.tool()
def set_navigation_bounds(operation: str, actor_path: str = "", location: dict | None = None,
                          extent: dict | None = None, label: str = "", world_path: str = "",
                          confirm: bool = False, dry_run: bool = False, save: bool = False) -> str:
    """Create/update/delete an axis-aligned native box NavMeshBoundsVolume in the persistent level.

    extent contains half extents (X/Y/Z, each 1-100000 units). Update supplies full
    location/extent and resets rotation/scale to axis aligned unit scale. Delete
    requires actor_path and confirm. Ordinary editor maps only; stop PIE/simulation.
    Uses native brush geometry, transactions and navigation bounds notification.
    Optional save saves the entire existing /Game map, including prior unsaved edits.
    Bounds edits can queue native background nav-data work; inspect build state.
    """
    return httpx.post(f"{app.BASE_URL}/navigation/bounds", json={
        "Operation": operation, "ActorPath": actor_path, "Location": location or {"X": 0, "Y": 0, "Z": 0},
        "Extent": extent or {"X": 500, "Y": 500, "Z": 250}, "Label": label, "WorldPath": world_path,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }).text


@mcp.tool()
def set_navigation_modifier(operation: str, actor_path: str = "", location: dict | None = None,
                              extent: dict | None = None,
                              area_class: str = "/Script/NavigationSystem.NavArea_Obstacle",
                              area_class_to_replace: str = "", label: str = "",
                              world_path: str = "", confirm: bool = False,
                              dry_run: bool = False, save: bool = False) -> str:
    """Create/update/delete an axis-aligned box NavModifierVolume in an ordinary persistent level.

    Supply complete location/half-extents and area references on update. area_class
    paints navigation areas; empty disables painting. area_class_to_replace limits
    replacement to that area; empty clears the restriction. Use compatible concrete
    NavArea class paths. Delete requires confirmation. Preflight, dry-run/no-op,
    native brush geometry/undo, native area setters and optional map save are supported.
    Stop PIE/simulation first. Geometry changes need native generation before query
    results reflect them; inspect_navigation returns bounded modifier rows/build state.
    """
    return httpx.post(f"{app.BASE_URL}/navigation/modifiers", json={
        "Operation": operation, "ActorPath": actor_path,
        "Location": location or {"X": 0, "Y": 0, "Z": 0},
        "Extent": extent or {"X": 500, "Y": 500, "Z": 250},
        "AreaClass": area_class, "AreaClassToReplace": area_class_to_replace,
        "Label": label, "WorldPath": world_path, "bConfirm": confirm,
        "bDryRun": dry_run, "bSave": save
    }).text


@mcp.tool()
def build_navigation(confirm: bool = False, dry_run: bool = False,
                     save: bool = False, world_path: str = "") -> str:
    """Run UE's blocking current-world navigation build and report native task/data state.

    Requires confirmation, eligible bounds, no running generation tasks, and an ordinary editor
    map with PIE/simulation stopped. This waits for native generation; it is not an
    asynchronous job and cannot cancel while the game thread is building. Dry-run
    performs preflight only. Optional save saves the whole map. Use projection/path
    queries to verify navigability; idle task state alone does not establish success.
    World Partition navigation builders remain a separate workflow.
    """
    return httpx.post(f"{app.BASE_URL}/navigation/build", json={
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save, "WorldPath": world_path
    }, timeout=600).text


def sample_navigation_points(origin: dict, radius: float = 500, sample_count: int = 1,
                              reachable: bool = True, project_origin: bool = True,
                              query_extent: dict | None = None, nav_data_path: str = "",
                              filter_class: str = "", max_search_nodes: int = 2048,
                              world_context: str = "editor", pie_instance: int = -1) -> str:
    """Sample native random reachable or navigable points using selected editor/PIE nav data.

    origin/extent use X/Y/Z. Reachable points use UE's native reachable query;
    navigable points need not connect to the origin. Radius is (0,100000], count
    1-32. Optional origin projection reports failure without inventing points.
    Uses a copied filter with a bounded search-node count. Samples are neither
    deterministic nor guaranteed unique. Radius follows native navigation query
    geometry, not a guaranteed 3D Euclidean sphere. This never creates nav data.
    """
    return httpx.post(f"{app.BASE_URL}/navigation/query", json={
        "Operation": "random_reachable" if reachable else "random_navigable",
        "Start": origin, "Radius": radius, "SampleCount": sample_count,
        "bProjectEndpoints": project_origin,
        "QueryExtent": query_extent or {"X": 100, "Y": 100, "Z": 300},
        "NavDataPath": nav_data_path, "FilterClass": filter_class,
        "MaxSearchNodes": max_search_nodes, "WorldContext": world_context, "PIEInstance": pie_instance
    }).text


def inspect_navigation_filter_costs(nav_data_path: str = "", filter_class: str = "",
                                    world_context: str = "editor", pie_instance: int = -1) -> str:
    """Inspect native registered area IDs and effective cached query-filter costs/flags.

    Select native data explicitly or use its default without creating data. Supports
    editor/PIE world selection. Output is bounded to data with at most 256 cost slots;
    costs alone do not establish passability. No search is run and cached filters
    are not modified. Reported node limit precedes per-query overrides.
    """
    return httpx.post(f"{app.BASE_URL}/navigation/query", json={
        "Operation": "inspect_filter", "NavDataPath": nav_data_path,
        "FilterClass": filter_class, "WorldContext": world_context, "PIEInstance": pie_instance
    }).text


def query_navigation(start: dict, end: dict | None = None, operation: str = "path",
                      query_extent: dict | None = None, nav_data_path: str = "",
                      filter_class: str = "", project_endpoints: bool = True,
                      allow_partial: bool = False, max_search_nodes: int = 2048,
                      max_points: int = 256, cost_limit: float = 1e9, world_path: str = "",
                      world_context: str = "editor", pie_instance: int = -1) -> str:
    """Run a native editor/selected-PIE path or projection query without creating nav data.

    Coordinates and projection extent use X/Y/Z. Select an inspected nav_data_path
    or use native default data. filter_class optionally selects a compatible concrete
    navigation filter. A copied filter limits search nodes without editing defaults.
    Path queries can project both endpoints first; failed projection reports queried=false.
    Partial paths are explicit. max_points truncates returned rows, preserving full
    native point count/length/cost. Results describe the current native mesh and filter.
    world_context is editor or pie; multiple PIE worlds require an explicit index.
    world_path guards the selected world package. PIE queries never edit editor assets.
    """
    return httpx.post(f"{app.BASE_URL}/navigation/query", json={
        "Operation": operation, "Start": start, "End": end or start,
        "QueryExtent": query_extent or {"X": 100, "Y": 100, "Z": 300},
        "NavDataPath": nav_data_path, "FilterClass": filter_class,
        "bProjectEndpoints": project_endpoints, "bAllowPartial": allow_partial,
        "MaxSearchNodes": max_search_nodes, "MaxPoints": max_points,
        "CostLimit": cost_limit, "WorldPath": world_path,
        "WorldContext": world_context, "PIEInstance": pie_instance
    }).text


# Tools listed to clients. Each picks one of the functions above with its variant argument.
edit_smart_navigation_link = merged_tool("edit_smart_navigation_link", {
    "set_smart_navigation_link": set_smart_navigation_link,
    "set_runtime_smart_link_enabled": set_runtime_smart_link_enabled,
})
navigation_query = merged_tool("navigation_query", {
    "sample_navigation_points": sample_navigation_points,
    "inspect_navigation_filter_costs": inspect_navigation_filter_costs,
    "query_navigation": query_navigation,
})
