# Untested features

Implemented tools that no passing live test fully covers yet. An entry is removed as soon as a test covers it; what was
verified, and how, is in VERIFICATION_REPORT_2026-10-25.md and VERIFICATION_REPORT_2026-10-30.md. Fully verified work
is listed in IMPLEMENTED_FEATURES.md.

The editor target builds on UE 5.7.1. Each entry gives one current status:

- **Not run:** no test exercises it yet.
- **Partial:** part of the behaviour is verified; the rest is named.
- **Blocked:** the engine or project lacks something the test needs; the blocker is named.

Last cleaned up 2026-11-03: 60 entries (sibling tools with the same blocker share an entry).

## StateTree

- [ ] **Typed schema containers**: `SchemaContainers` in schema settings (`edit_state_tree_schema`). **Blocked:** no
  engine or plugin schema has an editable container field; a container edit on a reference field is refused. Schema
  references are verified (smoke_state_tree_batch_live.py).

## AI Perception and Gameplay Tags (runtime)

- [ ] **AI Perception config diagnostics**: inspector errors/warnings for duplicate senses, invalid ranges/ages, sight
  angle, dominant-sense coverage and disabled affiliations. **Partial** (smoke_pie_perception_live.py): valid configs
  report no issues; invalid configurations were not induced.
- [ ] **Runtime Gameplay Tag interface inspection** (`inspect_runtime_gameplay_tags`): PIE actors implementing
  `IGameplayTagAssetInterface`. **Blocked:** no engine or project actor implements the interface at actor level.
  Component providers (the ASC) are verified.
- [ ] **Live actor GameplayTagQuery evaluation** (`evaluate_runtime_gameplay_tag_query`). **Blocked:** same as above;
  provider-path evaluation on an ASC is verified.

## Gameplay Ability System

- [ ] **Modifier evaluation channels**: evaluation channel and capture final channel on typed modifiers. **Partial**
  (smoke_gas_authoring_live.py): channel 0 accepted and an invalid channel refused; the project leaves channels
  disabled, so aliases and multi-channel aggregation are untested.
- [ ] **Component tag fields/readback**: scalar tag/container fields on effect components. **Partial**: inherited
  Added tags reload after a cold restart. The scalar half is **blocked**: every 5.7 effect component stores tags as
  inherited containers, so none has a scalar tag or container field for `TagProperties`.
- [ ] **Component direct tag queries**: editable query fields on effect components (`Queries`). **Blocked:** no 5.7
  effect component has a scalar FGameplayTagQuery field (Immunity and RemoveOther use arrays of FGameplayEffectQuery).
- [ ] **Component class references**: hard class references on effect components. **Blocked:** no 5.7 effect
  component has a scalar TSubclassOf field.
- [ ] **Blueprint `SoftObjectReferences`**: soft asset references in GAS Blueprint defaults. **Blocked:** no 5.7 GAS
  ability, effect, calculation or cue class exposes a soft object field.
- [ ] **Blueprint `SoftClassReferences`**: soft class references in GAS Blueprint defaults. **Blocked:** no 5.7 GAS
  class exposes a soft class field.

## Skeleton, animation curves and IK rigs

- [ ] **Skeleton edits at runtime and edge cases**: effects on retargeted playback, blend-profile blending and
  compatible-skeleton evaluation; Persona preview refresh; Anim Blueprint consumers of renamed sources and profiles;
  zero/negative socket scales; case-only renames; multiple preview entries per target. **Not run.**
- [ ] **Virtual-bone target-dependency rename**. **Blocked:** the engine crashes on a virtual-bone *target*, so
  creation now refuses one (smoke_skeleton_pair_live.py); only pre-existing assets could hold such a dependency.
  Source-dependency renames are verified.
- [ ] **Skeleton structural diagnostics** (in `inspect_skeleton_structure`). **Partial:** clean structures report
  `structurally_valid` with no issues; malformed structures were not induced.
- [ ] **Skeleton reference-pose readback**. **Partial:** finite local and component-space transforms on the Mannequin;
  negative/nonuniform scale and truncation not exercised.
- [ ] **Skeleton hierarchy comparison** (`compare_skeleton_hierarchies`). **Partial:** identical hierarchies (161
  shared bones, no differences) and a missing source; mismatched hierarchies not compared.
- [ ] **Transform channel extrapolation**. **Blocked:** UE 5.7's sequencer controller only applies curve attributes to
  float curves, so the route refuses (dry runs included) until a different native path exists.
- [ ] **Source curve structural diagnostics** (`inspect_animation_curve_diagnostics`). **Partial**
  (smoke_animation_curves_deep_live.py): clean curves report valid; NaN, bad-mode and outside-duration issues not
  induced.
- [ ] **IK/retarget name and string settings** (`set_ik_settings_text_value`). **Partial:** FName edits verified with
  a cold reload; no engine settings field is an FString, so the string kind is untested.
- [ ] **IK/retarget numeric-array settings** (`set_ik_settings_number_list`). **Blocked:** no engine solver/op settings
  field is a numeric array; only rejection on a name array is verified.
- [ ] **IK definition structural diagnostics**. **Partial:** clean rigs verified; malformed-definition issues not
  induced.
- [ ] **Retarget pose diagnostics**. **Partial:** clean retargeters verified; missing/nonfinite pose issues not
  induced.
- [ ] **Temporary retarget initialization failure** response (`processor_initialized=false`). **Partial:** success
  reports `evaluated=true`; the failure path was not induced.
- [ ] **Retarget export partial results** (missing/wrong-skeleton/failed-save lists). **Partial:** the success path is
  verified; partial failures not induced.
- [ ] **Temporary IK stored-goal preflight** (rejecting malformed stored goals). **Partial:** valid goals pass; the
  rejection path was not induced.

## Pose Search

- [ ] **Motion-matching runtime and derived index**: search results, runtime selection, PIE playback, index staleness
  and quality after edits. **Not run.**
- [ ] **Role mirror table authoring**. **Blocked:** no MirrorDataTable exists and none can be scripted
  (`MirrorDataTableFactory` sets its skeleton only through a dialog; `DataTableFactory` refuses the subclass).
- [ ] **Entry mirror-policy authoring**. **Blocked:** needs a MirrorDataTable (as above).
- [ ] **Mirrored interaction warp evaluation**. **Blocked:** needs a MirrorDataTable; only a missing-table refusal is
  verified.
- [ ] **Composite insertion**. **Blocked:** no AnimComposite can be scripted (`AnimCompositeFactory` exposes no
  skeleton or source). Montage insertion is verified.
- [ ] **Composite sampling intervals**. **Blocked:** as above; montage intervals are verified.
- [ ] **Authored configuration diagnostics**. **Partial:** clean databases verified; individual issue codes not induced.
- [ ] **Channel vector-field authoring**. **Blocked:** no engine channel has an FVector leaf; only rejection is verified.
- [ ] **Vector/color field default reset**. **Partial:** FLinearColor reset verified; no channel has an FVector leaf.

## Niagara

- [ ] **Renderer linear-color authoring**. **Blocked:** no engine renderer exposes an FLinearColor leaf; only rejection
  verified.
- [ ] **Renderer vector/color default reset**. **Partial:** FVector and FName reset verified with a cold reload;
  FLinearColor blocked as above.
- [ ] **Input consistency diagnostics** (same-name input conflicts). **Blocked:** the routes refuse a second same-name
  input, so a conflict cannot be built; clean validation is verified.
- [ ] **Repeated-input exposure/priority synchronization**. **Blocked:** as above; single-definition edits are verified.
- [ ] **Emitter module vector/color pin defaults**. **Blocked:** stock modules expose vector/color inputs as
  rapid-iteration parameters, not function-call pins.
- [ ] **System module vector/color pin defaults**. **Blocked:** stock system modules have no unlinked vector/color
  pins. The scalar half is verified.
- [ ] **Validation rule name/asset, vector/color, string/text and name/string-array fields** (four tools).
  **Blocked:** the only string fields in 5.7 rule classes sit inside array elements, which these routes do not
  traverse; no rule has such a leaf.

## Geometry Script and splines

- [ ] **Static Mesh LOD extraction** (`CopyMeshFromStaticMeshV2`). **Partial:** LOD0 from SourceModel and RenderData
  verified with a cold reload; LOD1–7 and missing-LOD refusal not exercised (needs a mesh with LODs).
- [ ] **Writing existing Static Mesh LODs** (`CopyMeshToStaticMesh`). **Partial:** LOD0 write and reload verified;
  LOD1–7 and recompute/lightmap option variants not exercised.
- [ ] **Spline closing input key** (`set_spline_closing_key`). **Partial:** accepted with dry-run/no-change checks and
  bad keys refused; the inspectors do not expose the closing key, so the stored value is not read back.
- [ ] **Restore automatic spline closing key** (`reset_spline_closing_key`). **Partial:** as above.

## World Partition, HLOD, audio, decals and render targets

- [ ] **Runtime-cell inspection, cell detail, cell contents and cell mappings** (four tools). **Blocked:** the editor
  runtime hash generates no streaming cells without PIE or cook; enumeration returns an empty page and per-cell routes
  refuse unknown cells. PIE is now available, but these routes require a stopped editor.
- [ ] **HLOD builder string, name and int64 leaves** (three tools). **Blocked:** no engine HLOD builder settings have
  such leaves; only refusal is verified.
- [ ] **Name-dependent partition actor Data Layer moves**. **Blocked:** no actor whose package depends on its
  membership was available; ordinary actors are correctly refused.
- [ ] **SpatialHash grid-info contributions**. **Partial:** the SpatialHash fixture map exists, but no route creates
  grid-info actors, so only the empty page is verified.
- [ ] **Legacy HLOD hard reference, FName, FString and linear-color leaves** (four tools). **Blocked:** none of the
  279 local HLOD leaves has these types (the only color is an FColor); only refusal verified.
- [ ] **Legacy LOD actor dependency discovery**. **Blocked:** no route builds legacy HLOD clusters, so no ALODActor
  exists; the empty listing and refusals are verified.
- [ ] **World Settings default reverb plugin effect** (`ReverbPluginEffect`). **Blocked:** no reverb plugin asset in
  the project. ReverbEffect and DefaultBaseSoundMix are verified.
- [ ] **AudioVolume reverb plugin effect**. **Blocked:** as above; ReverbEffect is verified.
- [ ] **Decal mobility propagation to children**. **Partial:** root mobility edits persist; propagation is unobserved
  because the decal's native children are already Movable and nothing can make them non-movable.
- [ ] **Float16 volume render-target DDS export**. **Partial:** 2D, cube and 2D-array DDS exports verified on a GPU
  editor; non-float16 volumes are refused; a float16 volume export is untested.

## Sequencer, Take Recorder and editor extensions

- [ ] **Sequencer folder structural validation**. **Partial:** clean trees verified before and after a cold reload;
  malformed-tree diagnostics not induced.
- [ ] **Take Recorder preset origin** (`PresetOrigin`). **Blocked:** no TakePreset asset exists and none can be
  scripted. Timestamp and level origin are verified.
- [ ] **Take Recorder source-list inspection**. **Blocked:** no route creates a source list, and recording needs the
  Take Recorder UI and a renderer; only the empty result is verified.
- [ ] **Widget animations and asset consolidation edge cases**: Delete/Rename of graph-referenced widget animations
  and consolidation redirector fallout. **Not run.** Game Features, Smart Objects and Editor Utilities are verified.

- [ ] **Remote Control Preset edge cases**: multi-object bindings, asset-bound (non-actor) fields, nested struct paths.
  **Partial** (smoke_remote_control_live.py): single-actor-component properties and an actor function are verified;
  undo of expose/unexpose is not. Calling exposed functions, exposed actors and protocol bindings are not implemented.

- [ ] **Game core edge cases**: `cancel_package`, Shipping/DebugGame packaging, axis input, propagating class defaults to loaded child Blueprints. **Not run** (child propagation is not implemented).

## How remaining entries can be unblocked

- **Fixtures:** `Verification/fixtures/create_fixtures.py` creates test assets with the editor stopped (pythonscript
  commandlet). A MirrorDataTable, AnimComposite or TakePreset cannot be scripted in 5.7 and would need an asset made by
  hand in the editor.
- **PIE:** `POST /editor/pie/start` and `/editor/pie/stop` run Play-In-Editor headless; poll `/editor/status` for
  `is_playing`.
- **GPU readback:** start the editor with `-RenderOffscreen` instead of `-nullrhi`.
- **Engine data:** entries blocked on missing field types (Niagara, HLOD, Pose Search vectors) only become testable with
  custom classes that expose those fields.

## Remaining implementation

Nested container parameters; nested node containers and instanced UObject settings; broader schema/context
configuration; other domains listed in IMPLEMENTATION_PLAN.md.
