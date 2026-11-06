"""IK Rigs and IK Retargeters."""
import httpx

from . import app
from .app import merged_tool
from .app import mcp


@mcp.tool()
def set_skeleton_translation_retargeting(asset_path: str, bones: list[str],
                                         mode: str = "Animation", children: bool = False,
                                         confirm: bool = False, dry_run: bool = False,
                                         save: bool = False) -> str:
    """Set native Skeleton bone translation retargeting mode transactionally.

    Modes: Animation, Skeleton, AnimationScaled, AnimationRelative, OrientAndScale.
    Requires stopped PIE, confirmed /Game Skeleton and 1..256 unique raw bone names.
    children includes descendants; reports affected/changed counts. No IK Retargeter
    editing or animation rebake. Structure inspector returns numeric native modes 0..4.
    """
    return httpx.patch(f"{app.BASE_URL}/skeletons/translation-retargeting", json={
        "AssetPath": asset_path, "Bones": bones, "Mode": mode, "bChildren": children,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_skeleton_compatibility_retarget_policy(asset_path: str, enabled: bool,
                                                confirm: bool = False,
                                                dry_run: bool = False, save: bool = False) -> str:
    """Set native use-retarget-modes-from-compatible-Skeleton policy.

    Requires confirmed /Game Skeleton and stopped PIE; transaction, no-op/dry-run,
    optional save and before/current readback. Does not edit compatibility lists,
    source Skeletons or animation data.
    """
    return httpx.patch(f"{app.BASE_URL}/skeletons/compatibility/policy", json={
        "AssetPath": asset_path, "bUseCompatibleRetargetModes": enabled,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def inspect_skeleton_retarget_pose(asset_path: str, pose_name: str,
                                    bones: list[str] | None = None) -> str:
    """Read stored named retarget-source pose transforms without loading source mesh.

    <=256 unique raw bone names or first <=256 bones when omitted; availability and
    finite-safe local transforms returned. Structure inspection lists source names and
    soft mesh links. Does not rebuild source poses or evaluate/retarget animations.
    """
    return httpx.post(f"{app.BASE_URL}/skeletons/retarget-sources/pose", json={
        "AssetPath": asset_path, "PoseName": pose_name, "Bones": bones or []
    }, timeout=180).text


@mcp.tool()
def edit_skeleton_retarget_source(asset_path: str, pose_name: str, source_mesh_path: str,
                                   operation: str = "create", confirm: bool = False,
                                   dry_run: bool = False, save: bool = False) -> str:
    """Create/refresh named native retarget-source pose from exact-Skeleton mesh.

    Requires confirmed /Game Skeleton, stopped PIE and registered persistent mesh
    using that Skeleton. Preflights native pose build and finite transforms; native
    update/callback, transaction/no-op/dry-run/optional save. Does not rebake animations.
    """
    return httpx.post(f"{app.BASE_URL}/skeletons/retarget-sources", json={
        "AssetPath": asset_path, "PoseName": pose_name, "SourceMeshPath": source_mesh_path,
        "Operation": operation, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_animation_named_retarget_source(asset_path: str, pose_name: str = "",
                                         confirm: bool = False, dry_run: bool = False,
                                         save: bool = False) -> str:
    """Select sequence Skeleton's named retarget source, or default with empty/None name.

    Requires confirmed /Game AnimSequence and stopped PIE; validates named source.
    Clears per-animation source-mesh override. Transaction/native property notification
    may rebuild derived data; optional save. No IK Retargeter/cross-Skeleton rebake.
    """
    return httpx.patch(f"{app.BASE_URL}/animations/retarget-source", json={
        "AssetPath": asset_path, "PoseName": pose_name, "bConfirm": confirm,
        "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_animation_retarget_source_mesh(asset_path: str, source_mesh_path: str,
                                        confirm: bool = False, dry_run: bool = False,
                                        save: bool = False) -> str:
    """Select/refresh per-sequence source-mesh reference pose and clear named source.

    Confirmed /Game AnimSequence, stopped PIE and exact-Skeleton persistent mesh.
    Native pose preflight, source setter/data refresh and transaction/optional save.
    Repeated calls refresh pose even if mesh selection is unchanged. No animation rebake.
    """
    return httpx.patch(f"{app.BASE_URL}/animations/retarget-source/mesh", json={
        "AssetPath": asset_path, "SourceMeshPath": source_mesh_path,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def inspect_animation_retarget_source(asset_path: str, bones: list[str] | None = None) -> str:
    """Read sequence retarget selection and native effective reference pose.

    <=256 unique raw bones or first <=256 if omitted. Returns named-source validity,
    soft source mesh, native effective source identity and finite-safe local transforms.
    Native cached mesh-pose precedence/fallback applies; no source mesh load or refresh.
    """
    return httpx.post(f"{app.BASE_URL}/animations/retarget-source/query", json={
        "AssetPath": asset_path, "Bones": bones or []
    }, timeout=180).text


@mcp.tool()
def delete_skeleton_retarget_source(asset_path: str, pose_name: str,
                                     allow_referenced: bool = False, confirm: bool = False,
                                     dry_run: bool = False, save: bool = False) -> str:
    """Delete named Skeleton retarget source with animation consumer checks.

    Confirmed /Game Skeleton and stopped PIE. Scans <=256 registry-tag candidates
    (loads to verify Skeleton) plus loaded sequences. Blocks consumers unless explicit
    allow_referenced; dry-run reports them. Stale registry/custom users may be absent.
    Does not rewrite animations; native missing-source fallback applies after deletion.
    """
    return httpx.request("DELETE", f"{app.BASE_URL}/skeletons/retarget-sources", json={
        "AssetPath": asset_path, "PoseName": pose_name, "bAllowReferenced": allow_referenced,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def rename_skeleton_retarget_source(asset_path: str, pose_name: str, new_name: str,
                                     confirm: bool = False, dry_run: bool = False,
                                     save: bool = False) -> str:
    """Rename named retarget source and migrate discovered /Game animation consumers.

    Confirmed /Game Skeleton/stopped PIE, distinct unused destination. Registry-tag
    candidates and loaded sequences checked (<=256); all consumers must be persistent
    /Game assets. Single transaction, separate optional package saves can partially
    succeed. Stale registry/custom users may be absent. Dry-run lists migration scope.
    """
    return httpx.patch(f"{app.BASE_URL}/skeletons/retarget-sources/name", json={
        "AssetPath": asset_path, "PoseName": pose_name, "NewName": new_name,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def duplicate_skeleton_retarget_source(asset_path: str, pose_name: str, new_name: str,
                                        confirm: bool = False, dry_run: bool = False,
                                        save: bool = False) -> str:
    """Copy stored retarget-source pose and soft mesh link into unused name.

    Confirmed /Game Skeleton/stopped PIE, <64 sources, <=4096 finite transforms.
    Transaction/native callback/optional save; no source mesh loading/rebuild or
    animation consumer migration. Supports preserved poses with missing source meshes.
    """
    return httpx.post(f"{app.BASE_URL}/skeletons/retarget-sources/duplicate", json={
        "AssetPath": asset_path, "PoseName": pose_name, "NewName": new_name,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


def edit_skeleton_stored_retarget_pose(asset_path: str, pose_name: str, edits: list[dict],
                                        clear_source_mesh: bool = False,
                                        confirm: bool = False, dry_run: bool = False,
                                        save: bool = False) -> str:
    """Edit <=256 stored local retarget-pose bone transforms with transaction.

    Each row: Bone, Location {X,Y,Z}, Rotation {Pitch,Yaw,Roll}, Scale {X,Y,Z}.
    Confirmed /Game Skeleton/stopped PIE; unique raw bones with stored transforms.
    Optional source-link clearing preserves manual pose; retained mesh refresh may
    overwrite edits. No animation rebake or retarget quality evaluation.
    """
    return httpx.patch(f"{app.BASE_URL}/skeletons/retarget-sources/pose", json={
        "AssetPath": asset_path, "PoseName": pose_name, "PoseEdits": edits,
        "bClearSourceMesh": clear_source_mesh, "bConfirm": confirm,
        "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


def reset_skeleton_stored_retarget_pose(asset_path: str, pose_name: str, bones: list[str],
                                         children: bool = False, clear_source_mesh: bool = False,
                                         confirm: bool = False, dry_run: bool = False,
                                         save: bool = False) -> str:
    """Restore stored named-pose bones from current Skeleton local reference pose.

    Confirmed /Game Skeleton/stopped PIE; <=256 unique raw bones, optional descendants.
    Requires existing stored transforms; no array expansion. Optional source-link clear,
    transaction/native callback/dry-run/save. Retained mesh refresh may overwrite reset.
    """
    return httpx.patch(f"{app.BASE_URL}/skeletons/retarget-sources/pose", json={
        "AssetPath": asset_path, "PoseName": pose_name, "Bones": bones,
        "bResetReferencePose": True, "bChildren": children,
        "bClearSourceMesh": clear_source_mesh, "bConfirm": confirm,
        "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def inspect_ik_rig_definition(asset_path: str) -> str:
    """Inspect native IK Rig preview mesh/pelvis, <=256 goals/chains and <=128 solver structs.

    Requires registered full object path; explicit truncation. Loads asset without
    solving, retarget preview or authoring mutation.
    """
    return httpx.get(f"{app.BASE_URL}/ik-rigs/definition", params={"asset_path": asset_path}, timeout=180).text


@mcp.tool()
def inspect_ik_retargeter_definition(asset_path: str) -> str:
    """Inspect native IK Retargeter source/target rigs, preview meshes and current poses.

    Includes root/<=256 rotation offsets per current pose and <=128 retarget op structs.
    Explicit truncation; native getters may load referenced assets. No solve/export/mutation.
    """
    return httpx.get(f"{app.BASE_URL}/ik-retargeters/definition", params={
        "asset_path": asset_path
    }, timeout=180).text


@mcp.tool()
def create_ik_rig_retarget_chain(asset_path: str, chain_name: str, start_bone: str,
                                  end_bone: str, goal_name: str = "", confirm: bool = False,
                                  dry_run: bool = False, save: bool = False) -> str:
    """Create native IK Rig retarget chain with existing ordered bone endpoints.

    Confirmed /Game rig/stopped PIE; unused name, <256 chains, optional existing goal.
    Native controller transaction/dry-run/save; no solver/retarget preview execution.
    """
    return httpx.post(f"{app.BASE_URL}/ik-rigs/chains", json={
        "AssetPath": asset_path, "ChainName": chain_name, "StartBone": start_bone,
        "EndBone": end_bone, "GoalName": goal_name, "bConfirm": confirm,
        "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_ik_rig_retarget_root(asset_path: str, bone_name: str = "", confirm: bool = False,
                              dry_run: bool = False, save: bool = False) -> str:
    """Set/clear IK Rig pelvis/retarget root through native controller.

    Confirmed /Game rig/stopped PIE; existing native IK skeleton bone or empty/None.
    Native reinitialization/transaction, no-op/dry-run/save and before/current readback.
    """
    return httpx.patch(f"{app.BASE_URL}/ik-rigs/root", json={
        "AssetPath": asset_path, "RootBone": bone_name, "bConfirm": confirm,
        "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def change_ik_rig_retarget_chain(asset_path: str, chain_name: str, operation: str,
                                  new_name: str = "", confirm: bool = False,
                                  dry_run: bool = False, save: bool = False) -> str:
    """Rename/remove exact existing native IK Rig retarget chain.

    Confirmed /Game rig/stopped PIE; rename requires unused non-None name.
    Native controller transaction/delegates/no-op/dry-run/save. Downstream retargeters
    may react to native delegates but are not explicitly migrated or saved here.
    """
    return httpx.post(f"{app.BASE_URL}/ik-rigs/chains/lifecycle", json={
        "AssetPath": asset_path, "ChainName": chain_name, "Operation": operation,
        "NewName": new_name, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def edit_ik_rig_retarget_chain(asset_path: str, chain_name: str, start_bone: str,
                                end_bone: str, goal_name: str = "", confirm: bool = False,
                                dry_run: bool = False, save: bool = False) -> str:
    """Replace existing IK chain endpoints/goal after complete hierarchy preflight.

    Confirmed /Game rig/stopped PIE, exact chain, existing ordered bones/optional goal.
    Native complete retarget-definition setter preserves other chains/pelvis and avoids
    intermediate endpoint edits. Transaction/no-op/dry-run/readback/optional save.
    """
    return httpx.patch(f"{app.BASE_URL}/ik-rigs/chains", json={
        "AssetPath": asset_path, "ChainName": chain_name, "StartBone": start_bone,
        "EndBone": end_bone, "GoalName": goal_name, "bConfirm": confirm,
        "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def create_ik_rig_goal(asset_path: str, goal_name: str, bone_name: str,
                        confirm: bool = False, dry_run: bool = False,
                        save: bool = False) -> str:
    """Create native initialized IK goal on existing rig bone.

    Confirmed /Game rig/stopped PIE, unused goal name/<256 goals. Native controller
    transaction/readback/dry-run/save. Solver connection and chain assignment separate.
    """
    return httpx.post(f"{app.BASE_URL}/ik-rigs/goals", json={
        "AssetPath": asset_path, "GoalName": goal_name, "BoneName": bone_name,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def change_ik_rig_goal(asset_path: str, goal_name: str, operation: str,
                        new_name: str = "", confirm: bool = False,
                        dry_run: bool = False, save: bool = False) -> str:
    """Rename/remove exact existing IK goal through native controller.

    Confirmed /Game rig/stopped PIE; valid solver stack and unsanitized unused rename.
    Native solver/chain references update; reports chain impact. Transaction/dry-run/save.
    Downstream retargeters are not explicitly migrated or saved.
    """
    return httpx.post(f"{app.BASE_URL}/ik-rigs/goals/lifecycle", json={
        "AssetPath": asset_path, "GoalName": goal_name, "Operation": operation,
        "NewName": new_name, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_ik_rig_goal_bone(asset_path: str, goal_name: str, bone_name: str,
                         confirm: bool = False, dry_run: bool = False,
                         save: bool = False) -> str:
    """Reassign IK goal to existing native bone with initial-transform/solver callbacks.

    Confirmed /Game rig/stopped PIE, exact goal and valid solver stack. Reports chain
    reference count; chain endpoints/current goal transform not explicitly edited.
    Native controller transaction/no-op/dry-run/readback/optional save.
    """
    return httpx.patch(f"{app.BASE_URL}/ik-rigs/goals/bone", json={
        "AssetPath": asset_path, "GoalName": goal_name, "BoneName": bone_name,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_ik_rig_goal_weights(asset_path: str, goal_name: str, position_alpha: float = 1,
                            rotation_alpha: float = 1, confirm: bool = False,
                            dry_run: bool = False, save: bool = False) -> str:
    """Set native IK goal position/rotation alpha [0,1] on exact owned goal.

    Confirmed /Game rig/stopped PIE; owner/goal transaction and property notifications,
    no-op/dry-run/save and finite-safe before/current readback. No solve execution.
    """
    return httpx.patch(f"{app.BASE_URL}/ik-rigs/goals/weights", json={
        "AssetPath": asset_path, "GoalName": goal_name, "PositionAlpha": position_alpha,
        "RotationAlpha": rotation_alpha, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def list_ik_rig_solver_types(search: str = "", limit: int = 64) -> str:
    """Discover loaded native IK solver structs and <=64 editable default fields each.

    limit 1..128; bounded values/truncation/clamp metadata. Discovery does not prove
    native controller addability. Does not load assets, solve or mutate rig stacks.
    """
    return httpx.get(f"{app.BASE_URL}/ik-rigs/solver-types", params={
        "search": search, "limit": limit
    }, timeout=180).text


@mcp.tool()
def add_ik_rig_solver(asset_path: str, solver_type: str, confirm: bool = False,
                       dry_run: bool = False, save: bool = False) -> str:
    """Append loaded native derived solver struct to IK Rig stack (<128 entries).

    Confirmed /Game rig/stopped PIE; controller initialization/transaction/readback/save.
    Dry-run validates expected append index only. Bone/goal configuration and solving
    remain separate; stack indices can change after subsequent edits.
    """
    return httpx.post(f"{app.BASE_URL}/ik-rigs/solvers", json={
        "AssetPath": asset_path, "SolverType": solver_type, "bConfirm": confirm,
        "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def remove_ik_rig_solver(asset_path: str, solver_index: int, expected_type: str,
                          confirm: bool = False, dry_run: bool = False,
                          save: bool = False) -> str:
    """Remove native solver at current index guarded by expected struct type.

    Confirmed /Game rig/stopped PIE, <=128 stack entries. Native controller transaction/
    reinitialization/readback/dry-run/save. Goals/chains retained; re-inspect shifted indices.
    Type guard cannot distinguish multiple instances of the same solver type.
    """
    return httpx.request("DELETE", f"{app.BASE_URL}/ik-rigs/solvers", json={
        "AssetPath": asset_path, "SolverIndex": solver_index, "SolverType": expected_type,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def move_ik_rig_solver(asset_path: str, solver_index: int, target_index: int,
                        expected_type: str, confirm: bool = False,
                        dry_run: bool = False, save: bool = False) -> str:
    """Move current IK solver to final index within stack, expected native type guarded.

    Confirmed /Game rig/stopped PIE, <=128 entries. target_index 0..count-1 (not one-past).
    Native controller reinitialization/transaction/no-op/dry-run/readback/save. Reinspect
    shifted indices; type guard cannot distinguish multiple instances of same type.
    """
    return httpx.patch(f"{app.BASE_URL}/ik-rigs/solvers/order", json={
        "AssetPath": asset_path, "SolverIndex": solver_index, "TargetIndex": target_index,
        "SolverType": expected_type, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_ik_rig_solver_enabled(asset_path: str, solver_index: int, expected_type: str,
                               enabled: bool = True, confirm: bool = False,
                               dry_run: bool = False, save: bool = False) -> str:
    """Enable/disable native IK solver guarded by current index/expected struct type.

    Confirmed /Game rig/stopped PIE, <=128 stack; controller reinitialization/transaction,
    no-op/dry-run/readback/save. Definition inspector includes enabled state. No solve.
    """
    return httpx.patch(f"{app.BASE_URL}/ik-rigs/solvers/enabled", json={
        "AssetPath": asset_path, "SolverIndex": solver_index, "SolverType": expected_type,
        "bEnabled": enabled, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def connect_ik_rig_goal(asset_path: str, solver_index: int, expected_type: str,
                         goal_name: str, connected: bool = True, confirm: bool = False,
                         dry_run: bool = False, save: bool = False) -> str:
    """Connect/disconnect existing IK goal to current type-guarded solver.

    Confirmed /Game rig/stopped PIE; native controller callbacks/transaction/readback/save.
    No-op supported. Dry-run checks identity/current state, not solver-specific acceptance.
    Solver-specific goal settings initialize natively; no solve execution.
    """
    return httpx.post(f"{app.BASE_URL}/ik-rigs/solvers/goals", json={
        "AssetPath": asset_path, "SolverIndex": solver_index, "SolverType": expected_type,
        "GoalName": goal_name, "Operation": "connect" if connected else "disconnect",
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_ik_rig_solver_bone(asset_path: str, solver_index: int, expected_type: str,
                           role: str, bone_name: str, confirm: bool = False,
                           dry_run: bool = False, save: bool = False) -> str:
    """Assign existing rig bone to solver start/end role through native controller.

    Requires confirmed /Game rig, stopped PIE, matching current index/type and supported
    role ('start' or 'end'). Transaction, no-op/readback and optional saving supported.
    Dry-run does not establish solver topology or solve correctness; clearing is unsupported.
    """
    return httpx.patch(f"{app.BASE_URL}/ik-rigs/solvers/bone", json={
        "AssetPath": asset_path, "SolverIndex": solver_index, "SolverType": expected_type,
        "Operation": role, "BoneName": bone_name, "bConfirm": confirm,
        "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_ik_rig_preview_mesh(asset_path: str, mesh_path: str, confirm: bool = False,
                            dry_run: bool = False, save: bool = False) -> str:
    """Assign compatible persistent skeletal mesh to confirmed /Game IK Rig.

    Native controller checks compatibility and refreshes stored skeleton on a changed
    mesh. Requires stopped PIE; supports transaction, readback, no-op and optional save.
    Dry-run loads assets/checks compatibility without assignment. No solve or bake.
    Same-mesh assignment does not refresh skeleton; clearing is unsupported.
    """
    return httpx.patch(f"{app.BASE_URL}/ik-rigs/preview-mesh", json={
        "AssetPath": asset_path, "MeshPath": mesh_path, "bConfirm": confirm,
        "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_ik_rig_bone_excluded(asset_path: str, bone_name: str, excluded: bool = True,
                              confirm: bool = False, dry_run: bool = False,
                              save: bool = False) -> str:
    """Exclude/include one existing bone in a confirmed /Game IK Rig, with stopped PIE.

    Uses native controller reinitialization, transaction, no-op/readback and optional save.
    Does not propagate to descendants, remove bones or verify solver-specific behavior.
    Inspect IK Rig definition for the bounded excluded-bone list.
    """
    return httpx.patch(f"{app.BASE_URL}/ik-rigs/bones/excluded", json={
        "AssetPath": asset_path, "BoneName": bone_name, "bExcluded": excluded,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_ik_retargeter_rig(asset_path: str, side: str, rig_path: str,
                         confirm: bool = False, dry_run: bool = False,
                         save: bool = False) -> str:
    """Assign source/target IK Rig to confirmed /Game retargeter while PIE is stopped.

    Native assignment replaces side preview mesh; source changes rebuild operation
    chain mappings. Native target operation overrides remain. Transaction/readback,
    no-op and optional save; dry-run does not execute mapping callbacks. Referenced
    assets may load. No rig clearing, solve, bake or external asset migration.
    """
    return httpx.patch(f"{app.BASE_URL}/ik-retargeters/rig", json={
        "AssetPath": asset_path, "Side": side, "RigPath": rig_path,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_ik_retargeter_preview_mesh(asset_path: str, side: str, mesh_path: str,
                                  confirm: bool = False, dry_run: bool = False,
                                  save: bool = False) -> str:
    """Set compatible source/target preview mesh override on confirmed /Game retargeter.

    Requires stopped PIE and assigned side rig; checks native rig compatibility.
    Native retarget controller refreshes preview, without changing rig skeleton/mesh.
    Supports transaction/readback, dry-run, effective-mesh no-op and optional save.
    Clearing is unsupported. Does not verify solve/bake or per-operation rig overrides.
    """
    return httpx.patch(f"{app.BASE_URL}/ik-retargeters/preview-mesh", json={
        "AssetPath": asset_path, "Side": side, "MeshPath": mesh_path,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_ik_retargeter_current_pose(asset_path: str, side: str, pose_name: str,
                                   confirm: bool = False, dry_run: bool = False,
                                   save: bool = False) -> str:
    """Select existing source/target retarget pose on confirmed /Game retargeter.

    Requires stopped PIE; native controller reinitialization, transaction/readback,
    no-op, dry-run and optional save. Definition inspection lists available pose names.
    Does not edit pose offsets, solve or export animations.
    """
    return httpx.patch(f"{app.BASE_URL}/ik-retargeters/poses/current", json={
        "AssetPath": asset_path, "Side": side, "PoseName": pose_name,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def create_ik_retargeter_pose(asset_path: str, side: str, new_name: str,
                              source_pose: str = "", confirm: bool = False,
                              dry_run: bool = False, save: bool = False) -> str:
    """Create empty retarget pose or duplicate existing side pose, then select it.

    Requires unused non-None name, fewer than 256 side poses, confirmed /Game retargeter
    and stopped PIE. Native controller transaction/readback, dry-run and optional save.
    Empty source_pose creates zero offsets; supplied source copies stored offsets.
    No auto-alignment, solve or animation export.
    """
    return httpx.post(f"{app.BASE_URL}/ik-retargeters/poses", json={
        "AssetPath": asset_path, "Side": side, "NewName": new_name,
        "PoseName": source_pose, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def change_ik_retargeter_pose(asset_path: str, side: str, pose_name: str,
                               operation: str, new_name: str = "",
                               confirm: bool = False, dry_run: bool = False,
                               save: bool = False) -> str:
    """Rename/remove existing non-default source/target retarget pose.

    Confirmed /Game retargeter, stopped PIE; operation is rename or remove. Rename
    requires unused destination (same name is a no-op); removing current selects default.
    Native transactions/readback, dry-run and optional save. External pose-name
    consumers are not discovered/migrated. No solve or animation export.
    """
    return httpx.post(f"{app.BASE_URL}/ik-retargeters/poses/lifecycle", json={
        "AssetPath": asset_path, "Side": side, "PoseName": pose_name,
        "Operation": operation, "NewName": new_name,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def reset_ik_retargeter_pose(asset_path: str, side: str, pose_name: str,
                             bones: list[str], confirm: bool = False,
                             dry_run: bool = False, save: bool = False) -> str:
    """Reset whole retarget pose (empty bones) or up to 256 unique side-rig bones.

    Removes selected stored rotation offsets; selecting pelvis resets root translation.
    Empty list clears all rotations/root translation. Current selection remains unchanged.
    Confirmed /Game asset/stopped PIE, native transaction/readback, dry-run/no-op/save.
    No descendant expansion, auto-alignment, solve or export.
    """
    return httpx.post(f"{app.BASE_URL}/ik-retargeters/poses/reset", json={
        "AssetPath": asset_path, "Side": side, "PoseName": pose_name, "Bones": bones,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_ik_retargeter_root_offset(asset_path: str, side: str, pose_name: str,
                                  translation: dict, confirm: bool = False,
                                  dry_run: bool = False, save: bool = False) -> str:
    """Set absolute current retarget pose root translation (X/Y/Z, native units).

    Expected pose_name must exist and be current on source/target side. Finite components
    bounded to one million; confirmed /Game retargeter/stopped PIE. Converts absolute
    value to native additive delta, transaction/readback, dry-run/no-op and optional save.
    No pose selection change, auto-alignment, solve or export.
    """
    return httpx.patch(f"{app.BASE_URL}/ik-retargeters/poses/root-offset", json={
        "AssetPath": asset_path, "Side": side, "PoseName": pose_name,
        "Translation": translation, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_ik_retargeter_bone_rotation(asset_path: str, side: str, pose_name: str,
                                    bone_name: str, rotation: dict,
                                    confirm: bool = False, dry_run: bool = False,
                                    save: bool = False) -> str:
    """Set absolute current pose bone rotation offset from Pitch/Yaw/Roll degrees.

    Expected pose must be current; bone must exist in assigned side rig. Native setter
    stores normalized quaternion and sorts offsets hierarchically. Confirmed /Game
    asset/stopped PIE, transaction/readback, dry-run/no-op and optional save.
    No descendant expansion, selection change, auto-alignment, solve or export.
    """
    return httpx.patch(f"{app.BASE_URL}/ik-retargeters/poses/bone-rotation", json={
        "AssetPath": asset_path, "Side": side, "PoseName": pose_name,
        "BoneName": bone_name, "Rotation": rotation,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def list_ik_retargeter_operation_types(search: str = "", limit: int = 64) -> str:
    """Discover loaded native derived retarget operation structs and editable defaults.

    Search up to 128 characters, limit 1..128; sorted struct paths, up to 64 fields/type
    and 2048 exported characters/value, counts/truncation and clamp metadata.
    Native controller decides addability; discovery does not prove a valid operation stack.
    """
    return httpx.get(f"{app.BASE_URL}/ik-retargeters/operation-types", params={
        "search": search, "limit": limit
    }, timeout=180).text


@mcp.tool()
def add_ik_retargeter_operation(asset_path: str, operation_type: str,
                                 confirm: bool = False, dry_run: bool = False,
                                 save: bool = False) -> str:
    """Add loaded native top-level retarget operation to confirmed /Game retargeter.

    Requires stopped PIE, fewer than 128 valid operations; rejects duplicate singleton.
    Native unique naming, setup callbacks and stack cleanup may reorder indices.
    Transaction/type/count readback and optional save. Dry-run checks preflight only,
    without native setup callbacks. Reinspect stack before further operations.
    """
    return httpx.post(f"{app.BASE_URL}/ik-retargeters/operations", json={
        "AssetPath": asset_path, "SolverType": operation_type,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_ik_retargeter_operation_enabled(asset_path: str, operation_index: int,
                                        expected_type: str, expected_name: str,
                                        enabled: bool, confirm: bool = False,
                                        dry_run: bool = False, save: bool = False) -> str:
    """Enable/disable current index/type/name guarded native retarget operation.

    Definition inspection supplies names/types/enabled state. Confirmed /Game asset,
    stopped PIE, bounded stack, native reinitialization/transaction/readback, dry-run,
    no-op and optional save. Does not change child operation flags or verify solving.
    """
    return httpx.patch(f"{app.BASE_URL}/ik-retargeters/operations/enabled", json={
        "AssetPath": asset_path, "SolverIndex": operation_index, "SolverType": expected_type,
        "ExpectedName": expected_name, "bEnabled": enabled,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def remove_ik_retargeter_operation(asset_path: str, operation_index: int,
                                    expected_type: str, expected_name: str,
                                    cascade: bool = False, confirm: bool = False,
                                    dry_run: bool = False, save: bool = False) -> str:
    """Remove native index/type/name guarded retarget operation and optional children.

    Child-bearing operations require cascade=True. Confirmed /Game retargeter/stopped
    PIE, bounded valid stack, native transaction/count/identity readback, dry-run and
    optional save. Response lists affected names, including during dry-run. Reinspect
    indices after removal; external operation-name consumers are not migrated.
    """
    return httpx.request("DELETE", f"{app.BASE_URL}/ik-retargeters/operations", json={
        "AssetPath": asset_path, "SolverIndex": operation_index, "SolverType": expected_type,
        "ExpectedName": expected_name, "bCascade": cascade,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def rename_ik_retargeter_operation(asset_path: str, operation_index: int,
                                    expected_type: str, expected_name: str,
                                    new_name: str, confirm: bool = False,
                                    dry_run: bool = False, save: bool = False) -> str:
    """Rename current index/type/name guarded native retarget operation.

    Requires unused non-None destination or same-name no-op. Native rename migrates
    local child parent-name references; external consumers are not discovered/migrated.
    Confirmed /Game asset/stopped PIE, transaction/readback, dry-run and optional save.
    """
    return httpx.patch(f"{app.BASE_URL}/ik-retargeters/operations/name", json={
        "AssetPath": asset_path, "SolverIndex": operation_index, "SolverType": expected_type,
        "ExpectedName": expected_name, "NewName": new_name,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_ik_retargeter_operation_parent(asset_path: str, operation_index: int,
                                       expected_type: str, expected_name: str,
                                       parent_name: str, confirm: bool = False,
                                       dry_run: bool = False, save: bool = False) -> str:
    """Assign compatible native parent to current index/type/name guarded operation.

    Validates unique names, native parent type, no self-parent/cycles/dangling ancestry.
    Confirmed /Game asset/stopped PIE, native cleanup/transaction/readback, dry-run/no-op,
    optional save. Cleanup may reorder indices; response supplies current child index.
    Clearing parent unsupported; no solve verification.
    """
    return httpx.patch(f"{app.BASE_URL}/ik-retargeters/operations/parent", json={
        "AssetPath": asset_path, "SolverIndex": operation_index, "SolverType": expected_type,
        "ExpectedName": expected_name, "ParentName": parent_name,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def move_ik_retargeter_operation(asset_path: str, operation_index: int,
                                  expected_type: str, expected_name: str,
                                  target_index: int, confirm: bool = False,
                                  dry_run: bool = False, save: bool = False) -> str:
    """Request native operation move, followed by native ordering-constraint cleanup.

    Index/type/name guards and unique bounded valid stack. Native cleanup can change
    requested destination or leave order unchanged; response reports actual index/order.
    Confirmed /Game asset/stopped PIE, transaction/identity readback and optional save.
    Dry-run does not simulate cleanup. Reinspect indices before further operations.
    """
    return httpx.patch(f"{app.BASE_URL}/ik-retargeters/operations/order", json={
        "AssetPath": asset_path, "SolverIndex": operation_index, "SolverType": expected_type,
        "ExpectedName": expected_name, "TargetIndex": target_index,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def inspect_ik_retargeter_operation(asset_path: str, operation_index: int,
                                     expected_type: str, expected_name: str) -> str:
    """Inspect authored editable fields of current index/type/name guarded operation.

    Read-only persistent retargeter inspection, up to 128 fields/8192 characters per
    native export-text value with truncation. Includes nested settings where reflected.
    Exporter intermediate allocation is uncapped; no mutation or solve performed.
    """
    return httpx.post(f"{app.BASE_URL}/ik-retargeters/operations/inspect", json={
        "AssetPath": asset_path, "SolverIndex": operation_index,
        "SolverType": expected_type, "ExpectedName": expected_name
    }, timeout=180).text


@mcp.tool()
def inspect_ik_rig_solver(asset_path: str, solver_index: int, expected_type: str) -> str:
    """Read authored editable fields of current index/type guarded native IK solver.

    Persistent registered IK Rig, bounded stack; up to 128 fields and 8192 native
    export-text characters/value with truncation. Includes nested settings where reflected.
    Same-type solver instances are not uniquely identified by type guard. Native exporter
    intermediate allocation is uncapped. No mutation, solve or property import.
    """
    return httpx.post(f"{app.BASE_URL}/ik-rigs/solvers/inspect", json={
        "AssetPath": asset_path, "SolverIndex": solver_index, "SolverType": expected_type
    }, timeout=180).text


@mcp.tool()
def inspect_ik_retargeter_chain_mapping(asset_path: str, operation_index: int,
                                         expected_type: str, expected_name: str) -> str:
    """Read native operation target/source chain pairs without refreshing or auto-mapping.

    Current index/type/name guarded persistent retargeter. Up to 256 pairs with total
    count/truncation, cached readiness and chain presence. Operations without mappings
    return mapping_available=False. Does not establish retarget quality or run solving.
    """
    return httpx.post(f"{app.BASE_URL}/ik-retargeters/operations/mapping/inspect", json={
        "AssetPath": asset_path, "SolverIndex": operation_index,
        "SolverType": expected_type, "ExpectedName": expected_name
    }, timeout=180).text


@mcp.tool()
def set_ik_retargeter_chain_mapping(asset_path: str, operation_index: int,
                                     expected_type: str, expected_name: str,
                                     target_chain: str, source_chain: str = "",
                                     confirm: bool = False, dry_run: bool = False,
                                     save: bool = False) -> str:
    """Assign/clear one target chain's source within one guarded retarget operation.

    Existing chains in ready cached mapping required; empty/None source clears mapping.
    Confirmed /Game retargeter/stopped PIE, unique operation name/index/type guards,
    native reinitialization/transaction/readback, dry-run/no-op and optional save.
    No auto-mapping or solve verification.
    """
    return httpx.patch(f"{app.BASE_URL}/ik-retargeters/operations/mapping", json={
        "AssetPath": asset_path, "SolverIndex": operation_index, "SolverType": expected_type,
        "ExpectedName": expected_name, "ChainName": target_chain, "SourceChain": source_chain,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def auto_map_ik_retargeter_chains(asset_path: str, operation_index: int,
                                  expected_type: str, expected_name: str,
                                  mode: str = "exact", force_remap: bool = False,
                                  confirm: bool = False, dry_run: bool = False,
                                  save: bool = False) -> str:
    """Auto-map one guarded operation using exact/fuzzy/clear native algorithm.

    Scratch mapping preview returns planned pairs and changed count, including dry-run.
    Confirmed /Game asset/stopped PIE, ready bounded mapping, unique name/index/type,
    native controller transaction/readback, no-op and optional save. force_remap controls
    native overwrite behavior. Fuzzy name similarity does not establish retarget quality.
    """
    return httpx.post(f"{app.BASE_URL}/ik-retargeters/operations/mapping/auto", json={
        "AssetPath": asset_path, "SolverIndex": operation_index, "SolverType": expected_type,
        "ExpectedName": expected_name, "Operation": mode, "bForceRemap": force_remap,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def refresh_ik_retargeter_chain_mapping(asset_path: str, operation_index: int,
                                         expected_type: str, expected_name: str,
                                         confirm: bool = False, dry_run: bool = False,
                                         save: bool = False) -> str:
    """Reconcile native operation chain mapping and regenerate settings after rig edits.

    Requires source rig and operation custom target rig, bounded chains and unique
    index/type/name identity. Confirmed /Game asset/stopped PIE, transaction/optional save.
    Dry-run reconciles scratch mapping without native settings callbacks; reports counts.
    Does not auto-map, solve or export. Inspect mappings/settings after refresh.
    """
    return httpx.post(f"{app.BASE_URL}/ik-retargeters/operations/mapping/refresh", json={
        "AssetPath": asset_path, "SolverIndex": operation_index, "SolverType": expected_type,
        "ExpectedName": expected_name, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def auto_align_ik_retargeter_pose(asset_path: str, side: str, pose_name: str,
                                  bones: list[str], method: str = "chain",
                                  confirm: bool = False, dry_run: bool = False,
                                  save: bool = False) -> str:
    """Invoke native current-pose auto-alignment: chain/mesh/local_axes/global_axes.

    Empty bones aligns all and RESETS ENTIRE POSE FIRST. Selected bones do not reset
    entire pose. Expected current pose, both rigs/preview meshes, confirmed /Game asset,
    stopped PIE and bounded bones required. Transaction/optional save. Native void API
    may skip bones; invocation does not establish quality. Dry-run preflight only.
    """
    return httpx.post(f"{app.BASE_URL}/ik-retargeters/poses/auto-align", json={
        "AssetPath": asset_path, "Side": side, "PoseName": pose_name, "Bones": bones,
        "Operation": method, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def snap_ik_retargeter_pose_to_ground(asset_path: str, side: str, pose_name: str,
                                       reference_bone: str = "", confirm: bool = False,
                                       dry_run: bool = False, save: bool = False) -> str:
    """Invoke native current-pose root-height correction using reference-pose height.

    Empty/None reference bone selects lowest mapped bone; explicit bone must exist in
    preview mesh. Requires both rigs/meshes, current expected pose, confirmed /Game asset
    and stopped PIE. Transaction, finite root readback, optional save; dry-run preflight
    only. Native void API can skip if processor not ready; invocation is not success proof.
    """
    return httpx.post(f"{app.BASE_URL}/ik-retargeters/poses/snap-ground", json={
        "AssetPath": asset_path, "Side": side, "PoseName": pose_name,
        "BoneName": reference_bone, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def inspect_ik_retargeter_pose(asset_path: str, side: str, pose_name: str,
                               bones: list[str]) -> str:
    """Inspect named stored retarget pose without selecting it.

    Empty bones lists stored offsets sorted/capped at 256; selected up to 256 unique
    names report explicit offset or implicit identity and side-rig bone presence.
    Includes root translation/version/current flag; nonfinite components report null.
    No pose evaluation, solve or export. Referenced rig may load.
    """
    return httpx.post(f"{app.BASE_URL}/ik-retargeters/poses/inspect", json={
        "AssetPath": asset_path, "Side": side, "PoseName": pose_name, "Bones": bones
    }, timeout=180).text


@mcp.tool()
def set_ik_rig_goal_transform(asset_path: str, goal_name: str, translation: dict,
                               rotation: dict, scale: dict, confirm: bool = False,
                               dry_run: bool = False, save: bool = False) -> str:
    """Set absolute native goal CurrentTransform in rig global/component space.

    Translation/scale use X/Y/Z, rotation Pitch/Yaw/Roll degrees; bounded finite values,
    nonzero scale. Unique owned goal, confirmed /Game rig/stopped PIE; native setter,
    owner/goal transaction, readback, dry-run/no-op and optional save. Initial transform
    unchanged; no solve or runtime component propagation verified.
    """
    return httpx.patch(f"{app.BASE_URL}/ik-rigs/goals/transform", json={
        "AssetPath": asset_path, "GoalName": goal_name, "Translation": translation,
        "Rotation": rotation, "Scale": scale,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def inspect_ik_rig_goal_transform(asset_path: str, goal_name: str) -> str:
    """Read stored native goal initial/current transforms in rig global/component space.

    Persistent registered rig and unique owned goal required. Reports translation/scale,
    XYZW quaternion, finite/normalized status; nonfinite components report null.
    Read-only; does not inspect runtime components or execute a solve.
    """
    return httpx.post(f"{app.BASE_URL}/ik-rigs/goals/transform/inspect", json={
        "AssetPath": asset_path, "GoalName": goal_name
    }, timeout=180).text


@mcp.tool()
def reset_ik_rig_goal_transforms(asset_path: str, confirm: bool = False,
                                  dry_run: bool = False, save: bool = False) -> str:
    """Reset ALL native goal initial/current transforms to bone reference transforms.

    Confirmed /Game rig/stopped PIE; up to 256 valid owned uniquely named goals with
    existing bones and finite reference transforms. Native controller, owner/goal
    transaction/readback, dry-run change count/no-op and optional save. Replaces initial
    AND current transforms; no goal deletion or solve/runtime propagation verified.
    """
    return httpx.post(f"{app.BASE_URL}/ik-rigs/goals/transform/reset", json={
        "AssetPath": asset_path, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def inspect_ik_rig_solver_connections(asset_path: str, solver_index: int,
                                       expected_type: str) -> str:
    """Read native solver enabled state, start/end bone roles and rig goal connections.

    Persistent registered rig, bounded index/type guarded stack and <=256 goals.
    Reports role capability/bone presence and native per-goal connection state.
    Includes solver-reported settings goal names with orphan/ambiguous matches, count
    and truncation (256). Coverage depends on native solver enumeration completeness.
    Same-type instances are not uniquely identified. No mutation or solve.
    """
    return httpx.post(f"{app.BASE_URL}/ik-rigs/solvers/connections", json={
        "AssetPath": asset_path, "SolverIndex": solver_index, "SolverType": expected_type
    }, timeout=180).text


@mcp.tool()
def inspect_ik_rig_skeleton(asset_path: str, bones: list[str]) -> str:
    """Read stored IK Rig bone hierarchy, exclusion and global reference transforms.

    Empty bones returns first 256 with truncation; explicit up to 256 unique existing
    names selects bones. Reports parent/array consistency and finite-safe transforms.
    Persistent registered rig required; no runtime pose evaluation, solve or mutation.
    """
    return httpx.post(f"{app.BASE_URL}/ik-rigs/skeleton/inspect", json={
        "AssetPath": asset_path, "Bones": bones
    }, timeout=180).text


@mcp.tool()
def check_ik_rig_mesh_compatibility(asset_path: str, mesh_path: str) -> str:
    """Read native IK Rig processor skeleton compatibility for candidate skeletal mesh.

    Persistent registered assets; candidate mesh has 1..4096 bones. Returns compatible
    false for native incompatibility without assigning mesh. Loads assets; no solve.
    Compatibility does not establish goal placement, convergence or retarget quality.
    """
    return httpx.post(f"{app.BASE_URL}/ik-rigs/mesh-compatibility", json={
        "AssetPath": asset_path, "MeshPath": mesh_path
    }, timeout=180).text


@mcp.tool()
def refresh_ik_rig_initial_goal_transforms(asset_path: str, confirm: bool = False,
                                           dry_run: bool = False, save: bool = False) -> str:
    """Refresh ALL goal initial transforms from reference bones, preserving relative deltas.

    Uses native ResetInitialGoalTransforms transform composition. Requires valid owned
    unique goals/bones, finite initial/current/reference transforms and invertible initial
    scale. Confirmed /Game rig/stopped PIE, owner/goal transactions, prepared readback,
    dry-run change counts/no-op and optional save. No solve/runtime propagation verified.
    """
    return httpx.post(f"{app.BASE_URL}/ik-rigs/goals/transform/refresh-initial", json={
        "AssetPath": asset_path, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def add_ik_retargeter_default_operations(asset_path: str, confirm: bool = False,
                                          dry_run: bool = False, save: bool = False) -> str:
    """Initialize EMPTY retarget stack with UE 5.7 native six-operation defaults.

    Pelvis, FK chains, run IK/child IK chains, root motion and curve remap. Requires
    confirmed persistent /Game retargeter/stopped PIE. Native setup callbacks, transaction,
    count/name validity readback and optional save. Dry-run preflight only; no rig
    assignment, auto-map, solve or export. Reinspect stack before further authoring.
    """
    return httpx.post(f"{app.BASE_URL}/ik-retargeters/operations/defaults", json={
        "AssetPath": asset_path, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def run_ik_retargeter_operation_setup(asset_path: str, operation_index: int,
                                       expected_type: str, expected_name: str,
                                       confirm: bool = False, dry_run: bool = False,
                                       save: bool = False) -> str:
    """Re-run native operation OnAddedToStack setup; may replace mappings/settings.

    Current index/type/name, valid unique bounded stack and compatible existing parent
    guards. Confirmed /Game retargeter/stopped PIE, native transaction/identity readback
    and optional save. Dry-run identity/parent preflight only; native void callback
    invocation is not proof of readiness/quality. Inspect settings afterward.
    """
    return httpx.post(f"{app.BASE_URL}/ik-retargeters/operations/setup", json={
        "AssetPath": asset_path, "SolverIndex": operation_index, "SolverType": expected_type,
        "ExpectedName": expected_name, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def assign_ik_rig_to_retargeter_operations(asset_path: str, side: str, rig_path: str,
                                           confirm: bool = False, dry_run: bool = False,
                                           save: bool = False) -> str:
    """Invoke native rig-assignment callbacks on ALL retarget operations.

    May replace operation-specific rigs/settings/mappings; asset-level rig and preview
    are separate. Confirmed /Game asset/stopped PIE, registered persistent rig, bounded
    valid unique operation stack/acyclic parent hierarchy, transaction/readback and save.
    Dry-run preflight only; invocation does not prove every operation accepted rig.
    """
    return httpx.post(f"{app.BASE_URL}/ik-retargeters/operations/assign-rig", json={
        "AssetPath": asset_path, "Side": side, "RigPath": rig_path,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def inspect_ik_retargeter_operation_hierarchy(asset_path: str) -> str:
    """Diagnose native retarget operation name/parent graph without modification.

    Persistent registered asset, up to 128 operations. Reports invalid structs, missing/
    duplicate names, missing/ambiguous/incompatible parents and cycles. Structural
    consistency does not establish native ordering, settings validity or solve readiness.
    """
    return httpx.get(f"{app.BASE_URL}/ik-retargeters/operations/hierarchy", params={
        "asset_path": asset_path
    }, timeout=180).text


@mcp.tool()
def change_ik_rig_solver_bone_settings(asset_path: str, solver_index: int,
                                        expected_type: str, bone_name: str,
                                        operation: str, confirm: bool = False,
                                        dry_run: bool = False, save: bool = False) -> str:
    """Add/remove native solver-specific bone setting entry; operation add or remove.

    Current index/type guard, existing bone, custom-setting capability/native acceptance,
    confirmed /Game rig/stopped PIE. Native initialization/reinitialization, transaction,
    readback, dry-run/no-op and optional save. Individual settings/solve remain separate.
    """
    return httpx.post(f"{app.BASE_URL}/ik-rigs/solvers/bone-settings", json={
        "AssetPath": asset_path, "SolverIndex": solver_index, "SolverType": expected_type,
        "BoneName": bone_name, "Operation": operation,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def inspect_ik_rig_solver_bone_settings(asset_path: str, solver_index: int,
                                         expected_type: str, bone_name: str) -> str:
    """Read native per-bone solver settings type and authored editable field values.

    Current index/type guard, existing bone/custom settings support; missing entry reports
    has_settings=False. Up to 64 fields/4096 export-text characters per value, truncation
    included; exporter intermediate allocation uncapped. No creation, mutation or solve.
    """
    return httpx.post(f"{app.BASE_URL}/ik-rigs/solvers/bone-settings/inspect", json={
        "AssetPath": asset_path, "SolverIndex": solver_index,
        "SolverType": expected_type, "BoneName": bone_name
    }, timeout=180).text


@mcp.tool()
def inspect_ik_rig_solver_goal_settings(asset_path: str, solver_index: int,
                                         expected_type: str, goal_name: str) -> str:
    """Read native solver-specific goal settings type and authored editable values.

    Current index/type guard, existing rig goal/custom settings support; absent entry
    reports has_settings=False. Up to 64 fields/4096 export-text characters per value
    with truncation; native exporter intermediate allocation uncapped. No mutation/solve.
    """
    return httpx.post(f"{app.BASE_URL}/ik-rigs/solvers/goal-settings/inspect", json={
        "AssetPath": asset_path, "SolverIndex": solver_index,
        "SolverType": expected_type, "GoalName": goal_name
    }, timeout=180).text


@mcp.tool()
def inspect_ik_rig_solver_settings(asset_path: str, solver_index: int,
                                    expected_type: str) -> str:
    """Read dedicated native solver settings type and authored editable fields.

    Current index/type guarded persistent registered rig. Requires native settings type
    deriving from solver settings base; up to 64 fields/4096 export-text characters/value,
    with truncation. Native exporter intermediate allocation uncapped. No mutation/solve.
    """
    return httpx.post(f"{app.BASE_URL}/ik-rigs/solvers/settings/inspect", json={
        "AssetPath": asset_path, "SolverIndex": solver_index, "SolverType": expected_type
    }, timeout=180).text


@mcp.tool()
def inspect_ik_retargeter_operation_settings(asset_path: str, operation_index: int,
                                              expected_type: str, expected_name: str) -> str:
    """Read dedicated native operation settings type and authored editable fields.

    Persistent registered retargeter, current index/type/name guarded bounded stack;
    settings type must derive from native base. Up to 64 fields/4096 export-text
    characters/value with truncation; native exporter intermediate allocation uncapped.
    No settings creation, mutation or solve.
    """
    return httpx.post(f"{app.BASE_URL}/ik-retargeters/operations/settings/inspect", json={
        "AssetPath": asset_path, "SolverIndex": operation_index,
        "SolverType": expected_type, "ExpectedName": expected_name
    }, timeout=180).text


@mcp.tool()
def reset_ik_retargeter_operation_settings(asset_path: str, operation_index: int,
                                            expected_type: str, expected_name: str,
                                            confirm: bool = False, dry_run: bool = False,
                                            save: bool = False) -> str:
    """Reset ENTIRE dedicated operation settings struct to native constructed defaults.

    May clear configured references/chain settings; native SetSettings callbacks may
    adjust defaults. Does not rerun initial setup. Confirmed /Game asset/stopped PIE,
    current index/type/name guard, transaction, dry-run/no-op and optional save.
    Inspect settings afterward; no solve/export verification.
    """
    return httpx.post(f"{app.BASE_URL}/ik-retargeters/operations/settings/reset", json={
        "AssetPath": asset_path, "SolverIndex": operation_index, "SolverType": expected_type,
        "ExpectedName": expected_name, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def reset_ik_rig_solver_settings(asset_path: str, solver_index: int,
                                  expected_type: str, confirm: bool = False,
                                  dry_run: bool = False, save: bool = False) -> str:
    """Reset dedicated native solver editable settings from constructed defaults.

    May replace configured solver settings; bone/goal entries remain separate. Current
    index/type guarded confirmed /Game rig/stopped PIE, native setter/transaction,
    dry-run/no-op and optional save. Inspect settings afterward; refresh/solve unverified.
    """
    return httpx.post(f"{app.BASE_URL}/ik-rigs/solvers/settings/reset", json={
        "AssetPath": asset_path, "SolverIndex": solver_index, "SolverType": expected_type,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def reset_ik_rig_solver_bone_settings(asset_path: str, solver_index: int,
                                       expected_type: str, bone_name: str,
                                       confirm: bool = False, dry_run: bool = False,
                                       save: bool = False) -> str:
    """Reset existing native bone settings values from defaults, preserving entry identity.

    Native setter copy policy excludes BlueprintReadOnly/transient properties. Current
    index/type, existing bone/settings and capability guards, confirmed /Game rig/stopped
    PIE, transaction/identity readback, dry-run/no-op and optional save. No solve verified.
    """
    return httpx.post(f"{app.BASE_URL}/ik-rigs/solvers/bone-settings/reset", json={
        "AssetPath": asset_path, "SolverIndex": solver_index, "SolverType": expected_type,
        "BoneName": bone_name, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def reset_ik_rig_solver_goal_settings(asset_path: str, solver_index: int,
                                       expected_type: str, goal_name: str,
                                       confirm: bool = False, dry_run: bool = False,
                                       save: bool = False) -> str:
    """Reset existing native solver goal settings from defaults, preserving goal identity.

    Native setter copy policy excludes BlueprintReadOnly/transient properties. Current
    index/type, existing rig goal/settings and capability guards, confirmed /Game rig/
    stopped PIE, transaction/identity readback, dry-run/no-op and optional save.
    Does not disconnect goal; refresh/solve remains unverified.
    """
    return httpx.post(f"{app.BASE_URL}/ik-rigs/solvers/goal-settings/reset", json={
        "AssetPath": asset_path, "SolverIndex": solver_index, "SolverType": expected_type,
        "GoalName": goal_name, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_ik_rig_solver_scalar(asset_path: str, solver_index: int, expected_type: str,
                              field_name: str, value: float, confirm: bool = False,
                              dry_run: bool = False, save: bool = False) -> str:
    """Edit direct writable bool/numeric dedicated solver settings field.

    Bool uses 0/1; integers must fit/integral; finite values bounded to one billion and
    native clamp metadata. Enums use declared integral values (hidden/sentinel rejected); nested writable struct paths use dots (up to 8 segments). Confirmed /Game rig/stopped PIE,
    index/type guard, scratch/native setter, transaction/readback, dry-run/no-op/save.
    Edit conditions/cross-field invariants and solve correctness are not evaluated.
    """
    return httpx.patch(f"{app.BASE_URL}/ik-rigs/solvers/settings/scalar", json={
        "AssetPath": asset_path, "SolverIndex": solver_index, "SolverType": expected_type,
        "FieldName": field_name, "ScalarValue": value,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_ik_retargeter_operation_scalar(asset_path: str, operation_index: int,
                                        expected_type: str, expected_name: str,
                                        field_name: str, value: float,
                                        confirm: bool = False, dry_run: bool = False,
                                        save: bool = False) -> str:
    """Edit direct writable bool/numeric dedicated retarget operation settings field.

    Bool 0/1, integers integral/fit, finite bounded values/native clamp checks. Enums use declared integral values (hidden/sentinel rejected); nested writable struct paths use dots (up to 8 segments). Confirmed /Game retargeter/stopped PIE, index/type/name guard, scratch
    copy/native SetSettings, transaction/readback, dry-run/no-op/save. Native setter may
    reject fields excluded by operation runtime copy policy. No solve validation.
    """
    return httpx.patch(f"{app.BASE_URL}/ik-retargeters/operations/settings/scalar", json={
        "AssetPath": asset_path, "SolverIndex": operation_index, "SolverType": expected_type,
        "ExpectedName": expected_name, "FieldName": field_name, "ScalarValue": value,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_ik_rig_solver_bone_scalar(asset_path: str, solver_index: int, expected_type: str,
                                   bone_name: str, field_name: str, value: float,
                                   confirm: bool = False, dry_run: bool = False,
                                   save: bool = False) -> str:
    """Edit direct bool/numeric field of existing native per-bone solver settings.

    Preserves bone identity through scratch/native setter. Index/type/existing bone/
    settings/capability guards, numeric fit/native clamps, confirmed /Game rig/stopped
    PIE, transaction/readback, dry-run/no-op/save. Enums use declared integral values (hidden/sentinel rejected); nested writable struct paths use dots (up to 8 segments) or solve check.
    Native edit conditions/cross-field invariants are not evaluated.
    """
    return httpx.patch(f"{app.BASE_URL}/ik-rigs/solvers/bone-settings/scalar", json={
        "AssetPath": asset_path, "SolverIndex": solver_index, "SolverType": expected_type,
        "BoneName": bone_name, "FieldName": field_name, "ScalarValue": value,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_ik_rig_solver_goal_scalar(asset_path: str, solver_index: int, expected_type: str,
                                   goal_name: str, field_name: str, value: float,
                                   confirm: bool = False, dry_run: bool = False,
                                   save: bool = False) -> str:
    """Edit direct bool/numeric field of existing native solver-specific goal settings.

    Preserves goal identity/connection through scratch/native setter. Index/type/existing
    goal/settings/capability guards, numeric fit/native clamps, confirmed /Game rig/stopped
    PIE, transaction/readback, dry-run/no-op/save. Enums use declared integral values (hidden/sentinel rejected); nested writable struct paths use dots (up to 8 segments) or solve check.
    Native edit conditions/cross-field invariants are not evaluated.
    """
    return httpx.patch(f"{app.BASE_URL}/ik-rigs/solvers/goal-settings/scalar", json={
        "AssetPath": asset_path, "SolverIndex": solver_index, "SolverType": expected_type,
        "GoalName": goal_name, "FieldName": field_name, "ScalarValue": value,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_ik_settings_spatial_value(asset_path: str, scope: str, index: int,
                                   expected_type: str, field_name: str, kind: str,
                                   value: dict, item_name: str = "",
                                   expected_name: str = "", confirm: bool = False,
                                   dry_run: bool = False, save: bool = False) -> str:
    """Edit native vector/rotator/quaternion/transform settings field.

    scope: solver, bone, goal, operation. kind: vector (X/Y/Z, <=1e6) or rotator
    (Pitch/Yaw/Roll degrees, <=360000), or quaternion (finite normalized X/Y/Z/W).
    transform uses native Translation/Rotation/Scale3D with normalized quaternion,
    bounded translation/scale and nonzero scale. item_name selects existing bone/goal; operation
    requires expected_name. Confirmed /Game asset/stopped PIE; existing identity and
    settings guards, scratch/native setter, transaction/readback, dry-run/no-op/save.
    Field path supports up to 8 writable nested struct segments separated by dots.
    Field must exactly match native struct type. Cross-field/solve validation separate.
    """
    routes = {"solver": "/ik-rigs/solvers/settings/scalar",
              "bone": "/ik-rigs/solvers/bone-settings/scalar",
              "goal": "/ik-rigs/solvers/goal-settings/scalar",
              "operation": "/ik-retargeters/operations/settings/scalar"}
    if scope not in routes or kind not in ("vector", "rotator", "quaternion", "transform"):
        raise ValueError("Invalid settings scope or spatial value kind")
    body = {"AssetPath": asset_path, "SolverIndex": index, "SolverType": expected_type,
            "FieldName": field_name, "ValueKind": kind, "ExpectedName": expected_name,
            "BoneName": item_name, "GoalName": item_name,
            "bConfirm": confirm, "bDryRun": dry_run, "bSave": save}
    body[{"vector": "VectorValue", "rotator": "RotatorValue",
          "quaternion": "QuaternionValue", "transform": "TransformValue"}[kind]] = value
    return httpx.patch(f"{app.BASE_URL}{routes[scope]}", json=body, timeout=180).text


@mcp.tool()
def set_ik_settings_text_value(asset_path: str, scope: str, index: int,
                                expected_type: str, field_name: str, kind: str,
                                value: str, item_name: str = "",
                                expected_name: str = "", confirm: bool = False,
                                dry_run: bool = False, save: bool = False) -> str:
    """Edit writable direct FName/FString IK or retarget settings field.

    scope solver/bone/goal/operation; kind name (<=128 chars) or string (<=1024), single
    line. Empty name maps to None. Existing identity/settings guards, confirmed /Game
    asset/stopped PIE, scratch/native setter, transaction/readback, dry-run/no-op/save.
    Does not rename rig bones/goals/chains or migrate consumers; semantic name references
    and native edit conditions/cross-field invariants are not validated.
    """
    routes = {"solver": "/ik-rigs/solvers/settings/scalar",
              "bone": "/ik-rigs/solvers/bone-settings/scalar",
              "goal": "/ik-rigs/solvers/goal-settings/scalar",
              "operation": "/ik-retargeters/operations/settings/scalar"}
    if scope not in routes or kind not in ("name", "string"):
        raise ValueError("Invalid settings scope or text value kind")
    return httpx.patch(f"{app.BASE_URL}{routes[scope]}", json={
        "AssetPath": asset_path, "SolverIndex": index, "SolverType": expected_type,
        "ExpectedName": expected_name, "BoneName": item_name, "GoalName": item_name,
        "FieldName": field_name, "ValueKind": kind, "TextValue": value,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def reset_ik_settings_field(asset_path: str, scope: str, index: int,
                              expected_type: str, field_name: str, item_name: str = "",
                              expected_name: str = "", confirm: bool = False,
                              dry_run: bool = False, save: bool = False) -> str:
    """Reset ONE writable direct native settings field to constructed default.

    scope solver/bone/goal/operation; item_name selects existing bone/goal, operation
    requires expected_name. Copies entire selected property, including containers/refs;
    may clear configured data. Native setter copy policy still applies. Confirmed /Game
    asset/stopped PIE, scratch/native setter, transaction/readback, dry-run/no-op/save.
    Field path supports up to 8 writable nested struct segments separated by dots.
    Does not reset sibling fields; native cross-field/solve validation remains separate.
    """
    routes = {"solver": "/ik-rigs/solvers/settings/scalar",
              "bone": "/ik-rigs/solvers/bone-settings/scalar",
              "goal": "/ik-rigs/solvers/goal-settings/scalar",
              "operation": "/ik-retargeters/operations/settings/scalar"}
    if scope not in routes:
        raise ValueError("Invalid settings scope")
    return httpx.patch(f"{app.BASE_URL}{routes[scope]}", json={
        "AssetPath": asset_path, "SolverIndex": index, "SolverType": expected_type,
        "ExpectedName": expected_name, "BoneName": item_name, "GoalName": item_name,
        "FieldName": field_name, "ValueKind": "default",
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


def set_ik_settings_name_list(asset_path: str, scope: str, index: int,
                               expected_type: str, field_name: str, values: list[str],
                               item_name: str = "", expected_name: str = "",
                               confirm: bool = False, dry_run: bool = False,
                               save: bool = False) -> str:
    """Replace writable native TArray<FName> settings field; empty list clears it.

    scope solver/bone/goal/operation; up to 256 bounded single-line names, order and
    duplicates preserved. Dot paths traverse writable structs only. Existing identity/
    settings guards, confirmed /Game asset/stopped PIE, scratch/native setter, transaction/
    readback, dry-run/no-op/save. Semantic name references/cross-field rules not validated.
    """
    routes = {"solver": "/ik-rigs/solvers/settings/scalar",
              "bone": "/ik-rigs/solvers/bone-settings/scalar",
              "goal": "/ik-rigs/solvers/goal-settings/scalar",
              "operation": "/ik-retargeters/operations/settings/scalar"}
    if scope not in routes:
        raise ValueError("Invalid settings scope")
    return httpx.patch(f"{app.BASE_URL}{routes[scope]}", json={
        "AssetPath": asset_path, "SolverIndex": index, "SolverType": expected_type,
        "ExpectedName": expected_name, "BoneName": item_name, "GoalName": item_name,
        "FieldName": field_name, "ValueKind": "names", "NameValues": values,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_ik_settings_asset_reference(asset_path: str, scope: str, index: int,
                                     expected_type: str, field_name: str,
                                     reference_path: str, item_name: str = "",
                                     expected_name: str = "", confirm: bool = False,
                                     dry_run: bool = False, save: bool = False) -> str:
    """Assign/clear writable native hard/soft object asset reference settings field.

    Empty reference_path clears; otherwise registered persistent asset matching native
    property class required, loaded even for soft references/dry-run. Class/instanced
    properties excluded. scope solver/bone/goal/operation; writable nested struct paths,
    existing identity/settings guards, confirmed /Game asset/stopped PIE, scratch/native
    setter, transaction/readback, dry-run/no-op/save. No semantic compatibility/solve check.
    """
    routes = {"solver": "/ik-rigs/solvers/settings/scalar",
              "bone": "/ik-rigs/solvers/bone-settings/scalar",
              "goal": "/ik-rigs/solvers/goal-settings/scalar",
              "operation": "/ik-retargeters/operations/settings/scalar"}
    if scope not in routes:
        raise ValueError("Invalid settings scope")
    return httpx.patch(f"{app.BASE_URL}{routes[scope]}", json={
        "AssetPath": asset_path, "SolverIndex": index, "SolverType": expected_type,
        "ExpectedName": expected_name, "BoneName": item_name, "GoalName": item_name,
        "FieldName": field_name, "ValueKind": "asset", "TextValue": reference_path,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


def set_ik_settings_number_list(asset_path: str, scope: str, index: int,
                                 expected_type: str, field_name: str, values: list[float],
                                 item_name: str = "", expected_name: str = "",
                                 confirm: bool = False, dry_run: bool = False,
                                 save: bool = False) -> str:
    """Replace native numeric-array settings field; empty list clears, enums excluded.

    Up to 256 finite bounded numbers; native integer fit/integrality and array clamp
    metadata checked. scope solver/bone/goal/operation, writable nested struct paths,
    existing identity/settings guards, confirmed /Game asset/stopped PIE, scratch/native
    setter, transaction/readback, dry-run/no-op/save. No cross-field/solve validation.
    """
    routes = {"solver": "/ik-rigs/solvers/settings/scalar",
              "bone": "/ik-rigs/solvers/bone-settings/scalar",
              "goal": "/ik-rigs/solvers/goal-settings/scalar",
              "operation": "/ik-retargeters/operations/settings/scalar"}
    if scope not in routes:
        raise ValueError("Invalid settings scope")
    return httpx.patch(f"{app.BASE_URL}{routes[scope]}", json={
        "AssetPath": asset_path, "SolverIndex": index, "SolverType": expected_type,
        "ExpectedName": expected_name, "BoneName": item_name, "GoalName": item_name,
        "FieldName": field_name, "ValueKind": "numbers", "NumberValues": values,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_ik_retargeter_curve_remap(asset_path: str, operation_index: int,
                                  expected_type: str, expected_name: str,
                                  source_curves: list[str], target_curves: list[str],
                                  copy_all_curves: bool = True, remap_curves: bool = True,
                                  confirm: bool = False, dry_run: bool = False,
                                  save: bool = False) -> str:
    """Replace native curve-remap operation pairs and copy/remap flags.

    Equal lists <=256, bounded non-None names/unique destinations; empty lists clear.
    Current index/type/name guard, confirmed /Game asset/stopped PIE, scratch/native
    setter, transaction/dry-run/no-op/save. Curve existence/animation export not verified.
    """
    return httpx.patch(f"{app.BASE_URL}/ik-retargeters/operations/curve-remap", json={
        "AssetPath": asset_path, "SolverIndex": operation_index, "SolverType": expected_type,
        "ExpectedName": expected_name, "SourceCurves": source_curves, "TargetCurves": target_curves,
        "bCopyAllCurves": copy_all_curves, "bRemapCurves": remap_curves,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def inspect_ik_retargeter_curve_remap(asset_path: str, operation_index: int,
                                      expected_type: str, expected_name: str) -> str:
    """Read typed native curve-remap pairs/flags with identifier diagnostics.

    Current index/type/name guarded persistent retargeter; exact native curve-remap op.
    Up to 256 pairs output with total/truncation, invalid names and duplicate destination
    counts. Curve existence in animation/skeletons and runtime/export behavior not checked.
    """
    return httpx.post(f"{app.BASE_URL}/ik-retargeters/operations/curve-remap/inspect", json={
        "AssetPath": asset_path, "SolverIndex": operation_index,
        "SolverType": expected_type, "ExpectedName": expected_name
    }, timeout=180).text


@mcp.tool()
def copy_ik_retargeter_operation_settings(asset_path: str, destination_index: int,
                                           expected_type: str, destination_name: str,
                                           source_index: int, source_name: str,
                                           confirm: bool = False, dry_run: bool = False,
                                           save: bool = False) -> str:
    """Copy dedicated settings between same-type native operations in one retargeter.

    Both index/name identities and exact type/settings type checked. Scratch snapshot,
    native SetSettings policy, transaction, dry-run/no-op/save. Identity/parent/enabled
    outside settings are not copied; native policy may omit fields. Confirmed /Game
    asset/stopped PIE; inspect settings afterward, no solve/export verification.
    """
    return httpx.post(f"{app.BASE_URL}/ik-retargeters/operations/settings/copy", json={
        "AssetPath": asset_path, "SolverIndex": destination_index, "SolverType": expected_type,
        "ExpectedName": destination_name, "TargetIndex": source_index, "SourceName": source_name,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def copy_ik_rig_solver_settings(asset_path: str, destination_index: int,
                                 source_index: int, expected_type: str,
                                 confirm: bool = False, dry_run: bool = False,
                                 save: bool = False) -> str:
    """Copy dedicated native settings between same-type solvers in one IK Rig.

    Current source/destination indices and exact solver/settings types guarded; same-type
    instances have no unique identity guard. Scratch snapshot/native setter copy policy,
    confirmed /Game rig/stopped PIE, transaction/dry-run/no-op/save. Bone/goal entries
    and enabled state outside settings are separate. Inspect afterward; no solve verified.
    """
    return httpx.post(f"{app.BASE_URL}/ik-rigs/solvers/settings/copy", json={
        "AssetPath": asset_path, "SolverIndex": destination_index,
        "TargetIndex": source_index, "SolverType": expected_type,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def copy_ik_rig_solver_bone_settings(asset_path: str, solver_index: int,
                                      expected_type: str, source_bone: str,
                                      destination_bone: str, confirm: bool = False,
                                      dry_run: bool = False, save: bool = False) -> str:
    """Copy values between existing per-bone settings entries within one native solver.

    Existing source/destination bones/settings, current index/type and capability guards.
    Scratch/native setter copy policy preserves destination bone identity. Confirmed
    /Game rig/stopped PIE, transaction/identity readback, dry-run/no-op/save.
    Does not create entries or verify bone suitability/solve behavior.
    """
    return httpx.post(f"{app.BASE_URL}/ik-rigs/solvers/bone-settings/copy", json={
        "AssetPath": asset_path, "SolverIndex": solver_index, "SolverType": expected_type,
        "SourceName": source_bone, "BoneName": destination_bone,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def copy_ik_rig_solver_goal_settings(asset_path: str, solver_index: int,
                                      expected_type: str, source_goal: str,
                                      destination_goal: str, confirm: bool = False,
                                      dry_run: bool = False, save: bool = False) -> str:
    """Copy existing solver goal-settings values while preserving destination identity.

    Existing source/destination rig goals/settings, current index/type/capability guards.
    Scratch/native setter copy policy, confirmed /Game rig/stopped PIE, transaction/
    identity readback, dry-run/no-op/save. Does not create connections or validate solving.
    """
    return httpx.post(f"{app.BASE_URL}/ik-rigs/solvers/goal-settings/copy", json={
        "AssetPath": asset_path, "SolverIndex": solver_index, "SolverType": expected_type,
        "SourceName": source_goal, "GoalName": destination_goal,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def reset_ik_retargeter_chain_settings(asset_path: str, target_chain: str,
                                        confirm: bool = False, dry_run: bool = False,
                                        save: bool = False) -> str:
    """Invoke native target-chain settings reset across ALL retarget operations.

    Target chain must appear in an operation mapping; matching names reported for context.
    Native implementations decide callback effects. Confirmed /Game asset/stopped PIE,
    bounded valid stack, transaction/dry-run/save. Dry-run does not simulate callbacks;
    invocation does not prove all settings reset. Inspect settings afterward; no solve.
    """
    return httpx.post(f"{app.BASE_URL}/ik-retargeters/chains/settings/reset", json={
        "AssetPath": asset_path, "ChainName": target_chain,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def auto_characterize_ik_rig(asset_path: str, confirm: bool = False,
                              dry_run: bool = False, save: bool = False) -> str:
    """Generate/apply native IK retarget root/chains from preview mesh characterization.

    REPLACES retarget definition; native apply requires matched template. Dry-run reports
    template match and planned chains without applying. Confirmed /Game rig/stopped PIE,
    bounded preview mesh/chain counts, transaction and optional save. Does not create
    solver setup or verify solving; downstream assets not explicitly migrated/saved.
    """
    return httpx.post(f"{app.BASE_URL}/ik-rigs/auto-characterize", json={
        "AssetPath": asset_path, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def auto_setup_ik_rig_fbik(asset_path: str, confirm: bool = False,
                            dry_run: bool = False, save: bool = False) -> str:
    """Apply native template FBIK setup: adds solver, creates/reuses goals/settings.

    May update chain goal assignments. Matched template, existing root/endpoints,
    conservative capacity/valid-stack and confirmed /Game/stopped PIE guards. Native
    transaction/count readback/save. Dry-run preflight only, never invokes mutating
    generator. Failure may leave partial undoable changes; inspect before retrying.
    No solve/retarget quality verified.
    """
    return httpx.post(f"{app.BASE_URL}/ik-rigs/auto-fbik", json={
        "AssetPath": asset_path, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def diagnose_ik_rig_definition(asset_path: str) -> str:
    """Read bounded IK Rig goal/chain/root/solver structural diagnostics.

    Reports invalid ownership/names/bones/transforms/alphas, chain endpoint ancestry and
    goal references, invalid solver structs/root. Up to 256 issues with total/truncation.
    Requires bounded definition; no solver-specific settings/convergence/runtime validation.
    """
    return httpx.get(f"{app.BASE_URL}/ik-rigs/diagnostics", params={
        "asset_path": asset_path
    }, timeout=180).text


@mcp.tool()
def diagnose_ik_retargeter_poses(asset_path: str) -> str:
    """Diagnose stored source/target retarget pose references and numeric validity.

    Reports missing side rigs/default/current poses, missing offset bones, nonfinite root
    translations/rotations and unnormalized quaternions. Bounded pose/offset counts,
    up to 256 issues with total/truncation; referenced rigs may load. No mutation/solve.
    """
    return httpx.get(f"{app.BASE_URL}/ik-retargeters/poses/diagnostics", params={
        "asset_path": asset_path
    }, timeout=180).text


@mcp.tool()
def inspect_ik_retargeter_operation_warning(asset_path: str, operation_index: int,
                                             expected_type: str, expected_name: str) -> str:
    """Read native warning from stored asset operation, without processor initialization.

    Index/type/name guarded persistent retargeter; bounded warning text, enabled and
    asset-struct initialized flag. State may be default/stale, not a running processor
    instance or proof of readiness. No mutation, solve or preview initialization.
    """
    return httpx.post(f"{app.BASE_URL}/ik-retargeters/operations/warning", json={
        "AssetPath": asset_path, "SolverIndex": operation_index,
        "SolverType": expected_type, "ExpectedName": expected_name
    }, timeout=180).text


@mcp.tool()
def check_ik_retargeter_readiness(asset_path: str) -> str:
    """Initialize fresh temporary native retarget processor with asset preview meshes.

    Requires stopped PIE, persistent registered retargeter and bounded valid operation/
    rig/mesh definitions. Returns native IsInitialized and bounded native errors/warnings/messages (64 each,
    2048 characters/message); warnings may also reach editor log.
    Uses asset-filled profile, no RunRetargeter/playback/export or requested asset mutation.
    Includes temporary processor operation initialized/enabled/LOD eligibility state.
    Eligibility is not execution tracing. Success does not establish motion quality
    or active editor processor readiness.
    """
    return httpx.get(f"{app.BASE_URL}/ik-retargeters/readiness", params={
        "asset_path": asset_path
    }, timeout=180).text


def evaluate_ik_retargeter_reference_pose(asset_path: str, target_bones: list[str]) -> str:
    """Evaluate one native retarget frame from source mesh global reference pose.

    Fresh temporary processor/asset-filled profile/zero delta time, stopped PIE, bounded
    rigs/meshes/operations. Empty target_bones returns first 256; explicit unique names
    select up to 256. Returns target global transforms/nonfinite count. No animation
    sampling/warmup/export/component playback or requested asset mutation; untested.
    Composed source reference scale is baked into global translations, then stripped;
    native source-scale operation is applied before retarget evaluation.
    """
    return httpx.post(f"{app.BASE_URL}/ik-retargeters/evaluate-reference-pose", json={
        "AssetPath": asset_path, "Bones": target_bones
    }, timeout=180).text


def evaluate_ik_retargeter_pose(asset_path: str, source_bones: list[str],
                                source_local_transforms: list[dict],
                                target_bones: list[str], warmup_frames: int = 0,
                                delta_time: float = 0.0, local_output: bool = False,
                                source_pose: str = "", target_pose: str = "",
                                force_all_ik_off: bool | None = None,
                                lod: int = -1, disabled_operations: list[str] | None = None,
                                source_mesh: str = "", target_mesh: str = "") -> str:
    """Evaluate a posed source skeleton through temporary native retarget processor.

    Optional registered persistent source_mesh/target_mesh overrides use native side-rig
    compatibility checks; empty uses asset preview. Asset preview selections unchanged.

    Up to 256 unique source bones and matching absolute local native transforms replace
    source reference locals; unspecified bones retain reference locals. Transforms use
    Translation/Rotation/Scale3D, finite bounded translation/scale, unit quaternion and
    nonzero scale. Hierarchy composed, scale stripped, native source scaling applied.
    Empty target selection returns first 256. local_output returns parent-relative target
    transforms; default returns global transforms. Parent transforms must be invertible. Stopped PIE, fresh processor/asset profile,
    0..120 warmup frames/0..0.1 delta (positive for warmup); constant input pose.
    Optional existing source_pose/target_pose override temporary profile selection only;
    force_all_ik_off overrides native profile IK flag only when supplied. Empty pose names
    and None IK flag use asset profile. lod=-1 bypasses LOD thresholds; 0..8 applies
    native operation thresholds (does not change mesh bone LOD).
    disabled_operations names temporarily disable processor operations after initialization
    and before each frame; asset flags unchanged. Parent initialization still runs.
    Initialization failure returns evaluated=False with native logs/operation state,
    without output transforms. Includes temporary operation state/LOD eligibility,
    not execution tracing.
    No animation sampling/export/component playback or requested asset mutation.
    """
    return httpx.post(f"{app.BASE_URL}/ik-retargeters/evaluate-reference-pose", json={
        "AssetPath": asset_path, "SourceBones": source_bones,
        "SourceLocalTransforms": source_local_transforms, "Bones": target_bones,
        "WarmupFrames": warmup_frames, "DeltaTime": delta_time, "bLocalOutput": local_output,
        "SourcePoseOverride": source_pose, "TargetPoseOverride": target_pose,
        "bForceAllIKOff": bool(force_all_ik_off),
        "bOverrideForceAllIKOff": force_all_ik_off is not None, "EvaluationLOD": lod,
        "DisabledEvaluationOps": disabled_operations or [],
        "SourceMeshPath": source_mesh, "TargetMeshPath": target_mesh
    }, timeout=180).text


@mcp.tool()
def create_ik_asset(asset_path: str, kind: str, confirm: bool = False,
                      dry_run: bool = False, save: bool = False) -> str:
    """Create native IK Rig or Retargeter asset through editor factory.

    kind rig/retargeter. Full unused /Game object path matching package basename,
    confirmed/stopped PIE. Retargeter factory creates default operations; configuration
    and mesh/rig assignment remain separate. Dry-run collision/path preflight; optional
    save. Unsaved creation stays in memory; factory undo/persistence remain unverified.
    """
    return httpx.post(f"{app.BASE_URL}/ik-assets", json={
        "AssetPath": asset_path, "Operation": kind,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def duplicate_ik_asset(source_asset_path: str, destination_asset_path: str,
                         confirm: bool = False, dry_run: bool = False,
                         save: bool = False) -> str:
    """Duplicate native IK Rig/Retargeter through AssetTools to unused /Game path.

    Registered persistent source, destination object/package collision guards, confirmed/
    stopped PIE, transaction/identity readback, dry-run/save. Native duplication preserves
    authored configuration; external meshes/rigs remain shared. No reference migration.
    Unsaved copy stays in memory; undo/reload unverified.
    """
    return httpx.post(f"{app.BASE_URL}/ik-assets/duplicate", json={
        "AssetPath": destination_asset_path, "SourceAssetPath": source_asset_path,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def export_ik_retargeter_sequences(asset_path: str, animation_paths: list[str],
                                    output_folder: str, prefix: str = "",
                                    suffix: str = "_Retargeted", confirm: bool = False,
                                    dry_run: bool = False, save: bool = False,
                                    only_animated_bones: bool = True,
                                    retain_additive_flags: bool = True,
                                    source_mesh: str = "", target_mesh: str = "",
                                    search: str = "", replace: str = "") -> str:
    """Native duplicate-and-retarget export of 1..16 sequences to unused /Game outputs.

    Optional explicit source_mesh/target_mesh paths; empty uses preview meshes. Native
    side-rig mesh compatibility checked; exact source mesh skeleton, <=100000 sampled keys, bounded meshes/stack.
    Native only-animated-bones/additive-retention options; additive retention may differ
    from preview. Reports source-to-output manifest and sample counts/length/additive/root-motion/
    root-lock flags; output dirty/skeleton metadata. Flags do not validate motion fidelity.
    Native search/replace naming runs before prefix/suffix; every computed destination
    must remain valid/unused. No overwrites/referenced-asset expansion. Confirmed/stopped PIE; dry-run validates
    destinations and temporary processor only. Native progress/cancellation can leave
    partial outputs; missing/wrong-skeleton outputs and failed saves are reported explicitly
    without automatic cleanup. Expected path/target skeleton readback, optional per-output saves
    (partial saves possible). Does not establish animation quality; inspect results.
    """
    return httpx.post(f"{app.BASE_URL}/ik-retargeters/export-sequences", json={
        "AssetPath": asset_path, "AnimationPaths": animation_paths, "OutputFolder": output_folder,
        "OutputPrefix": prefix, "OutputSuffix": suffix,
        "OutputSearch": search, "OutputReplace": replace,
        "bExportOnlyAnimatedBones": only_animated_bones,
        "bRetainAdditiveFlags": retain_additive_flags,
        "SourceMeshPath": source_mesh, "TargetMeshPath": target_mesh,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=1800).text


@mcp.tool()
def check_ik_rig_readiness(asset_path: str, mesh_path: str) -> str:
    """Initialize temporary native IK processor with explicit mesh and asset goals.

    Persistent registered rig/mesh, bounded bones/goals/valid solver stack, stopped PIE.
    Returns native initialized flag and bounded logs; may allocate transient native
    objects. No Solve/component playback/export or requested asset mutation.
    Initialization does not prove convergence or active editor processor readiness.
    """
    return httpx.post(f"{app.BASE_URL}/ik-rigs/readiness", json={
        "AssetPath": asset_path, "MeshPath": mesh_path
    }, timeout=180).text


@mcp.tool()
def evaluate_ik_rig_reference_pose(asset_path: str, mesh_path: str, bones: list[str],
                                   goal_overrides: list[dict] | None = None,
                                   source_bones: list[str] | None = None,
                                   source_local_transforms: list[dict] | None = None,
                                   local_output: bool = False,
                                   world_to_component: dict | None = None) -> str:
    """Run one fresh native IK solve from mesh reference pose with stored goal transforms.

    Stopped PIE, bounded persistent rig/mesh/solver stack. Empty bones returns first 256;
    explicit up to 256 unique names. Native logs, finite-safe global transforms and goal residuals against native final
    blended targets (position native units/rotation degrees); residuals are not a universal
    convergence verdict. Includes resolved global target position/quaternion, native space/
    transform-source enums and blend alphas. Native logs and finite-safe transforms;
    initialization failure reports evaluated=False. Identity world-to-component, no
    component playback/export or requested asset mutation. goal_overrides entries use Name,
    Position XYZ, Rotation Pitch/Yaw/Roll, PositionAlpha/RotationAlpha [0,1], bAdditive
    (false=component, true=additive), bWorldSpace (mutually exclusive with additive).
    world_to_component is a finite bounded normalized native transform, default identity.
    Optional PositionSpace/RotationSpace strings independently select component/additive/
    world, overriding shared flags. Empty strings inherit shared mode.
    Optional SourceBone selects native bone-driven goal transform from input pose;
    bone must exist, additive/world flags false and explicit space strings empty. Manual Position/Rotation
    then ignored by native resolution; alphas still apply. Up to 256 goals; asset unchanged.
    Optional matching source_bones/source_local_transforms (<=256) replace absolute
    reference locals before hierarchy composition; unspecified bones retain ref locals.
    Native transforms use Translation/Rotation/Scale3D. local_output returns parent-relative
    transforms after invertible-parent checks; default global. Goal residuals and per-bone
    input/output movement diagnostics stay global (native distance/degrees).
    Does not prove convergence.
    """
    return httpx.post(f"{app.BASE_URL}/ik-rigs/evaluate-reference-pose", json={
        "AssetPath": asset_path, "MeshPath": mesh_path, "Bones": bones,
        "GoalOverrides": goal_overrides or [], "SourceBones": source_bones or [],
        "SourceLocalTransforms": source_local_transforms or [], "bLocalOutput": local_output,
        **({"WorldToComponent": world_to_component} if world_to_component is not None else {})
    }, timeout=180).text


# Tools listed to clients. Each picks one of the functions above with its variant argument.
edit_skeleton_retarget_pose = merged_tool("edit_skeleton_retarget_pose", {
    "edit_skeleton_stored_retarget_pose": edit_skeleton_stored_retarget_pose,
    "reset_skeleton_stored_retarget_pose": reset_skeleton_stored_retarget_pose,
})
evaluate_ik_retargeter = merged_tool("evaluate_ik_retargeter", {
    "evaluate_ik_retargeter_reference_pose": evaluate_ik_retargeter_reference_pose,
    "evaluate_ik_retargeter_pose": evaluate_ik_retargeter_pose,
})
set_ik_settings = merged_tool("set_ik_settings", {
    "name_list": set_ik_settings_name_list,
    "number_list": set_ik_settings_number_list,
})
