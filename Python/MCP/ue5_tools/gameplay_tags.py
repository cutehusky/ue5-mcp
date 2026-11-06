"""Gameplay Tags."""
import httpx

from . import app
from .app import merged_tool
from .app import mcp


@mcp.tool()
def inspect_gameplay_tags(tag: str = "", search: str = "", limit: int = 100,
                          dictionary_only: bool = True) -> str:
    """Discover registered native Gameplay Tags, parent chains and editor source metadata.

    Empty tag lists registered catalog; explicit tag selects itself and descendants.
    dictionary_only excludes implicit-only descendants. Does not add or rename tags.
    """
    return httpx.get(f"{app.BASE_URL}/gameplay-tags", params={
        "tag": tag, "search": search, "limit": limit,
        "dictionary_only": str(dictionary_only).lower()
    }, timeout=180).text


def evaluate_gameplay_tags(tags: list[str], required_tags: list[str], mode: str = "All",
                           exact: bool = False) -> str:
    """Evaluate native Gameplay Tag container matching (All/Any/None).

    All names must be registered; duplicates collapse. Hierarchical matching allows
    child tags to satisfy parent requirements; exact checks explicit members only.
    Also reports native hierarchical FGameplayTagQuery evaluation and description.
    Empty containers use native semantics. Does not mutate assets or registrations.
    """
    return httpx.post(f"{app.BASE_URL}/gameplay-tags/evaluate", json={
        "Tags": tags, "RequiredTags": required_tags, "Mode": mode, "bExact": exact
    }, timeout=180).text


def evaluate_gameplay_tag_query(tags: list[str], query_nodes: list[dict], root_index: int = 0) -> str:
    """Build/evaluate a native compound GameplayTagQuery from indexed expression nodes.

    Each node has Mode, Tags and Children (zero-based indices). Modes: AllTags,
    AnyTags, NoTags, AllTagsExact, AnyTagsExact, AllExpressions, AnyExpressions, NoExpressions. Tag nodes contain
    registered Tags only; expression nodes contain Children only. All nodes must
    be reachable; cycles reject. Bounds: 128 nodes, depth 16, 512 expanded nodes,
    2048 expanded tags. Empty expressions retain native semantics. No assets mutate.
    """
    return httpx.post(f"{app.BASE_URL}/gameplay-tags/evaluate", json={
        "Tags": tags, "QueryNodes": query_nodes, "RootIndex": root_index
    }, timeout=180).text


def edit_data_asset_gameplay_tags(asset_path: str, property_name: str, tags: list[str],
                                  confirm: bool = False, dry_run: bool = False, save: bool = False) -> str:
    """Replace editable GameplayTag/GameplayTagContainer field on a /Game Data Asset.

    All tags must be registered. Scalar tag fields accept zero/one unique tag; empty
    tags clears. Requires confirmation for changes, stopped PIE, native transaction.
    Supports dry-run/save. Nested properties, Blueprint defaults and tag queries are
    not handled by this endpoint.
    """
    return httpx.patch(f"{app.BASE_URL}/gameplay-tags/asset-property", json={
        "AssetPath": asset_path, "PropertyName": property_name, "Tags": tags,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


def edit_data_asset_gameplay_tag_query(asset_path: str, property_name: str,
                                       query_nodes: list[dict], root_index: int = 0,
                                       confirm: bool = False, dry_run: bool = False, save: bool = False) -> str:
    """Replace an editable native GameplayTagQuery field on a /Game Data Asset.

    Uses the indexed expression format from evaluate_gameplay_tag_query, with the
    same registered-tag/cycle/depth/size guards. Empty query_nodes clears the query.
    Requires confirmation for changes; supports transaction, dry-run and save.
    """
    return httpx.patch(f"{app.BASE_URL}/gameplay-tags/asset-property", json={
        "AssetPath": asset_path, "PropertyName": property_name, "QueryNodes": query_nodes,
        "RootIndex": root_index, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def inspect_data_asset_gameplay_tags(asset_path: str) -> str:
    """Inspect top-level Data Asset GameplayTag/container/query fields and editability.

    Includes tag filter/category metadata, bounded registered values and query
    descriptions/referenced tags and bounded indexed query_nodes for authoring
    round-trip when query_nodes_truncated is false. Nested fields are not enumerated.
    """
    return httpx.get(f"{app.BASE_URL}/gameplay-tags/asset-properties", params={
        "asset_path": asset_path
    }, timeout=180).text


@mcp.tool()
def evaluate_data_asset_gameplay_tag_query(asset_path: str, property_name: str, tags: list[str]) -> str:
    """Evaluate the native GameplayTagQuery currently stored on a Data Asset field.

    Reads current loaded asset value, including unsaved edits; all input tags must
    be registered. Does not rebuild the query or mutate the asset. Empty query
    behavior follows native FGameplayTagQuery semantics.
    """
    return httpx.post(f"{app.BASE_URL}/gameplay-tags/asset-query/evaluate", json={
        "AssetPath": asset_path, "PropertyName": property_name, "Tags": tags
    }, timeout=180).text


@mcp.tool()
def create_gameplay_tag(tag_name: str, source_name: str, comment: str = "",
                        confirm: bool = False, dry_run: bool = False) -> str:
    """Create a persistent tag in an existing ordinary ini tag-list source.

    Native editor API writes ini immediately; no transaction undo. Requires confirm
    for new tags and stopped PIE. source_name is an existing ini basename, not a path.
    Existing exact source/comment is a no-op; conflicting or restricted tags reject.
    """
    return httpx.post(f"{app.BASE_URL}/gameplay-tags", json={
        "TagName": tag_name, "SourceName": source_name, "Comment": comment,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_gameplay_tag_sources(search: str = "", limit: int = 100) -> str:
    """Discover registered tag sources, native source types and config files.

    Indicates sources accepted for persistent tag creation, including the default
    ini list. Native, restricted and DataTable sources require their own authoring.
    """
    return httpx.get(f"{app.BASE_URL}/gameplay-tags/sources", params={
        "search": search, "limit": limit
    }, timeout=180).text


@mcp.tool()
def create_gameplay_tag_source(source_name: str, confirm: bool = False, dry_run: bool = False) -> str:
    """Register an ordinary project ini tag source using Unreal's editor API.

    Requires stopped PIE and confirm for new sources. source_name is a basename
    ending .ini, containing letters/digits/underscore/hyphen. Existing ordinary
    source is a no-op. Native API writes the file when its first tag is added;
    source registration alone is not persisted and has no transaction undo.
    """
    return httpx.post(f"{app.BASE_URL}/gameplay-tags/sources", json={
        "SourceName": source_name, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def update_gameplay_tag_comment(tag_name: str, comment: str, source_name: str = "",
                                confirm: bool = False, dry_run: bool = False) -> str:
    """Update an explicit ordinary ini tag's comment with native editor API.

    Requires one source, stopped PIE and confirmation for changes. Optional source
    name guards the selected source. Restriction metadata is preserved. Ini writes
    are immediate and not undoable; restricted/native/table tags reject.
    """
    return httpx.patch(f"{app.BASE_URL}/gameplay-tags", json={
        "TagName": tag_name, "Comment": comment, "SourceName": source_name,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def rename_gameplay_tag(tag_name: str, new_tag_name: str, rename_children: bool = True,
                        confirm: bool = False, dry_run: bool = False) -> str:
    """Rename ordinary ini tags using native editor rename/redirect behavior.

    Previews <=256 affected explicit single-source tags; rejects target collisions,
    restricted/native/table sources and overlapping ancestor/descendant prefixes.
    Requires confirm for changes; immediate ini writes are not undoable or atomic
    across files. Dry-run returns the old/new mapping without writing.
    """
    return httpx.post(f"{app.BASE_URL}/gameplay-tags/rename", json={
        "TagName": tag_name, "NewTagName": new_tag_name, "bRenameChildren": rename_children,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def delete_gameplay_tag(tag_name: str, source_name: str = "", confirm: bool = False,
                        dry_run: bool = False) -> str:
    """Delete an unused ordinary ini leaf tag through native editor API.

    Requires confirm, stopped PIE, explicit single ini source, no children, and
    native unused-tag scan success. Optional source guard. Native writes immediately
    without undo; unused scanning follows editor asset reference knowledge.
    """
    return httpx.request("DELETE", f"{app.BASE_URL}/gameplay-tags", json={
        "TagName": tag_name, "SourceName": source_name, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def move_gameplay_tags_to_source(tags: list[str], target_source: str, confirm: bool = False,
                                 dry_run: bool = False) -> str:
    """Move explicit ordinary ini tags to another existing ordinary source.

    Validates the entire <=256-tag unique batch before writing; tags already in
    target are no-ops. Requires confirmation for changes. Native multi-file writes
    are immediate/non-atomic and not undoable; inspect moved/failed and native_success
    for partial failure. Descendants move only when explicitly listed.
    """
    return httpx.post(f"{app.BASE_URL}/gameplay-tags/move", json={
        "Tags": tags, "SourceName": target_source, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_unused_gameplay_tags(search: str = "", limit: int = 100) -> str:
    """Run native editor unused-tag scan and list bounded candidates/source metadata.

    Requires stopped PIE. Reports leaf status and deletion-adapter eligibility.
    Asset/config/redirect references follow native scan knowledge; dynamic strings
    and external references may not be represented. Does not delete tags.
    """
    return httpx.get(f"{app.BASE_URL}/gameplay-tags/unused", params={
        "search": search, "limit": limit
    }, timeout=180).text


@mcp.tool()
def inspect_runtime_gameplay_tags(actor_path: str = "", search: str = "", limit: int = 100,
                                  pie_instance: int = -1) -> str:
    """Inspect owned Gameplay Tags on PIE actors implementing GameplayTagAssetInterface.

    Explicit actor must belong to selected PIE and implement the native interface.
    Returns sorted bounded tags and actor authority. Actor Tags/name arrays and
    component-only tag providers are not treated as interface-owned Gameplay Tags.
    """
    return httpx.get(f"{app.BASE_URL}/gameplay-tags/runtime", params={
        "actor_path": actor_path, "search": search, "limit": limit, "pie_instance": pie_instance
    }, timeout=180).text


def evaluate_runtime_gameplay_tag_query(actor_path: str, query_nodes: list[dict] | None = None,
                                        root_index: int = 0, asset_path: str = "",
                                        property_name: str = "", pie_instance: int = -1) -> str:
    """Evaluate a native query against current interface-owned tags of one PIE actor.

    Supply compound query_nodes or asset_path/property_name for a stored Data Asset
    query. Actor must implement GameplayTagAssetInterface in selected PIE. Evaluates
    all owned tags without snapshot truncation and does not mutate actor or asset.
    """
    return httpx.post(f"{app.BASE_URL}/gameplay-tags/runtime/evaluate", json={
        "ActorPath": actor_path, "QueryNodes": query_nodes or [], "RootIndex": root_index,
        "AssetPath": asset_path, "PropertyName": property_name, "PIEInstance": pie_instance
    }, timeout=180).text


@mcp.tool()
def inspect_runtime_gameplay_tag_providers(search: str = "", limit: int = 100, pie_instance: int = -1) -> str:
    """Discover PIE components implementing GameplayTagAssetInterface and owned tags."""
    return httpx.get(f"{app.BASE_URL}/gameplay-tags/runtime/providers", params={
        "search": search, "limit": limit, "pie_instance": pie_instance
    }, timeout=180).text


def evaluate_provider_gameplay_tag_query(provider_path: str, query_nodes: list[dict] | None = None,
                                         root_index: int = 0, asset_path: str = "",
                                         property_name: str = "", pie_instance: int = -1) -> str:
    """Evaluate supplied/stored native query on a PIE actor/component tag-interface provider."""
    return httpx.post(f"{app.BASE_URL}/gameplay-tags/runtime/evaluate", json={
        "ProviderPath": provider_path, "QueryNodes": query_nodes or [], "RootIndex": root_index,
        "AssetPath": asset_path, "PropertyName": property_name, "PIEInstance": pie_instance
    }, timeout=180).text


@mcp.tool()
def inspect_gameplay_tag_settings(search: str = "", limit: int = 100) -> str:
    """Inspect native tag loading/replication settings, table sources and redirects.

    search filters redirect old/new names; targets report current registration.
    Read-only snapshot of current project settings, with bounded redirect/table output.
    """
    return httpx.get(f"{app.BASE_URL}/gameplay-tags/settings", params={
        "search": search, "limit": limit
    }, timeout=180).text


@mcp.tool()
def resolve_gameplay_tags(tags: list[str]) -> str:
    """Resolve <=256 tag names using native Gameplay Tags import/redirect rules.

    Reports direct registration, native import acceptance, resolved name and whether
    redirection occurred. Invalid/unregistered names produce native invalid results;
    malformed names reject. Does not edit assets or redirect settings.
    """
    return httpx.post(f"{app.BASE_URL}/gameplay-tags/resolve", json={"Tags": tags}, timeout=180).text


@mcp.tool()
def edit_gameplay_tag_table_row(asset_path: str, row_name: str, tag_name: str, comment: str = "",
                                confirm: bool = False, dry_run: bool = False, save: bool = False) -> str:
    """Create/update a native GameplayTagTableRow on an existing /Game DataTable.

    Rejects duplicate tags and changing an existing row's tag identity. Supports
    confirmation, transaction, refresh, dry-run/save. Reports whether table is a
    configured tag source; editing a table does not register it in project settings.
    """
    return httpx.patch(f"{app.BASE_URL}/gameplay-tags/table-row", json={
        "AssetPath": asset_path, "PropertyName": row_name, "TagName": tag_name, "Comment": comment,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def register_gameplay_tag_table(asset_path: str, confirm: bool = False, dry_run: bool = False) -> str:
    """Register existing native GameplayTagTableRow DataTable as project tag source.

    Validates <=4096 rows, tag syntax and duplicate identities. Requires stopped
    PIE and confirmation for new source. Writes project ini immediately, refreshes
    native tag tree, and reports table dirty state; does not save table contents.
    Config writes are not transaction-undoable. Existing source is a no-op.
    """
    return httpx.post(f"{app.BASE_URL}/gameplay-tags/table-sources", json={
        "AssetPath": asset_path, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def add_runtime_loose_gameplay_tag(component_path: str, tag: str, count: int = 1,
                                   confirm: bool = False, dry_run: bool = False,
                                   pie_instance: int = -1) -> str:
    """Add a registered non-replicated loose tag to authoritative initialized PIE ASC.

    Requires confirmation, count 1..1000000. Native callbacks may activate abilities.
    Returns aggregate before/after counts; these include other sources and children.
    Does not track source ownership or provide a matching owned removal handle.
    """
    return httpx.post(f"{app.BASE_URL}/ability-system/runtime/loose-tags", json={
        "ComponentPath": component_path, "EventTag": tag, "TagCount": count,
        "bConfirm": confirm, "bDryRun": dry_run, "PIEInstance": pie_instance
    }, timeout=180).text


# Tools listed to clients. Each picks one of the functions above with its variant argument.
evaluate_gameplay_tag_expression = merged_tool("evaluate_gameplay_tag_expression", {
    "evaluate_gameplay_tags": evaluate_gameplay_tags,
    "evaluate_gameplay_tag_query": evaluate_gameplay_tag_query,
})
edit_data_asset_tag_property = merged_tool("edit_data_asset_tag_property", {
    "edit_data_asset_gameplay_tags": edit_data_asset_gameplay_tags,
    "edit_data_asset_gameplay_tag_query": edit_data_asset_gameplay_tag_query,
})
evaluate_runtime_tag_query = merged_tool("evaluate_runtime_tag_query", {
    "evaluate_runtime_gameplay_tag_query": evaluate_runtime_gameplay_tag_query,
    "evaluate_provider_gameplay_tag_query": evaluate_provider_gameplay_tag_query,
})
