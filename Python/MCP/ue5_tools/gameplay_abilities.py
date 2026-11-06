"""Gameplay Ability System authoring and runtime."""
import httpx

from . import app
from .app import mcp


@mcp.tool()
def inspect_ability_system_runtime(component_path: str = "", search: str = "", limit: int = 100,
                                   pie_instance: int = -1) -> str:
    """Inspect selected PIE ability-system components, owned tags and granted abilities.

    Includes active effect handles/classes/stacks/duration/remaining/period,
    active spec modifier magnitudes/attributes/operations, effect asset/granted tags,
    ability dynamic source tags, context instigator/causer/
    source and bounded tag SetByCaller magnitudes,
    attribute-set fields with native base/current values and finite flags,
    owner/avatar, authority/registration, ability handles/classes/levels,
    input IDs, source objects, active status and bounded native instance paths/
    cancelability/policies. Snapshots are bounded; explicit
    component paths must belong to selected PIE. Does not activate or grant abilities.
    """
    return httpx.get(f"{app.BASE_URL}/ability-system/runtime", params={
        "component_path": component_path, "search": search, "limit": limit, "pie_instance": pie_instance
    }, timeout=180).text


@mcp.tool()
def control_ability_system_runtime(component_path: str, ability_handle: str, operation: str,
                                   confirm: bool = False, dry_run: bool = False, pie_instance: int = -1) -> str:
    """Activate/cancel one granted ability on an authoritative initialized PIE component.

    Use handle from current inspection. activate invokes native checks without remote
    activation; cancel requires confirmation and respects native cancelability.
    Dry-run validates target only, without predicting costs/cooldowns/activation success.
    Response reports native acceptance and immediate active state, not completion.
    """
    return httpx.post(f"{app.BASE_URL}/ability-system/runtime", json={
        "ComponentPath": component_path, "AbilityHandle": ability_handle, "Operation": operation,
        "bConfirm": confirm, "bDryRun": dry_run, "PIEInstance": pie_instance
    }, timeout=180).text


@mcp.tool()
def remove_runtime_gameplay_effect(component_path: str, effect_handle: str, stacks_to_remove: int = -1,
                                   confirm: bool = False, dry_run: bool = False, pie_instance: int = -1) -> str:
    """Remove an active native Gameplay Effect or stack count on authoritative PIE component.

    Handle must come from selected component's current inspection. -1 removes all
    stacks; positive count removes that many. Requires confirm; dry-run validates
    only. Native callbacks/removal rules apply; response reports immediate state.
    """
    return httpx.request("DELETE", f"{app.BASE_URL}/ability-system/runtime/effects", json={
        "ComponentPath": component_path, "EffectHandle": effect_handle, "StacksToRemove": stacks_to_remove,
        "bConfirm": confirm, "bDryRun": dry_run, "PIEInstance": pie_instance
    }, timeout=180).text


@mcp.tool()
def list_ability_system_classes(kind: str = "ability", search: str = "", limit: int = 100) -> str:
    """Discover loaded ability/effect/attribute_set/execution/magnitude/effect_component/cue_actor/cue_static classes and fields.

    Abilities include native instancing/net execution policy values. Registry
    blueprint_candidates include unloaded assets and require load/compile validation.
    """
    return httpx.get(f"{app.BASE_URL}/ability-system/classes", params={
        "kind": kind, "search": search, "limit": limit
    }, timeout=180).text


@mcp.tool()
def send_runtime_gameplay_event(component_path: str, event_tag: str, magnitude: float = 0.0,
                                instigator_path: str = "", dry_run: bool = False,
                                pie_instance: int = -1, target_path: str = "",
                                instigator_tags: list[str] | None = None, target_tags: list[str] | None = None,
                                optional_object_path: str = "", optional_object2_path: str = "",
                                target_actor_paths: list[str] | None = None) -> str:
    """Dispatch native GAS gameplay event to an authoritative initialized PIE component.

    Tag/payload tags must be registered; target defaults to component avatar.
    Explicit target and optional instigator must be
    in selected PIE. Optional object paths reference loaded same-PIE runtime objects.
    target_actor_paths supplies <=64 unique same-PIE actors as native ActorArray
    target data. Reports native triggered-ability count, not completion. Dry-run
    validates input/targets without executing callbacks or predicting activation.
    """
    return httpx.post(f"{app.BASE_URL}/ability-system/runtime/events", json={
        "ComponentPath": component_path, "EventTag": event_tag, "EventMagnitude": magnitude,
        "InstigatorPath": instigator_path, "TargetPath": target_path,
        "TargetActorPaths": target_actor_paths or [], "OptionalObjectPath": optional_object_path, "OptionalObject2Path": optional_object2_path,
        "InstigatorTags": instigator_tags or [], "TargetTags": target_tags or [], "bDryRun": dry_run, "PIEInstance": pie_instance
    }, timeout=180).text


@mcp.tool()
def set_runtime_gameplay_attribute(component_path: str, attribute_path: str, base_value: float,
                                   confirm: bool = False, dry_run: bool = False, pie_instance: int = -1) -> str:
    """Set native attribute base value on an authoritative PIE ability-system component.

    Use field_path from current attribute inspection. Rejects ambiguous duplicate
    spawned sets, nonfinite/out-of-bounds values and native clamp violations.
    Requires confirmation for change. Native callbacks/aggregation may alter readback;
    no direct current-value overwrite or asset mutation. Dry-run validates only.
    """
    return httpx.patch(f"{app.BASE_URL}/ability-system/runtime/attributes", json={
        "ComponentPath": component_path, "AttributePath": attribute_path, "BaseValue": base_value,
        "bConfirm": confirm, "bDryRun": dry_run, "PIEInstance": pie_instance
    }, timeout=180).text


@mcp.tool()
def grant_runtime_gameplay_ability(component_path: str, ability_class_path: str, level: int = 1,
                                   input_id: int = -1, confirm: bool = False, dry_run: bool = False,
                                   pie_instance: int = -1, dynamic_source_tags: list[str] | None = None, source_object_path: str = "") -> str:
    """Grant loaded concrete native/compiled ability class on authoritative initialized PIE component.

    dynamic_source_tags supplies registered spec tags before native grant callbacks.
    source_object_path optionally identifies a loaded same-PIE runtime source object.
    Requires confirmation; dry-run validates only. Repeated calls grant additional
    specs. Native OnGiveAbility callbacks can activate/remove grants immediately;
    response reports observed handle/granted state. Does not edit persistent defaults.
    """
    return httpx.post(f"{app.BASE_URL}/ability-system/runtime/abilities", json={
        "ComponentPath": component_path, "AbilityClassPath": ability_class_path,
        "Level": level, "InputID": input_id, "DynamicSourceTags": dynamic_source_tags or [], "SourceObjectPath": source_object_path, "bConfirm": confirm,
        "bDryRun": dry_run, "PIEInstance": pie_instance
    }, timeout=180).text


@mcp.tool()
def remove_runtime_gameplay_ability(component_path: str, ability_handle: str, operation: str = "clear",
                                    confirm: bool = False, dry_run: bool = False, pie_instance: int = -1) -> str:
    """Remove one granted ability by native handle on authoritative PIE component.

    clear invokes ClearAbility; on_end removes when finished (immediately if inactive)
    and clears native InputID. Requires confirmation. Native callbacks/list locks may
    defer removal; response reports observed immediate granted/active state.
    """
    return httpx.request("DELETE", f"{app.BASE_URL}/ability-system/runtime/abilities", json={
        "ComponentPath": component_path, "AbilityHandle": ability_handle, "Operation": operation,
        "bConfirm": confirm, "bDryRun": dry_run, "PIEInstance": pie_instance
    }, timeout=180).text


@mcp.tool()
def apply_runtime_gameplay_effect(component_path: str, effect_class_path: str,
                                  target_component_path: str = "", level: float = 1.0,
                                  set_by_caller: dict | None = None, confirm: bool = False,
                                  dry_run: bool = False, pie_instance: int = -1, effect_causer_path: str = "", source_object_path: str = "",
                                  dynamic_asset_tags: list[str] | None = None) -> str:
    """Apply native effect spec from authoritative PIE source to target (defaults self).

    Uses loaded concrete/current effect class, positive bounded level and registered
    tag-to-finite-number SetByCaller map. Requires confirmation. Native application
    rules execute; instant effects may leave no active handle. Optional effect causer
    must be authoritative same-PIE actor; source object must be loaded same-PIE runtime object. Dry-run validates
    targets/inputs without constructing specs or predicting application success.
    """
    return httpx.post(f"{app.BASE_URL}/ability-system/runtime/effects", json={
        "ComponentPath": component_path, "EffectClassPath": effect_class_path,
        "TargetComponentPath": target_component_path, "EffectLevel": level,
        "DynamicAssetTags": dynamic_asset_tags or [], "EffectCauserPath": effect_causer_path, "SourceObjectPath": source_object_path,
        "SetByCaller": set_by_caller or {}, "bConfirm": confirm, "bDryRun": dry_run,
        "PIEInstance": pie_instance
    }, timeout=180).text


@mcp.tool()
def set_runtime_gameplay_effect_level(component_path: str, effect_handle: str, level: int,
                                      confirm: bool = False, dry_run: bool = False, pie_instance: int = -1) -> str:
    """Update active native Gameplay Effect level by component-owned handle.

    Requires authoritative selected PIE, integer level 1-1000000 and confirmation
    for changes. Native magnitude recalculation/callbacks apply; response reports
    immediate level and continued active state. Dry-run validates without callbacks.
    """
    return httpx.patch(f"{app.BASE_URL}/ability-system/runtime/effects", json={
        "ComponentPath": component_path, "EffectHandle": effect_handle, "Level": level,
        "bConfirm": confirm, "bDryRun": dry_run, "PIEInstance": pie_instance
    }, timeout=180).text


@mcp.tool()
def update_runtime_effect_magnitudes(component_path: str, effect_handle: str, set_by_caller: dict,
                                     confirm: bool = False, dry_run: bool = False, pie_instance: int = -1) -> str:
    """Update native active effect SetByCaller tag magnitudes on authoritative PIE component.

    Requires 1-64 registered tag/finite-value pairs and confirmation. Native batch
    recalculation runs; unused tags may not affect modifiers. Dry-run validates only.
    """
    return httpx.patch(f"{app.BASE_URL}/ability-system/runtime/effects/magnitudes", json={
        "ComponentPath": component_path, "EffectHandle": effect_handle, "SetByCaller": set_by_caller,
        "bConfirm": confirm, "bDryRun": dry_run, "PIEInstance": pie_instance
    }, timeout=180).text


@mcp.tool()
def inhibit_runtime_gameplay_effect(component_path: str, effect_handle: str, inhibit: bool = True,
                                    invoke_gameplay_cues: bool = True, confirm: bool = False,
                                    dry_run: bool = False, pie_instance: int = -1) -> str:
    """Inhibit/uninhibit native active effect on authoritative selected PIE component.

    Requires confirmation for changes. Native callbacks may remove the effect;
    use returned current_handle, not previous_handle, for subsequent operations.
    Optional gameplay cue events follow native setter behavior. Dry-run validates only.
    """
    return httpx.patch(f"{app.BASE_URL}/ability-system/runtime/effects/inhibition", json={
        "ComponentPath": component_path, "EffectHandle": effect_handle, "bInhibit": inhibit,
        "bInvokeGameplayCues": invoke_gameplay_cues, "bConfirm": confirm,
        "bDryRun": dry_run, "PIEInstance": pie_instance
    }, timeout=180).text


@mcp.tool()
def dispatch_runtime_ability_input(component_path: str, ability_handle: str, operation: str,
                                    dry_run: bool = False, pie_instance: int = -1) -> str:
    """Dispatch press/release native spec input callback for one authoritative PIE ability.

    Updates spec input state and invokes native callback. Does not emulate local
    player bindings, automatically activate inactive abilities, or promise replicated
    input events. Explicit activation uses control_ability_system_runtime.
    """
    return httpx.post(f"{app.BASE_URL}/ability-system/runtime/input", json={
        "ComponentPath": component_path, "AbilityHandle": ability_handle, "Operation": operation,
        "bDryRun": dry_run, "PIEInstance": pie_instance
    }, timeout=180).text


@mcp.tool()
def set_runtime_gameplay_ability_level(component_path: str, ability_handle: str, level: int,
                                       confirm: bool = False, dry_run: bool = False, pie_instance: int = -1) -> str:
    """Update granted native ability spec level with replication dirty marking.

    Requires selected authoritative PIE, current handle, level 1-1000000 and confirm
    for changes. Does not recreate existing effect specs or active ability internals.
    Dry-run validates only; response reports immediate granted spec level.
    """
    return httpx.patch(f"{app.BASE_URL}/ability-system/runtime/abilities", json={
        "ComponentPath": component_path, "AbilityHandle": ability_handle, "Level": level,
        "bConfirm": confirm, "bDryRun": dry_run, "PIEInstance": pie_instance
    }, timeout=180).text


@mcp.tool()
def check_runtime_gameplay_ability(component_path: str, ability_handle: str, pie_instance: int = -1,
                                   source_tags: list[str] | None = None, target_tags: list[str] | None = None) -> str:
    """Run native CanActivateAbility and return current result/relevant failure tags.

    Uses primary ability instance when present, otherwise granted definition.
    Optional registered source_tags/target_tags supply explicit activation context;
    omitted containers preserve native null context. Also runs native cost/cooldown checks and reports remaining/duration and tags.
    Executes custom activation checks without activating or reserving costs; result
    does not guarantee a later activation. Requires initialized selected PIE component.
    """
    return httpx.post(f"{app.BASE_URL}/ability-system/runtime/abilities/check", json={
        "ComponentPath": component_path, "AbilityHandle": ability_handle, "PIEInstance": pie_instance,
        "bUseCheckTags": source_tags is not None or target_tags is not None,
        "InstigatorTags": source_tags or [], "TargetTags": target_tags or []
    }, timeout=180).text


@mcp.tool()
def inspect_runtime_ability_tag_counts(component_path: str, tags: list[str], pie_instance: int = -1) -> str:
    """Inspect native aggregate GAS counts for <=256 registered tags in selected PIE.

    Includes explicit/hierarchical owned membership. Counts include child-tag
    contributions and do not identify loose-tag ownership or effect sources.
    """
    return httpx.post(f"{app.BASE_URL}/ability-system/runtime/tag-counts", json={
        "ComponentPath": component_path, "Tags": tags, "PIEInstance": pie_instance
    }, timeout=180).text


@mcp.tool()
def inspect_gameplay_effect_definition(class_path: str) -> str:
    """Inspect loaded native/Blueprint GameplayEffect class default definition.

    Reports structured cue tags/ranges/magnitude attributes, owned native effect
    components and their bounded editable fields,
    execution calculation classes, duration/stacking policies, modifier paths/operations/magnitude
    types and bounded reflected editable defaults. Does not create specs or evaluate
    context-dependent modifier magnitudes; no class defaults are changed.
    """
    return httpx.get(f"{app.BASE_URL}/ability-system/effect-definition", params={
        "class_path": class_path
    }, timeout=180).text


@mcp.tool()
def inspect_gameplay_ability_definition(class_path: str) -> str:
    """Inspect loaded ability defaults, policies, asset tags, triggers and cost/cooldown classes.

    Includes structured trigger_rows with tags, registration and native source values,
    plus bounded reflected editable defaults. Native virtual cost/cooldown
    getters run on the class default object; no grant or activation is performed.
    """
    return httpx.get(f"{app.BASE_URL}/ability-system/ability-definition", params={
        "class_path": class_path
    }, timeout=180).text


@mcp.tool()
def load_ability_system_class(class_path: str, kind: str = "ability") -> str:
    """Load/validate native or existing Blueprint GAS class without compiling or editing.

    kind is ability/effect/attribute_set/execution/magnitude/effect_component/cue_actor/cue_static. Blueprint class paths require _C and a
    registered asset; class must be concrete/current/compiled. Loading can execute
    normal Unreal class/asset initialization. Runtime controls still validate target.
    """
    return httpx.post(f"{app.BASE_URL}/ability-system/classes/load", json={
        "ClassPath": class_path, "Kind": kind
    }, timeout=180).text


@mcp.tool()
def inspect_gameplay_attribute_definition(class_path: str) -> str:
    """Inspect loaded AttributeSet class native attribute paths and default values.

    Includes inherited float/GameplayAttributeData fields, replicated flag, clamps
    and finite base/current defaults. Runtime aggregated values use PIE inspection.
    """
    return httpx.get(f"{app.BASE_URL}/ability-system/attribute-definition", params={
        "class_path": class_path
    }, timeout=180).text


@mcp.tool()
def add_runtime_attribute_set(component_path: str, class_path: str, confirm: bool = False,
                               dry_run: bool = False, pie_instance: int = -1) -> str:
    """Create/register concrete native AttributeSet on authoritative initialized PIE component.

    Rejects related existing sets to avoid ambiguous attributes; capped at 64 sets.
    Requires confirmation. Initializes class defaults; no persistent defaults change.
    Blueprint AttributeSet construction and removal are not supported here.
    """
    return httpx.post(f"{app.BASE_URL}/ability-system/runtime/attribute-sets", json={
        "ComponentPath": component_path, "ClassPath": class_path, "bConfirm": confirm,
        "bDryRun": dry_run, "PIEInstance": pie_instance
    }, timeout=180).text


@mcp.tool()
def evaluate_gameplay_effect_definition(class_path: str, level: float = 1.0) -> str:
    """Evaluate native level-only static effect magnitudes and period without applying.

    Reports static availability for duration/modifiers. Context-dependent magnitudes
    return null; does not simulate captures, executions, SetByCaller or requirements.
    """
    return httpx.post(f"{app.BASE_URL}/ability-system/effect-definition/evaluate", json={
        "ClassPath": class_path, "EffectLevel": level
    }, timeout=180).text


@mcp.tool()
def execute_runtime_gameplay_cue(component_path: str, cue_tag: str, raw_magnitude: float = 0.0,
                                 normalized_magnitude: float = 0.0, dry_run: bool = False,
                                 pie_instance: int = -1, location: dict | None = None, normal: dict | None = None) -> str:
    """Execute one-shot native Gameplay Cue on authoritative initialized PIE component.

    Requires registered GameplayCue descendant and finite raw/normalized [0,1]
    magnitudes. Location defaults to avatar; optional X/Y/Z location and nonzero
    normal are validated (normal is normalized). Uses native effect context. Submission does not prove notify matching
    or rendered output; dry-run validates without cue dispatch.
    """
    return httpx.post(f"{app.BASE_URL}/ability-system/runtime/cues/execute", json={
        "ComponentPath": component_path, "EventTag": cue_tag, "EventMagnitude": raw_magnitude,
        "CueLocation": location or {}, "bUseAvatarLocation": location is None,
        "CueNormal": normal if normal is not None else {"X": 0, "Y": 0, "Z": 1},
        "NormalizedMagnitude": normalized_magnitude, "bDryRun": dry_run, "PIEInstance": pie_instance
    }, timeout=180).text


@mcp.tool()
def set_runtime_ability_input_id(component_path: str, ability_handle: str, input_id: int,
                                 confirm: bool = False, dry_run: bool = False, pie_instance: int = -1) -> str:
    """Rebind granted native ability InputID with replication dirty marking.

    -1 unbinds; 0..65535 bind. Requires authoritative PIE and confirmation for changes;
    pressed input must first be released. Multiple specs may share IDs. Does not
    create Enhanced Input mappings or dispatch input events.
    """
    return httpx.patch(f"{app.BASE_URL}/ability-system/runtime/abilities/input-id", json={
        "ComponentPath": component_path, "AbilityHandle": ability_handle, "InputID": input_id,
        "bConfirm": confirm, "bDryRun": dry_run, "PIEInstance": pie_instance
    }, timeout=180).text


@mcp.tool()
def set_runtime_ability_source_tags(component_path: str, ability_handle: str, tags: list[str],
                                    confirm: bool = False, dry_run: bool = False, pie_instance: int = -1) -> str:
    """Replace inactive granted ability's dynamic spec source tags (empty clears).

    Requires registered tags, authoritative selected PIE and confirmation for changes.
    Active grants reject changes; native spec dirty marking handles replication.
    Existing effect captures/specs are not rewritten. Dry-run validates only.
    """
    return httpx.patch(f"{app.BASE_URL}/ability-system/runtime/abilities/source-tags", json={
        "ComponentPath": component_path, "AbilityHandle": ability_handle, "DynamicSourceTags": tags,
        "bConfirm": confirm, "bDryRun": dry_run, "PIEInstance": pie_instance
    }, timeout=180).text


@mcp.tool()
def create_gameplay_blueprint(asset_path: str, kind: str = "ability", parent_class_path: str = "",
                               dry_run: bool = False, save: bool = False) -> str:
    """Create native-parent or Blueprint-parent GAS Blueprint in unused /Game package.

    kind: ability, effect, execution, magnitude, cue_actor or cue_static.

    Uses specialized ability Blueprint class where appropriate and native compilation.
    Parent defaults to native family base; custom parent uses native or registered Blueprint _C path.
    Parent must be compatible/non-final/Blueprintable; Blueprint parent must be current and compiled.
    Parent loads for validation, including dry-run; its graph is not compiled by this operation.
    Requires stopped PIE. Dry-run validates destination/parent only. Compile/save
    failure may leave created unsaved asset for inspection; existing assets never overwrite.
    """
    return httpx.post(f"{app.BASE_URL}/ability-system/blueprints", json={
        "AssetPath": asset_path, "Kind": kind, "ClassPath": parent_class_path,
        "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def edit_gameplay_blueprint_defaults(asset_path: str, properties: dict,
                                      confirm: bool = False, dry_run: bool = False, save: bool = False, class_references: dict | None = None, tag_properties: dict | None = None,
                                      triggers: list[dict] | None = None, modifiers: list[dict] | None = None,
                                      timing: dict | None = None, executions: list[dict] | None = None, cues: list[dict] | None = None, stacking: dict | None = None, effect_components: list[dict] | None = None, captures: list[dict] | None = None, object_references: dict | None = None, soft_object_references: dict | None = None, soft_class_references: dict | None = None, reset_properties: list[str] | None = None) -> str:
    """Edit scalar/plain-struct GAS ability/effect/calculation/cue Blueprint defaults with native compile.

    reset_properties restores inherited scalar/plain/reference fields from parent defaults.
    soft_class_references accepts native class paths or current compiled Blueprint _C paths.
    soft_object_references stores soft asset paths; assets load for native type validation.
    object_references maps editable non-instanced hard asset fields to registered paths or None.
    captures replaces calculation capture rows: AttributePath, Source (Source/Target), bSnapshot.
    Validates imports on temporary duplicate before transaction; requires current
    compiled /Game Blueprint, stopped PIE and confirmation for changes. Dry-run
    imports and native object validation without compilation. Native validation
    diagnostics are returned; NotValidated is not a validation success. Compile failure may leave edits available to
    undo. References/containers/typed GAS structures require dedicated adapters.
    """
    return httpx.patch(f"{app.BASE_URL}/ability-system/blueprints/defaults", json={
        "ObjectReferences": object_references or {},
        "SoftObjectReferences": soft_object_references or {},
        "SoftClassReferences": soft_class_references or {},
        "ResetProperties": reset_properties or [],
        "bSetCaptures": captures is not None, "Captures": captures or [],
        "AssetPath": asset_path, "Properties": properties, "ClassReferences": class_references or {}, "TagProperties": tag_properties or {}, "bSetTriggers": triggers is not None, "Triggers": triggers or [], "bSetEffectComponents": effect_components is not None, "EffectComponents": effect_components or [],
        "Stacking": stacking or {}, "bSetCues": cues is not None, "Cues": cues or [],
        "bSetExecutions": executions is not None, "Executions": executions or [],
        "bSetTiming": timing is not None, "DurationPolicy": (timing or {}).get("DurationPolicy", "Instant"),
        "DurationCurveTable": (timing or {}).get("DurationCurveTable", ""),
        "DurationCurveRow": (timing or {}).get("DurationCurveRow", ""),
        "PeriodCurveTable": (timing or {}).get("PeriodCurveTable", ""),
        "PeriodCurveRow": (timing or {}).get("PeriodCurveRow", ""),
        "Duration": (timing or {}).get("Duration", 1), "Period": (timing or {}).get("Period", 0),
        "bSetModifiers": modifiers is not None, "Modifiers": modifiers or [], "bConfirm": confirm,
        "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def activate_runtime_abilities_by_tags(component_path: str, tags: list[str],
                                       confirm: bool = False, dry_run: bool = False,
                                       pie_instance: int = -1) -> str:
    """Try native tag-filtered ability activation on authoritative initialized PIE ASC.

    Requires confirmation and 1..64 registered tags. Multiple abilities can activate.
    Remote activation is disabled; native acceptance does not prove completion.
    Dry-run validates inputs only, without activation checks or execution.
    """
    return httpx.post(f"{app.BASE_URL}/ability-system/runtime/activate-by-tags", json={
        "ComponentPath": component_path, "Tags": tags, "bConfirm": confirm,
        "bDryRun": dry_run, "PIEInstance": pie_instance
    }, timeout=180).text


@mcp.tool()
def cancel_runtime_abilities_by_tags(component_path: str, tags: list[str],
                                     excluded_tags: list[str] | None = None,
                                     confirm: bool = False, dry_run: bool = False,
                                     pie_instance: int = -1) -> str:
    """Request native tag-filtered cancellation on authoritative initialized PIE ASC.

    Requires confirmation, 1..64 registered filter tags and <=64 excluded tags.
    Uncancelable abilities may remain. Reports aggregate active grant counts;
    callbacks can activate others. Dry-run validates inputs only.
    """
    return httpx.post(f"{app.BASE_URL}/ability-system/runtime/cancel-by-tags", json={
        "ComponentPath": component_path, "Tags": tags, "ExcludedTags": excluded_tags or [],
        "bConfirm": confirm, "bDryRun": dry_run, "PIEInstance": pie_instance
    }, timeout=180).text


@mcp.tool()
def match_runtime_abilities_by_tags(component_path: str, tags: list[str],
                                    pie_instance: int = -1) -> str:
    """Read native all-tag-matching PIE ability grants without activation checks.

    Returns <=256 grants, handles, asset/source tags and active state. Does not
    predict activation, cooldown/cost success or cancellation filter semantics.
    Requires 1..64 registered tags and registered selected PIE component.
    """
    return httpx.post(f"{app.BASE_URL}/ability-system/runtime/match-abilities", json={
        "ComponentPath": component_path, "Tags": tags, "PIEInstance": pie_instance
    }, timeout=180).text


@mcp.tool()
def query_runtime_gameplay_effects(component_path: str, tags: list[str],
                                   query: str = "effect_all", pie_instance: int = -1,
                                   compound_queries: list[dict] | None = None,
                                   effect_class_path: str = "", attribute_path: str = "",
                                   source_object_path: str = "", ignored_handles: list[str] | None = None) -> str:
    """Query native active effect tags in selected PIE without mutation.

    query is owning_any/all/no, effect_any/all/no or source_any/all/no.
    Supply 1..64 registered tags or compound_queries (<=4). Compound rows contain
    PropertyName (owning/effect/source/source_aggregate), QueryNodes and RootIndex.
    Families combine with AND and cannot be repeated. Optional loaded effect class
    and modified attribute field paths also combine with AND; at least one filter
    is required (tags may be empty). Optional source_object_path is a loaded selected-PIE
    runtime source object. ignored_handles accepts <=256 unique current component handles.
    Returns <=256 handles with timing, tags, context, evaluated modifiers and cached
    modified-attribute totals. These totals are spec application history, not current
    attribute deltas or a prediction. Nonfinite numbers serialize as null.
    Source filtering uses native EffectSource semantics. Infinite duration uses native sentinels.
    Native owning/effect/captured source-spec tag semantics apply; handles can expire.
    """
    return httpx.post(f"{app.BASE_URL}/ability-system/runtime/query-effects", json={
        "ComponentPath": component_path, "Tags": tags, "Operation": query,
        "RuntimeQueries": compound_queries or [],
        "EffectClassPath": effect_class_path, "AttributePath": attribute_path,
        "SourceObjectPath": source_object_path, "IgnoredEffectHandles": ignored_handles or [],
        "PIEInstance": pie_instance
    }, timeout=180).text
