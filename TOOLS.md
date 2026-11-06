# UE5_MCP tools

All 1732 tools, grouped by feature module in `Python/MCP/ue5_tools/`. **Core** tools are listed to clients by default; reach the others with `find_tools` and `call_tool`, or start the server with `--all-tools`.

Tools that show variants take a required `variant` argument.

## Features

| Feature | Tools |
|---|---|
| [ai](#ai) | 44 |
| [animation](#animation) | 91 |
| [assets](#assets) | 30 |
| [audio](#audio) | 106 |
| [blueprints](#blueprints) | 42 |
| [catalog](#catalog) | 3 |
| [cinematics](#cinematics) | 58 |
| [data](#data) | 6 |
| [debugging](#debugging) | 7 |
| [editor](#editor) | 12 |
| [foliage](#foliage) | 39 |
| [gameplay_abilities](#gameplay_abilities) | 31 |
| [gameplay_tags](#gameplay_tags) | 21 |
| [geometry_script](#geometry_script) | 87 |
| [ik_retarget](#ik_retarget) | 102 |
| [input](#input) | 7 |
| [landscape](#landscape) | 24 |
| [lighting](#lighting) | 131 |
| [materials](#materials) | 60 |
| [meshes](#meshes) | 23 |
| [navigation](#navigation) | 14 |
| [niagara](#niagara) | 137 |
| [pcg](#pcg) | 49 |
| [physics](#physics) | 25 |
| [playtest_build](#playtest_build) | 23 |
| [pose_search](#pose_search) | 75 |
| [remote_control](#remote_control) | 6 |
| [rigs](#rigs) | 16 |
| [splines](#splines) | 37 |
| [state_tree](#state_tree) | 22 |
| [textures](#textures) | 184 |
| [ui](#ui) | 6 |
| [volumes](#volumes) | 31 |
| [world](#world) | 48 |
| [world_partition](#world_partition) | 135 |

## ai

| Tool | Core | Description |
|---|---|---|
| `add_blackboard_key` |  | Add a local native Blackboard key; names use UE FName case-insensitive identity. |
| `ai_perception_runtime` |  | Variants: `control_ai_perception_runtime`, `configure_ai_perception_runtime` |
| `compile_behavior_tree` |  | Rebuild native runtime execution data from the graph and report validation. |
| `compile_environment_query` |  | Rebuild native EQS runtime option/test arrays from the editor graph. |
| `configure_ai_perception_component` |  | Configure a placed editor AI Perception component with transaction/save support. |
| `configure_ai_perception_source` |  | Replace placed source component auto-registration and sense list with transaction/save. |
| `control_ai_perception_source` |  | Request native PIE stimulus-source registration for one actor/sense. |
| `create_behavior_tree` | Core | Create an empty Behavior Tree asset. |
| `create_behavior_tree_decorator_logic` |  | Attach a native compound decorator using prefix rows. |
| `create_behavior_tree_node` |  | Create a native graph node from a concrete composite/task/service/decorator class. |
| `create_blackboard` | Core | Create an empty Blackboard asset. |
| `create_environment_query` |  | Create an empty native EQS asset in a new /Game package. |
| `delete_behavior_tree_node` |  | Delete a node with its attached subnodes/links; preview affected_nodes via dry-run. |
| `edit_environment_query_option` |  | Create/update/delete one native EQS option and its generator settings. |
| `edit_environment_query_test` |  | Create/update/delete a native EQS test compatible with its option item type. |
| `environment_query_runtime` |  | Variants: `run_environment_query`, `control_environment_query_request` |
| `initialize_behavior_tree_graph` |  | Explicitly create the native editor graph, preserving existing runtime nodes/Blackboard. |
| `initialize_environment_query_graph` |  | Initialize the native EQS editor graph, preserving existing runtime options. |
| `inspect_ai_perception_components` |  | Inspect placed editor AI Perception components and stored sense configuration. |
| `inspect_ai_perception_runtime` |  | Inspect native AI Perception components in the selected live PIE world. |
| `inspect_ai_perception_sources` |  | Inspect placed editor stimuli-source components and stored registration senses. |
| `inspect_behavior_tree` |  | Inspect native graph/root, tasks/services/decorators, pins, properties and selector bindings. |
| `inspect_behavior_tree_runtime` |  | Inspect registered live Behavior Tree components in one PIE world. |
| `inspect_blackboard` |  | Inspect Blackboard keys, types, and parent Blackboard. |
| `inspect_environment_query` |  | Inspect native EQS options, generators, tests, providers and compiled order. |
| `inspect_environment_query_requests` |  | Read owned native EQS status/results, or list retained requests in one PIE world. |
| `layout_behavior_tree_nodes` |  | Set unique top-level node positions: [{NodeGuid, X, Y}], each within +/-1e6. |
| `layout_environment_query` |  | Set option NodeGuid/X/Y positions; unique X determines native fallback order. |
| `list_ai_perception_classes` |  | List loaded concrete AI Perception sense/config classes and editable defaults. |
| `list_environment_query_owners` |  | Find live PIE actor paths and authority for explicit EQS request owners. |
| `remove_blackboard_key` |  | Delete a local key transactionally. Referencers require confirm; preview via dry_run. |
| `replace_behavior_tree_decorator_logic` |  | Replace a compound expression transactionally; omitted name preserves it. |
| `replace_behavior_tree_runtime_subtree` |  | Replace currently instantiated dynamic tasks with an exact registered tag. |
| `replace_environment_query_generators` |  | Replace one option's native generator tree, preserving its GUID and tests. |
| `report_ai_perception_damage` |  | Submit a native damage perception stimulus between authoritative PIE actors. |
| `report_ai_perception_noise` |  | Submit a native asynchronous hearing event from an authoritative PIE actor. |
| `set_behavior_tree_blackboard` |  | Set/clear the root and compiled-tree Blackboard together; changes require confirm. |
| `set_behavior_tree_link` |  | Connect/disconnect a top-level output to input using the native graph schema. |
| `set_blackboard_parent` |  | Set or clear the parent with cycle/key-conflict checks and native cache propagation. |
| `smart_object_definition` |  | Smart Object definitions: Inspect/Create/AddSlot/SetSlot/RemoveSlot. |
| `update_behavior_tree_node` |  | Transactionally edit native node settings/selectors after transient preflight. |
| `update_blackboard_key` |  | Edit a local Blackboard key with native transaction and descendant preflight. |
| `validate_behavior_tree` |  | Validate native graph topology, compiled execution data and direct Blackboard compatibility. |
| `validate_blackboard` |  | Validate bounded parent chains, effective key names/types and native ID capacity. |

## animation

| Tool | Core | Description |
|---|---|---|
| `add_animation_graph_node` |  | Add a reflected AnimGraph node class to an Animation Blueprint graph. |
| `change_skeleton_curve_metadata` |  | Rename/remove Skeleton curve metadata through native storage APIs. |
| `compare_skeleton_hierarchies` |  | Compare registered Skeleton raw bone names, direct parents and local reference poses. |
| `compile_animation_blueprint` |  | Compile an Animation Blueprint and report its resulting status. |
| `create_animation_sequence` |  | Create an empty Animation Sequence from a valid Skeleton asset. |
| `create_animation_transform_curve` |  | Create empty native editable drive-track transform curve for existing Skeleton bone. |
| `create_skeleton_blend_profile` |  | Create owned native blend profile/mask on confirmed /Game Skeleton. |
| `create_skeleton_virtual_bone` |  | Create native virtual bone on confirmed /Game Skeleton with stopped PIE. |
| `delete_skeleton_blend_profile` |  | Delete owned profile using native editor-style array removal and garbage marking. |
| `delete_skeleton_socket` |  | Delete exactly one skeleton-owned socket and its Skeleton preview attachments. |
| `delete_skeleton_virtual_bones` |  | Delete virtual bones in dependency order using native Skeleton rebuild. |
| `duplicate_animation_float_curve` |  | Duplicate existing float curve through native animation data controller. |
| `duplicate_animation_transform_curve` |  | Duplicate all nine native transform channels to unused existing Skeleton bone name. |
| `edit_animation_blueprint_pose_link` |  | Connect or disconnect pose pins using the Animation Graph schema. |
| `edit_animation_blueprint_state_machine` |  | Add/remove states or transitions, or set the state-machine entry target. |
| `edit_animation_blueprint_transition` |  | Edit a state transition by GUID, including blend and priority settings. |
| `edit_animation_bone_track` |  | Add/remove a Skeleton bone track or replace one frame's transform. |
| `edit_animation_curve_key` |  | Variants: `edit_animation_rich_float_key`, `move_animation_rich_float_key` |
| `edit_animation_data` |  | Variants: `edit_animation_asset`, `edit_animation_curve` |
| `edit_animation_sequence_attribute` |  | Add/remove a typed bone attribute or set/remove one key. |
| `edit_animation_sequence_compression` |  | Set validated Animation Sequence compression assets and related options. |
| `edit_animation_sequence_settings` |  | Edit reflected Animation Sequence settings. |
| `edit_animation_sequence_timing` |  | Change source frame rate or resize frames with bone-key resampling. |
| `edit_blend_space_axis` |  | Edit axis display_name, min, max, grid_num, snap_to_grid, or wrap_input. |
| `edit_blend_space_sample` |  | Add, update, move, or delete a Blend Space sample by persistent ID or index. Delete requires confirm. |
| `edit_montage_section` |  | Create, update, link, or delete an Animation Montage section. |
| `edit_skeletal_preview_attachment` |  | Add/remove persistent StaticMesh/SkeletalMesh preview attachment metadata. |
| `edit_skeleton_compatibility` |  | Add/remove one-way native compatible-Skeleton declaration with transaction. |
| `edit_skeleton_curve_metadata` |  | Create/update full Skeleton curve metadata settings with native storage APIs. |
| `edit_skeleton_socket` |  | Create/update a skeleton-owned socket on a /Game Skeleton with native transaction. |
| `evaluate_animation_float_curve` |  | Evaluate native source rich float curve at <=512 finite bounded times. |
| `evaluate_animation_transform_curve` |  | Sample native full source transform curve, <=256 finite times and weight [0,1]. |
| `evaluate_animation_transform_curve_channel` |  | Sample one source transform rich channel using native interpolation/extrapolation. |
| `get_animation_curve` |  | Read float keys from an animation curve. |
| `inspect_animation_blueprint` | Core | Summarize an Animation Blueprint's Skeleton, graphs, states, and status. |
| `inspect_animation_bone_track_keys` |  | Read a page of source bone-track transforms by frame. |
| `inspect_animation_curve_diagnostics` |  | Check source float/transform rich-curve structure, <=1024 channels/65536 keys. |
| `inspect_animation_float_curve_range` |  | Read native source float-curve time/value ranges, <=4096 keys. |
| `inspect_animation_rich_float_curve` |  | Read paginated native float curve interpolation/tangent/weight/extrapolation data. |
| `inspect_animation_sequence` |  | Inspect Animation Sequence timing, source model, compression, and content counts. |
| `inspect_animation_sequence_compression` |  | Inspect bone/curve compression assets, frame stripping, error scale, and cache state. |
| `inspect_animation_sequence_timeline` |  | List notify tracks/events, sync markers, curves, and animated attributes. |
| `inspect_animation_transform_curve_channel` |  | Read rich keys from one native transform-curve channel, count 1..512. |
| `inspect_animation_transform_curve_keys` |  | Read native or union transform-curve key timeline and transforms, count 1..256. |
| `inspect_blend_space` |  | Inspect a Blend Space or Blend Space 1D. |
| `inspect_skeleton_blend_profile_references` |  | Inspect loaded strong profile referencers and Skeleton-wide package dependencies. |
| `inspect_skeleton_blend_profile_scales` |  | Read native effective profile scales and distinguish explicit entries/defaults. |
| `inspect_skeleton_structure` |  | Inspect registered Skeleton bones, skeleton-owned sockets and virtual bones. |
| `layout_animation_blueprint_graph` |  | Format an Animation Blueprint graph identified by its full path. The spacings are the gaps between nodes. |
| `list_animation_blueprint_graphs` |  | List nested graphs or inspect one graph's nodes, pose pins, and links. |
| `list_animation_blueprint_state_machines` |  | Inspect state machines, states, transitions, rules, and blend settings. |
| `list_animation_blueprint_variables` |  | List Animation Blueprint variables with types, categories, and defaults. |
| `list_animation_sequence_attributes` |  | List animated bone attributes and their typed keys. |
| `list_animation_sequence_tracks` |  | List source bone tracks and their matching Skeleton bone indices. |
| `list_animation_source_curves` |  | List sorted source float/transform curve names, flags and channel key counts. |
| `list_blend_space_axes` |  | List the active axes of a Blend Space or Blend Space 1D. |
| `list_blend_space_samples` |  | List Blend Space sample assets and coordinates. |
| `move_animation_transform_curve_key` |  | Move exact-time keys in matching transform channels, preserving sparse/rich data. |
| `offset_animation_float_curve_time` |  | Shift all float curve key times, retaining rich fields through native setter. |
| `offset_animation_transform_curve_time` |  | Shift all nine source transform-channel key timelines with complete preflight. |
| `preview_blend_space_input` |  | Preview the sampled animation weights at a Blend Space input. |
| `rebuild_blend_space` |  | Rebuild Blend Space segmentation or triangulation from its samples. |
| `remove_animation_float_curve_key_range` |  | Remove keys with inclusive times in ordered in-duration interval. |
| `remove_animation_transform_curve` |  | Remove existing source transform curve and all nine channel key sets. |
| `remove_animation_transform_curve_key` |  | Remove exact-time keys across native transform channels, retaining sparse data. |
| `remove_animation_transform_curve_key_range` |  | Remove inclusive-time keys across all nine transform channels. |
| `rename_animation_float_curve` |  | Rename source float curve through native animation data controller. |
| `rename_animation_transform_curve` |  | Rename native transform curve to distinct unused existing Skeleton bone name. |
| `rename_skeleton_blend_profile` |  | Rename existing owned blend profile/mask through native Skeleton API. |
| `rename_skeleton_socket` |  | Rename Skeleton-owned socket and Skeleton preview attachment names. |
| `rename_skeleton_virtual_bone` |  | Rename native virtual bone and reparent Skeleton-owned socket attachments. |
| `replace_animation_rich_float_curve` |  | Replace <=4096 existing source float curve rich keys through native controller. |
| `replace_animation_transform_curve_channel` |  | Replace rich keys in one existing transform curve channel via native controller. |
| `replace_animation_transform_curve_keys` |  | Replace all nine transform channel key sets with native complete transform keys. |
| `resample_animation_float_curve` |  | Replace float curve with linear native samples at 1..4096 ordered times. |
| `resample_animation_transform_curve` |  | Replace transform curve with native samples at 1..4096 strictly ordered times. |
| `reset_skeleton_blend_profile_entries` |  | Remove explicit blend-profile/mask bone entries, restoring native default scale. |
| `scale_animation_float_curve_time` |  | Retime source float curve with native ScaleCurve around origin. |
| `set_animation_float_curve_color` |  | Set native float-curve editor display color; channels R/G/B/A in [0,1]. |
| `set_animation_float_curve_comment` |  | Set native editor float-curve comment (<=4096 characters); empty clears. |
| `set_animation_float_curve_extrapolation` |  | Set existing source float curve extrapolation without replacing keys. |
| `set_animation_float_curve_flag` |  | Set native Editable/Metadata/Disabled float-curve flag transactionally. |
| `set_animation_transform_channel_extrapolation` |  | Set native extrapolation on one existing transform curve channel. |
| `set_animation_transform_curve_flag` |  | Set native transform-curve Editable/DriveTrack/Disabled flag. |
| `set_animation_transform_curve_key` |  | Set native whole-transform key on existing curve at in-duration time. |
| `set_skeleton_blend_profile_mode` |  | Change native profile interpretation to TimeFactor/WeightFactor/BlendMask. |
| `set_skeleton_blend_profile_scales` |  | Set existing native blend-profile/mask bone scales with transaction. |
| `validate_animation_blueprint` |  | Check Skeleton, graph links, state-machine wiring, and compile status. |
| `validate_animation_sequence` |  | Check Skeleton, source frames, bone tracks, attributes, notifies, and sync markers. |
| `validate_blend_space` |  | Check Blend Space axes, sample compatibility, coordinates, and interpolation data. |
| `widget_animations` |  | UMG Widget Blueprint animations: Inspect/Create/Rename/Delete/SetRange. |

## assets

| Tool | Core | Description |
|---|---|---|
| `audit_editor_assets` |  | Audit dependencies, missing packages, referencers, and redirectors. |
| `batch_asset_operations` |  | Run ordered generic set_properties or save operations and return one result per entry. The batch is not atomic. |
| `close_asset_editor` |  | Close all editors for an asset; requires confirm=True. |
| `consolidate_assets` |  | Consolidate 1..64 same-class assets into target via native ObjectTools::ConsolidateObjects. |
| `create_asset` | Core | Create a new asset at an unused /Game path. Existing assets are never overwritten. Requires stopped PIE. |
| `delete_asset` | Core | Force-delete an asset package. This can remove undo history and should be used deliberately. |
| `describe_asset` | Core | Describe a UE asset. Includes Blueprint parent/type and the widget list for Widget Blueprints. |
| `describe_ue_class` | Core | Get UE class metadata, Blueprint-callable functions, properties, and parameter types. |
| `duplicate_asset` | Core | Duplicate an asset to a new content path. |
| `fixup_editor_redirectors` |  | Fix referencers and delete resolved redirectors; requires confirmation. |
| `focus_asset_editor` |  | Focus an already-open asset editor. |
| `get_asset_capabilities` |  | List legacy family names plus per-family generic, inspect, edit, create, rebuild, and validate flags. |
| `get_asset_editor_status` |  | Report whether an asset editor is open and its editor name. |
| `get_asset_properties` | Core | Read reflected properties from a UE asset, including structs, arrays, enums and asset references. |
| `get_asset_referencers` | Core | Find cached package referencers of an asset. |
| `get_asset_source_control_history` |  | Read bounded revision metadata for up to 16 /Game assets or selected project files. |
| `get_asset_source_control_status` |  | Read source-control state for /Game assets or selected project files, including missing files. |
| `get_content_browser_selection` |  | List assets selected in the primary UE Content Browser. |
| `get_editor_source_control_provider` |  | Inspect the editor's configured source-control provider and supported operations. |
| `list_assets` | Core | List assets below a UE content directory. |
| `list_ue_classes` | Core | Find classes by name, parent, category or origin, including Blueprints that are not loaded and custom C++ classes. |
| `open_asset_editor` |  | Open the appropriate UE editor for an asset. |
| `operate_asset_source_control` |  | Run a provider operation on /Game assets or selected project files. Revert/submit require confirmation; submit requires a description and saved packages. |
| `preview_asset_operation` |  | Preview property changes or a save with validation and no asset mutation. |
| `rename_asset` | Core | Rename or move an asset to a new content path. |
| `reveal_content_browser_assets` |  | Select assets and focus their location in the UE Content Browser. |
| `save_asset` | Core | Save a dirty UE asset package. |
| `select_content_browser_assets` |  | Select assets in the Content Browser without forcing it to the foreground. |
| `set_asset_properties` | Core | Set reflected asset properties using dot paths and UE text values. |
| `validate_asset` | Core | Check asset identity and preflight property paths and values without editing the asset. |

## audio

| Tool | Core | Description |
|---|---|---|
| `add_audio_volume_override` |  | Append AudioVolume override row targeting unique loaded USoundSubmix, count<128 guard. |
| `add_audio_volume_send_row` |  | Append native AudioVolume send row, listener_state0 inside/1 outside, count<128 guard. |
| `add_audio_volume_submix_send` |  | Append native-default send to inspected listener row, loaded USoundSubmixBase target. |
| `compile_metasound` |  | Register a MetaSound graph with the frontend to compile it, optionally saving. |
| `control_audio_diagnostic_capture` |  | Queue or release a native audio-thread diagnostic snapshot in PIE. |
| `control_audio_trace` |  | Capture native process-wide audio profiling to a project Saved/Profiling/UE5MCP .utrace file. |
| `control_control_bus_mix_profile` |  | Save/load a native mix profile. Indices 0-999; overwrite/load replacement require confirmation. |
| `control_modulation_recording` |  | Record real native PIE destination values; operations start/stop/release. |
| `control_modulation_runtime` |  | Control native PIE modulation without editing saved assets. |
| `control_quartz_clock` |  | Create or control a PIE Quartz clock. Operations: create/time_signature/tempo/start/pause/resume/stop/reset/delete. |
| `control_quartz_events` |  | Subscribe to Quartz metronome events or schedule native tempo/reset/notify/start_other commands. |
| `convert_modulation_parameter_values` |  | Apply native parameter conversion to 1-256 values; direction normalized_to_unit or unit_to_normalized. |
| `create_audio_plugin_settings` |  | Create a default plugin source settings asset from a compatible concrete loaded class. |
| `create_dialogue_asset` |  | Create a Dialogue Voice or Dialogue Wave using the native editor factory. |
| `create_metasound` |  | Create a MetaSound source or patch, optionally using a same-type preset parent. |
| `create_modulation_asset` |  | Create a parameter, Control Bus, mix, patch, generator or Audio Bus modulation asset. |
| `create_sound_attenuation` |  | Create a Sound Attenuation asset for audio sections, sounds, or cues. |
| `create_sound_concurrency` |  | Create a Sound Concurrency asset for sound voice management. |
| `create_sound_cue` | Core | Create an empty Sound Cue asset with its editor graph root. |
| `edit_attenuation_plugin_reference` |  | Add/remove/clear compatible attenuation plugin settings references without editing the referenced asset. |
| `edit_attenuation_submix_send` |  | Upsert/remove/clear attenuation submix sends with Manual, Linear, or CustomCurve control. |
| `edit_audio_asset_settings` |  | Edit reflected settings on a supported audio asset, including Sound Concurrency. |
| `edit_audio_component_settings` |  | Edit persistent Audio Component settings with validation and transaction; compile template changes. |
| `edit_audio_volume_send_inline_keys` |  | Add one linear key or Remove key_index with mandatory full ordered native row snapshots. |
| `edit_control_bus_mix_stage` |  | Upsert, remove or clear native Control Bus Mix stages; removal requires confirmation. |
| `edit_dialogue_context` |  | Upsert/remove/clear dialogue contexts with compatible voice and recorded audio references. |
| `edit_dialogue_voice` |  | Edit Dialogue Voice gender/plurality while preserving localization identity. |
| `edit_dialogue_wave` |  | Edit dialogue script, subtitles, voice direction, and mature flag; refresh native context proxies. |
| `edit_metasound_graph` |  | Add/remove/connect/disconnect/edit MetaSound nodes; node removal requires confirmation. |
| `edit_modulation_generator` |  | Edit LFO, AD envelope or envelope follower settings using native Params field names. |
| `edit_modulation_patch_input` |  | Upsert/remove/clear patch inputs, selected by Control Bus. Removal requires confirmation. |
| `edit_modulation_settings` |  | Edit typed modulation settings with preflight validation. |
| `edit_sound_attenuation_curve` |  | Set external or replace/clear inline attenuation, absorption, reverb, or priority curves. |
| `edit_sound_attenuation_settings` |  | Edit named attenuation controls from inspection; validate ranges before mutation. |
| `edit_sound_class_settings` |  | Edit typed Sound Class gains, routing, loading behavior, and hierarchy references. |
| `edit_sound_cue_graph` |  | Add/delete/connect/move/layout/compile Sound Cue nodes; node deletion requires confirmation. |
| `edit_sound_mix_adjuster` |  | Upsert or confirmed-remove a Sound Class adjuster on a Sound Mix. |
| `edit_sound_mix_settings` |  | Edit Sound Mix timing and individual EQ band frequency, gain, and bandwidth values. |
| `edit_sound_submix_effect` |  | Add a Sound Effect Submix Preset to the chain or remove it with confirmation. |
| `edit_sound_submix_settings` |  | Edit Sound Submix parent, auto-disable, envelope-following, and level settings. |
| `edit_sound_wave_settings` |  | Edit typed Sound Wave codec, streaming, loop, Sound Class, attenuation, and concurrency settings. |
| `evaluate_sound_attenuation` |  | Sample native distance-volume attenuation at up to 256 world-space x/y/z points. |
| `import_modulation_file_transform` |  | Import/reimport a native file-backed patch input transform using a local Sound Factory format. |
| `import_sound_wave` | Core | Import a native-supported audio file as a Sound Wave; replacement requires confirmation. |
| `inspect_audio_asset` |  | Inspect supported audio assets, including Dialogue Voice and Dialogue Wave metadata. |
| `inspect_audio_component_settings` |  | Inspect an SCS/native default-subobject template or placed editor Audio Component; specify one target path. |
| `inspect_audio_diagnostic_capture` |  | Poll native captured sound state. Weak object paths resolve on the game thread after capture. |
| `inspect_audio_trace` |  | Inspect native trace connection/channel capabilities and optional owned capture metadata/file size. |
| `inspect_audio_volume` |  | Inspect loaded AudioVolume controls/reverb/interior settings and submix collection counts. |
| `inspect_audio_volume_send_inline_curve` |  | Inspect stored inline send-curve keys/tangents/weights/extrapolation, pages1..128. |
| `inspect_audio_volume_submix` |  | Inspect SubmixSendSettings/SubmixOverrideSettings rows1..128/nested sends or effects16. |
| `inspect_audio_volume_submix_row_items` |  | Page all sends/effects within selected AudioVolume submix row, native order1..128. |
| `inspect_control_bus_mix_profile` |  | Inspect native on-disk mix profile stage targets/attack/release without changing assets. |
| `inspect_dialogue_voice` |  | Inspect a Dialogue Voice's gender, plurality, localization GUID, and dirty state. |
| `inspect_dialogue_wave` |  | Inspect dialogue script/subtitles, voice direction, contexts, audio references, and localization keys. |
| `inspect_metasound_graph` |  | Inspect MetaSound graph metadata, interface pins, node defaults, locations, and edges. |
| `inspect_modulation_asset` |  | Inspect parameter domains, buses, mix stages, generator parameters, or patch inputs/transforms. |
| `inspect_modulation_recording` |  | Poll bounded native modulation readings with sequence cursor and monotonic receipt times. |
| `inspect_modulation_runtime` |  | Inspect native PIE modulation mix activity/values and adapter-owned destination handles. |
| `inspect_quartz_clock` |  | Inspect a native runtime Quartz clock in PIE, including tempo, transport and musical durations. |
| `inspect_quartz_events` |  | Poll native Quartz command/metronome callbacks, with sequence cursor, overflow count and terminal state. |
| `inspect_sound_attenuation_settings` |  | Inspect attenuation numeric settings, flags, enum choices, shape extents, and custom curves. |
| `inspect_sound_class_settings` |  | Inspect typed Sound Class volume, pitch, routing, hierarchy, and defaults. |
| `inspect_sound_cue_graph` |  | Inspect Sound Cue graph nodes, positions, pins, links, and node settings. |
| `inspect_sound_mix_settings` |  | Inspect Sound Mix timing, four EQ bands, and Sound Class adjusters. |
| `inspect_sound_submix_settings` |  | Inspect Sound Submix hierarchy, level, auto-disable, envelope, and effects settings. |
| `inspect_sound_wave_settings` |  | Inspect Sound Wave compression, loading, loop, attenuation, and concurrency settings. |
| `inspect_sound_wave_source` |  | Inspect imported Sound Wave duration, channels, sample rate, and source files. |
| `list_audio_plugin_settings_classes` |  | List loaded concrete spatialization, occlusion, reverb, and source-override settings classes. |
| `list_metasound_node_classes` |  | Search the registered, referenceable MetaSound node classes and their pins. |
| `list_sound_wave_import_formats` |  | List audio extensions supported by the installed native Sound Factory for import/reimport. |
| `rebuild_sound_wave` |  | Rebuild a Sound Wave's derived platform audio data. |
| `reimport_sound_wave` |  | Reimport a Sound Wave from its recorded audio file or a confirmed new source/format. |
| `remove_audio_volume_override` |  | Remove existing AudioVolume override row with exact submix/full effect-chain/count guards. |
| `remove_audio_volume_send_row` |  | Remove whole listener send row with exact state/count/full ordered destination guards. |
| `remove_audio_volume_submix_send` |  | Remove inspected AudioVolume destination send with target/row/count/listener guards. |
| `reorder_audio_volume_overrides` |  | Reorder all AudioVolume override rows by complete unique source-index permutation<=128. |
| `reorder_audio_volume_send_rows` |  | Reorder listener rows by complete unique permutation<=128/ordered current state guards. |
| `reorder_audio_volume_submix_sends` |  | Reorder all sends in selected listener row via unique permutation<=64/full target guards. |
| `replace_audio_volume_send_linear_keys` |  | Replace entire inline send curve with linear keys<=256; discards old tangents/interpolation/handles. |
| `resolve_dialogue_context` |  | Resolve a dialogue context through UE's native proxy and localized text APIs without playing audio. |
| `sample_modulation_asset` |  | Sample a fresh native LFO/AD instance or a patch input transform. Read-only; no live playback state. |
| `set_audio_volume_control` |  | Set AudioVolume Priority+/-1e6 or bEnabled with exact identity/current native value guards. |
| `set_audio_volume_interior` |  | Set AudioVolume Exterior/Interior Volume0..1, Time/LPFTime0.01..100000, LPF20..20000Hz. |
| `set_audio_volume_override_crossfade` |  | Edit existing AudioVolume submix override crossfade0..100000 with row/submix/value guards. |
| `set_audio_volume_override_effects` |  | Replace full ordered AudioVolume override effect chain<=64, empty clears/duplicates allowed. |
| `set_audio_volume_override_target` |  | Set existing AudioVolume override target to loaded USoundSubmix or empty repair-state clear. |
| `set_audio_volume_reverb` |  | Set AudioVolume reverb Volume0..1/FadeTime0..100000/bApplyReverb using native setter. |
| `set_audio_volume_reverb_object` |  | Assign ReverbEffect/ReverbPluginEffect using loaded compatible asset or permitted empty clear. |
| `set_audio_volume_send_control` |  | Set SendLevelControlMethod0 Linear1 CustomCurve2 Manual, SendStage0 post1 pre, or DisableManualSendClamp0..1. |
| `set_audio_volume_send_curve` |  | Assign loaded CurveFloat to selected AudioVolume send or empty clear, full reference/context guards. |
| `set_audio_volume_send_inline_curve_setting` |  | Edit stored inline send curve with mandatory full ordered untruncated native row snapshot texts. |
| `set_audio_volume_send_inline_key_setting` |  | Edit stored inline send curve with mandatory full ordered untruncated native row snapshot texts. |
| `set_audio_volume_send_numeric` |  | Edit SendLevel/MinSendLevel/MaxSendLevel/MinSendDistance/MaxSendDistance with exact guards. |
| `set_audio_volume_send_row_listener` |  | Set existing listener row0 inside/1 outside, exact row/count/send-count/current state guards. |
| `set_audio_volume_send_target` |  | Reassign selected send to loaded USoundSubmixBase or empty repair-state clear. |
| `validate_audio_asset` |  | Validate that an asset is a supported audio asset family, including Sound Concurrency. |
| `validate_dialogue_asset` |  | Validate dialogue enums, localization identity/keys, contexts, and recorded audio references. |
| `validate_metasound` |  | Validate MetaSound frontend document structure and graph edges. |
| `validate_modulation_asset` |  | Validate parameter domains, Control Bus references and Control Bus Mix stage targets/timing. |
| `validate_sound_attenuation` |  | Validate attenuation shape geometry, numeric ranges, enum values, and custom curves. |
| `validate_sound_class` |  | Validate Sound Class numeric settings and parent/child hierarchy consistency. |
| `validate_sound_cue` |  | Validate Sound Cue graph roots, links, node references, cycles, and wave players. |
| `validate_sound_mix` |  | Validate Sound Mix timing, EQ bands, class adjusters, and passive activation loops. |
| `validate_sound_submix` |  | Validate Sound Submix level, parent hierarchy, envelope settings, and effect chain. |
| `validate_sound_wave` |  | Validate Sound Wave compression and imported source metadata. |

## blueprints

| Tool | Core | Description |
|---|---|---|
| `add_branch_node_to_graph` | Core | Add a Branch node. |
| `add_break_struct_node_to_graph` |  | Add a Break Struct node. |
| `add_class_cast_node_to_graph` |  | Add a Class Cast node. |
| `add_comment_node_to_graph` |  | Add a comment node. |
| `add_component_to_bp` | Core | Add a component to the Blueprint. |
| `add_dynamic_cast_node_to_graph` | Core | Add a Dynamic Cast node. |
| `add_enum_cast_node_to_graph` |  | Add a Byte-to-Enum Cast node. |
| `add_event_to_graph` | Core | Add an event (custom or built-in) to the specified graph in the Blueprint. |
| `add_execution_sequence_node_to_graph` |  | Add an Execution Sequence node. |
| `add_function_call_to_graph` | Core | Add a function call node to the specified graph in the Blueprint. |
| `add_generic_node_to_graph` | Core | Add any concrete K2 node class returned by get_supported_nodes. |
| `add_make_struct_node_to_graph` |  | Add a Make Struct node. |
| `add_math_node_to_graph` | Core | Add a UKismetMathLibrary function node. |
| `add_switch_node_to_graph` |  | Add one switch node using switch_type: enum, integer, string, or name. |
| `add_variable_to_bp` | Core | Add a new variable to the Blueprint. |
| `add_variable_to_graph` | Core | Add a variable node (setter or getter) to the specified graph in the Blueprint. |
| `break_pin_connection` | Core | Break the connection between pins in the specified graph. |
| `compile_blueprint` | Core | Compile the Blueprint and return success, error and warning counts, and each message with its node. |
| `connect_pins` | Core | Connect pins between nodes in the specified graph. |
| `create_blueprint` | Core | Create a new Unreal Engine Blueprint. |
| `create_function` | Core | Create a new function in the Blueprint. |
| `delete_function` | Core | Delete a function from the Blueprint. |
| `delete_variable_from_bp` | Core | Delete a variable from the Blueprint. |
| `edit_blueprint_graph` | Core | Add nodes, connect them and set pin values in one call. If a step fails, the nodes it added are removed. |
| `edit_component_in_bp` | Core | Variants: `rename_component_in_bp`, `reattach_component_in_bp` |
| `edit_function` | Core | Edit an existing function in the Blueprint. |
| `edit_variable_in_bp` | Core | Variants: `rename_variable_in_bp`, `set_variable_default_value_in_bp` |
| `get_blueprint_functions` | Core | Get the list of functions in the Blueprint. |
| `get_blueprint_graph` | Core | Read nodes, pins, defaults and links from an event or function graph. |
| `get_blueprint_variables` | Core | Get the list of variables in the Blueprint. |
| `get_component_properties` | Core | Get the properties of a component in the Blueprint. |
| `get_components_of_bp` | Core | Get the list of components in the Blueprint. |
| `get_graph` | Core | Get the details of a specific graph structure (nodes and connections) in the Blueprint. |
| `get_supported_nodes` | Core | Get the list of supported nodes for the Blueprint system. |
| `inspect_blueprint_class_defaults` | Core | List a Blueprint's editable class defaults, including inherited ones and default subobjects. |
| `list_blueprint_functions` |  | List Blueprint-callable/pure/event functions for a loaded UE class. |
| `list_graph_node_types` |  | List concrete node classes for blueprint, animation, material, or all graphs. |
| `organize_blueprint_graph` | Core | Format a Blueprint graph so it reads left to right, with few crossings, no overlaps and straight execution lines. |
| `remove_component_from_bp` | Core | Remove a component from the Blueprint. |
| `set_blueprint_class_default` | Core | Set one class default of a /Game Blueprint using UE text, then compile it. |
| `set_component_property` | Core | Set properties for a component in the Blueprint. |
| `set_pin_default_value` | Core | Set the default value for a pin on a node in the specified graph. |

## catalog

| Tool | Core | Description |
|---|---|---|
| `call_tool` | Core | Run any Unreal tool by name, including those not listed. Take arguments from describe_tool. |
| `describe_tool` | Core | Return one tool's full description and input schema, for use with call_tool. |
| `find_tools` | Core | Search every Unreal tool, including those not listed. Empty query and domain returns domains with tool counts. |

## cinematics

| Tool | Core | Description |
|---|---|---|
| `add_level_sequence_event_endpoint_pin` |  | Native endpoint output parameter pin/new unique identifier; exact director/node identities/full pin snapshot. |
| `cinematic_camera_cut_metadata` |  | Inspect/Binding/LockPrevious/Thumbnail native dedicated camera-cut metadata. |
| `cinematic_camera_cut_track_policy` |  | Inspect/CanBlend/AutoManage/Rearrange native camera-cut track. Disabling blend or enabling auto-manage |
| `cinematic_shot_metadata` |  | Inspect/Name/Thumbnail native cinematic shot metadata. Name<=256/no controls; empty restores |
| `cinematic_take_metadata_edit` |  | Variants: `cinematic_take_metadata`, `set_cinematic_take_timing_metadata`, `set_cinematic_take_provenance_metadata`, `remove_cinematic_take_metadata` |
| `create_cinematic_camera` |  | Create a placed CineCameraActor with validated lens, filmback, and focus settings. |
| `create_level_sequence` | Core | Create an empty Level Sequence asset. |
| `discover_level_sequence_channel_info` |  | Variants: `discover_level_sequence_numeric_channels`, `discover_level_sequence_channels` |
| `discover_level_sequence_event_endpoints` |  | Discover loaded sequence director Blueprint custom-event/function-entry nodes/GUIDs/pins/page1..128. |
| `duplicate_level_sequence_channel_key` |  | Duplicate full native Float/Double/Bool/Byte/Integer/Object/Event key into vacant section tick frame. |
| `edit_cinematic_camera` |  | Edit a placed or sequence-template CineCameraActor; pass asset_path and binding_guid for a template. |
| `edit_cinematic_shot` |  | Add, rename, or remove a Level Sequence shot. Cycles are rejected; removal requires confirm. |
| `edit_level_sequence_binding` |  | Add a possessable, add_spawnable from an actor class or placed actor, or remove either binding. Removal requires confirm. |
| `edit_level_sequence_camera_cut` |  | Add or remove a nonoverlapping camera cut for an existing camera binding. Removal requires confirm. |
| `edit_level_sequence_key` |  | Set or remove a key in a supported float, transform, visibility, audio, or animation channel. Removal requires confirm. |
| `edit_level_sequence_section` |  | Add/remove a section or edit skeletal-animation and audio section settings. Event add accepts event_section_type trigger (default) or repeater. Removal requi... |
| `edit_level_sequence_settings` |  | Edit reflected Movie Scene settings such as playback range or display rate. |
| `edit_level_sequence_subsequence` |  | Add or remove a nested Level Sequence section. Removal requires confirm. |
| `edit_level_sequence_track` |  | Add or remove a track. Bound: transform, visibility, float_property, byte_property, integer_property, object_property (top-level property_name=property_path... |
| `evaluate_level_sequence_frame` |  | Play transform plus optional visibility/float tracks in preview or direct mode, restoring the bound editor actor afterward. |
| `inspect_cinematic_camera` |  | Inspect a placed CineCameraActor or a Level Sequence camera binding/template. |
| `inspect_cinematic_take_sources` |  | Inspect existing native take source-list metadata/basic source identities, enabled/take/tint fields. |
| `inspect_level_sequence` |  | Inspect a Level Sequence's Movie Scene timing, bindings, tracks, and sections. |
| `level_sequence_binding_tag` |  | Variants: `level_sequence_binding_tags`, `rename_level_sequence_binding_tag` |
| `level_sequence_channel_defaults` |  | Variants: `level_sequence_channel_default`, `level_sequence_object_channel_default` |
| `level_sequence_channel_extrapolation` |  | Inspect/Edit Float/Double Movie Scene channel PreInfinity/PostInfinity enum policy. |
| `level_sequence_channel_keys` |  | Variants: `level_sequence_numeric_key_policy`, `set_level_sequence_key_tangents`, `move_level_sequence_numeric_key`, `set_level_sequence_numeric_key_value`, `edit_level_sequence_numeric_key`, `level_sequence_discrete_keys`, `level_sequence_object_keys`, `level_sequence_event_keys`, `bind_level_sequence_event_endpoint`, `edit_level_sequence_event_payload`, `create_level_sequence_event_endpoint` |
| `level_sequence_event_repeater` |  | Variants: `inspect_level_sequence_event_repeater`, `level_sequence_event_repeater_endpoint`, `edit_level_sequence_repeater_payload` |
| `level_sequence_event_track_policy` |  | Inspect/edit native event track bFireEventsWhenForwards/Backwards bool0or1 or EventPosition enum. |
| `level_sequence_folder` |  | Variants: `level_sequence_folders`, `edit_level_sequence_folder_settings`, `move_or_remove_level_sequence_folder`, `assign_level_sequence_folder_content` |
| `level_sequence_integer_interpolation` |  | Inspect/Set native Integer bInterpolateLinearKeys policy. Set requires exact prior bool, |
| `level_sequence_markers` |  | Variants: `level_sequence_marked_frames`, `set_level_sequence_marker_metadata`, `set_level_sequence_markers_locked` |
| `level_sequence_section_automatic_easing` |  | Inspect track easing or toggle In/Out automatic mode and run native track-wide UpdateEasing. |
| `level_sequence_section_blend_type` |  | Inspect/Set native section blend type using reported supported values (not enum ordinals). |
| `level_sequence_section_builtin_easing` |  | Inspect native easing presets or assign selected In/Out side to reported built-in preset. |
| `level_sequence_section_completion_mode` |  | Inspect/Set native section completion mode using reported enum values. |
| `level_sequence_section_easing` |  | Inspect native section easing or set manual In/Out duration in tick frames. |
| `level_sequence_section_external_easing` |  | Inspect/assign native external CurveFloat easing to In/Out side. Inspect optional persistent curve |
| `level_sequence_section_overlap_priority` |  | Inspect/Set native int32 overlap priority (higher wins per native API), with peer diagnostics. |
| `level_sequence_section_pre_post_roll` |  | Inspect/Set native paired section pre/post-roll durations0..1M tick frames. |
| `level_sequence_subsection_origin` |  | Inspect/Mask/DefaultSet/DefaultClear native subsection transform origin; axis0..5=translationXYZ/rotationXYZ. |
| `level_sequence_subsection_parameters` |  | Inspect/Bias/Flags/Loop/StartOffset/EndOffset/FirstLoopOffset/FixedPlayRate/FixedTime native subsection/shot params. |
| `level_sequence_subsection_reference` |  | Inspect/Set native subsection/shot sequence reference; empty candidate clears. |
| `level_sequence_track_evaluation_policy` |  | Inspect/edit native track bEvalNearestSection/bEvaluateInPreroll/bEvaluateInPostroll. |
| `level_sequence_track_mute` |  | Inspect or set persistent Track/Row native evaluation disable flag. Rows0..4096/disabled arrays256. |
| `list_cinematic_shots` |  | List named shot sections, nested sequences, rows, and frame ranges. |
| `list_level_sequence_bindings` |  | List Level Sequence object bindings and their track counts. |
| `list_level_sequence_camera_cuts` |  | List Level Sequence camera-cut sections and referenced camera bindings. |
| `list_level_sequence_keys` |  | List float, transform, visibility, audio, or skeletal-animation channel keys in a Level Sequence section. |
| `list_level_sequence_sections` |  | List Level Sequence sections, frame ranges, rows, bindings, and channel counts. |
| `list_level_sequence_subsequences` |  | List nested Level Sequence sections and their timing ranges. |
| `list_level_sequence_tracks` |  | List master and object-bound Level Sequence tracks with section counts. |
| `offset_level_sequence_channel_keys` |  | Offset every key in one Float/Double/Bool/Byte/Integer/Object/Event channel using native Offset. |
| `remove_level_sequence_event_endpoint_pin` |  | Preflight/remove native user output parameter pin, exact director/node/pin snapshot identities. |
| `sample_level_sequence_channel` |  | Variants: `sample_level_sequence_numeric_channel`, `sample_level_sequence_discrete_channel`, `sample_level_sequence_object_channel` |
| `set_cinematic_camera_cut_range` |  | Set native cut inclusive-exclusive range and call OnSectionMoved ValueSet cleanup/UpdateEasing. |
| `validate_level_sequence` |  | Validate Level Sequence Movie Scene timing and basic track structure. |
| `validate_level_sequence_folders` |  | Bounded reachable native folder structural validation; does not repair or evaluate. |

## data

| Tool | Core | Description |
|---|---|---|
| `create_data_asset` | Core | Create a Data Asset from a non-abstract UDataAsset-derived class. |
| `delete_data_table_row` | Core | Delete a row from a DataTable. |
| `get_data_table_rows` | Core | Read all rows from a DataTable as JSON, including the row struct path. |
| `inspect_data_asset` | Core | Inspect a UDataAsset or UPrimaryDataAsset. |
| `upsert_data_table_row` | Core | Create or replace a DataTable row. |
| `validate_data_asset` |  | Validate a Data Asset and optional derived class compatibility. |

## debugging

| Tool | Core | Description |
|---|---|---|
| `compile_cpp_with_live_coding` | Core | Compile changed C++ with Live Coding. Result is success, no_changes, in_progress or failure. |
| `control_blueprint_debugger` | Core | Continue from a breakpoint. operation must be: resume, step_in, step_over, or step_out. |
| `create_cpp_class` | Core | Add a C++ class to a project module, writing its .h and .cpp files. Requires confirm unless dry_run. |
| `edit_blueprint_breakpoint` | Core | Add, remove, enable or disable a breakpoint, or clear_all. Adding needs a windowed editor, not -nullrhi. |
| `get_live_coding_status` | Core | Report whether Live Coding is available, enabled and compiling. |
| `inspect_blueprint_debug_state` | Core | Report whether a breakpoint has paused the game and, if so, the node, call stack, locals and Blueprint variables. |
| `list_blueprint_breakpoints` |  | List a Blueprint's breakpoints with their node ids. |

## editor

| Tool | Core | Description |
|---|---|---|
| `clear_editor_selection` |  | Clear the level-editor actor selection. |
| `editor_utilities` |  | Editor Utility Widgets/Blueprints: Inspect (paged discovery), SpawnTab (widget) or Run (TryRun). |
| `execute_console_command` | Core | Run one Unreal console command or console variable, in the play session if one is running. Requires confirm=True. |
| `game_feature_plugins` |  | Game Feature plugins: Inspect (names/URLs/native states) and Activate/Deactivate/Unload requests. |
| `get_editor_logs` | Core | Read the newest lines of this editor session's Output Log, with filters. |
| `get_project_errors` | Core | Summarise current problems: this session's log errors, editor Message Log pages and the last C++ build's errors. |
| `get_ue_editor_selection` |  | List actors currently selected in the UE level editor. |
| `get_ue_editor_status` | Core | Get current UE editor, world, map, play-state, engine, and selection status. |
| `list_blueprint_errors` | Core | Compile the Blueprints under a /Game folder and return those with errors, with each message and node. |
| `redo_ue_editor_transaction` | Core | Redo the latest undone UE editor transaction. |
| `run_editor_map_check` |  | Run UE Map Check for the active editor world without opening result dialogs. |
| `undo_ue_editor_transaction` | Core | Undo the latest UE editor transaction, such as an actor or asset edit. |

## foliage

| Tool | Core | Description |
|---|---|---|
| `add_foliage_instance` |  | Append manual unbased instance to existing initialized static-mesh foliage actor/type. |
| `create_foliage_type` |  | Create a static-mesh foliage type asset at a new canonical /Game/Folder/Name.Name path. |
| `create_procedural_foliage_spawner` |  | Create an empty procedural foliage spawner asset at a new canonical /Game/Folder/Name.Name path. |
| `delete_foliage_instance` |  | Delete manual static-mesh foliage with actor/type GUID/count/index/base/transform guards. |
| `edit_foliage_blocking_inline_keys` |  | Add a linear key at unique normalized float time/value0..1 or Remove key_index. |
| `inspect_foliage_blocking_inline_falloff` |  | Inspect stored inline falloff keys/tangents in pages1..128, without curve evaluation or simulation. |
| `inspect_foliage_instances` |  | Page1..128 native editor foliage placements/world transforms/base IDs/procedural GUID/flags. |
| `inspect_foliage_type` |  | Inspect loaded foliage type independently of actor registration; update GUID/settings/source. |
| `inspect_foliage_types` |  | Page1..128 foliage actor type map/settings/source/editor and optional HISM counts. |
| `inspect_procedural_foliage_blocking_volumes` |  | Inspect up to128 loaded procedural blocking volumes/target/falloff flag/external curve/key count. |
| `inspect_procedural_foliage_spawner` |  | Inspect loaded spawner seed/tile/quad-tree configuration/cached types/material soft paths. |
| `inspect_world_foliage` |  | Inspect up to128 loaded current-world native foliage partition actors/type counts. |
| `inspect_world_procedural_foliage` |  | Inspect up to128 loaded current-world procedural foliage components/spawner/GUID/surface flags. |
| `register_foliage_type` |  | Register/initialize loaded shared static-mesh foliage asset on existing actor in ordinary map. |
| `replace_foliage_blocking_linear_falloff` |  | Replace full inline curve with linear time/value keys<=256, normalized0..1. |
| `replace_foliage_type_materials` |  | Replace OverrideMaterials/NaniteOverrideMaterials with full inspected ordered path-array guard. |
| `replace_procedural_foliage_spawner_types` |  | Replace spawner type wrappers with <=128 loaded persistent foliage type assets, empty clears. |
| `set_foliage_blocking_inline_curve_setting` |  | Set DefaultValue0..1, ClearDefaultValue(value1), PreInfinityExtrap or PostInfinityExtrap. |
| `set_foliage_blocking_inline_key_setting` |  | Edit one key with mandatory full untruncated native_snapshot_text from inspection. |
| `set_foliage_instance_transform` |  | Move manual static-mesh foliage via native hash/implementation move notifications. |
| `set_foliage_type` |  | Variants: `scalar`, `bool` |
| `set_foliage_type_cull_range` |  | Set ordered integer cull min/max0..1e9 world units with full inspected interval/type GUID guard. |
| `set_foliage_type_material_slot` |  | Set existing OverrideMaterials/NaniteOverrideMaterials slot to loaded material or empty null. |
| `set_foliage_type_mesh` |  | Replace foliage type source mesh with loaded persistent UStaticMesh, no clear. |
| `set_foliage_type_placement_range` |  | Set ordered ZOffset/Height range+/-1e9 world units or GroundSlopeAngle0..359 degrees. |
| `set_foliage_type_procedural_bool` |  | Set bCanGrowInShade/bSpawnsInShade/DensityFalloffEnabled, standalone GUID/current flag guards. |
| `set_foliage_type_procedural_curve` |  | Assign ScaleCurve/DensityFalloffCurve loaded external CurveFloat or empty embedded fallback. |
| `set_foliage_type_procedural_scale` |  | Set procedural growth min/max scale0.001..1000 adapter cap, full inspected interval/type GUID guard. |
| `set_foliage_type_procedural_setting` |  | Set native procedural type numeric setting independently of actor registration. |
| `set_foliage_type_scale_range` |  | Set ScaleX/ScaleY/ScaleZ ordered min/max0.001..1000 adapter cap. |
| `set_foliage_type_scaling` |  | Set scaling0 Uniform/1 Free/2 LockXY/3 LockXZ/4 LockYZ, inspected mode/type GUID guard. |
| `set_procedural_foliage_blocking_falloff` |  | Set blocking-volume falloff flag/loaded external CurveFloat or empty embedded fallback. |
| `set_procedural_foliage_blocking_target` |  | Set blocking volume target to loaded current-world procedural volume or empty all-procedural scope. |
| `set_procedural_foliage_component_bool` |  | Set bAllowLandscape/bAllowBSP/bAllowStaticMesh/bAllowTranslucent/bAllowFoliage/bShowDebugTiles. |
| `set_procedural_foliage_spawner` |  | Assign loaded persistent procedural spawner or empty clear, inspected component GUID/reference guard. |
| `set_procedural_foliage_spawner_setting` |  | Set RandomSeed int32/NumUniqueTiles1..64/TileSize1..1e6cm/MinimumQuadTreeSize0.01..1e6cm. |
| `set_procedural_foliage_terrain_materials` |  | Set spawner terrain-material override flag/full soft-reference list with inspected pair guard. |
| `set_procedural_foliage_tile_overlap` |  | Set authored tile overlap0..1e6cm adapter cap with inspected overlap/spawner/component GUID guards. |
| `unregister_empty_foliage_type` |  | Remove empty static-mesh foliage type registration from ordinary non-WorldPartition actor. |

## gameplay_abilities

| Tool | Core | Description |
|---|---|---|
| `activate_runtime_abilities_by_tags` |  | Try native tag-filtered ability activation on authoritative initialized PIE ASC. |
| `add_runtime_attribute_set` |  | Create/register concrete native AttributeSet on authoritative initialized PIE component. |
| `apply_runtime_gameplay_effect` |  | Apply native effect spec from authoritative PIE source to target (defaults self). |
| `cancel_runtime_abilities_by_tags` |  | Request native tag-filtered cancellation on authoritative initialized PIE ASC. |
| `check_runtime_gameplay_ability` |  | Run native CanActivateAbility and return current result/relevant failure tags. |
| `control_ability_system_runtime` |  | Activate/cancel one granted ability on an authoritative initialized PIE component. |
| `create_gameplay_blueprint` |  | Create native-parent or Blueprint-parent GAS Blueprint in unused /Game package. |
| `dispatch_runtime_ability_input` |  | Dispatch press/release native spec input callback for one authoritative PIE ability. |
| `edit_gameplay_blueprint_defaults` |  | Edit scalar/plain-struct GAS ability/effect/calculation/cue Blueprint defaults with native compile. |
| `evaluate_gameplay_effect_definition` |  | Evaluate native level-only static effect magnitudes and period without applying. |
| `execute_runtime_gameplay_cue` |  | Execute one-shot native Gameplay Cue on authoritative initialized PIE component. |
| `grant_runtime_gameplay_ability` |  | Grant loaded concrete native/compiled ability class on authoritative initialized PIE component. |
| `inhibit_runtime_gameplay_effect` |  | Inhibit/uninhibit native active effect on authoritative selected PIE component. |
| `inspect_ability_system_runtime` |  | Inspect selected PIE ability-system components, owned tags and granted abilities. |
| `inspect_gameplay_ability_definition` |  | Inspect loaded ability defaults, policies, asset tags, triggers and cost/cooldown classes. |
| `inspect_gameplay_attribute_definition` |  | Inspect loaded AttributeSet class native attribute paths and default values. |
| `inspect_gameplay_effect_definition` |  | Inspect loaded native/Blueprint GameplayEffect class default definition. |
| `inspect_runtime_ability_tag_counts` |  | Inspect native aggregate GAS counts for <=256 registered tags in selected PIE. |
| `list_ability_system_classes` |  | Discover loaded ability/effect/attribute_set/execution/magnitude/effect_component/cue_actor/cue_static classes and fields. |
| `load_ability_system_class` |  | Load/validate native or existing Blueprint GAS class without compiling or editing. |
| `match_runtime_abilities_by_tags` |  | Read native all-tag-matching PIE ability grants without activation checks. |
| `query_runtime_gameplay_effects` |  | Query native active effect tags in selected PIE without mutation. |
| `remove_runtime_gameplay_ability` |  | Remove one granted ability by native handle on authoritative PIE component. |
| `remove_runtime_gameplay_effect` |  | Remove an active native Gameplay Effect or stack count on authoritative PIE component. |
| `send_runtime_gameplay_event` |  | Dispatch native GAS gameplay event to an authoritative initialized PIE component. |
| `set_runtime_ability_input_id` |  | Rebind granted native ability InputID with replication dirty marking. |
| `set_runtime_ability_source_tags` |  | Replace inactive granted ability's dynamic spec source tags (empty clears). |
| `set_runtime_gameplay_ability_level` |  | Update granted native ability spec level with replication dirty marking. |
| `set_runtime_gameplay_attribute` |  | Set native attribute base value on an authoritative PIE ability-system component. |
| `set_runtime_gameplay_effect_level` |  | Update active native Gameplay Effect level by component-owned handle. |
| `update_runtime_effect_magnitudes` |  | Update native active effect SetByCaller tag magnitudes on authoritative PIE component. |

## gameplay_tags

| Tool | Core | Description |
|---|---|---|
| `add_runtime_loose_gameplay_tag` |  | Add a registered non-replicated loose tag to authoritative initialized PIE ASC. |
| `create_gameplay_tag` | Core | Create a persistent tag in an existing ordinary ini tag-list source. |
| `create_gameplay_tag_source` |  | Register an ordinary project ini tag source using Unreal's editor API. |
| `delete_gameplay_tag` |  | Delete an unused ordinary ini leaf tag through native editor API. |
| `edit_data_asset_tag_property` |  | Variants: `edit_data_asset_gameplay_tags`, `edit_data_asset_gameplay_tag_query` |
| `edit_gameplay_tag_table_row` |  | Create/update a native GameplayTagTableRow on an existing /Game DataTable. |
| `evaluate_data_asset_gameplay_tag_query` |  | Evaluate the native GameplayTagQuery currently stored on a Data Asset field. |
| `evaluate_gameplay_tag_expression` |  | Variants: `evaluate_gameplay_tags`, `evaluate_gameplay_tag_query` |
| `evaluate_runtime_tag_query` |  | Variants: `evaluate_runtime_gameplay_tag_query`, `evaluate_provider_gameplay_tag_query` |
| `inspect_data_asset_gameplay_tags` |  | Inspect top-level Data Asset GameplayTag/container/query fields and editability. |
| `inspect_gameplay_tag_settings` |  | Inspect native tag loading/replication settings, table sources and redirects. |
| `inspect_gameplay_tag_sources` |  | Discover registered tag sources, native source types and config files. |
| `inspect_gameplay_tags` | Core | Discover registered native Gameplay Tags, parent chains and editor source metadata. |
| `inspect_runtime_gameplay_tag_providers` |  | Discover PIE components implementing GameplayTagAssetInterface and owned tags. |
| `inspect_runtime_gameplay_tags` |  | Inspect owned Gameplay Tags on PIE actors implementing GameplayTagAssetInterface. |
| `inspect_unused_gameplay_tags` |  | Run native editor unused-tag scan and list bounded candidates/source metadata. |
| `move_gameplay_tags_to_source` |  | Move explicit ordinary ini tags to another existing ordinary source. |
| `register_gameplay_tag_table` |  | Register existing native GameplayTagTableRow DataTable as project tag source. |
| `rename_gameplay_tag` |  | Rename ordinary ini tags using native editor rename/redirect behavior. |
| `resolve_gameplay_tags` |  | Resolve <=256 tag names using native Gameplay Tags import/redirect rules. |
| `update_gameplay_tag_comment` |  | Update an explicit ordinary ini tag's comment with native editor API. |

## geometry_script

| Tool | Core | Description |
|---|---|---|
| `add_geometry_script_mesh_component` |  | Create/register empty Dynamic Mesh component on existing editor-world actor. |
| `add_geometry_script_named_polygroup_layer` |  | Add named extended polygroup layer or reuse matching native FName (case-insensitive). |
| `add_geometry_script_triangle` |  | Append triangle from distinct existing native vertex IDs, group0..1e6. |
| `add_geometry_script_vertex` |  | Append native isolated vertex, returning ID; finite XYZ +/-1e9. |
| `append_geometry_script_box` |  | Append native unsubdivided box to owned current-world Dynamic Mesh component. |
| `append_geometry_script_cylinder` |  | Append native cylinder to staged mesh; radius/height positive<=1e6. |
| `append_geometry_script_mesh` |  | Append distinct mesh using current component transforms; uniform target scale. |
| `append_geometry_script_sphere` |  | Append native latitude-longitude sphere on temporary mesh then commit with undo. |
| `apply_geometry_script_perlin_noise` |  | Optional inspected face selection limits native affected vertices/UV elements. |
| `auto_generate_geometry_script_uvs` |  | Replace existing UV channel with native XAtlas or PatchBuilder layout. |
| `bevel_geometry_script_polygroups` |  | Bevel native default-polygroup topology edges without spatial filter. |
| `boolean_geometry_script_meshes` |  | Boolean/trim/polygroup classification using component transforms in world space. |
| `clear_geometry_script_collision` |  | Clear authored simple collision with native physics update/undo/dry-run. |
| `clear_geometry_script_mesh` |  | Clear geometry while retaining Dynamic Mesh component; native replacement undo. |
| `clear_geometry_script_polygroup_layer` |  | Reset all group values in existing default(-1)/extended0..7 layer. |
| `clear_geometry_script_uv_channel` |  | Clear selected UV0..7 overlay elements without deleting channel/mesh topology. |
| `compact_geometry_script_mesh` |  | Compact sparse dynamic-mesh IDs through native Geometry Script. |
| `compute_geometry_script_tangents` |  | Compute FastMikkT/PerTriangle/StandardMikkT tangents on staged mesh copy. |
| `copy_geometry_script_mesh` |  | Copy full native local mesh geometry/attributes between current-world components. |
| `copy_geometry_script_polygroup_layer` |  | Overwrite group values between existing layers -1(default) or extended0..7. |
| `copy_geometry_script_uv_channel` |  | Overwrite an existing UV channel with another channel on the same mesh. |
| `copy_static_mesh_to_geometry_script_mesh` |  | Replace Dynamic Mesh with persistent Static Mesh SourceModel/RenderData LOD0..7. |
| `cut_geometry_script_mesh_with_plane` |  | Cut by component-local frame origin/Z normal, optionally fill cut boundaries. |
| `decompose_geometry_script_mesh_into_convex_hulls` |  | Replace mesh with combined convex decomposition pieces, target hulls1..64. |
| `delete_geometry_script_triangle` |  | Delete native triangle with exact inspected vertex-order guard. |
| `delete_geometry_script_triangles` |  | Delete1..256 unique inspected faces with matching expected vertex-order triples. |
| `extrude_geometry_script_mesh` |  | Linear-extrude all faces, preserve native group defaults. |
| `fill_geometry_script_holes` |  | Fill native boundary loops, report filled/failed counts; partial results commit. |
| `find_geometry_script_region_faces` |  | Polygroup layer -1 is default;0..7 selects an existing extended layer. |
| `flare_geometry_script_mesh` |  | Flare/bulge local frame axes using Sin/SinSquared/Triangle profile. |
| `flip_geometry_script_normals` |  | Reverse whole-mesh winding and normals through native Geometry Script. |
| `flip_geometry_script_selected_normals` |  | Reverse inspected selected face winding and/or normal direction. |
| `generate_geometry_script_collision` |  | Replace Dynamic Mesh component simple collision from staged mesh geometry. |
| `generate_geometry_script_polygroups` |  | Target polygroup layer -1(default) or existing extended0..7. |
| `generate_static_mesh_collision_from_geometry_script_mesh` |  | Generate/overwrite loaded /Game Static Mesh simple collision from Dynamic Mesh. |
| `inset_outset_geometry_script_faces` |  | Inset/outset all faces with native signed-distance convention. |
| `inspect_geometry_script_collision` |  | Read authored simple collision counts by shape type and component settings. |
| `inspect_geometry_script_edges` |  | Read edge endpoint/incident triangle IDs and boundary flags in ID spans. |
| `inspect_geometry_script_materials` |  | Read up to64 component base material slots; null is empty path, truncation explicit. |
| `inspect_geometry_script_normals` |  | Read normal/tangent overlay vectors and triangle assignments in ID spans. |
| `inspect_geometry_script_polygroups` |  | Summarize default(-1) or existing extended(0..7) polygroups by sorted ID with triangle counts/sample face. |
| `inspect_geometry_script_topology` |  | Read native vertex positions/triangle vertex IDs over <=256-ID spans each. |
| `inspect_geometry_script_uvs` |  | Read UV coordinates and per-triangle overlay element assignments in ID spans. |
| `inspect_geometry_script_vertex_colors` |  | Read primary color overlay RGBA and triangle assignments in ID spans1..256. |
| `inspect_geometry_script_world_meshes` |  | Inspect <=128 loaded current-world Dynamic Mesh components/native topology counts. |
| `measure_geometry_script_mesh` |  | Read native area/signed volume/center/bounds/closed/boundary edge-loop counts. |
| `measure_geometry_script_uvs` |  | Read whole-channel mesh/UV area and bounds, including unset UV flag. |
| `model_geometry_script_mesh_with_plane` |  | Slice into halves in one mesh or mirror about local frame origin/Z plane. |
| `offset_geometry_script_faces` |  | Offset faces by VertexNormal/FaceNormal/ParallelFaceOffset native modeling. |
| `offset_or_shell_geometry_script_mesh` |  | Offset along averaged normals or create thickened Shell with original surface. |
| `project_geometry_script_uvs` |  | Optional inspected face selection; empty retains native whole-mesh behavior. |
| `recompute_geometry_script_normals` |  | Recompute normals natively on staged copy, preserving native hard-edge sharing. |
| `recompute_geometry_script_uvs` |  | Optional inspected face selection; empty retains native whole-mesh behavior. |
| `remap_geometry_script_material_ids` |  | Replace one material ID across an existing dynamic mesh, preserving other IDs. |
| `remesh_geometry_script_mesh` |  | Native uniform remesh by approximate triangle count or target edge length. |
| `remove_geometry_script_small_components` |  | Remove disconnected components below any native volume/area/count threshold. |
| `remove_geometry_script_unused_vertices` |  | Remove vertices unused by triangles, preserving remaining IDs/connectivity. |
| `repack_geometry_script_uvs` |  | Repack existing UV islands with native image-width/rotation controls. |
| `repair_geometry_script_boundaries` |  | Snap open boundaries or resolve TJunctions through native mesh repair. |
| `replace_geometry_script_mesh_with_convex_hull` |  | Replace mesh with native convex hull, generated attributes/per-face normals. |
| `replace_geometry_script_mesh_with_swept_hull` |  | Replace mesh with hull of XY-plane projection swept along frame Z extents. |
| `scale_geometry_script_texel_density` |  | Optional inspected face selection; empty retains native whole-mesh behavior. |
| `self_union_geometry_script_mesh` |  | Apply native self-union for overlapping/self-intersecting mesh geometry. |
| `set_geometry_script_material` |  | Set/clear existing base slot or append next slot0..63 with count/value guards. |
| `set_geometry_script_material_ids` |  | Assign native triangle material ID0..255 across whole staged mesh. |
| `set_geometry_script_normal_mode` |  | Repair winding or generate PerVertex smooth / PerFace split normal overlays. |
| `set_geometry_script_polygroup_layer_count` |  | Set extended polygroup layers0..8; reducing count discards removed layers. |
| `set_geometry_script_selected_material_ids` |  | Assign material ID0..255 to1..256 inspected faces, retaining other IDs. |
| `set_geometry_script_selected_polygroup` |  | Polygroup layer -1 is default;0..7 selects an existing extended layer. |
| `set_geometry_script_selected_vertex_color` |  | Color1..256 inspected faces; seam mode isolates colors and ignores channel masks. |
| `set_geometry_script_triangle_material_id` |  | Assign one triangle material ID with inspected vertex-order/current ID guards. |
| `set_geometry_script_triangle_uvs` |  | Assign three UV corners as a new isolated UV island on an existing face. |
| `set_geometry_script_uv_channel_count` |  | Set native UV channel count1..8; reducing count discards removed channels. |
| `set_geometry_script_vertex_color` |  | Set constant linear RGBA0..1 on vertex color overlay with channel masks. |
| `set_geometry_script_vertex_position` |  | Set existing native vertex using exact inspected position guard, finite XYZ +/-1e9. |
| `simplify_geometry_script_mesh` |  | Simplify toward triangle count with native QEM/volume/attribute-aware method. |
| `simplify_geometry_script_regions` |  | Group layer -1(default) or existing extended0..7 for group-dependent operation. |
| `smooth_geometry_script_mesh` |  | Optional inspected face selection limits native affected vertices/UV elements. |
| `split_geometry_script_normals` |  | Group layer -1(default) or existing extended0..7 for group-dependent operation. |
| `tessellate_geometry_script_mesh` |  | Subdivide linearly with Uniform or curved PN tessellation, level1..6. |
| `transform_geometry_script_mesh` |  | Transform existing component-local mesh on temporary copy, commit with native undo. |
| `transform_geometry_script_uvs` |  | Optional inspected face selection limits native affected vertices/UV elements. |
| `validate_geometry_script_mesh` |  | Native internal mesh validity/finite-position diagnostics on bounded copy. |
| `warp_geometry_script_mesh` |  | Bend/Twist mesh using component-local normalized/unit-scale frame. |
| `wave_geometry_script_mesh` |  | Apply native SinWave1D/2D warp in normalized/unit-scale local frame (UE has no SinWave3D implementation). |
| `weld_geometry_script_edges` |  | Weld coincident boundary edges with native tolerance/unique-pair controls. |
| `write_geometry_script_mesh_to_static_mesh` |  | Overwrite existing loaded /Game Static Mesh source LOD from Dynamic Mesh. |

## ik_retarget

| Tool | Core | Description |
|---|---|---|
| `add_ik_retargeter_default_operations` |  | Initialize EMPTY retarget stack with UE 5.7 native six-operation defaults. |
| `add_ik_retargeter_operation` |  | Add loaded native top-level retarget operation to confirmed /Game retargeter. |
| `add_ik_rig_solver` |  | Append loaded native derived solver struct to IK Rig stack (<128 entries). |
| `assign_ik_rig_to_retargeter_operations` |  | Invoke native rig-assignment callbacks on ALL retarget operations. |
| `auto_align_ik_retargeter_pose` |  | Invoke native current-pose auto-alignment: chain/mesh/local_axes/global_axes. |
| `auto_characterize_ik_rig` |  | Generate/apply native IK retarget root/chains from preview mesh characterization. |
| `auto_map_ik_retargeter_chains` |  | Auto-map one guarded operation using exact/fuzzy/clear native algorithm. |
| `auto_setup_ik_rig_fbik` |  | Apply native template FBIK setup: adds solver, creates/reuses goals/settings. |
| `change_ik_retargeter_pose` |  | Rename/remove existing non-default source/target retarget pose. |
| `change_ik_rig_goal` |  | Rename/remove exact existing IK goal through native controller. |
| `change_ik_rig_retarget_chain` |  | Rename/remove exact existing native IK Rig retarget chain. |
| `change_ik_rig_solver_bone_settings` |  | Add/remove native solver-specific bone setting entry; operation add or remove. |
| `check_ik_retargeter_readiness` |  | Initialize fresh temporary native retarget processor with asset preview meshes. |
| `check_ik_rig_mesh_compatibility` |  | Read native IK Rig processor skeleton compatibility for candidate skeletal mesh. |
| `check_ik_rig_readiness` |  | Initialize temporary native IK processor with explicit mesh and asset goals. |
| `connect_ik_rig_goal` |  | Connect/disconnect existing IK goal to current type-guarded solver. |
| `copy_ik_retargeter_operation_settings` |  | Copy dedicated settings between same-type native operations in one retargeter. |
| `copy_ik_rig_solver_bone_settings` |  | Copy values between existing per-bone settings entries within one native solver. |
| `copy_ik_rig_solver_goal_settings` |  | Copy existing solver goal-settings values while preserving destination identity. |
| `copy_ik_rig_solver_settings` |  | Copy dedicated native settings between same-type solvers in one IK Rig. |
| `create_ik_asset` |  | Create native IK Rig or Retargeter asset through editor factory. |
| `create_ik_retargeter_pose` |  | Create empty retarget pose or duplicate existing side pose, then select it. |
| `create_ik_rig_goal` |  | Create native initialized IK goal on existing rig bone. |
| `create_ik_rig_retarget_chain` |  | Create native IK Rig retarget chain with existing ordered bone endpoints. |
| `delete_skeleton_retarget_source` |  | Delete named Skeleton retarget source with animation consumer checks. |
| `diagnose_ik_retargeter_poses` |  | Diagnose stored source/target retarget pose references and numeric validity. |
| `diagnose_ik_rig_definition` |  | Read bounded IK Rig goal/chain/root/solver structural diagnostics. |
| `duplicate_ik_asset` |  | Duplicate native IK Rig/Retargeter through AssetTools to unused /Game path. |
| `duplicate_skeleton_retarget_source` |  | Copy stored retarget-source pose and soft mesh link into unused name. |
| `edit_ik_rig_retarget_chain` |  | Replace existing IK chain endpoints/goal after complete hierarchy preflight. |
| `edit_skeleton_retarget_pose` |  | Variants: `edit_skeleton_stored_retarget_pose`, `reset_skeleton_stored_retarget_pose` |
| `edit_skeleton_retarget_source` |  | Create/refresh named native retarget-source pose from exact-Skeleton mesh. |
| `evaluate_ik_retargeter` |  | Variants: `evaluate_ik_retargeter_reference_pose`, `evaluate_ik_retargeter_pose` |
| `evaluate_ik_rig_reference_pose` |  | Run one fresh native IK solve from mesh reference pose with stored goal transforms. |
| `export_ik_retargeter_sequences` |  | Native duplicate-and-retarget export of 1..16 sequences to unused /Game outputs. |
| `inspect_animation_retarget_source` |  | Read sequence retarget selection and native effective reference pose. |
| `inspect_ik_retargeter_chain_mapping` |  | Read native operation target/source chain pairs without refreshing or auto-mapping. |
| `inspect_ik_retargeter_curve_remap` |  | Read typed native curve-remap pairs/flags with identifier diagnostics. |
| `inspect_ik_retargeter_definition` |  | Inspect native IK Retargeter source/target rigs, preview meshes and current poses. |
| `inspect_ik_retargeter_operation` |  | Inspect authored editable fields of current index/type/name guarded operation. |
| `inspect_ik_retargeter_operation_hierarchy` |  | Diagnose native retarget operation name/parent graph without modification. |
| `inspect_ik_retargeter_operation_settings` |  | Read dedicated native operation settings type and authored editable fields. |
| `inspect_ik_retargeter_operation_warning` |  | Read native warning from stored asset operation, without processor initialization. |
| `inspect_ik_retargeter_pose` |  | Inspect named stored retarget pose without selecting it. |
| `inspect_ik_rig_definition` |  | Inspect native IK Rig preview mesh/pelvis, <=256 goals/chains and <=128 solver structs. |
| `inspect_ik_rig_goal_transform` |  | Read stored native goal initial/current transforms in rig global/component space. |
| `inspect_ik_rig_skeleton` |  | Read stored IK Rig bone hierarchy, exclusion and global reference transforms. |
| `inspect_ik_rig_solver` |  | Read authored editable fields of current index/type guarded native IK solver. |
| `inspect_ik_rig_solver_bone_settings` |  | Read native per-bone solver settings type and authored editable field values. |
| `inspect_ik_rig_solver_connections` |  | Read native solver enabled state, start/end bone roles and rig goal connections. |
| `inspect_ik_rig_solver_goal_settings` |  | Read native solver-specific goal settings type and authored editable values. |
| `inspect_ik_rig_solver_settings` |  | Read dedicated native solver settings type and authored editable fields. |
| `inspect_skeleton_retarget_pose` |  | Read stored named retarget-source pose transforms without loading source mesh. |
| `list_ik_retargeter_operation_types` |  | Discover loaded native derived retarget operation structs and editable defaults. |
| `list_ik_rig_solver_types` |  | Discover loaded native IK solver structs and <=64 editable default fields each. |
| `move_ik_retargeter_operation` |  | Request native operation move, followed by native ordering-constraint cleanup. |
| `move_ik_rig_solver` |  | Move current IK solver to final index within stack, expected native type guarded. |
| `refresh_ik_retargeter_chain_mapping` |  | Reconcile native operation chain mapping and regenerate settings after rig edits. |
| `refresh_ik_rig_initial_goal_transforms` |  | Refresh ALL goal initial transforms from reference bones, preserving relative deltas. |
| `remove_ik_retargeter_operation` |  | Remove native index/type/name guarded retarget operation and optional children. |
| `remove_ik_rig_solver` |  | Remove native solver at current index guarded by expected struct type. |
| `rename_ik_retargeter_operation` |  | Rename current index/type/name guarded native retarget operation. |
| `rename_skeleton_retarget_source` |  | Rename named retarget source and migrate discovered /Game animation consumers. |
| `reset_ik_retargeter_chain_settings` |  | Invoke native target-chain settings reset across ALL retarget operations. |
| `reset_ik_retargeter_operation_settings` |  | Reset ENTIRE dedicated operation settings struct to native constructed defaults. |
| `reset_ik_retargeter_pose` |  | Reset whole retarget pose (empty bones) or up to 256 unique side-rig bones. |
| `reset_ik_rig_goal_transforms` |  | Reset ALL native goal initial/current transforms to bone reference transforms. |
| `reset_ik_rig_solver_bone_settings` |  | Reset existing native bone settings values from defaults, preserving entry identity. |
| `reset_ik_rig_solver_goal_settings` |  | Reset existing native solver goal settings from defaults, preserving goal identity. |
| `reset_ik_rig_solver_settings` |  | Reset dedicated native solver editable settings from constructed defaults. |
| `reset_ik_settings_field` |  | Reset ONE writable direct native settings field to constructed default. |
| `run_ik_retargeter_operation_setup` |  | Re-run native operation OnAddedToStack setup; may replace mappings/settings. |
| `set_animation_named_retarget_source` |  | Select sequence Skeleton's named retarget source, or default with empty/None name. |
| `set_animation_retarget_source_mesh` |  | Select/refresh per-sequence source-mesh reference pose and clear named source. |
| `set_ik_retargeter_bone_rotation` |  | Set absolute current pose bone rotation offset from Pitch/Yaw/Roll degrees. |
| `set_ik_retargeter_chain_mapping` |  | Assign/clear one target chain's source within one guarded retarget operation. |
| `set_ik_retargeter_current_pose` |  | Select existing source/target retarget pose on confirmed /Game retargeter. |
| `set_ik_retargeter_curve_remap` |  | Replace native curve-remap operation pairs and copy/remap flags. |
| `set_ik_retargeter_operation_enabled` |  | Enable/disable current index/type/name guarded native retarget operation. |
| `set_ik_retargeter_operation_parent` |  | Assign compatible native parent to current index/type/name guarded operation. |
| `set_ik_retargeter_operation_scalar` |  | Edit direct writable bool/numeric dedicated retarget operation settings field. |
| `set_ik_retargeter_preview_mesh` |  | Set compatible source/target preview mesh override on confirmed /Game retargeter. |
| `set_ik_retargeter_rig` |  | Assign source/target IK Rig to confirmed /Game retargeter while PIE is stopped. |
| `set_ik_retargeter_root_offset` |  | Set absolute current retarget pose root translation (X/Y/Z, native units). |
| `set_ik_rig_bone_excluded` |  | Exclude/include one existing bone in a confirmed /Game IK Rig, with stopped PIE. |
| `set_ik_rig_goal_bone` |  | Reassign IK goal to existing native bone with initial-transform/solver callbacks. |
| `set_ik_rig_goal_transform` |  | Set absolute native goal CurrentTransform in rig global/component space. |
| `set_ik_rig_goal_weights` |  | Set native IK goal position/rotation alpha [0,1] on exact owned goal. |
| `set_ik_rig_preview_mesh` |  | Assign compatible persistent skeletal mesh to confirmed /Game IK Rig. |
| `set_ik_rig_retarget_root` |  | Set/clear IK Rig pelvis/retarget root through native controller. |
| `set_ik_rig_solver_bone` |  | Assign existing rig bone to solver start/end role through native controller. |
| `set_ik_rig_solver_bone_scalar` |  | Edit direct bool/numeric field of existing native per-bone solver settings. |
| `set_ik_rig_solver_enabled` |  | Enable/disable native IK solver guarded by current index/expected struct type. |
| `set_ik_rig_solver_goal_scalar` |  | Edit direct bool/numeric field of existing native solver-specific goal settings. |
| `set_ik_rig_solver_scalar` |  | Edit direct writable bool/numeric dedicated solver settings field. |
| `set_ik_settings` |  | Variants: `name_list`, `number_list` |
| `set_ik_settings_asset_reference` |  | Assign/clear writable native hard/soft object asset reference settings field. |
| `set_ik_settings_spatial_value` |  | Edit native vector/rotator/quaternion/transform settings field. |
| `set_ik_settings_text_value` |  | Edit writable direct FName/FString IK or retarget settings field. |
| `set_skeleton_compatibility_retarget_policy` |  | Set native use-retarget-modes-from-compatible-Skeleton policy. |
| `set_skeleton_translation_retargeting` |  | Set native Skeleton bone translation retargeting mode transactionally. |
| `snap_ik_retargeter_pose_to_ground` |  | Invoke native current-pose root-height correction using reference-pose height. |

## input

| Tool | Core | Description |
|---|---|---|
| `edit_input_action_settings` |  | Edit reflected Enhanced Input Action settings such as ValueType or bConsumeInput. |
| `edit_input_mapping_context_settings` |  | Edit reflected Enhanced Input Mapping Context settings. |
| `inspect_input_action` | Core | Inspect an Enhanced Input Action asset. |
| `inspect_input_mapping_context` | Core | Inspect Enhanced Input Action-to-key mappings. |
| `map_input_action` | Core | Map an Enhanced Input Action to a key name such as SpaceBar or W. |
| `replace_input_action_key` |  | Replace one key mapping for an Enhanced Input Action. |
| `unmap_input_action` | Core | Remove an Enhanced Input Action key mapping. |

## landscape

| Tool | Core | Description |
|---|---|---|
| `create_landscape` |  | Create a flat native landscape in an ordinary (non-WorldPartition) editor map. |
| `create_landscape_edit_layer` |  | Append standard native ULandscapeEditLayer with full inspected stack GUID guard<=256. |
| `delete_landscape_edit_layer` |  | Delete unlocked standard native edit layer/no brushes in ordinary non-WorldPartition map. |
| `inspect_landscape_components` |  | Inspect landscape proxy component-array page1..128, topology/combined heightmap/weightmaps. |
| `inspect_landscape_edit_layer_heights` |  | Read bounded explicit edit-layer source with inspected native layer GUID/path/target support. |
| `inspect_landscape_edit_layer_weights` |  | Read bounded explicit edit-layer source with inspected native layer GUID/path/target support. |
| `inspect_landscape_edit_layers` |  | Inspect native UE5.7 edit-layer stack objects/GUID/name/flags/brush count/capabilities/alpha. |
| `inspect_landscape_heights` |  | Read native combined landscape source heights in grid rectangle dimensions1..64/origin+/-1e6. |
| `inspect_landscape_layer_info` |  | Inspect loaded native layer-info blend/physical-material/hardness/collision/debug/spline settings. |
| `inspect_landscape_paint_layers` |  | Page1..128 existing shared landscape-info paint target layers/names/asset/owner paths. |
| `inspect_landscape_weights` |  | Read combined paint weight bytes0..255 for loaded registered layer-info asset. |
| `inspect_world_landscapes` |  | Inspect up to128 loaded current-world landscape/streaming proxies, identity/topology/transform. |
| `rename_landscape_edit_layer` |  | Rename unlocked native edit layer with inspected actor/GUID/path/exact display-name guard. |
| `reorder_landscape_edit_layer` |  | Move native edit layer to final zero-based destination index, full inspected GUID order<=256. |
| `replace_foliage_type_landscape_layers` |  | Replace LandscapeLayers/ExclusionLandscapeLayers with full inspected ordered-name guard. |
| `set_landscape_edit_layer_alpha` |  | Set unlocked supported native Heightmap/Weightmap layer alpha within native inspected range. |
| `set_landscape_edit_layer_bool` |  | Set native edit-layer Visible/Locked with exact main actor/layer GUID/path/current flag guards. |
| `set_landscape_edit_layer_heights` |  | Patch raw uint16 heights0..65535, flattened row-major Y/X rectangle dimensions1..64. |
| `set_landscape_edit_layer_weights` |  | Patch selected paint-layer source weights0..255 flattened Y/X, dimensions1..64. |
| `set_landscape_layer_info_asset` |  | Set shared PhysicalMaterial/SplineFalloffModulationTexture to loaded compatible asset or empty clear. |
| `set_landscape_layer_info_blend` |  | Set shared native layer-info blend method0..2/group<=128 pair with inspected pair guard. |
| `set_landscape_layer_info_debug_color` |  | Set shared layer-info linear debug RGBA RGB0..1/alpha1, full inspected current RGBA guard. |
| `set_landscape_layer_info_scalar` |  | Set Hardness/MinimumCollisionRelevanceWeight0..1, SplineFalloffModulationTiling0.01..1e6, |
| `set_landscape_layer_info_spline_mask` |  | Set native spline-falloff texture channel0 Red/1 Green/2 Blue/3 Alpha, inspected ordinal guard. |

## lighting

| Tool | Core | Description |
|---|---|---|
| `add_post_process_blendable` |  | Append unique loaded persistent blendable-interface object, inspected count<64/weight0..1. |
| `create_decal_actor` |  | Create exact native decal actor/default root in exact ordinary unlocked persistent world. |
| `create_height_fog` |  | Create native height-fog actor in ordinary persistent map with native defaults. |
| `create_light_actor` | Core | Create native Point/Spot/Rect/Directional/Sky light in ordinary persistent map. |
| `create_local_fog` |  | Create native local-fog actor in ordinary persistent map with native defaults. |
| `create_planar_reflection` |  | Create native planar reflection actor in ordinary persistent map with native defaults. |
| `create_reflection_capture` |  | Create native Sphere/Box capture in ordinary persistent map with native defaults. |
| `create_sky_atmosphere` |  | Create native ASkyAtmosphere in ordinary persistent map with native defaults. |
| `create_volumetric_cloud` |  | Create native volumetric-cloud actor in ordinary persistent map with native defaults. |
| `delete_decal_actor` |  | Delete exact native persistent decal actor/root with world/GUID/label/material guards. |
| `delete_height_fog` |  | Delete native height-fog actor with inspected actor/component identity guards. |
| `delete_light_actor` |  | Delete native ordinary/sky light actor with inspected actor class/component guards. |
| `delete_local_fog` |  | Delete native local-fog actor with inspected actor/component identity guards. |
| `delete_planar_reflection` |  | Delete native planar actor with exact inspected actor/component identities. |
| `delete_reflection_capture` |  | Delete persistent-level capture actor with inspected component/build GUID guards. |
| `delete_sky_atmosphere` |  | Delete native sky-atmosphere actor with exact inspected actor/component identity guards. |
| `delete_volumetric_cloud` |  | Delete native volumetric-cloud actor with inspected actor/component identity guards. |
| `discover_planar_reflection_show_flags` |  | Discover native engine/custom show flags in name-sorted pages1..128 with substring filter. |
| `inspect_decal_mobility` |  | Inspect root-plus-descendant native attachment mobility hierarchy<=256 in breadth-first order. |
| `inspect_decal_receivers_page` |  | Page loaded persistent current-world primitive receives-decals flags1..128/path sorted. |
| `inspect_decals_page` |  | Page native loaded persistent current-world decals1..128, path sorted/optional owner filter. |
| `inspect_directional_light_clouds` |  | Inspect native directional atmosphere/cloud shadow flags/strength/bias/extent/resolution/sample controls. |
| `inspect_directional_light_shadows` |  | Inspect native directional cascade/far/distance-field/ray shadow/forward priority settings and adapter bounds. |
| `inspect_height_fog_page` |  | Page loaded persistent current-world UExponentialHeightFogComponent components in path order1..128. |
| `inspect_light_advanced_policy` |  | Inspect contribution/ray-end bias/MegaLights/cinematic-cached shadow policy and edit metadata. |
| `inspect_light_lightmass_settings` |  | Inspect stored local/directional light Lightmass fields and full native snapshot. |
| `inspect_light_ray_policy` |  | Inspect ray shadow policy/sample count/deep shadow/transmission/translucent/reflection/GI flags. |
| `inspect_light_shaft_settings` |  | Inspect light-shaft bloom/directional occlusion fields, stored tint bytes and direction override. |
| `inspect_light_view_channels` |  | Inspect five native view-lighting bits/mask and separate three object-lighting channels. |
| `inspect_light_world_influence` |  | Inspect light/skylight editor bAffectsWorld gate plus visibility/registration/render-state metadata. |
| `inspect_lights_page` |  | Page loaded persistent current-world lights in component-path order1..128. |
| `inspect_local_fog_page` |  | Page loaded persistent current-world ULocalFogVolumeComponent components in path order1..128. |
| `inspect_local_light_exposure` |  | Inspect authored inverse exposure blend/intensity/units/IES/mobility, no exposure or renderer evaluation. |
| `inspect_planar_reflection_actor_lists` |  | Inspect inherited hidden/show-only actor references in independent pages1..128. |
| `inspect_planar_reflection_component_lists` |  | Inspect hidden/show-only weak primitive-component refs in independent pages1..128. |
| `inspect_planar_reflection_show_flags` |  | Page stored flag overrides1..128 and query up to128 named current component bits. |
| `inspect_planar_reflections_page` |  | Inspect component-path sorted loaded persistent current-world planar captures in pages1..128. |
| `inspect_post_process_setting_fields` |  | Page native settings schema/override flags1..128 fields; scalar/bool/object/color/vector values. |
| `inspect_post_process_volume` |  | Read authored enabled/unbound/priority/radius/weight and up to64 blendable references. |
| `inspect_reflection_captures_page` |  | Inspect component-path sorted loaded persistent current-world captures in pages1..128. |
| `inspect_sky_atmospheres_page` |  | Page loaded persistent current-world USkyAtmosphereComponent components in path order1..128. |
| `inspect_sky_light_capture_policy` |  | Inspect emissive-only/realtime capture and inherited ray/deep-shadow/contribution policy plus resolution. |
| `inspect_sky_light_occlusion` |  | Inspect native skylight DFAO/cloud-AO fields/bounds/tint bytes, no rendering support or output evaluation. |
| `inspect_sky_lights_page` |  | Page loaded persistent current-world skylights in component-path order1..128 with optional exact owner. |
| `inspect_volumetric_clouds_page` |  | Page loaded persistent current-world UVolumetricCloudComponent components in path order1..128. |
| `inspect_world_height_fog` |  | Read up to128 native height-fog components and authored first-layer/volumetric controls. |
| `inspect_world_light_components` |  | Read up to128 current-world light components, identities/mobility/visibility/shadows/color/intensity. |
| `inspect_world_local_fog` |  | Inspect up to128 loaded current-world local fog components and authored controls. |
| `inspect_world_planar_reflections` |  | Read up to128 native planar reflection components and authored quality/fade controls. |
| `inspect_world_reflection_captures` |  | Read up to128 current-world reflection captures and authored source/brightness/offset. |
| `inspect_world_sky_atmospheres` |  | Inspect up to128 current-world sky-atmosphere components, native scalar/color/flag names. |
| `inspect_world_sky_lights` |  | Read up to128 native sky lights and authored source/capture/hemisphere settings. |
| `inspect_world_volumetric_clouds` |  | Inspect up to128 current-world volumetric clouds, native scalar/flag names/material soft path. |
| `queue_reflection_capture_recapture` |  | Queue native recapture for registered visible capture with inspected build GUID guard. |
| `queue_sky_light_capture` |  | Invoke native dirty-capture request with inspected source/cube/real-time guards. |
| `remove_post_process_blendable` |  | Remove one inspected blendable with count/index/object/weight guards, max64 entries. |
| `reset_post_process_setting` |  | Variants: `scalar`, `integer`, `bool`, `vector`, `enum` |
| `reset_post_process_setting_object` |  | Restore native hard object-reference default with inspected object/override guards. |
| `set_decal_appearance` |  | Variants: `set_decal_local_size`, `set_decal_linear_color` |
| `set_decal_mobility` |  | Set native decal mobility0 Static/1 Stationary/2 Movable with current/GUID/label/direct-child-count guards. |
| `set_decal_placement` |  | Variants: `set_decal_visible`, `set_decal_world_transform` |
| `set_decal_setting` |  | Set SortOrder int32, FadeScreenSize0..1, FadeStartDelay/FadeDuration/FadeInStartDelay/FadeInDuration0..100000s, |
| `set_directional_light_atmosphere_index` |  | Set native atmosphere sun slot0/1 with inspected current index guard. |
| `set_directional_light_cloud_setting` |  | Set inspected atmosphere/cloud shadow flag/scalar within reported adapter bounds. |
| `set_directional_light_luminance_color` |  | Set AtmosphereSunDiskColorScale or CloudScatteredLuminanceScale linear RGBA0..1000. |
| `set_directional_light_shadow_setting` |  | Set inspected native directional shadow/forward-priority field within reported adapter bounds. |
| `set_height_fog` |  | Variants: `scalar`, `color` |
| `set_height_fog_albedo` |  | Set stored volumetric albedo RGBA bytes0..255 with full inspected color guard. |
| `set_height_fog_cubemap` |  | Assign loaded persistent fog-inscattering cubemap or empty to clear, current asset guard. |
| `set_height_fog_render_flag` |  | Set bOverrideLightColorsWithFogInscatteringColors/bHoldout/bRenderInMainPass. |
| `set_height_fog_second_layer` |  | Set second-layer [density,falloff,height offset] with full current triple guard. |
| `set_height_fog_transform` |  | Set unattached height-fog component world transform; inspected transform guard. |
| `set_height_fog_visible` |  | Set fog component visibility with inspected flag guard; no child propagation. |
| `set_height_fog_volumetric_enabled` |  | Set native volumetric-fog enable with inspected current flag guard; scalar settings retained. |
| `set_light` | Core | Variants: `scalar`, `bool` |
| `set_light_advanced_policy` |  | Set SpecularScale/DiffuseScale0..1, RayEndBias0..1e6, MegaLightsShadowMethod0 Default/1 RayTracing/2 VSM, |
| `set_light_channels` |  | Set channel0/1/2 flags (three0/1 values) with full inspected current-channel guard. |
| `set_light_function_scale` |  | Set native projection XYZ scale with full inspected vector guard; material retained. |
| `set_light_lightmass_setting` |  | Edit IndirectLightingSaturation0..4, ShadowExponent0.1..4, bUseAreaShadowsForStationaryLight0..1, |
| `set_light_mobility` |  | Set Static/Stationary/Movable with inspected native ordinal0/1/2 guard. |
| `set_light_ray_policy` |  | Set CastRaytracedShadow0 Disabled/1 UseProjectSetting/2 Enabled, SamplesPerPixel1..1024, |
| `set_light_shaft_appearance` |  | Variants: `set_light_shaft_bloom_tint`, `set_directional_light_shaft_override_direction` |
| `set_light_shaft_setting` |  | Set native bEnableLightShaftBloom0..1/BloomScale0..10/BloomThreshold0..4/BloomMaxBrightness0..100, |
| `set_light_stored_color` |  | Set native stored RGBA bytes0..255 with exact stored_color_rgba inspection guard. |
| `set_light_transform` |  | Set unattached ordinary/sky light component world transform; inspected transform guard. |
| `set_light_view_channels` |  | Set all five view-lighting bits0..1 with full exact prior-bit/GUID/label guard, zero mask allowed. |
| `set_light_visible` |  | Set native ordinary/sky light visibility with current flag guard, no child propagation. |
| `set_light_world_influence` |  | Edit light/skylight bAffectsWorld with exact flag/GUID/label guard; can unbuild baked lighting. |
| `set_local_fog` |  | Variants: `scalar`, `color` |
| `set_local_fog_priority` |  | Set local-fog native sort priority-127..127 with exact inspected integer guard. |
| `set_local_fog_transform` |  | Set unattached local-fog component world transform; inspected transform guard. |
| `set_local_fog_visible` |  | Set fog component visibility with inspected flag guard; no child propagation. |
| `set_local_light_exposure_blend` |  | Set native local-light InverseExposureBlend0..1 with exact current value/GUID/label guard. |
| `set_local_light_units_intensity` |  | Set Unitless/Candelas/Lumens/EV/Nits plus explicit intensity with current pair guards. |
| `set_planar_reflection` |  | Variants: `scalar`, `bool` |
| `set_planar_reflection_actor_list` |  | Replace inherited HiddenActors or ShowOnlyActors<=64 with full ordered prior-path guard. |
| `set_planar_reflection_capture_numeric` |  | Set LODDistanceFactor0.1..10, MaxViewDistanceOverride-1..1e9cm, CaptureSortPriority signed int32. |
| `set_planar_reflection_capture_policy` |  | Set inherited PrimitiveRenderMode0 Legacy/1 RenderScenePrimitives/2 UseShowOnlyList, |
| `set_planar_reflection_component_list` |  | Replace HiddenComponents/ShowOnlyComponents<=64 with full prior-path guard. |
| `set_planar_reflection_screen_percentage` |  | Set integer planar screen percentage25..100 with inspected current value guard. |
| `set_planar_reflection_show_flags` |  | Replace full ordered native show-flag overrides<=128 with exact previous name/bool guard. |
| `set_planar_reflection_transform` |  | Set unattached planar component world transform; inspected transform guard. |
| `set_planar_reflection_visible` |  | Set planar component visibility with inspected current flag guard; children unchanged. |
| `set_post_process_blendable_weight` |  | Set existing blendable weight0..1 with inspected count/index/object/weight guards. |
| `set_post_process_setting` |  | Variants: `scalar`, `bool`, `enum`, `vector`, `integer` |
| `set_post_process_setting_object` |  | Assign loaded compatible persistent hard object reference, or empty to clear if allowed. |
| `set_post_process_setting_override` |  | Set native setting's override flag; use field name without bOverride_ prefix. |
| `set_post_process_volume_control` |  | Set Priority(+/-1e6), BlendRadius(0..1e6), BlendWeight(0..1), Enabled/Unbound(bool). |
| `set_primitive_receives_decals` |  | Set primitive bReceivesDecals with exact current flag/GUID/label guard and native setter/readback. |
| `set_reflection_capture_offset` |  | Set native world-space capture offset with inspected vector guard, XYZ+/-1e9. |
| `set_reflection_capture_scalar` |  | Set Brightness/SourceCubemapAngle or shape InfluenceRadius/BoxTransitionDistance/InfluenceRadiusScale. |
| `set_reflection_capture_source` |  | Set CapturedScene/SpecifiedCubemap and cubemap with inspected current pair guards. |
| `set_reflection_capture_transform` |  | Set unattached capture component world transform; inspected transform guard. |
| `set_reflection_capture_visible` |  | Set native capture visibility with inspected current flag guard; no child propagation. |
| `set_sky_atmosphere` |  | Variants: `scalar`, `bool`, `color` |
| `set_sky_atmosphere_absorption_tent` |  | Set native absorption tent triple [tip altitude km, tip value, width km]. |
| `set_sky_atmosphere_ground_albedo` |  | Set native stored GroundAlbedo RGBA bytes0..255 with full inspected current-color guard. |
| `set_sky_atmosphere_transform` |  | Set unattached sky-atmosphere world transform with inspected transform/mode guard. |
| `set_sky_atmosphere_transform_mode` |  | Set native planet placement mode0 top at absolute world origin, |
| `set_sky_atmosphere_visible` |  | Set sky-atmosphere component visibility with exact inspected flag/identity guards. |
| `set_sky_light` |  | Variants: `scalar`, `bool`, `color` |
| `set_sky_light_capture_policy` |  | Set inspected skylight bCaptureEmissiveOnly/bRealTimeCapture and inherited contribution/ray policy. |
| `set_sky_light_hemisphere_color` |  | Set lower-hemisphere linear RGBA0..1000 with full inspected current-color guard. |
| `set_sky_light_occlusion` |  | Set inspected native skylight DFAO/cloud-AO scalar/flag/combine mode within reported bounds. |
| `set_sky_light_occlusion_tint` |  | Set native OcclusionTint RGBA bytes0..255 with full current-byte/GUID/label guard. |
| `set_sky_light_source` |  | Set CapturedScene/SpecifiedCubemap pair with inspected source/cubemap guards. |
| `set_volumetric_cloud` |  | Variants: `scalar`, `bool` |
| `set_volumetric_cloud_ground_albedo` |  | Set stored cloud ground-albedo RGBA bytes0..255 with exact full inspected-color guard. |
| `set_volumetric_cloud_tracing_mode` |  | Set tracing max-distance mode0 cloud-layer entry point /1 point of view. |
| `set_volumetric_cloud_transform` |  | Set unattached cloud authored world transform with inspected full transform guard. |
| `set_volumetric_cloud_visible` |  | Set cloud component visibility with exact inspected flag/identities, no child propagation. |

## materials

| Tool | Core | Description |
|---|---|---|
| `add_material_collection_parameter` |  | Append Scalar/Vector native collection parameter/new unique name/native GUID/per-kind1024 budget. |
| `audit_static_mesh_component_nanite_materials` |  | Run native Nanite material audit including current component overrides. |
| `connect_material_expressions` | Core | Connect two Material expression nodes by their UObject names. |
| `create_material_expression` | Core | Create a Material expression node, using a class path such as /Script/Engine.MaterialExpressionScalarParameter. |
| `create_material_parameter_collection` |  | Create native Material Parameter Collection via AssetTools/native factory defaults. |
| `delete_material_collection_parameter` |  | Delete native Scalar/Vector collection parameter, dry-run reports sorted loaded direct references. |
| `delete_material_expression` |  | Delete a Material expression node by UObject name. |
| `discover_material_expression_metadata` |  | Discover native material/function-owned expression metadata/path/GUID/class/snapshots/pages1..128. |
| `discover_material_parameter_collections` |  | Discover loaded native collection assets/pages1..128/counts/dirty/direct loaded expression counts. |
| `edit_material_core_settings` |  | Edit Material domain, blend mode, shading model, two-sided state, and usage flags. |
| `edit_material_instance_parameter` | Core | Set an existing scalar, vector, texture, static switch, runtime VT, or font override. |
| `edit_material_instance_settings` |  | Edit reflected Material Instance Constant settings. |
| `edit_material_parameter_group_entry` |  | Add/Remove native material authored group-order metadata; no expression group reassignment. |
| `edit_material_settings` | Core | Edit reflected parent Material settings. |
| `inspect_decal_material_users` |  | Page loaded current-world decals directly referencing exact material object path, empty selects unassigned. |
| `inspect_loaded_decal_materials` |  | Discover loaded persistent material interfaces with native DeferredDecal base domain, pages1..128. |
| `inspect_material_asset` | Core | Inspect a parent Material or Material Instance. |
| `inspect_material_collection_references` |  | Inspect loaded direct collection-expression references/pages1..128/optional parameter GUID. |
| `inspect_material_collection_world_values` |  | Inspect native effective collection values in exact current Editor/active PIE world/page1..128. |
| `inspect_material_enumeration_entries` |  | Observe native loaded UEnum/material enumeration provider entries/pages1..128/first4096 retained. |
| `inspect_material_expression_metadata` |  | Inspect material/function expression Group/SortPriority/Desc/ControlType/EnumerationIndex/editability/full snapshot. |
| `inspect_material_font_atlas` |  | Inspect loaded font cache mode/atlas refs/source headers/pages1..128/destination font snapshot. |
| `inspect_material_parameter_groups` |  | Inspect loaded native material editor-only authored group priorities/page1..128/full group snapshot. |
| `inspect_texture_material_overrides` |  | Page loaded persistent material-instance direct authored texture overrides1..128, unverified. |
| `layout_material_expressions` | Core | Automatically arrange parent Material expression nodes. |
| `list_material_expressions` | Core | List parent Material expression nodes and their editor positions. |
| `list_material_instance_parameters` | Core | List effective Material Instance parameters, groups, values, and override flags. |
| `list_material_parameters` | Core | List parent Material parameters with types, groups, descriptions, and defaults. |
| `material_collection_defaults` |  | Inspect native collection defaults/page1..128 or edit Scalar/Vector default at kind-local start index. |
| `material_collection_parameter_reference` |  | Inspect/Set native collection parameter expression collection/name/native parameter GUID. |
| `material_expression_parameter_default` |  | Inspect/Set exact native scalar or vector parameter default in material/function. |
| `material_font_sample_default` |  | Inspect/Set native font-sample/parameter font+atlas page0..255 in material/function. |
| `material_instance_enumeration_slots` |  | Inspect paged native instance enumeration slots/effective parent fallback, or Set start slot0..255. |
| `material_parameter_primitive_data_binding` |  | Inspect/Set native scalar/vector custom primitive-data enable/index (1/4 consecutive floats). |
| `material_scalar_enumeration_reference` |  | Inspect/Set scalar parameter soft Enumeration reference for material/function owners. |
| `material_scalar_slider_range` |  | Inspect/Set native material/function scalar parameter paired slider min/max UI metadata. |
| `material_static_parameter_default` |  | Inspect/Set native static bool/switch or component-mask parameter defaults in material/function. |
| `material_texture_channel_labels` |  | Inspect/Set native engine texture-sample four RGBA channel labels in material/function. |
| `material_texture_sample_policy` |  | Inspect native engine texture-sample policy or edit SamplerType/SamplerSource/MipValueMode/GatherMode enum |
| `material_vector_channel_labels` |  | Inspect/Set native vector parameter four RGBA channel labels for material/function owners. |
| `rename_material_collection_parameter` |  | Rename native Scalar/Vector collection parameter preserving GUID/default/order. |
| `reorder_material_collection_parameters` |  | Full Scalar/Vector kind-local permutation; preserves native GUID/name/default and other kind. |
| `reset_material_collection_world_values` |  | Native reset clears all world instance scalar/vector override maps, exact current Editor/PIE identity. |
| `reset_material_instance_parameters` |  | Clear every local parameter override on a Material Instance Constant. |
| `resolve_material_enumeration_value` |  | Resolve loaded enum/provider name with int32 fallback and separate found/result decimal strings. |
| `set_decal_material` |  | Assign loaded persistent DeferredDecal-domain material interface or empty clear. |
| `set_material_collection_world_value` |  | Set native Scalar/Vector world collection override/current Editor or active PIE world. |
| `set_material_expression_metadata` |  | Edit material/function Group/Desc text, SortPriority+-1000000, or scalar ControlType enum. |
| `set_material_instance_parent` | Core | Assign a Material or Material Instance as parent; rejects inheritance cycles. |
| `set_material_parameter` | Core | Set a scalar, vector, or texture parameter on a Material Instance Constant. |
| `set_material_parameter_group_priority` |  | Edit existing unique native material authored group priority+-1000000 with full group snapshot. |
| `set_material_texture_sample_reference` |  | Assign loaded persistent texture or empty clear to native engine texture-sample/object default. |
| `set_runtime_virtual_texture_material_data` |  | Set RVT CustomMaterialData native float4+-65504, full prior values/snapshot required, unverified. |
| `set_skeletal_mesh_material` |  | Assign a material to a skeletal mesh material slot. |
| `set_static_mesh_material` | Core | Assign a material to a static mesh material slot. |
| `set_volumetric_cloud_material` |  | Assign loaded persistent Volume-domain cloud material or empty clear. |
| `summarize_material` |  | Read a parent Material's domain, blend mode, shading models, two-sided state, and usage flags. |
| `validate_material` | Core | Report Material shader compilation status and available compile errors. |
| `validate_material_collection_structure` |  | Read-only native collection name/GUID uniqueness-validity/lookup roundtrip/default-finite/count checks. |
| `validate_material_instance` |  | Report missing parent and local overrides absent from the parent parameter set. |

## meshes

| Tool | Core | Description |
|---|---|---|
| `customize_mesh_socket` |  | Copy shared Skeleton socket into a mesh-only override, preserving native settings. |
| `delete_mesh_socket` |  | Delete exactly one mesh-owned socket and its mesh preview attachments. |
| `edit_mesh_socket` |  | Create/update a mesh-owned socket on a /Game SkeletalMesh with native transaction. |
| `import_fbx` | Core | Import an FBX file to an unused /Game path. Existing assets are never overwritten. Requires stopped PIE. |
| `import_static_mesh` | Core | Import OBJ or glTF/GLB. OBJ replacement requires confirmation; glTF uses a new scene folder and returns actual asset paths. |
| `inspect_mesh_sockets` |  | Inspect mesh-only and shared Skeleton socket definitions and override selection. |
| `inspect_runtime_skeletal_socket` |  | Read current evaluated socket transform on a registered selected-PIE mesh component. |
| `inspect_static_mesh_nanite` |  | Read loaded Static Mesh Nanite settings/resource counters/fallback LOD counts. |
| `inspect_static_mesh_source` |  | Inspect Static Mesh LOD geometry and source file status. |
| `inspect_world_legacy_lod_actors` |  | Inspect sorted loaded legacy LOD actor tiers/local setup indices/direct subactor refs. |
| `inspect_world_static_mesh_nanite_components` |  | Discover up to128 loaded current editor-world Static Mesh components/subclasses. |
| `promote_mesh_socket` |  | Copy mesh-only socket to its /Game Skeleton, optionally removing local override. |
| `reimport_static_mesh` |  | Reimport a Static Mesh from its recorded source or a confirmed new source. |
| `rename_mesh_socket` |  | Rename mesh-owned socket and mesh preview attachment names. |
| `reset_static_mesh_nanite_setting` |  | Reset one supported typed Nanite field to native FMeshNaniteSettings default. |
| `set_skeletal_mesh_section` |  | Edit skeletal mesh section flags: recompute_tangent, cast_shadow, or visible_in_ray_tracing. |
| `set_static_mesh_component_force_disable_nanite` |  | Set native force-disable Nanite override on exact placed Static Mesh component. |
| `set_static_mesh_lod_group` |  | Set a static mesh LOD group, such as SmallProp or LargeProp. |
| `set_static_mesh_lod_screen_sizes` |  | Set static mesh LOD screen-size thresholds. |
| `set_static_mesh_nanite_setting` |  | Enums GenerateFallback(PlatformDefault/Enabled), FallbackTarget(Auto/PercentTriangles/RelativeError). |
| `set_static_mesh_setting` |  | Edit static mesh settings: generate_lightmap_uvs or allow_cpu_access. |
| `set_world_composition_tile_lod_distance` |  | Edit existing loaded tile LOD relative distance0..1e9 with cache/package/index/count guards. |
| `set_world_composition_tile_lod_list` |  | Replace tile LOD distance metadata<=4, empty clears, with full ordered stale guard. |

## navigation

| Tool | Core | Description |
|---|---|---|
| `build_navigation` | Core | Run UE's blocking current-world navigation build and report native task/data state. |
| `control_navigation_agent` |  | Control an owned transient native character/controller probe in selected PIE. |
| `edit_smart_navigation_link` |  | Variants: `set_smart_navigation_link`, `set_runtime_smart_link_enabled` |
| `inspect_navigation` |  | Inspect active editor-world native navigation data, bounded bounds rows and native build/task state. |
| `inspect_navigation_agent` |  | Poll native probe position/velocity, path status/request and paged completion/link events. |
| `inspect_navigation_area` |  | Inspect a direct-native-parent NavArea Blueprint's costs, color, agents and validation. |
| `inspect_navigation_filter` |  | Inspect a compiled /Game Blueprint with direct native NavigationQueryFilter parent. |
| `inspect_navigation_links` |  | Inspect native proxies in editor or selected PIE world; ambiguous PIE worlds require an explicit index. |
| `navigation_query` |  | Variants: `sample_navigation_points`, `inspect_navigation_filter_costs`, `query_navigation` |
| `set_navigation_area` |  | Create/update a Blueprint whose direct native parent is NavArea. |
| `set_navigation_bounds` |  | Create/update/delete an axis-aligned native box NavMeshBoundsVolume in the persistent level. |
| `set_navigation_filter` |  | Create/update a native NavigationQueryFilter Blueprint and compile its defaults. |
| `set_navigation_links` |  | Create/update/delete a native simple-link proxy in an ordinary persistent editor level. |
| `set_navigation_modifier` |  | Create/update/delete an axis-aligned box NavModifierVolume in an ordinary persistent level. |

## niagara

| Tool | Core | Description |
|---|---|---|
| `add_niagara_effect_type_rule` |  | Append owned validation rule using native class-default settings (max 128). |
| `add_niagara_emitter` |  | Insert a copied native emitter asset/version through Niagara editor utility. |
| `add_niagara_emitter_module` |  | Variants: `append_niagara_emitter_module`, `insert_niagara_emitter_module` |
| `add_niagara_renderer` |  | Append concrete native renderer to owned stateful emitter with target-support check. |
| `add_niagara_script_comment_box` |  | Create native graph comment box with <=4096 characters at bounded coordinates. |
| `add_niagara_script_compound_input` |  | Create vector (XYZ) or color (RGBA) parameter input with finite components. |
| `add_niagara_script_constant_input` |  | Create an unexposed optional parameter input with stored scalar/vector/color value. |
| `add_niagara_script_function_call` |  | Add an unconnected module/function/dynamic-input script call with explicit version. |
| `add_niagara_script_operation` |  | Create an unconnected operation from a unique native graph context action. |
| `add_niagara_script_output` |  | Append float/int/bool/vector/color output to function/dynamic-input output node. |
| `add_niagara_script_parameter_map` |  | Create empty native parameter-map get/set node with initialized base pins. |
| `add_niagara_script_reroute` |  | Create an unconnected native Niagara reroute with initialized GUID/pins. |
| `add_niagara_script_scalar_input` |  | Create scalar parameter input node (float/int/bool), unique native-safe name. |
| `add_niagara_user` |  | Variants: `scalar`, `vector`, `color` |
| `bind_niagara_simulation_stage_user_integer` |  | Bind a stage integer setting to an existing exact int32 User parameter. |
| `connect_niagara_script_pins` |  | Connect opposite pins via native schema, optionally replacing existing links. |
| `copy_niagara_effect_type_scalability_row` |  | Replace existing same-kind scalability row from another inspected effect type. |
| `create_niagara_effect_type` |  | Create effect-type scalability profile using native factory class defaults. |
| `create_niagara_emitter_asset` |  | Create a standalone emitter through native factory defaults (modules/renderers). |
| `create_niagara_script_asset` |  | Create module, function or dynamic_input using its native Niagara factory. |
| `create_niagara_system` | Core | Create native empty Niagara system via editor factory without interactive picker. |
| `create_niagara_validation_rule_set` |  | Create native rule set, or duplicate source when source_asset_path supplied. |
| `disconnect_niagara_script_pins` |  | Remove one symmetric pin link via native schema; missing link is a no-op. |
| `discover_niagara_scalability_profiles` |  | List <=256 manager-loaded device profiles and <=32 configured quality names. |
| `duplicate_niagara_effect_type` |  | Duplicate registered effect type through native AssetTools into new /Game path. |
| `duplicate_niagara_emitter` |  | Append native stateful/stateless emitter copy with new handle GUID. |
| `duplicate_niagara_emitter_asset` |  | Duplicate a standalone registered emitter asset via native AssetTools. |
| `duplicate_niagara_renderer` |  | Append native renderer duplicate through versioned AddRenderer API. |
| `duplicate_niagara_script_asset` |  | Duplicate a registered Niagara script/module asset via native AssetTools. |
| `duplicate_niagara_script_node` |  | Duplicate native operation/reroute/comment via graph text export/import. |
| `duplicate_niagara_system` |  | Duplicate persistent native Niagara system via AssetTools to new /Game destination. |
| `edit_niagara_effect_type_rule` |  | Remove/move/duplicate owned effect-type validation rule; duplicate appends. |
| `edit_niagara_effect_type_scalability_conditions` |  | Add/remove/duplicate/move scalability CVar conditions, <=128 entries. |
| `edit_niagara_effect_type_scalability_rows` |  | Add/remove/duplicate/move authored system/emitter scalability row (max128). |
| `edit_niagara_rule_set_rule` |  | Author reusable rule-set rules: add/inspect/remove/move/duplicate, |
| `edit_niagara_script_output` |  | Remove, move (final index) or rename function/dynamic-input output. |
| `edit_niagara_system_module_pin_default` |  | Set/reset unlinked writable system module scalar/vector/color pin default. |
| `edit_niagara_system_rapid_parameter` |  | Set/remove existing exact Constants. rapid parameter on system_spawn/system_update. |
| `evaluate_niagara_effect_type_scalability` |  | Native profile/quality selection evaluation for <=128 authored rows. |
| `insert_niagara_system_module` |  | Insert module into system_spawn/system_update; -1 appends. |
| `inspect_active_niagara_effect_type_scalability` |  | Inspect native current-editor effective effect-type scalability configuration. |
| `inspect_niagara_effect_type` |  | Inspect authored effect-type scalability settings and validation rule identities. |
| `inspect_niagara_effect_type_rule` |  | Inspect current owned rule's authored fields, enum choices and clamp metadata. |
| `inspect_niagara_effect_type_scalability` |  | Inspect authored system/emitter scalability rows and record fingerprints. |
| `inspect_niagara_effect_type_scalability_conflicts` |  | Evaluate native selection overlap on <=32 scalability rows using loaded profiles. |
| `inspect_niagara_emitter_asset` |  | Inspect persistent emitter asset versions (<=128) and exposed version GUID. |
| `inspect_niagara_emitter_module` |  | Inspect a current module's native input pins/defaults/types and connections. |
| `inspect_niagara_emitter_rapid_iteration` |  | Inspect up to 256 native stack rapid-iteration names/types/stored values. |
| `inspect_niagara_emitter_stack` |  | Inspect particle/emitter spawn/update module parameter-map chain order. |
| `inspect_niagara_emitter_stack_dependencies` |  | Check authored same-stack dependency provider/order/version constraints. |
| `inspect_niagara_renderer` |  | Inspect up to 128 editable fields of owned stateful emitter renderer. |
| `inspect_niagara_script_asset` |  | Inspect registered Niagara script/module asset identity, usage and versions. |
| `inspect_niagara_script_graph` |  | Inspect an existing script version graph: node identities/classes/positions, |
| `inspect_niagara_system` |  | Inspect persistent native Niagara system with up to 128 emitter handles. |
| `inspect_niagara_system_module` |  | Inspect current system_spawn/system_update module input pins/defaults/links. |
| `inspect_niagara_system_rapid_iteration` |  | Inspect native system_spawn/system_update rapid-iteration store. |
| `inspect_niagara_system_stack` |  | Inspect system_spawn/system_update modules in parameter-map chain order. |
| `inspect_niagara_system_stack_dependencies` |  | Check system_spawn/system_update same-stack dependency providers/order/versions. |
| `inspect_niagara_validation_rule_set` |  | Inspect reusable rule-set ordered rule identities/classes/ownership/enabled state. |
| `list_niagara_renderer_types` |  | Discover up to 128 loaded concrete native renderer classes and editable fields. |
| `list_niagara_script_operations` |  | Discover up to 256 unique native operation names/classes/titles/tooltips |
| `list_niagara_significance_handlers` |  | List up to 128 loaded concrete native significance-handler classes. |
| `list_niagara_validation_rule_types` |  | List up to 128 loaded concrete native Niagara validation rule classes. |
| `move_niagara_renderer` |  | Move owned stateful renderer to final_index via native versioned API. |
| `move_niagara_script_node` |  | Set graph node layout coordinates within +/-1e6 using GUID/path guards. |
| `move_niagara_simulation_stage` |  | Move an owned versioned stage to a final zero-based index in its current list. |
| `remove_niagara_emitter` |  | Remove native emitter handle with system parameter cleanup/cache invalidation. |
| `remove_niagara_emitter_rapid_parameter` |  | Remove existing exact Constants. float/int/bool/vector/color rapid parameter. |
| `remove_niagara_event_handler` |  | Remove a handler by unique native script usage ID after exact identity guards. |
| `remove_niagara_renderer` |  | Remove owned stateful emitter renderer via native versioned API. |
| `remove_niagara_script_node` |  | Remove a native user-deletable graph node via DestroyNode, including its links. |
| `remove_niagara_simulation_stage` |  | Remove an owned versioned stage with exact emitter/version/index/path guards. |
| `remove_niagara_user_parameter` |  | Remove exact User. float/int/bool/vector/color parameter/default from exposed store. |
| `rename_niagara_emitter` |  | Rename native emitter handle with native-safe unique non-None name (<=128). |
| `rename_niagara_script_input` |  | Rename parameter input via native OnRenameNode with collision checks. |
| `rename_niagara_simulation_stage` |  | Rename an owned versioned stage with a unique native-safe name (1..128 chars). |
| `request_niagara_system_compile` |  | Request native asynchronous Niagara compilation, optionally forced. |
| `reset_niagara_effect_type_rule_field` |  | Reset supported scalar/enum/name/vector/color leaf to exact native class default. |
| `reset_niagara_effect_type_scalability_field` |  | Reset scalar/enum/name/text/vector/color leaf to native scalability row default. |
| `reset_niagara_effect_type_scalability_row` |  | Reset complete scalability row to native defaults, preserving row order. |
| `reset_niagara_emitter_module_pin_default` |  | Reset unlinked writable scalar/vector/color module pin to autogenerated default. |
| `reset_niagara_renderer_field` |  | Reset editable renderer scalar/enum/name/vector/color leaf to native class default. |
| `reset_niagara_script_pin_default` |  | Reset an unlinked writable scalar/vector3/color input to its autogenerated default. |
| `reset_niagara_simulation_stage_binding` |  | Reset an integer stage binding to its configured native parameter default. |
| `resize_niagara_script_comment_box` |  | Resize a native comment box to integer dimensions 32..100000. |
| `set_niagara_effect_type_policy` |  | Edit bAllowCullingForLocalPlayers, UpdateFrequency or CullReaction. |
| `set_niagara_effect_type_rule` |  | Variants: `scalar`, `enum` |
| `set_niagara_effect_type_rule_compound` |  | Set exact native FVector XYZ/FLinearColor RGBA rule leaf (kind=vector/color). |
| `set_niagara_effect_type_rule_reference` |  | Set owned rule FName or hard asset reference leaf (kind=name/asset). |
| `set_niagara_effect_type_rule_sets` |  | Replace ordered <=128 unique registered validation rule-set references. |
| `set_niagara_effect_type_scalability` |  | Variants: `scalar`, `enum` |
| `set_niagara_effect_type_scalability_condition` |  | Replace all settings of an existing scalability CVar condition. |
| `set_niagara_effect_type_scalability_profile` |  | Set existing device profile override: state=default/enabled/disabled. |
| `set_niagara_effect_type_scalability_quality` |  | Toggle native effects quality bit (0..31) on inspected system/emitter row. |
| `set_niagara_effect_type_significance` |  | Assign owned native significance handler; empty clears, same class retained. |
| `set_niagara_emitter` |  | Variants: `scalar`, `enum` |
| `set_niagara_emitter_enabled` |  | Set native Niagara emitter enabled state guarded by current index/stable GUID. |
| `set_niagara_emitter_fixed_bounds` |  | Set an owned emitter version's authored fixed box with ordered finite corners. |
| `set_niagara_emitter_module_enabled` |  | Set native module group enabled state, including associated input nodes. |
| `set_niagara_emitter_module_pin_compound` |  | Set unlinked writable native module vector3 XYZ or color RGBA pin default. |
| `set_niagara_emitter_module_pin_default` |  | Set unlinked writable native module float/int32/bool input pin default. |
| `set_niagara_emitter_rapid_compound` |  | Set existing exact Constants. vector XYZ/color RGBA rapid-iteration value. |
| `set_niagara_emitter_rapid_scalar` |  | Set existing exact Constants. rapid-iteration float/int/bool value. |
| `set_niagara_event_handler_bool` |  | Set bRandomSpawnNumber or UpdateAttributeInitialValues on an event handler. |
| `set_niagara_event_handler_count` |  | Set uint32 SpawnNumber, MinSpawnNumber or MaxEventsPerFrame. |
| `set_niagara_event_handler_execution_mode` |  | Set visible native event mode EveryParticle or SpawnedParticles. |
| `set_niagara_event_handler_source` |  | Set event source name and emitter GUID; empty/zero GUID means self. |
| `set_niagara_module_usage_contexts` |  | Replace module usage mask from unique native execution-context enum names. |
| `set_niagara_renderer` |  | Variants: `scalar`, `enum`, `name`, `vector`, `color` |
| `set_niagara_renderer_asset` |  | Set owned renderer direct hard asset reference; empty clears unless native NoClear. |
| `set_niagara_renderer_enabled` |  | Set owned stateful emitter renderer enabled state with GUID/object guards. |
| `set_niagara_script` |  | Variants: `text`, `bool`, `enum` |
| `set_niagara_script_deprecation_replacement` |  | Set a version's replacement script recommendation; empty clears. |
| `set_niagara_script_input_exposure` |  | Set parameter input bExposed, bRequired or bHidden (advanced caller display). |
| `set_niagara_script_input_priority` |  | Set native int32 CallSortPriority on a parameter input node. |
| `set_niagara_script_input_value` |  | Set existing input's stored float/int32/bool/vector/color value; name/type preserved. |
| `set_niagara_script_node_comment` |  | Set node comment up to 4096 characters; empty clears. |
| `set_niagara_script_pin_compound` |  | Set exact vector3 XYZ or color RGBA unlinked writable input pin default. |
| `set_niagara_script_pin_scalar` |  | Set exact float/int32/bool unlinked writable input pin default via schema. |
| `set_niagara_script_provided_dependencies` |  | Replace up to 128 unique non-None provided dependency IDs; empty clears. |
| `set_niagara_script_required_dependencies` |  | Replace up to 128 required dependencies; empty clears. |
| `set_niagara_simulation_stage` |  | Variants: `enum`, `bool` |
| `set_niagara_simulation_stage_enabled` |  | Set an owned stage enabled flag using exact emitter/version/index/path guards. |
| `set_niagara_simulation_stage_integer_default` |  | Set positive int32 default for NumIterations, ElementCountX/Y/Z or |
| `set_niagara_simulation_stage_state_range` |  | Set ordered inclusive int32 particle-state bounds on a generic stage. |
| `set_niagara_system_determinism` |  | Set authored system determinism flag and int32 seed. |
| `set_niagara_system_effect_type` |  | Assign registered native effect type; empty clears. Shared policy unchanged. |
| `set_niagara_system_fixed_bounds` |  | Set authored fixed bounds corners ({x,y,z}) and enable flag. |
| `set_niagara_system_fixed_tick` |  | Set native fixed simulation timestep flag and finite delta 1/240..1 seconds. |
| `set_niagara_system_module_enabled` |  | Set native system module group enabled state with exact stack/node guards. |
| `set_niagara_system_warmup` |  | Set native warmup time/delta; time rounds down to a whole tick multiple. |
| `set_niagara_user` |  | Variants: `scalar`, `vector`, `color` |
| `set_niagara_validation_rule` |  | Variants: `text`, `string_array` |
| `set_niagara_validation_rule_reference_array` |  | Replace <=256 hard asset/class rule references; empty clears, order retained. |
| `simulate_niagara_system_preview` |  | Advance hidden temporary solo CPU Niagara preview, return age/completion and |
| `validate_niagara_script_graph` |  | Report node/pin identity, ownership, orphan/link issues and same-name input |
| `validate_niagara_system_rules` |  | Run native validation rules on a transient system duplicate, no automatic fixes. |

## pcg

| Tool | Core | Description |
|---|---|---|
| `add_pcg_actor_component` |  | Create/register native instance PCG component on existing editor-world actor. |
| `add_pcg_graph_pin` |  | Add native graph IO custom pin: input node=-2/output=-1, <=64 authored pins. |
| `add_pcg_graph_typed_parameter` |  | Variants: `add_pcg_graph_parameter`, `add_pcg_graph_enum_parameter`, `add_pcg_graph_asset_parameter`, `add_pcg_graph_class_parameter` |
| `add_pcg_node` |  | Create native settings-class PCG node/default pins at bounded editor position. |
| `create_pcg_graph` |  | Create empty PCG graph with native editor factory and no template dialog. |
| `create_pcg_graph_instance` |  | Create native PCG graph instance with registered graph/interface parent. |
| `discover_pcg_data_classes` |  | List <=256 loaded concrete native PCG data classes/type identifiers. |
| `discover_pcg_node_classes` |  | List <=256 loaded concrete native PCG settings classes; palette suitability unverified. |
| `duplicate_pcg_graph` |  | Duplicate persistent PCG graph through native AssetTools. |
| `duplicate_pcg_graph_instance` |  | Duplicate persistent PCG graph instance through native AssetTools. |
| `duplicate_pcg_node` |  | Copy owned node settings into new unlinked PCG node at requested position. |
| `edit_pcg_component_settings` |  | Variants: `set_pcg_component_settings`, `set_pcg_component_generation_trigger` |
| `edit_pcg_edge` |  | Connect/disconnect native labeled PCG edge without displacing other links. |
| `edit_pcg_graph_parameter_override` |  | Control instance parameter: enable_override/disable_override/reset_value. |
| `edit_pcg_graph_pin` |  | Variants: `edit_pcg_graph_pins`, `rename_pcg_graph_pin`, `configure_pcg_graph_pin`, `set_pcg_graph_pin_data_types` |
| `edit_pcg_node_display` |  | Variants: `edit_pcg_node_presentation`, `set_pcg_node_comment`, `set_pcg_node_comment_display` |
| `inspect_pcg_component_output` |  | Inspect idle current-world component cached graph output, <=256 entries. |
| `inspect_pcg_component_resources` |  | Inspect <=256 managed resources on idle current-world PCG component. |
| `inspect_pcg_component_status` |  | Poll one current-world PCG component by inspected component/actor identity. |
| `inspect_pcg_graph` |  | Inspect persistent native PCG graph nodes/settings/pins/edge endpoints. |
| `inspect_pcg_graph_dependencies` |  | Inspect authored subgraph/instance-parent dependencies and cycle/missing diagnostics. |
| `inspect_pcg_graph_interface` |  | Inspect native PCG graph/instance parent chain and <=256 parameter entries. |
| `inspect_pcg_graph_parameter_array` |  | Inspect <=256 array parameter elements as bounded native-export records. |
| `inspect_pcg_graph_pins` |  | Inspect <=64 authored graph IO pins (input node=-2/output=-1). |
| `inspect_pcg_node_settings` |  | Inspect authored internal-node settings, identity and native-export fingerprint. |
| `inspect_pcg_output_metadata` |  | Inspect cached output metadata names/type IDs: default and <=16 supported |
| `inspect_pcg_output_points` |  | Read <=256 cached native points: transform, density, seed, bounds, color, |
| `inspect_pcg_world_components` |  | List <=256 loaded PCG components in current stopped editor world. |
| `remove_pcg_actor_component` |  | Remove clean nonpartitioned actor-instance PCG component, not native/BP defaults. |
| `remove_pcg_graph_parameter` |  | Remove base graph parameter after native removal-policy check. |
| `remove_pcg_node` |  | Remove inspected internal PCG node with native link cleanup. |
| `rename_pcg_graph_parameter` |  | Rename base graph parameter using native API, preserving GUID/value. |
| `request_pcg_component_operation` |  | Request native local generate/cleanup/cancel; returns task ID/status, no wait. |
| `reset_pcg_graph_settings_field` |  | Reset direct scalar/enum/name/string/text/vector/color graph setting to native CDO. |
| `reset_pcg_node_settings_field` |  | Reset scalar/enum/name/string/text/vector/color leaf to native class default. |
| `set_pcg_component_graph` |  | Bind/clear idle current-world component graph using native local setter. |
| `set_pcg_component_partitioned` |  | Set native PCG partition mode on idle registered current-world component. |
| `set_pcg_graph_instance_parent` |  | Replace persistent graph-instance parent using inspected parent_hash. |
| `set_pcg_graph_parameter` |  | Variants: `scalar`, `text`, `vector`, `enum`, `int64`, `string_array`, `scalar_array`, `vector_array` |
| `set_pcg_graph_parameter_asset` |  | Set compatible persistent hard/soft asset graph parameter, empty clears. |
| `set_pcg_graph_parameter_class` |  | Set/clear compatible loaded native class graph parameter; abstract classes allowed. |
| `set_pcg_graph_parameter_rotator` |  | Set exact FRotator graph parameter; finite angles +/-1e6 degrees. |
| `set_pcg_graph_parameter_transform` |  | Set exact FTransform parameter: Translation XYZ, Rotation XYZW, Scale3D XYZ. |
| `set_pcg_graph_settings` |  | Variants: `scalar`, `enum`, `text` |
| `set_pcg_node_settings` |  | Variants: `scalar`, `enum`, `text`, `string_array` |
| `set_pcg_node_settings_asset` |  | Set compatible persistent hard/soft asset leaf, or clear with empty source. |
| `set_pcg_node_settings_compound` |  | Set exact FVector/FLinearColor settings leaf (kind=vector/color). |
| `set_pcg_subgraph` |  | Bind/clear native subgraph node to registered graph or graph instance. |
| `validate_pcg_graph` |  | Report local PCG node/pin/edge ownership, duplicate labels, symmetry/direction, |

## physics

| Tool | Core | Description |
|---|---|---|
| `add_physics_shape` |  | Add a sphere, box, capsule, or convex shape to an existing Physics Asset body. |
| `create_physics_body` |  | Add a Physics Asset body with an initial sphere, box, capsule, or convex shape. |
| `create_physics_constraint` |  | Connect two Physics Asset bodies with typed linear/angular limits and optional projection. |
| `delete_physics_body` |  | Preview affected constraints/collision pairs and delete a body only with confirm. |
| `delete_physics_constraint` |  | Preview or delete a Physics Asset constraint; deletion requires confirm. |
| `delete_physics_shape` |  | Preview or remove one Physics Asset shape; deletion requires confirm. |
| `edit_physics_body_profile` |  | Add, duplicate, rename, edit, or confirm deletion of a Physical Animation profile. |
| `edit_physics_body_settings` |  | Edit allowlisted Physics Asset body settings after transient preflight. |
| `edit_physics_constraint` |  | Edit Physics Asset constraint body association, limits, and projection. |
| `edit_physics_constraint_drive` |  | Set a full linear or angular drive using UE field names for flags, strengths, and targets. |
| `edit_physics_constraint_profile` |  | Add, duplicate, rename, capture, or confirm deletion of a constraint profile. |
| `inspect_physics_asset` |  | Inspect a Physics Asset. |
| `inspect_physics_body_settings` |  | Inspect a Physics Asset body's type, collision, mass, bounds, and CCD settings. |
| `inspect_physics_constraint_drive` |  | Inspect linear and angular drives for a Physics Asset constraint. |
| `inspect_physics_volume` |  | Read native physics volume priority/friction/terminal velocity/water/contact flags and gravity. |
| `list_physics_bodies` |  | List Physics Asset bodies and primitive-shape counts. |
| `list_physics_body_profiles` |  | List Physical Animation profiles and optional settings for one body. |
| `list_physics_collision_pairs` |  | List disabled collision pairs in a Physics Asset. |
| `list_physics_constraint_profiles` |  | List constraint profiles, coverage, and optional selected constraint drive strengths. |
| `list_physics_constraints` |  | List Physics Asset constraint names and connected bones. |
| `list_physics_shapes` |  | List primitive shapes, collision state, and mass contribution on a Physics Asset body. |
| `refresh_physics_asset` |  | Refresh Physics Asset body caches and notify editor previews. |
| `set_physics_collision_pair` |  | Enable or disable collision between two Physics Asset bodies. |
| `set_physics_volume_setting` |  | Set Priority(int32), TerminalVelocity/FluidFriction(0..1e6), WaterVolume/PhysicsOnContact(bool). |
| `validate_physics_asset` |  | Check Physics Asset body geometry, duplicate bones, preview mesh, and constraint references. |

## playtest_build

| Tool | Core | Description |
|---|---|---|
| `cancel_package` | Core | Stop the running package job and its child processes. |
| `compile_editor_blueprints` | Core | Compile specified Blueprints, or selected Content Browser Blueprints. |
| `control_editor_automation_test` | Core | Variants: `run_editor_automation_test`, `stop_editor_automation_test` |
| `control_ue_play_session` | Core | Control the UE play session. operation must be: start, start_here, pause, resume, or stop. |
| `get_editor_automation_status` | Core | Get completion, success, duration, warnings, errors, and entries for the current test. |
| `get_editor_build_status` | Core | Report asset/shader compilation, redirector fix-up, automation, and PIE activity. |
| `get_editor_screenshot_status` | Core | Report whether the latest requested editor screenshot has been written. |
| `get_package_status` | Core | Report the current package job: running, exit code, output folder and the end of its log. |
| `inspect_gameplay_calculation_definition` |  | Inspect native effect calculation attribute captures: field, source/target, snapshot. |
| `inspect_gameplay_definition_defaults` |  | Read GAS defaults, parent differences, enum options and reference constraints. |
| `inspect_gameplay_evaluation_channels` |  | Inspect native GAS evaluation-channel enablement, IDs, aliases and validity. |
| `inspect_play_session` | Core | Observe the running PIE game: time, GameMode, player pawn location/velocity and live actors. |
| `inspect_project_game_settings` | Core | Read the project's default game map, editor startup map, default GameMode and GameInstance class. |
| `list_editor_automation_tests` | Core | Discover local UE automation tests valid for the current editor environment. |
| `move_play_mouse` | Core | Point the mouse in the running game and report what is under it. Then click with send_play_input. |
| `package_game` | Core | Start packaging the project in the background with RunUAT BuildCookRun; poll get_package_status. |
| `read_play_actor_properties` | Core | Read live values from an actor in the running game, such as a score. |
| `request_editor_screenshot` | Core | Request a deterministic PNG screenshot under Saved/Screenshots/UE5MCP. |
| `send_play_input` | Core | Send a key to the running PIE game's first player, to playtest it. |
| `set_project_game_setting` | Core | Set GameDefaultMap, EditorStartupMap, GlobalDefaultGameMode or GameInstanceClass. |
| `start_play_in_editor` |  | Queue an in-process Play-In-Editor session on the current editor map. |
| `stop_play_in_editor` |  | Request the end of the running Play-In-Editor session (ends on the next tick). |
| `validate_gameplay_definition` |  | Validate loaded native or current compiled GAS ability/effect/calculation/cue defaults on a temporary duplicate. |

## pose_search

| Tool | Core | Description |
|---|---|---|
| `add_pose_search_database_blend_space` |  | Append a registered persistent native Blend Space using default entry settings. |
| `add_pose_search_database_composite` |  | Append a registered persistent native Animation Composite with entry defaults. |
| `add_pose_search_database_montage` |  | Append a registered persistent native Animation Montage with entry defaults. |
| `add_pose_search_database_multi_animation` |  | Append a native experimental multi-animation asset with default entry settings. |
| `add_pose_search_database_sequence` |  | Append native sequence entry with default sampling/options to Pose Search database. |
| `add_pose_search_default_channels` |  | Initialize empty schema with native default trajectory and pose channels. |
| `add_pose_search_group_child` |  | Append native channel child to an authored top-level explicit Group channel. |
| `add_pose_search_interaction_item` |  | Append experimental interaction item with unique role and registered animation. |
| `add_pose_search_schema_channel` |  | Append loaded concrete native feature channel to confirmed /Game schema. |
| `add_pose_search_schema_role` |  | Append native skeleton role to Pose Search schema; mirror table initially unset. |
| `copy_pose_search_asset_setting` |  | Copy one direct setting between exact-class schema/database/interaction assets. |
| `create_pose_search_asset` |  | Create schema, database, normalization_set or interaction via native factories. |
| `duplicate_pose_search_asset` |  | Duplicate a schema, database, normalization set or interaction via AssetTools. |
| `duplicate_pose_search_database_entry` |  | Copy complete authored database entry settings at insertion_index in [0,count]. |
| `duplicate_pose_search_group_child` |  | Append native duplicate of explicit-group child, preserving authored settings. |
| `duplicate_pose_search_interaction_item` |  | Append complete item copy under unique non-None role, sharing asset references. |
| `duplicate_pose_search_schema_channel` |  | Duplicate authored native channel/settings and append under same schema. |
| `duplicate_pose_search_schema_role` |  | Append a new unique role sharing source role skeleton and mirror table. |
| `evaluate_pose_search_interaction_warp` |  | Evaluate native interaction warp at one time using ordered actor root transforms. |
| `finalize_pose_search_schema` |  | Invoke native schema finalization/notifications and report resulting cached layout. |
| `inspect_pose_search_asset_setting` |  | Inspect direct schema/database/interaction setting beside native class default. |
| `inspect_pose_search_channel` |  | Read authored feature-channel fields guarded by current index/object identity. |
| `inspect_pose_search_database` |  | Read native Pose Search database animation assets and schema summary. |
| `inspect_pose_search_database_entry` |  | Read native current-index/animation-path guarded database entry settings. |
| `inspect_pose_search_entry_timing` |  | Inspect native duration and effective interval at supplied blend parameters. |
| `inspect_pose_search_interaction` |  | Inspect native experimental interaction asset items (up to 64). |
| `inspect_pose_search_normalization_set` |  | Inspect up to 256 authored database references in a native normalization set. |
| `inspect_pose_search_sampling_points` |  | Enumerate native entry blend parameters (up to 1024) without pose sampling. |
| `inspect_pose_search_schema` |  | Read native Pose Search schema roles and authored feature channels. |
| `list_pose_search_channel_types` |  | Discover loaded concrete native Pose Search feature-channel classes/defaults. |
| `move_pose_search_database_entry` |  | Move complete authored entry to final_index in [0,count), preserving settings. |
| `move_pose_search_group_child` |  | Move explicit-group child to final_index, preserving child objects/settings. |
| `move_pose_search_interaction_item` |  | Move complete interaction item to final_index, preserving all item settings. |
| `move_pose_search_schema_channel` |  | Move authored Pose Search channel to final index while preserving object/settings. |
| `move_pose_search_schema_role` |  | Move a unique role entry to final_index, preserving names and references. |
| `remove_pose_search_database_entry` |  | Remove current native database entry, preserving source animation asset. |
| `remove_pose_search_group_child` |  | Remove authored explicit-group child reference guarded by index/object identity. |
| `remove_pose_search_interaction_item` |  | Remove interaction item guarded by current index, role and animation identity. |
| `remove_pose_search_schema_channel` |  | Remove authored channel reference with native schema finalization. |
| `remove_pose_search_schema_role` |  | Remove a unique schema role entry. Channels/dependent databases are not migrated; |
| `rename_pose_search_interaction_role` |  | Rename selected interaction role to a unique non-None name, retaining settings. |
| `rename_pose_search_schema_role` |  | Rename a unique schema role, retaining skeleton/mirror references. |
| `replace_pose_search_entry_animation` |  | Replace supported entry animation preserving authored settings. |
| `request_pose_search_database_index` |  | Request asynchronous native derived indexing: new or continue. |
| `reset_pose_search_asset_setting` |  | Reset one direct schema/database/interaction setting to native class default. |
| `reset_pose_search_channel_field` |  | Reset scalar/enum/name/vector/linear-color leaf to its native channel class default. |
| `sample_pose_search_entry_root` |  | Temporarily sample native role root transform at time/blend parameters. |
| `set_pose_search_blend_sampling_range` |  | Set normalized Blend Space entry interval: [0,0] full duration or 0<=start<end<=1. |
| `set_pose_search_channel` |  | Variants: `scalar`, `name`, `enum`, `vector`, `color` |
| `set_pose_search_database_cost_bias` |  | Set BaseCostBias, ContinuingPoseCostBias, LoopingCostBias or |
| `set_pose_search_database_entry_flags` |  | Edit native database entry enabled/reselection flags, rejecting external sync entries. |
| `set_pose_search_database_index_tuning` |  | Set one native index tuning field with bounds and integer validation. |
| `set_pose_search_database_interval` |  | Set ExcludeFromDatabaseParameters or AdditionalExtrapolationTime offsets. |
| `set_pose_search_database_normalization_set` |  | Assign a registered native normalization set; empty path clears the reference. |
| `set_pose_search_database_preview_mesh` |  | Set editor preview override; empty path clears to native skeleton default. |
| `set_pose_search_database_schema` |  | Assign native Pose Search schema to confirmed persistent /Game database. |
| `set_pose_search_database_search_mode` |  | Set BruteForce, PCAKDTree, VPTree or EventOnly native search mode. |
| `set_pose_search_database_tags` |  | Replace ordered FName metadata tags; empty list clears (not Gameplay Tags). |
| `set_pose_search_entry_mirror_policy` |  | Set authored entry mirror policy: original, mirrored, or both. |
| `set_pose_search_entry_sampling_range` |  | Set sequence/composite/montage entry range; [0,0] means full duration. |
| `set_pose_search_interaction_animation` |  | Replace interaction item animation, retaining role/origin/warp settings. |
| `set_pose_search_interaction_banking` |  | Set experimental interaction WarpingBankingWeight to finite 0..1. |
| `set_pose_search_interaction_origin` |  | Set role origin relative to shared interaction frame using native Transform JSON. |
| `set_pose_search_interaction_preview_mesh` |  | Assign editor preview mesh override; empty path clears to native default preview. |
| `set_pose_search_interaction_weight` |  | Set WarpingWeightRotation or WarpingWeightTranslation to finite 0..1. |
| `set_pose_search_normalization_databases` |  | Replace normalization-set membership with up to 256 unique native databases. |
| `set_pose_search_pose_bones` |  | Replace pose-channel sampled bones, up to 64 unique channel sampling-role skeleton bones. |
| `set_pose_search_role_mirror_table` |  | Assign/clear role mirror table; empty path clears, exact role skeleton required. |
| `set_pose_search_role_skeleton` |  | Replace an existing schema role skeleton with a registered persistent skeleton. |
| `set_pose_search_sampling` |  | Variants: `set_pose_search_blend_sampling`, `set_pose_search_multi_animation_sampling` |
| `set_pose_search_schema_flag` |  | Set bAddDataPadding, bInjectAdditionalDebugChannels or |
| `set_pose_search_schema_permutation` |  | Set NumberOfPermutations (integer 1..1e9), PermutationsSampleRate (1..240), |
| `set_pose_search_schema_preprocessor` |  | Set schema data preprocessor: None, Normalize, NormalizeOnlyByDeviation, |
| `set_pose_search_schema_sample_rate` |  | Edit native Pose Search schema sample rate 1..240, invoking schema Finalize. |
| `set_pose_search_trajectory_samples` |  | Replace trajectory samples (<=64), empty list clears. |

## remote_control

| Tool | Core | Description |
|---|---|---|
| `create_remote_control_preset` |  | Create an empty Remote Control Preset in an unused /Game package. |
| `expose_remote_control_field` |  | Expose an editable property or BlueprintCallable function of a loaded editor object on a preset. |
| `inspect_remote_control_preset` |  | Inspect a preset's exposed properties and functions, bound objects and current property values. |
| `list_remote_control_presets` |  | List Remote Control Preset assets from the asset registry. |
| `set_remote_control_value` |  | Set an exposed property on its bound objects using UE text, guarded by the inspected label and value. |
| `unexpose_remote_control_field` |  | Remove an exposed property or function from a preset, guarded by its inspected id and label. |

## rigs

| Tool | Core | Description |
|---|---|---|
| `compile_control_rig` |  | Recompile a Control Rig Blueprint VM and report compiler counts. |
| `compile_modular_rig` |  | Recompile a Modular Rig and report VM compiler counts. |
| `edit_control_rig_graph` |  | Add/edit RigVM nodes, collapse or expand selected graph nodes, create constants/structs/reroutes on pins, resolve templates, edit dynamic array pins, and cha... |
| `edit_control_rig_hierarchy` |  | Add/edit Control Rig values, settings, available spaces, and channel hosts. switch_parent preserves the control's global transform by default; maintain_globa... |
| `edit_modular_rig_connection` |  | Connect, disconnect, or edit targets of a Modular Rig connector. |
| `edit_modular_rig_module` |  | Add, rename, reparent, or confirm deletion of a Modular Rig module. |
| `edit_modular_rig_variable` |  | Set/reset a module config override or bind/unbind a top-level variable. |
| `inspect_control_rig` |  | Inspect a Control Rig or Modular Rig asset. |
| `list_control_rig_graphs` |  | List RigVM model graphs with node summaries and links. |
| `list_control_rig_hierarchy` |  | List Control Rig hierarchy elements with type, parent, and child count. |
| `list_control_rig_templates` |  | List registered RigVM template notations, optionally filtered by name. |
| `list_modular_rig_connections` |  | List Modular Rig connector targets and unresolved connectors. |
| `list_modular_rig_modules` |  | List Modular Rig module references, classes, and parents. |
| `list_modular_rig_variables` |  | List a module's editable variables, config overrides, and bindings. |
| `validate_control_rig` |  | Validate RigVM graph nodes, pins, links, templates, and contained graphs, optionally compiling the Control Rig VM. |
| `validate_modular_rig` |  | Check module references and unresolved required connectors. |

## splines

| Tool | Core | Description |
|---|---|---|
| `add_spline_actor_component` |  | Create/register native instance Spline component on existing persistent actor. |
| `add_spline_mesh_actor_component` |  | Create a native spline mesh instance component on an existing persistent actor. |
| `clear_spline_points` |  | Clear all spline points using inspected count<=4096 guard/native update. |
| `find_spline_closest_point` |  | Native closest input-key query and world frame/distance-table readback. |
| `fit_spline_mesh_to_segment` |  | Fit existing mesh endpoints to source spline segment, including the closing segment. |
| `insert_spline_point` |  | Insert local point at index0..count; index=count appends, resulting count<=4096. |
| `inspect_spline_points` |  | Read native spline points in local coordinates, pages1..128. |
| `inspect_spline_segments` |  | Read native segment pages1..128, Local/World, including closing-loop key span. |
| `inspect_spline_settings` |  | Read spline duration/reparameterization steps/stationary endpoints/local up. |
| `inspect_world_spline_components` |  | Discover up to128 loaded stopped-editor-world spline components/subclasses. |
| `inspect_world_spline_mesh_components` |  | Discover up to128 loaded current editor-world spline mesh components. |
| `remove_spline_actor_component` |  | Remove inspected ordinary spline instance component; nonroot/no children required. |
| `remove_spline_mesh_actor_component` |  | Remove inspected actor instance spline mesh; nonroot/no attached children required. |
| `remove_spline_point` |  | Remove inspected spline point with count/current local position guards. |
| `replace_spline_point_positions` |  | Replace all spline positions0..4096, reset native point properties/metadata. |
| `reset_spline_closing_key` |  | Restore automatic closing key on an already closed spline with inspected count/key guards. |
| `sample_spline_by_distance` |  | Sample native distance table at1..128 equally spaced inclusive distances. |
| `sample_spline_by_time` |  | Sample1..128 times within0..authored duration; end-1 uses duration. |
| `sample_spline_mesh_slices` |  | Read1..128 native local deformation slice transforms over ordered alpha0..1. |
| `set_spline_closed_loop` |  | Open/close spline with current count/loop-state guards and native update. |
| `set_spline_closing_key` |  | Set closing parameter on an already closed spline with inspected count/key guards. |
| `set_spline_default_up_vector` |  | Set normalized local default up vector with inspected count/current vector guards. |
| `set_spline_mesh_asset` |  | Assign a loaded persistent noncompiling mesh with inspected current asset guard. |
| `set_spline_mesh_boundaries` |  | Set spline mesh longitudinal bounds with inspected current min/max guards. |
| `set_spline_mesh_endpoints` |  | Set component-local spline mesh endpoints/tangents together, with inspected asset/four-vector guards. |
| `set_spline_mesh_forward_axis` |  | Set longitudinal mesh axis X/Y/Z with inspected native ordinal (0/1/2) guard. |
| `set_spline_mesh_offsets` |  | Set local cross-section XY offset pairs with inspected offset/asset identity guards. |
| `set_spline_mesh_rolls` |  | Set start/end roll in radians with inspected exact roll/asset identity guards. |
| `set_spline_mesh_scales` |  | Set local cross-section XY scale pairs with inspected scale/asset identity guards. |
| `set_spline_mesh_smooth_interpolation` |  | Set native eased versus linear roll/scale/offset interpolation with current flag guard. |
| `set_spline_mesh_up_direction` |  | Set normalized local spline mesh up direction with inspected vector/asset guards. |
| `set_spline_point_position` |  | Move inspected spline point in local coordinates with exact count/position guard. |
| `set_spline_point_rotation` |  | Set normalized local XYZW quaternion with inspected count/orientation guards. |
| `set_spline_point_scale` |  | Set point scale XYZ +/-1000, including zero/negative values, with current guards. |
| `set_spline_point_tangents` |  | Set local arrive/leave tangents; native setter switches to CurveCustomTangent. |
| `set_spline_point_type` |  | Set Linear/Curve/Constant/CurveClamped/CurveCustomTangent point type. |
| `set_spline_setting` |  | Set Duration(>0<=1e6), ReparamStepsPerSegment(integer4..100), StationaryEndpoints(bool). |

## state_tree

| Tool | Core | Description |
|---|---|---|
| `compile_state_tree` |  | Compile through the native StateTree editor pipeline after transient preflight. |
| `create_state_tree` | Core | Create a native StateTree with its schema/editor data, root and compiled data. |
| `edit_state_tree_binding` |  | Set/delete a direct native property binding with compile preflight. |
| `edit_state_tree_function` |  | Create/update/delete a native StateTree property function with compile preflight. |
| `edit_state_tree_node` |  | Create/update/delete schema-approved native struct nodes with compile preflight. |
| `edit_state_tree_parameter` |  | Create/update/delete/reset a native root or state property-bag parameter. |
| `edit_state_tree_schema` |  | Edit owned schema scalar, reference, container and context-class fields. |
| `edit_state_tree_state` |  | Create/update/move/delete a native StateTree state with compile preflight. |
| `edit_state_tree_transition` |  | Create/update/delete an ordered native transition, preserving its conditions. |
| `inspect_state_tree` |  | Inspect native StateTree hierarchy/nodes/compiled states and hashes. |
| `inspect_state_tree_runtime` |  | Inspect live native StateTree components in the selected PIE world. |
| `list_state_tree_binding_sources` |  | List native execution-scope binding source IDs, types and property names for a target. |
| `list_state_tree_node_classes` |  | List loaded schema-approved concrete native/compiled Blueprint node classes and fields. |
| `list_state_tree_node_types` |  | Discover loaded schema-approved native node structs and editable field metadata. |
| `list_state_tree_schemas` |  | Discover loaded concrete native StateTree schemas and default capabilities. |
| `move_state_tree_node` |  | Reorder a node within its current native collection while preserving GUID/bindings. |
| `move_state_tree_parameter` |  | Reorder a root/state property-bag field, preserving GUID/value; -1 appends. |
| `move_state_tree_transition` |  | Reorder a native transition; index is final position, -1 appends; keeps conditions/IDs. |
| `replace_state_tree_parameter_type` |  | Replace a root/state scalar parameter type while retaining its field GUID/name. |
| `retarget_state_tree_link` |  | Retarget Linked to an owned Subtree or LinkedAsset to linked_asset_path. |
| `set_state_tree_required_event` |  | Set/clear the native event required to enter a state. |
| `state_tree_runtime` |  | Variants: `control_state_tree_runtime`, `send_state_tree_event`, `set_state_tree_runtime_parameters` |

## textures

| Tool | Core | Description |
|---|---|---|
| `align_runtime_virtual_texture_bounds` |  | Align native RVT volume with native SetBounds/landscape snap, unverified. |
| `build_runtime_virtual_texture_streaming_mips` |  | Build one RVT component streaming mips for native supported paths, unverified; no explicit save. |
| `compare_texture_source_mips` |  | Compare native BGRA8 selected source mips/exact IDs/matching layout, unverified. |
| `convert_render_target_to_texture` |  | Native target-to-new-texture conversion with GPU readback/possible render-thread waits, unverified. |
| `copy_texture_source_mip` |  | Copy compatible authored BGRA8 source mip/all slices with exact identities/snapshot, unverified. |
| `create_render_target_2d` |  | Create source-free native 2D render-target asset at new canonical /Game/Folder/Name.Name, dimensions1..2048. |
| `create_render_target_2d_array` |  | Create source-free native array target at new canonical /Game/Folder/Name.Name, no overwrite. |
| `create_render_target_cube` |  | Create source-free exact native cube render-target asset at canonical new /Game/Folder/Name.Name. |
| `create_render_target_volume` |  | Create source-free native volume target at new canonical /Game/Folder/Name.Name, no overwrite. |
| `create_runtime_virtual_texture` |  | Create native runtime virtual-texture asset with native defaults, unverified. |
| `create_runtime_virtual_texture_instance_override` |  | Create absent local material-instance RVT override through native setter, unverified. |
| `create_runtime_virtual_texture_volume` |  | Spawn native RVT volume/root component at location in ordinary unlocked persistent map, unverified. |
| `create_source_texture_2d_array` |  | Create source-backed Texture2DArray through native factory, unverified. |
| `create_source_texture_cube_array` |  | Create source-backed cube array via native factory, unverified. New canonical /Game path, no overwrite. |
| `create_source_volume_texture` |  | Create source-backed volume via native factory, unverified. New /Game path only, no overwrite. |
| `create_texture_2d_array_without_source_file` |  | Optional RGBA byte fill (omitted=opaque white), no linear color conversion. Create opaque-white direct-source Texture2DArray without image/per-slice assets,... |
| `create_texture_2d_without_source_file` |  | Create native Texture2D without an image file, unverified. New canonical /Game path, no overwrite. |
| `create_texture_cube_array_without_source_file` |  | Optional RGBA byte fill (omitted=opaque white), no linear color conversion. Create opaque-white direct-source TextureCubeArray without image/per-cube assets,... |
| `create_texture_cube_without_source_file` |  | Optional RGBA byte fill (omitted=opaque white), no linear color conversion. Create native source-backed TextureCube without image file, opaque-white six face... |
| `create_virtual_texture_builder` |  | Create native empty streaming runtime-VT builder container, unverified. New /Game path, no overwrite. |
| `create_volume_texture_without_source_file` |  | Optional RGBA byte fill (omitted=opaque white), no linear color conversion. Create native opaque-white BGRA8 source-backed volume without image/atlas, unveri... |
| `delete_runtime_virtual_texture_volume` |  | Delete exact native RVT volume/root in ordinary unlocked persistent map, unverified. |
| `discover_runtime_virtual_texture_components` |  | Discover current-world persistent RVT components including unassigned ones1..128, unverified. |
| `discover_runtime_virtual_texture_writers` |  | Discover current-world primitive authored RVT writers including empty destination lists, unverified. |
| `discover_scene_capture_2d_show_flags` |  | Discover native engine/custom show-flag registry in name-sorted pages1..128 with substring filter. |
| `discover_scene_capture_cube_show_flags` |  | Discover native engine/custom show-flag registry in name-sorted pages1..128 with substring filter. |
| `duplicate_runtime_virtual_texture` |  | Duplicate native RVT authored asset through AssetTools/full snapshot guard, unverified. |
| `duplicate_source_texture` |  | Duplicate native source texture through AssetTools with exact class/source attribute ID, unverified. |
| `edit_texture_settings` |  | Edit reflected texture settings, for example SRGB, LODGroup, or MipGenSettings. |
| `export_render_target_image` |  | Export native2D/cube/volume/2D-array DDS or selected slice PNG/EXR/HDR under Saved/UE5_MCP/Exports. |
| `export_texture_source_dds` |  | Export native2D/2D-array/cube/cube-array/volume selected block/layer/all authored mips as DDS. |
| `export_texture_source_image` |  | Export authored source block/layer/mip/slice as PNG/EXR/HDR under Saved/UE5_MCP/Exports. |
| `fill_texture_source_mip` |  | Overwrite selected authored BGRA8 source mip/all slices with RGBA bytes, unverified. |
| `import_texture` | Core | Import a local image (or .ies light profile) as a Texture asset; replacement requires confirmation. |
| `inspect_loaded_render_targets_2d` |  | Page loaded persistent 2D target assets1..128 with path substring, authored metadata only. |
| `inspect_loaded_render_targets_2d_array` |  | Page loaded persistent array targets1..128/path substring with native width/height/slices metadata. |
| `inspect_loaded_render_targets_cube` |  | Page loaded persistent cube target assets1..128/path substring, authored face/HDR/override/mip metadata. |
| `inspect_loaded_render_targets_volume` |  | Page loaded persistent volume targets1..128/path substring with native XYZ/HDR/override metadata. |
| `inspect_loaded_runtime_virtual_textures` |  | Page loaded persistent runtime virtual textures1..128 with native policy dimensions, unverified. |
| `inspect_loaded_source_texture_cube_arrays` |  | Page loaded persistent cube arrays with optional exact direct source-cube reference filter, unverified. |
| `inspect_loaded_source_texture_cubes` |  | Page loaded persistent source-backed cube textures1..128/path substring, excludes cube render targets. |
| `inspect_loaded_source_volume_textures` |  | Page loaded persistent source-backed volume textures1..128/path substring/optional direct2D source filter. |
| `inspect_loaded_texture_2d_arrays` |  | Page loaded persistent source-backed texture arrays1..128/path substring/optional direct source-texture filter. |
| `inspect_loaded_virtual_texture_builders` |  | Page loaded persistent VT builders1..128/hash/authored embedded refs, unverified. |
| `inspect_render_target_2d` |  | Inspect loaded persistent 2D render-target authored settings/dimensions/clear color/native enums. |
| `inspect_render_target_2d_array` |  | Inspect loaded persistent array target width/height/slices/HDR/override/gamma/UAV/clear/edit metadata. |
| `inspect_render_target_2d_capture_consumers` |  | Page direct loaded scene-capture2D target references across all worlds/templates/transients1..128. |
| `inspect_render_target_conversion` |  | Inspect native2D/cube/volume/array render-target conversion policy/class/formats, unverified. |
| `inspect_render_target_cube` |  | Inspect loaded persistent cube target face size/HDR/override/gamma/mip/UAV/clear color/edit metadata. |
| `inspect_render_target_cube_capture_consumers` |  | Page direct loaded cube-capture references across worlds/templates/transients1..128. |
| `inspect_render_target_volume` |  | Inspect loaded persistent volume target XYZ/HDR/override/gamma/UAV/clear/native edit metadata. |
| `inspect_runtime_virtual_texture` |  | Inspect runtime virtual-texture authored policy/native clamped dimensions, unverified. |
| `inspect_runtime_virtual_texture_bounds_contributors` |  | Inspect primitive selection used by native RVT bounds alignment across loaded worlds, unverified. |
| `inspect_runtime_virtual_texture_component_platforms` |  | Page current-world RVT component authored enable overrides1..128/key-sorted, unverified. |
| `inspect_runtime_virtual_texture_component_settings` |  | Inspect current-world RVT component authored bounds/scalability/streaming policies, unverified. |
| `inspect_runtime_virtual_texture_components` |  | Page loaded RVT component direct asset references across worlds/templates/transients1..128, unverified. |
| `inspect_runtime_virtual_texture_effective_parameters` |  | Page declared RVT params/native inherited effective values/local override indices, unverified. |
| `inspect_runtime_virtual_texture_expressions` |  | Page loaded asset-owned RVT sample expression direct refs1..128 and authored flag comparisons, unverified. |
| `inspect_runtime_virtual_texture_instance_parameters` |  | Inspect instance authored RVT override pages1..128/list<=256/full ordered parent-override snapshot, unverified. |
| `inspect_runtime_virtual_texture_layers` |  | Inspect native RVT layer count/policy pixel formats/sRGB/YCoCg sampling, unverified. |
| `inspect_runtime_virtual_texture_overrides` |  | Page loaded persistent material-instance authored direct RVT overrides1..128, unverified. |
| `inspect_runtime_virtual_texture_parameter_declarations` |  | Page native inherited RVT parameter declarations/name-association-layer-GUID and local override indices, unverified. |
| `inspect_runtime_virtual_texture_sample` |  | Inspect individual loaded RVT sample/parameter expression including unassigned refs, unverified. |
| `inspect_runtime_virtual_texture_streaming_status` |  | Explicit native RVT streaming settings/format status for deferred/mobile, unverified. |
| `inspect_runtime_virtual_texture_writer_settings` |  | Inspect current-world primitive authored RVT writer list/LOD-culling/main-pass policy, unverified. |
| `inspect_runtime_virtual_texture_writers` |  | Page loaded primitive authored RuntimeVirtualTextures direct refs1..128, unverified. |
| `inspect_scene_capture_2d_actor_lists` |  | Inspect authored hidden/show-only actor references in independent pages1..128, render-mode and component-list metadata. |
| `inspect_scene_capture_2d_collection_layout` |  | Inspect assigned collection authored vector order/defaults1..128 and configured5/4-vector output capacity/overlap. |
| `inspect_scene_capture_2d_collection_writers` |  | Page loaded capture2D references to selected transform collection across worlds/templates/transients1..128. |
| `inspect_scene_capture_2d_component_lists` |  | Inspect hidden/show-only weak primitive-component references in independent pages1..128. |
| `inspect_scene_capture_2d_settings` |  | Inspect native projection/source/render-mode/scheduling/LOD/priority/ortho-plane settings and enum metadata. |
| `inspect_scene_capture_2d_show_flags` |  | Page stored show-flag overrides1..128 and optionally query current native component bits<=128. |
| `inspect_scene_capture_cube_actor_lists` |  | Inspect authored hidden/show-only actor references in independent pages1..128, render-mode and component-list metadata. |
| `inspect_scene_capture_cube_component_lists` |  | Inspect hidden/show-only weak primitive-component references in independent pages1..128. |
| `inspect_scene_capture_cube_settings` |  | Inspect cube rotation/source/mode/scheduling/postprocess/LOD/distance/priority fields and native snapshots/enums. |
| `inspect_scene_capture_cube_show_flags` |  | Page stored show-flag overrides1..128 and optionally query current native component bits<=128. |
| `inspect_scene_captures_2d_page` |  | Page loaded persistent current-world scene-capture2D metadata1..128, optional exact owner. |
| `inspect_scene_captures_cube_page` |  | Page native loaded persistent current-world cube captures1..128/path sorted/optional owner. |
| `inspect_source_texture_cube` |  | Inspect source-backed TextureCube headers and available authored compression/mip/LOD/filter/long-lat fields. |
| `inspect_source_texture_cube_array` |  | Inspect loaded source-backed cube array headers and source-cube reference pages1..128, unverified. |
| `inspect_source_volume_texture` |  | Inspect source-backed VolumeTexture source headers/tiling/address and optional2D source reference. |
| `inspect_texture` |  | Inspect a Texture asset. |
| `inspect_texture_2d_array` |  | Inspect source-backed Texture2DArray address/source headers and authored source-texture refs1..128. |
| `inspect_texture_2d_settings` |  | Inspect authored native Texture2D address/filter/mip/LOD/compression/color/padding/VT policy, unverified. |
| `inspect_texture_alpha_coverage` |  | Inspect native2D/cube/volume/2D-array/cube-array mip-coverage flag, RGBA thresholds/editability. |
| `inspect_texture_array_source_compatibility` |  | Diagnose complete2D/cube array source-header policy for up to128 refs, unverified. |
| `inspect_texture_brush_assets` |  | Page loaded persistent SlateBrushAsset direct texture resources1..128, unverified. |
| `inspect_texture_compression_settings` |  | Inspect five native source texture classes' compression values/editability/visible enum choices. |
| `inspect_texture_downscale_overrides` |  | Inspect nativeTexture2D authored downscale default/ordered platform pages1..128/options choices. |
| `inspect_texture_expression_references` |  | Page loaded asset-owned texture-base expression direct defaults1..128, unverified. |
| `inspect_texture_sampling_settings` |  | Inspect native2D/cube/volume/array/cube-array LODGroup/Filter/MipGenSettings/MipLoadOptions/SRGB/NeverStream and LOD integer settings. |
| `inspect_texture_source` |  | Inspect source image dimensions, ID, files, and local file status. |
| `inspect_texture_source_identity` |  | Inspect native source identifiers/payload metadata/image compression, unverified. |
| `inspect_texture_source_layout` |  | Discover texture source blocks or layers in independent pages1..128, unverified. |
| `inspect_texture_source_linear_pixels` |  | Native source grayscale/float/HDR image decode and gamma-to-linear pixel pages1..128, unverified. |
| `inspect_texture_source_linear_statistics` |  | Native grayscale/HDR linear-color source statistics, unverified; exact source-ID/decoded64MiB/pixels<=16777216. |
| `inspect_texture_source_mip_statistics` |  | Decode selected BGRA8 source mip for byte-channel statistics/alpha coverage-histogram, unverified. |
| `inspect_texture_source_mips` |  | Inspect selected source block/layer mip header pages1..32, unverified. |
| `inspect_texture_source_pixels` |  | Explicit native BGRA8 source mip decode/pixel pages1..128, unverified; source-ID guard. |
| `inspect_texture_streaming_state` |  | Inspect copied native cached texture residency/requested LOD counts and policy, unverified. |
| `inspect_texture_virtual_policy` |  | Inspect authored VT streaming/priority/prefetch/related LOD policy and native metadata, unverified. |
| `inspect_virtual_texture_builder` |  | Inspect loaded streaming runtime-VT builder flags/hash/desktop-mobile embedded refs, unverified. |
| `inspect_virtual_texture_builder_components` |  | Page loaded RVT component direct streaming-builder refs across worlds/templates/transients, unverified. |
| `measure_texture_source_alpha_coverage` |  | Measure selected native2D/cube/volume/array/cube-array source mip linear RGBA coverage. |
| `patch_texture_source_mip` |  | Patch contiguous authored BGRA8 source mip1..128 pixels with exact prior RGBA bytes, unverified. |
| `reimport_texture` |  | Reimport a Texture from its recorded source or a confirmed new local file. |
| `remove_runtime_virtual_texture_instance_override` |  | Remove one local material-instance RVT override via native array notifications, unverified. |
| `reorder_source_texture_cube_array_sources` |  | Reorder cube-array sources by complete unique index permutation1..128, unverified. |
| `reorder_texture_2d_array_sources` |  | Reorder complete source-texture list1..128 by unique index permutation/full current paths/class guards. |
| `replace_source_texture_cube_array_sources` |  | Replace cube-array sources1..128 with exact previous ordered paths0..128, unverified. |
| `replace_texture_2d_array_sources` |  | Replace list-generated array slices with 1..128 unique loaded compatible sources; native regeneration, unverified. |
| `resize_render_target_2d` |  | Edit paired standard-format target dimensions1..2048 with full previous pair/class guard. |
| `resize_render_target_2d_array` |  | Resize all array target width/height/slices together with full current dimensions/class guards. |
| `resize_render_target_volume` |  | Resize all volume target XYZ together with full current dimensions/class guards. |
| `set_light_texture` |  | Assign loaded IESTexture/LightFunctionMaterial or rect SourceTexture; empty clears. |
| `set_render_target_2d_array_clear_color` |  | Author native array clear linear RGBA-65504..65504 with class/width/height/slices/HDR/full previous color guards. |
| `set_render_target_2d_array_setting` |  | Set native array TargetGamma0..10/bHDR/bSupportsUAV0..1 with exact class/width/height/slices/current scalar guards. |
| `set_render_target_2d_clear_color` |  | Author linear clear RGBA-65504..65504 with full class/dimension/format/previous color guards. |
| `set_render_target_2d_setting` |  | Set TargetGamma0..10, RenderTargetFormat/native mip sampler enums, shared/UAV/auto-mips flags0..1. |
| `set_render_target_cube_clear_color` |  | Author cube clear linear RGBA-65504..65504 with full class/face/HDR/previous color guards. |
| `set_render_target_cube_setting` |  | Set cube SizeX1..2048/TargetGamma0..10/bHDR/bSupportsUAV/bAutoGenerateMips/native MipsSamplerFilter. |
| `set_render_target_volume_clear_color` |  | Author native volume clear linear RGBA-65504..65504 with class/XYZ/HDR/full previous color guards. |
| `set_render_target_volume_setting` |  | Set native volume TargetGamma0..10/bHDR/bSupportsUAV0..1 with exact class/XYZ/current scalar guards. |
| `set_runtime_virtual_texture_bounds_actor` |  | Assign loaded same-world RVT bounds alignment actor soft ref or empty clear, unverified. |
| `set_runtime_virtual_texture_component` |  | Variants: `numeric`, `enum` |
| `set_runtime_virtual_texture_component_fixed_color` |  | Set RVT component fixed streaming-mip linear RGBA+-65504, enabled policy required, unverified. |
| `set_runtime_virtual_texture_component_flag` |  | Set current-world RVT component bool with actor identity/full snapshot guards, unverified. |
| `set_runtime_virtual_texture_component_platform` |  | Edit RVT component EnableInGamePerPlatform Default/Override/RemoveOverride, unverified. |
| `set_runtime_virtual_texture_component_reference` |  | Assign RVT component VirtualTexture/StreamingTexture loaded asset or empty clear, unverified. |
| `set_runtime_virtual_texture_instance_parameter` |  | Set existing declared material-instance-constant RVT override through native setter, unverified. |
| `set_runtime_virtual_texture_layout` |  | Set RVT MaterialType or LODGroup visible enum with exact current/full snapshot, unverified. |
| `set_runtime_virtual_texture_policy` |  | Set runtime VT clear/page-table/update/priority override flags or RemoveLowMips0..5, unverified. |
| `set_runtime_virtual_texture_priority` |  | Set runtime VT CustomPriority visible scoped enum, existing override required, unverified. |
| `set_runtime_virtual_texture_sample_policy` |  | Set RVT sample position-origin/address/mip enums or bEnableFeedback0or1, unverified. |
| `set_runtime_virtual_texture_sample_reference` |  | Assign RVT sample loaded asset/empty clear with exact prior ref/3flags/GUID/membership, unverified. |
| `set_runtime_virtual_texture_size` |  | Set encoded RVT TileCount exponent/TileSize code/TileBorderSize code, unverified. |
| `set_runtime_virtual_texture_volume_transform` |  | Set exact native unattached RVT volume world transform, full identity/settings/prior guards, unverified. |
| `set_runtime_virtual_texture_writer_list` |  | Replace primitive authored RVT writer destinations0..128, empty clears, unverified. |
| `set_runtime_virtual_texture_writer_main_pass` |  | Set primitive VirtualTextureRenderPassType visible enum with actor/writer snapshot guards, unverified. |
| `set_runtime_virtual_texture_writer_numeric` |  | Set primitive RVT VirtualTextureLodBias -7..8/CullMips0..7/MinCoverage0..7, unverified. |
| `set_scene_capture_2d_actor_list` |  | Replace HiddenActors/ShowOnlyActors<=64 with full ordered current-list/class/GUID/label guard. |
| `set_scene_capture_2d_clip_plane` |  | Set world clip-plane base+/-1e9 and unit normal with full prior pair/enable/class/GUID/label guards. |
| `set_scene_capture_2d_collection_parameter` |  | Set CollectionTransformWorldToLocal/CollectionTransformProjection first-vector name with exact prior/ref guards. |
| `set_scene_capture_2d_component_list` |  | Replace HiddenComponents/ShowOnlyComponents<=64 with full prior-path/class/GUID/label guard. |
| `set_scene_capture_2d_output_name` |  | Set UserSceneTextureBaseColor/Normal/SceneColor native FName with exact prior name/class/GUID/label guards. |
| `set_scene_capture_2d_projection_matrix` |  | Set full16-entry row-major native custom projection matrix/use flag with exact prior pair/class/GUID/label guards. |
| `set_scene_capture_2d_resolution_divisor` |  | Set paired MainViewResolutionDivisor integer XY1..64 with full prior pair/class/GUID/label guards. |
| `set_scene_capture_2d_setting` |  | Set inspected native capture setting within reported adapter bounds/native visible enum options. |
| `set_scene_capture_2d_show_flags` |  | Replace complete ordered show-flag overrides<=128 with full prior name/bool/class/GUID/label guards. |
| `set_scene_capture_2d_target` |  | Assign loaded persistent render-target2D asset or empty clear with exact reference/GUID/label guard. |
| `set_scene_capture_2d_transform_collection` |  | Assign loaded material parameter collection or empty clear for native capture matrix outputs. |
| `set_scene_capture_2d_view_channels` |  | Set all five native view-lighting bits0..1 with full prior/class/GUID/label guards, zero allowed. |
| `set_scene_capture_cube_actor_list` |  | Replace HiddenActors/ShowOnlyActors<=64 with full ordered current-list/class/GUID/label guard. |
| `set_scene_capture_cube_component_list` |  | Replace HiddenComponents/ShowOnlyComponents<=64 with full prior-path/class/GUID/label guard. |
| `set_scene_capture_cube_setting` |  | Set inspected native cube capture field with class/GUID/label/current and optional full native snapshot guards. |
| `set_scene_capture_cube_show_flags` |  | Replace complete ordered show-flag overrides<=128 with full prior name/bool/class/GUID/label guards. |
| `set_scene_capture_cube_target` |  | Assign loaded persistent cube render target or empty clear with exact previous reference/GUID/label guards. |
| `set_scene_capture_cube_view_channels` |  | Set all five native view-lighting bits0..1 with full prior/class/GUID/label guards, zero allowed. |
| `set_source_volume_texture_address` |  | Set source VolumeTexture tiling0 Wrap1 Clamp2 Mirror on all axes with exact class/current guard. |
| `set_source_volume_texture_source` |  | Replace volume source reference and explicit paired tile sizes; native source regeneration, unverified. |
| `set_source_volume_texture_tiles` |  | Set paired volume source tile sizes; native source regeneration, unverified. |
| `set_texture_2d_address` |  | Set native Texture2D AddressX/Y0 Wrap1 Clamp2 Mirror, unverified. |
| `set_texture_2d_adjustment` |  | Set native Texture2D non-destructive color-adjustment policy, unverified. |
| `set_texture_2d_array_address` |  | Set source-backed Texture2DArray AddressX/Y/Z0 Wrap1 Clamp2 Mirror with exact class/current guards. |
| `set_texture_2d_build_resize` |  | Set paired Texture2D ResizeDuringBuildX/Y0..4096, zero uses source dimension, unverified. |
| `set_texture_2d_filter` |  | Set native Texture2D Filter visible enum with exact current/source ID guards, unverified. |
| `set_texture_2d_lod_limit` |  | Set Texture2D LODBias -32..32/NumCinematicMipLevels0..32/MaxTextureSize0 or power-of-two1..16384. |
| `set_texture_2d_mip_load_policy` |  | Set Texture2D MipLoadOptions visible native scoped enum, unverified. |
| `set_texture_2d_mip_policy` |  | Set Texture2D MipGenSettings visible native enum, unverified; enum options from settings inspection. |
| `set_texture_2d_padding_color` |  | Set authored Texture2D PaddingColor full RGBA bytes, unverified; no linear conversion. |
| `set_texture_2d_padding_policy` |  | Set Texture2D PowerOfTwoMode visible native enum with source/current/snapshot guards, unverified. |
| `set_texture_2d_processing_flag` |  | Set Texture2D bPreserveBorder/bFlipGreenChannel/bPadWithBorderColor with exact current/source guards, unverified. |
| `set_texture_alpha_coverage` |  | Set native2D/cube/volume/2D-array/cube-array mip coverage scaling and four RGBA thresholds0..1. |
| `set_texture_build_resize` |  | Pair native source texture ResizeDuringBuildX/Y0..4096,0 uses source dimension. |
| `set_texture_color_adjustment` |  | Set native2D/cube/volume/array/cube-array AdjustBrightness/BrightnessCurve/Vibrance/Saturation/ |
| `set_texture_compression_setting` |  | Set native source texture CompressionSettings/CompressionQuality/LossyCompressionAmount enum |
| `set_texture_downscale_override` |  | NativeTexture2D downscale Default/Override/RemoveOverride; values0..8, Default empty key. |
| `set_texture_padding_color` |  | Set native source texture PaddingColor RGBA bytes0..255, five native classes where editable. |
| `set_texture_sampling_setting` |  | Set five native source texture classes' LODGroup/Filter/MipGenSettings/MipLoadOptions enum or SRGB/NeverStream boolean0or1. |
| `set_texture_virtual_policy` |  | Set authored VT prefetch/priority policy on existing VT2D texture, unverified. |
| `set_virtual_texture_builder_mobile_policy` |  | Set builder separate-mobile bool with exact hash/desktop-mobile refs/current guard, unverified. |
| `synchronize_runtime_virtual_texture_sample` |  | Synchronize native RVT sample type/packed/adaptive flags from assigned asset, unverified. |
| `update_texture_from_render_target` |  | Native render-target readback into existing texture source with full snapshots, unverified. |
| `validate_texture_source_mip_payloads` |  | Native decode/size validation for all source mips in selected block-layer, unverified. |

## ui

| Tool | Core | Description |
|---|---|---|
| `add_widget_to_blueprint` | Core | Add a UMG widget to the root or to an existing panel widget. |
| `create_widget_blueprint` | Core | Create a real UWidgetBlueprint, optionally derived from a UUserWidget class. |
| `list_widget_blueprint_widgets` | Core | List Widget Blueprint widgets, classes, parents, and child indices. |
| `remove_widget_from_blueprint` | Core | Remove a widget and its descendants from a Widget Blueprint. |
| `reparent_widget` | Core | Move a Widget Blueprint widget under another panel widget. |
| `set_widget_properties` | Core | Set reflected Widget properties such as text, visibility, anchors, or render transform. |

## volumes

| Tool | Core | Description |
|---|---|---|
| `create_box_volume` | Core | Optional native hollow Box/Cylinder; Box wall_thickness is full dimension reduction |
| `create_cone_volume` |  | Create native polygonal cone volume, same types/map rules as box/cylinder. |
| `create_cylinder_volume` |  | Optional native hollow Box/Cylinder; Box wall_thickness is full dimension reduction |
| `create_sphere_volume` |  | Location type also supports initialized World Partition, native unheld editor loader. |
| `delete_volume` |  | Delete inspected persistent-level volume in ordinary map; no attached actors required. |
| `inspect_cull_distance_volume` |  | Read enabled state and size/cull-distance table pages1..128. |
| `inspect_editor_streaming_volumes` |  | Inspect loaded streaming volume identities/settings/assignments in current editor world. |
| `inspect_pain_volume` |  | Read native pain volume damage/interval/flags/type/instigator; no damage/timer calls. |
| `inspect_volume_brush_builder` |  | Read stored Box/Cylinder/Sphere builder dimensions/flags and model identity/count guards. |
| `inspect_volume_brush_polygons` |  | Inspect native authored brush polygons in local space, page1..128/first64 vertices each. |
| `inspect_volume_cached_overlaps` |  | Read up to128 current-world actors from inspected brush's existing overlap cache. |
| `inspect_volume_collision` |  | Read brush collision profile/enabled/overlap/physics-state and body aggregate counts. |
| `inspect_volume_collision_profiles` |  | Read project collision presets(up to128),32 channel names/object-trace query mappings. |
| `inspect_world_volume_page` |  | Inspect sorted loaded current-world volume pages1..128 with optional loaded class/level filters. |
| `inspect_world_volumes` |  | Read up to128 loaded current-world volume actors/subclasses and coarse world bounds. |
| `query_volume_point` |  | Native world-space volume point/sphere overlap, radius0..1e6/world XYZ+/-1e9. |
| `replace_cull_distance_volume_table` |  | Replace entire ordered cull table with full inspected table guard; max4096 pairs. |
| `replace_volume_brush_shape` |  | Optional native hollow Box/Cylinder; Box wall_thickness is full dimension reduction |
| `set_cull_distance_volume_enabled` |  | Set cull-volume enabled flag with inspected current-state guard. |
| `set_cull_distance_volume_entry` |  | Edit existing cull size/distance pair0..1e9 with inspected count/current pair guards. |
| `set_editor_streaming_volume_setting` |  | Edit loaded persistent streaming volume bDisabled/bEditorPreVisOnly0..1 or StreamingUsage0..4. |
| `set_editor_sublevel_streaming_volumes` |  | Replace full ordered sublevel streaming-volume assignments<=64; empty clears. |
| `set_editor_sublevel_volume_unload_cooldown` |  | Set authored native float volume-unload cooldown seconds0..1e6 with exact current guard. |
| `set_pain_volume_damage_type` |  | Assign loaded UDamageType subclass with exact inspected current class guard. |
| `set_pain_volume_setting` |  | Set DamagePerSec(0..1e6), PainInterval(0.001..1e6), PainCausing/EntryPain(bool). |
| `set_volume_brush_color` |  | Set authored volume wireframe custom RGBA bytes and enable flag with full stale guards. |
| `set_volume_collision_enabled` |  | Set NoCollision/QueryOnly/PhysicsOnly/QueryAndPhysics/ProbeOnly/QueryAndProbe. |
| `set_volume_collision_object_type` |  | Set brush native object channel ordinal0..31 with inspected current type guard. |
| `set_volume_collision_profile` |  | Assign configured collision preset with inspected current name/brush identity guards. |
| `set_volume_collision_response` |  | Set one native channel0..31 to Ignore/Overlap/Block; expected ordinal0/1/2. |
| `set_volume_overlap_events` |  | Set inspected volume brush overlap-event flag with exact identity/current-value guards. |

## world

| Tool | Core | Description |
|---|---|---|
| `add_actor_component` | Core | Create and register a transactional instance component on a placed actor. |
| `add_editor_sublevel` |  | Attach an existing map as a streaming sublevel with an optional transform. |
| `attach_actor_component` |  | Attach a scene component to another component, or detach when the parent is empty. |
| `create_editor_world` | Core | Create a blank map or an independent map copied from a template. |
| `create_level_instance` |  | Create a native standalone Level Instance from a saved /Game map in the active editor level. |
| `delete_actor_component` |  | Delete a non-root instance component; confirmation is always required. |
| `delete_editor_actor` | Core | Delete an editor actor; requires confirm=True. |
| `duplicate_editor_actor` | Core | Duplicate an editor actor with an optional X/Y/Z offset. |
| `edit_editor_actor_transform` | Core | Edit an actor transform, label, folder, or attachment in the current level. |
| `edit_level_instance` |  | Variants: `operate_level_instance`, `break_level_instance` |
| `get_actor_component_properties` | Core | Serialize reflected properties for one component on a placed actor. |
| `get_ue_viewport` | Core | Get the active level viewport camera location and rotation. |
| `inspect_editor_world` |  | Inspect the active world, or metadata for a specified UE map asset. |
| `inspect_editor_world_settings` | Core | Includes field_capabilities: native leaf/member editability, storage/config flags, |
| `inspect_level_instances` |  | Inspect Level Instances, loaded/editing actors, and source editing state; optionally validate map references and cycles. |
| `inspect_precomputed_visibility_override` |  | Inspect authored visible/invisible actor and invisible-level refs, independent pages1..128. |
| `inspect_world_composition_tile_hierarchy` |  | Inspect cached tile ancestors<=128 and sorted direct-child pages1..128. |
| `inspect_world_composition_tiles` |  | Read existing ordinary-world cached composition tiles, native-order pages1..128. |
| `list_actor_components` | Core | List the deterministic component hierarchy of a placed editor actor. |
| `list_editor_actors` | Core | List actors in the current editor world, optionally filtered by label/name/class. |
| `list_editor_sublevels` |  | List streaming sublevels attached to the active editor world. |
| `list_editor_worlds` |  | List UE map assets deterministically without loading them. |
| `load_editor_world` | Core | Load a UE map into the editor using a /Game package or object path. |
| `make_editor_sublevel_current` |  | Make an already-loaded unlocked ordinary sublevel current for editing and visible. |
| `place_editor_asset` | Core | Place an actor class or asset using UE's actor-factory workflow and an explicit transform. |
| `query_scene_actors` | Core | Query placed actors deterministically by identity, class, tag, folder, level, or bounds. |
| `remove_editor_sublevel` |  | Detach a streaming sublevel; requires explicit confirmation. |
| `save_editor_world` | Core | Save the active map, optionally under a new /Game path. |
| `select_all_editor_actors` |  | Select all actors in the current editor world. |
| `select_editor_actors` | Core | Replace the level-editor selection with actor object paths. |
| `set_actor_component_properties` | Core | Set reflected properties on one placed-actor component transactionally. |
| `set_editor_actor_properties` | Core | Set reflected actor properties using UE property paths and string values. |
| `set_editor_sublevel` |  | Variants: `color`, `boolean` |
| `set_editor_sublevel_folder` |  | Set native sublevel organization folder, including unloaded ordinary attached entries. |
| `set_editor_sublevel_locked` |  | Set authored edit lock of an already-loaded ordinary attached sublevel. |
| `set_editor_sublevel_priority` |  | Set native signed32 sublevel streaming priority with current/context guards. |
| `set_editor_sublevel_streaming_class` |  | Replace an already-loaded ordinary sublevel streaming class using native editor helper. |
| `set_editor_sublevel_transform` |  | Set already-loaded ordinary sublevel offset through native editor transform handling. |
| `set_editor_sublevel_visibility` |  | Load as needed and set a streaming sublevel's editor visibility. |
| `set_editor_world_settings` | Core | Ordinary-map HLOD policy: bGenerateSingleClusterForLevel and TransformSettings.HLODBakingTransform, |
| `set_precomputed_visibility_override_actors` |  | Replace OverrideVisibleActors/OverrideInvisibleActors<=64 with full ordered stale guard. |
| `set_precomputed_visibility_override_levels` |  | Replace complete invisible-level name list<=64 with exact ordered previous-name guard. |
| `set_ue_viewport` | Core | Set the active level viewport camera using X/Y/Z and Pitch/Yaw/Roll fields. |
| `set_world_composition_setting` |  | Set existing composition instance policy with exact identities/current value guard. |
| `set_world_composition_tile_display` |  | Set loaded tile browser ZOrder signed32 or bHideInTileView0..1 with native metadata guards. |
| `set_world_composition_tile_layer` |  | Edit existing loaded tile's embedded layer metadata with full native cache/package guards. |
| `spawn_editor_actor` | Core | Spawn an Actor class or placeable asset in the current editor world. |
| `validate_editor_world` |  | Validate a map and optionally its dependencies or active-world Map Check. |

## world_partition

| Tool | Core | Description |
|---|---|---|
| `add_partition_runtime_hlod_setup` |  | Append spatial HLOD setup before trailing persistent setup via native ArrayAdd/fixup. |
| `add_partition_runtime_main_definition` |  | Append native HashSet main definition from loaded concrete runtime partition class. |
| `add_partition_spatial_hash_grid` |  | Append authored SpatialHash grid with full ordered unique current names/count<128 guards. |
| `add_world_legacy_hlod_level` |  | Append native-default local legacy HLOD level, exact count<128/no override/ordinary map guards. |
| `create_data_layer_asset` |  | Create standalone ordinary Data Layer asset using native factory/AssetTools, no overwrite. |
| `create_partition_data_layer_instance` |  | Create ordinary asset-backed Data Layer instance from already-loaded persistent asset. |
| `create_partition_private_data_layer` |  | Create native private editor Data Layer with constructor-owned embedded asset. |
| `create_partition_streaming_source_component` |  | Create native streaming-source instance on loaded editable descriptor actor/current source count<64. |
| `create_world_partition_editor_region` |  | Create unloaded native partition-owned box loader, inspected partition/registry count<1024. |
| `create_world_partition_hlod_layer_asset` |  | Create native HLOD Layer using factory/AssetTools at new /Game path, no overwrite. |
| `delete_partition_data_layer_instance` |  | Remove ordinary layer instance via native editor subsystem; source asset retained. |
| `duplicate_world_legacy_hlod_level` |  | Append full reflected copy of existing local legacy HLOD level, preserving prior levels. |
| `inspect_data_layer_asset_info` |  | Variants: `inspect_data_layer_asset`, `inspect_partition_private_data_layer_asset` |
| `inspect_hlod_builder_setting_fields` |  | Inspect native HLOD builder settings root or nested struct path(up to8), page1..128. |
| `inspect_hlod_cluster_volume` |  | Inspect manual HLOD volume overlap policy/zero-based tier filter, empty=all. |
| `inspect_loaded_partition_actor_data_layers` |  | Page registered current-world layers with loaded actor effective/direct membership and native eligibility. |
| `inspect_partition_actor_pin` |  | Inspect native pin hold/weak loaded state and GUID-only API descriptor identity compatibility. |
| `inspect_partition_actor_pins` |  | Page native GUID-addressable descriptors matching pinned/unpinned state, up to128 matches. |
| `inspect_partition_actor_reference_graph` |  | Bounded same-container BFS descriptor reference graph:<=128 nodes/depth16/1024 edges. |
| `inspect_partition_actor_referencers` |  | Reverse one-hop descriptor references in exact target container/page1..128 matches. |
| `inspect_partition_data_layer_hierarchy` |  | Inspect registered layer ancestors<=128 and descendants<=128/depth16 with cycle/frontier flags. |
| `inspect_partition_data_layer_impact` |  | Inspect direct children and paginated matching registered actor descriptors without loading. |
| `inspect_partition_data_layers` |  | Page current-world registered Data Layers without requiring an actor path. |
| `inspect_partition_default_hlod_layer` |  | Inspect current initialized partition default HLOD reference/streaming/editability/package state. |
| `inspect_partition_editor_region` |  | Inspect exact registered partition-owned loader wrapper/world/hold/optional label-color-bounds/count. |
| `inspect_partition_hlod_options` |  | Inspect authored HLOD editor permission/standalone build flag/native experimental eligibility. |
| `inspect_partition_location_volumes` |  | Page loaded native LocationVolume actor-owned editor loaders1..128 with identity/hold/bounds/color. |
| `inspect_partition_policies` |  | Inspect authored native server streaming/stream-out/Data Layer logic enums/choices/editability. |
| `inspect_partition_runtime_cell_contents` |  | Page native existing cell actor names or sorted unique package names1..128 without loading. |
| `inspect_partition_runtime_cell_detail` |  | Inspect exact hash-enumerated cell path/GUID:state/policy/HLOD/data-layer and native data bounds. |
| `inspect_partition_runtime_cell_mappings` |  | Page existing native level-streaming cell actor/package/container mappings1..128. |
| `inspect_partition_runtime_classes` |  | Discover loaded runtime-partition classes/page1..128, creation flag eligibility and editable metadata32. |
| `inspect_partition_runtime_definition_fields` |  | Inspect existing uniquely owned runtime definition native/custom fields/page1..128. |
| `inspect_partition_runtime_definitions` |  | Inspect authored native RuntimeHashSet main/HLOD partition definitions, page1..128. |
| `inspect_partition_runtime_grid_eligibility` |  | Native current hash IsValidGrid for supplied token/loaded actor class plus default grid. |
| `inspect_partition_runtime_hlod_eligibility` |  | Native hash HLOD eligibility for loaded layer/grid plus explicit HashSet setup matches128/count. |
| `inspect_partition_runtime_hlod_layer_references` |  | Page all existing HLOD setup reference slots1..128 with full inspected setup ownership guards. |
| `inspect_partition_runtime_hlod_setups` |  | Page authored spatial/nonspatial HLOD setup identities1..128 with full main ownership guards. |
| `inspect_partition_spatial_hash_grid_info_actors` |  | Inspect loaded native hidden/NotPlaceable grid-info actor contributions/page1..128. |
| `inspect_partition_spatial_hash_grids` |  | Inspect authored RuntimeSpatialHash grid definitions/page1..128 without actor load/generation. |
| `inspect_partition_spatial_hash_settings` |  | Inspect authored project overrides0..2/current native defaults/resolved flags/Z culling/cached settings. |
| `inspect_partition_streaming` |  | Inspect authored/effective/editor partition streaming flags and registered/loaded descriptor counts. |
| `inspect_partition_streaming_source_components` |  | Inspect loaded authored editor source components/owner identity/flags/enums/grids/color/shape count. |
| `inspect_partition_streaming_source_shapes` |  | Page authored source shapes1..128 as native DTO-compatible objects for exact array guards. |
| `inspect_world_legacy_hlod_fields` |  | Discover authored local HLOD nested structs<=8/page1..128, metadata and simple native text. |
| `inspect_world_legacy_hlod_levels` |  | Read authored local legacy HLOD setup levels/common clustering settings, pages1..128. |
| `inspect_world_legacy_hlod_setup_classes` |  | Discover loaded HLOD setup subclasses/selectability flags, sorted pages1..128. |
| `inspect_world_partition` |  | Inspect World Partition, external actors, streaming, and Data Layer counts. |
| `inspect_world_partition_actor_descriptor` |  | Inspect single native descriptor by partition/container path/GUID without loading actor. |
| `inspect_world_partition_actor_descriptors` |  | Page registered WorldPartition actor descriptors without loading actors, offset0..1e6/count1..128. |
| `inspect_world_partition_actor_references` |  | Page native direct actor references1..128, optional editor-only array, same-container metadata lookup. |
| `inspect_world_partition_box_actors` |  | Query registered descriptor editor bounds intersecting box without loading actors. |
| `inspect_world_partition_containers` |  | Page native registered descriptor-container paths/IDs/packages/transform/child count/partition metadata. |
| `inspect_world_partition_editor_regions` |  | Page partition-owned editor loader adapters/path/world/loaded/user-created/label/bounds1..128. |
| `inspect_world_partition_hlod_layer` |  | Inspect loaded HLOD asset generation type/builder settings/classes/parent/linked references. |
| `inspect_world_partition_hlod_layer_referencers` |  | Page loaded HLOD assets referencing target as parent/linked layer1..128, including inactive links. |
| `inspect_world_partition_hlod_linked_chain` |  | Inspect loaded hard linked-HLOD chain bounded128 distinct nodes, paginated rows1..128. |
| `inspect_world_partition_runtime_cells` |  | Page existing runtime-hash streaming cells0..1e6/count1..128 in stopped editor partition. |
| `list_world_data_layers` |  | List current-world Data Layers and their effective editor states. |
| `load_world_partition_editor_region` |  | Load user-created native region with inspected partition/adapter/count/state/label/bounds guards. |
| `move_partition_actor_data_layers` |  | Native ActorPartition move for name-dependent external actors, with whole current set/package guards. |
| `normalize_partition_runtime_hlod_indices` |  | Normalize spatial HLOD indices to array order after removal; persistent index unchanged. |
| `preview_partition_streaming_source_grid_filter` |  | Preview native source include/exclude matching against supplied grid names<=128. |
| `preview_partition_streaming_source_shapes` |  | Native authored shape transform preview with supplied grid range0..1e9/default fallback. |
| `release_unloaded_world_partition_editor_region` |  | Release unloaded user-created native partition-owned editor region with inspected identity/count/shape guard. |
| `remove_partition_runtime_hlod_setup` |  | Remove spatial HLOD setup with full ordered setup and removed reference guards. |
| `remove_partition_runtime_main_definition` |  | Remove main HashSet definition preserving at least one, full ordered path/name/HLOD impact guards. |
| `remove_partition_spatial_hash_grid` |  | Remove authored grid with full ordered count/name/index guards and preserve at least one. |
| `remove_partition_streaming_source_component` |  | Remove actor-owned source instance, excluding native/SCS/default components. |
| `remove_world_legacy_hlod_level` |  | Remove local legacy HLOD setup level with count/index/ordinary-map/override guards. |
| `rename_partition_runtime_definition` |  | Rename main runtime grid or HLOD setup with exact inspected ownership/current name guards. |
| `rename_partition_spatial_hash_grid` |  | Rename authored SpatialHash grid with exact current identity/name/count guards. |
| `reorder_partition_runtime_hlod_setups` |  | Permute spatial HLOD setups with full ordered path guards<=64; persistent setup remains last. |
| `reorder_partition_runtime_main_definitions` |  | Permute authored main definitions with full ordered identity guards; first becomes default grid. |
| `reorder_partition_spatial_hash_grids` |  | Reorder authored grids by full unique name permutation; first grid becomes default. |
| `reorder_world_legacy_hlod_levels` |  | Reorder local HLOD levels using complete unique source-index permutation<=128. |
| `replace_loaded_partition_actor_data_layers` |  | Replace whole effective membership using public native remove/add deltas; exact set guards<=64. |
| `replace_partition_runtime_hlod_layer_references` |  | Add/remove/reorder/clear HLOD setup refs through full ordered array replacement<=128. |
| `replace_partition_runtime_main_class` |  | Replace selected main with loaded concrete runtime class/native defaults; grid name retained. |
| `replace_partition_streaming_source_shapes` |  | Add/remove/reorder/clear native shapes<=64 with exact ordered fields/current enabled guards. |
| `replace_partition_streaming_source_target_grids` |  | Add/remove/reorder/clear source target grids through full ordered list<=64/current behavior guards. |
| `replace_unloaded_partition_editor_region` |  | Replace unloaded user-created region with native box shape, new identity before old release. |
| `reset_world_legacy_hlod_level` |  | Reset entire local HLOD level to native constructor defaults, full snapshot required. |
| `set_data_layer_asset_actor_filters` |  | Set standalone ordinary Data Layer actor-filter support with inspected type/current flag guards. |
| `set_data_layer_asset_debug_color` |  | Set native Data Layer debug color using exactly4 RGBA byte channels0..255. |
| `set_data_layer_asset_enum` |  | Set DataLayerType (0 Runtime/1 Editor) or runtime-only LoadFilter (0 None/1 ClientOnly/2 ServerOnly). |
| `set_hlod_builder` |  | Variants: `numeric`, `bool`, `enum`, `string`, `name`, `int64` |
| `set_hlod_builder_asset_reference` |  | Set native hard asset-reference leaf, inspected settings/type/path/current reference guards. |
| `set_hlod_cluster_volume_policy` |  | Set manual HLOD volume overlap/full tier filter with exact current guards. |
| `set_loaded_partition_actor_data_layer` |  | Add/remove already-loaded partition actor membership via native Data Layer editor subsystem. |
| `set_loaded_partition_actor_hlod_layer` |  | Assign loaded native HLOD layer or empty explicit clear, inspected actor/layer/grid identity guards. |
| `set_loaded_partition_actor_runtime_grid` |  | Set loaded partition actor runtime grid, native CanEditChange/IsValidGrid for actor class. |
| `set_loaded_partition_actor_spatial` |  | Set already-loaded partition actor authored spatial-loading flag with full identity/current raw flag guard. |
| `set_partition_actor_pin` |  | Native partition-owned actor pin/unpin with exact descriptor/current pin+loaded state guards. |
| `set_partition_actor_pins` |  | Batch1..64 native actor pin/unpin holds; entries use ContainerPath/ActorGuid/ActorPath/ |
| `set_partition_data_layer_filter_included` |  | Set per-instance default actor-filter inclusion with current flag/type/asset guards. |
| `set_partition_data_layer_initial` |  | Variants: `set_partition_data_layer_initial_runtime_state`, `set_partition_data_layer_initial_visibility` |
| `set_partition_data_layer_instance_asset` |  | Replace ordinary instance asset reference or empty clear, without migrating actor references. |
| `set_partition_data_layer_loading` |  | Set current editor Data Layer load flag with exact current state/identity guards. |
| `set_partition_data_layer_locked` |  | Set local Data Layer lock with inspected current bitfield and writable ordinary owner guards. |
| `set_partition_data_layer_parent` |  | Set registered Data Layer parent; empty parent clears to root, empty expected aliases None. |
| `set_partition_data_layer_short_name` |  | Rename editable Data Layer short name with inspected current spelling guard. |
| `set_partition_data_layer_streaming_setting` |  | Set StreamingPriority signed32 (lower=higher priority) or OverrideBlockOnSlowStreaming0..2. |
| `set_partition_data_layer_visibility` |  | Set current editor Data Layer visibility with inspected current flag/path guards. |
| `set_partition_default_hlod_layer` |  | Set native partition default HLOD reference; loaded persistent layer or empty clear. |
| `set_partition_hlod_option` |  | Set bAllowShowingHLODsInEditor or bHasStandaloneHLOD authored flag with native eligibility. |
| `set_partition_location_volume_debug_color` |  | Set authored LocationVolume debug RGBA bytes with exact color/identity/current hold guards. |
| `set_partition_location_volume_loading` |  | Native existing LocationVolume Load/Unload with exact identity/label/bounds/hold guards. |
| `set_partition_policy` |  | Set ServerStreamingMode0..3, ServerStreamingOutMode0..2 or DataLayersLogicOperator0 Or/1 And. |
| `set_partition_runtime_definition` |  | Variants: `numeric`, `bool` |
| `set_partition_runtime_definition_bounds_mode` |  | Set main bounds mode0 UseContent/1 UseCellBounds/2 UseMinContentCellBounds. |
| `set_partition_runtime_definition_debug_color` |  | Set main/HLOD runtime partition linear debug RGBA0..1, full inspected ownership/color guards. |
| `set_partition_runtime_definition_origin` |  | Set main LHGrid origin XYZ within +/-1e9 with full inspected ownership/current vector guards. |
| `set_partition_runtime_hlod_layer_reference` |  | Replace existing runtime HLOD setup reference slot with loaded persistent HLOD layer. |
| `set_partition_spatial_hash_grid_appearance` |  | Variants: `set_partition_spatial_hash_grid_blocking`, `set_partition_spatial_hash_grid_origin`, `set_partition_spatial_hash_grid_debug_color` |
| `set_partition_spatial_hash_grid_numeric` |  | Set SpatialHash CellSize1600..1e9/Priority signed32/float LoadingRange0..1e9. |
| `set_partition_spatial_hash_settings` |  | Variants: `set_partition_spatial_hash_override`, `set_partition_spatial_hash_z_culling` |
| `set_partition_streaming` |  | Native main partition streaming setter with exact current flag/identity and clean-package guards. |
| `set_partition_streaming_source_setting` |  | Variants: `set_partition_streaming_source_enabled`, `set_partition_streaming_source_enum` |
| `set_partition_streaming_source_visualization` |  | Variants: `set_partition_streaming_source_debug_color`, `set_partition_streaming_source_visualizer_range` |
| `set_private_data_layer_asset_actor_filters` |  | Set private embedded Data Layer asset actor-filter support with exact owner/type/value guards. |
| `set_private_data_layer_asset_debug_color` |  | Set private embedded editor Data Layer debug RGBA bytes0..255 with full identity/color guards. |
| `set_world_data_layer_state` |  | Change a named Data Layer's explicit editor loading or visibility state. |
| `set_world_legacy_hlod` |  | Variants: `numeric`, `boolean` |
| `set_world_legacy_hlod_material_override` |  | Set ordinary-map legacy HLOD base-material override, loaded compatible material or empty clear. |
| `set_world_legacy_hlod_method` |  | Set local HLOD method1 Merge/2 Simplify/3 Approximate with exact index/count/current guards. |
| `set_world_legacy_hlod_nested` |  | Variants: `numeric`, `boolean`, `enum`, `name`, `string`, `color` |
| `set_world_legacy_hlod_nested_int_point` |  | Edit inspected nested HLOD FIntPoint as complete XY pair0..1000000/native clamps. |
| `set_world_legacy_hlod_nested_object` |  | Edit inspected nested HLOD hard asset reference, loaded compatible assets or permitted clear. |
| `set_world_legacy_hlod_setup_override` |  | Assign loaded concrete legacy HLOD setup class override or empty clear, preserving local setup. |
| `set_world_partition_hlod_layer_class` |  | Set HLODBuilderClass/HLODActorClass/HLODModifierClass, inspected type/class/settings identity guards. |
| `set_world_partition_hlod_layer_type` |  | Set native generation type0..5 with inspected current type/settings-object identity guard. |
| `set_world_partition_hlod_linked_layer` |  | Set CustomHLODActor linked layer with inspected current type/link guard, loaded target/empty clear. |
| `set_world_partition_hlod_parent` |  | Set loaded HLOD layer parent/empty clear with inspected parent guard/prospective acyclic chain<=128. |
| `unload_world_partition_editor_region` |  | Unload user-created region with inspected partition/adapter/count/state/label/bounds guards. |
