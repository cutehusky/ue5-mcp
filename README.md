# UE5 MCP

An Unreal Engine 5 editor plugin and a Python [MCP](https://modelcontextprotocol.io) server that let AI agents build and inspect Unreal projects: Blueprints, assets, levels, animation, AI, audio, VFX, cinematics, playtesting, and packaging.

```text
MCP client  --streamable HTTP-->  Python server (FastMCP)  --REST-->  UE5_MCP plugin  -->  Unreal Editor
            http://localhost:9000/mcp                     http://localhost:<api port>
```

## Requirements

* Unreal Engine 5.7. The editor target is built and tested on 5.7.1.
* A toolchain that can compile editor plugins, because the plugin ships as source. Development and testing happen on Windows, and the commands below use Windows paths.
* Python 3.10 to 3.13. Python 3.14 is excluded by `pyproject.toml` because the MCP dependency may not support it yet.

The engine plugins this one depends on, such as Niagara, PCG, StateTree, and GameplayAbilities, are listed in `UE5_MCP.uplugin` and enabled with it.

## Installation

For the full guide, including client setup and troubleshooting, see [INSTALL.md](INSTALL.md). AI agents can follow [AGENT_INSTALL.md](AGENT_INSTALL.md).

1. Clone the repository into your project's `Plugins` folder:

   ```bash
   cd <YourUEProject>/Plugins
   git clone https://github.com/cutehusky/ue5-mcp.git UE5_MCP
   ```

2. Open the project, let Unreal build the plugin, and check that **UE5_MCP** is enabled in the **Plugins** tab.

3. Install the MCP server:

   ```bash
   cd UE5_MCP/Python/MCP
   python -m venv .venv
   .venv/Scripts/python -m pip install --upgrade pip
   .venv/Scripts/python -m pip install -e .
   ```

   Run directly, `mcp_server.py` also sets itself up. It reuses `.venv` or `.venv-ue311` if either works, otherwise creates `.venv`, then re-launches inside it and installs any missing `httpx`, `mcp`, and `python-dotenv` packages.

   | Variable | Effect |
   |---|---|
   | `UE5_MCP_VENV` | Use this virtual environment directory instead |
   | `UE5_MCP_AUTO_INSTALL=0` | Do not install missing packages |

## Usage

### Start from the editor

1. Open **Window > UE5_MCP**.
2. Set the Python executable (for example `<project>/Plugins/UE5_MCP/Python/MCP/.venv/Scripts/python.exe`), the path to `mcp_server.py`, and the MCP port.
3. Click **Run Python MCP server**. This also starts the Unreal API server if needed and passes both ports to Python, so no `.env` file is required.

To pick the Unreal API port yourself, turn off **Use automatic port allocation**. The Python process stops when the plugin shuts down.

### Start from a terminal

Start the Unreal API server from the tab first, then run:

```bash
.venv/Scripts/python mcp_server.py --port 9000 --ue-api-url http://localhost:8080
```

Instead of passing flags, you can set the values in `Python/MCP/.env`. Flags take priority. The defaults are port `9000` and `http://localhost:8080`.

```env
PORT=9000
UE5_REST_API_URL=http://localhost:8080
```

### Connect a client

Point any MCP client that supports streamable HTTP at `http://localhost:9000/mcp`, using your MCP port.

### Scripting from Python

Scripts can call any tool directly with `from ue5_client import ue`. See the [ue5-python-scripting skill](skills/ue5-python-scripting/SKILL.md) and [FEATURE_MAP.md](FEATURE_MAP.md).

### Finding tools

The server has 1,732 tools, and listing them all costs about 440k tokens. By default, clients see 144: a core game-making set of 141 plus these three catalog tools, which reach everything else.

| Tool | Purpose |
|---|---|
| `find_tools` | Search all tools by keyword or domain |
| `describe_tool` | Get one tool's description and input schema |
| `call_tool` | Run any tool by name |

`TOOLS.md` lists every tool by feature. Start the server with `--all-tools` to list everything. To change the core set, edit `CORE_TOOLS` in `Python/MCP/ue5_tools/catalog.py`.

Some tools cover several related operations or value types, and take a required `variant` argument. For example, `set_light` takes `variant="scalar"` or `variant="bool"`. Each tool's description lists what every variant requires and accepts. Older tool names are mapped to these in `IMPLEMENTED_FEATURES.md`, under "Merged tools".

### Calling tools

Mutation tools use the asset or Blueprint path first, followed by the operation-specific values. Optional values are omitted or use documented defaults.

Examples:

```python
create_blueprint("/Game/UE5MCP/TestBP", "/Script/Engine.Actor")
create_widget_blueprint("/Game/UE5MCP/TestWidget")
validate_asset("/Game/UE5MCP/TestBP.TestBP", asset_class="Blueprint")
edit_animation_data(variant="edit_animation_curve", asset_path="/Game/Anim.Run.Run", operation="add_sync_marker", curve_name="Foot_L", notify_track="Sync")
create_material_expression("/Game/Materials/M_MCP.M_MCP", "/Script/Engine.MaterialExpressionScalarParameter", expression_name="Speed")
```

DELETE operations that carry JSON bodies are sent with an explicit HTTP DELETE request. `Python/MCP/tests/smoke_bug_report_regression_live.py` keeps these fixes covered.

Valid class names, Blueprint paths, and signature formats are in `common_instruction` in `Python/MCP/ue5_tools/app.py`.

## Coverage

| Area | Tools |
|---|---:|
| Blueprints, widgets, input, data | 62 |
| Assets and meshes | 53 |
| Textures and materials | 245 |
| Animation, rigs, retargeting, Pose Search, physics | 319 |
| Worlds, World Partition, landscape, foliage, splines, volumes, navigation | 353 |
| Lighting, atmosphere, post process, decals | 151 |
| Niagara, PCG, Geometry Script | 310 |
| AI, StateTree, Gameplay Abilities, Gameplay Tags | 125 |
| Audio | 106 |
| Cinematics and Sequencer | 83 |
| Editor control, playtesting, packaging, Remote Control | 37 |
| Tool catalog | 3 |

### Implementation status

Reviewed 2026-11-04 against the UE 5.7 source routes and Python tools. A tool existing does not mean it has been verified: see [UNTESTED_FEATURES.md](UNTESTED_FEATURES.md). [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) is the authoritative list of what is still to do.

| Area | Status | Implemented surface |
|---|---|---|
| Blueprint core | Implemented | Create, compile, functions, variables, components, graphs, pins, layout |
| Widget Blueprint | Implemented | Tree inspection, add/delete, reflected properties, reparent |
| DataTable | Implemented | Row read, upsert, delete |
| Generic assets | Implemented | List, describe, create through engine factories (`create_asset`), properties, save, duplicate, rename, delete, referencers |
| Shared asset foundation | Partial | Per-family capability matrix, validate, preview, dirty-state, save-selected, and ordered non-atomic asset property/save batches with per-operation results |
| Property editing | Implemented with native UE import | Primitive values, enums, structs, arrays, sets, maps, object references, soft/class-compatible native import |
| Material | Partial | Expressions, links, layout, focused domain/blend/shading/two-sided/usage inspection and typed editing, parameter defaults/groups, compile, and shader-status validation when a shader resource is available |
| Material Instance | Partial | Effective parameter/group/override inspection; typed scalar/vector/texture/static-switch/font/runtime-VT edits; parent assignment with cycle checks; full parameter reset including static overrides; missing-parent and orphaned-override validation; reflected settings |
| Texture | Partial | Inspect, reflected settings, platform settings, refresh, resource rebuild, validation; source image diagnostics and guarded local image import, replacement, and reimport |
| Static Mesh | Partial | Materials, LOD screen sizes/groups, lightmap UV, CPU access; source geometry/file diagnostics and guarded OBJ/glTF/GLB import/reimport. glTF imports use a new scene folder and report generated assets; existing meshes use reimport. FBX import through `import_fbx`, without reimport |
| Skeletal Mesh | Implemented for current routes | Materials, section flags, and FBX import through `import_fbx`. Skeletal reimport and glTF remain pending |
| Animation Sequence | Partial | Creation from a Skeleton; source-model timing, bone-track and timeline inspection; paged bone-track keys with add/remove/frame replacement; frame-rate resampling and confirmed duration trim; built-in and registered-struct attribute edits; typed compression edits; notify/curve/sync-marker operations; Skeleton and timeline validation |
| Animation Montage | Implemented for current routes | Sections and existing animation operations |
| Animation Blueprint | Partial | Skeleton/graph/variable summaries; nested state-machine, transition, and pose-link inspection; state and transition lifecycle, entry reassignment, state rename/reset settings, graph layout, typed transition and schema-checked pose-link edits; compile and structural validation |
| Blend Space | Implemented for current routes | Inspect, sample listing/editing with persistent IDs, axis listing/editing, triangulation rebuild, preview weights, and validation for 2D and 1D |
| Physics Asset | Partial | Body and sphere/box/capsule/convex shape editing, convex hull vertex-topology replacement, body settings and Physical Animation profiles, constraints and drives, constraint profiles, collision pairs, refresh, structural validation, and opt-in runtime collision-mesh, body/constraint initialization, bounded simulation up to 600 frames, per-frame stability sampling, and impulse-response checks |
| Control Rig | Partial | Hierarchy editing; scalar, vector, transform, and enum-backed values; per-dimension limits; display/shape/color/visibility settings; animation roles and proxy drivers; available-space management, parent switching with global-transform preservation, and animation-channel hosts; RigVM unit, branch, comment, constant, struct, If, Select, enum, typed array, invoke-entry, free-reroute, injected-unit, and generic template nodes with wildcard-pin resolution; on-pin constant/make/break-struct/reroute insertion with confirmed input replacement; dynamic array-pin add/insert/duplicate/remove/clear/resize; pin display-name, expansion, and watch edits; link-preserving collapse of selected nodes and confirmation-protected expansion; `/control-rigs/templates` and `list_control_rig_templates` list registered template notations; graph readback includes nested pin paths and subpins, pin display/expansion/watch/array state, contained graph paths/counts, native template resolution, fully-unresolved status when a template is registered, wildcard state, event names, pin directions, and injection metadata; structural graph validation with optional VM compilation; function definitions, local variables, getter/setter nodes, input/output pins and references, typed and on-link reroutes, layout, links, and compile |
| Modular Rig | Partial | Module, connector, array-target, config override, and variable binding routes; `/modular-rigs/dependencies` reports module-parent and connector-target edges, variable bindings, config overrides, and unresolved connectors with required/optional status; required-connector validation and recompile |
| World / Level asset | Partial | Map lifecycle plus initial sublevel, World Partition, and Data Layer controls; typed persistent World Settings for gravity/bounds, VR scale, native class overrides, rendering, visibility and nested Lightmass controls, with preflight/dry-run, undo/redo, optional save and cold restart persistence in ordinary/partitioned maps; typed map-owned navigation configs, native system recreation, agent masks/module flags and confirmed disable/restore. The persistent module-config subclass depends on this plugin and preserves false native flags across reload. Ordinary maps also support native box navigation bounds CRUD/undo, confirmed blocking navigation builds, build-state inspection and bounded native projection/path queries with partial-path policy, verified against an obstacle fixture and cold reload. Remaining World Settings families and partition-cell loading remain pending |
| World Partition / levels | Implemented for current routes | Partition/external-actor inspection, Data Layer list/load/unload/show/hide, and streaming sublevel list/add/confirmed-remove/visibility |
| Navigation query filters | Partial | Direct-native-parent NavigationQueryFilter Blueprint creation/inspection, typed area travel/entering costs, exclusions and 16-bit include/exclude masks; structural validation, native compile/cache invalidation, dry-run/no-op, undo/redo and optional save. Ordinary-map native box modifier painting/replacement/disable and Null-area blocking, brush/area undo and save are implemented. Real path choice from travel and boundary entering costs, native exclusion/flag behavior and cold restart persistence passed. Custom/inherited filters and partition modifier persistence remain pending |
| Navigation area definitions | Partial | Direct-native-parent NavArea Blueprint creation/inspection and typed travel/entering costs, RGBA color and supported agents; compile/save, dry-run/no-op, native registration IDs and change-sensitive undo/redo refresh. Painted custom-area costs, filter overrides, agent registration and cold restart persistence passed. Additional native/meta/inherited area bases, custom flags and agent-definition authoring remain pending |
| Native PIE movement probes | Partial | Owned transient native character/controller pairs with capsule dimensions from default nav data, native move/stop/pause/resume, position/velocity/path status and paged move-completion events. Bounded lifetime, expiry/release, retained-probe caps and world/module cleanup. Physical obstacle detours, native completion/abort, editor isolation and two-PIE teardown passed. Selected-PIE smart-link multicast observation and owned-pawn resume are available; events share the bounded cursor history. Broader gameplay AI execution and physical-gap locomotion remain pending |
| Navigation links | Partial | Plain native simple-link and smart-only proxy CRUD, local endpoints/world transforms, area/agent settings, preflight, dry-run/no-op, native undo and map save. Simple direction/snap/projection controls and smart relevance/enabled/disabled-area configuration are supported. Selected-PIE native smart-link toggles change paths without rebuild requests and preserve editor state. Native off-mesh connectivity, direction, area exclusion, two-PIE reset and cold restart persistence passed. Owned native PIE probes support reached events and native link resume. Physical-gap locomotion, derived-proxy authoring, custom IDs/flags, definition assets and segment links remain pending |
| Level Instance | Partial | Standalone lifecycle, map references, transforms, cycle validation, confirmed removal, and native source edit/commit/discard. Confirmed break supports ordinary maps, recursion, folder preservation, explicit saving, and partial-result diagnostics; native break clears undo history. Lifecycle, source editing, and break passed live/restart tests. Packing, overrides, complex package commits, and World Partition/external-actor persistence remain pending |
| Scene / spawned actor editing | Implemented for current routes | Spawn/list/select/query/duplicate/delete plus transform, label, folder, attachment, actor properties, and placed-actor component hierarchy/CRUD/property editing |
| Behavior Tree graphs | Partial | Native graph inspection/init; composite/task/service/decorator CRUD; schema links; scalar/plain-struct properties and key/value bindings; explicit positions and native child order; Blackboard assignment; compile/validation, transactions, dry-run/save and PIE guards. Existing runtime-tree initialization/undo, native controller execution and cold graph/order persistence passed. Simple Parallel has native task/background pins and immediate/delayed finish modes; both native runtime behaviors, role-preserving layout, undo and cold persistence passed. Static Run Behavior references support native root-decorator injection, scoped read-only preview IDs, dependency/Blackboard guards and source preservation; gated nested execution, undo/redo and cold refresh passed. Compound AND/OR/NOT expressions support native graph creation/replacement, inner graph inspection and compiled IDs; all eight truth-table cases, undo/redo and cold persistence passed. Compound root subtree injection preserves source identities and scopes repeated inner preview IDs; native gated nested execution, reference transactions and cold refresh passed. Dynamic subtree default references and registered injection tags support typed edits, dependency/ignored-root-decorator guards, undo and cold persistence; native active-subtree replacement execution passed. Live PIE component discovery and exact-tag runtime replacement include current-instance inspection, authority/dependency/Blackboard guards, dry-run/no-op and clear semantics; seven native Behavior Tree tests and HTTP PIE discovery/guards passed. Multiplayer boundary fixtures, UObject/container/providers and Blueprint runtime gates remain open |
| AI assets | Partial | Behavior Tree graph support above; typed Blackboard local/inherited inspection, key add/update/rename/delete, category/description/synchronization settings, parent edits, dependency preflight and native undo/redo. Real MoveTo selector rename transactions and cold Blackboard hierarchy persistence passed. Exact native scalar/vector/rotation/Object/Class/Enum defaults and constraints support transient preflight and native subobject transactions; real component initialization and cold persistence passed. Struct/custom key settings, broader selector providers remain pending. AI Perception inspection exists; invalid-config diagnostics are only partly verified; StateTree support is described below; EQS support is described below |
| StateTree | Partial | Native asset creation, hierarchy CRUD/move, transitions and schema-approved native struct tasks/conditions/evaluators; scalar/plain-struct settings, native compilation, transient preflight, transactions, dry-run/no-op and save. Native execution verifies task timing and condition selection after undo/redo; HTTP and fresh-editor persistence checks passed. Root/state scalar, enum and plain native struct parameter bags and direct bindings support stable field IDs, rename, atomic required node inputs, native execution-scope source discovery and guarded deletion. Native runtime parameter selection/undo, HTTP typed defaults/bindings and cold bag/binding persistence passed. Local linked subtrees support native inherited layouts/defaults, overrides/reset, direct parameter bindings, retarget and selection-cycle/reference guards; native timing/target execution and undo/redo, HTTP authoring and cold persistence passed. External linked assets support isolated dependency previews, schema/cycle checks, transitive caller parameter propagation and grouped transactions/save. Native execution through linked assets and runtime undo/retarget, HTTP authoring and cold dependency persistence passed. Typed Object/Class/SoftObject/SoftClass parameters validate persistent assets and native/generated classes against explicit constraints; native condition execution/undo, HTTP and cold reference persistence passed. Container parameters, property functions/output bindings, Blueprint UObject settings, single-task schemas, considerations, broader schema/context compatibility and live PIE controls remain open |
| Environment Queries | Partial | Native EQS creation/graph initialization, option/generator/test settings and lifecycle, fallback/test order, enabled state, scalar/class settings and Float/Int/Bool provider defaults/query parameters; compile/validation, transactions, dry-run/no-op and save. Native named-parameter fallback execution and undo passed; REST and cold graph/provider persistence passed. Native nested matching-type composite generator expressions support creation/replacement, inspection, compatibility/ownership guards and preserved option/test identities; native item-count execution, undo/redo, REST and cold nested persistence passed. Live native asynchronous PIE query requests expose typed parameters, status/results, cancellation, expiry and cleanup; three EQS automation tests and actual PIE HTTP execution passed. Forced layouts, async composite children, custom providers and broader Blueprint/multiplayer/runtime coverage remain open |
| Data Asset / Primary Data Asset | Partial | Typed inspect/create/validate routes; no Data Registry or primary bundle editing yet |
| Enhanced Input assets | Partial | Input Action/Mapping Context view and settings editing, map/unmap/replace key operations, and generic Data Asset creation |
| Audio assets | Partial | Sound Wave typed settings/rebuild and guarded native WAV/AIF/AIFF/FLAC/Ogg/Opus/MP3 import/reimport; Sound Cue and MetaSound graphs; typed Sound Class/Mix/Submix settings and hierarchies; attenuation controls, curves, submix sends, plugin references and native gain sampling; plugin settings class discovery/creation; attenuation and concurrency creation; typed Blueprint local/inherited SCS, native default-subobject and placed-instance Audio Component settings with validated native references/concurrency, undo/redo, native inherited overrides/reset and descendant propagation, compile/package save and cold restart persistence including World Partition external actor packages; Dialogue Voice/Wave creation, script/subtitle/voice settings, validated context mappings, localization identity/key inspection, native resolution and save/reload; Quartz runtime PIE clock creation, tempo, lifecycle, inspection, time signatures/pulse overrides, quantized control commands/cancellation, metronome/callback polling, and transient quantized SoundBase playback/stop/pause/resume with native component state/finish callbacks, spatial world transforms/attachment/movement, attenuation/concurrency references and native pre/post Audio Bus sends; modulation parameter, Control Bus, mix, patch, LFO/AD/follower generator and Audio Bus creation/settings, stages/inputs, native conversion and bounded sampling; guarded file-driven patch import/reimport with native WaveTable processing, owned runtime Curve Float baking and cached editor source recipes; native PIE modulation destinations/values, mix/global runtime controls, native proxy filtering, bounded batch controls, device-wide resets, bounded live destination/envelope-follower recordings, audio-thread logical-sound/device-configuration snapshots, guarded native profile save/load and bounded process-wide native Unreal Insights trace capture with channel discovery, native session ownership, manual/duration/PIE stop and retained files. Advanced Audio Component properties, plugin-specific typed parameters, hardware-voice summaries and CPU/DSP trace analysis remain pending |
| Cinematic / Sequencer assets | Partial | Level Sequence create/inspect/settings/validate; possessable and class/actor-template spawnable bindings with confirmed removal; transform, visibility, float-property, fade, audio, and skeletal-animation track/section add/confirmed remove; audio-section start offset, looping, subtitle suppression, and attenuation settings; skeletal-animation section play rate with duration adjustment, reverse, slot, notifier/custom-mode flags, and clip offsets; numeric, audio, animation-weight, and visibility key editing; bounded playback sampling for transform plus optional visibility and float-property tracks on a native actor (up to 600 display frames), in preview or opt-in direct mode with actor values and map package dirty state restored; guarded camera-cut, subsequence, and named shot editing with cycle checks; CineCamera create/inspect/edit for placed actors and sequence templates. Other track combinations, audio asset settings, advanced animation options, camera animation/layout, and take authoring remain pending |
| UE editor status and play control | Implemented | `/editor/status`, `/editor/selection`, `/editor/viewport`, `/editor/play`, `/editor/transactions/undo`, `/editor/transactions/redo`, guarded `/worlds/load` |
| Level editor actors | Implemented for current routes | List/search, spawn, select, select-all, clear, duplicate, confirmed delete |
| Asset editors | Implemented for current routes | Status, open, focus, and confirmed close |
| Content Browser / placement | Implemented for current routes | Selected assets, selection/reveal synchronization, and actor-factory placement with transform, label, folder, and selection control |
| Editor diagnostics | Implemented for current routes | Filtered bounded logs, active-world Map Check, single-participant automation discovery/run/status/stop, and screenshot request/status |
| Build and project validation | Implemented for current routes | Blueprint compilation, asset/shader/fix-up activity status, dependency/referencer audits, and confirmation-protected redirector fix-up; C++ build state is explicitly unavailable |
| Source control | Partial | Provider availability, `/Game` asset and selected project-file status/history, including missing files; guarded checkout/add/revert/submit with dry-run, dirty-package checks, package reload, and submit hooks. Isolated Git tests passed config/asset operations, missing-file restore, deletion submission/history, and path guards. Checkout-enabled providers, changelists, general revision download/diff, and sync remain pending |
| UE reflection docs | Implemented | `/ue/classes`, `/ue/classes/describe`, `/ue/blueprint-functions` |
| Niagara | Partial | Systems, emitter and script assets, renderers, user parameters, script graphs, emitter and system stacks and modules, effect types and scalability, validation rule sets |
| PCG | Implemented for current routes | Graphs and instances, nodes, edges and pins, node and graph settings, typed parameters and overrides, subgraphs, dependencies, validation; world component generation, status and output inspection |
| Geometry Script | Implemented for current routes | Mesh components, topology, UVs, normals, polygroups, materials, vertex colors, and collision. Modeling Tools are not implemented |
| Landscape | Partial | Creation, components, height and weight data, paint layers, edit layers, layer info assets |
| Foliage | Partial | Foliage types and instances, procedural spawners, blocking volumes and falloff |
| Splines | Partial | Spline and spline mesh components: points, tangents, sampling, settings, mesh fitting |
| Volumes | Partial | Box, cylinder, sphere and cone volumes; collision; brush shapes; pain, cull distance and streaming volume settings |
| Lighting and atmosphere | Partial | Lights, sky lights, height and local fog, volumetric clouds, sky atmosphere, post process, reflection captures, planar reflections, decals |
| Gameplay Ability System | Implemented for current routes | Ability, effect, attribute and calculation definitions; gameplay Blueprints; PIE grants, effects, attributes, events, cues, and ability activation. Some edge cases are in UNTESTED_FEATURES.md |
| Gameplay Tags | Implemented for current routes | Tags, sources and tables, rename/delete/move, unused-tag audit, Data Asset tags and queries, runtime and provider query evaluation |
| IK Rig / Retargeter | Partial | IK Rig chains, goals and solvers; retargeter poses, chain mapping, operations, and curve remap |
| Pose Search | Partial | Schemas and channels, databases and entries, normalization sets, interaction assets, index requests |
| Smart Objects / Game Features | Partial | Smart Object definition and Game Feature plugin tools. Behavior definitions, world conditions, annotations, placed components, and Game Feature descriptor/action editing remain pending |
| Remote Control | Implemented for current routes | Preset list/inspect/create, field expose/unexpose, value set |
| Playtest and packaging | Partial | PIE control and inspection, simulated play input, project game settings, Win64 packaging through RunUAT with output in `Saved/MCPBuilds`. Other platforms and device deployment remain pending |

### Important limitations

- `/assets/batch` accepts an ordered `Operations` array and preserves the legacy single-operation body. It is non-atomic: earlier successful operations remain applied after a later failure. Batch preflight rejects nested object-reference traversal.
- Remaining Control Rig channel/space options and other Sequencer track combinations remain open. The frame evaluator samples transform, visibility, and float-property tracks together in preview or direct mode, restoring actor values and map package dirty state. Class-only spawnable templates also survive save and editor restart.
- Some new asset routes expose reflected-property editing rather than dedicated typed DTOs.
- The property system uses UE 5.7 `FProperty::ImportText_Direct` and native export logic. Nested object paths require an existing object; array indexes must already exist.
- Python syntax validation and the UE 5.7 `DemoForPluginEditor` Development build pass, including `UE5_MCP`.
- UE documentation results are based on classes currently loaded in the running editor; unloaded engine/plugin classes are not returned until their modules/assets are loaded.
- Live actor routes operate on the current editor world. Actor deletion and asset-editor closing require `bConfirm=true`; viewport writes require an active level viewport.
- `load_editor_world` refuses to switch maps during PIE. Its `dirty_policy` is `fail`, `save`, or `discard`; the default reports separate dirty map/content package lists without changing state, while discard additionally requires `confirm=True`.

## Testing

The scripts are in `Python/MCP/tests/`. The `smoke_*_live.py` scripts need a running editor, and some expect the plugin at `<project>/Plugins/UE5_MCP`.

For unattended runs, launch the editor with `-UE5MCPApiPort=8080`. This starts only the Unreal API on that port. Without the flag, startup is controlled from the tab.

Run these from the plugin directory:

```bash
python Python/MCP/tests/smoke_sequencer_live.py
```

This one exercises Sequencer authoring against a disposable, unsaved sequence, using the running editor.

```bash
python Python/MCP/tests/smoke_sequencer_persistence.py
```

This one needs port 8080 free. It starts two command-line editor sessions to verify save and reload, then deletes its uniquely named test sequence.

## Roadmap

Next, from [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md):

1. Add Blueprint debugging and C++ feedback: breakpoints, C++ class creation, compile and Live Coding status.
2. Build one small game using only the core tools, then correct `CORE_TOOLS` based on what was missing.
3. Remove the duplicate `start_play_in_editor` and `stop_play_in_editor` tools, and try the tool list in a real client such as Claude Desktop or Cursor.

## Documentation

| File | Contents |
|---|---|
| [IMPLEMENTED_FEATURES.md](IMPLEMENTED_FEATURES.md) | Implemented work and the common API contract |
| [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) | Outstanding work |
| [UNTESTED_FEATURES.md](UNTESTED_FEATURES.md) | Implemented tools with no complete passing live test |
| [UE5_EDITOR_TOOL_DESIGN.md](UE5_EDITOR_TOOL_DESIGN.md) | Tool design |
| [UE5_EDITOR_API_MAPPING.md](UE5_EDITOR_API_MAPPING.md) | Mapping to UE editor APIs |
| [VERIFICATION_REPORT_2026-10-25.md](VERIFICATION_REPORT_2026-10-25.md), [VERIFICATION_REPORT_2026-10-30.md](VERIFICATION_REPORT_2026-10-30.md) | Verification results |

## Contributing

Tools live in `Python/MCP/ue5_tools/`, one module per feature group, and `mcp_server.py` loads them automatically. Keep them aligned with the plural REST routes, such as `/blueprints/functions`.

For new work:

* Follow the common API contract in [IMPLEMENTED_FEATURES.md](IMPLEMENTED_FEATURES.md): dry run, confirmation, transactions, and saving only on request.
* Record each new feature in `IMPLEMENTED_FEATURES.md` and `UNTESTED_FEATURES.md`, then remove it from `IMPLEMENTATION_PLAN.md`.
* Report unsupported optional engine plugins as unavailable, never as implemented.

## License

[MIT](LICENSE)
