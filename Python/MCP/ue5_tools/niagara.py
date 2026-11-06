"""Niagara systems, emitters and scripts."""
import httpx

from . import app
from .app import merged_tool
from .app import mcp


@mcp.tool()
def inspect_niagara_system(asset_path: str) -> str:
    """Inspect persistent native Niagara system with up to 128 emitter handles.

    Reports emitter index/stable ID/name/enabled state, warmup settings, dirty state
    and up to 256 exposed user parameter names/types/sizes/object/interface flags.
    References may load; no compilation, simulation, rendering, readiness proof or mutation.
    """
    return httpx.get(f"{app.BASE_URL}/niagara/systems/definition", params={
        "asset_path": asset_path
    }, timeout=180).text


@mcp.tool()
def set_niagara_emitter_enabled(asset_path: str, emitter_index: int,
                                expected_emitter_id: str, enabled: bool,
                                confirm: bool = False, dry_run: bool = False,
                                save: bool = False) -> str:
    """Set native Niagara emitter enabled state guarded by current index/stable GUID.

    <=128 emitters, confirmed /Game/stopped PIE, transaction/native graph refresh and
    compile invalidation/readback/dry-run/no-op/save. Setter immediate recompile disabled;
    notifications may schedule derived work. No explicit compile/simulation/rendering.
    """
    return httpx.patch(f"{app.BASE_URL}/niagara/systems/emitters/enabled", json={
        "AssetPath": asset_path, "EmitterIndex": emitter_index, "EmitterId": expected_emitter_id,
        "bEnabled": enabled, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def rename_niagara_emitter(asset_path: str, emitter_index: int,
                            expected_emitter_id: str, new_name: str,
                            confirm: bool = False, dry_run: bool = False,
                            save: bool = False) -> str:
    """Rename native emitter handle with native-safe unique non-None name (<=128).

    Current index/GUID identity, <=128 emitters, confirmed /Game/stopped PIE,
    transaction/native namespace propagation/readback/dry-run/no-op/save. External
    name consumers unchanged; notifications may schedule derived work. No explicit
    compile/simulation/rendering.
    """
    return httpx.patch(f"{app.BASE_URL}/niagara/systems/emitters/name", json={
        "AssetPath": asset_path, "EmitterIndex": emitter_index, "EmitterId": expected_emitter_id,
        "NewName": new_name, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_niagara_system_warmup(asset_path: str, time: float = 0,
                              tick_delta: float = 1/15, confirm: bool = False,
                              dry_run: bool = False, save: bool = False) -> str:
    """Set native warmup time/delta; time rounds down to a whole tick multiple.

    Time 0..600 seconds, delta 1/240..1, <=100000 ticks. Confirmed /Game/stopped PIE,
    transaction/native setters/notification/resolved readback/dry-run/no-op/save.
    No simulation, explicit compile or rendering; appearance/runtime cost unverified.
    """
    return httpx.patch(f"{app.BASE_URL}/niagara/systems/warmup", json={
        "AssetPath": asset_path, "WarmupTime": time, "WarmupDelta": tick_delta,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


def set_niagara_user_scalar(asset_path: str, parameter_name: str, kind: str, value: float,
                             confirm: bool = False, dry_run: bool = False,
                             save: bool = False) -> str:
    """Set existing exact-type User. scalar default: float, int or bool (0/1).

    Finite +/-1e9, integral int, <=1024 store parameters, confirmed /Game/stopped PIE,
    transaction/native store setter/readback/dry-run/no-op/save. No creation or live
    component override; no explicit compile/simulation/rendering.
    """
    return httpx.patch(f"{app.BASE_URL}/niagara/systems/user-parameters/scalar", json={
        "AssetPath": asset_path, "ParameterName": parameter_name,
        "ValueKind": kind, "ScalarValue": value,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


def set_niagara_user_vector(asset_path: str, parameter_name: str,
                             x: float, y: float, z: float,
                             confirm: bool = False, dry_run: bool = False,
                             save: bool = False) -> str:
    """Set existing exact native vector3 User. default using float-vector storage.

    Finite +/-1e9 components, <=1024 parameters, confirmed /Game/stopped PIE,
    transaction/native store setter/float readback/dry-run/no-op/save. Excludes LWC
    position type and live component overrides; no compile/simulation/rendering.
    """
    return httpx.patch(f"{app.BASE_URL}/niagara/systems/user-parameters/vector", json={
        "AssetPath": asset_path, "ParameterName": parameter_name,
        "VectorValue": {"x": x, "y": y, "z": z},
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


def set_niagara_user_color(asset_path: str, parameter_name: str,
                            r: float, g: float, b: float, a: float = 1,
                            confirm: bool = False, dry_run: bool = False,
                            save: bool = False) -> str:
    """Set existing exact native linear-color User. default (finite RGBA +/-1e6).

    No color-space conversion; HDR values allowed. <=1024 store parameters, confirmed
    /Game/stopped PIE, transaction/native setter/readback/dry-run/no-op/save.
    No parameter creation/live component override/compile/simulation/rendering.
    """
    return httpx.patch(f"{app.BASE_URL}/niagara/systems/user-parameters/color", json={
        "AssetPath": asset_path, "ParameterName": parameter_name,
        "ColorValue": {"r": r, "g": g, "b": b, "a": a},
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def duplicate_niagara_system(asset_path: str, source_asset_path: str,
                              confirm: bool = False, dry_run: bool = False,
                              save: bool = False) -> str:
    """Duplicate persistent native Niagara system via AssetTools to new /Game destination.

    Matching package/object names, registry/disk/loaded collision rejection, confirmed
    stopped PIE, transaction/identity+class readback/dry-run/save. Embedded emitters
    follow native duplication; external references shared. No explicit compile,
    simulation/rendering or runtime readiness proof.
    """
    return httpx.post(f"{app.BASE_URL}/niagara/systems/duplicate", json={
        "AssetPath": asset_path, "SourceAssetPath": source_asset_path,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def create_niagara_system(asset_path: str, confirm: bool = False,
                           dry_run: bool = False, save: bool = False) -> str:
    """Create native empty Niagara system via editor factory without interactive picker.

    New matching /Game package/object, collision rejection, confirmed stopped PIE,
    transaction/identity+class readback/dry-run/save. Factory initializes default graphs,
    assigns project default effect type and natively requests compilation. No compile
    wait/simulation/rendering or runtime readiness proof.
    """
    return httpx.post(f"{app.BASE_URL}/niagara/systems", json={
        "AssetPath": asset_path, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def request_niagara_system_compile(asset_path: str, force: bool = False,
                                    confirm: bool = False, dry_run: bool = False) -> str:
    """Request native asynchronous Niagara compilation, optionally forced.

    Confirmed registered persistent uncooked /Game system/stopped PIE. Reports native
    request return/pending/readiness snapshot; return is not compilation success.
    Poll system inspection for pending/script statuses. No completion wait, asset save,
    simulation/rendering or quality proof.
    """
    return httpx.post(f"{app.BASE_URL}/niagara/systems/compile-request", json={
        "AssetPath": asset_path, "bForce": force, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_niagara_renderer_enabled(asset_path: str, emitter_index: int,
                                 expected_emitter_id: str, renderer_index: int,
                                 expected_renderer_path: str, enabled: bool,
                                 confirm: bool = False, dry_run: bool = False,
                                 save: bool = False) -> str:
    """Set owned stateful emitter renderer enabled state with GUID/object guards.

    <=128 emitters/64 renderers, confirmed /Game/stopped PIE, system/emitter/renderer
    transaction/native notifications/readback/dry-run/no-op/save. Stateless and external
    renderer ownership rejected. No explicit compile/simulation/rendering.
    """
    return httpx.patch(f"{app.BASE_URL}/niagara/systems/renderers/enabled", json={
        "AssetPath": asset_path, "EmitterIndex": emitter_index, "EmitterId": expected_emitter_id,
        "RendererIndex": renderer_index, "RendererPath": expected_renderer_path,
        "bEnabled": enabled, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def inspect_niagara_renderer(asset_path: str, emitter_index: int,
                              expected_emitter_id: str, renderer_index: int,
                              expected_renderer_path: str, field: str = "") -> str:
    """Inspect up to 128 editable fields of owned stateful emitter renderer.

    Current emitter index/GUID and renderer index/path guards. Native type/value,
    edit-const/clamp/edit-condition metadata, bounded 4096 chars/value/truncation.
    Exporter intermediate allocation uncapped; no mutation/compile/simulation/rendering.
    """
    return httpx.post(f"{app.BASE_URL}/niagara/systems/renderers/inspect", json={
        "AssetPath": asset_path, "EmitterIndex": emitter_index, "EmitterId": expected_emitter_id,
        "RendererIndex": renderer_index, "RendererPath": expected_renderer_path, "FieldName": field
    }, timeout=180).text


def set_niagara_renderer_scalar(asset_path: str, emitter_index: int,
                                expected_emitter_id: str, renderer_index: int,
                                expected_renderer_path: str, field: str, value: float,
                                confirm: bool = False, dry_run: bool = False,
                                save: bool = False) -> str:
    """Set owned renderer direct editable bool/non-enum numeric field.

    Finite +/-1e9, native clamps/integer widths, bool 0/1; emitter GUID/renderer identity,
    confirmed /Game/stopped PIE, transaction/native notifications/readback/dry-run/save.
    Edit conditions/cross-field validity unverified; no compile/simulation/rendering.
    """
    # field accepts <=8 writable struct segments; array/object traversal is rejected.
    return httpx.patch(f"{app.BASE_URL}/niagara/systems/renderers/scalar", json={
        "AssetPath": asset_path, "EmitterIndex": emitter_index, "EmitterId": expected_emitter_id,
        "RendererIndex": renderer_index, "RendererPath": expected_renderer_path,
        "FieldName": field, "ScalarValue": value,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


def set_niagara_renderer_enum(asset_path: str, emitter_index: int,
                              expected_emitter_id: str, renderer_index: int,
                              expected_renderer_path: str, field: str, value: str,
                              confirm: bool = False, dry_run: bool = False,
                              save: bool = False) -> str:
    """Set owned renderer editable native enum by short or qualified name.

    Hidden/_MAX values rejected; inspect renderer for choices. Identity/ownership,
    confirmed /Game/stopped PIE, transaction/native notification/readback/dry-run/save.
    Edit conditions/cross-field validity unverified; no compile/simulation/rendering.
    """
    # field accepts <=8 writable struct segments; array/object traversal is rejected.
    return httpx.patch(f"{app.BASE_URL}/niagara/systems/renderers/enum", json={
        "AssetPath": asset_path, "EmitterIndex": emitter_index, "EmitterId": expected_emitter_id,
        "RendererIndex": renderer_index, "RendererPath": expected_renderer_path,
        "FieldName": field, "NewName": value,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_niagara_renderer_asset(asset_path: str, emitter_index: int,
                               expected_emitter_id: str, renderer_index: int,
                               expected_renderer_path: str, field: str, referenced_asset: str = "",
                               confirm: bool = False, dry_run: bool = False,
                               save: bool = False) -> str:
    """Set owned renderer direct hard asset reference; empty clears unless native NoClear.

    Registered persistent native-class match, no instanced/class/soft references.
    Identity/ownership, confirmed /Game/stopped PIE, transaction/notifications/readback/
    dry-run/save. Referenced asset unchanged; material/render compatibility unverified.
    """
    # field accepts <=8 writable struct segments; array/object traversal is rejected.
    return httpx.patch(f"{app.BASE_URL}/niagara/systems/renderers/asset", json={
        "AssetPath": asset_path, "EmitterIndex": emitter_index, "EmitterId": expected_emitter_id,
        "RendererIndex": renderer_index, "RendererPath": expected_renderer_path,
        "FieldName": field, "SourceAssetPath": referenced_asset,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


def set_niagara_renderer_name(asset_path: str, emitter_index: int,
                              expected_emitter_id: str, renderer_index: int,
                              expected_renderer_path: str, field: str, value: str,
                              confirm: bool = False, dry_run: bool = False,
                              save: bool = False) -> str:
    """Set editable FName renderer leaf through <=8 writable struct segments.

    Empty means None; bounded single-line text. Identity/ownership, confirmed /Game/
    stopped PIE, transaction/native notifications/readback/dry-run/no-op/save.
    Does not establish Niagara variable binding/type validity; no compile/rendering.
    """
    return httpx.patch(f"{app.BASE_URL}/niagara/systems/renderers/name", json={
        "AssetPath": asset_path, "EmitterIndex": emitter_index, "EmitterId": expected_emitter_id,
        "RendererIndex": renderer_index, "RendererPath": expected_renderer_path,
        "FieldName": field, "NewName": value,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def reset_niagara_renderer_field(asset_path: str, emitter_index: int,
                                  expected_emitter_id: str, renderer_index: int,
                                  expected_renderer_path: str, field: str,
                                  confirm: bool = False, dry_run: bool = False,
                                  save: bool = False) -> str:
    """Reset editable renderer scalar/enum/name/vector/color leaf to native class default.

    Supports <=8 writable struct segments; excludes arrays/objects/arbitrary structs.
    Identity/ownership, confirmed /Game/stopped PIE, transaction/notifications/native
    default readback/dry-run/no-op/save. Defaults do not prove binding/type validity.
    No explicit compile/simulation/rendering.
    """
    return httpx.post(f"{app.BASE_URL}/niagara/systems/renderers/reset-field", json={
        "AssetPath": asset_path, "EmitterIndex": emitter_index, "EmitterId": expected_emitter_id,
        "RendererIndex": renderer_index, "RendererPath": expected_renderer_path,
        "FieldName": field, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


def set_niagara_renderer_vector(asset_path: str, emitter_index: int,
                                expected_emitter_id: str, renderer_index: int,
                                expected_renderer_path: str, field: str,
                                x: float, y: float, z: float,
                                confirm: bool = False, dry_run: bool = False,
                                save: bool = False) -> str:
    """Set native FVector renderer leaf through <=8 writable editable struct segments.

    Finite components +/-1e9; identity/ownership, confirmed /Game/stopped PIE,
    transaction/native notifications/readback/dry-run/no-op/save. Other vector struct
    types excluded; binding/cross-field validity unverified. No compile/rendering.
    """
    return httpx.patch(f"{app.BASE_URL}/niagara/systems/renderers/vector", json={
        "AssetPath": asset_path, "EmitterIndex": emitter_index, "EmitterId": expected_emitter_id,
        "RendererIndex": renderer_index, "RendererPath": expected_renderer_path,
        "FieldName": field, "VectorValue": {"x": x, "y": y, "z": z},
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def list_niagara_renderer_types(search: str = "") -> str:
    """Discover up to 128 loaded concrete native renderer classes and editable fields.

    Optional class-path search <=128 characters; native names/types/protection flags.
    Does not prove simulation-target/material/binding compatibility. No creation,
    compilation, simulation or rendering.
    """
    return httpx.get(f"{app.BASE_URL}/niagara/renderer-types", params={"search": search}, timeout=180).text


@mcp.tool()
def add_niagara_renderer(asset_path: str, emitter_index: int, expected_emitter_id: str,
                          renderer_class: str, confirm: bool = False,
                          dry_run: bool = False, save: bool = False) -> str:
    """Append concrete native renderer to owned stateful emitter with target-support check.

    Capacity 64, current emitter index/GUID, confirmed /Game/stopped PIE, transaction/
    native AddRenderer/version bindings/readback/dry-run/save. Native update context
    may reinitialize live instances. Defaults may need material/attribute setup;
    no explicit compile/simulation/rendering or visual readiness proof.
    """
    return httpx.post(f"{app.BASE_URL}/niagara/systems/renderers", json={
        "AssetPath": asset_path, "EmitterIndex": emitter_index, "EmitterId": expected_emitter_id,
        "RendererClass": renderer_class, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def remove_niagara_renderer(asset_path: str, emitter_index: int,
                             expected_emitter_id: str, renderer_index: int,
                             expected_renderer_path: str, confirm: bool = False,
                             dry_run: bool = False, save: bool = False) -> str:
    """Remove owned stateful emitter renderer via native versioned API.

    Emitter GUID/renderer identity, unique pointer occurrence, confirmed /Game/stopped
    PIE, transaction/delegate+binding rebuild/full remaining-order readback/dry-run/save.
    UObject retained for undo; native live-instance reinitialization possible. Reinspect
    shifted indices. No explicit compile/simulation/rendering.
    """
    return httpx.request("DELETE", f"{app.BASE_URL}/niagara/systems/renderers", json={
        "AssetPath": asset_path, "EmitterIndex": emitter_index, "EmitterId": expected_emitter_id,
        "RendererIndex": renderer_index, "RendererPath": expected_renderer_path,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def move_niagara_renderer(asset_path: str, emitter_index: int,
                           expected_emitter_id: str, renderer_index: int,
                           expected_renderer_path: str, final_index: int,
                           confirm: bool = False, dry_run: bool = False,
                           save: bool = False) -> str:
    """Move owned stateful renderer to final_index via native versioned API.

    Emitter GUID/renderer identity, unique occurrence, bounded final index, confirmed
    /Game/stopped PIE, transaction/native binding rebuild/full order readback/dry-run/
    no-op/save. Native live-instance reinitialization possible; no compile/rendering.
    """
    return httpx.patch(f"{app.BASE_URL}/niagara/systems/renderers/order", json={
        "AssetPath": asset_path, "EmitterIndex": emitter_index, "EmitterId": expected_emitter_id,
        "RendererIndex": renderer_index, "RendererPath": expected_renderer_path,
        "TargetIndex": final_index, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def duplicate_niagara_renderer(asset_path: str, emitter_index: int,
                                expected_emitter_id: str, renderer_index: int,
                                expected_renderer_path: str, confirm: bool = False,
                                dry_run: bool = False, save: bool = False) -> str:
    """Append native renderer duplicate through versioned AddRenderer API.

    Capacity 64, owned stateful emitter/GUID and renderer identity, confirmed /Game/
    stopped PIE, transaction/binding rebuild/full order readback/dry-run/save.
    External references shared; native instanced-property duplication retained.
    Live-instance reinitialization possible; no explicit compile/simulation/rendering.
    """
    return httpx.post(f"{app.BASE_URL}/niagara/systems/renderers/duplicate", json={
        "AssetPath": asset_path, "EmitterIndex": emitter_index, "EmitterId": expected_emitter_id,
        "RendererIndex": renderer_index, "RendererPath": expected_renderer_path,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


def set_niagara_renderer_color(asset_path: str, emitter_index: int,
                               expected_emitter_id: str, renderer_index: int,
                               expected_renderer_path: str, field: str,
                               r: float, g: float, b: float, a: float = 1,
                               confirm: bool = False, dry_run: bool = False,
                               save: bool = False) -> str:
    """Set native linear-color renderer leaf through <=8 writable struct segments.

    Finite RGBA +/-1e6; no color-space conversion. Identity/ownership, confirmed
    /Game/stopped PIE, transaction/native notifications/readback/dry-run/no-op/save.
    Binding/cross-field validity unverified; no explicit compile/simulation/rendering.
    """
    return httpx.patch(f"{app.BASE_URL}/niagara/systems/renderers/color", json={
        "AssetPath": asset_path, "EmitterIndex": emitter_index, "EmitterId": expected_emitter_id,
        "RendererIndex": renderer_index, "RendererPath": expected_renderer_path,
        "FieldName": field, "ColorValue": {"r": r, "g": g, "b": b, "a": a},
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def remove_niagara_emitter(asset_path: str, emitter_index: int, expected_emitter_id: str,
                            confirm: bool = False, dry_run: bool = False,
                            save: bool = False) -> str:
    """Remove native emitter handle with system parameter cleanup/cache invalidation.

    Current index/unique GUID, <=128 emitters, confirmed /Game/stopped PIE,
    transaction/notification/full remaining GUID order readback/dry-run/save.
    External assets/consumers unchanged; reinspect shifted indices. No explicit
    compile/simulation/rendering.
    """
    return httpx.request("DELETE", f"{app.BASE_URL}/niagara/systems/emitters", json={
        "AssetPath": asset_path, "EmitterIndex": emitter_index, "EmitterId": expected_emitter_id,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def duplicate_niagara_emitter(asset_path: str, emitter_index: int,
                               expected_emitter_id: str, new_name: str,
                               confirm: bool = False, dry_run: bool = False,
                               save: bool = False) -> str:
    """Append native stateful/stateless emitter copy with new handle GUID.

    Unique native-safe name, capacity 128, current source index/GUID, confirmed /Game/
    stopped PIE, transaction/system parameter refresh/readback/dry-run/save. External
    asset references shared; no explicit compile/simulation/rendering.
    """
    return httpx.post(f"{app.BASE_URL}/niagara/systems/emitters/duplicate", json={
        "AssetPath": asset_path, "EmitterIndex": emitter_index, "EmitterId": expected_emitter_id,
        "NewName": new_name, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_niagara_system_effect_type(asset_path: str, effect_type_path: str = "",
                                   confirm: bool = False, dry_run: bool = False,
                                   save: bool = False) -> str:
    """Assign registered native effect type; empty clears. Shared policy unchanged.

    Confirmed /Game/stopped PIE, transaction/native scalability resolution/readback/
    dry-run/no-op/save. Native update context may reinitialize live instances;
    no explicit compile/simulation/rendering or scalability behavior proof.
    """
    return httpx.patch(f"{app.BASE_URL}/niagara/systems/effect-type", json={
        "AssetPath": asset_path, "SourceAssetPath": effect_type_path,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_niagara_system_fixed_bounds(asset_path: str, minimum: dict, maximum: dict,
                                     enabled: bool = True, confirm: bool = False,
                                     dry_run: bool = False, save: bool = False) -> str:
    """Set authored fixed bounds corners ({x,y,z}) and enable flag.

    Finite ordered coordinates within +/-1e9; disabled retains supplied box. Confirmed
    /Game/stopped PIE, transaction/native setter/property event/readback/dry-run/save.
    Does not prove particle coverage/culling; no compile/simulation/rendering.
    """
    return httpx.patch(f"{app.BASE_URL}/niagara/systems/fixed-bounds", json={
        "AssetPath": asset_path, "BoundsMin": minimum, "BoundsMax": maximum,
        "bEnabled": enabled, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def add_niagara_emitter(asset_path: str, emitter_path: str, version_id: str = "",
                         confirm: bool = False, dry_run: bool = False,
                         save: bool = False) -> str:
    """Insert a copied native emitter asset/version through Niagara editor utility.

    Empty version selects exposed version. Registered persistent assets, capacity 128,
    confirmed /Game/stopped PIE, transaction/native graph integration/GUID readback/
    dry-run/save. Utility may compile/reinitialize instances; source asset unchanged.
    No simulation/rendering or runtime readiness proof.
    """
    return httpx.post(f"{app.BASE_URL}/niagara/systems/emitters", json={
        "AssetPath": asset_path, "SourceAssetPath": emitter_path, "VersionId": version_id,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def inspect_niagara_emitter_asset(asset_path: str) -> str:
    """Inspect persistent emitter asset versions (<=128) and exposed version GUID.

    Reports major/minor, version-data availability, simulation target and renderer
    count. No insertion/compile/simulation/rendering/mutation or runtime validity proof.
    """
    return httpx.get(f"{app.BASE_URL}/niagara/emitters/definition", params={
        "asset_path": asset_path
    }, timeout=180).text


def add_niagara_user_scalar(asset_path: str, parameter_name: str, kind: str,
                             value: float = 0, confirm: bool = False,
                             dry_run: bool = False, save: bool = False) -> str:
    """Create new User. float/int/bool parameter and default; rejects name across all types.

    Capacity 1024, finite +/-1e9, integral int/bool 0..1, confirmed /Game/stopped PIE,
    transaction/native store registration+setter/readback/dry-run/save. Does not create
    graph bindings or live component overrides; no compile/simulation/rendering.
    """
    return httpx.post(f"{app.BASE_URL}/niagara/systems/user-parameters/scalar", json={
        "AssetPath": asset_path, "ParameterName": parameter_name,
        "ValueKind": kind, "ScalarValue": value,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


def add_niagara_user_vector(asset_path: str, parameter_name: str,
                             x: float, y: float, z: float,
                             confirm: bool = False, dry_run: bool = False,
                             save: bool = False) -> str:
    """Create new native vector3 User. default using float-vector storage.

    Finite +/-1e9 components, <=1024 parameters, confirmed /Game/stopped PIE,
    transaction/native store setter/float readback/dry-run/no-op/save. Rejects name collisions across all types; excludes LWC
    positions, graph binding creation and live overrides; no compile/simulation/rendering.
    """
    return httpx.post(f"{app.BASE_URL}/niagara/systems/user-parameters/vector", json={
        "AssetPath": asset_path, "ParameterName": parameter_name,
        "VectorValue": {"x": x, "y": y, "z": z},
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


def add_niagara_user_color(asset_path: str, parameter_name: str,
                            r: float, g: float, b: float, a: float = 1,
                            confirm: bool = False, dry_run: bool = False,
                            save: bool = False) -> str:
    """Create new native linear-color User. default (finite RGBA +/-1e6).

    No color-space conversion; HDR values allowed. <=1024 store parameters, confirmed
    /Game/stopped PIE, transaction/native setter/readback/dry-run/no-op/save.
    Rejects name collisions across all types; no graph binding creation/live override.
    """
    return httpx.post(f"{app.BASE_URL}/niagara/systems/user-parameters/color", json={
        "AssetPath": asset_path, "ParameterName": parameter_name,
        "ColorValue": {"r": r, "g": g, "b": b, "a": a},
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def remove_niagara_user_parameter(asset_path: str, parameter_name: str, kind: str,
                                   confirm: bool = False, dry_run: bool = False,
                                   save: bool = False) -> str:
    """Remove exact User. float/int/bool/vector/color parameter/default from exposed store.

    Graph references, component overrides and external consumers are not migrated;
    repair separately. Confirmed /Game/stopped PIE, bounded store, transaction/native
    removal/count+absence readback/dry-run/save. No explicit compile/simulation/rendering.
    """
    return httpx.request("DELETE", f"{app.BASE_URL}/niagara/systems/user-parameters", json={
        "AssetPath": asset_path, "ParameterName": parameter_name, "ValueKind": kind,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_niagara_system_determinism(asset_path: str, enabled: bool, random_seed: int = 0,
                                    confirm: bool = False, dry_run: bool = False,
                                    save: bool = False) -> str:
    """Set authored system determinism flag and int32 seed.

    Confirmed /Game/stopped PIE, transaction/native property notifications/readback/
    dry-run/no-op/save. Component seed offsets/emitter settings remain native;
    repeatable GPU/runtime output not proven. No compile/simulation/rendering.
    """
    return httpx.patch(f"{app.BASE_URL}/niagara/systems/determinism", json={
        "AssetPath": asset_path, "bEnabled": enabled, "RandomSeed": random_seed,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_niagara_system_fixed_tick(asset_path: str, enabled: bool,
                                   delta_seconds: float = 1/60, confirm: bool = False,
                                   dry_run: bool = False, save: bool = False) -> str:
    """Set native fixed simulation timestep flag and finite delta 1/240..1 seconds.

    Confirmed /Game/stopped PIE, transaction/both native property notifications/getter
    readback/dry-run/no-op/save. Runtime scheduling/substeps/performance unverified;
    no explicit compile/simulation/rendering.
    """
    return httpx.patch(f"{app.BASE_URL}/niagara/systems/fixed-tick", json={
        "AssetPath": asset_path, "bEnabled": enabled, "WarmupDelta": delta_seconds,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


def set_niagara_emitter_scalar(asset_path: str, emitter_index: int, emitter_id: str,
                               version_id: str, field: str, value: float,
                               confirm: bool = False, dry_run: bool = False,
                               save: bool = False) -> str:
    """Edit an owned emitter version scalar with current index/GUID/version guards.

    Fields: bLocalSpace, bDeterminism, bRequiresPersistentIDs (0/1), RandomSeed
    (int32), PreAllocationCount and MaxGPUParticlesSpawnPerFrame (nonnegative int32).
    Native versioned notifications, transaction/readback/dry-run/save; callbacks may
    compile/reinitialize. Allocation modes may override counts. Runtime unverified.
    """
    return httpx.patch(f"{app.BASE_URL}/niagara/systems/emitters/scalar", json={
        "AssetPath": asset_path, "EmitterIndex": emitter_index, "EmitterId": emitter_id,
        "VersionId": version_id, "FieldName": field, "ScalarValue": value,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


def set_niagara_emitter_enum(asset_path: str, emitter_index: int, emitter_id: str,
                             version_id: str, field: str, enum_name: str,
                             confirm: bool = False, dry_run: bool = False,
                             save: bool = False) -> str:
    """Set SimTarget, InterpolatedSpawnMode, CalculateBoundsMode or AllocationMode.

    Requires a declared visible short/qualified enum name, current handle/version
    identities and confirmed /Game/stopped PIE. Simulation target edits require
    support from all current renderers. Transaction/readback/dry-run/save; native
    callbacks may compile/reinitialize. Runtime compatibility remains unverified.
    """
    return httpx.patch(f"{app.BASE_URL}/niagara/systems/emitters/enum", json={
        "AssetPath": asset_path, "EmitterIndex": emitter_index, "EmitterId": emitter_id,
        "VersionId": version_id, "FieldName": field, "NewName": enum_name,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_niagara_emitter_fixed_bounds(asset_path: str, emitter_index: int, emitter_id: str,
                                      version_id: str, min_x: float, min_y: float,
                                      min_z: float, max_x: float, max_y: float, max_z: float,
                                      confirm: bool = False, dry_run: bool = False,
                                      save: bool = False) -> str:
    """Set an owned emitter version's authored fixed box with ordered finite corners.

    Coordinates bounded +/-1e9; exact handle/version identities required. Select
    CalculateBoundsMode Fixed separately via emitter enum editing. System bounds
    may override this box. Transaction/native notifications/readback/dry-run/save.
    Particle coverage/culling and runtime behavior remain unverified.
    """
    return httpx.patch(f"{app.BASE_URL}/niagara/systems/emitters/fixed-bounds", json={
        "AssetPath": asset_path, "EmitterIndex": emitter_index, "EmitterId": emitter_id,
        "VersionId": version_id, "BoundsMin": {"X": min_x, "Y": min_y, "Z": min_z},
        "BoundsMax": {"X": max_x, "Y": max_y, "Z": max_z},
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_niagara_simulation_stage_enabled(asset_path: str, emitter_index: int,
                                          emitter_id: str, version_id: str,
                                          stage_index: int, stage_path: str, enabled: bool,
                                          confirm: bool = False, dry_run: bool = False,
                                          save: bool = False) -> str:
    """Set an owned stage enabled flag using exact emitter/version/index/path guards.

    Requires valid stage script, confirmed /Game/stopped PIE. Native SetEnabled
    invalidates compilation and broadcasts changes; callbacks may compile/reinitialize.
    Transaction/readback/dry-run/save; enabled bindings/execution conditions remain.
    No compile wait or simulation/rendering.
    """
    return httpx.patch(f"{app.BASE_URL}/niagara/systems/simulation-stages/enabled", json={
        "AssetPath": asset_path, "EmitterIndex": emitter_index, "EmitterId": emitter_id,
        "VersionId": version_id, "StageIndex": stage_index, "StagePath": stage_path,
        "bEnabled": enabled, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def rename_niagara_simulation_stage(asset_path: str, emitter_index: int,
                                     emitter_id: str, version_id: str,
                                     stage_index: int, stage_path: str, new_name: str,
                                     confirm: bool = False, dry_run: bool = False,
                                     save: bool = False) -> str:
    """Rename an owned versioned stage with a unique native-safe name (1..128 chars).

    Exact handle/version/stage identities, confirmed /Game/stopped PIE, transaction,
    property notification/compile invalidation/readback/dry-run/save. External name
    consumers are not migrated. Native callbacks may compile/reinitialize.
    """
    return httpx.patch(f"{app.BASE_URL}/niagara/systems/simulation-stages/name", json={
        "AssetPath": asset_path, "EmitterIndex": emitter_index, "EmitterId": emitter_id,
        "VersionId": version_id, "StageIndex": stage_index, "StagePath": stage_path,
        "NewName": new_name, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def move_niagara_simulation_stage(asset_path: str, emitter_index: int,
                                   emitter_id: str, version_id: str,
                                   stage_index: int, stage_path: str, target_index: int,
                                   confirm: bool = False, dry_run: bool = False,
                                   save: bool = False) -> str:
    """Move an owned versioned stage to a final zero-based index in its current list.

    Exact handle/version/stage guards, confirmed /Game/stopped PIE; transaction,
    native order change/broadcast, full pointer-order readback, no-op/dry-run/save.
    Native callbacks may compile/reinitialize; runtime execution remains unverified.
    """
    return httpx.patch(f"{app.BASE_URL}/niagara/systems/simulation-stages/order", json={
        "AssetPath": asset_path, "EmitterIndex": emitter_index, "EmitterId": emitter_id,
        "VersionId": version_id, "StageIndex": stage_index, "StagePath": stage_path,
        "TargetIndex": target_index, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def remove_niagara_simulation_stage(asset_path: str, emitter_index: int,
                                     emitter_id: str, version_id: str,
                                     stage_index: int, stage_path: str,
                                     confirm: bool = False, dry_run: bool = False,
                                     save: bool = False) -> str:
    """Remove an owned versioned stage with exact emitter/version/index/path guards.

    Confirmed /Game/stopped PIE; transaction, native delegate cleanup/change
    broadcast, full remaining-order readback, dry-run/save. Objects retained for
    undo; graph nodes/external references are not migrated. Runtime unverified.
    """
    return httpx.request("DELETE", f"{app.BASE_URL}/niagara/systems/simulation-stages", json={
        "AssetPath": asset_path, "EmitterIndex": emitter_index, "EmitterId": emitter_id,
        "VersionId": version_id, "StageIndex": stage_index, "StagePath": stage_path,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


def set_niagara_simulation_stage_enum(asset_path: str, emitter_index: int,
                                       emitter_id: str, version_id: str,
                                       stage_index: int, stage_path: str, field: str,
                                       enum_name: str, confirm: bool = False,
                                       dry_run: bool = False, save: bool = False) -> str:
    """Set generic stage IterationSource, ExecuteBehavior, DirectDispatchType or
    DirectDispatchElementType to a declared enum name.

    Requires exact current emitter/version/stage identities and confirmed /Game,
    stopped PIE. Transaction/native property notification/readback/dry-run/save.
    Data-interface bindings and execution dependencies need separate configuration;
    native callbacks may compile/reinitialize. No simulation or compile wait.
    """
    return httpx.patch(f"{app.BASE_URL}/niagara/systems/simulation-stages/enum", json={
        "AssetPath": asset_path, "EmitterIndex": emitter_index, "EmitterId": emitter_id,
        "VersionId": version_id, "StageIndex": stage_index, "StagePath": stage_path,
        "FieldName": field, "NewName": enum_name, "bConfirm": confirm,
        "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


def set_niagara_simulation_stage_bool(asset_path: str, emitter_index: int,
                                       emitter_id: str, version_id: str,
                                       stage_index: int, stage_path: str, field: str,
                                       enabled: bool, confirm: bool = False,
                                       dry_run: bool = False, save: bool = False) -> str:
    """Set a generic simulation-stage boolean with exact identity/version guards.

    Fields: bDisablePartialParticleUpdate, bParticleIterationStateEnabled,
    bGpuDispatchForceLinear, bOverrideGpuDispatchNumThreads. Confirmed /Game/stopped
    PIE; transaction/native notification/readback/dry-run/save. Particle-state
    bindings/ranges and dispatch counts require separate configuration.
    """
    return httpx.patch(f"{app.BASE_URL}/niagara/systems/simulation-stages/bool", json={
        "AssetPath": asset_path, "EmitterIndex": emitter_index, "EmitterId": emitter_id,
        "VersionId": version_id, "StageIndex": stage_index, "StagePath": stage_path,
        "FieldName": field, "bEnabled": enabled, "bConfirm": confirm,
        "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_niagara_simulation_stage_state_range(asset_path: str, emitter_index: int,
                                              emitter_id: str, version_id: str,
                                              stage_index: int, stage_path: str,
                                              state_min: int, state_max: int,
                                              confirm: bool = False, dry_run: bool = False,
                                              save: bool = False) -> str:
    """Set ordered inclusive int32 particle-state bounds on a generic stage.

    Exact handle/version/stage identities, confirmed /Game/stopped PIE; transaction,
    native notification/readback/dry-run/save. Enable particle-state filtering and
    configure its attribute binding separately. Runtime filtering remains unverified.
    """
    return httpx.patch(f"{app.BASE_URL}/niagara/systems/simulation-stages/state-range", json={
        "AssetPath": asset_path, "EmitterIndex": emitter_index, "EmitterId": emitter_id,
        "VersionId": version_id, "StageIndex": stage_index, "StagePath": stage_path,
        "StateMin": state_min, "StateMax": state_max, "bConfirm": confirm,
        "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_niagara_simulation_stage_integer_default(asset_path: str, emitter_index: int,
                                                  emitter_id: str, version_id: str,
                                                  stage_index: int, stage_path: str,
                                                  field: str, value: int,
                                                  confirm: bool = False,
                                                  dry_run: bool = False, save: bool = False) -> str:
    """Set positive int32 default for NumIterations, ElementCountX/Y/Z or
    OverrideGpuDispatchNumThreadsX/Y/Z. Preserves existing parameter bindings,
    which can override defaults. Exact identities, confirmed /Game/stopped PIE,
    transaction/native notification/readback/dry-run/save. GPU limits unverified.
    """
    return httpx.patch(f"{app.BASE_URL}/niagara/systems/simulation-stages/integer-default", json={
        "AssetPath": asset_path, "EmitterIndex": emitter_index, "EmitterId": emitter_id,
        "VersionId": version_id, "StageIndex": stage_index, "StagePath": stage_path,
        "FieldName": field, "ScalarValue": value, "bConfirm": confirm,
        "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def reset_niagara_simulation_stage_binding(asset_path: str, emitter_index: int,
                                            emitter_id: str, version_id: str,
                                            stage_index: int, stage_path: str, field: str,
                                            confirm: bool = False, dry_run: bool = False,
                                            save: bool = False) -> str:
    """Reset an integer stage binding to its configured native parameter default.

    Supports NumIterations, ElementCountX/Y/Z, OverrideGpuDispatchNumThreadsX/Y/Z.
    Preserves current integer default bytes; a native default may name a parameter.
    Exact identities, confirmed /Game/stopped PIE, transaction/readback/dry-run/save.
    """
    return httpx.post(f"{app.BASE_URL}/niagara/systems/simulation-stages/reset-binding", json={
        "AssetPath": asset_path, "EmitterIndex": emitter_index, "EmitterId": emitter_id,
        "VersionId": version_id, "StageIndex": stage_index, "StagePath": stage_path,
        "FieldName": field, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def bind_niagara_simulation_stage_user_integer(asset_path: str, emitter_index: int,
                                                emitter_id: str, version_id: str,
                                                stage_index: int, stage_path: str,
                                                field: str, parameter_name: str,
                                                confirm: bool = False,
                                                dry_run: bool = False, save: bool = False) -> str:
    """Bind a stage integer setting to an existing exact int32 User parameter.

    Supports NumIterations, ElementCountX/Y/Z, OverrideGpuDispatchNumThreadsX/Y/Z.
    Requires binding allows User parameters; preserves stored default bytes.
    Exact identities, confirmed /Game/stopped PIE, transaction/readback/dry-run/save.
    Runtime resolution, positive counts and GPU limits remain unverified.
    """
    return httpx.patch(f"{app.BASE_URL}/niagara/systems/simulation-stages/user-integer-binding", json={
        "AssetPath": asset_path, "EmitterIndex": emitter_index, "EmitterId": emitter_id,
        "VersionId": version_id, "StageIndex": stage_index, "StagePath": stage_path,
        "FieldName": field, "ParameterName": parameter_name, "bConfirm": confirm,
        "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_niagara_event_handler_count(asset_path: str, emitter_index: int,
                                     emitter_id: str, version_id: str, event_index: int,
                                     script_path: str, field: str, value: int,
                                     confirm: bool = False, dry_run: bool = False,
                                     save: bool = False) -> str:
    """Set uint32 SpawnNumber, MinSpawnNumber or MaxEventsPerFrame.

    Random spawn min must not exceed max. Exact handle/version/event/script guards,
    confirmed /Game/stopped PIE, transaction/notification/readback/dry-run/save.
    Execution mode controls relevance; runtime event behavior remains unverified.
    """
    return httpx.patch(f"{app.BASE_URL}/niagara/systems/event-handlers/count", json={
        "AssetPath": asset_path, "EmitterIndex": emitter_index, "EmitterId": emitter_id,
        "VersionId": version_id, "EventIndex": event_index, "ScriptPath": script_path,
        "FieldName": field, "ScalarValue": value, "bConfirm": confirm,
        "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_niagara_event_handler_bool(asset_path: str, emitter_index: int,
                                    emitter_id: str, version_id: str, event_index: int,
                                    script_path: str, field: str, enabled: bool,
                                    confirm: bool = False, dry_run: bool = False,
                                    save: bool = False) -> str:
    """Set bRandomSpawnNumber or UpdateAttributeInitialValues on an event handler.

    Enabling random spawning requires ordered min/max counts. Exact emitter/version/
    event/script identities, confirmed /Game/stopped PIE, transaction/native
    notification/readback/dry-run/save. Execution mode controls relevance.
    """
    return httpx.patch(f"{app.BASE_URL}/niagara/systems/event-handlers/bool", json={
        "AssetPath": asset_path, "EmitterIndex": emitter_index, "EmitterId": emitter_id,
        "VersionId": version_id, "EventIndex": event_index, "ScriptPath": script_path,
        "FieldName": field, "bEnabled": enabled, "bConfirm": confirm,
        "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_niagara_event_handler_execution_mode(asset_path: str, emitter_index: int,
                                              emitter_id: str, version_id: str,
                                              event_index: int, script_path: str,
                                              mode: str, confirm: bool = False,
                                              dry_run: bool = False, save: bool = False) -> str:
    """Set visible native event mode EveryParticle or SpawnedParticles.

    Short/qualified names accepted; hidden modes rejected. Switching to spawned
    particles validates random spawn range. Exact identities, confirmed /Game/
    stopped PIE, transaction/notification/readback/dry-run/save. Payload unverified.
    """
    return httpx.patch(f"{app.BASE_URL}/niagara/systems/event-handlers/execution-mode", json={
        "AssetPath": asset_path, "EmitterIndex": emitter_index, "EmitterId": emitter_id,
        "VersionId": version_id, "EventIndex": event_index, "ScriptPath": script_path,
        "NewName": mode, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_niagara_event_handler_source(asset_path: str, emitter_index: int,
                                      emitter_id: str, version_id: str, event_index: int,
                                      script_path: str, event_name: str,
                                      source_emitter_id: str = "", confirm: bool = False,
                                      dry_run: bool = False, save: bool = False) -> str:
    """Set event source name and emitter GUID; empty/zero GUID means self.

    Nonzero source must exist in this system. Exact handler identities, confirmed
    /Game/stopped PIE, transaction/native notification/readback/dry-run/save.
    Event generation, payload compatibility and dependency cycles unverified.
    """
    return httpx.patch(f"{app.BASE_URL}/niagara/systems/event-handlers/source", json={
        "AssetPath": asset_path, "EmitterIndex": emitter_index, "EmitterId": emitter_id,
        "VersionId": version_id, "EventIndex": event_index, "ScriptPath": script_path,
        "SourceEmitterId": source_emitter_id, "NewName": event_name,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def remove_niagara_event_handler(asset_path: str, emitter_index: int,
                                   emitter_id: str, version_id: str, event_index: int,
                                   script_path: str, confirm: bool = False,
                                   dry_run: bool = False, save: bool = False) -> str:
    """Remove a handler by unique native script usage ID after exact identity guards.

    Requires all current handler scripts valid, confirmed /Game/stopped PIE.
    Transaction/native delegate cleanup/full remaining-order readback/dry-run/save.
    Script objects retained for undo; graph nodes/external references not migrated.
    """
    return httpx.request("DELETE", f"{app.BASE_URL}/niagara/systems/event-handlers", json={
        "AssetPath": asset_path, "EmitterIndex": emitter_index, "EmitterId": emitter_id,
        "VersionId": version_id, "EventIndex": event_index, "ScriptPath": script_path,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def inspect_niagara_script_asset(asset_path: str) -> str:
    """Inspect registered Niagara script/module asset identity, usage and versions.

    Reports up to 128 version GUIDs/major/minor/exposed flags and current script
    compile snapshot. Status is not per-version execution or module compatibility
    proof. No graph mutation, compile request/wait, simulation or rendering.
    """
    return httpx.post(f"{app.BASE_URL}/niagara/scripts/inspect", json={
        "AssetPath": asset_path
    }, timeout=180).text


@mcp.tool()
def duplicate_niagara_script_asset(source_asset_path: str, asset_path: str,
                                     confirm: bool = False, dry_run: bool = False,
                                     save: bool = False) -> str:
    """Duplicate a registered Niagara script/module asset via native AssetTools.

    Requires a new matching /Game package/object path and stopped PIE. Registry,
    disk and loaded-package collision checks; transaction/class/path readback,
    dry-run/save. Embedded graphs/versions follow native duplication rules;
    external references remain shared. No explicit compile/simulation/rendering.
    """
    return httpx.post(f"{app.BASE_URL}/niagara/scripts/duplicate", json={
        "SourceAssetPath": source_asset_path, "AssetPath": asset_path,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def duplicate_niagara_emitter_asset(source_asset_path: str, asset_path: str,
                                      confirm: bool = False, dry_run: bool = False,
                                      save: bool = False) -> str:
    """Duplicate a standalone registered emitter asset via native AssetTools.

    New matching /Game package/object path, stopped PIE, registry/disk/loaded-package
    collision checks; transaction/class/path readback/dry-run/save. Embedded graph/
    version data follow engine duplication rules; external references remain shared.
    No system insertion or explicit compile/simulation/rendering.
    """
    return httpx.post(f"{app.BASE_URL}/niagara/emitters/duplicate", json={
        "SourceAssetPath": source_asset_path, "AssetPath": asset_path,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def create_niagara_emitter_asset(asset_path: str, confirm: bool = False,
                                   dry_run: bool = False, save: bool = False) -> str:
    """Create a standalone emitter through native factory defaults (modules/renderers).

    New matching /Game package/object path, confirmed stopped PIE, registry/disk/
    loaded-package collision checks; native transaction/class/path readback,
    dry-run/save. Native factory initializes graph/editor data without a picker.
    No system insertion, compile wait or simulation/rendering.
    """
    return httpx.post(f"{app.BASE_URL}/niagara/emitters", json={
        "AssetPath": asset_path, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def create_niagara_script_asset(asset_path: str, kind: str = "module",
                                  confirm: bool = False, dry_run: bool = False,
                                  save: bool = False) -> str:
    """Create module, function or dynamic_input using its native Niagara factory.

    Uses configured default script or procedural graph fallback. Confirmed new
    matching /Game destination/stopped PIE, collision checks, transaction/class/
    path/usage readback, dry-run/save. No stack insertion or compile wait/simulation.
    """
    return httpx.post(f"{app.BASE_URL}/niagara/scripts", json={
        "AssetPath": asset_path, "ValueKind": kind, "bConfirm": confirm,
        "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


def set_niagara_script_text(asset_path: str, version_id: str, field: str, text: str,
                              confirm: bool = False, dry_run: bool = False,
                              save: bool = False) -> str:
    """Set versioned Category, Description, Keywords, NoteMessage or
    InlineOverviewDisplayName (up to 4096 chars). Plain text replaces localization
    identity on changed fields. Explicit version, confirmed /Game/stopped PIE,
    transaction/native notification/reacquired readback/no-op/dry-run/save.
    """
    return httpx.patch(f"{app.BASE_URL}/niagara/scripts/text", json={
        "AssetPath": asset_path, "VersionId": version_id, "FieldName": field,
        "TextValue": text, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


def set_niagara_script_bool(asset_path: str, version_id: str, field: str,
                              enabled: bool, confirm: bool = False,
                              dry_run: bool = False, save: bool = False) -> str:
    """Set versioned bSuggested, bDeprecated or bExperimental metadata.

    Explicit existing version, confirmed /Game/stopped PIE, typed bool transaction/
    native notification/reacquired readback/no-op/dry-run/save. Messages and
    replacement script configured separately; no graph mutation or compile wait.
    """
    return httpx.patch(f"{app.BASE_URL}/niagara/scripts/bool", json={
        "AssetPath": asset_path, "VersionId": version_id, "FieldName": field,
        "bEnabled": enabled, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


def set_niagara_script_enum(asset_path: str, version_id: str, field: str,
                              enum_name: str, confirm: bool = False,
                              dry_run: bool = False, save: bool = False) -> str:
    """Set LibraryVisibility or NumericOutputTypeSelectionMode for a script version.

    Declared visible short/qualified enum names; explicit existing version,
    confirmed /Game/stopped PIE, transaction/notification/readback/dry-run/save.
    Graph inference and existing stack compatibility remain unverified.
    """
    return httpx.patch(f"{app.BASE_URL}/niagara/scripts/enum", json={
        "AssetPath": asset_path, "VersionId": version_id, "FieldName": field,
        "NewName": enum_name, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_niagara_script_provided_dependencies(asset_path: str, version_id: str,
                                              dependency_ids: list[str],
                                              confirm: bool = False,
                                              dry_run: bool = False, save: bool = False) -> str:
    """Replace up to 128 unique non-None provided dependency IDs; empty clears.

    Names bounded to 128 characters. Explicit existing version, confirmed /Game/
    stopped PIE, transaction/versioned notification/readback/no-op/dry-run/save.
    Dependent modules and stack ordering are not migrated or validated.
    """
    return httpx.patch(f"{app.BASE_URL}/niagara/scripts/provided-dependencies", json={
        "AssetPath": asset_path, "VersionId": version_id, "DependencyIds": dependency_ids,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_niagara_module_usage_contexts(asset_path: str, version_id: str,
                                       usage_names: list[str], confirm: bool = False,
                                       dry_run: bool = False, save: bool = False) -> str:
    """Replace module usage mask from unique native execution-context enum names.

    Supports particle spawn/update/event/simulation-stage and emitter/system spawn/
    update; hidden usages rejected, empty clears. Explicit version, confirmed /Game/
    stopped PIE, transaction/notification/readback/dry-run/save. Graph compatibility
    and existing stack instances are not migrated or validated.
    """
    return httpx.patch(f"{app.BASE_URL}/niagara/scripts/usage-contexts", json={
        "AssetPath": asset_path, "VersionId": version_id, "UsageNames": usage_names,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_niagara_script_deprecation_replacement(asset_path: str, version_id: str,
                                                replacement_path: str = "",
                                                confirm: bool = False,
                                                dry_run: bool = False, save: bool = False) -> str:
    """Set a version's replacement script recommendation; empty clears.

    Replacement must be distinct, registered/persistent and have matching usage.
    Explicit version, confirmed /Game/stopped PIE, transaction/native notification/
    readback/dry-run/save. No conversion scripts run; pins/cycles unvalidated.
    """
    return httpx.patch(f"{app.BASE_URL}/niagara/scripts/deprecation-replacement", json={
        "AssetPath": asset_path, "VersionId": version_id,
        "SourceAssetPath": replacement_path, "bConfirm": confirm,
        "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_niagara_script_required_dependencies(asset_path: str, version_id: str,
                                               dependencies: list[dict],
                                               confirm: bool = False,
                                               dry_run: bool = False, save: bool = False) -> str:
    """Replace up to 128 required dependencies; empty clears.

    Records: Id, Order (PreDependency/PostDependency), Constraint (SameScript/
    AllScripts), RequiredVersion, UsageMask (0..15), Description. ID <=128, version
    <=256, description <=4096 chars. Explicit version/confirmed /Game/stopped PIE,
    transaction/native notification/full-list readback/dry-run/save. Version syntax,
    providers, cycles and stack ordering unvalidated; plain text descriptions.
    """
    return httpx.patch(f"{app.BASE_URL}/niagara/scripts/required-dependencies", json={
        "AssetPath": asset_path, "VersionId": version_id,
        "RequiredDependencies": dependencies, "bConfirm": confirm,
        "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def inspect_niagara_script_graph(asset_path: str, version_id: str) -> str:
    """Inspect an existing script version graph: node identities/classes/positions,
    pin identities/types/defaults and links. Bounded to 256 nodes, 64 pins/node,
    4096 total pins and 64 links/pin, with truncation flags. No mutation, evaluation,
    compile request/wait, simulation or rendering.
    """
    return httpx.post(f"{app.BASE_URL}/niagara/scripts/graph/inspect", json={
        "AssetPath": asset_path, "VersionId": version_id
    }, timeout=180).text


@mcp.tool()
def move_niagara_script_node(asset_path: str, version_id: str, node_id: str,
                               node_path: str, x: int, y: int, confirm: bool = False,
                               dry_run: bool = False, save: bool = False) -> str:
    """Set graph node layout coordinates within +/-1e6 using GUID/path guards.

    Existing version/owned graph <=256 nodes, confirmed /Game/stopped PIE,
    transaction/native graph notification/identity-position readback/dry-run/save.
    Versions sharing the graph share layout changes; callbacks may derive work.
    """
    return httpx.patch(f"{app.BASE_URL}/niagara/scripts/graph/node-position", json={
        "AssetPath": asset_path, "VersionId": version_id, "NodeId": node_id,
        "NodePath": node_path, "NodeX": x, "NodeY": y,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_niagara_script_node_comment(asset_path: str, version_id: str, node_id: str,
                                      node_path: str, text: str, confirm: bool = False,
                                      dry_run: bool = False, save: bool = False) -> str:
    """Set node comment up to 4096 characters; empty clears.

    Existing version/owned graph <=256 nodes, exact GUID/path, confirmed /Game/
    stopped PIE, transaction/native graph notification/readback/no-op/dry-run/save.
    Versions sharing the graph share comment changes.
    """
    return httpx.patch(f"{app.BASE_URL}/niagara/scripts/graph/node-comment", json={
        "AssetPath": asset_path, "VersionId": version_id, "NodeId": node_id,
        "NodePath": node_path, "TextValue": text,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_niagara_script_pin_scalar(asset_path: str, version_id: str, node_id: str,
                                    node_path: str, pin_id: str, value: float,
                                    confirm: bool = False, dry_run: bool = False,
                                    save: bool = False) -> str:
    """Set exact float/int32/bool unlinked writable input pin default via schema.

    Float bounded +/-1e9, int32 integral, bool 0/1. Exact version/node/pin identities,
    confirmed /Game/stopped PIE, transaction/native notification/reacquired readback/
    dry-run/save. Shared graphs share edits; semantic compatibility unverified.
    """
    return httpx.patch(f"{app.BASE_URL}/niagara/scripts/graph/pin-scalar", json={
        "AssetPath": asset_path, "VersionId": version_id, "NodeId": node_id,
        "NodePath": node_path, "PinId": pin_id, "ScalarValue": value,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def reset_niagara_script_pin_default(asset_path: str, version_id: str, node_id: str,
                                       node_path: str, pin_id: str, confirm: bool = False,
                                       dry_run: bool = False, save: bool = False) -> str:
    """Reset an unlinked writable scalar/vector3/color input to its autogenerated default.

    Exact version/node/pin identities, confirmed /Game/stopped PIE, native schema
    reset callback, transaction/reacquired readback/no-op/dry-run/save. Shared graphs
    share edits; generated default/graph semantic compatibility remains unverified.
    """
    return httpx.post(f"{app.BASE_URL}/niagara/scripts/graph/reset-pin-default", json={
        "AssetPath": asset_path, "VersionId": version_id, "NodeId": node_id,
        "NodePath": node_path, "PinId": pin_id, "bConfirm": confirm,
        "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def connect_niagara_script_pins(asset_path: str, version_id: str, node_id: str,
                                  node_path: str, pin_id: str, target_node_id: str,
                                  target_node_path: str, target_pin_id: str,
                                  confirm: bool = False, dry_run: bool = False,
                                  save: bool = False, replace_existing: bool = False) -> str:
    """Connect opposite pins via native schema, optionally replacing existing links.

    Exact version/node paths/GUIDs/pin IDs; confirmed /Game/stopped PIE, bounded graph,
    transaction/reacquired bidirectional readback/no-op/dry-run/save. Dry-run reports
    native compatibility response. Break-others responses require replace_existing=True; conversion unsupported.
    """
    return httpx.post(f"{app.BASE_URL}/niagara/scripts/graph/connect", json={
        "AssetPath": asset_path, "VersionId": version_id, "NodeId": node_id,
        "NodePath": node_path, "PinId": pin_id, "TargetNodeId": target_node_id,
        "TargetNodePath": target_node_path, "TargetPinId": target_pin_id,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save,
        "bForce": replace_existing
    }, timeout=180).text


@mcp.tool()
def disconnect_niagara_script_pins(asset_path: str, version_id: str, node_id: str,
                                     node_path: str, pin_id: str, target_node_id: str,
                                     target_node_path: str, target_pin_id: str,
                                     confirm: bool = False, dry_run: bool = False,
                                     save: bool = False) -> str:
    """Remove one symmetric pin link via native schema; missing link is a no-op.

    Exact version/endpoint node GUIDs-paths/pin IDs, bounded graph/pins/links,
    confirmed /Game/stopped PIE, transaction/native callbacks/reacquired absence
    readback/dry-run/save. Other links preserved by native operation.
    """
    return httpx.post(f"{app.BASE_URL}/niagara/scripts/graph/disconnect", json={
        "AssetPath": asset_path, "VersionId": version_id, "NodeId": node_id,
        "NodePath": node_path, "PinId": pin_id, "TargetNodeId": target_node_id,
        "TargetNodePath": target_node_path, "TargetPinId": target_pin_id,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def remove_niagara_script_node(asset_path: str, version_id: str, node_id: str,
                                 node_path: str, confirm: bool = False,
                                 dry_run: bool = False, save: bool = False) -> str:
    """Remove a native user-deletable graph node via DestroyNode, including its links.

    Exact version/GUID/path, owned bounded graph/pins/links, confirmed /Game/stopped
    PIE; transaction including neighbors, absence/link readback/dry-run/save.
    Shared graph versions share deletion; external consumers are not migrated.
    """
    return httpx.request("DELETE", f"{app.BASE_URL}/niagara/scripts/graph/nodes", json={
        "AssetPath": asset_path, "VersionId": version_id, "NodeId": node_id,
        "NodePath": node_path, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def add_niagara_script_reroute(asset_path: str, version_id: str, x: int = 0,
                                 y: int = 0, confirm: bool = False,
                                 dry_run: bool = False, save: bool = False) -> str:
    """Create an unconnected native Niagara reroute with initialized GUID/pins.

    Existing version/owned graph below 256 nodes, coordinates +/-1e6, confirmed
    /Game/stopped PIE, transaction/native creator/readback/dry-run/save. Wire
    separately via schema connections; shared graph versions share creation.
    """
    return httpx.post(f"{app.BASE_URL}/niagara/scripts/graph/reroutes", json={
        "AssetPath": asset_path, "VersionId": version_id, "NodeX": x, "NodeY": y,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def add_niagara_script_function_call(asset_path: str, version_id: str,
                                       source_asset_path: str, source_version_id: str,
                                       x: int = 0, y: int = 0, confirm: bool = False,
                                       dry_run: bool = False, save: bool = False) -> str:
    """Add an unconnected module/function/dynamic-input script call with explicit version.

    Distinct registered reference with bounded native graph; confirmed /Game/stopped
    PIE, transaction/native node creator/GUID-pins-reference readback/dry-run/save.
    Wire separately; bounded traversal rejects reference cycles (128 graphs/4096 nodes/
    depth 32). Unresolved references rejected; module context compatibility unvalidated.
    """
    return httpx.post(f"{app.BASE_URL}/niagara/scripts/graph/function-calls", json={
        "AssetPath": asset_path, "VersionId": version_id,
        "SourceAssetPath": source_asset_path, "SourceVersionId": source_version_id,
        "NodeX": x, "NodeY": y, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def list_niagara_script_operations(asset_path: str, version_id: str) -> str:
    """Discover up to 256 unique native operation names/classes/titles/tooltips
    from a script version's native graph actions. Uses transient template graph;
    action generation may load references and its work is not bounded. No persistent
    graph mutation, compile request/wait, simulation or rendering.
    """
    return httpx.post(f"{app.BASE_URL}/niagara/scripts/graph/operation-types", json={
        "AssetPath": asset_path, "VersionId": version_id
    }, timeout=180).text


@mcp.tool()
def add_niagara_script_operation(asset_path: str, version_id: str, operation_name: str,
                                   x: int = 0, y: int = 0, confirm: bool = False,
                                   dry_run: bool = False, save: bool = False) -> str:
    """Create an unconnected operation from a unique native graph context action.

    Discover names with list_niagara_script_operations. Existing version/owned graph
    below 256 nodes, coordinates +/-1e6, confirmed /Game/stopped PIE, transaction/
    native action/pins-identity readback/dry-run/save. Action generation work uncapped.
    """
    return httpx.post(f"{app.BASE_URL}/niagara/scripts/graph/operations", json={
        "AssetPath": asset_path, "VersionId": version_id, "NewName": operation_name,
        "NodeX": x, "NodeY": y, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def add_niagara_script_comment_box(asset_path: str, version_id: str, text: str,
                                     x: int = 0, y: int = 0, confirm: bool = False,
                                     dry_run: bool = False, save: bool = False) -> str:
    """Create native graph comment box with <=4096 characters at bounded coordinates.

    Explicit version/owned graph below 256 nodes, confirmed /Game/stopped PIE,
    transaction/native graph creator/GUID-text readback/dry-run/save. Uses native
    default box dimensions; shared graph versions share comment creation.
    """
    return httpx.post(f"{app.BASE_URL}/niagara/scripts/graph/comment-boxes", json={
        "AssetPath": asset_path, "VersionId": version_id, "TextValue": text,
        "NodeX": x, "NodeY": y, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def resize_niagara_script_comment_box(asset_path: str, version_id: str, node_id: str,
                                        node_path: str, width: int, height: int,
                                        confirm: bool = False, dry_run: bool = False,
                                        save: bool = False) -> str:
    """Resize a native comment box to integer dimensions 32..100000.

    Exact version/node GUID/path, owned bounded graph, confirmed /Game/stopped PIE,
    transaction/native graph notification/readback/no-op/dry-run/save. Shared graph
    versions share dimension changes; node inspection includes width/height.
    """
    return httpx.patch(f"{app.BASE_URL}/niagara/scripts/graph/comment-box-size", json={
        "AssetPath": asset_path, "VersionId": version_id, "NodeId": node_id,
        "NodePath": node_path, "NodeWidth": width, "NodeHeight": height,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def validate_niagara_script_graph(asset_path: str, version_id: str) -> str:
    """Report node/pin identity, ownership, orphan/link issues and same-name input
    type/exposure/priority/reference conflicts or value allocation mismatches.

    Budgets: 256 nodes, 64 pins/node, 4096 total pins, 64 links/pin, 16384 directed
    links; up to 256 issue records with total/truncation. No type inference,
    reference recursion, compilation or runtime validity proof. No mutation.
    """
    return httpx.post(f"{app.BASE_URL}/niagara/scripts/graph/validate", json={
        "AssetPath": asset_path, "VersionId": version_id
    }, timeout=180).text


@mcp.tool()
def duplicate_niagara_script_node(asset_path: str, version_id: str, node_id: str,
                                    node_path: str, x: int, y: int, confirm: bool = False,
                                    dry_run: bool = False, save: bool = False) -> str:
    """Duplicate native operation/reroute/comment via graph text export/import.

    Fresh node GUID/unlinked pins; exact source identities, bounded graph/position,
    confirmed /Game/stopped PIE, transaction/readback/dry-run/save. Export capped
    after allocation (1Mi chars); no clipboard. Script-call/parameter nodes excluded.
    """
    return httpx.post(f"{app.BASE_URL}/niagara/scripts/graph/duplicate-node", json={
        "AssetPath": asset_path, "VersionId": version_id, "NodeId": node_id,
        "NodePath": node_path, "NodeX": x, "NodeY": y,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def add_niagara_script_parameter_map(asset_path: str, version_id: str, kind: str,
                                       x: int = 0, y: int = 0, confirm: bool = False,
                                       dry_run: bool = False, save: bool = False) -> str:
    """Create empty native parameter-map get/set node with initialized base pins.

    kind=get or set. Explicit version/owned graph below 256 nodes, coordinates
    +/-1e6, confirmed /Game/stopped PIE, transaction/native creator/GUID-pin-count
    readback/dry-run/save. Parameter pins and wiring configured separately.
    """
    return httpx.post(f"{app.BASE_URL}/niagara/scripts/graph/parameter-maps", json={
        "AssetPath": asset_path, "VersionId": version_id, "ValueKind": kind,
        "NodeX": x, "NodeY": y, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def add_niagara_script_scalar_input(asset_path: str, version_id: str, name: str,
                                      kind: str, value: float = 0, x: int = 0, y: int = 0,
                                      confirm: bool = False, dry_run: bool = False,
                                      save: bool = False) -> str:
    """Create scalar parameter input node (float/int/bool), unique native-safe name.

    Float +/-1e9, int32 integral, bool 0/1. Explicit version/owned graph, bounded
    placement, confirmed /Game/stopped PIE, native creator/transaction/readback/
    dry-run/save. Caller exposure and graph metadata behavior remain unverified.
    """
    return httpx.post(f"{app.BASE_URL}/niagara/scripts/graph/scalar-inputs", json={
        "AssetPath": asset_path, "VersionId": version_id, "ParameterName": name,
        "ValueKind": kind, "ScalarValue": value, "NodeX": x, "NodeY": y,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_niagara_script_input_exposure(asset_path: str, version_id: str, node_id: str,
                                        node_path: str, field: str, enabled: bool,
                                        confirm: bool = False, dry_run: bool = False,
                                        save: bool = False) -> str:
    """Set parameter input bExposed, bRequired or bHidden (advanced caller display).

    Exact version/node GUID/path, owned graph, confirmed /Game/stopped PIE,
    transaction/native property+graph notifications/readback/no-op/dry-run/save.
    Native caller/context rules determine effective exposure; runtime unverified.
    """
    return httpx.patch(f"{app.BASE_URL}/niagara/scripts/graph/input-exposure", json={
        "AssetPath": asset_path, "VersionId": version_id, "NodeId": node_id,
        "NodePath": node_path, "FieldName": field, "bEnabled": enabled,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_niagara_script_input_priority(asset_path: str, version_id: str, node_id: str,
                                        node_path: str, priority: int,
                                        confirm: bool = False, dry_run: bool = False,
                                        save: bool = False) -> str:
    """Set native int32 CallSortPriority on a parameter input node.

    Exact version/node GUID/path, owned graph, confirmed /Game/stopped PIE,
    transaction/native property+graph notifications/readback/no-op/dry-run/save.
    Caller ordering/ties follow native rules; shared graph versions share edits.
    """
    return httpx.patch(f"{app.BASE_URL}/niagara/scripts/graph/input-priority", json={
        "AssetPath": asset_path, "VersionId": version_id, "NodeId": node_id,
        "NodePath": node_path, "ScalarValue": priority,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def add_niagara_script_compound_input(asset_path: str, version_id: str, name: str,
                                        kind: str, components: list[float],
                                        x: int = 0, y: int = 0, confirm: bool = False,
                                        dry_run: bool = False, save: bool = False) -> str:
    """Create vector (XYZ) or color (RGBA) parameter input with finite components.

    Vector components +/-1e9, color +/-1e6; native float vector/color storage.
    Unique native-safe name, explicit version, owned graph, confirmed /Game/stopped
    PIE, transaction/native creator/readback/dry-run/save. No color-space conversion.
    """
    if kind not in ("vector", "color") or len(components) != (3 if kind == "vector" else 4):
        raise ValueError("vector requires XYZ; color requires RGBA")
    payload = {"AssetPath": asset_path, "VersionId": version_id, "ParameterName": name,
               "ValueKind": kind, "NodeX": x, "NodeY": y,
               "bConfirm": confirm, "bDryRun": dry_run, "bSave": save}
    payload["VectorValue" if kind == "vector" else "ColorValue"] = dict(zip(
        ("X", "Y", "Z") if kind == "vector" else ("R", "G", "B", "A"), components))
    return httpx.post(f"{app.BASE_URL}/niagara/scripts/graph/compound-inputs",
                      json=payload, timeout=180).text


@mcp.tool()
def set_niagara_script_input_value(asset_path: str, version_id: str, node_id: str,
                                     node_path: str, scalar_value: float = 0,
                                     vector_value: list[float] | None = None,
                                     color_value: list[float] | None = None,
                                     confirm: bool = False, dry_run: bool = False,
                                     save: bool = False) -> str:
    """Set existing input's stored float/int32/bool/vector/color value; name/type preserved.

    Send scalar_value, XYZ vector_value or RGBA color_value matching native type.
    Exact identities, confirmed /Game/stopped PIE, transaction/native notification/
    full value readback/dry-run/save. Caller overrides/pin defaults remain native.
    """
    payload = {"AssetPath": asset_path, "VersionId": version_id, "NodeId": node_id,
               "NodePath": node_path, "ScalarValue": scalar_value,
               "bConfirm": confirm, "bDryRun": dry_run, "bSave": save}
    if vector_value is not None and color_value is not None:
        raise ValueError("send only one of vector_value or color_value")
    payload["ValueKind"] = "scalar"
    if vector_value is not None:
        if len(vector_value) != 3: raise ValueError("vector_value requires XYZ")
        payload["VectorValue"] = dict(zip(("X", "Y", "Z"), vector_value))
        payload["ValueKind"] = "vector"
    if color_value is not None:
        if len(color_value) != 4: raise ValueError("color_value requires RGBA")
        payload["ColorValue"] = dict(zip(("R", "G", "B", "A"), color_value))
        payload["ValueKind"] = "color"
    return httpx.patch(f"{app.BASE_URL}/niagara/scripts/graph/input-value",
                       json=payload, timeout=180).text


@mcp.tool()
def rename_niagara_script_input(asset_path: str, version_id: str, node_id: str,
                                  node_path: str, new_name: str, confirm: bool = False,
                                  dry_run: bool = False, save: bool = False) -> str:
    """Rename parameter input via native OnRenameNode with collision checks.

    Synchronizes same-name/same-usage input nodes and reallocates pins. Exact
    identities, confirmed /Game/stopped PIE, transaction/affected-input readback/
    no-op/dry-run/save. External callers not migrated; shared graphs share rename.
    """
    return httpx.patch(f"{app.BASE_URL}/niagara/scripts/graph/input-name", json={
        "AssetPath": asset_path, "VersionId": version_id, "NodeId": node_id,
        "NodePath": node_path, "NewName": new_name,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def add_niagara_script_constant_input(asset_path: str, version_id: str, name: str,
                                        kind: str, scalar_value: float = 0,
                                        components: list[float] | None = None,
                                        x: int = 0, y: int = 0, confirm: bool = False,
                                        dry_run: bool = False, save: bool = False) -> str:
    """Create an unexposed optional parameter input with stored scalar/vector/color value.

    Native representation uses Parameter usage with bExposed=false/bRequired=false;
    effective compilation remains native. Kind float/int/bool/vector/color. Existing
    version/unique safe name, confirmed /Game/stopped PIE, transaction/dry-run/save.
    """
    if kind not in ("float", "int", "bool", "vector", "color"):
        raise ValueError("kind must be float/int/bool/vector/color")
    payload = {"AssetPath": asset_path, "VersionId": version_id, "ParameterName": name,
               "ValueKind": kind, "ScalarValue": scalar_value, "bExposeInput": False,
               "NodeX": x, "NodeY": y, "bConfirm": confirm, "bDryRun": dry_run,
               "bSave": save}
    if kind in ("vector", "color"):
        if components is None or len(components) != (3 if kind == "vector" else 4):
            raise ValueError("vector requires XYZ components; color requires RGBA")
        payload["VectorValue" if kind == "vector" else "ColorValue"] = dict(zip(
            ("X", "Y", "Z") if kind == "vector" else ("R", "G", "B", "A"), components))
    endpoint = "compound-inputs" if kind in ("vector", "color") else "scalar-inputs"
    return httpx.post(f"{app.BASE_URL}/niagara/scripts/graph/{endpoint}",
                      json=payload, timeout=180).text


@mcp.tool()
def add_niagara_script_output(asset_path: str, version_id: str, node_id: str,
                                node_path: str, name: str, kind: str,
                                confirm: bool = False, dry_run: bool = False,
                                save: bool = False) -> str:
    """Append float/int/bool/vector/color output to function/dynamic-input output node.

    Unique native-safe name, <=64 outputs/pins, exact identities, confirmed /Game/
    stopped PIE, transaction/native pin reallocation/full order-type readback/
    dry-run/save. Existing callers not migrated; shared graphs share changes.
    """
    return httpx.post(f"{app.BASE_URL}/niagara/scripts/graph/outputs", json={
        "AssetPath": asset_path, "VersionId": version_id, "NodeId": node_id,
        "NodePath": node_path, "ParameterName": name, "ValueKind": kind,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def edit_niagara_script_output(asset_path: str, version_id: str, node_id: str,
                                 node_path: str, output_index: int, expected_name: str,
                                 action: str, target_index: int = -1, new_name: str = "",
                                 confirm: bool = False, dry_run: bool = False,
                                 save: bool = False) -> str:
    """Remove, move (final index) or rename function/dynamic-input output.

    Exact version/node identities plus current index/name, bounded list/name,
    confirmed /Game/stopped PIE, transaction/native pin reallocation/full order-type
    readback/no-op/dry-run/save. Existing callers not migrated; removal drops wiring.
    """
    return httpx.patch(f"{app.BASE_URL}/niagara/scripts/graph/outputs", json={
        "AssetPath": asset_path, "VersionId": version_id, "NodeId": node_id,
        "NodePath": node_path, "OutputIndex": output_index, "ParameterName": expected_name,
        "ValueKind": action, "TargetIndex": target_index, "NewName": new_name,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_niagara_script_pin_compound(asset_path: str, version_id: str, node_id: str,
                                      node_path: str, pin_id: str, kind: str,
                                      components: list[float], confirm: bool = False,
                                      dry_run: bool = False, save: bool = False) -> str:
    """Set exact vector3 XYZ or color RGBA unlinked writable input pin default.

    Finite bounded components, native struct text serialization/schema setter,
    exact identities, confirmed /Game/stopped PIE, transaction/reacquired text
    readback/dry-run/save. No position/LWC or color-space conversion.
    """
    if kind not in ("vector", "color") or len(components) != (3 if kind == "vector" else 4):
        raise ValueError("vector requires XYZ; color requires RGBA")
    payload = {"AssetPath": asset_path, "VersionId": version_id, "NodeId": node_id,
               "NodePath": node_path, "PinId": pin_id, "bConfirm": confirm,
               "bDryRun": dry_run, "bSave": save}
    payload["VectorValue" if kind == "vector" else "ColorValue"] = dict(zip(
        ("X", "Y", "Z") if kind == "vector" else ("R", "G", "B", "A"), components))
    return httpx.patch(f"{app.BASE_URL}/niagara/scripts/graph/pin-compound",
                       json=payload, timeout=180).text


def append_niagara_emitter_module(asset_path: str, emitter_index: int, emitter_id: str,
                                    version_id: str, stack: str, module_path: str,
                                    module_version_id: str, confirm: bool = False,
                                    dry_run: bool = False, save: bool = False) -> str:
    """Append module using native stack wiring to particle/emitter spawn/update.

    stack=particle_spawn/particle_update/emitter_spawn/emitter_update. Exact emitter
    identities, registered module with declared usage and explicit version, confirmed
    /Game/stopped PIE, transaction/identity readback/dry-run/save. Dependencies/input
    configuration/runtime compatibility unverified; callbacks may compile/reinitialize.
    """
    return httpx.post(f"{app.BASE_URL}/niagara/systems/emitters/modules", json={
        "AssetPath": asset_path, "EmitterIndex": emitter_index, "EmitterId": emitter_id,
        "VersionId": version_id, "ValueKind": stack, "SourceAssetPath": module_path,
        "SourceVersionId": module_version_id, "bConfirm": confirm,
        "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def inspect_niagara_emitter_stack(asset_path: str, emitter_index: int, emitter_id: str,
                                    version_id: str, stack: str) -> str:
    """Inspect particle/emitter spawn/update module parameter-map chain order.

    Exact emitter identities; bounded graph/pins/traversal with cycle/ambiguous-link
    diagnostics. Returns module node IDs/paths/script references/versions/enabled
    states. No mutation, compile request/wait, simulation or runtime validity proof.
    """
    return httpx.post(f"{app.BASE_URL}/niagara/systems/emitters/stack-inspect", json={
        "AssetPath": asset_path, "EmitterIndex": emitter_index, "EmitterId": emitter_id,
        "VersionId": version_id, "ValueKind": stack
    }, timeout=180).text


@mcp.tool()
def set_niagara_emitter_module_enabled(asset_path: str, emitter_index: int,
                                        emitter_id: str, version_id: str, stack: str,
                                        node_id: str, node_path: str, enabled: bool,
                                        confirm: bool = False, dry_run: bool = False,
                                        save: bool = False) -> str:
    """Set native module group enabled state, including associated input nodes.

    Exact emitter/version/stack/module identities, complete bounded map traversal,
    confirmed /Game/stopped PIE, transaction/native setter/main-node readback/
    dry-run/save. Always applies group setter to synchronize mixed enabled states.
    Native compile invalidation; no compile wait/simulation/rendering.
    """
    return httpx.patch(f"{app.BASE_URL}/niagara/systems/emitters/modules/enabled", json={
        "AssetPath": asset_path, "EmitterIndex": emitter_index, "EmitterId": emitter_id,
        "VersionId": version_id, "ValueKind": stack, "NodeId": node_id,
        "NodePath": node_path, "bEnabled": enabled, "bConfirm": confirm,
        "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


def insert_niagara_emitter_module(asset_path: str, emitter_index: int, emitter_id: str,
                                    version_id: str, stack: str, module_path: str,
                                    module_version_id: str, target_index: int = -1,
                                    confirm: bool = False, dry_run: bool = False,
                                    save: bool = False) -> str:
    """Insert module at native zero-based stack index; -1 appends.

    Index within 0..current module count, complete bounded map chain, exact emitter/
    module versions and declared usage, confirmed /Game/stopped PIE, transaction/
    native stack wiring/identity readback/dry-run/save. Dependencies not reordered.
    """
    return httpx.post(f"{app.BASE_URL}/niagara/systems/emitters/modules", json={
        "AssetPath": asset_path, "EmitterIndex": emitter_index, "EmitterId": emitter_id,
        "VersionId": version_id, "ValueKind": stack, "SourceAssetPath": module_path,
        "SourceVersionId": module_version_id, "TargetIndex": target_index,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def inspect_niagara_emitter_module(asset_path: str, emitter_index: int, emitter_id: str,
                                     version_id: str, stack: str, node_id: str,
                                     node_path: str) -> str:
    """Inspect a current module's native input pins/defaults/types and connections.

    Exact emitter/version/stack/module identities, bounded traversal/pins/link output.
    Stack overrides, rapid-iteration parameters and static switches may live elsewhere;
    no effective value evaluation, mutation, compilation or simulation.
    """
    return httpx.post(f"{app.BASE_URL}/niagara/systems/emitters/modules/inspect", json={
        "AssetPath": asset_path, "EmitterIndex": emitter_index, "EmitterId": emitter_id,
        "VersionId": version_id, "ValueKind": stack, "NodeId": node_id,
        "NodePath": node_path
    }, timeout=180).text


@mcp.tool()
def set_niagara_emitter_module_pin_default(asset_path: str, emitter_index: int,
                                            emitter_id: str, version_id: str, stack: str,
                                            node_id: str, node_path: str, pin_id: str,
                                            value: float, confirm: bool = False,
                                            dry_run: bool = False, save: bool = False) -> str:
    """Set unlinked writable native module float/int32/bool input pin default.

    Exact emitter/version/stack/module/pin identities, typed bounds, confirmed /Game/
    stopped PIE, transaction/schema setter/reacquired readback/no-op/dry-run/save.
    Stack overrides, rapid-iteration and static-switch values are not edited.
    """
    return httpx.patch(f"{app.BASE_URL}/niagara/systems/emitters/modules/pin-default", json={
        "AssetPath": asset_path, "EmitterIndex": emitter_index, "EmitterId": emitter_id,
        "VersionId": version_id, "ValueKind": stack, "NodeId": node_id,
        "NodePath": node_path, "PinId": pin_id, "ScalarValue": value,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_niagara_emitter_module_pin_compound(asset_path: str, emitter_index: int,
                                             emitter_id: str, version_id: str, stack: str,
                                             node_id: str, node_path: str, pin_id: str,
                                             kind: str, components: list[float],
                                             confirm: bool = False, dry_run: bool = False,
                                             save: bool = False) -> str:
    """Set unlinked writable native module vector3 XYZ or color RGBA pin default.

    Finite bounded components/native struct export, exact emitter/version/module/
    pin identities, confirmed /Game/stopped PIE, transaction/schema setter/readback/
    dry-run/save. Stack overrides and rapid-iteration parameters remain separate.
    """
    if kind not in ("vector", "color") or len(components) != (3 if kind == "vector" else 4):
        raise ValueError("vector requires XYZ; color requires RGBA")
    payload = {"AssetPath": asset_path, "EmitterIndex": emitter_index,
               "EmitterId": emitter_id, "VersionId": version_id, "ValueKind": stack,
               "NodeId": node_id, "NodePath": node_path, "PinId": pin_id,
               "bConfirm": confirm, "bDryRun": dry_run, "bSave": save}
    payload["VectorValue" if kind == "vector" else "ColorValue"] = dict(zip(
        ("X", "Y", "Z") if kind == "vector" else ("R", "G", "B", "A"), components))
    return httpx.patch(f"{app.BASE_URL}/niagara/systems/emitters/modules/pin-compound",
                       json=payload, timeout=180).text


@mcp.tool()
def reset_niagara_emitter_module_pin_default(asset_path: str, emitter_index: int,
                                              emitter_id: str, version_id: str,
                                              stack: str, node_id: str, node_path: str,
                                              pin_id: str, confirm: bool = False,
                                              dry_run: bool = False, save: bool = False) -> str:
    """Reset unlinked writable scalar/vector/color module pin to autogenerated default.

    Exact emitter/version/stack/module/pin identities, complete bounded map chain,
    confirmed /Game/stopped PIE, transaction/native schema reset/reacquired readback/
    no-op/dry-run/save. Stack overrides/rapid iteration/static switches unchanged.
    """
    return httpx.post(f"{app.BASE_URL}/niagara/systems/emitters/modules/reset-pin-default", json={
        "AssetPath": asset_path, "EmitterIndex": emitter_index, "EmitterId": emitter_id,
        "VersionId": version_id, "ValueKind": stack, "NodeId": node_id,
        "NodePath": node_path, "PinId": pin_id, "bConfirm": confirm,
        "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def inspect_niagara_emitter_rapid_iteration(asset_path: str, emitter_index: int,
                                             emitter_id: str, version_id: str,
                                             stack: str) -> str:
    """Inspect up to 256 native stack rapid-iteration names/types/stored values.

    Exact emitter/version/stack identities. Scalar/vector/color values copied by
    exact native types; other payloads not dereferenced. Names retained verbatim,
    not resolved to module UI or effective values. No mutation or compilation.
    """
    return httpx.post(f"{app.BASE_URL}/niagara/systems/emitters/rapid-iteration/inspect", json={
        "AssetPath": asset_path, "EmitterIndex": emitter_index, "EmitterId": emitter_id,
        "VersionId": version_id, "ValueKind": stack
    }, timeout=180).text


@mcp.tool()
def set_niagara_emitter_rapid_scalar(asset_path: str, emitter_index: int,
                                      emitter_id: str, version_id: str, stack: str,
                                      parameter_name: str, kind: str, value: float,
                                      confirm: bool = False, dry_run: bool = False,
                                      save: bool = False) -> str:
    """Set existing exact Constants. rapid-iteration float/int/bool value.

    Use verbatim inspected name/type; no creation or name rewriting. Exact emitter/
    version/stack, bounded store/value, confirmed /Game/stopped PIE, transaction/
    native store setter/readback/no-op/dry-run/save. Effective module values unverified.
    """
    return httpx.patch(f"{app.BASE_URL}/niagara/systems/emitters/rapid-iteration/scalar", json={
        "AssetPath": asset_path, "EmitterIndex": emitter_index, "EmitterId": emitter_id,
        "VersionId": version_id, "ValueKind": stack, "ParameterName": parameter_name,
        "FieldName": kind, "ScalarValue": value, "bConfirm": confirm,
        "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_niagara_emitter_rapid_compound(asset_path: str, emitter_index: int,
                                        emitter_id: str, version_id: str, stack: str,
                                        parameter_name: str, kind: str,
                                        components: list[float], confirm: bool = False,
                                        dry_run: bool = False, save: bool = False) -> str:
    """Set existing exact Constants. vector XYZ/color RGBA rapid-iteration value.

    Finite bounded components, exact native type/name/emitter/version, confirmed
    /Game/stopped PIE, transaction/native store setter/value readback/dry-run/save.
    No parameter creation, name rewriting, LWC or color-space conversion.
    """
    if kind not in ("vector", "color") or len(components) != (3 if kind == "vector" else 4):
        raise ValueError("vector requires XYZ; color requires RGBA")
    payload = {"AssetPath": asset_path, "EmitterIndex": emitter_index,
               "EmitterId": emitter_id, "VersionId": version_id, "ValueKind": stack,
               "ParameterName": parameter_name, "FieldName": kind,
               "bConfirm": confirm, "bDryRun": dry_run, "bSave": save}
    payload["VectorValue" if kind == "vector" else "ColorValue"] = dict(zip(
        ("X", "Y", "Z") if kind == "vector" else ("R", "G", "B", "A"), components))
    return httpx.patch(f"{app.BASE_URL}/niagara/systems/emitters/rapid-iteration/compound",
                       json=payload, timeout=180).text


@mcp.tool()
def remove_niagara_emitter_rapid_parameter(asset_path: str, emitter_index: int,
                                            emitter_id: str, version_id: str, stack: str,
                                            parameter_name: str, kind: str,
                                            confirm: bool = False, dry_run: bool = False,
                                            save: bool = False) -> str:
    """Remove existing exact Constants. float/int/bool/vector/color rapid parameter.

    Exact identities/type/name, bounded store, confirmed /Game/stopped PIE,
    transaction/native removal/absence-count readback/dry-run/save. Native editor
    reconciliation may recreate derived parameters; graph defaults not migrated.
    """
    return httpx.request("DELETE", f"{app.BASE_URL}/niagara/systems/emitters/rapid-iteration", json={
        "AssetPath": asset_path, "EmitterIndex": emitter_index, "EmitterId": emitter_id,
        "VersionId": version_id, "ValueKind": stack, "ParameterName": parameter_name,
        "FieldName": kind, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def inspect_niagara_system_rapid_iteration(asset_path: str, stack: str) -> str:
    """Inspect native system_spawn/system_update rapid-iteration store.

    Registered persistent system and owned script, up to 256 verbatim parameter
    names/types with typed scalar/vector/color stored values and truncation flags.
    No effective value evaluation, mutation, compilation or simulation.
    """
    return httpx.post(f"{app.BASE_URL}/niagara/systems/rapid-iteration/inspect", json={
        "AssetPath": asset_path, "ValueKind": stack
    }, timeout=180).text


@mcp.tool()
def edit_niagara_system_rapid_parameter(asset_path: str, stack: str, parameter_name: str,
                                         kind: str, action: str = "set", value: float = 0,
                                         components: list[float] | None = None,
                                         confirm: bool = False, dry_run: bool = False,
                                         save: bool = False) -> str:
    """Set/remove existing exact Constants. rapid parameter on system_spawn/system_update.

    kind=float/int/bool/vector/color; action=set/remove. Vector XYZ/color RGBA
    components required for compound set. Confirmed /Game/stopped PIE, native
    system/script transaction/store setter/removal/readback/dry-run/save. No creation.
    """
    if kind not in ("float", "int", "bool", "vector", "color") or action not in ("set", "remove"):
        raise ValueError("Unsupported rapid parameter kind/action")
    payload = {"AssetPath": asset_path, "ValueKind": stack, "ParameterName": parameter_name,
               "FieldName": kind, "ScalarValue": value, "bConfirm": confirm,
               "bDryRun": dry_run, "bSave": save}
    if action == "set" and kind in ("vector", "color"):
        if components is None or len(components) != (3 if kind == "vector" else 4):
            raise ValueError("vector requires XYZ; color requires RGBA")
        payload["VectorValue" if kind == "vector" else "ColorValue"] = dict(zip(
            ("X", "Y", "Z") if kind == "vector" else ("R", "G", "B", "A"), components))
    base = f"{app.BASE_URL}/niagara/systems/rapid-iteration"
    if action == "remove":
        return httpx.request("DELETE", base, json=payload, timeout=180).text
    endpoint = "compound" if kind in ("vector", "color") else "scalar"
    return httpx.patch(f"{base}/{endpoint}", json=payload, timeout=180).text


@mcp.tool()
def inspect_niagara_system_stack(asset_path: str, stack: str) -> str:
    """Inspect system_spawn/system_update modules in parameter-map chain order.

    Registered persistent system, owned bounded graph/unique output, bounded
    traversal with cycle/ambiguous/asymmetric-link diagnostics. Returns module
    IDs/paths/script versions/enabled states; no mutation or compilation.
    """
    return httpx.post(f"{app.BASE_URL}/niagara/systems/stack-inspect", json={
        "AssetPath": asset_path, "ValueKind": stack
    }, timeout=180).text


@mcp.tool()
def insert_niagara_system_module(asset_path: str, stack: str, module_path: str,
                                   module_version_id: str, target_index: int = -1,
                                   confirm: bool = False, dry_run: bool = False,
                                   save: bool = False) -> str:
    """Insert module into system_spawn/system_update; -1 appends.

    Registered matching-usage module/version, owned bounded graph/validated chain,
    confirmed /Game/stopped PIE, native wiring/transaction/full order readback/
    dry-run/save. Dependencies/inputs/runtime compatibility unverified.
    """
    return httpx.post(f"{app.BASE_URL}/niagara/systems/modules", json={
        "AssetPath": asset_path, "ValueKind": stack, "SourceAssetPath": module_path,
        "SourceVersionId": module_version_id, "TargetIndex": target_index,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def inspect_niagara_system_module(asset_path: str, stack: str, node_id: str,
                                    node_path: str) -> str:
    """Inspect current system_spawn/system_update module input pins/defaults/links.
    Exact module identities, bounded native chain. No mutation/effective evaluation.
    """
    return httpx.post(f"{app.BASE_URL}/niagara/systems/modules/inspect", json={
        "AssetPath": asset_path, "ValueKind": stack, "NodeId": node_id,
        "NodePath": node_path
    }, timeout=180).text


@mcp.tool()
def set_niagara_system_module_enabled(asset_path: str, stack: str, node_id: str,
                                        node_path: str, enabled: bool,
                                        confirm: bool = False, dry_run: bool = False,
                                        save: bool = False) -> str:
    """Set native system module group enabled state with exact stack/node guards.
    Confirmed /Game/stopped PIE, transaction/native group setter/main-node readback/
    dry-run/save. Setter synchronizes associated nodes; callbacks may compile.
    """
    return httpx.patch(f"{app.BASE_URL}/niagara/systems/modules/enabled", json={
        "AssetPath": asset_path, "ValueKind": stack, "NodeId": node_id,
        "NodePath": node_path, "bEnabled": enabled,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def edit_niagara_system_module_pin_default(asset_path: str, stack: str, node_id: str,
                                             node_path: str, pin_id: str,
                                             action: str = "set", kind: str = "float",
                                             value: float = 0,
                                             components: list[float] | None = None,
                                             confirm: bool = False, dry_run: bool = False,
                                             save: bool = False) -> str:
    """Set/reset unlinked writable system module scalar/vector/color pin default.

    action=set/reset; native type validation and exact stack/module/pin identities,
    confirmed /Game/stopped PIE, transaction/schema notifications/readback/dry-run/
    save. Stack overrides/rapid iteration/static switches remain separate.
    """
    if action not in ("set", "reset") or kind not in ("float", "int", "bool", "vector", "color"):
        raise ValueError("Unsupported action/kind")
    payload = {"AssetPath": asset_path, "ValueKind": stack, "NodeId": node_id,
               "NodePath": node_path, "PinId": pin_id, "ScalarValue": value,
               "bConfirm": confirm, "bDryRun": dry_run, "bSave": save}
    base = f"{app.BASE_URL}/niagara/systems/modules"
    if action == "reset":
        return httpx.post(f"{base}/reset-pin-default", json=payload, timeout=180).text
    if kind in ("vector", "color"):
        if components is None or len(components) != (3 if kind == "vector" else 4):
            raise ValueError("vector requires XYZ; color requires RGBA")
        payload["VectorValue" if kind == "vector" else "ColorValue"] = dict(zip(
            ("X", "Y", "Z") if kind == "vector" else ("R", "G", "B", "A"), components))
    endpoint = "pin-compound" if kind in ("vector", "color") else "pin-default"
    return httpx.patch(f"{base}/{endpoint}", json=payload, timeout=180).text


@mcp.tool()
def inspect_niagara_emitter_stack_dependencies(asset_path: str, emitter_index: int,
                                                 emitter_id: str, version_id: str,
                                                 stack: str) -> str:
    """Check authored same-stack dependency provider/order/version constraints.

    Exact emitter/version/stack and complete bounded chain; up to 256 checks,
    65536 comparison budget. AllScripts providers may exist elsewhere; disabled/
    conditional modules not evaluated. Native invalid version expressions are
    unconstrained. Diagnostics only; no mutation or compile/runtime validity proof.
    """
    return httpx.post(f"{app.BASE_URL}/niagara/systems/emitters/stack-dependencies", json={
        "AssetPath": asset_path, "EmitterIndex": emitter_index, "EmitterId": emitter_id,
        "VersionId": version_id, "ValueKind": stack
    }, timeout=180).text


@mcp.tool()
def inspect_niagara_system_stack_dependencies(asset_path: str, stack: str) -> str:
    """Check system_spawn/system_update same-stack dependency providers/order/versions.

    Complete bounded owned graph chain, 65536 comparisons, up to 256 check records.
    AllScripts providers may exist elsewhere; disabled/conditional modules not
    evaluated. Native invalid version expressions are unconstrained. No mutation,
    compilation or runtime validity proof.
    """
    return httpx.post(f"{app.BASE_URL}/niagara/systems/stack-dependencies", json={
        "AssetPath": asset_path, "ValueKind": stack
    }, timeout=180).text


@mcp.tool()
def inspect_niagara_effect_type(asset_path: str) -> str:
    """Inspect authored effect-type scalability settings and validation rule identities.

    Registered persistent asset; <=64 editable field exports (4096 chars), <=128
    rule/ruleset references with counts/truncation. Export allocation uncapped;
    active platform settings and validation rules not evaluated. No mutation.
    """
    return httpx.post(f"{app.BASE_URL}/niagara/effect-types/inspect", json={
        "AssetPath": asset_path
    }, timeout=180).text


@mcp.tool()
def create_niagara_effect_type(asset_path: str, confirm: bool = False,
                                 dry_run: bool = False, save: bool = False) -> str:
    """Create effect-type scalability profile using native factory class defaults.
    New matching /Game destination, confirmed stopped PIE, collision checks,
    transaction/class-path readback/dry-run/save. No system assignment or simulation.
    """
    return httpx.post(f"{app.BASE_URL}/niagara/effect-types", json={
        "AssetPath": asset_path, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def duplicate_niagara_effect_type(source_asset_path: str, asset_path: str,
                                    confirm: bool = False, dry_run: bool = False,
                                    save: bool = False) -> str:
    """Duplicate registered effect type through native AssetTools into new /Game path.
    Collision checks/transaction/class-path readback/dry-run/save. Instanced rules/
    significance handler follow native duplication; external references stay shared.
    """
    return httpx.post(f"{app.BASE_URL}/niagara/effect-types/duplicate", json={
        "SourceAssetPath": source_asset_path, "AssetPath": asset_path,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_niagara_effect_type_policy(asset_path: str, field: str, enum_name: str = "",
                                     enabled: bool = False, confirm: bool = False,
                                     dry_run: bool = False, save: bool = False) -> str:
    """Edit bAllowCullingForLocalPlayers, UpdateFrequency or CullReaction.

    Bool uses enabled; enums require visible declared short/qualified enum_name.
    Shared profile affects referencing systems. Confirmed /Game/stopped PIE,
    transaction/native notification/readback/no-op/dry-run/save; runtime unverified.
    """
    endpoint = "bool" if field == "bAllowCullingForLocalPlayers" else "enum"
    return httpx.patch(f"{app.BASE_URL}/niagara/effect-types/{endpoint}", json={
        "AssetPath": asset_path, "FieldName": field, "NewName": enum_name,
        "bEnabled": enabled, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def list_niagara_significance_handlers() -> str:
    """List up to 128 loaded concrete native significance-handler classes."""
    return httpx.post(f"{app.BASE_URL}/niagara/significance-handlers", json={}, timeout=180).text


@mcp.tool()
def set_niagara_effect_type_significance(asset_path: str, handler_class: str = "",
                                          confirm: bool = False, dry_run: bool = False,
                                          save: bool = False) -> str:
    """Assign owned native significance handler; empty clears, same class retained.
    Confirmed /Game/stopped PIE, transaction/native notification/ownership-class
    readback/dry-run/save. Shared effect profile affects referencing systems.
    """
    return httpx.patch(f"{app.BASE_URL}/niagara/effect-types/significance-handler", json={
        "AssetPath": asset_path, "HandlerClass": handler_class,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def list_niagara_validation_rule_types() -> str:
    """List up to 128 loaded concrete native Niagara validation rule classes."""
    return httpx.post(f"{app.BASE_URL}/niagara/validation-rule-types", json={}, timeout=180).text


@mcp.tool()
def add_niagara_effect_type_rule(asset_path: str, rule_class: str,
                                   confirm: bool = False, dry_run: bool = False,
                                   save: bool = False) -> str:
    """Append owned validation rule using native class-default settings (max 128).
    Confirmed /Game/stopped PIE, transaction/native notification/ownership-count
    readback/dry-run/save. No validation execution or automatic fixes invoked.
    """
    return httpx.post(f"{app.BASE_URL}/niagara/effect-types/rules", json={
        "AssetPath": asset_path, "RuleClass": rule_class,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def edit_niagara_effect_type_rule(asset_path: str, rule_index: int, rule_path: str,
                                    action: str, target_index: int = -1,
                                    confirm: bool = False, dry_run: bool = False,
                                    save: bool = False) -> str:
    """Remove/move/duplicate owned effect-type validation rule; duplicate appends.
    Exact index/path/unique pointer, max128 rules, confirmed /Game/stopped PIE,
    transaction/native notification/full pointer-order readback/dry-run/save.
    Removed objects retained for undo; no validation execution or fixes invoked.
    """
    return httpx.patch(f"{app.BASE_URL}/niagara/effect-types/rules", json={
        "AssetPath": asset_path, "RuleIndex": rule_index, "RulePath": rule_path,
        "ValueKind": action, "TargetIndex": target_index,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def inspect_niagara_effect_type_rule(asset_path: str, rule_index: int,
                                       rule_path: str, field: str = "") -> str:
    """Inspect current owned rule's authored fields, enum choices and clamp metadata.
    Exact index/path/ownership; <=128 fields, <=128 choices, text<=4096 with
    truncation. Export allocation uncapped. No rule execution/fixes or mutation.
    """
    return httpx.post(f"{app.BASE_URL}/niagara/effect-types/rules/inspect", json={
        "AssetPath": asset_path, "RuleIndex": rule_index, "RulePath": rule_path,
        "FieldName": field
    }, timeout=180).text


def set_niagara_effect_type_rule_scalar(asset_path: str, rule_index: int, rule_path: str,
                                          field: str, value: float, confirm: bool = False,
                                          dry_run: bool = False, save: bool = False) -> str:
    """Set owned validation rule bool/numeric leaf, nested structs up to 8 segments.
    Writable nontransient fields, bool0/1/native integer width/clamp checks, finite
    +/-1e9, exact rule identity, confirmed /Game/stopped PIE, transaction/native
    notifications/readback/no-op/dry-run/save. No arrays/objects or rule execution.
    """
    return httpx.patch(f"{app.BASE_URL}/niagara/effect-types/rules/scalar", json={
        "AssetPath": asset_path, "RuleIndex": rule_index, "RulePath": rule_path,
        "FieldName": field, "ScalarValue": value, "bConfirm": confirm,
        "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


def set_niagara_effect_type_rule_enum(asset_path: str, rule_index: int, rule_path: str,
                                        field: str, enum_name: str, confirm: bool = False,
                                        dry_run: bool = False, save: bool = False) -> str:
    """Set owned rule enum leaf by declared visible short/qualified native name.
    Up to8 inline struct segments, exact rule index/path, confirmed /Game/stopped
    PIE, transaction/native notifications/value+identity readback/no-op/dry-run/save.
    Hidden/sentinel choices and arrays/object traversal rejected. No rule execution.
    """
    return httpx.patch(f"{app.BASE_URL}/niagara/effect-types/rules/enum", json={
        "AssetPath": asset_path, "RuleIndex": rule_index, "RulePath": rule_path,
        "FieldName": field, "NewName": enum_name, "bConfirm": confirm,
        "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_niagara_effect_type_rule_reference(asset_path: str, rule_index: int,
                                             rule_path: str, field: str, kind: str,
                                             value: str = "", confirm: bool = False,
                                             dry_run: bool = False, save: bool = False) -> str:
    """Set owned rule FName or hard asset reference leaf (kind=name/asset).

    Empty name becomes None; empty asset clears unless native NoClear. Asset must
    be registered/persistent/type-compatible; instanced/class properties rejected.
    Up to8 inline structs, exact identities, confirmed /Game/stopped PIE,
    transaction/notifications/readback/no-op/dry-run/save. No rule execution.
    """
    if kind not in ("name", "asset"): raise ValueError("kind must be name/asset")
    return httpx.patch(f"{app.BASE_URL}/niagara/effect-types/rules/{kind}", json={
        "AssetPath": asset_path, "RuleIndex": rule_index, "RulePath": rule_path,
        "FieldName": field, "NewName": value if kind == "name" else "",
        "SourceAssetPath": value if kind == "asset" else "", "bConfirm": confirm,
        "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def reset_niagara_effect_type_rule_field(asset_path: str, rule_index: int,
                                           rule_path: str, field: str,
                                           confirm: bool = False, dry_run: bool = False,
                                           save: bool = False) -> str:
    """Reset supported scalar/enum/name/vector/color leaf to exact native class default.
    Bounded inline struct path, exact rule identity, confirmed /Game/stopped PIE,
    transaction/native copy+notifications/readback/no-op/dry-run/save. No rule execution.
    """
    return httpx.post(f"{app.BASE_URL}/niagara/effect-types/rules/reset-field", json={
        "AssetPath": asset_path, "RuleIndex": rule_index, "RulePath": rule_path,
        "FieldName": field, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_niagara_effect_type_rule_compound(asset_path: str, rule_index: int,
                                            rule_path: str, field: str, kind: str,
                                            components: list[float], confirm: bool = False,
                                            dry_run: bool = False, save: bool = False) -> str:
    """Set exact native FVector XYZ/FLinearColor RGBA rule leaf (kind=vector/color).
    Finite bounds +/-1e9 vector, +/-1e6 color; <=8 inline struct segments, exact rule
    identity, confirmed /Game/stopped PIE, transaction/notifications/readback/dry-run/
    save. No rule execution or color-space conversion.
    """
    if kind not in ("vector", "color") or len(components) != (3 if kind == "vector" else 4):
        raise ValueError("vector requires XYZ; color requires RGBA")
    payload = {"AssetPath": asset_path, "RuleIndex": rule_index, "RulePath": rule_path,
               "FieldName": field, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save}
    payload["VectorValue" if kind == "vector" else "ColorValue"] = dict(zip(
        ("X", "Y", "Z") if kind == "vector" else ("R", "G", "B", "A"), components))
    return httpx.patch(f"{app.BASE_URL}/niagara/effect-types/rules/{kind}",
                       json=payload, timeout=180).text


@mcp.tool()
def set_niagara_effect_type_rule_sets(asset_path: str, rule_set_paths: list[str],
                                        confirm: bool = False, dry_run: bool = False,
                                        save: bool = False) -> str:
    """Replace ordered <=128 unique registered validation rule-set references.
    Empty clears; persistent native rule sets, confirmed /Game/stopped PIE,
    transaction/native notification/full pointer-order readback/no-op/dry-run/save.
    Referenced assets unchanged; validation rules/fixes not executed.
    """
    return httpx.patch(f"{app.BASE_URL}/niagara/effect-types/rule-sets", json={
        "AssetPath": asset_path, "RuleSetPaths": rule_set_paths,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def inspect_niagara_validation_rule_set(asset_path: str) -> str:
    """Inspect reusable rule-set ordered rule identities/classes/ownership/enabled state.
    Up to128 rules with count/truncation. No rule execution/fixes or mutation.
    """
    return httpx.post(f"{app.BASE_URL}/niagara/rule-sets/inspect", json={"AssetPath": asset_path}, timeout=180).text


@mcp.tool()
def create_niagara_validation_rule_set(asset_path: str, source_asset_path: str = "",
                                         confirm: bool = False, dry_run: bool = False,
                                         save: bool = False) -> str:
    """Create native rule set, or duplicate source when source_asset_path supplied.
    New matching /Game destination, collision checks, confirmed stopped PIE,
    transaction/class-path readback/dry-run/save. No rule execution or assignment.
    """
    suffix = "/duplicate" if source_asset_path else ""
    return httpx.post(f"{app.BASE_URL}/niagara/rule-sets{suffix}", json={
        "AssetPath": asset_path, "SourceAssetPath": source_asset_path,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def edit_niagara_rule_set_rule(asset_path: str, action: str, rule_index: int = -1,
                                 rule_path: str = "", rule_class: str = "",
                                 target_index: int = -1, field: str = "",
                                 value: float = 0, text: str = "",
                                 components: list[float] | None = None,
                                 confirm: bool = False, dry_run: bool = False,
                                 save: bool = False) -> str:
    """Author reusable rule-set rules: add/inspect/remove/move/duplicate,
    scalar/enum/name/asset/vector/color/reset. Exact rule identities required except
    add; bounded owned rules and confirmed /Game/stopped PIE for mutations.
    text supplies enum/name/asset value; field selects bounded nested leaf.
    Native transactions/notifications/readback/dry-run/save; no rule execution.
    """
    allowed = {"add", "inspect", "remove", "move", "duplicate", "scalar", "enum",
               "name", "asset", "vector", "color", "reset"}
    if action not in allowed: raise ValueError("Unsupported rule-set action")
    payload = {"AssetPath": asset_path, "RuleIndex": rule_index, "RulePath": rule_path,
               "RuleClass": rule_class, "TargetIndex": target_index, "FieldName": field,
               "ScalarValue": value, "NewName": text, "SourceAssetPath": text,
               "ValueKind": action, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save}
    if action in ("vector", "color"):
        if components is None or len(components) != (3 if action == "vector" else 4):
            raise ValueError("vector requires XYZ; color requires RGBA")
        payload["VectorValue" if action == "vector" else "ColorValue"] = dict(zip(
            ("X", "Y", "Z") if action == "vector" else ("R", "G", "B", "A"), components))
    method = "POST" if action in ("add", "inspect", "reset") else "PATCH"
    suffix = "" if action in ("add", "remove", "move", "duplicate") else "/reset-field" if action == "reset" else f"/{action}"
    return httpx.request(method, f"{app.BASE_URL}/niagara/rule-sets/rules{suffix}",
                         json=payload, timeout=180).text


def set_niagara_validation_rule_text(asset_path: str, rule_index: int, rule_path: str,
                                        field: str, text: str, confirm: bool = False,
                                        dry_run: bool = False, save: bool = False) -> str:
    """Set owned effect-type/rule-set FString/FText leaf <=4096 characters.
    <=8 writable inline structs, exact rule identity, confirmed /Game/stopped PIE,
    transaction/native notifications/readback/dry-run/save. Empty clears; changed
    FText uses plain text localization identity. No rule execution/config toggles.
    """
    return httpx.patch(f"{app.BASE_URL}/niagara/effect-types/rules/text", json={
        "AssetPath": asset_path, "RuleIndex": rule_index, "RulePath": rule_path,
        "FieldName": field, "TextValue": text, "bConfirm": confirm,
        "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


def set_niagara_validation_rule_string_array(asset_path: str, rule_index: int,
                                               rule_path: str, field: str,
                                               values: list[str], confirm: bool = False,
                                               dry_run: bool = False, save: bool = False) -> str:
    """Replace <=256 FName/FString values in owned effect-type/rule-set rule array.
    Empty clears; order/duplicates retained. Name<=128/non-None/single-line,
    string<=4096. Bounded inline struct path, exact rule identities, confirmed /Game/
    stopped PIE, transaction/native notifications/full readback/dry-run/save.
    """
    return httpx.patch(f"{app.BASE_URL}/niagara/effect-types/rules/string-array", json={
        "AssetPath": asset_path, "RuleIndex": rule_index, "RulePath": rule_path,
        "FieldName": field, "StringValues": values, "bConfirm": confirm,
        "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_niagara_validation_rule_reference_array(asset_path: str, rule_index: int,
                                                  rule_path: str, field: str,
                                                  paths: list[str], confirm: bool = False,
                                                  dry_run: bool = False, save: bool = False) -> str:
    """Replace <=256 hard asset/class rule references; empty clears, order retained.
    Loaded classes checked against native MetaClass (abstract selectors allowed),
    assets registered/persistent/property-compatible; instanced arrays rejected.
    Exact owned rule identity, bounded struct path, confirmed /Game/stopped PIE,
    transaction/native notifications/full pointer readback/dry-run/save.
    """
    return httpx.patch(f"{app.BASE_URL}/niagara/effect-types/rules/reference-array", json={
        "AssetPath": asset_path, "RuleIndex": rule_index, "RulePath": rule_path,
        "FieldName": field, "StringValues": paths, "bConfirm": confirm,
        "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def validate_niagara_system_rules(asset_path: str, confirm: bool = False,
                                    dry_run: bool = False) -> str:
    """Run native validation rules on a transient system duplicate, no automatic fixes.
    Confirmed/stopped PIE, <=128 emitters; data-processing view model with auto-compile/
    simulation disabled. <=256 results/64 fix descriptions, counts/truncation.
    Rule work uncapped; custom rules may have side effects. No save/compile wait;
    transient source paths aren't persistent identities. Dry-run only checks rules.
    """
    return httpx.post(f"{app.BASE_URL}/niagara/systems/validate-rules", json={
        "AssetPath": asset_path, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def simulate_niagara_system_preview(asset_path: str, ticks: int = 1,
                                       delta_seconds: float = 1/60,
                                       confirm: bool = False, dry_run: bool = False,
                                       overrides: list[dict] | None = None,
                                       transform: dict | None = None, seed_offset: int = 0) -> str:
    """Advance hidden temporary solo CPU Niagara preview, return age/completion and
    <=128 sampled tick/age/execution-state/local-bounds records.
    Optional transform uses native FTransform JSON; seed_offset int32 applies to
    temporary component before activation. Overrides <=64 records: Name, Kind=float/int/bool/vector/color, Scalar/Vector/Color;
    existing exact-type User parameters only, applied to temporary component.
    Confirmed/stopped PIE, already compiled ready system, stateful CPU emitters;
    1..600 ticks, delta1/240..1, <=30 simulated seconds. Native/custom per-tick work
    and authored warmup uncapped. No save, compile wait, image or particle-output proof.
    """
    payload = {
        "AssetPath": asset_path, "PreviewOverrides": overrides or [], "SimulationTicks": ticks, "WarmupDelta": delta_seconds,
        "bConfirm": confirm, "bDryRun": dry_run, "PreviewSeedOffset": seed_offset
    }
    if transform is not None: payload["PreviewTransform"] = transform
    return httpx.post(f"{app.BASE_URL}/niagara/systems/simulate-preview",
                      json=payload, timeout=180).text


@mcp.tool()
def inspect_niagara_effect_type_scalability(asset_path: str, kind: str) -> str:
    """Inspect authored system/emitter scalability rows and record fingerprints.
    <=128 rows, <=256 flattened fields per row through eight struct levels,
    visible enum choices, quality/profile masks and typed CVar conditions.
    Bounded field text/clamp metadata. Native export hash
    supports stale-row guards; exporter allocation uncapped. No active-platform
    resolution, mutation, rule execution, compilation or simulation.
    """
    # Rows include bounded flattened inline struct paths and visible enum choices.
    return httpx.post(f"{app.BASE_URL}/niagara/effect-types/scalability/inspect", json={
        "AssetPath": asset_path, "ValueKind": kind
    }, timeout=180).text


@mcp.tool()
def edit_niagara_effect_type_scalability_rows(asset_path: str, kind: str, action: str,
                                                row_index: int = -1, record_hash: str = "",
                                                target_index: int = -1,
                                                confirm: bool = False, dry_run: bool = False,
                                                save: bool = False) -> str:
    """Add/remove/duplicate/move authored system/emitter scalability row (max128).
    Existing row requires inspected index/hash; move uses final target index,
    duplicate appends, add uses native defaults. Confirmed /Game/stopped PIE,
    transaction/native notifications/full ordered snapshot readback/dry-run/save.
    Active platform resolution not evaluated; exporter allocation uncapped.
    """
    return httpx.patch(f"{app.BASE_URL}/niagara/effect-types/scalability/rows", json={
        "AssetPath": asset_path, "ValueKind": kind, "NewName": action,
        "ScalabilityIndex": row_index, "RecordHash": record_hash,
        "TargetIndex": target_index, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


def set_niagara_effect_type_scalability_scalar(asset_path: str, kind: str,
                                                 row_index: int, record_hash: str,
                                                 field: str, value: float,
                                                 confirm: bool = False, dry_run: bool = False,
                                                 save: bool = False) -> str:
    """Set bool/numeric scalability row leaf with inspected index/hash stale guard.
    kind=system/emitter; <=8 writable inline structs, native clamp/integer-width/
    bool0/1/finite bounds, confirmed /Game/stopped PIE, transaction/root notification/
    reacquired row-value readback/dry-run/save. Active platform resolution unverified.
    """
    return httpx.patch(f"{app.BASE_URL}/niagara/effect-types/scalability/scalar", json={
        "AssetPath": asset_path, "ValueKind": kind, "ScalabilityIndex": row_index,
        "RecordHash": record_hash, "FieldName": field, "ScalarValue": value,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


def set_niagara_effect_type_scalability_enum(asset_path: str, kind: str,
                                           row_index: int, record_hash: str,
                                           field: str, value: str,
                                           confirm: bool = False, dry_run: bool = False,
                                           save: bool = False) -> str:
    """Set declared visible native enum on an inspected system/emitter scalability row.
    Requires current index/hash, writable inline struct field and confirmed /Game/
    stopped PIE. Uses transaction, native notification, reacquired readback and
    optional save. Returns current fingerprint; active platform behavior unverified.
    """
    return httpx.patch(f"{app.BASE_URL}/niagara/effect-types/scalability/enum", json={
        "AssetPath": asset_path, "ValueKind": kind, "ScalabilityIndex": row_index,
        "RecordHash": record_hash, "FieldName": field, "NewName": value,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def reset_niagara_effect_type_scalability_field(asset_path: str, kind: str,
                                              row_index: int, record_hash: str,
                                              field: str, confirm: bool = False,
                                              dry_run: bool = False, save: bool = False) -> str:
    """Reset scalar/enum/name/text/vector/color leaf to native scalability row default.
    Preserves other fields; requires inspected index/hash and writable inline struct
    path. Confirmed /Game/stopped PIE, transaction, notification, reacquired readback,
    optional save and current fingerprint response. Platform validity unverified.
    """
    return httpx.patch(f"{app.BASE_URL}/niagara/effect-types/scalability/reset-field", json={
        "AssetPath": asset_path, "ValueKind": kind, "ScalabilityIndex": row_index,
        "RecordHash": record_hash, "FieldName": field,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_niagara_effect_type_scalability_quality(asset_path: str, kind: str,
                                              row_index: int, record_hash: str,
                                              quality_level: int, enabled: bool,
                                              confirm: bool = False,
                                              dry_run: bool = False, save: bool = False) -> str:
    """Toggle native effects quality bit (0..31) on inspected system/emitter row.
    Preserves device-profile/CVar conditions. Uses native cache invalidation,
    transaction, notification/readback and optional save; returns row fingerprint.
    Confirmed /Game/stopped PIE required. Active platform resolution unverified.
    """
    return httpx.patch(f"{app.BASE_URL}/niagara/effect-types/scalability/quality", json={
        "AssetPath": asset_path, "ValueKind": kind, "ScalabilityIndex": row_index,
        "RecordHash": record_hash, "ScalarValue": quality_level, "bEnabled": enabled,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_niagara_effect_type_scalability_profile(asset_path: str, kind: str,
                                              row_index: int, record_hash: str,
                                              profile: str, quality_level: int,
                                              state: str, confirm: bool = False,
                                              dry_run: bool = False, save: bool = False) -> str:
    """Set existing device profile override: state=default/enabled/disabled.
    Native fixed-quality profiles may update all bits; unavailable quality reads
    Default. No profiles created. <=128 overrides; inspected index/hash, confirmed
    /Game/stopped PIE, transaction/native readback/save/current fingerprint.
    Native preflight updates caches; active platform/render behavior unverified.
    """
    return httpx.patch(f"{app.BASE_URL}/niagara/effect-types/scalability/profile", json={
        "AssetPath": asset_path, "ValueKind": kind, "ScalabilityIndex": row_index,
        "RecordHash": record_hash, "ScalarValue": quality_level,
        "NewName": profile, "TextValue": state, "bConfirm": confirm,
        "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def edit_niagara_effect_type_scalability_conditions(asset_path: str, kind: str,
                                                  row_index: int, record_hash: str,
                                                  action: str, condition_index: int = -1,
                                                  target_index: int = -1, cvar_name: str = "",
                                                  confirm: bool = False,
                                                  dry_run: bool = False, save: bool = False) -> str:
    """Add/remove/duplicate/move scalability CVar conditions, <=128 entries.
    Add uses native defaults and existing bool/int/float CVar; duplicate appends,
    move uses final index. Inspected row/hash, confirmed /Game/stopped PIE,
    transaction/cache invalidation/order-content readback/save/current fingerprint.
    Does not modify CVar values or evaluate platform conditions.
    """
    return httpx.patch(f"{app.BASE_URL}/niagara/effect-types/scalability/conditions", json={
        "AssetPath": asset_path, "ValueKind": kind, "ScalabilityIndex": row_index,
        "RecordHash": record_hash, "NewName": action, "OutputIndex": condition_index,
        "TargetIndex": target_index, "TextValue": cvar_name, "bConfirm": confirm,
        "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def set_niagara_effect_type_scalability_condition(asset_path: str, kind: str,
                                                row_index: int, record_hash: str,
                                                condition_index: int, cvar_name: str,
                                                pass_response: str = "None",
                                                fail_response: str = "Disable",
                                                bool_value: bool = True,
                                                use_min_int: bool = False,
                                                use_max_int: bool = False,
                                                min_int: int = 1, max_int: int = 1,
                                                use_min_float: bool = False,
                                                use_max_float: bool = False,
                                                min_float: float = 1, max_float: float = 1,
                                                confirm: bool = False,
                                                dry_run: bool = False, save: bool = False) -> str:
    """Replace all settings of an existing scalability CVar condition.
    Responses: None/Enable/Disable. Existing bool/int/float CVar; int32 and finite
    float +/-1e9 bounds, enabled min<=max. Each call replaces all condition fields.
    Current row/hash, confirmed /Game/stopped PIE, transaction/cache notification/
    native readback/save. Runtime CVar values untouched; no condition evaluation.
    """
    return httpx.patch(f"{app.BASE_URL}/niagara/effect-types/scalability/condition-settings", json={
        "AssetPath": asset_path, "ValueKind": kind, "ScalabilityIndex": row_index,
        "RecordHash": record_hash, "OutputIndex": condition_index,
        "ConditionConfig": {"Name": cvar_name, "PassResponse": pass_response,
            "FailResponse": fail_response, "BoolValue": bool_value,
            "UseMinInt": use_min_int, "UseMaxInt": use_max_int,
            "MinInt": min_int, "MaxInt": max_int,
            "UseMinFloat": use_min_float, "UseMaxFloat": use_max_float,
            "MinFloat": min_float, "MaxFloat": max_float},
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def inspect_niagara_effect_type_scalability_conflicts(asset_path: str, kind: str,
                                                    confirm: bool = False,
                                                    dry_run: bool = False) -> str:
    """Evaluate native selection overlap on <=32 scalability rows using loaded profiles.
    Confirmed/stopped PIE; <=256 profiles and <=65536 pair/profile comparisons.
    Native copies preserve authored assets. Returns row pairs/profile quality masks,
    <=256 pairs/128 profiles each. May load ini data/populate global caches; native
    work not strictly bounded. Dry run preflights only; no compile/simulation/save.
    """
    return httpx.post(f"{app.BASE_URL}/niagara/effect-types/scalability/conflicts", json={
        "AssetPath": asset_path, "ValueKind": kind,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def discover_niagara_scalability_profiles() -> str:
    """List <=256 manager-loaded device profiles and <=32 configured quality names.
    Includes profile name/path/device type/base/asset visibility and active profile.
    Native manager access may initialize profile state. No explicit profile creation,
    switching, CVar application, selection evaluation, asset edit or simulation.
    """
    return httpx.post(f"{app.BASE_URL}/niagara/scalability/profiles", json={}, timeout=180).text


@mcp.tool()
def evaluate_niagara_effect_type_scalability(asset_path: str, kind: str,
                                            profile: str, quality_level: int,
                                            check_current_state_only: bool = True,
                                            confirm: bool = False, dry_run: bool = False) -> str:
    """Native profile/quality selection evaluation for <=128 authored rows.
    Returns activity/potential activity, default/available masks and bounded reasons.
    Uses copies, existing profile, quality0..31; confirmed/stopped PIE required.
    Native evaluation may load ini/CVar data and populate global caches. Dry run
    preflights only. No profile switch, CVar application, asset edit or simulation.
    """
    return httpx.post(f"{app.BASE_URL}/niagara/effect-types/scalability/evaluate", json={
        "AssetPath": asset_path, "ValueKind": kind, "NewName": profile,
        "ScalarValue": quality_level, "bEnabled": check_current_state_only,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_active_niagara_effect_type_scalability(asset_path: str, kind: str,
                                                confirm: bool = False,
                                                dry_run: bool = False) -> str:
    """Inspect native current-editor effective effect-type scalability configuration.
    Returns first active row index/hash or native fallback and <=128 field values.
    Confirmed/stopped PIE, <=128 rows/conditions/profile entries; dry run preflights.
    Native cached selections/ini/CVar data may affect results and update caches.
    Does not compose system/emitter overrides or prove live culling behavior.
    """
    return httpx.post(f"{app.BASE_URL}/niagara/effect-types/scalability/active", json={
        "AssetPath": asset_path, "ValueKind": kind,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def copy_niagara_effect_type_scalability_row(asset_path: str, kind: str,
                                           row_index: int, record_hash: str,
                                           source_asset_path: str, source_row_index: int,
                                           source_record_hash: str, confirm: bool = False,
                                           dry_run: bool = False, save: bool = False) -> str:
    """Replace existing same-kind scalability row from another inspected effect type.
    Separate source/destination index/hash guards. Copies full native row including
    platform/profile/CVar conditions; <=128 rows. Confirmed /Game destination/stopped
    PIE, transaction/cache invalidation/readback/save/current destination fingerprint.
    No source mutation; export intermediate allocation uncapped; no simulation.
    """
    return httpx.patch(f"{app.BASE_URL}/niagara/effect-types/scalability/copy-row", json={
        "AssetPath": asset_path, "ValueKind": kind, "ScalabilityIndex": row_index,
        "RecordHash": record_hash, "SourceAssetPath": source_asset_path,
        "SourceScalabilityIndex": source_row_index, "SourceRecordHash": source_record_hash,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


@mcp.tool()
def reset_niagara_effect_type_scalability_row(asset_path: str, kind: str,
                                            row_index: int, record_hash: str,
                                            confirm: bool = False,
                                            dry_run: bool = False, save: bool = False) -> str:
    """Reset complete scalability row to native defaults, preserving row order.
    Includes platform/profile/CVar conditions. Current index/hash, <=128 rows,
    confirmed /Game/stopped PIE, transaction/cache invalidation/full native readback,
    optional save/current fingerprint. Active selection/render behavior unverified.
    """
    return httpx.patch(f"{app.BASE_URL}/niagara/effect-types/scalability/reset-row", json={
        "AssetPath": asset_path, "ValueKind": kind, "ScalabilityIndex": row_index,
        "RecordHash": record_hash, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save
    }, timeout=180).text


# Tools listed to clients. Each picks one of the functions above with its variant argument.
add_niagara_emitter_module = merged_tool("add_niagara_emitter_module", {
    "append_niagara_emitter_module": append_niagara_emitter_module,
    "insert_niagara_emitter_module": insert_niagara_emitter_module,
})
set_niagara_user = merged_tool("set_niagara_user", {
    "scalar": set_niagara_user_scalar,
    "vector": set_niagara_user_vector,
    "color": set_niagara_user_color,
})
set_niagara_renderer = merged_tool("set_niagara_renderer", {
    "scalar": set_niagara_renderer_scalar,
    "enum": set_niagara_renderer_enum,
    "name": set_niagara_renderer_name,
    "vector": set_niagara_renderer_vector,
    "color": set_niagara_renderer_color,
})
add_niagara_user = merged_tool("add_niagara_user", {
    "scalar": add_niagara_user_scalar,
    "vector": add_niagara_user_vector,
    "color": add_niagara_user_color,
})
set_niagara_emitter = merged_tool("set_niagara_emitter", {
    "scalar": set_niagara_emitter_scalar,
    "enum": set_niagara_emitter_enum,
})
set_niagara_simulation_stage = merged_tool("set_niagara_simulation_stage", {
    "enum": set_niagara_simulation_stage_enum,
    "bool": set_niagara_simulation_stage_bool,
})
set_niagara_script = merged_tool("set_niagara_script", {
    "text": set_niagara_script_text,
    "bool": set_niagara_script_bool,
    "enum": set_niagara_script_enum,
})
set_niagara_effect_type_rule = merged_tool("set_niagara_effect_type_rule", {
    "scalar": set_niagara_effect_type_rule_scalar,
    "enum": set_niagara_effect_type_rule_enum,
})
set_niagara_validation_rule = merged_tool("set_niagara_validation_rule", {
    "text": set_niagara_validation_rule_text,
    "string_array": set_niagara_validation_rule_string_array,
})
set_niagara_effect_type_scalability = merged_tool("set_niagara_effect_type_scalability", {
    "scalar": set_niagara_effect_type_scalability_scalar,
    "enum": set_niagara_effect_type_scalability_enum,
})
