"""Pose Search and Motion Matching."""
import httpx

from . import app
from .app import merged_tool
from .app import mcp


@mcp.tool()
def inspect_pose_search_database(asset_path: str) -> str:
    """Read native Pose Search database animation assets and schema summary.

    Persistent registered database; up to 256 assets with count/truncation, schema path,
    sample rate/cardinality/channel/role counts and dirty state. References may load;
    cardinality may be stale. No index build, motion-matching query/playback or mutation.
    """
    return httpx.get(f"{app.BASE_URL}/pose-search/databases/definition", params={
        "asset_path": asset_path
    }, timeout=180).text


@mcp.tool()
def inspect_pose_search_schema(asset_path: str) -> str:
    """Read native Pose Search schema roles and authored feature channels.

    Persistent registered schema; up to 64 skeleton/mirror roles and 128 channels with
    counts/truncation/ownership, sample rate/cardinality/dirty state. Authored channels
    read via typed native property reflection; finalized summary may be stale.
    No Finalize/index build/search or mutation.
    """
    return httpx.get(f"{app.BASE_URL}/pose-search/schemas/definition", params={
        "asset_path": asset_path
    }, timeout=180).text


@mcp.tool()
def list_pose_search_channel_types(search: str = "", limit: int = 64) -> str:
    """Discover loaded concrete native Pose Search feature-channel classes/defaults.

    Search <=128 chars, limit 1..128; sorted class paths, up to 64 editable fields/type
    and 2048 exported characters/value with truncation/clamp/edit-condition metadata.
    Native exporter intermediate allocation uncapped. No creation/finalize/index/search.
    """
    return httpx.get(f"{app.BASE_URL}/pose-search/channel-types", params={
        "search": search, "limit": limit
    }, timeout=180).text


@mcp.tool()
def set_pose_search_schema_sample_rate(asset_path: str, sample_rate: int,
                                         confirm: bool = False, dry_run: bool = False,
                                         save: bool = False) -> str:
    """Edit native Pose Search schema sample rate 1..240, invoking schema Finalize.

    Confirmed registered persistent /Game schema/stopped PIE, transaction/readback,
    dry-run/no-op/save. Referencing database indexes may become stale or react to native
    notifications; no explicit index build/search requested. Feature remains untested.
    """
    return httpx.patch(f"{app.BASE_URL}/pose-search/schemas/sample-rate", json={
        "AssetPath": asset_path, "SampleRate": sample_rate,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_pose_search_database_schema(asset_path: str, schema_path: str,
                                      confirm: bool = False, dry_run: bool = False,
                                      save: bool = False) -> str:
    """Assign native Pose Search schema to confirmed persistent /Game database.

    Registered persistent schema/database, stopped PIE, native property notification,
    transaction/readback, dry-run/no-op/save. Existing animation compatibility/index
    readiness not established; native listeners may request derived index work.
    Clearing unsupported; no explicit index build or motion-matching query requested.
    """
    return httpx.patch(f"{app.BASE_URL}/pose-search/databases/schema", json={
        "AssetPath": asset_path, "SchemaPath": schema_path,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def add_pose_search_schema_channel(asset_path: str, channel_class: str,
                                     confirm: bool = False, dry_run: bool = False,
                                     save: bool = False) -> str:
    """Append loaded concrete native feature channel to confirmed /Game schema.

    <128 authored channels, stopped PIE, native schema ownership/AddChannel/property
    notification/Finalize, transaction/readback/dry-run/save. New channel uses native
    defaults which may require configuration; no index validity/search established.
    """
    return httpx.post(f"{app.BASE_URL}/pose-search/schemas/channels", json={
        "AssetPath": asset_path, "ChannelClass": channel_class,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def inspect_pose_search_channel(asset_path: str, channel_index: int,
                                   expected_channel_path: str, field: str = "", child_indices: list[int] | None = None) -> str:
    """Read authored feature-channel fields guarded by current index/object identity.

    Persistent registered schema, owned channel, bounded authored array; up to 128 fields/
    4096 native export-text characters/value with constraint metadata/truncation.
    Optional field selects a dot path through <=8 structs, with leaf metadata and
    bounded struct child discovery. Native exporter intermediate allocation uncapped; no finalize/index/search/mutation.
    """
    # child_indices selects <=8 explicit-group child levels; expected path identifies final object.
    return httpx.post(f"{app.BASE_URL}/pose-search/schemas/channels/inspect", json={
        "AssetPath": asset_path, "ChannelIndex": channel_index,
        "ChildIndices": child_indices or [], "ChannelPath": expected_channel_path, "FieldName": field
    }, timeout=180).text


@mcp.tool()
def move_pose_search_schema_channel(asset_path: str, channel_index: int,
                                      expected_channel_path: str, target_index: int,
                                      confirm: bool = False, dry_run: bool = False,
                                      save: bool = False) -> str:
    """Move authored Pose Search channel to final index while preserving object/settings.

    Current index/object-path/ownership guard, bounded array, confirmed /Game schema/
    stopped PIE. Native array swaps/property event/Finalize, transaction/readback,
    dry-run/no-op/save. Derived index layout may change; no explicit index build/search.
    """
    return httpx.patch(f"{app.BASE_URL}/pose-search/schemas/channels/order", json={
        "AssetPath": asset_path, "ChannelIndex": channel_index,
        "ChannelPath": expected_channel_path, "TargetIndex": target_index,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def remove_pose_search_schema_channel(asset_path: str, channel_index: int,
                                        expected_channel_path: str,
                                        confirm: bool = False, dry_run: bool = False,
                                        save: bool = False) -> str:
    """Remove authored channel reference with native schema finalization.

    Current index/object path/ownership guard, bounded array, confirmed /Game schema/
    stopped PIE, transaction/count/identity readback, dry-run/save. Object not explicitly
    garbage-marked; shared/nested/external references not migrated. Indexes may stale
    or react to native notifications; no explicit index build/search requested.
    """
    return httpx.request("DELETE", f"{app.BASE_URL}/pose-search/schemas/channels", json={
        "AssetPath": asset_path, "ChannelIndex": channel_index,
        "ChannelPath": expected_channel_path,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def duplicate_pose_search_schema_channel(asset_path: str, channel_index: int,
                                           expected_channel_path: str,
                                           confirm: bool = False, dry_run: bool = False,
                                           save: bool = False) -> str:
    """Duplicate authored native channel/settings and append under same schema.

    Current index/object-path/ownership guard, <128 channels, confirmed /Game/stopped
    PIE. Native duplication/AddChannel/property event/Finalize, transaction/readback,
    dry-run/save. Nested instancing follows native policy; external references shared.
    Feature/index validity not established; no explicit index build/search.
    """
    return httpx.post(f"{app.BASE_URL}/pose-search/schemas/channels/duplicate", json={
        "AssetPath": asset_path, "ChannelIndex": channel_index,
        "ChannelPath": expected_channel_path,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


def set_pose_search_channel_scalar(asset_path: str, channel_index: int,
                                     expected_channel_path: str, field_name: str,
                                     value: float, confirm: bool = False,
                                     dry_run: bool = False, save: bool = False, child_indices: list[int] | None = None) -> str:
    """Edit writable direct bool/non-enum numeric feature-channel field.

    Bool 0/1, bounded finite values/native clamps; integers nonnegative <=INT32_MAX.
    Current index/object identity, owned channel, confirmed /Game schema/stopped PIE,
    schema/channel transaction/notifications/Finalize, dry-run/no-op/save. Native edit
    conditions/cross-field/index validity remain separate; no explicit index/search.
    """
    # Dot paths support up to eight writable editable struct segments; no arrays/objects.
    # Integer values honor signedness and storage width within the +/-1e9 request bound.
    # child_indices selects <=8 explicit-group child levels; expected path identifies final object.
    return httpx.patch(f"{app.BASE_URL}/pose-search/schemas/channels/scalar", json={
        "AssetPath": asset_path, "ChannelIndex": channel_index,
        "ChildIndices": child_indices or [], "ChannelPath": expected_channel_path, "FieldName": field_name, "ScalarValue": value,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def add_pose_search_schema_role(asset_path: str, role: str, skeleton_path: str,
                                  confirm: bool = False, dry_run: bool = False,
                                  save: bool = False) -> str:
    """Append native skeleton role to Pose Search schema; mirror table initially unset.

    Unique bounded non-None role, registered persistent skeleton, <64 roles, confirmed
    /Game schema/stopped PIE. Native AddSkeleton/property event/Finalize, transaction/
    readback/dry-run/save. Channel role/bone references/database compatibility not checked;
    no explicit index build/search requested.
    """
    return httpx.post(f"{app.BASE_URL}/pose-search/schemas/roles", json={
        "AssetPath": asset_path, "Role": role, "SkeletonPath": skeleton_path,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_pose_search_role_mirror_table(asset_path: str, role: str, mirror_table_path: str,
                                        confirm: bool = False, dry_run: bool = False,
                                        save: bool = False) -> str:
    """Assign/clear role mirror table; empty path clears, exact role skeleton required.

    Unique existing role, registered persistent mirror table, confirmed /Game schema/
    stopped PIE, transaction/native notification/Finalize/readback/dry-run/no-op/save.
    Mirror rows/axis and mirrored database index validity not established; no index/search.
    """
    return httpx.patch(f"{app.BASE_URL}/pose-search/schemas/roles/mirror-table", json={
        "AssetPath": asset_path, "Role": role, "MirrorTablePath": mirror_table_path,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def add_pose_search_default_channels(asset_path: str, confirm: bool = False,
                                       dry_run: bool = False, save: bool = False) -> str:
    """Initialize empty schema with native default trajectory and pose channels.

    Requires 1..64 valid skeleton roles, empty authored channel array, confirmed /Game
    schema/stopped PIE. Native AddDefaultChannels/Finalize, transaction/count readback,
    dry-run/save. Sampling defaults may need configuration; no index/search/quality proof.
    """
    return httpx.post(f"{app.BASE_URL}/pose-search/schemas/channels/defaults", json={
        "AssetPath": asset_path, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def add_pose_search_database_sequence(asset_path: str, animation_path: str,
                                        confirm: bool = False, dry_run: bool = False,
                                        save: bool = False) -> str:
    """Append native sequence entry with default sampling/options to Pose Search database.

    Registered persistent assets/schema, native skeleton compatibility, no duplicate
    sequence, <4096 entries, confirmed /Game/stopped PIE. Native property notification,
    transaction/readback/dry-run/save. No explicit index build/search/readiness proof.
    """
    return httpx.post(f"{app.BASE_URL}/pose-search/databases/sequences", json={
        "AssetPath": asset_path, "AnimationPath": animation_path,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def inspect_pose_search_database_entry(asset_path: str, animation_index: int,
                                         expected_animation_path: str) -> str:
    """Read native current-index/animation-path guarded database entry settings.

    Reports enabled/reselection/mirror/sampling options, external synchronization metadata
    and native schema skeleton compatibility. Bounded persistent registered database;
    repeated same-asset entries distinguished by current index. No index/search/mutation.
    """
    # Includes animation roles and Blend Space sampling configuration; no sample enumeration.
    return httpx.post(f"{app.BASE_URL}/pose-search/databases/entries/inspect", json={
        "AssetPath": asset_path, "AnimationIndex": animation_index,
        "AnimationPath": expected_animation_path
    }, timeout=180).text


@mcp.tool()
def set_pose_search_database_entry_flags(asset_path: str, animation_index: int,
                                           expected_animation_path: str, enabled: bool,
                                           disable_reselection: bool = False,
                                           confirm: bool = False, dry_run: bool = False,
                                           save: bool = False) -> str:
    """Edit native database entry enabled/reselection flags, rejecting external sync entries.

    Current index/animation identity, confirmed /Game database/stopped PIE, native property
    notification/transaction/readback/dry-run/no-op/save. Native listeners may request
    derived index work; no explicit build/search/runtime selection behavior verified.
    """
    return httpx.patch(f"{app.BASE_URL}/pose-search/databases/entries/flags", json={
        "AssetPath": asset_path, "AnimationIndex": animation_index,
        "AnimationPath": expected_animation_path, "bEnabled": enabled,
        "bDisableReselection": disable_reselection,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def remove_pose_search_database_entry(asset_path: str, animation_index: int,
                                        expected_animation_path: str,
                                        confirm: bool = False, dry_run: bool = False,
                                        save: bool = False) -> str:
    """Remove current native database entry, preserving source animation asset.

    Current index/animation identity guard; externally synchronized entries rejected.
    Confirmed /Game database/stopped PIE, transaction/native property event/count readback,
    dry-run/save. Reinspect shifted indices; no explicit index build/search requested.
    """
    return httpx.request("DELETE", f"{app.BASE_URL}/pose-search/databases/entries", json={
        "AssetPath": asset_path, "AnimationIndex": animation_index,
        "AnimationPath": expected_animation_path,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_pose_search_entry_sampling_range(asset_path: str, animation_index: int,
                                           expected_animation_path: str,
                                           start: float = 0, end: float = 0,
                                           confirm: bool = False, dry_run: bool = False,
                                           save: bool = False) -> str:
    """Set sequence/composite/montage entry range; [0,0] means full duration.

    Otherwise finite 0<=start<end<=animation duration. Current index/animation guard,
    external-sync rejection, confirmed /Game database/stopped PIE, native setter/property
    notification/transaction/readback/dry-run/no-op/save. Source animation untrimmed;
    no explicit index build/search or runtime selection behavior verified.
    """
    return httpx.patch(f"{app.BASE_URL}/pose-search/databases/entries/sampling-range", json={
        "AssetPath": asset_path, "AnimationIndex": animation_index,
        "AnimationPath": expected_animation_path, "RangeStart": start, "RangeEnd": end,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_pose_search_entry_mirror_policy(asset_path: str, animation_index: int,
                                       expected_animation_path: str, mirror_policy: str,
                                       confirm: bool = False, dry_run: bool = False,
                                       save: bool = False) -> str:
    """Set authored entry mirror policy: original, mirrored, or both.

    Mirrored policies require every schema role's mirror table to match its skeleton.
    Current index/animation guard, external-sync rejection, confirmed /Game database,
    stopped PIE, transaction/readback/dry-run/no-op/save. No explicit index build/search.
    """
    return httpx.patch(f"{app.BASE_URL}/pose-search/databases/entries/mirror-policy", json={
        "AssetPath": asset_path, "AnimationIndex": animation_index,
        "AnimationPath": expected_animation_path, "MirrorPolicy": mirror_policy,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def duplicate_pose_search_database_entry(asset_path: str, animation_index: int,
                                         expected_animation_path: str, insertion_index: int,
                                         confirm: bool = False, dry_run: bool = False,
                                         save: bool = False) -> str:
    """Copy complete authored database entry settings at insertion_index in [0,count].

    Shares the source animation asset. Requires current index/animation identity,
    rejects external synchronization, caps entries at 4096. Confirmed /Game/stopped
    PIE, transaction/native property event/full struct readback/dry-run/save.
    Reinspect shifted indices. No explicit index build/search.
    """
    return httpx.post(f"{app.BASE_URL}/pose-search/databases/entries/duplicate", json={
        "AssetPath": asset_path, "AnimationIndex": animation_index,
        "AnimationPath": expected_animation_path, "TargetIndex": insertion_index,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def move_pose_search_database_entry(asset_path: str, animation_index: int,
                                    expected_animation_path: str, final_index: int,
                                    confirm: bool = False, dry_run: bool = False,
                                    save: bool = False) -> str:
    """Move complete authored entry to final_index in [0,count), preserving settings.

    Current index/animation identity guard; externally synchronized source rejected.
    Confirmed /Game database/stopped PIE, transaction/native property event, full
    ordering/settings readback, dry-run/no-op/save. Reinspect shifted indices.
    No explicit index build/search or source animation mutation.
    """
    return httpx.patch(f"{app.BASE_URL}/pose-search/databases/entries/order", json={
        "AssetPath": asset_path, "AnimationIndex": animation_index,
        "AnimationPath": expected_animation_path, "TargetIndex": final_index,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def add_pose_search_database_blend_space(asset_path: str, blend_space_path: str,
                                         confirm: bool = False, dry_run: bool = False,
                                         save: bool = False) -> str:
    """Append a registered persistent native Blend Space using default entry settings.

    Requires native schema skeleton compatibility, rejects existing same-asset entry,
    caps entries at 4096. Confirmed /Game database/stopped PIE, transaction/native
    property notification/readback/dry-run/save. Sampling parameters retain native
    defaults; no explicit index build/search or motion-matching readiness established.
    """
    return httpx.post(f"{app.BASE_URL}/pose-search/databases/blend-spaces", json={
        "AssetPath": asset_path, "AnimationPath": blend_space_path,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


def set_pose_search_blend_sampling(asset_path: str, animation_index: int,
                                   expected_animation_path: str,
                                   single_sample: bool = False, grid_sampling: bool = False,
                                   horizontal_samples: int = 9, vertical_samples: int = 2,
                                   blend_x: float = 0, blend_y: float = 0,
                                   confirm: bool = False, dry_run: bool = False,
                                   save: bool = False) -> str:
    """Replace Blend Space entry sampling settings; single/grid modes are exclusive.

    Counts 1..25; bounded finite parameters use native out-of-axis handling. Current
    index/animation guard, external-sync rejection, confirmed /Game/stopped PIE,
    transaction/property notification/readback/dry-run/no-op/save. No explicit index
    build/search. Single/grid modes override counts natively.
    """
    return httpx.patch(f"{app.BASE_URL}/pose-search/databases/entries/blend-sampling", json={
        "AssetPath": asset_path, "AnimationIndex": animation_index,
        "AnimationPath": expected_animation_path, "bSingleSample": single_sample,
        "bGridSampling": grid_sampling, "HorizontalSamples": horizontal_samples,
        "VerticalSamples": vertical_samples, "BlendX": blend_x, "BlendY": blend_y,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def add_pose_search_database_composite(asset_path: str, animation_path: str,
                                       confirm: bool = False, dry_run: bool = False,
                                       save: bool = False) -> str:
    """Append a registered persistent native Animation Composite with entry defaults.

    Native schema skeleton compatibility, duplicate rejection, <4096 entry capacity,
    confirmed /Game database/stopped PIE, transaction/property notification/readback,
    dry-run/save. No explicit index build/search or motion-matching readiness proof.
    """
    return httpx.post(f"{app.BASE_URL}/pose-search/databases/composites", json={
        "AssetPath": asset_path, "AnimationPath": animation_path,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def add_pose_search_database_montage(asset_path: str, animation_path: str,
                                       confirm: bool = False, dry_run: bool = False,
                                       save: bool = False) -> str:
    """Append a registered persistent native Animation Montage with entry defaults.

    Native schema skeleton compatibility, duplicate rejection, <4096 entry capacity,
    confirmed /Game database/stopped PIE, transaction/property notification/readback,
    dry-run/save. No explicit index build/search or motion-matching readiness proof.
    """
    return httpx.post(f"{app.BASE_URL}/pose-search/databases/montages", json={
        "AssetPath": asset_path, "AnimationPath": animation_path,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_pose_search_database_cost_bias(asset_path: str, field: str, value: float,
                                       confirm: bool = False, dry_run: bool = False,
                                       save: bool = False) -> str:
    """Set BaseCostBias, ContinuingPoseCostBias, LoopingCostBias or
    ContinuingInteractionCostBias to a finite value within +/-1e9.

    Negative costs favor selection/continuation, positive costs discourage it.
    Confirmed /Game database/stopped PIE, transaction/native property notification,
    float readback/dry-run/no-op/save. No runtime selection behavior verified and
    no explicit index build/search. Continuing-pose/interaction biases are excluded from native DDC hash.
    """
    return httpx.patch(f"{app.BASE_URL}/pose-search/databases/cost-bias", json={
        "AssetPath": asset_path, "FieldName": field, "ScalarValue": value,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_pose_search_database_search_mode(asset_path: str, mode: str,
                                         confirm: bool = False, dry_run: bool = False,
                                         save: bool = False) -> str:
    """Set BruteForce, PCAKDTree, VPTree or EventOnly native search mode.

    VPTree/EventOnly are experimental native modes. Confirmed /Game/stopped PIE,
    transaction/native property event/readback/dry-run/no-op/save. Notifications may
    request index work; no explicit index build/search or runtime behavior verified.
    """
    return httpx.patch(f"{app.BASE_URL}/pose-search/databases/search-mode", json={
        "AssetPath": asset_path, "SearchMode": mode,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_pose_search_database_index_tuning(asset_path: str, field: str, value: float,
                                          confirm: bool = False, dry_run: bool = False,
                                          save: bool = False) -> str:
    """Set one native index tuning field with bounds and integer validation.

    NumberOfPrincipalComponents 1..64; KDTreeMaxLeafSize 1..256;
    KDTreeQueryNumNeighbors 1..600; KDTreeQueryNumNeighborsWithDuplicates 0..600
    (zero means unbounded duplicate evaluation); PosePruningSimilarityThreshold and
    PCAValuesPruningSimilarityThreshold finite 0..1e9. Search mode determines
    applicability. Confirmed /Game/stopped PIE, transaction/property event/readback,
    dry-run/no-op/save. No explicit index build/search or quality verification.
    """
    return httpx.patch(f"{app.BASE_URL}/pose-search/databases/index-tuning", json={
        "AssetPath": asset_path, "FieldName": field, "ScalarValue": value,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def inspect_pose_search_normalization_set(asset_path: str) -> str:
    """Inspect up to 256 authored database references in a native normalization set.

    Reports validity, schema path, entry count and reciprocal set reference. References
    may load; no normalization/index build, compatibility proof, search or mutation.
    """
    return httpx.get(f"{app.BASE_URL}/pose-search/normalization-sets/definition", params={
        "asset_path": asset_path
    }, timeout=180).text


@mcp.tool()
def set_pose_search_database_normalization_set(asset_path: str, normalization_set_path: str = "",
                                               confirm: bool = False, dry_run: bool = False,
                                               save: bool = False) -> str:
    """Assign a registered native normalization set; empty path clears the reference.

    Set membership is edited separately. Confirmed /Game database/stopped PIE,
    transaction/property event/readback/dry-run/no-op/save. No explicit normalization
    or index build/search; cross-database compatibility remains unverified.
    """
    return httpx.patch(f"{app.BASE_URL}/pose-search/databases/normalization-set", json={
        "AssetPath": asset_path, "NormalizationSetPath": normalization_set_path,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_pose_search_normalization_databases(asset_path: str, database_paths: list[str],
                                            confirm: bool = False, dry_run: bool = False,
                                            save: bool = False) -> str:
    """Replace normalization-set membership with up to 256 unique native databases.

    Empty list clears. Preserves requested order; reciprocal database set references
    are edited separately. Confirmed /Game set/stopped PIE, registered persistent
    databases, transaction/property event/readback/dry-run/no-op/save. No explicit
    normalization/index build/search or schema compatibility proof.
    """
    return httpx.patch(f"{app.BASE_URL}/pose-search/normalization-sets/databases", json={
        "AssetPath": asset_path, "DatabasePaths": database_paths,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_pose_search_database_tags(asset_path: str, tags: list[str],
                                   confirm: bool = False, dry_run: bool = False,
                                   save: bool = False) -> str:
    """Replace ordered FName metadata tags; empty list clears (not Gameplay Tags).

    Up to 256 unique non-None names, each <=128 characters, single-line with no
    boundary whitespace. FName uniqueness is case-insensitive. Confirmed /Game,
    stopped PIE, transaction/property event/readback/dry-run/no-op/save. No explicit
    index build/search or runtime filtering behavior verified.
    """
    return httpx.patch(f"{app.BASE_URL}/pose-search/databases/tags", json={
        "AssetPath": asset_path, "Tags": tags,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def create_pose_search_asset(asset_path: str, kind: str, skeleton_path: str = "",
                              schema_path: str = "", confirm: bool = False,
                              dry_run: bool = False, save: bool = False) -> str:
    """Create schema, database, normalization_set or interaction via native factories.

    Schema requires skeleton_path; database requires schema_path. Destination is a
    new /Game package/object with matching names; no overwrite. Confirmed stopped
    PIE, transaction, factory defaults, dry-run/save. Further authoring may be needed;
    no explicit index build/search or runtime readiness proof.
    """
    return httpx.post(f"{app.BASE_URL}/pose-search/assets", json={
        "AssetPath": asset_path, "AssetKind": kind, "SkeletonPath": skeleton_path,
        "SchemaPath": schema_path, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def duplicate_pose_search_asset(asset_path: str, source_asset_path: str,
                                 confirm: bool = False, dry_run: bool = False,
                                 save: bool = False) -> str:
    """Duplicate a schema, database, normalization set or interaction via AssetTools.

    Destination is a new /Game package/object with matching names; no overwrite.
    Instanced objects follow native duplication; external asset references remain
    shared. Confirmed stopped PIE, transaction, identity/class readback, dry-run/save.
    No explicit index build/search or runtime readiness proof.
    """
    return httpx.post(f"{app.BASE_URL}/pose-search/assets/duplicate", json={
        "AssetPath": asset_path, "SourceAssetPath": source_asset_path,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


def set_pose_search_channel_name(asset_path: str, channel_index: int,
                                 expected_channel_path: str, field: str, value: str,
                                 confirm: bool = False, dry_run: bool = False,
                                 save: bool = False, child_indices: list[int] | None = None) -> str:
    """Set an editable FName channel field; empty value means None.

    Current index/object identity and ownership guards, bounded single-line name,
    confirmed /Game/stopped PIE, transaction/channel+schema notifications/finalize,
    readback/dry-run/no-op/save. Dot paths traverse up to eight editable struct fields (e.g. Bone.BoneName).
    Arrays, objects and read-only fields are rejected.
    Native role resolution/edit conditions/index validity require later verification.
    """
    # child_indices selects <=8 explicit-group child levels; expected path identifies final object.
    return httpx.patch(f"{app.BASE_URL}/pose-search/schemas/channels/name", json={
        "AssetPath": asset_path, "ChannelIndex": channel_index,
        "ChildIndices": child_indices or [], "ChannelPath": expected_channel_path, "FieldName": field, "NameValue": value,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


def set_pose_search_channel_enum(asset_path: str, channel_index: int,
                                 expected_channel_path: str, field: str, value: str,
                                 confirm: bool = False, dry_run: bool = False,
                                 save: bool = False, child_indices: list[int] | None = None) -> str:
    """Set native enum channel field by short or qualified enumerator name.

    Rejects hidden/sentinel values. Supports dot paths through up to eight writable
    editable struct fields; no arrays/objects. Current index/identity/ownership guards,
    confirmed /Game/stopped PIE, transaction/notifications/finalize/readback/dry-run/save.
    No explicit index build/search or cross-field validity proof.
    """
    # child_indices selects <=8 explicit-group child levels; expected path identifies final object.
    return httpx.patch(f"{app.BASE_URL}/pose-search/schemas/channels/enum", json={
        "AssetPath": asset_path, "ChannelIndex": channel_index,
        "ChildIndices": child_indices or [], "ChannelPath": expected_channel_path, "FieldName": field, "NameValue": value,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def reset_pose_search_channel_field(asset_path: str, channel_index: int,
                                    expected_channel_path: str, field: str,
                                    confirm: bool = False, dry_run: bool = False,
                                    save: bool = False, child_indices: list[int] | None = None) -> str:
    """Reset scalar/enum/name/vector/linear-color leaf to its native channel class default.

    Dot paths through <=8 writable editable structs; no arrays/objects or whole
    arbitrary structs. Current index/identity/ownership guards, confirmed /Game/stopped PIE,
    transaction/notifications/finalize/readback/dry-run/no-op/save. Native defaults
    may require further role/bone configuration; no explicit index build/search.
    """
    # child_indices selects <=8 explicit-group child levels; expected path identifies final object.
    return httpx.post(f"{app.BASE_URL}/pose-search/schemas/channels/reset-field", json={
        "AssetPath": asset_path, "ChannelIndex": channel_index,
        "ChildIndices": child_indices or [], "ChannelPath": expected_channel_path, "FieldName": field,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_pose_search_schema_preprocessor(asset_path: str, mode: str,
                                        confirm: bool = False, dry_run: bool = False,
                                        save: bool = False) -> str:
    """Set schema data preprocessor: None, Normalize, NormalizeOnlyByDeviation,
    or NormalizeWithCommonSchema (last two are native experimental modes).

    Confirmed /Game schema/stopped PIE, transaction/native property event/finalize,
    readback/dry-run/no-op/save. No explicit normalization/index build/search or
    runtime behavior verified.
    """
    return httpx.patch(f"{app.BASE_URL}/pose-search/schemas/preprocessor", json={
        "AssetPath": asset_path, "Preprocessor": mode,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_pose_search_schema_permutation(asset_path: str, field: str, value: float,
                                       confirm: bool = False, dry_run: bool = False,
                                       save: bool = False) -> str:
    """Set NumberOfPermutations (integer 1..1e9), PermutationsSampleRate (1..240),
    or PermutationsTimeOffset (finite +/-1e9 seconds).

    Indexing cost grows with count; rate applies when count exceeds one. Confirmed
    /Game/stopped PIE, transaction/property event/finalize/readback/dry-run/no-op/save.
    No explicit index build/search or runtime behavior verified.
    """
    return httpx.patch(f"{app.BASE_URL}/pose-search/schemas/permutations", json={
        "AssetPath": asset_path, "FieldName": field, "ScalarValue": value,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_pose_search_schema_flag(asset_path: str, field: str, enabled: bool,
                                 confirm: bool = False, dry_run: bool = False,
                                 save: bool = False) -> str:
    """Set bAddDataPadding, bInjectAdditionalDebugChannels or
    bDrawInjectAdditionalDebugChannels. Padding aligns feature data at memory cost;
    debug flags control native injected channels/drawing.

    Confirmed /Game/stopped PIE, transaction/property event/finalize/readback,
    dry-run/no-op/save. No explicit index build/search or debug rendering verified.
    """
    return httpx.patch(f"{app.BASE_URL}/pose-search/schemas/flags", json={
        "AssetPath": asset_path, "FieldName": field, "bEnabled": enabled,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def request_pose_search_database_index(asset_path: str, request: str = "continue",
                                        confirm: bool = False, dry_run: bool = False) -> str:
    """Request asynchronous native derived indexing: new or continue.

    New refreshes keys; continue observes existing work or starts missing work, and
    does not guarantee freshness. Reissue continue to poll without replacing work.
    Returns in_progress/success/failed. Confirmed /Game/stopped PIE, persistent
    uncooked database/schema. No blocking wait, asset save, search or playback.
    Success does not establish a nonempty index or motion-matching quality.
    """
    return httpx.post(f"{app.BASE_URL}/pose-search/databases/index-request", json={
        "AssetPath": asset_path, "IndexRequest": request,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_pose_search_role_skeleton(asset_path: str, role: str, skeleton_path: str,
                                  confirm: bool = False, dry_run: bool = False,
                                  save: bool = False) -> str:
    """Replace an existing schema role skeleton with a registered persistent skeleton.

    Existing mirror table must exactly match replacement; clear it first otherwise.
    Unique role, confirmed /Game/stopped PIE, transaction/property event/finalize,
    readback/dry-run/no-op/save. Channel bones/dependent databases are not migrated
    or saved. No explicit index build/search or compatibility proof.
    """
    return httpx.patch(f"{app.BASE_URL}/pose-search/schemas/roles/skeleton", json={
        "AssetPath": asset_path, "Role": role, "SkeletonPath": skeleton_path,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def move_pose_search_schema_role(asset_path: str, role: str, final_index: int,
                                 confirm: bool = False, dry_run: bool = False,
                                 save: bool = False) -> str:
    """Move a unique role entry to final_index, preserving names and references.

    Bounded 64-role schema, confirmed /Game/stopped PIE, native struct-array swaps,
    transaction/ArrayMove/finalize/ordering readback/dry-run/no-op/save. Derived
    cardinality/index state may change; no explicit index build/search.
    """
    return httpx.patch(f"{app.BASE_URL}/pose-search/schemas/roles/order", json={
        "AssetPath": asset_path, "Role": role, "TargetIndex": final_index,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def remove_pose_search_schema_role(asset_path: str, role: str,
                                   confirm: bool = False, dry_run: bool = False,
                                   save: bool = False) -> str:
    """Remove a unique schema role entry. Channels/dependent databases are not migrated;
    update their role references separately to resolve any resulting missing roles.

    Bounded 64-role schema, confirmed /Game/stopped PIE, transaction/native array
    removal/property event/finalize/ordering readback/dry-run/save. Last role may be
    removed for schema reconstruction; no explicit index build/search.
    """
    return httpx.request("DELETE", f"{app.BASE_URL}/pose-search/schemas/roles", json={
        "AssetPath": asset_path, "Role": role,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def duplicate_pose_search_schema_role(asset_path: str, role: str, new_role: str,
                                      confirm: bool = False, dry_run: bool = False,
                                      save: bool = False) -> str:
    """Append a new unique role sharing source role skeleton and mirror table.

    Native finalization rebuilds derived bone caches. Existing channel roles and
    dependent databases unchanged. Capacity 64, confirmed /Game/stopped PIE,
    transaction/ArrayAdd/finalize/ordering readback/dry-run/save. No index build/search.
    """
    return httpx.post(f"{app.BASE_URL}/pose-search/schemas/roles/duplicate", json={
        "AssetPath": asset_path, "Role": role, "NameValue": new_role,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def rename_pose_search_schema_role(asset_path: str, role: str, new_role: str,
                                   confirm: bool = False, dry_run: bool = False,
                                   save: bool = False) -> str:
    """Rename a unique schema role, retaining skeleton/mirror references.

    Channel role names and dependent assets are not migrated; update references
    separately. Unique non-None destination, bounded 64 roles, confirmed /Game/
    stopped PIE, transaction/property notification/finalize/ordering readback,
    dry-run/no-op/save. FName comparison treats case-only renames as no-op.
    No explicit index build/search.
    """
    return httpx.patch(f"{app.BASE_URL}/pose-search/schemas/roles/name", json={
        "AssetPath": asset_path, "Role": role, "NameValue": new_role,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def add_pose_search_database_multi_animation(asset_path: str, animation_path: str,
                                             confirm: bool = False, dry_run: bool = False,
                                             save: bool = False) -> str:
    """Append a native experimental multi-animation asset with default entry settings.

    All 1..64 unique animation roles require matching unique schema roles, valid
    skeletons and registered compatible source animations. Duplicate rejection,
    capacity 4096, confirmed /Game/stopped PIE, transaction/property event/readback/
    dry-run/save. No explicit index build/search or interaction-quality proof.
    """
    return httpx.post(f"{app.BASE_URL}/pose-search/databases/multi-animations", json={
        "AssetPath": asset_path, "AnimationPath": animation_path,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def inspect_pose_search_interaction(asset_path: str) -> str:
    """Inspect native experimental interaction asset items (up to 64).

    Reports roles, duplicates, animations, preview meshes, finite-safe warp weights,
    origin validity/text and banking weight. No warp evaluation, sampling, index
    build/search or mutation.
    """
    return httpx.get(f"{app.BASE_URL}/pose-search/interactions/definition", params={
        "asset_path": asset_path
    }, timeout=180).text


@mcp.tool()
def add_pose_search_interaction_item(asset_path: str, role: str, animation_path: str,
                                     confirm: bool = False, dry_run: bool = False,
                                     save: bool = False) -> str:
    """Append experimental interaction item with unique role and registered animation.

    Capacity 64, native origin/warp defaults, confirmed /Game/stopped PIE,
    transaction/ArrayAdd/full struct readback/dry-run/save. Duration synchronization
    and role/schema compatibility require separate configuration. No warp evaluation,
    index build or search.
    """
    return httpx.post(f"{app.BASE_URL}/pose-search/interactions/items", json={
        "AssetPath": asset_path, "Role": role, "AnimationPath": animation_path,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def remove_pose_search_interaction_item(asset_path: str, item_index: int,
                                        expected_role: str, expected_animation_path: str,
                                        confirm: bool = False, dry_run: bool = False,
                                        save: bool = False) -> str:
    """Remove interaction item guarded by current index, role and animation identity.

    Capacity 64, confirmed /Game/stopped PIE, transaction/ArrayRemove/full remaining
    settings+ordering readback/dry-run/save. Source animations/dependent databases
    unchanged; reinspect shifted indices. No warp evaluation/index build/search.
    """
    return httpx.request("DELETE", f"{app.BASE_URL}/pose-search/interactions/items", json={
        "AssetPath": asset_path, "AnimationIndex": item_index, "Role": expected_role,
        "AnimationPath": expected_animation_path,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def move_pose_search_interaction_item(asset_path: str, item_index: int,
                                      expected_role: str, expected_animation_path: str,
                                      final_index: int, confirm: bool = False,
                                      dry_run: bool = False, save: bool = False) -> str:
    """Move complete interaction item to final_index, preserving all item settings.

    Current index/role/animation guard, <=64 items, confirmed /Game/stopped PIE,
    transaction/ArrayMove/full ordering+settings readback/dry-run/no-op/save.
    Reinspect shifted indices. No warp evaluation/index build/search.
    """
    return httpx.patch(f"{app.BASE_URL}/pose-search/interactions/items/order", json={
        "AssetPath": asset_path, "AnimationIndex": item_index, "Role": expected_role,
        "AnimationPath": expected_animation_path, "TargetIndex": final_index,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_pose_search_interaction_weight(asset_path: str, item_index: int,
                                       expected_role: str, expected_animation_path: str,
                                       field: str, value: float, confirm: bool = False,
                                       dry_run: bool = False, save: bool = False) -> str:
    """Set WarpingWeightRotation or WarpingWeightTranslation to finite 0..1.

    Native runtime normalizes relative weights across items. Current index/role/
    animation identity guard, <=64 items, confirmed /Game/stopped PIE, transaction/
    property event/full item readback/dry-run/no-op/save. No warp evaluation or
    index build/search.
    """
    return httpx.patch(f"{app.BASE_URL}/pose-search/interactions/items/weight", json={
        "AssetPath": asset_path, "AnimationIndex": item_index, "Role": expected_role,
        "AnimationPath": expected_animation_path, "FieldName": field, "ScalarValue": value,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_pose_search_interaction_banking(asset_path: str, value: float,
                                        confirm: bool = False, dry_run: bool = False,
                                        save: bool = False) -> str:
    """Set experimental interaction WarpingBankingWeight to finite 0..1.

    Confirmed /Game asset/stopped PIE, native property notification, transaction,
    float readback/dry-run/no-op/save. Native warping interprets banking factor;
    no warp evaluation, index build/search or motion-quality proof.
    """
    return httpx.patch(f"{app.BASE_URL}/pose-search/interactions/banking-weight", json={
        "AssetPath": asset_path, "ScalarValue": value,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_pose_search_interaction_origin(asset_path: str, item_index: int,
                                       expected_role: str, expected_animation_path: str,
                                       origin: dict, confirm: bool = False,
                                       dry_run: bool = False, save: bool = False) -> str:
    """Set role origin relative to shared interaction frame using native Transform JSON.

    origin: {"translation":{"x":0,"y":0,"z":0},
    "rotation":{"x":0,"y":0,"z":0,"w":1},"scale3D":{"x":1,"y":1,"z":1}}.
    Finite bounded transform, normalized quaternion, invertible scale required.
    Current index/role/animation guard, confirmed /Game/stopped PIE, transaction/
    native property event/full item readback/dry-run/no-op/save. No warp evaluation.
    """
    return httpx.patch(f"{app.BASE_URL}/pose-search/interactions/items/origin", json={
        "AssetPath": asset_path, "AnimationIndex": item_index, "Role": expected_role,
        "AnimationPath": expected_animation_path, "Origin": origin,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_pose_search_interaction_animation(asset_path: str, item_index: int,
                                          expected_role: str, expected_animation_path: str,
                                          animation_path: str, confirm: bool = False,
                                          dry_run: bool = False, save: bool = False) -> str:
    """Replace interaction item animation, retaining role/origin/warp settings.

    Registered persistent replacement, exact existing preview-override skeleton match,
    current index/role/animation identity guard, <=64 items, confirmed /Game/stopped
    PIE, transaction/property event/full item readback/dry-run/no-op/save. Dependent
    schema compatibility and duration synchronization require separate configuration.
    """
    return httpx.patch(f"{app.BASE_URL}/pose-search/interactions/items/animation", json={
        "AssetPath": asset_path, "AnimationIndex": item_index, "Role": expected_role,
        "AnimationPath": expected_animation_path, "SourceAssetPath": animation_path,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_pose_search_interaction_preview_mesh(asset_path: str, item_index: int,
                                             expected_role: str, expected_animation_path: str,
                                             mesh_path: str = "", confirm: bool = False,
                                             dry_run: bool = False, save: bool = False) -> str:
    """Assign editor preview mesh override; empty path clears to native default preview.

    Registered persistent mesh must exactly match item animation skeleton. Current
    index/role/animation guard, <=64 items, confirmed /Game/stopped PIE, transaction/
    property event/full item readback/dry-run/no-op/save. No warp evaluation/rendering.
    """
    return httpx.patch(f"{app.BASE_URL}/pose-search/interactions/items/preview-mesh", json={
        "AssetPath": asset_path, "AnimationIndex": item_index, "Role": expected_role,
        "AnimationPath": expected_animation_path, "SourceAssetPath": mesh_path,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def rename_pose_search_interaction_role(asset_path: str, item_index: int,
                                        expected_role: str, expected_animation_path: str,
                                        new_role: str, confirm: bool = False,
                                        dry_run: bool = False, save: bool = False) -> str:
    """Rename selected interaction role to a unique non-None name, retaining settings.

    Schema/channel roles and dependent assets are not migrated. Current index/role/
    animation guard, <=64 items, confirmed /Game/stopped PIE, transaction/property
    event/full item readback/dry-run/no-op/save. Case-only FName changes are no-op.
    No warp evaluation/index build/search.
    """
    return httpx.patch(f"{app.BASE_URL}/pose-search/interactions/items/role", json={
        "AssetPath": asset_path, "AnimationIndex": item_index, "Role": expected_role,
        "AnimationPath": expected_animation_path, "NameValue": new_role,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def duplicate_pose_search_interaction_item(asset_path: str, item_index: int,
                                           expected_role: str, expected_animation_path: str,
                                           new_role: str, confirm: bool = False,
                                           dry_run: bool = False, save: bool = False) -> str:
    """Append complete item copy under unique non-None role, sharing asset references.

    Origin/warp settings copied. Current index/role/animation identity, capacity 64,
    confirmed /Game/stopped PIE, transaction/ArrayAdd/full item readback/dry-run/save.
    Schema/channel role references and dependent assets unchanged; no warp evaluation
    or index build/search.
    """
    return httpx.post(f"{app.BASE_URL}/pose-search/interactions/items/duplicate", json={
        "AssetPath": asset_path, "AnimationIndex": item_index, "Role": expected_role,
        "AnimationPath": expected_animation_path, "NameValue": new_role,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def evaluate_pose_search_interaction_warp(asset_path: str, expected_roles: list[str],
                                          actor_root_transforms: list[dict], time: float = 0,
                                          relevant_roles: list[str] | None = None,
                                          mirror_table_paths: list[str] | None = None) -> str:
    """Evaluate native interaction warp at one time using ordered actor root transforms.

    1..64 roots in native Transform JSON, matching expected role order. Finite bounded
    transforms, normalized rotations/nonzero scales, valid animations and warp weights.
    Empty relevant_roles selects all; otherwise unique existing role names.
    Native alignment with fewer than two relevant roles returns input roots. Optional mirror_table_paths must match item count; empty entries are unmirrored.
    Each nonempty registered table must match that role animation skeleton; returns native text, structured transforms, validity and input/output
    translation/angular deltas. Deltas describe alignment, not quality or convergence.
    Stopped PIE; no asset edit/save/index build/search, actor movement or playback.
    """
    return httpx.post(f"{app.BASE_URL}/pose-search/interactions/evaluate-warp", json={
        "AssetPath": asset_path, "ExpectedRoles": expected_roles,
        "ActorRootTransforms": actor_root_transforms, "ScalarValue": time,
        "RelevantRoles": relevant_roles or [], "MirrorTablePaths": mirror_table_paths or []
    }, timeout=180).text


@mcp.tool()
def inspect_pose_search_entry_timing(asset_path: str, animation_index: int,
                                     expected_animation_path: str,
                                     blend_x: float = 0, blend_y: float = 0) -> str:
    """Inspect native duration and effective interval at supplied blend parameters.

    Blend Space authored interval is normalized; effective interval is seconds.
    Current index/animation identity, valid bounded roles, finite parameters/stopped
    PIE. No pose sampling, index build/search, mutation or playback.
    """
    return httpx.post(f"{app.BASE_URL}/pose-search/databases/entries/timing", json={
        "AssetPath": asset_path, "AnimationIndex": animation_index,
        "AnimationPath": expected_animation_path, "BlendX": blend_x, "BlendY": blend_y
    }, timeout=180).text


@mcp.tool()
def set_pose_search_blend_sampling_range(asset_path: str, animation_index: int,
                                         expected_animation_path: str,
                                         start: float = 0, end: float = 0,
                                         confirm: bool = False, dry_run: bool = False,
                                         save: bool = False) -> str:
    """Set normalized Blend Space entry interval: [0,0] full duration or 0<=start<end<=1.

    Native effective range scales by parameter-dependent duration. Current index/
    animation guard, external-sync rejection, confirmed /Game/stopped PIE, transaction/
    property notification/readback/dry-run/no-op/save. Source Blend Space untrimmed;
    no explicit index build/search.
    """
    return httpx.patch(f"{app.BASE_URL}/pose-search/databases/entries/blend-range", json={
        "AssetPath": asset_path, "AnimationIndex": animation_index,
        "AnimationPath": expected_animation_path, "RangeStart": start, "RangeEnd": end,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def replace_pose_search_entry_animation(asset_path: str, animation_index: int,
                                        expected_animation_path: str, animation_path: str,
                                        confirm: bool = False, dry_run: bool = False,
                                        save: bool = False) -> str:
    """Replace supported entry animation preserving authored settings.

    Every replacement role must match schema skeleton; existing interval must fit.
    Reset interval to full duration before switching Blend Space normalized/time units.
    Current index/animation guard, external-sync rejection, confirmed /Game/stopped
    PIE, transaction/property event/full entry readback/dry-run/no-op/save.
    No explicit index build/search or runtime quality proof.
    """
    return httpx.patch(f"{app.BASE_URL}/pose-search/databases/entries/animation", json={
        "AssetPath": asset_path, "AnimationIndex": animation_index,
        "AnimationPath": expected_animation_path, "SourceAssetPath": animation_path,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


def set_pose_search_channel_vector(asset_path: str, channel_index: int,
                                   expected_channel_path: str, field: str,
                                   x: float, y: float, z: float,
                                   confirm: bool = False, dry_run: bool = False,
                                   save: bool = False, child_indices: list[int] | None = None) -> str:
    """Set editable native FVector leaf through <=8 writable struct segments.

    Finite components within +/-1e9; no array/object traversal. Current index/object
    identity/ownership guards, confirmed /Game/stopped PIE, transaction/channel+schema
    notifications/finalize/readback/dry-run/no-op/save. Native edit conditions and
    cross-field validity remain unverified; no explicit index build/search.
    """
    # child_indices selects <=8 explicit-group child levels; expected path identifies final object.
    return httpx.patch(f"{app.BASE_URL}/pose-search/schemas/channels/vector", json={
        "AssetPath": asset_path, "ChannelIndex": channel_index,
        "ChildIndices": child_indices or [], "ChannelPath": expected_channel_path, "FieldName": field,
        "VectorValue": {"x": x, "y": y, "z": z},
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_pose_search_pose_bones(asset_path: str, channel_index: int,
                               expected_channel_path: str, bones: list[dict],
                               confirm: bool = False, dry_run: bool = False,
                               save: bool = False, child_indices: list[int] | None = None) -> str:
    """Replace pose-channel sampled bones, up to 64 unique channel sampling-role skeleton bones.

    bones: [{"Bone":"foot_l","Flags":3,"Weight":1,"NormalizationGroup":"feet"}].
    Flags combine velocity=1/position=2/rotation=4/phase=8; finite nonnegative weights.
    Optional DebugColor={"r":0,"g":1,"b":0,"a":1}; default green.
    Empty list clears; finite bounded linear color components required. Identity/ownership guards,
    confirmed /Game/stopped PIE, transaction/notifications/finalize/readback/dry-run/save.
    No explicit index build/search or feature-quality proof.
    """
    # child_indices selects <=8 explicit-group child levels; expected path identifies final object.
    return httpx.patch(f"{app.BASE_URL}/pose-search/schemas/channels/pose-bones", json={
        "AssetPath": asset_path, "ChannelIndex": channel_index,
        "ChildIndices": child_indices or [], "ChannelPath": expected_channel_path, "SampledBones": bones,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_pose_search_trajectory_samples(asset_path: str, channel_index: int,
                                       expected_channel_path: str, samples: list[dict],
                                       confirm: bool = False, dry_run: bool = False,
                                       save: bool = False, child_indices: list[int] | None = None) -> str:
    """Replace trajectory samples (<=64), empty list clears.

    samples: [{"Offset":0.5,"Flags":2,"Weight":1,"NormalizationGroup":"future"}].
    Flags velocity=1/position=2/velocityDirection=4/facing=8, XY variants=16/32/64/128.
    Optional DebugColor native RGBA object, default blue. Bounded finite offsets,
    nonnegative weights, identity/ownership, confirmed /Game/stopped PIE, transaction/
    notifications/finalize/readback/dry-run/save. No explicit index build/search.
    """
    # child_indices selects <=8 explicit-group child levels; expected path identifies final object.
    return httpx.patch(f"{app.BASE_URL}/pose-search/schemas/channels/trajectory-samples", json={
        "AssetPath": asset_path, "ChannelIndex": channel_index,
        "ChildIndices": child_indices or [], "ChannelPath": expected_channel_path, "TrajectorySamples": samples,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def finalize_pose_search_schema(asset_path: str, confirm: bool = False,
                                 dry_run: bool = False, save: bool = False) -> str:
    """Invoke native schema finalization/notifications and report resulting cached layout.

    Unique valid skeleton roles, <=128 authored channels, confirmed /Game/stopped PIE,
    transaction/dry-run/save. Native failures may reset cardinality/channels and log
    errors; requested save is skipped when native errors are observed.
    Returns bounded native diagnostics and needs_review; absence of errors does not
    prove successful construction. Dry-run returns existing
    cache. Native listeners may request index work; no explicit index build/search.
    """
    return httpx.post(f"{app.BASE_URL}/pose-search/schemas/finalize", json={
        "AssetPath": asset_path, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def add_pose_search_group_child(asset_path: str, channel_index: int,
                                expected_group_path: str, channel_class: str,
                                confirm: bool = False, dry_run: bool = False,
                                save: bool = False, child_indices: list[int] | None = None) -> str:
    """Append native channel child to an authored top-level explicit Group channel.

    Excludes generated pose/trajectory children; concrete loaded native class, capacity
    128, group identity/ownership, confirmed /Game/stopped PIE, transaction/native
    notifications/finalize/readback/dry-run/save. Child defaults may need configuration;
    no explicit index build/search.
    """
    # child_indices selects <=8 explicit-group child levels; expected path identifies final object.
    return httpx.post(f"{app.BASE_URL}/pose-search/schemas/channels/group-children", json={
        "AssetPath": asset_path, "ChannelIndex": channel_index,
        "ChildIndices": child_indices or [], "ChannelPath": expected_group_path, "ChannelClass": channel_class,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def remove_pose_search_group_child(asset_path: str, channel_index: int,
                                   expected_group_path: str, child_index: int,
                                   expected_child_path: str, confirm: bool = False,
                                   dry_run: bool = False, save: bool = False,
                                   child_indices: list[int] | None = None) -> str:
    """Remove authored explicit-group child reference guarded by index/object identity.

    child_indices selects parent group through <=8 explicit-group levels. Capacity
    128; confirmed /Game/stopped PIE, transaction/ArrayRemove/finalize/order readback/
    dry-run/save. UObject preserved for undo, other references unchanged. Reinspect
    shifted child indices. No explicit index build/search.
    """
    return httpx.request("DELETE", f"{app.BASE_URL}/pose-search/schemas/channels/group-children", json={
        "AssetPath": asset_path, "ChannelIndex": channel_index,
        "ChannelPath": expected_group_path, "ChildIndices": child_indices or [],
        "AnimationIndex": child_index, "SourceAssetPath": expected_child_path,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def move_pose_search_group_child(asset_path: str, channel_index: int,
                                 expected_group_path: str, child_index: int,
                                 expected_child_path: str, final_index: int,
                                 confirm: bool = False, dry_run: bool = False,
                                 save: bool = False, child_indices: list[int] | None = None) -> str:
    """Move explicit-group child to final_index, preserving child objects/settings.

    Nested parent selected by child_indices (<=8 levels), current group/child identity,
    <=128 children, confirmed /Game/stopped PIE, transaction/ArrayMove/finalize/full
    pointer ordering readback/dry-run/no-op/save. Reinspect shifted indices.
    No explicit index build/search.
    """
    return httpx.patch(f"{app.BASE_URL}/pose-search/schemas/channels/group-children/order", json={
        "AssetPath": asset_path, "ChannelIndex": channel_index,
        "ChannelPath": expected_group_path, "ChildIndices": child_indices or [],
        "AnimationIndex": child_index, "SourceAssetPath": expected_child_path,
        "TargetIndex": final_index, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def duplicate_pose_search_group_child(asset_path: str, channel_index: int,
                                      expected_group_path: str, child_index: int,
                                      expected_child_path: str, confirm: bool = False,
                                      dry_run: bool = False, save: bool = False,
                                      child_indices: list[int] | None = None) -> str:
    """Append native duplicate of explicit-group child, preserving authored settings.

    Instanced descendants follow native duplication; external asset refs shared.
    Nested parent path <=8 levels, current group/child identity, capacity 128,
    confirmed /Game/stopped PIE, transaction/ArrayAdd/finalize/order readback/dry-run/
    save. No explicit index build/search.
    """
    return httpx.post(f"{app.BASE_URL}/pose-search/schemas/channels/group-children/duplicate", json={
        "AssetPath": asset_path, "ChannelIndex": channel_index,
        "ChannelPath": expected_group_path, "ChildIndices": child_indices or [],
        "AnimationIndex": child_index, "SourceAssetPath": expected_child_path,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


def set_pose_search_channel_color(asset_path: str, channel_index: int,
                                  expected_channel_path: str, field: str,
                                  r: float, g: float, b: float, a: float = 1,
                                  confirm: bool = False, dry_run: bool = False,
                                  save: bool = False, child_indices: list[int] | None = None) -> str:
    """Set native FLinearColor leaf with finite RGBA components within +/-1e6.

    Up to eight editable struct segments and eight explicit-group child levels;
    no array/object traversal. Identity/ownership, confirmed /Game/stopped PIE,
    transaction/notifications/finalize/readback/dry-run/no-op/save. No color-space
    conversion, rendering or explicit index build/search.
    """
    return httpx.patch(f"{app.BASE_URL}/pose-search/schemas/channels/color", json={
        "AssetPath": asset_path, "ChannelIndex": channel_index,
        "ChannelPath": expected_channel_path, "ChildIndices": child_indices or [],
        "FieldName": field, "ColorValue": {"r": r, "g": g, "b": b, "a": a},
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_pose_search_database_preview_mesh(asset_path: str, mesh_path: str = "",
                                          confirm: bool = False, dry_run: bool = False,
                                          save: bool = False) -> str:
    """Set editor preview override; empty path clears to native skeleton default.

    Registered persistent mesh must exactly match schema default-role skeleton.
    Confirmed /Game/stopped PIE, transaction/property event/readback/dry-run/no-op/save.
    Preview is excluded from native DDC hash; no rendering or index build/search.
    """
    return httpx.patch(f"{app.BASE_URL}/pose-search/databases/preview-mesh", json={
        "AssetPath": asset_path, "SourceAssetPath": mesh_path,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_pose_search_database_interval(asset_path: str, field: str,
                                      start_offset: float, end_offset: float,
                                      confirm: bool = False, dry_run: bool = False,
                                      save: bool = False) -> str:
    """Set ExcludeFromDatabaseParameters or AdditionalExtrapolationTime offsets.

    Native seconds relative to animation start/end; inverted intervals intentionally
    allowed (e.g. exclusion 0,-0.3). Finite +/-1e6, confirmed /Game/stopped PIE,
    transaction/property event/readback/dry-run/no-op/save. Offsets may exclude all
    poses for short assets; no explicit index build/search or quality proof.
    """
    return httpx.patch(f"{app.BASE_URL}/pose-search/databases/interval", json={
        "AssetPath": asset_path, "FieldName": field,
        "RangeStart": start_offset, "RangeEnd": end_offset,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def inspect_pose_search_sampling_points(asset_path: str, animation_index: int,
                                        expected_animation_path: str) -> str:
    """Enumerate native entry blend parameters (up to 1024) without pose sampling.

    Current index/animation guard, valid <=64 role animations, stopped PIE; authored
    sampling counts 1..32, Blend Space grid <=1024. Native single/grid/1D/wrapped
    parameter rules retained. Multi-animation uses first Blend Space role domain.
    No index build/search/mutation.
    """
    return httpx.post(f"{app.BASE_URL}/pose-search/databases/entries/sampling-points", json={
        "AssetPath": asset_path, "AnimationIndex": animation_index,
        "AnimationPath": expected_animation_path
    }, timeout=180).text


def set_pose_search_multi_animation_sampling(asset_path: str, animation_index: int,
                                             expected_animation_path: str,
                                             horizontal_samples: int = 9,
                                             vertical_samples: int = 2,
                                             confirm: bool = False, dry_run: bool = False,
                                             save: bool = False) -> str:
    """Set multi-animation entry sample counts 1..25 using native first Blend Space role domain.

    Count mode only; stored single/grid flags cleared, blend parameters set to zero.
    Native no-Blend-Space entries yield one zero parameter. Current index/animation,
    external-sync rejection, confirmed /Game/stopped PIE, transaction/property event/
    readback/dry-run/no-op/save. No explicit index build/search.
    """
    return httpx.patch(f"{app.BASE_URL}/pose-search/databases/entries/blend-sampling", json={
        "AssetPath": asset_path, "AnimationIndex": animation_index,
        "AnimationPath": expected_animation_path,
        "HorizontalSamples": horizontal_samples, "VerticalSamples": vertical_samples,
        "bSingleSample": False, "bGridSampling": False, "BlendX": 0, "BlendY": 0,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def sample_pose_search_entry_root(asset_path: str, animation_index: int,
                                   expected_animation_path: str, role: str, time: float,
                                   blend_x: float = 0, blend_y: float = 0,
                                   sample_times: list[float] | None = None,
                                   preprocessing_sample_rate: int = 30,
                                   enforce_compressed_sampling: bool = True) -> str:
    """Temporarily sample native role root transform at time/blend parameters.

    Current index/animation identity, unique existing role, skeleton-backed animation,
    valid role origin, bounded finite time/parameters, stopped PIE. Native compressed-data enforcement is configurable; root preprocessing rate
    1..240 (default 30), looping/extrapolation retained; returns root transform/validity.
    Optional sample_times (<=256 finite 0..1e6) yields ordered native root text
    and consecutive translation/angular deltas, reusing one sampler. No index
    build/search, asset mutation or actor playback.
    """
    return httpx.post(f"{app.BASE_URL}/pose-search/databases/entries/sample-root", json={
        "AssetPath": asset_path, "AnimationIndex": animation_index,
        "AnimationPath": expected_animation_path, "Role": role, "ScalarValue": time,
        "BlendX": blend_x, "BlendY": blend_y, "SampleTimes": sample_times or [],
        "SampleRate": preprocessing_sample_rate,
        "bEnforceCompressedSampling": enforce_compressed_sampling
    }, timeout=180).text


@mcp.tool()
def reset_pose_search_asset_setting(asset_path: str, field: str,
                                     confirm: bool = False, dry_run: bool = False,
                                     save: bool = False) -> str:
    """Reset one direct schema/database/interaction setting to native class default.

    Supports editable scalar/enum/name/vector/color/interval fields; excludes arrays,
    objects and transient settings. Confirmed /Game/stopped PIE, transaction/native
    property event/finalize/readback/dry-run/no-op/save. Defaults do not guarantee
    cross-field validity; no explicit index build/search.
    """
    return httpx.post(f"{app.BASE_URL}/pose-search/assets/reset-field", json={
        "AssetPath": asset_path, "FieldName": field,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def copy_pose_search_asset_setting(asset_path: str, source_asset_path: str, field: str,
                                    confirm: bool = False, dry_run: bool = False,
                                    save: bool = False) -> str:
    """Copy one direct setting between exact-class schema/database/interaction assets.

    Editable scalar/enum/name/vector/color/interval fields; finite numeric/struct source
    values, no arrays/objects/transients. Registered persistent source, confirmed
    /Game destination/stopped PIE, transaction/notifications/readback/dry-run/no-op/save.
    Source is unchanged; cross-field destination validity remains unverified.
    """
    return httpx.post(f"{app.BASE_URL}/pose-search/assets/copy-field", json={
        "AssetPath": asset_path, "SourceAssetPath": source_asset_path, "FieldName": field,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def inspect_pose_search_asset_setting(asset_path: str, field: str) -> str:
    """Inspect direct schema/database/interaction setting beside native class default.

    Supports scalar/enum/name/vector/color/interval values; reports native type,
    constraints, bounded text/truncation and default difference. Registered persistent
    asset required; no confirmation, mutation, finalization or index build/search.
    """
    return httpx.post(f"{app.BASE_URL}/pose-search/assets/inspect-field", json={
        "AssetPath": asset_path, "FieldName": field
    }, timeout=180).text


# Tools listed to clients. Each picks one of the functions above with its variant argument.
set_pose_search_sampling = merged_tool("set_pose_search_sampling", {
    "set_pose_search_blend_sampling": set_pose_search_blend_sampling,
    "set_pose_search_multi_animation_sampling": set_pose_search_multi_animation_sampling,
})
set_pose_search_channel = merged_tool("set_pose_search_channel", {
    "scalar": set_pose_search_channel_scalar,
    "name": set_pose_search_channel_name,
    "enum": set_pose_search_channel_enum,
    "vector": set_pose_search_channel_vector,
    "color": set_pose_search_channel_color,
})
