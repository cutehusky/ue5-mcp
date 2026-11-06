# UE5MCP Implementation Plan — Outstanding Work

Only unimplemented or partially implemented features are listed here. Descriptions
of implemented work are in [IMPLEMENTED_FEATURES.md](IMPLEMENTED_FEATURES.md);
implemented-but-unverified work is tracked in [UNTESTED_FEATURES.md](UNTESTED_FEATURES.md).

Priority: implement remaining features first; defer testing. Record each new
feature in IMPLEMENTED_FEATURES.md and UNTESTED_FEATURES.md, then remove it here.

## Rules for new work

- Follow the common API contract (dry_run, confirm, exact snapshot guards, transactions,
  dirty-on-success, save only on request); see IMPLEMENTED_FEATURES.md "Common API contract".
- Report unsupported optional engine plugins as unavailable, never as implemented.
- Console commands go through `execute_console_command` only: confirmation required, and no quit, crash or Python commands.
- Capability matrix must not report a family as fully implemented from generic property access.

## Next up: making a game from an empty project

Reviewed 2026-11-04 against the tool list. Work top-down; everything after this section is lower priority.

1. **Tidy up.** Remove the duplicate `start_play_in_editor` and `stop_play_in_editor` once tests move to
   `control_ue_play_session`. Try the tool list in a real client such as Claude Desktop or Cursor.

## Areas with no implementation yet

- **UI / CommonUI**: activatable widget stacks, CommonUI input actions/routing validation,
  styles/themes, widget design-time layout tooling, property bindings, named slots.
  (Widget animations: basic list/create/rename/delete/range exist; track/key authoring missing.)
- **Controlled Python execution** (allowlisted scripts only) and command/menu registration inspection.
- **Material Layers / Layer Blends** authoring; shader statistics/compile diagnostics.
- **Debugging**: network emulation, replay controls.
- **Build and delivery**: non-Win64 packaging and launch, shader/DDC status,
  device deployment, crash-report collection.
- **Collaboration**: changelists, checkout-enabled provider verification, revision download/diff/sync,
  multi-user session state.
- **Mass Entity** tooling.
- **Geometry**: Modeling Tools.
- **Import**: FBX and Skeletal Mesh reimport; import options beyond `import_fbx` (scale, LODs, morph targets, animation
  range); skeletal glTF; broader scene reimport/texture dependencies; other source formats.

## Partially implemented — remaining scope

### Shared contract
- Dedicated transaction response metadata.
- Atomic (non-ordered) asset batching; nested object-reference traversal in batches.

### Content Browser and assets
- Migrate, collections, broader redirector fix-up workflows.
- Texture: larger/custom-format render-target mutations, explicit derived-data/pixel workflows.

### World building
- Complete world/level adapters; remaining World Settings families.
- World Partition cells and external-actor persistence (incl. partition navigation/volume mutations).
- Level Instance packing, property overrides, complex moved-package commits.
- Landscape, foliage, splines, volumes, lighting, reflection captures, post-process: deepen typed coverage.
- Navigation: broader collision/area and smart-link authoring, custom/inherited filter and area-base
  adapters, additional agents, PIE queries; volume experimental resolution/fill-underneath, arbitrary shapes.

### Materials
- Complete typed Material APIs and material-instance settings.
- Complete unloaded name-based dependency analysis; broad shader/graph compatibility.

### Animation, rigs, physics
- Full Animation Sequence authoring.
- Physics Asset authoring remainder.
- Wider RigVM node families; Control Rig typed settings remainder; Modular Rig authoring remainder.
- IK Retargeter, Pose Search / Motion Matching depth, skeletal sockets and virtual bones depth.

### VFX
- Niagara: systems, emitters, modules, parameters, simulations, renderers, validation — extend existing utilities.

### Audio
- Advanced Audio Component properties; plugin-specific typed parameters;
  hardware-voice summaries and CPU/DSP trace analysis.

### Gameplay and AI
- StateTree: reference/container parameter runtime combinations, nested container parameters,
  nested node containers and instanced UObject settings, node reference containers,
  broader schema/context configuration, runtime events/parameter changes,
  transition-condition/consideration expression runtime combinations.
- Behavior Tree: specialized nodes/providers, dynamic runtime substitution,
  Blueprint-derived subtree tasks, large/deep dependency boundaries.
- EQS: custom providers, test-class migration, forced/mixed composite item layouts,
  async composite execution, incremental inner-generator editing, Blueprint node/context
  runtime gates, broader navigation/trace generators/tests.
- Smart Objects: behavior definitions, world conditions, annotations, placed components.
- Game Features: descriptor/initial-state/actions editing.

### Cinematics
- Other track combinations and specialized tracks/channels; camera animation/layout.
- Sequencer director endpoint body authoring; full runtime/cook/graph compatibility.
- Take Recorder: source-list creation/source authoring and custom configuration, presets, recording start/stop. Basic source-list inspection is implemented but unverified.

### Debugging and quality
- Output Log streaming (`get_editor_logs` only reads on request); deeper runtime actor inspection.

## Deferred verification

See UNTESTED_FEATURES.md "Deferred verification sequence". Testing in IMPLEMENTED_FEATURES.md
"Testing" section describes the required per-family checks.

