# UE5 Editor Tool Design

## Purpose

This design expands UE5_MCP from asset-specific helpers into a complete,
module-gated editor automation surface. “Complete” means the tool can discover
and safely control the principal UE5 editor workflows; optional engine plugins
are reported as unavailable rather than emulated or silently ignored.

**Status legend:** **Implemented** means the listed workflow has a dedicated
route and MCP wrapper; **Partial** means only a limited or generic slice is
available; **Missing** means no dedicated implementation exists. Statuses were
audited against the current route registration and Python MCP wrapper source.

## Common Tool Contract

**Status: Partial.** Every typed mutation should accept the following common fields in addition to its
family-specific fields:

```json
{
  "asset_path": "/Game/Example.Asset",
  "operation": "create|update|delete|validate|compile|rebuild",
  "dry_run": false,
  "save": false,
  "transaction": "Descriptive editor undo label",
  "confirmation_token": "required for destructive operations"
}
```

Every response returns `success`, `changed`, `dirty`, `saved`, `warnings`,
`errors`, `validation`, and `transaction`. `dry_run=true` must not mutate;
destructive previews return a single-use, asset-and-operation-bound
`confirmation_token`. All mutations run in an editor transaction, mark the
owning package dirty only after success, and save only when `save=true`.

`GET /editor/capabilities` reports each family’s module availability and the
supported levels: `inspect`, `edit`, `create`, `compile_or_rebuild`, and
`validate`.

## Core Editor Tool Families

| Family | Status | REST routes | MCP tools | Key behavior |
|---|---|---|---|---|
| Map and world | **Partial** — current-world inspect/save only | `/worlds/list`, `/worlds/create`, `/worlds/load`, `/worlds/save`, `/worlds/settings`, `/worlds/validate` | `list_maps`, `create_map`, `load_map`, `edit_world_settings`, `validate_map` | Map transition previews dirty packages and needs confirmation when work would be discarded. |
| Scene and components | **Partial** — actor spawn/edit exists; component/query tools are absent | `/scene/actors/query`, `/scene/actors/components`, `/scene/actors/components/properties`, `/scene/actors/tags` | `query_actors`, `list_actor_components`, `edit_actor_components`, `set_actor_tags` | Deterministic filtering by class, tag, folder, level, and bounds; component deletion previews attachments. |
| World Partition | **Missing** | `/worlds/partition`, `/worlds/data-layers`, `/levels/sublevels`, `/levels/visibility`, `/level-instances` | `inspect_world_partition`, `edit_data_layers`, `edit_sublevels`, `edit_level_instance` | Public APIs only; mutations return affected actors/packages. |
| Content Browser | **Partial** — generic asset operations and asset-editor windows exist | `/editor/assets/import`, `/editor/assets/reimport`, `/editor/assets/migrate`, `/editor/assets/consolidate`, `/editor/assets/select`, `/editor/assets/reveal`, `/editor/assets/fixup-redirectors` | `import_asset`, `reimport_asset`, `migrate_assets`, `consolidate_assets`, `select_assets`, `reveal_asset` | Validates source paths and destination policy; consolidate/migrate/fixup always require preview and confirmation. |
| Placement | **Partial** — generic actor/asset spawn exists | `/editor/placement`, `/editor/placement/classes`, `/editor/placement/factories` | `place_actor`, `list_placeable_classes`, `list_actor_factories` | Uses actor factories for meshes, Blueprints, lights, cameras, decals, volumes, foliage, and assets. |
| PIE and debugging | **Partial** — lifecycle/status/viewport/undo-redo exist | `/editor/play`, `/editor/logs`, `/editor/map-check`, `/editor/automation`, `/editor/screenshots`, `/editor/runtime-world` | `control_play_session`, `read_output_log`, `run_map_check`, `run_automation_tests`, `capture_editor_screenshot`, `inspect_pie_world` | Clearly identifies editor versus PIE world; test runs return IDs and pollable results. |
| Build and delivery | **Missing** | `/editor/compile`, `/editor/build-status`, `/editor/cook`, `/editor/package`, `/editor/launch`, `/editor/derived-data` | `compile_project`, `get_build_status`, `cook_project`, `package_project`, `launch_on_device` | Long-running jobs return IDs, state, logs, diagnostics, and artifacts; no claim of hot-reload success before completion. |
| Source control | **Missing** | `/editor/source-control/status`, `/checkout`, `/add`, `/revert`, `/submit` | `source_control_status`, `checkout_files`, `submit_changes` | Available only when a UE source-control provider is connected; submit/revert require confirmation. |

## Specialized Authoring Families

| Family | Status | REST routes | Required support |
|---|---|---|---|
| Landscape, Foliage, and Spline | **Missing** | `/landscapes/*`, `/foliage/*`, `/splines/*` | Inspect/create/edit components, layers, instances, points, and validation. Destructive bulk edits require a count-and-impact preview. |
| PCG and Geometry | **Missing** | `/pcg/*`, `/geometry/*`, `/modeling/*` | PCG graph/component parameters and generation; geometry/modeling actions must run as explicit transactions and report generated assets. |
| Niagara | **Missing** | `/niagara/systems`, `/niagara/emitters`, `/niagara/parameters`, `/niagara/compile`, `/niagara/validate` | System/emitter graph inspection, parameter editing, compile diagnostics, and validation. |
| Materials and textures | **Partial** — Material graph/settings and texture settings/rebuild exist | `/material-functions/*`, `/material-parameter-collections/*`, `/textures/import`, `/textures/mips`, `/textures/statistics`, `/render-targets/*`, `/virtual-textures/*` | Typed material-function and collection editing, source/mip diagnostics, specialized texture families, and shader statistics. |
| Animation and rigging | **Partial** — animation routes exist; physics and rig authoring do not | `/physics-assets/*`, `/control-rigs/*`, `/modular-rigs/*`, `/ik-retargeters/*`, `/pose-search/*`, `/skeletal-meshes/sockets`, `/skeletal-meshes/virtual-bones` | Public controller APIs for physics bodies/constraints, RigVM graphs, rig modules/connectors, retargeting, and animation metadata. |
| VFX and audio | **Partial** — core audio inspect/settings exist; VFX and graph authoring do not | `/metasounds/*`, `/sound-cues/*`, `/audio/profiling`, `/audio/import` | Typed graph authoring, source/reimport controls, compiler diagnostics, and profiling data. |
| UI | **Partial** — Widget-tree CRUD/property editing exists | `/widget-blueprints/layout`, `/widget-blueprints/bindings`, `/widget-blueprints/animations`, `/common-ui/*` | Design-time layout, bindings, animation, named slots, CommonUI stacks/actions, and input validation. |
| Gameplay and AI | **Partial** — Blueprint, Input, Behavior Tree, and Blackboard slices exist | `/state-trees/*`, `/environment-queries/*`, `/ai-perception/*`, `/gameplay-abilities/*`, `/gameplay-tags/*`, `/game-features/*`, `/smart-objects/*`, `/mass/*` | Module-gated asset/component control, graph validation, and explicit unsupported responses when plugins are disabled. |
| Cinematics | **Partial** — Level Sequence read/settings support exists | `/level-sequences/bindings`, `/tracks`, `/sections`, `/keys`, `/subsequences`, `/cinematic/cameras`, `/camera-cuts`, `/shots`, `/takes` | Typed authoring for common tracks/channels, cameras, shots, and recordings; destructive binding/track/section changes are previewed. |

## Module and Job Architecture

**Status: Missing.**

- Implement each family as an editor-only adapter with a matching capability
  provider and Python MCP wrapper module.
- Load optional UE modules dynamically and expose their availability through
  `/editor/capabilities`; no optional route is registered as functional unless
  its module and public APIs are present.
- Use a shared job manager for Automation, compile, cook, package, launch,
  screenshot, generation, and other long-running work. Jobs expose
  `queued`, `running`, `succeeded`, `failed`, and `cancelled` states plus
  timestamps, logs, diagnostics, and output paths.
- Keep the current HTTP API as the transport. Python MCP tools are thin,
  typed wrappers that return the native structured result without duplicating
  editor logic.

## Security and Safety Rules

**Status: Partial.** Actor and asset-editor deletion use boolean confirmation,
and several property routes support dry-run. The common transaction metadata,
affected-reference previews, confirmation tokens, route-wide validation, and
allowlisted diagnostics layer remain to be implemented.

- Never expose unrestricted console commands, arbitrary editor Python, shell
  execution, file deletion, source-control submit/revert, or packaging actions.
- Provide narrowly scoped diagnostic commands only through an explicit
  allowlist; reject map loads, script execution, configuration changes, and
  unbounded mutations through that channel.
- Require preview plus confirmation for destructive asset, world, scene,
  source-control, and bulk operations. Include affected references, actor
  count, dirty packages, and intended files in the preview.
- All routes must validate asset class, module availability, editor/PIE state,
  and property compatibility before mutation.

## Delivery Order

1. Shared contract, capability matrix, jobs, map lifecycle, scene components,
   Content Browser synchronization, PIE diagnostics, and Map Check.
2. World Partition/Data Layers/Level Instances, import/reimport, source
   control, build/cook/package jobs, and asset auditing.
3. Physics/rigging, Sequencer authoring, Landscape/Foliage/Spline, PCG,
   Niagara, and advanced animation.
4. MetaSound, CommonUI, StateTree/EQS/GAS/Game Features, Smart Objects/Mass,
   device deployment, and controlled editor-extensibility integrations.

Every delivery stage must add route registration tests, Python wrapper tests,
live-editor acceptance tests, dry-run/confirmation tests, and save/reload plus
undo/redo verification.
