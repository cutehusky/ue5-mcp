"""Physics Assets and collision pairs."""
import httpx

from . import app
from .app import mcp


@mcp.tool()
def inspect_physics_asset(asset_path: str) -> str:
    """Inspect a Physics Asset."""
    return httpx.get(f"{app.BASE_URL}/physics-assets/inspect", params={"asset_path": asset_path}).text


@mcp.tool()
def list_physics_bodies(asset_path: str) -> str:
    """List Physics Asset bodies and primitive-shape counts."""
    return httpx.get(f"{app.BASE_URL}/physics-assets/bodies", params={"asset_path": asset_path}).text


@mcp.tool()
def create_physics_body(asset_path: str, bone_name: str,
                        skeletal_mesh_path: str = "", shape_type: str = "sphere",
                        center: dict | None = None, rotation: dict | None = None,
                        size: dict | None = None, radius: float = 5.0,
                        length: float = 10.0, dry_run: bool = False,
                        save: bool = False, vertices: list[dict] | None = None) -> str:
    """Add a Physics Asset body with an initial sphere, box, capsule, or convex shape."""
    return httpx.post(f"{app.BASE_URL}/physics-assets/bodies", json={
        "AssetPath": asset_path, "Operation": "add", "BoneName": bone_name,
        "SkeletalMeshPath": skeletal_mesh_path, "ShapeType": shape_type,
        "Center": center or {"X": 0, "Y": 0, "Z": 0},
        "Rotation": rotation or {"Pitch": 0, "Yaw": 0, "Roll": 0},
        "Size": size or {"X": 10, "Y": 10, "Z": 10},
        "Radius": radius, "Length": length, "Vertices": vertices or [],
        "bDryRun": dry_run, "bSave": save
    }).text


@mcp.tool()
def delete_physics_body(asset_path: str, bone_name: str,
                        dry_run: bool = False, confirm: bool = False,
                        save: bool = False) -> str:
    """Preview affected constraints/collision pairs and delete a body only with confirm."""
    return httpx.request("DELETE", f"{app.BASE_URL}/physics-assets/bodies", json={
        "AssetPath": asset_path, "BoneName": bone_name,
        "bDryRun": dry_run, "bConfirm": confirm, "bSave": save
    }).text


@mcp.tool()
def list_physics_shapes(asset_path: str, bone_name: str) -> str:
    """List primitive shapes, collision state, and mass contribution on a Physics Asset body."""
    return httpx.get(f"{app.BASE_URL}/physics-assets/shapes", params={
        "asset_path": asset_path, "bone_name": bone_name
    }).text


@mcp.tool()
def add_physics_shape(asset_path: str, bone_name: str, shape_type: str,
                      center: dict | None = None, rotation: dict | None = None,
                      size: dict | None = None, radius: float = 5.0,
                      length: float = 10.0, enable_collision: bool = True,
                      contribute_to_mass: bool = True, dry_run: bool = False,
                      save: bool = False, vertices: list[dict] | None = None) -> str:
    """Add a sphere, box, capsule, or convex shape to an existing Physics Asset body."""
    return httpx.post(f"{app.BASE_URL}/physics-assets/shapes", json={
        "AssetPath": asset_path, "Operation": "add", "BoneName": bone_name,
        "ShapeType": shape_type, "Center": center or {"X": 0, "Y": 0, "Z": 0},
        "Rotation": rotation or {"Pitch": 0, "Yaw": 0, "Roll": 0},
        "Size": size or {"X": 10, "Y": 10, "Z": 10},
        "Radius": radius, "Length": length, "Vertices": vertices or [],
        "bEnableCollision": enable_collision,
        "bContributeToMass": contribute_to_mass,
        "bDryRun": dry_run, "bSave": save
    }).text


@mcp.tool()
def delete_physics_shape(asset_path: str, bone_name: str,
                         shape_type: str, shape_index: int,
                         dry_run: bool = False, confirm: bool = False,
                         save: bool = False) -> str:
    """Preview or remove one Physics Asset shape; deletion requires confirm."""
    return httpx.request("DELETE", f"{app.BASE_URL}/physics-assets/shapes", json={
        "AssetPath": asset_path, "BoneName": bone_name,
        "ShapeType": shape_type, "ShapeIndex": shape_index,
        "bDryRun": dry_run, "bConfirm": confirm, "bSave": save
    }).text


@mcp.tool()
def list_physics_constraints(asset_path: str) -> str:
    """List Physics Asset constraint names and connected bones."""
    return httpx.get(f"{app.BASE_URL}/physics-assets/constraints", params={"asset_path": asset_path}).text


@mcp.tool()
def inspect_physics_constraint_drive(asset_path: str, constraint_name: str) -> str:
    """Inspect linear and angular drives for a Physics Asset constraint."""
    return httpx.get(f"{app.BASE_URL}/physics-assets/drives", params={
        "asset_path": asset_path, "constraint_name": constraint_name
    }).text


@mcp.tool()
def list_physics_constraint_profiles(asset_path: str, constraint_name: str = "") -> str:
    """List constraint profiles, coverage, and optional selected constraint drive strengths."""
    return httpx.get(f"{app.BASE_URL}/physics-assets/profiles", params={
        "asset_path": asset_path, "constraint_name": constraint_name
    }).text


@mcp.tool()
def list_physics_body_profiles(asset_path: str, bone_name: str = "") -> str:
    """List Physical Animation profiles and optional settings for one body."""
    return httpx.get(f"{app.BASE_URL}/physics-assets/body-profiles", params={
        "asset_path": asset_path, "bone_name": bone_name
    }).text


@mcp.tool()
def inspect_physics_body_settings(asset_path: str, bone_name: str) -> str:
    """Inspect a Physics Asset body's type, collision, mass, bounds, and CCD settings."""
    return httpx.get(f"{app.BASE_URL}/physics-assets/body-settings", params={
        "asset_path": asset_path, "bone_name": bone_name
    }).text


@mcp.tool()
def edit_physics_body_settings(asset_path: str, bone_name: str,
                               settings: dict[str, str], dry_run: bool = False,
                               save: bool = False) -> str:
    """Edit allowlisted Physics Asset body settings after transient preflight."""
    return httpx.patch(f"{app.BASE_URL}/physics-assets/body-settings", json={
        "AssetPath": asset_path, "BoneName": bone_name,
        "Settings": {key: str(value).lower() if isinstance(value, bool) else str(value)
                     for key, value in settings.items()},
        "bDryRun": dry_run, "bSave": save
    }).text


@mcp.tool()
def edit_physics_body_profile(asset_path: str, operation: str, profile_name: str,
                              bone_name: str = "", source_profile_name: str = "",
                              new_name: str = "", settings: dict | None = None,
                              dry_run: bool = False, confirm: bool = False,
                              save: bool = False) -> str:
    """Add, duplicate, rename, edit, or confirm deletion of a Physical Animation profile."""
    return httpx.post(f"{app.BASE_URL}/physics-assets/body-profiles", json={
        "AssetPath": asset_path, "Operation": operation,
        "ProfileName": profile_name, "BoneName": bone_name,
        "SourceProfileName": source_profile_name, "NewName": new_name,
        **(settings or {}), "bDryRun": dry_run,
        "bConfirm": confirm, "bSave": save
    }).text


@mcp.tool()
def edit_physics_constraint_profile(asset_path: str, operation: str,
                                    profile_name: str, source_profile_name: str = "",
                                    new_name: str = "", constraint_name: str = "",
                                    dry_run: bool = False, confirm: bool = False,
                                    save: bool = False) -> str:
    """Add, duplicate, rename, capture, or confirm deletion of a constraint profile."""
    return httpx.post(f"{app.BASE_URL}/physics-assets/profiles", json={
        "AssetPath": asset_path, "Operation": operation,
        "ProfileName": profile_name, "SourceProfileName": source_profile_name,
        "NewName": new_name, "ConstraintName": constraint_name,
        "bDryRun": dry_run, "bConfirm": confirm, "bSave": save
    }).text


@mcp.tool()
def edit_physics_constraint_drive(asset_path: str, constraint_name: str,
                                  drive_type: str, settings: dict,
                                  dry_run: bool = False, save: bool = False) -> str:
    """Set a full linear or angular drive using UE field names for flags, strengths, and targets."""
    return httpx.patch(f"{app.BASE_URL}/physics-assets/drives", json={
        "AssetPath": asset_path, "ConstraintName": constraint_name,
        "DriveType": drive_type, **settings,
        "bDryRun": dry_run, "bSave": save
    }).text


@mcp.tool()
def create_physics_constraint(asset_path: str, constraint_name: str,
                              child_bone: str, parent_bone: str,
                              linear_motion: str = "", angular_motion: str = "",
                              linear_limit: float = -1.0, swing1_limit: float = -1.0,
                              swing2_limit: float = -1.0, twist_limit: float = -1.0,
                              projection: str = "", dry_run: bool = False,
                              save: bool = False) -> str:
    """Connect two Physics Asset bodies with typed linear/angular limits and optional projection."""
    return httpx.post(f"{app.BASE_URL}/physics-assets/constraints", json={
        "AssetPath": asset_path, "Operation": "add", "ConstraintName": constraint_name,
        "ChildBone": child_bone, "ParentBone": parent_bone,
        "LinearMotion": linear_motion, "AngularMotion": angular_motion,
        "LinearLimit": linear_limit, "Swing1Limit": swing1_limit,
        "Swing2Limit": swing2_limit, "TwistLimit": twist_limit,
        "Projection": projection, "bDryRun": dry_run, "bSave": save
    }).text


@mcp.tool()
def edit_physics_constraint(asset_path: str, constraint_name: str,
                            child_bone: str = "", parent_bone: str = "",
                            linear_motion: str = "", angular_motion: str = "",
                            linear_limit: float = -1.0, swing1_limit: float = -1.0,
                            swing2_limit: float = -1.0, twist_limit: float = -1.0,
                            projection: str = "", dry_run: bool = False,
                            save: bool = False) -> str:
    """Edit Physics Asset constraint body association, limits, and projection."""
    return httpx.patch(f"{app.BASE_URL}/physics-assets/constraints", json={
        "AssetPath": asset_path, "ConstraintName": constraint_name,
        "ChildBone": child_bone, "ParentBone": parent_bone,
        "LinearMotion": linear_motion, "AngularMotion": angular_motion,
        "LinearLimit": linear_limit, "Swing1Limit": swing1_limit,
        "Swing2Limit": swing2_limit, "TwistLimit": twist_limit,
        "Projection": projection, "bDryRun": dry_run, "bSave": save
    }).text


@mcp.tool()
def delete_physics_constraint(asset_path: str, constraint_name: str,
                              dry_run: bool = False, confirm: bool = False,
                              save: bool = False) -> str:
    """Preview or delete a Physics Asset constraint; deletion requires confirm."""
    return httpx.request("DELETE", f"{app.BASE_URL}/physics-assets/constraints", json={
        "AssetPath": asset_path, "ConstraintName": constraint_name,
        "bDryRun": dry_run, "bConfirm": confirm, "bSave": save
    }).text


@mcp.tool()
def list_physics_collision_pairs(asset_path: str) -> str:
    """List disabled collision pairs in a Physics Asset."""
    return httpx.get(f"{app.BASE_URL}/physics-assets/collision-pairs", params={"asset_path": asset_path}).text


@mcp.tool()
def set_physics_collision_pair(asset_path: str, bone_name: str,
                               other_bone_name: str, enable_collision: bool,
                               dry_run: bool = False, save: bool = False) -> str:
    """Enable or disable collision between two Physics Asset bodies."""
    return httpx.patch(f"{app.BASE_URL}/physics-assets/collision-pairs", json={
        "AssetPath": asset_path, "BoneName": bone_name,
        "OtherBoneName": other_bone_name,
        "bEnableCollision": enable_collision,
        "bDryRun": dry_run, "bSave": save
    }).text


@mcp.tool()
def validate_physics_asset(asset_path: str) -> str:
    """Check Physics Asset body geometry, duplicate bones, preview mesh, and constraint references."""
    return httpx.get(f"{app.BASE_URL}/physics-assets/validate", params={"asset_path": asset_path}).text


@mcp.tool()
def refresh_physics_asset(asset_path: str) -> str:
    """Refresh Physics Asset body caches and notify editor previews."""
    return httpx.post(f"{app.BASE_URL}/physics-assets/refresh", json={"AssetPath": asset_path}).text


@mcp.tool()
def inspect_physics_volume(actor_path: str) -> str:
    """Read native physics volume priority/friction/terminal velocity/water/contact flags and gravity.
    No overlap refresh or simulation proof; read-only/no save.
    """
    return httpx.post(f"{app.BASE_URL}/volumes/physics/inspect", json={"ActorPath": actor_path}, timeout=60).text


@mcp.tool()
def set_physics_volume_setting(actor_path: str, field: str, expected_value: float,
                                 scalar_value: float = 0, bool_value: bool = False,
                                 confirm: bool = False, dry_run: bool = False) -> str:
    """Set Priority(int32), TerminalVelocity/FluidFriction(0..1e6), WaterVolume/PhysicsOnContact(bool).
    Exact inspected field-value guard; boolean expected values0/1, floats use native precision.
    Transaction/property notification/readback/dry-run/no-op/no save. Unverified.
    """
    return httpx.post(f"{app.BASE_URL}/volumes/physics/settings", json={
        "ActorPath": actor_path, "FieldName": field, "ExpectedScalarValue": expected_value,
        "ScalarValue": scalar_value, "bBoolValue": bool_value, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text
