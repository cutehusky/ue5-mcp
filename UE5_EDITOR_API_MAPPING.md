# UE 5.7 editor API mapping

This mapping is based on public headers under `C:/Programs/Unreal/UE_5.7/Engine/Source`.

| UE API header | MCP capability | Current route/status |
|---|---|---|
| `UnrealEd/Public/Subsystems/EditorAssetSubsystem.h` | List, save, duplicate, rename, delete, referencers | `/assets/list`, `/assets/save`, `/assets/duplicate`, `/assets/rename`, `/assets/delete`, `/assets/referencers` |
| `MaterialEditor/Public/MaterialEditingLibrary.h` | Material expression CRUD, links, recompilation, layout | `/materials/expressions`, `/materials/expressions/connect`, `/materials/layout` |
| `StaticMeshEditor/Public/StaticMeshEditorSubsystem.h` | LOD screen sizes, LOD groups, lightmap UVs, CPU access | `/static-meshes/lod-screen-sizes`, `/static-meshes/lod-group`, `/static-meshes/settings` |
| `SkeletalMeshEditor/Public/SkeletalMeshEditorSubsystem.h` | Skeletal section flags and material slots | `/skeletal-meshes/sections`, `/skeletal-meshes/materials` |
| `AnimationBlueprintLibrary/Public/AnimationBlueprintLibrary.h` | Notify tracks/events, float/vector curve keys, sync markers, montage sections | `/animations/notifies`, `/animations/curves`, `/animations/montage-sections` |
| `BlueprintEditorLibrary/Public/BlueprintEditorLibrary.h` | Blueprint cleanup, variable exposure, reparenting, editor refresh | Partially mapped; next phase |
| `UnrealEd/Public/Subsystems/EditorActorSubsystem.h` | List, spawn, duplicate, delete, and select level actors | `/editor/actors`, `/editor/actors/spawn`, `/editor/actors/duplicate`, `/editor/actors/select`, `/editor/actors/select-all`, `/editor/actors/clear-selection`, `DELETE /editor/actors` |
| `UnrealEd/Public/Subsystems/AssetEditorSubsystem.h` | Open, close, focus, and inspect asset editors | `/editor/assets/status`, `/editor/assets/open`, `/editor/assets/focus`, `DELETE /editor/assets` |
| `UnrealEd/Public/Subsystems/UnrealEditorSubsystem.h` | Current world, editor selection, map/editor state, viewport camera | `/editor/status`, `/editor/viewport` |
| `EditorFramework/Public/Subsystems/PlacementSubsystem.h` | Editor placement and actor factory workflows | Not yet mapped |
| `UMG/Public/Blueprint/WidgetTree.h` and `UMG/Public/Components/PanelWidget.h` | Add, remove, reparent, inspect, and property-edit Widget Blueprint widgets | `/widget-blueprints/widgets`, `/widget-blueprints/widgets/properties`, `/widget-blueprints/widgets/reparent` |
| `UnrealEd/Public/Subsystems/UnrealEditorSubsystem.h` | Current editor world, game world, editor context, and viewport camera | `/editor/status`, `/editor/viewport` |
| `UnrealEd/Public/Kismet2/DebuggerCommands.h` | Start, pause, resume, stop, and query Play-in-Editor sessions | `/editor/play`, `/editor/status` |
| `UnrealEd/Classes/Editor/EditorEngine.h` | Global editor undo and redo | `/editor/transactions/undo`, `/editor/transactions/redo` |
| `LevelSequence/Public/LevelSequence.h` and `MovieScene/Public/MovieScene.h` | Level Sequence creation, settings, bindings, tracks, and range validation | `/level-sequences/inspect`, `/level-sequences/create`, `/level-sequences/settings`, `/level-sequences/bindings`, `/level-sequences/tracks`, `/level-sequences/validate` |
| `CoreUObject/Public/UObject/UObjectIterator.h` and `UnrealType.h` | Loaded class, function, property, metadata, and Blueprint capability discovery | `/ue/classes`, `/ue/classes/describe`, `/ue/blueprint-functions` |

## Remaining high-value mappings

1. `BlueprintEditorLibrary`: unused-node cleanup, variable exposure flags, graph refresh, and reparenting.
2. `EditorFramework/Public/Subsystems/PlacementSubsystem.h`: editor placement and actor-factory workflows.
3. `StaticMeshEditorSubsystem`: mesh build settings, Nanite source, vertex colors, and LOD import.
4. `AnimationBlueprintLibrary`: metadata, pose extraction, and virtual bones.
5. `MaterialEditingLibrary`: material usage flags, parameter sources, statistics, and material-function graphs.
6. `WidgetBlueprintLibrary` and `WidgetTree`: additional layout and design-time editing.

Destructive operations such as asset deletion and actor deletion should remain explicit MCP tools with clear warnings and, where possible, transaction/undo support.

## Editor status and live UE documentation

The reflection documentation endpoints query the running editor and therefore
describe the current engine/plugin load state:

- `/editor/status` returns engine version, project name, platform, editor/game
  worlds, map name, play/pause/running flags, and selected actor count.
- `/editor/selection` returns selected actor names, object paths, and classes.
- `/editor/viewport` gets or sets the active level viewport camera.
- `/editor/play` accepts only `start`, `pause`, `resume`, or `stop`; starting
  uses the active viewport location, and each action validates the current
  play state before it is applied.
- `/editor/transactions/undo` and `/editor/transactions/redo` expose the
  editor's transaction history, allowing MCP-driven mutations to be recovered
  using the same undo stack as interactive edits.
- `/editor/actors` lists current-world actors; spawn, selection, duplication, and explicit confirmation-protected deletion are available.
- `/editor/assets/status`, `/editor/assets/open`, `/editor/assets/focus`, and `DELETE /editor/assets` control asset-editor windows.
- `/ue/classes` searches loaded classes by name, parent class, Blueprint support,
  and abstract status.
- `/ue/classes/describe` returns class metadata, inherited functions, properties,
  C++ types, Blueprint read/write flags, and tooltips.
- `/ue/blueprint-functions` lists Blueprint-callable, pure, and event functions
  for a selected class, including parameter metadata.

These are reflection-backed discovery tools, not a replacement for the full
Unreal documentation site. Unloaded modules and classes are intentionally not
invented or scraped from disk.

## Audited implementation status

The following is the source-of-truth route inventory for the current checkout.

| Feature | Current routes | Status |
|---|---|---|
| Shared assets | `/assets/capabilities`, `/assets/validate`, `/assets/preview-operation`, `/assets/batch`, `/assets/dirty-state`, `/assets/save-all-selected` | Partial; batch currently accepts one operation request |
| Texture | `/textures/inspect`, `/textures/settings`, `/textures/platform-settings`, `/textures/rebuild`, `/textures/refresh`, `/textures/validate` | Partial; reflected property editing |
| Material | `/materials/inspect`, `/materials/settings`, `/materials/compile`, `/materials/validate`, existing parameter/expression/layout routes | Partial |
| Material Instance | `/material-instances/inspect`, `/material-instances/settings`, existing `/materials/parameters` | Partial |
| Animation Sequence | `/animation-sequences/inspect`, `/animation-sequences/settings`, `/animation-sequences/tracks`, `/animation-sequences/validate`, existing `/animations/*` | Partial |
| Animation Blueprint | `/animation-blueprints/inspect`, `/animation-blueprints/settings`, `/animation-blueprints/graphs`, `/animation-blueprints/compile` | Partial |
| Blend Space | `/blend-spaces/inspect`, `/blend-spaces/samples`, `/blend-spaces/validate` | Partial |
| Physics Asset | `/physics-assets/inspect`, `/physics-assets/bodies` | Inspection only |
| Control Rig | `/control-rigs/inspect`, `/control-rigs/properties` | Generic property support only |
| Modular Rig | `/modular-rigs/inspect`, `/modular-rigs/properties` | Generic property support only |
| Live editor control | `/editor/viewport`, `/editor/play`, `/editor/transactions/*`, `/editor/actors*`, `/editor/assets/*` | Implemented for current subsystem surface; destructive operations require confirmation |

## Property mapping audit

Property mutation is centralized in `Core/ObjUtils.cpp` and delegates value
parsing to UE 5.7 `FProperty::ImportText_Direct`. This covers all property
classes that UE’s native importer can parse, including numeric types, enums,
structs, hard/soft/class references, arrays, sets, maps, and optional or
engine/plugin-specific property classes that inherit the standard importer.

Serialization emits typed JSON for primitive values, enums, object paths,
structs, arrays, sets, and maps. Unsupported editor delegate-like properties
fall back to UE text export and should not be treated as writable without a
dedicated adapter.

Known path constraints:

- Property names are case-insensitive.
- Array paths use dot-separated numeric indexes, for example `Values.2`.
- Array indexes must already exist; editing does not resize arrays.
- Nested object editing requires a non-null existing object.
- Complete map/set replacement is supported through UE text import; typed
  key-level map operations are not exposed as REST DTOs yet.
