"""Sounds, Sound Cues, MetaSounds, modulation, Quartz and dialogue."""
import httpx

from . import app
from .app import mcp, _asset_request


@mcp.tool()
def inspect_audio_asset(asset_path: str, asset_type: str = "wave") -> str:
    """Inspect supported audio assets, including Dialogue Voice and Dialogue Wave metadata."""
    routes = {
        "wave": "audio/waves/inspect",
        "sound_wave": "audio/waves/inspect",
        "cue": "sound-cues/inspect",
        "sound_cue": "sound-cues/inspect",
        "class": "sound-classes/inspect",
        "sound_class": "sound-classes/inspect",
        "mix": "sound-mixes/inspect",
        "sound_mix": "sound-mixes/inspect",
        "submix": "sound-submixes/inspect",
        "sound_submix": "sound-submixes/inspect",
        "attenuation": "audio/attenuations/inspect",
        "sound_attenuation": "audio/attenuations/inspect",
        "concurrency": "audio/concurrencies/inspect",
        "sound_concurrency": "audio/concurrencies/inspect",
        "voice": "audio/dialogue/voices/settings",
        "dialogue_voice": "audio/dialogue/voices/settings",
        "dialogue_wave": "audio/dialogue/waves/settings",
        "modulation": "audio/modulation/settings",
        "control_bus": "audio/modulation/settings",
        "control_bus_mix": "audio/modulation/settings",
        "modulation_parameter": "audio/modulation/settings",
        "modulation_patch": "audio/modulation/settings",
        "modulation_generator": "audio/modulation/settings",
        "audio_bus": "audio/modulation/settings",
    }
    route = routes.get(asset_type.lower())
    if not route:
        raise ValueError("asset_type must be wave, cue, class, mix, submix, attenuation, concurrency, voice, dialogue_wave, or modulation")
    return httpx.get(f"{app.BASE_URL}/{route}", params={"asset_path": asset_path}).text


@mcp.tool()
def inspect_sound_class_settings(asset_path: str) -> str:
    """Inspect typed Sound Class volume, pitch, routing, hierarchy, and defaults."""
    return httpx.get(f"{app.BASE_URL}/sound-classes/settings", params={"asset_path": asset_path}).text


@mcp.tool()
def edit_sound_class_settings(asset_path: str, volume: float | None = None,
                              pitch: float | None = None,
                              low_pass_filter_frequency: float | None = None,
                              attenuation_distance_scale: float | None = None,
                              lfe_bleed: float | None = None,
                              voice_center_channel_volume: float | None = None,
                              default_2d_reverb_send_amount: float | None = None,
                              always_play: bool | None = None,
                              is_ui_sound: bool | None = None,
                              is_music: bool | None = None,
                              center_channel_only: bool | None = None,
                              apply_ambient_volumes: bool | None = None,
                              reverb: bool | None = None,
                              apply_effects: bool | None = None,
                              output_target: str | None = None,
                              loading_behavior: str | None = None,
                              default_submix_path: str | None = None,
                              parent_class_path: str | None = None,
                              dry_run: bool = False, save: bool = False) -> str:
    """Edit typed Sound Class gains, routing, loading behavior, and hierarchy references."""
    body: dict = {"AssetPath": asset_path, "bDryRun": dry_run, "bSave": save}
    fields = {
        "Volume": volume, "Pitch": pitch,
        "LowPassFilterFrequency": low_pass_filter_frequency,
        "AttenuationDistanceScale": attenuation_distance_scale,
        "LFEBleed": lfe_bleed, "VoiceCenterChannelVolume": voice_center_channel_volume,
        "Default2DReverbSendAmount": default_2d_reverb_send_amount,
        "AlwaysPlay": always_play, "IsUISound": is_ui_sound, "IsMusic": is_music,
        "CenterChannelOnly": center_channel_only, "ApplyAmbientVolumes": apply_ambient_volumes,
        "Reverb": reverb, "ApplyEffects": apply_effects,
        "OutputTarget": output_target, "LoadingBehavior": loading_behavior,
    }
    for name, value in fields.items():
        if value is not None:
            body[f"bSet{name}"] = True
            body[name] = value
    if default_submix_path is not None:
        body["bSetDefaultSubmix"] = True
        body["DefaultSubmixPath"] = default_submix_path
    if parent_class_path is not None:
        body["bSetParentClass"] = True
        body["ParentClassPath"] = parent_class_path
    return httpx.patch(f"{app.BASE_URL}/sound-classes/settings", json=body).text


@mcp.tool()
def validate_sound_class(asset_path: str) -> str:
    """Validate Sound Class numeric settings and parent/child hierarchy consistency."""
    return httpx.post(f"{app.BASE_URL}/sound-classes/validate", json={"AssetPath": asset_path}).text


@mcp.tool()
def inspect_sound_mix_settings(asset_path: str) -> str:
    """Inspect Sound Mix timing, four EQ bands, and Sound Class adjusters."""
    return httpx.get(f"{app.BASE_URL}/sound-mixes/settings", params={"asset_path": asset_path}).text


@mcp.tool()
def edit_sound_mix_settings(asset_path: str, initial_delay: float | None = None,
                            fade_in_time: float | None = None,
                            duration: float | None = None,
                            fade_out_time: float | None = None,
                            apply_eq: bool | None = None,
                            eq_priority: float | None = None,
                            eq_band_edits: list[dict] | None = None,
                            dry_run: bool = False, save: bool = False) -> str:
    """Edit Sound Mix timing and individual EQ band frequency, gain, and bandwidth values."""
    body: dict = {"AssetPath": asset_path, "bDryRun": dry_run, "bSave": save}
    fields = {
        "InitialDelay": initial_delay, "FadeInTime": fade_in_time,
        "Duration": duration, "FadeOutTime": fade_out_time,
        "ApplyEQ": apply_eq, "EQPriority": eq_priority,
    }
    for name, value in fields.items():
        if value is not None:
            body[f"bSet{name}"] = True
            body[name] = value
    if eq_band_edits is not None:
        body["EQBandEdits"] = []
        for band in eq_band_edits:
            item = {"BandIndex": band["band_index"]}
            for source, target in (("frequency_center", "FrequencyCenter"),
                                   ("gain", "Gain"), ("bandwidth", "Bandwidth")):
                if source in band:
                    item[f"bSet{target}"] = True
                    item[target] = band[source]
            body["EQBandEdits"].append(item)
    return httpx.patch(f"{app.BASE_URL}/sound-mixes/settings", json=body).text


@mcp.tool()
def edit_sound_mix_adjuster(asset_path: str, operation: str,
                            sound_class_path: str,
                            volume_adjuster: float | None = None,
                            pitch_adjuster: float | None = None,
                            low_pass_filter_frequency: float | None = None,
                            voice_center_channel_volume_adjuster: float | None = None,
                            apply_to_children: bool | None = None,
                            confirm_remove: bool = False,
                            dry_run: bool = False, save: bool = False) -> str:
    """Upsert or confirmed-remove a Sound Class adjuster on a Sound Mix."""
    body: dict = {"AssetPath": asset_path, "Operation": operation,
                  "SoundClassPath": sound_class_path, "bDryRun": dry_run,
                  "bConfirm": confirm_remove, "bSave": save}
    fields = {
        "VolumeAdjuster": volume_adjuster, "PitchAdjuster": pitch_adjuster,
        "LowPassFilterFrequency": low_pass_filter_frequency,
        "VoiceCenterChannelVolumeAdjuster": voice_center_channel_volume_adjuster,
        "ApplyToChildren": apply_to_children,
    }
    for name, value in fields.items():
        if value is not None:
            body[f"bSet{name}"] = True
            body[name] = value
    return httpx.post(f"{app.BASE_URL}/sound-mixes/adjusters", json=body).text


@mcp.tool()
def validate_sound_mix(asset_path: str) -> str:
    """Validate Sound Mix timing, EQ bands, class adjusters, and passive activation loops."""
    return httpx.post(f"{app.BASE_URL}/sound-mixes/validate", json={"AssetPath": asset_path}).text


@mcp.tool()
def inspect_sound_submix_settings(asset_path: str) -> str:
    """Inspect Sound Submix hierarchy, level, auto-disable, envelope, and effects settings."""
    return httpx.get(f"{app.BASE_URL}/sound-submixes/settings", params={"asset_path": asset_path}).text


@mcp.tool()
def edit_sound_submix_settings(asset_path: str, parent_submix_path: str | None = None,
                               auto_disable: bool | None = None,
                               auto_disable_time: float | None = None,
                               mute_when_backgrounded: bool | None = None,
                               envelope_follower_attack_time: int | None = None,
                               envelope_follower_release_time: int | None = None,
                               output_volume_db: float | None = None,
                               wet_level_db: float | None = None,
                               dry_level_db: float | None = None,
                               dry_run: bool = False, save: bool = False) -> str:
    """Edit Sound Submix parent, auto-disable, envelope-following, and level settings."""
    body: dict = {"AssetPath": asset_path, "bDryRun": dry_run, "bSave": save}
    fields = {
        "ParentSubmix": ("ParentSubmixPath", parent_submix_path),
        "AutoDisable": ("AutoDisable", auto_disable),
        "AutoDisableTime": ("AutoDisableTime", auto_disable_time),
        "MuteWhenBackgrounded": ("MuteWhenBackgrounded", mute_when_backgrounded),
        "EnvelopeFollowerAttackTime": ("EnvelopeFollowerAttackTime", envelope_follower_attack_time),
        "EnvelopeFollowerReleaseTime": ("EnvelopeFollowerReleaseTime", envelope_follower_release_time),
        "OutputVolumeDb": ("OutputVolumeDb", output_volume_db),
        "WetLevelDb": ("WetLevelDb", wet_level_db),
        "DryLevelDb": ("DryLevelDb", dry_level_db),
    }
    for flag, (name, value) in fields.items():
        if value is not None:
            body[f"bSet{flag}"] = True
            body[name] = value
    return httpx.patch(f"{app.BASE_URL}/sound-submixes/settings", json=body).text


@mcp.tool()
def edit_sound_submix_effect(asset_path: str, operation: str, effect_path: str,
                             confirm_remove: bool = False,
                             dry_run: bool = False, save: bool = False) -> str:
    """Add a Sound Effect Submix Preset to the chain or remove it with confirmation."""
    return httpx.post(f"{app.BASE_URL}/sound-submixes/effects", json={
        "AssetPath": asset_path, "Operation": operation, "EffectPath": effect_path,
        "bConfirm": confirm_remove, "bDryRun": dry_run, "bSave": save,
    }).text


@mcp.tool()
def validate_sound_submix(asset_path: str) -> str:
    """Validate Sound Submix level, parent hierarchy, envelope settings, and effect chain."""
    return httpx.post(f"{app.BASE_URL}/sound-submixes/validate", json={"AssetPath": asset_path}).text


@mcp.tool()
def create_sound_attenuation(asset_path: str, save: bool = False,
                             dry_run: bool = False) -> str:
    """Create a Sound Attenuation asset for audio sections, sounds, or cues."""
    return httpx.post(f"{app.BASE_URL}/audio/attenuations/create", json={
        "AssetPath": asset_path, "bSave": save, "bDryRun": dry_run
    }).text


@mcp.tool()
def inspect_sound_attenuation_settings(asset_path: str) -> str:
    """Inspect attenuation numeric settings, flags, enum choices, shape extents, and custom curves."""
    return httpx.get(f"{app.BASE_URL}/audio/attenuations/settings", params={"asset_path": asset_path}).text


@mcp.tool()
def edit_sound_attenuation_settings(asset_path: str,
                                    numeric_settings: dict[str, float] | None = None,
                                    flags: dict[str, bool] | None = None,
                                    enum_settings: dict[str, str] | None = None,
                                    shape_extents: dict | None = None,
                                    audio_link_settings_path: str | None = None,
                                    dry_run: bool = False, save: bool = False) -> str:
    """Edit named attenuation controls from inspection; validate ranges before mutation.

    Numeric names include falloff_distance, air_absorption_distance_min/max,
    occlusion_lowpass_frequency, and manual_reverb_send_level. Flags include
    attenuate, spatialize, air_absorption, listener_focus, occlusion, reverb_send,
    and priority_attenuation. Enum names and supported choices come from inspection.
    Shape extents use x/y/z; interpretation depends on sphere/capsule/box/cone.
    """
    body = {"AssetPath": asset_path, "NumericSettings": numeric_settings or {},
            "Flags": flags or {}, "EnumSettings": enum_settings or {},
            "bDryRun": dry_run, "bSave": save}
    if shape_extents is not None:
        body["bSetShapeExtents"] = True
        body["ShapeExtents"] = shape_extents
    if audio_link_settings_path is not None:
        body["bSetAudioLinkSettings"] = True
        body["AudioLinkSettingsPath"] = audio_link_settings_path
    return httpx.patch(f"{app.BASE_URL}/audio/attenuations/settings", json=body).text


@mcp.tool()
def edit_sound_attenuation_curve(asset_path: str, curve_name: str, operation: str,
                                 keys: list[dict] | None = None,
                                 curve_path: str = "", confirm_replace: bool = False,
                                 dry_run: bool = False, save: bool = False) -> str:
    """Set external or replace/clear inline attenuation, absorption, reverb, or priority curves.

    Operations: set_external, replace_inline, clear. Existing data replacement
    requires confirmation. Keys use time/value with optional interpolation
    Linear, Constant, or Cubic; curve input times are normalized to 0 through 1.
    """
    body = {"AssetPath": asset_path, "CurveName": curve_name, "Operation": operation,
            "CurvePath": curve_path, "bConfirm": confirm_replace,
            "bDryRun": dry_run, "bSave": save}
    if keys is not None:
        body["Keys"] = [{"Time": key["time"], "Value": key["value"],
                         "Interpolation": key.get("interpolation", "Linear")} for key in keys]
    return httpx.post(f"{app.BASE_URL}/audio/attenuations/curves", json=body).text


@mcp.tool()
def validate_sound_attenuation(asset_path: str) -> str:
    """Validate attenuation shape geometry, numeric ranges, enum values, and custom curves."""
    return httpx.post(f"{app.BASE_URL}/audio/attenuations/validate", json={"AssetPath": asset_path}).text


@mcp.tool()
def evaluate_sound_attenuation(asset_path: str, locations: list[dict],
                                origin: dict | None = None, rotation: dict | None = None,
                                distance_scale: float = 1.0) -> str:
    """Sample native distance-volume attenuation at up to 256 world-space x/y/z points.

    Origin defaults to zero and rotation uses pitch/yaw/roll. This evaluates the
    distance volume curve and shape; it does not trace occlusion or simulate audio.
    """
    body = {"AssetPath": asset_path, "Locations": locations, "DistanceScale": distance_scale}
    if origin is not None:
        body["Origin"] = origin
    if rotation is not None:
        body["Rotation"] = rotation
    return httpx.post(f"{app.BASE_URL}/audio/attenuations/evaluate", json=body).text


@mcp.tool()
def edit_attenuation_submix_send(asset_path: str, operation: str,
                                 submix_path: str = "", control_method: str | None = None,
                                 send_level: float | None = None,
                                 disable_manual_send_clamp: bool | None = None,
                                 min_send_level: float | None = None,
                                 max_send_level: float | None = None,
                                 min_send_distance: float | None = None,
                                 max_send_distance: float | None = None,
                                 external_curve_path: str | None = None,
                                 curve_keys: list[dict] | None = None,
                                 confirm_remove_or_replace: bool = False,
                                 dry_run: bool = False, save: bool = False) -> str:
    """Upsert/remove/clear attenuation submix sends with Manual, Linear, or CustomCurve control.

    Removal, clearing, and replacement of existing curve data require confirmation.
    Set the attenuation submix_sends flag to enable routing. Curve keys have
    normalized time/value and optional Linear, Constant, or Cubic interpolation.
    """
    body = {"AssetPath": asset_path, "Operation": operation, "SubmixPath": submix_path,
            "bConfirm": confirm_remove_or_replace, "bDryRun": dry_run, "bSave": save}
    if control_method is not None:
        body["ControlMethod"] = control_method
    for name, value in (("SendLevel", send_level), ("MinSendLevel", min_send_level),
                        ("MaxSendLevel", max_send_level), ("MinSendDistance", min_send_distance),
                        ("MaxSendDistance", max_send_distance)):
        if value is not None:
            body[f"bSet{name}"] = True
            body[name] = value
    if disable_manual_send_clamp is not None:
        body["bSetDisableManualSendClamp"] = True
        body["bDisableManualSendClamp"] = disable_manual_send_clamp
    if external_curve_path is not None:
        body["bSetExternalCurve"] = True
        body["CurvePath"] = external_curve_path
    if curve_keys is not None:
        body["bSetCurveKeys"] = True
        body["Keys"] = [{"Time": key["time"], "Value": key["value"],
                         "Interpolation": key.get("interpolation", "Linear")} for key in curve_keys]
    return httpx.post(f"{app.BASE_URL}/audio/attenuations/submix-sends", json=body).text


@mcp.tool()
def list_audio_plugin_settings_classes() -> str:
    """List loaded concrete spatialization, occlusion, reverb, and source-override settings classes."""
    return httpx.get(f"{app.BASE_URL}/audio/plugin-settings/classes").text


@mcp.tool()
def create_audio_plugin_settings(asset_path: str, settings_class: str,
                                 dry_run: bool = False, save: bool = False) -> str:
    """Create a default plugin source settings asset from a compatible concrete loaded class."""
    return httpx.post(f"{app.BASE_URL}/audio/plugin-settings/create", json={
        "AssetPath": asset_path, "SettingsClass": settings_class,
        "bDryRun": dry_run, "bSave": save,
    }).text


@mcp.tool()
def edit_attenuation_plugin_reference(asset_path: str, operation: str,
                                      plugin_type: str, settings_path: str = "",
                                      confirm_remove: bool = False,
                                      dry_run: bool = False, save: bool = False) -> str:
    """Add/remove/clear compatible attenuation plugin settings references without editing the referenced asset.

    Plugin types: spatialization, occlusion, reverb, source_data_override.
    Remove and clear require confirmation; plugin parameters use shared asset property tools.
    """
    return httpx.post(f"{app.BASE_URL}/audio/attenuations/plugins", json={
        "AssetPath": asset_path, "Operation": operation, "PluginType": plugin_type,
        "SettingsPath": settings_path, "bConfirm": confirm_remove,
        "bDryRun": dry_run, "bSave": save,
    }).text


@mcp.tool()
def create_modulation_asset(asset_path: str, asset_type: str = "bus", parameter_type: str = "scalar",
                            parameter_path: str = "", dry_run: bool = False, save: bool = False,
                            generator_type: str = "lfo") -> str:
    """Create a parameter, Control Bus, mix, patch, generator or Audio Bus modulation asset.

    Parameter types: scalar/scaled/frequency/filter_frequency/volume/bipolar/additive.
    Generator types: lfo/ad_envelope/envelope_follower. Patches start as bypassed drafts.
    A bus may reference a parameter; omission uses the native configured Volume parameter.
    """
    return httpx.post(f"{app.BASE_URL}/audio/modulation/create", json={
        "AssetPath": asset_path, "AssetType": asset_type, "ParameterType": parameter_type,
        "ParameterPath": parameter_path, "GeneratorType": generator_type, "bDryRun": dry_run, "bSave": save,
    }).text


@mcp.tool()
def inspect_modulation_asset(asset_path: str) -> str:
    """Inspect parameter domains, buses, mix stages, generator parameters, or patch inputs/transforms."""
    return httpx.get(f"{app.BASE_URL}/audio/modulation/settings", params={"asset_path": asset_path}).text


@mcp.tool()
def edit_modulation_settings(asset_path: str, numeric: dict[str, float] | None = None,
                             unit_display_name: str | None = None, parameter_path: str | None = None,
                             bypass: bool | None = None, override_address: bool | None = None,
                             address: str = "", generator_paths: list[str] | None = None,
                             retrigger_on_activation: bool | None = None, confirm: bool = False,
                             dry_run: bool = False, save: bool = False) -> str:
    """Edit typed modulation settings with preflight validation.

    Parameter numeric keys: DefaultNormalized and class-specific UnitMin/UnitMax/UnitRange/MinVolume.
    Mix numeric key: DurationSeconds (-1 means manual deactivation). Audio Bus numeric key: Channels (1/2/4/6/8).
    Patch settings support parameter_path and bypass. Empty parameter path clears a bus or patch link.
    Removing generator references requires confirm; address applies when override_address is supplied.
    """
    body = {"AssetPath": asset_path, "Numeric": numeric or {}, "bConfirm": confirm,
            "bDryRun": dry_run, "bSave": save}
    for value, flag, key in [
        (unit_display_name, "bSetUnitDisplayName", "UnitDisplayName"),
        (parameter_path, "bSetParameter", "ParameterPath"), (bypass, "bSetBypass", "bBypass"),
        (generator_paths, "bSetGenerators", "GeneratorPaths"),
        (retrigger_on_activation, "bSetRetriggerOnActivation", "bRetriggerOnActivation"),
    ]:
        if value is not None:
            body[flag], body[key] = True, value
    if override_address is not None:
        body.update(bSetAddress=True, bOverrideAddress=override_address, Address=address)
    return httpx.patch(f"{app.BASE_URL}/audio/modulation/settings", json=body).text


@mcp.tool()
def edit_control_bus_mix_stage(asset_path: str, operation: str = "upsert", bus_path: str = "",
                               target_normalized: float = 1.0, attack_seconds: float = .1,
                               release_seconds: float = .1, confirm: bool = False,
                               dry_run: bool = False, save: bool = False) -> str:
    """Upsert, remove or clear native Control Bus Mix stages; removal requires confirmation."""
    return httpx.post(f"{app.BASE_URL}/audio/modulation/stages", json={
        "AssetPath": asset_path, "Operation": operation, "BusPath": bus_path,
        "TargetNormalized": target_normalized, "AttackSeconds": attack_seconds,
        "ReleaseSeconds": release_seconds, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save,
    }).text


@mcp.tool()
def convert_modulation_parameter_values(asset_path: str, values: list[float],
                                        direction: str = "normalized_to_unit") -> str:
    """Apply native parameter conversion to 1-256 values; direction normalized_to_unit or unit_to_normalized."""
    return httpx.post(f"{app.BASE_URL}/audio/modulation/convert", json={
        "AssetPath": asset_path, "Values": values, "Direction": direction,
    }).text


@mcp.tool()
def validate_modulation_asset(asset_path: str) -> str:
    """Validate parameter domains, Control Bus references and Control Bus Mix stage targets/timing."""
    return httpx.post(f"{app.BASE_URL}/audio/modulation/validate", json={"AssetPath": asset_path}).text


@mcp.tool()
def inspect_control_bus_mix_profile(asset_path: str, profile_index: int = 0) -> str:
    """Inspect native on-disk mix profile stage targets/attack/release without changing assets."""
    return httpx.get(f"{app.BASE_URL}/audio/modulation/profiles", params={
        "asset_path": asset_path, "profile_index": profile_index,
    }).text


@mcp.tool()
def control_control_bus_mix_profile(asset_path: str, operation: str, profile_index: int = 0,
                                     pie_instance: int = -1, confirm: bool = False,
                                     dry_run: bool = False, save: bool = False) -> str:
    """Save/load a native mix profile. Indices 0-999; overwrite/load replacement require confirmation.

    Native save captures active proxy state or inactive asset state asynchronously; inspect the file to
    verify completion. Load validates the disk snapshot and replaces asset stages in a transaction;
    save optionally saves the changed mix asset. Native profiles omit duration and retrigger settings.
    Auto context uses PIE when active, otherwise the editor's main audio device. Stop PIE before
    saving changed asset stages; runtime-only/no-op profile loads preserve clean asset state.
    """
    return httpx.post(f"{app.BASE_URL}/audio/modulation/profiles", json={
        "AssetPath": asset_path, "Operation": operation, "ProfileIndex": profile_index,
        "PIEInstance": pie_instance, "bConfirm": confirm, "bDryRun": dry_run, "bSave": save,
    }).text


@mcp.tool()
def inspect_modulation_runtime(asset_path: str = "", pie_instance: int | None = None) -> str:
    """Inspect native PIE modulation mix activity/values and adapter-owned destination handles.

    Values are sampled from the last native processing tick; inactive modulators return native fallback 1.
    The destinations list includes only handles created through these tools.
    """
    params = {"asset_path": asset_path}
    if pie_instance is not None:
        params["pie_instance"] = pie_instance
    return httpx.get(f"{app.BASE_URL}/audio/modulation/runtime", params=params).text


@mcp.tool()
def control_audio_trace(capture_id: str, operation: str = "start", pie_instance: int = -1,
                         channels: list[str] | None = None, duration_seconds: float = 5.0,
                         max_file_mb: int = 64, dry_run: bool = False) -> str:
    """Capture native process-wide audio profiling to a project Saved/Profiling/UE5MCP .utrace file.

    Operations start/stop/release. Start requires PIE; duration [0.1,60], soft size threshold [1,256] MB.
    Channels: audio/audiomixer/cpu/frame/bookmark; defaults select all five. Discover available channels
    with inspect_audio_trace. Existing native connections and existing output files are rejected.
    Connection identity is checked before stopping. Newly enabled channels are restored on normal completion.
    Poll state through stopping until completed. Native buffering can overshoot the soft size threshold.
    release drops completed metadata while keeping the file; open it in Unreal Insights for analysis.
    """
    return httpx.post(f"{app.BASE_URL}/audio/profiling/traces", json={
        "CaptureId": capture_id, "Operation": operation, "PIEInstance": pie_instance,
        "Channels": channels or [], "DurationSeconds": duration_seconds,
        "MaxFileMB": max_file_mb, "bDryRun": dry_run}).text


@mcp.tool()
def inspect_audio_trace(capture_id: str = "") -> str:
    """Inspect native trace connection/channel capabilities and optional owned capture metadata/file size."""
    return httpx.get(f"{app.BASE_URL}/audio/profiling/traces", params={"capture_id": capture_id}).text


@mcp.tool()
def control_audio_diagnostic_capture(capture_id: str, operation: str = "capture", pie_instance: int = -1,
                                      limit: int = 128, dry_run: bool = False) -> str:
    """Queue or release a native audio-thread diagnostic snapshot in PIE.

    Captures logical active sounds for the selected world, plus device-wide logical count and
    audio-thread device configuration. This does not capture virtual-loop lists, hardware voices,
    CPU/DSP timing or PCM. limit bounds retained rows [1,512]; counts cover the full native list.
    Up to 16 retained captures per world and 128 global retained/pending entries. Poll for ready.
    release/world cleanup removes the capture; pending native work retires safely without cancellation.
    """
    return httpx.post(f"{app.BASE_URL}/audio/diagnostics/captures", json={
        "CaptureId": capture_id, "Operation": operation, "PIEInstance": pie_instance,
        "Limit": limit, "bDryRun": dry_run}).text


@mcp.tool()
def inspect_audio_diagnostic_capture(capture_id: str, pie_instance: int | None = None) -> str:
    """Poll native captured sound state. Weak object paths resolve on the game thread after capture.

    Playback/settings/flags and capture timestamps stay frozen; paths may become empty after deletion.
    """
    params = {"capture_id": capture_id}
    if pie_instance is not None:
        params["pie_instance"] = pie_instance
    return httpx.get(f"{app.BASE_URL}/audio/diagnostics/captures", params=params).text


@mcp.tool()
def control_modulation_recording(recording_id: str, operation: str = "start", asset_path: str = "",
                                 pie_instance: int = -1, interval_seconds: float = .05,
                                 duration_seconds: float = 2.0, dry_run: bool = False) -> str:
    """Record real native PIE destination values; operations start/stop/release.

    Owns a native destination until stopped/completed, then retains its samples until release/PIE teardown.
    Supports buses/generators/patches; envelope followers require an assigned Audio Bus with real input.
    Interval [0.01,1], duration [0.02,60], at most 1024 requested samples and 16 recordings per world.
    Reads latest modulation-tick values on the core game-thread ticker; skips are not synthesized.
    This does not provide sample-accurate PCM or cooked envelope data. Initial native fallback can be 1.
    Asset/bus paths describe the configured source at recording start.
    """
    return httpx.post(f"{app.BASE_URL}/audio/modulation/recordings", json={
        "RecordingId": recording_id, "Operation": operation, "AssetPath": asset_path,
        "PIEInstance": pie_instance, "IntervalSeconds": interval_seconds,
        "DurationSeconds": duration_seconds, "bDryRun": dry_run}).text


@mcp.tool()
def inspect_modulation_recording(recording_id: str, pie_instance: int | None = None,
                                 after_sequence: int = 0, limit: int = 128) -> str:
    """Poll bounded native modulation readings with sequence cursor and monotonic receipt times."""
    params = {"recording_id": recording_id, "after_sequence": after_sequence, "limit": limit}
    if pie_instance is not None:
        params["pie_instance"] = pie_instance
    return httpx.get(f"{app.BASE_URL}/audio/modulation/recordings", params=params).text


@mcp.tool()
def control_modulation_runtime(operation: str, asset_path: str = "", destination_id: str = "",
                                pie_instance: int = -1, stages: list[dict] | None = None,
                                target_normalized: float = 1.0, fade_seconds: float = -1.0,
                                duration_seconds: float = -1.0, retrigger_on_activation: bool = False,
                                dry_run: bool = False, asset_paths: list[str] | None = None,
                                address_filter: str = "", parameter_class_filter: str = "",
                                parameter_filter_path: str = "") -> str:
    """Control native PIE modulation without editing saved assets.

    Operations: create_destination/set_destination/clear_destination/release_destination,
    activate_mix/deactivate_mix/update_mix/update_mix_from_asset/update_modulator/set_global/clear_global.
    update_mix_by_filter uses native address-pattern matching and optional exact parameter class/asset
    filters against runtime proxy state. Empty address matches all; no matched-count readback is available.
    Matching follows UE PartsMatch semantics, including prefix matches. UE 5.7 terminal brace alternatives
    may match nothing; use character classes such as [AB] for single-character alternatives.
    Batch operations activate_mixes/deactivate_mixes/update_mixes_from_assets/update_modulators/
    set_globals/clear_globals use 1-128 unique asset_paths and no singular asset_path. set_globals applies
    one shared target value. All inputs are validated before independent asynchronous commands queue.
    clear_all_globals/deactivate_all_mixes affect all native mixes/globals on the selected PIE audio
    device, including those not created through this adapter.
    update_mix Stages use BusPath/TargetNormalized; buses must be unique members of the mix asset.
    Destinations hold modulators active and release on PIE teardown. Commands process asynchronously.
    """
    return httpx.post(f"{app.BASE_URL}/audio/modulation/runtime", json={
        "Operation": operation, "AssetPath": asset_path, "DestinationId": destination_id,
        "PIEInstance": pie_instance, "Stages": stages or [], "TargetNormalized": target_normalized,
        "FadeSeconds": fade_seconds, "DurationSeconds": duration_seconds,
        "bRetriggerOnActivation": retrigger_on_activation, "bDryRun": dry_run,
        "AssetPaths": asset_paths or [], "AddressFilter": address_filter,
        "ParameterClassFilter": parameter_class_filter, "ParameterFilterPath": parameter_filter_path,
    }).text


@mcp.tool()
def edit_modulation_generator(asset_path: str, numeric: dict[str, float] | None = None,
                               flags: dict[str, bool] | None = None, shape: str = "",
                               audio_bus_path: str | None = None, dry_run: bool = False,
                               save: bool = False) -> str:
    """Edit LFO, AD envelope or envelope follower settings using native Params field names.

    LFO numeric: Amplitude/Frequency/Offset/Phase/Width/ExponentialFactor; Shape is a native enum name.
    AD envelope: AttackTime/DecayTime/AttackCurve/DecayCurve. Follower: Gain/AttackTime/ReleaseTime.
    Flags: bBypass, bLooping (LFO/AD), bInvert (follower). Follower Audio Bus may be set or cleared.
    """
    body = {"AssetPath": asset_path, "Numeric": numeric or {}, "Flags": flags or {},
            "Shape": shape, "bDryRun": dry_run, "bSave": save}
    if audio_bus_path is not None:
        body.update(bSetAudioBus=True, AudioBusPath=audio_bus_path)
    return httpx.patch(f"{app.BASE_URL}/audio/modulation/generators/settings", json=body).text


@mcp.tool()
def edit_modulation_patch_input(asset_path: str, bus_path: str = "", operation: str = "upsert",
                                 sample_and_hold: bool = False, curve: str = "Linear", scalar: float = 2.5,
                                 curve_path: str = "", keys: list[dict] | None = None,
                                 confirm: bool = False, dry_run: bool = False, save: bool = False) -> str:
    """Upsert/remove/clear patch inputs, selected by Control Bus. Removal requires confirmation.

    Curves: Linear/Linear_Inv/Exp/Exp_Inverse/Log/Sin/Sin_Full/SCurve/Shared/Custom.
    Shared requires a Curve Float path; Custom requires 2-256 increasing normalized Time/Value keys,
    with Interpolation Linear/Constant/Cubic. Upsert supplies the complete input transform.
    """
    return httpx.post(f"{app.BASE_URL}/audio/modulation/inputs", json={
        "AssetPath": asset_path, "BusPath": bus_path, "Operation": operation,
        "bSampleAndHold": sample_and_hold, "Curve": curve, "Scalar": scalar,
        "CurvePath": curve_path, "Keys": keys or [], "bConfirm": confirm,
        "bDryRun": dry_run, "bSave": save,
    }).text


@mcp.tool()
def import_modulation_file_transform(asset_path: str, bus_path: str, source_file_path: str = "",
                                      operation: str = "import", channel_index: int = 0,
                                      resolution: int = 256, bit_depth: str = "IEEE_Float",
                                      phase: float = 0.0, top: float = 0.0, tail: float = 0.0,
                                      fade_in: float = 0.0, fade_out: float = 0.0,
                                      normalize: bool = True, remove_offset: bool = True,
                                      use_stored_settings: bool = True, confirm: bool = False,
                                      dry_run: bool = False, save: bool = False) -> str:
    """Import/reimport a native file-backed patch input transform using a local Sound Factory format.

    Channel wraps by native source channel count. Resolution is a power of two from 16-4096;
    bit depth is IEEE_Float or PCM_16. Reimport defaults to stored source path and edit settings.
    Replacement/reimport requires confirmation. Native fade-out boundaries may be adjusted slightly;
    effective_fade_out reports the stored native setting. Preflight decodes/processes during dry-run.
    Playback uses an owned native Shared CurveFloat baked from the processed table; the complete
    file transform/source samples remain cached in editor metadata for reimport and inspection.
    """
    return httpx.post(f"{app.BASE_URL}/audio/modulation/inputs/import", json={
        "AssetPath": asset_path, "BusPath": bus_path, "SourceFilePath": source_file_path,
        "Operation": operation, "ChannelIndex": channel_index, "Resolution": resolution,
        "BitDepth": bit_depth, "Phase": phase, "Top": top, "Tail": tail,
        "FadeIn": fade_in, "FadeOut": fade_out, "bNormalize": normalize,
        "bRemoveOffset": remove_offset, "bUseStoredSettings": use_stored_settings,
        "bConfirm": confirm, "bDryRun": dry_run, "bSave": save,
    }).text


@mcp.tool()
def sample_modulation_asset(asset_path: str, bus_path: str = "", values: list[float] | None = None,
                             samples: int = 32, step_seconds: float = .01) -> str:
    """Sample a fresh native LFO/AD instance or a patch input transform. Read-only; no live playback state.

    Generator sampling uses Samples/StepSeconds (up to 512 steps and 60 seconds total).
    Patch sampling uses bus_path and 1-256 normalized values; excludes patch mixing, output conversion
    and sample-and-hold state. Envelope follower sampling requires a live audio device and is unavailable here.
    """
    return httpx.post(f"{app.BASE_URL}/audio/modulation/sample", json={
        "AssetPath": asset_path, "BusPath": bus_path, "Values": values or [],
        "Samples": samples, "StepSeconds": step_seconds,
    }).text


@mcp.tool()
def inspect_quartz_clock(clock_name: str, pie_instance: int | None = None) -> str:
    """Inspect a native runtime Quartz clock in PIE, including tempo, transport and musical durations."""
    params = {"clock_name": clock_name}
    if pie_instance is not None:
        params["pie_instance"] = pie_instance
    return httpx.get(f"{app.BASE_URL}/audio/quartz/clock", params=params).text


@mcp.tool()
def control_quartz_clock(clock_name: str, operation: str = "create",
                         beats_per_minute: float = 120.0, beats_per_bar: int = 4,
                         beat_denominator: int = 4, pie_instance: int = -1,
                         use_audio_engine_clock_manager: bool = True,
                         ignore_level_change: bool = False, cancel_pending_events: bool = True,
                         confirm: bool = False, dry_run: bool = False,
                         pulse_overrides: list[dict] | None = None) -> str:
    """Create or control a PIE Quartz clock. Operations: create/time_signature/tempo/start/pause/resume/stop/reset/delete.

    Create sets time signature and tempo; tempo changes BPM on the next native tick.
    Audio engine manager defaults true; false uses the native subsystem clock manager.
    Clock state is runtime only. Inspect after queuing to observe completion. Deletion requires confirm.
    PulseOverrides use NumberOfPulses/PulseDuration native note enum names; their duration must span
    exactly one bar. time_signature resets transport and replaces pulse overrides (empty clears them).
    The settings response reports the request; UE exposes no native time-signature getter.
    """
    return httpx.post(f"{app.BASE_URL}/audio/quartz/control", json={
        "ClockName": clock_name, "Operation": operation, "BeatsPerMinute": beats_per_minute,
        "BeatsPerBar": beats_per_bar, "BeatDenominator": beat_denominator,
        "PIEInstance": pie_instance, "bUseAudioEngineClockManager": use_audio_engine_clock_manager,
        "bIgnoreLevelChange": ignore_level_change, "bCancelPendingEvents": cancel_pending_events,
        "bConfirm": confirm, "bDryRun": dry_run,
        "PulseOverrides": pulse_overrides or [],
    }).text


@mcp.tool()
def inspect_audio_component_settings(bp_path: str = "", component_name: str = "", actor_path: str = "") -> str:
    """Inspect an SCS/native default-subobject template or placed editor Audio Component; specify one target path.

    Inherited inspection reports the defining Blueprint and local override state without creating an override.
    """
    return httpx.get(f"{app.BASE_URL}/audio/components/settings", params={
        "bp_path": bp_path, "component_name": component_name, "actor_path": actor_path}).text


@mcp.tool()
def edit_audio_component_settings(bp_path: str = "", component_name: str = "",
                                  numeric_settings: dict | None = None, bool_settings: dict | None = None,
                                  references: dict | None = None, concurrency_paths: list[str] | None = None,
                                  dry_run: bool = False, save: bool = False, actor_path: str = "",
                                  reset_inherited_override: bool = False) -> str:
    """Edit persistent Audio Component settings with validation and transaction; compile template changes.

    Numeric: VolumeMultiplier [0,4], PitchMultiplier [0.125,4], LowPassFilterFrequency/
    HighPassFilterFrequency [0,20000], Priority [0,1000], SubtitlePriority [0,1000000].
    Boolean keys use native names: bAutoActivate, bAutoDestroy, bStopWhenOwnerDestroyed,
    bAllowSpatialization, bIsUISound, bEnableLowPassFilter, bEnableHighPassFilter, bOverridePriority,
    bOverrideSubtitlePriority, bCanPlayMultipleInstances.
    References: Sound, AttenuationSettings, SoundClassOverride; empty path clears a reference.
    concurrency_paths replaces the native set (empty list clears); omitted preserves it.
    Specify exactly one of bp_path (SCS/native default-subobject template) or actor_path (placed editor instance).
    Inherited edits create native child overrides; inspection/dry-run/no-op do not create overrides.
    reset_inherited_override removes SCS overrides or resets supported native-subobject settings to
    their immediate parent archetype; omit other settings. Native subobjects must belong to the selected
    Blueprint's CDO; native class defaults are never targets. has_local_override for native subobjects
    compares supported audio settings against their parent. Create/attach components with existing
    Blueprint/scene tools. Actor instances can be edited independently of their Blueprint defaults.
    save writes the Blueprint or actor's map/external package (including other dirty data in that package).
    Save new maps/actors with world save first. Stop PIE before real edits/saves. dry_run never mutates.
    """
    return httpx.patch(f"{app.BASE_URL}/audio/components/settings", json={
        "BpPath": bp_path, "ActorPath": actor_path, "ComponentName": component_name, "NumericSettings": numeric_settings or {},
        "BoolSettings": bool_settings or {}, "References": references or {},
        "bSetConcurrency": concurrency_paths is not None, "ConcurrencyPaths": concurrency_paths or [],
        "bResetInheritedOverride": reset_inherited_override,
        "bDryRun": dry_run, "bSave": save}).text


@mcp.tool()
def control_quartz_events(event_id: str, operation: str, clock_name: str = "", pie_instance: int = -1,
                           quantization: str = "Bar", multiplier: float = 1.0,
                           reference_point: str = "TransportRelative", beats_per_minute: float = 120.0,
                           other_clock_name: str = "", fire_on_clock_start: bool = True,
                           cancel_if_not_running: bool = False, resume_on_queued: bool = False,
                           dry_run: bool = False, sound_path: str = "", start_time: float = 0.0,
                           volume_multiplier: float = 1.0, pitch_multiplier: float = 1.0,
                           fade_in_duration: float = 0.0, spatialized: bool = False,
                           location: dict | None = None, rotation: dict | None = None,
                           attach_component_path: str = "", attach_socket: str = "",
                           attenuation_path: str = "", concurrency_path: str = "",
                           audio_bus_sends: list[dict] | None = None) -> str:
    """Subscribe to Quartz metronome events or schedule native tempo/reset/notify/start_other commands.

    Operations: subscribe/unsubscribe/tempo/reset/notify/start_other/cancel/release,
    play_sound/stop_sound/pause_sound/resume_sound/move_sound/set_audio_bus_sends. play_sound requires a native SoundBase asset and
    audio engine clock; owns a transient PIE Audio Component. location {X,Y,Z} in cm and rotation
    {Pitch,Yaw,Roll} in degrees are world transforms even when attached. AttachComponentPath must be a
    registered scene component in the selected PIE world. Optional native attenuation/concurrency assets
    and spatialized flag configure native rendering; source/attenuation settings determine effective spatialization.
    audio_bus_sends: up to 16 unique BusPath/bPostEffect pairs with SendLevel [0,4]. play_sound queues
    them before playback; set_audio_bus_sends updates owned components. Level 0 mutes a route.
    Source SoundBase must enable bus sends. Inspection reports requested settings, not mixer readback.
    move_sound changes the owned component world transform. Use stop_sound for queued sound
    cancellation. release also stops/destroys sound components. Each EventId owns a
    native clock handle and a bounded event buffer. Quantization uses native names; Multiplier 1-64;
    ReferencePoint BarRelative/TransportRelative/CurrentTimeRelative. Other clocks need the same manager.
    Poll to observe native callbacks. Cancel pending requests before releasing them. PIE teardown releases handles.
    """
    return httpx.post(f"{app.BASE_URL}/audio/quartz/events", json={
        "EventId": event_id, "Operation": operation, "ClockName": clock_name, "PIEInstance": pie_instance,
        "Quantization": quantization, "Multiplier": multiplier, "ReferencePoint": reference_point,
        "BeatsPerMinute": beats_per_minute, "OtherClockName": other_clock_name,
        "SoundPath": sound_path, "StartTime": start_time, "VolumeMultiplier": volume_multiplier,
        "PitchMultiplier": pitch_multiplier, "FadeInDuration": fade_in_duration,
        "bSpatialized": spatialized, "Location": location or {"X": 0, "Y": 0, "Z": 0},
        "Rotation": rotation or {"Pitch": 0, "Yaw": 0, "Roll": 0},
        "AttachComponentPath": attach_component_path, "AttachSocket": attach_socket,
        "AttenuationPath": attenuation_path, "ConcurrencyPath": concurrency_path,
        "AudioBusSends": audio_bus_sends or [],
        "bFireOnClockStart": fire_on_clock_start, "bCancelIfNotRunning": cancel_if_not_running,
        "bResumeOnQueued": resume_on_queued, "bDryRun": dry_run,
    }).text


@mcp.tool()
def inspect_quartz_events(event_id: str, pie_instance: int | None = None,
                           after_sequence: int = 0, limit: int = 128) -> str:
    """Poll native Quartz command/metronome callbacks, with sequence cursor, overflow count and terminal state.

    Receipt timestamps are monotonic game-thread delivery times; metronome bar/beat fields are native payloads.
    The buffer retains 256 events. next_sequence advances through this page; dropped_events reports overflow.
    """
    params = {"event_id": event_id, "after_sequence": after_sequence, "limit": limit}
    if pie_instance is not None:
        params["pie_instance"] = pie_instance
    return httpx.get(f"{app.BASE_URL}/audio/quartz/events", params=params).text


@mcp.tool()
def create_dialogue_asset(asset_path: str, asset_type: str = "wave",
                          dry_run: bool = False, save: bool = False) -> str:
    """Create a Dialogue Voice or Dialogue Wave using the native editor factory."""
    return httpx.post(f"{app.BASE_URL}/audio/dialogue/create", json={
        "AssetPath": asset_path, "AssetType": asset_type, "bDryRun": dry_run, "bSave": save,
    }).text


@mcp.tool()
def inspect_dialogue_voice(asset_path: str) -> str:
    """Inspect a Dialogue Voice's gender, plurality, localization GUID, and dirty state."""
    return httpx.get(f"{app.BASE_URL}/audio/dialogue/voices/settings", params={"asset_path": asset_path}).text


@mcp.tool()
def edit_dialogue_voice(asset_path: str, gender: str | None = None,
                        plurality: str | None = None,
                        dry_run: bool = False, save: bool = False) -> str:
    """Edit Dialogue Voice gender/plurality while preserving localization identity."""
    body = {"AssetPath": asset_path, "bDryRun": dry_run, "bSave": save}
    if gender is not None:
        body["Gender"] = gender
    if plurality is not None:
        body["Plurality"] = plurality
    return httpx.patch(f"{app.BASE_URL}/audio/dialogue/voices/settings", json=body).text


@mcp.tool()
def inspect_dialogue_wave(asset_path: str) -> str:
    """Inspect dialogue script/subtitles, voice direction, contexts, audio references, and localization keys."""
    return httpx.get(f"{app.BASE_URL}/audio/dialogue/waves/settings", params={"asset_path": asset_path}).text


@mcp.tool()
def edit_dialogue_wave(asset_path: str, spoken_text: str | None = None,
                       subtitle_override: str | None = None,
                       override_subtitle: bool | None = None,
                       voice_actor_direction: str | None = None,
                       mature: bool | None = None,
                       dry_run: bool = False, save: bool = False) -> str:
    """Edit dialogue script, subtitles, voice direction, and mature flag; refresh native context proxies."""
    body = {"AssetPath": asset_path, "bDryRun": dry_run, "bSave": save}
    for flag, field, value in (("SpokenText", "SpokenText", spoken_text),
                               ("SubtitleOverride", "SubtitleOverride", subtitle_override),
                               ("OverrideSubtitle", "bOverrideSubtitle", override_subtitle),
                               ("VoiceActorDirection", "VoiceActorDirection", voice_actor_direction),
                               ("Mature", "bMature", mature)):
        if value is not None:
            body[f"bSet{flag}"] = True
            body[field] = value
    return httpx.patch(f"{app.BASE_URL}/audio/dialogue/waves/settings", json=body).text


@mcp.tool()
def edit_dialogue_context(asset_path: str, operation: str,
                          context_id: str | None = None,
                          speaker_path: str | None = None,
                          target_paths: list[str] | None = None,
                          sound_wave_path: str | None = None,
                          localization_key_format: str | None = None,
                          confirm_remove: bool = False,
                          dry_run: bool = False, save: bool = False) -> str:
    """Upsert/remove/clear dialogue contexts with compatible voice and recorded audio references.

    Existing contexts can be selected by the native context_id from inspection,
    or by exact speaker and ordered targets. Removal/clear requires confirmation.
    Localization key formats may contain literal text and {ContextHash}.
    """
    body = {"AssetPath": asset_path, "Operation": operation,
            "bConfirm": confirm_remove, "bDryRun": dry_run, "bSave": save}
    if context_id is not None:
        body["ContextId"] = context_id
    for flag, field, value in (("Speaker", "SpeakerPath", speaker_path),
                               ("Targets", "TargetPaths", target_paths),
                               ("SoundWave", "SoundWavePath", sound_wave_path),
                               ("LocalizationKeyFormat", "LocalizationKeyFormat", localization_key_format)):
        if value is not None:
            body[f"bSet{flag}"] = True
            body[field] = value
    return httpx.post(f"{app.BASE_URL}/audio/dialogue/contexts", json=body).text


@mcp.tool()
def resolve_dialogue_context(asset_path: str, context_id: str | None = None,
                             speaker_path: str | None = None,
                             target_paths: list[str] | None = None) -> str:
    """Resolve a dialogue context through UE's native proxy and localized text APIs without playing audio."""
    body = {"AssetPath": asset_path, "ContextId": context_id or "",
            "SpeakerPath": speaker_path or "", "TargetPaths": target_paths or []}
    return httpx.post(f"{app.BASE_URL}/audio/dialogue/resolve", json=body).text


@mcp.tool()
def validate_dialogue_asset(asset_path: str) -> str:
    """Validate dialogue enums, localization identity/keys, contexts, and recorded audio references.

    Draft contexts produce warnings and ready_for_playback=false separately from structural validity.
    """
    return httpx.post(f"{app.BASE_URL}/audio/dialogue/validate", json={"AssetPath": asset_path}).text


@mcp.tool()
def create_sound_concurrency(asset_path: str, save: bool = False,
                             dry_run: bool = False) -> str:
    """Create a Sound Concurrency asset for sound voice management."""
    return httpx.post(f"{app.BASE_URL}/audio/concurrencies/create", json={
        "AssetPath": asset_path, "bSave": save, "bDryRun": dry_run
    }).text


@mcp.tool()
def create_sound_cue(asset_path: str, save: bool = False,
                     dry_run: bool = False) -> str:
    """Create an empty Sound Cue asset with its editor graph root."""
    return httpx.post(f"{app.BASE_URL}/sound-cues/create", json={
        "AssetPath": asset_path, "bSave": save, "bDryRun": dry_run
    }).text


@mcp.tool()
def inspect_sound_cue_graph(asset_path: str) -> str:
    """Inspect Sound Cue graph nodes, positions, pins, links, and node settings."""
    return httpx.get(f"{app.BASE_URL}/sound-cues/graph", params={"asset_path": asset_path}).text


@mcp.tool()
def edit_sound_cue_graph(asset_path: str, operation: str,
                         node_id: str | None = None,
                         node_class: str | None = None,
                         wave_path: str | None = None,
                         source_node_id: str | None = None,
                         target_node_id: str | None = None,
                         input_index: int | None = None,
                         position_x: int | None = None,
                         position_y: int | None = None,
                         looping: bool | None = None,
                         properties: dict | None = None,
                         replace_existing: bool = False,
                         confirm_delete: bool = False,
                         dry_run: bool = False, save: bool = False) -> str:
    """Add/delete/connect/move/layout/compile Sound Cue nodes; node deletion requires confirmation."""
    body: dict = {"AssetPath": asset_path, "Operation": operation,
                  "bReplaceExisting": replace_existing, "bConfirm": confirm_delete,
                  "bDryRun": dry_run, "bSave": save}
    if node_id is not None:
        body["NodeId"] = node_id
    if node_class is not None:
        body["NodeClass"] = node_class
    if wave_path is not None:
        body["bSetWave"] = True
        body["WavePath"] = wave_path
    if source_node_id is not None:
        body["SourceNodeId"] = source_node_id
    if target_node_id is not None:
        body["TargetNodeId"] = target_node_id
    if input_index is not None:
        body["InputIndex"] = input_index
    if position_x is not None:
        body["PositionX"] = position_x
    if position_y is not None:
        body["PositionY"] = position_y
    if looping is not None:
        body["bSetLooping"] = True
        body["bLooping"] = looping
    if properties is not None:
        body["Properties"] = properties
    return httpx.post(f"{app.BASE_URL}/sound-cues/graph", json=body).text


@mcp.tool()
def validate_sound_cue(asset_path: str) -> str:
    """Validate Sound Cue graph roots, links, node references, cycles, and wave players."""
    return httpx.post(f"{app.BASE_URL}/sound-cues/validate", json={"AssetPath": asset_path}).text


@mcp.tool()
def create_metasound(asset_path: str, asset_type: str = "source",
                     parent_asset_path: str | None = None,
                     dry_run: bool = False, save: bool = False) -> str:
    """Create a MetaSound source or patch, optionally using a same-type preset parent."""
    return httpx.post(f"{app.BASE_URL}/metasounds/create", json={
        "AssetPath": asset_path, "AssetType": asset_type,
        "ParentAssetPath": parent_asset_path or "",
        "bDryRun": dry_run, "bSave": save,
    }).text


@mcp.tool()
def list_metasound_node_classes(search: str = "", limit: int = 100) -> str:
    """Search the registered, referenceable MetaSound node classes and their pins."""
    return httpx.get(f"{app.BASE_URL}/metasounds/node-classes", params={
        "search": search, "limit": limit,
    }).text


@mcp.tool()
def inspect_metasound_graph(asset_path: str) -> str:
    """Inspect MetaSound graph metadata, interface pins, node defaults, locations, and edges."""
    return httpx.get(f"{app.BASE_URL}/metasounds/graph", params={"asset_path": asset_path}).text


@mcp.tool()
def edit_metasound_graph(asset_path: str, operation: str,
                         node_id: str | None = None,
                         node_class: str | None = None,
                         major_version: int = 1,
                         source_node_id: str | None = None,
                         source_output: str | None = None,
                         target_node_id: str | None = None,
                         target_input: str | None = None,
                         input_name: str | None = None,
                         input_value: str | None = None,
                         position_x: int | None = None,
                         position_y: int | None = None,
                         replace_existing: bool = False,
                         confirm_delete: bool = False,
                         dry_run: bool = False, save: bool = False) -> str:
    """Add/remove/connect/disconnect/edit MetaSound nodes; node removal requires confirmation."""
    body: dict = {"AssetPath": asset_path, "Operation": operation,
                  "MajorVersion": major_version,
                  "bReplaceExisting": replace_existing, "bConfirm": confirm_delete,
                  "bDryRun": dry_run, "bSave": save}
    for key, value in (("NodeId", node_id), ("NodeClass", node_class),
                       ("SourceNodeId", source_node_id), ("SourceOutput", source_output),
                       ("TargetNodeId", target_node_id), ("TargetInput", target_input),
                       ("InputName", input_name), ("InputValue", input_value),
                       ("PositionX", position_x), ("PositionY", position_y)):
        if value is not None:
            body[key] = value
    return httpx.post(f"{app.BASE_URL}/metasounds/graph", json=body).text


@mcp.tool()
def validate_metasound(asset_path: str) -> str:
    """Validate MetaSound frontend document structure and graph edges."""
    return httpx.post(f"{app.BASE_URL}/metasounds/validate", json={"AssetPath": asset_path}).text


@mcp.tool()
def compile_metasound(asset_path: str, dry_run: bool = False, save: bool = False) -> str:
    """Register a MetaSound graph with the frontend to compile it, optionally saving."""
    return httpx.post(f"{app.BASE_URL}/metasounds/compile", json={
        "AssetPath": asset_path, "bDryRun": dry_run, "bSave": save,
    }).text


@mcp.tool()
def inspect_sound_wave_settings(asset_path: str) -> str:
    """Inspect Sound Wave compression, loading, loop, attenuation, and concurrency settings."""
    return httpx.get(f"{app.BASE_URL}/audio/waves/settings", params={"asset_path": asset_path}).text


@mcp.tool()
def edit_sound_wave_settings(asset_path: str, compression_type: str | None = None,
                              compression_quality: int | None = None,
                              sample_rate_quality: str | None = None,
                              looping: bool | None = None,
                              loading_behavior: str | None = None,
                              cloud_streaming: bool | None = None,
                              sound_class_path: str | None = None,
                              attenuation_path: str | None = None,
                              concurrency_paths: list[str] | None = None,
                              override_concurrency: bool | None = None,
                              dry_run: bool = False, save: bool = False) -> str:
    """Edit typed Sound Wave codec, streaming, loop, Sound Class, attenuation, and concurrency settings."""
    body: dict = {"AssetPath": asset_path, "bDryRun": dry_run, "bSave": save}
    if compression_type is not None:
        body["CompressionType"] = compression_type
    if compression_quality is not None:
        body["bSetCompressionQuality"] = True
        body["CompressionQuality"] = compression_quality
    if sample_rate_quality is not None:
        body["SampleRateQuality"] = sample_rate_quality
    if looping is not None:
        body["bSetLooping"] = True
        body["bLooping"] = looping
    if loading_behavior is not None:
        body["LoadingBehavior"] = loading_behavior
    if cloud_streaming is not None:
        body["bSetCloudStreaming"] = True
        body["bCloudStreaming"] = cloud_streaming
    if sound_class_path is not None:
        body["bSetSoundClass"] = True
        body["SoundClassPath"] = sound_class_path
    if attenuation_path is not None:
        body["bSetAttenuation"] = True
        body["AttenuationPath"] = attenuation_path
    if concurrency_paths is not None:
        body["bSetConcurrencyPaths"] = True
        body["ConcurrencyPaths"] = concurrency_paths
    if override_concurrency is not None:
        body["bSetOverrideConcurrency"] = True
        body["bOverrideConcurrency"] = override_concurrency
    return httpx.patch(f"{app.BASE_URL}/audio/waves/settings", json=body).text


@mcp.tool()
def rebuild_sound_wave(asset_path: str, dry_run: bool = False,
                       save: bool = False) -> str:
    """Rebuild a Sound Wave's derived platform audio data."""
    return httpx.post(f"{app.BASE_URL}/audio/waves/rebuild", json={
        "AssetPath": asset_path, "bDryRun": dry_run, "bSave": save
    }).text


@mcp.tool()
def validate_sound_wave(asset_path: str) -> str:
    """Validate Sound Wave compression and imported source metadata."""
    return httpx.post(f"{app.BASE_URL}/audio/waves/validate", json={"AssetPath": asset_path}).text


@mcp.tool()
def inspect_sound_wave_source(asset_path: str) -> str:
    """Inspect imported Sound Wave duration, channels, sample rate, and source files."""
    return httpx.get(f"{app.BASE_URL}/audio/waves/source", params={"asset_path": asset_path}).text


@mcp.tool()
def list_sound_wave_import_formats() -> str:
    """List audio extensions supported by the installed native Sound Factory for import/reimport."""
    return httpx.get(f"{app.BASE_URL}/audio/waves/import-formats").text


@mcp.tool()
def import_sound_wave(source_file_path: str, destination_path: str, asset_name: str,
                      replace_existing: bool = False, confirm_replace: bool = False,
                      dry_run: bool = False, save: bool = False) -> str:
    """Import a native-supported audio file as a Sound Wave; replacement requires confirmation."""
    return httpx.post(f"{app.BASE_URL}/audio/waves/import", json={
        "SourceFilePath": source_file_path, "DestinationPath": destination_path,
        "AssetName": asset_name, "bReplaceExisting": replace_existing,
        "bConfirmReplace": confirm_replace, "bDryRun": dry_run, "bSave": save,
    }).text


@mcp.tool()
def reimport_sound_wave(asset_path: str, source_file_path: str = "",
                        confirm_reimport: bool = False,
                        confirm_source_change: bool = False,
                        dry_run: bool = False, save: bool = False) -> str:
    """Reimport a Sound Wave from its recorded audio file or a confirmed new source/format."""
    return httpx.post(f"{app.BASE_URL}/audio/waves/reimport", json={
        "AssetPath": asset_path, "SourceFilePath": source_file_path,
        "bConfirmReimport": confirm_reimport,
        "bConfirmSourceChange": confirm_source_change,
        "bDryRun": dry_run, "bSave": save,
    }).text


@mcp.tool()
def edit_audio_asset_settings(asset_path: str, properties: dict,
                              save: bool = False) -> str:
    """Edit reflected settings on a supported audio asset, including Sound Concurrency."""
    return _asset_request("audio/assets/settings", asset_path, properties, save=save)


@mcp.tool()
def validate_audio_asset(asset_path: str) -> str:
    """Validate that an asset is a supported audio asset family, including Sound Concurrency."""
    return httpx.post(f"{app.BASE_URL}/audio/validate", json={"AssetPath": asset_path}).text


@mcp.tool()
def inspect_audio_volume(actor_path: str) -> str:
    """Inspect loaded AudioVolume controls/reverb/interior settings and submix collection counts.
    Native authored metadata, not listener containment/proxy readiness/audible output proof.
    """
    return httpx.post(f"{app.BASE_URL}/volumes/audio/inspect", json={"ActorPath": actor_path}, timeout=180).text


@mcp.tool()
def set_audio_volume_control(actor_path: str, actor_guid: str, expected_label: str,
                              field_name: str, expected_value: float, priority: float = 0,
                              enabled: bool = False, confirm: bool = False, dry_run: bool = True) -> str:
    """Set AudioVolume Priority+/-1e6 or bEnabled with exact identity/current native value guards.
    Native setters update world ordering/audio proxy; transaction/events/readback, no audio sync/save.
    """
    return httpx.post(f"{app.BASE_URL}/volumes/audio/control", json={
        "ActorPath": actor_path, "ActorGuid": actor_guid, "ExpectedLabel": expected_label,
        "FieldName": field_name, "ExpectedScalarValue": expected_value,
        "ScalarValue": priority, "bBoolValue": enabled, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_audio_volume_interior(actor_path: str, actor_guid: str, expected_label: str,
                               field_name: str, expected_value: float, value: float,
                               confirm: bool = False, dry_run: bool = True) -> str:
    """Set AudioVolume Exterior/Interior Volume0..1, Time/LPFTime0.01..100000, LPF20..20000Hz.
    Native SetInteriorSettings, full struct preservation checks/current field guard/transaction/events.
    Rejects unrelated native-clamp changes; no audio sync/listener evaluation/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/volumes/audio/interior", json={
        "ActorPath": actor_path, "ActorGuid": actor_guid, "ExpectedLabel": expected_label,
        "FieldName": field_name, "ExpectedScalarValue": expected_value, "ScalarValue": value,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_audio_volume_reverb(actor_path: str, actor_guid: str, expected_label: str,
                             field_name: str, expected_value: float, value: float = 0,
                             apply: bool = False, confirm: bool = False, dry_run: bool = True) -> str:
    """Set AudioVolume reverb Volume0..1/FadeTime0..100000/bApplyReverb using native setter.
    Full struct preservation/current scalar and actor guards; interpolation clamp preflight.
    Transaction/events/proxy readback, no effect asset edit/audio sync/playback/save.
    """
    return httpx.post(f"{app.BASE_URL}/volumes/audio/reverb", json={
        "ActorPath": actor_path, "ActorGuid": actor_guid, "ExpectedLabel": expected_label,
        "FieldName": field_name, "ExpectedScalarValue": expected_value, "ScalarValue": value,
        "bBoolValue": apply, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_audio_volume_reverb_object(actor_path: str, actor_guid: str, expected_label: str,
                                    field_name: str, expected_object_path: str, object_path: str,
                                    confirm: bool = False, dry_run: bool = True) -> str:
    """Assign ReverbEffect/ReverbPluginEffect using loaded compatible asset or permitted empty clear.
    Exact current reference/actor guards, native setter/full struct preservation/proxy update.
    Class compatibility not runtime plugin support; no asset load/audio sync/playback/save.
    """
    return httpx.post(f"{app.BASE_URL}/volumes/audio/reverb-object", json={
        "ActorPath": actor_path, "ActorGuid": actor_guid, "ExpectedLabel": expected_label,
        "FieldName": field_name, "ExpectedObjectPath": expected_object_path, "ObjectPath": object_path,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_audio_volume_submix(actor_path: str, collection: str = "SubmixSendSettings",
                                 start: int = 0, count: int = 64) -> str:
    """Inspect SubmixSendSettings/SubmixOverrideSettings rows1..128/nested sends or effects16.
    Native routing metadata/inactive fields included; external curve ref only, no inline curve evaluation.
    No asset load/audio graph or proxy query/mutation/save.
    """
    return httpx.post(f"{app.BASE_URL}/volumes/audio/submix/inspect", json={
        "ActorPath": actor_path, "FieldName": collection, "EntryStart": start, "EntryCount": count
    }, timeout=180).text


@mcp.tool()
def set_audio_volume_override_crossfade(actor_path: str, actor_guid: str, expected_label: str,
                                         row_index: int, expected_count: int, expected_submix_path: str,
                                         expected_seconds: float, seconds: float,
                                         confirm: bool = False, dry_run: bool = True, expected_row_texts: list[str] | None = None) -> str:
    """Edit existing AudioVolume submix override crossfade0..100000 with row/submix/value guards.
    Native setter/full array preservation/transaction/proxy update; no runtime crossfade start/audio sync/save.
    """
    return httpx.post(f"{app.BASE_URL}/volumes/audio/submix/override-crossfade", json={
        "ActorPath": actor_path, "ActorGuid": actor_guid, "ExpectedLabel": expected_label,
        "EntryIndex": row_index, "ExpectedEntryCount": expected_count, "ExpectedObjectPath": expected_submix_path,
        "ExpectedScalarValue": expected_seconds, "ScalarValue": seconds, "ExpectedRowTexts": expected_row_texts or [], "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_audio_volume_override_effects(actor_path: str, actor_guid: str, expected_label: str,
                                       row_index: int, expected_count: int, expected_submix_path: str,
                                       expected_effect_paths: list[str], effect_paths: list[str],
                                       confirm: bool = False, dry_run: bool = True, expected_row_texts: list[str] | None = None) -> str:
    """Replace full ordered AudioVolume override effect chain<=64, empty clears/duplicates allowed.
    Loaded persistent submix presets, exact row/submix/full prior chain guards, native transaction/proxy update.
    Presets unchanged, backend/channel readiness not validated; no audio sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/volumes/audio/submix/override-effects", json={
        "ActorPath": actor_path, "ActorGuid": actor_guid, "ExpectedLabel": expected_label,
        "EntryIndex": row_index, "ExpectedEntryCount": expected_count, "ExpectedObjectPath": expected_submix_path,
        "ExpectedAssetPaths": expected_effect_paths, "AssetPaths": effect_paths,
        "ExpectedRowTexts": expected_row_texts or [], "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_audio_volume_override_target(actor_path: str, actor_guid: str, expected_label: str,
                                       row_index: int, expected_count: int, expected_submix_path: str,
                                       submix_path: str, confirm: bool = False, dry_run: bool = True, expected_row_texts: list[str] | None = None) -> str:
    """Set existing AudioVolume override target to loaded USoundSubmix or empty repair-state clear.
    Rejects sibling duplicate target, preserves chain/fade; exact row/current guards/native transaction.
    No channel/effect compatibility or cross-volume conflict evaluation, audio sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/volumes/audio/submix/override-target", json={
        "ActorPath": actor_path, "ActorGuid": actor_guid, "ExpectedLabel": expected_label,
        "EntryIndex": row_index, "ExpectedEntryCount": expected_count,
        "ExpectedObjectPath": expected_submix_path, "ObjectPath": submix_path,
        "ExpectedRowTexts": expected_row_texts or [], "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def add_audio_volume_override(actor_path: str, actor_guid: str, expected_label: str,
                               expected_count: int, submix_path: str,
                               confirm: bool = False, dry_run: bool = True, expected_row_texts: list[str] | None = None) -> str:
    """Append AudioVolume override row targeting unique loaded USoundSubmix, count<128 guard.
    Native defaults empty effect chain/crossfade0; active empty chain can override effects.
    Full array preservation/native setter/transaction/proxy update; no audio sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/volumes/audio/submix/override-add", json={
        "ActorPath": actor_path, "ActorGuid": actor_guid, "ExpectedLabel": expected_label,
        "ExpectedEntryCount": expected_count, "ObjectPath": submix_path,
        "ExpectedRowTexts": expected_row_texts or [], "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def remove_audio_volume_override(actor_path: str, actor_guid: str, expected_label: str,
                                  row_index: int, expected_count: int, expected_submix_path: str,
                                  expected_effect_paths: list[str], confirm: bool = False,
                                  dry_run: bool = True, expected_row_texts: list[str] | None = None) -> str:
    """Remove existing AudioVolume override row with exact submix/full effect-chain/count guards.
    Preserves survivors and referenced assets; native transaction/events/proxy update.
    No audio synchronization/playback/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/volumes/audio/submix/override-remove", json={
        "ActorPath": actor_path, "ActorGuid": actor_guid, "ExpectedLabel": expected_label,
        "EntryIndex": row_index, "ExpectedEntryCount": expected_count,
        "ExpectedObjectPath": expected_submix_path, "ExpectedAssetPaths": expected_effect_paths,
        "ExpectedRowTexts": expected_row_texts or [], "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def reorder_audio_volume_overrides(actor_path: str, actor_guid: str, expected_label: str,
                                    expected_submix_paths: list[str], source_index_order: list[int],
                                    confirm: bool = False, dry_run: bool = True, expected_row_texts: list[str] | None = None) -> str:
    """Reorder all AudioVolume override rows by complete unique source-index permutation<=128.
    Full ordered target guards, preserves chains/fades; duplicate/null existing targets retained.
    Native setter/transaction/full array readback/proxy update, no audio sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/volumes/audio/submix/override-reorder", json={
        "ActorPath": actor_path, "ActorGuid": actor_guid, "ExpectedLabel": expected_label,
        "ExpectedEntryCount": len(expected_submix_paths), "ExpectedAssetPaths": expected_submix_paths,
        "EntryOrder": source_index_order, "ExpectedRowTexts": expected_row_texts or [], "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def add_audio_volume_send_row(actor_path: str, actor_guid: str, expected_label: str,
                               expected_count: int, listener_state: int,
                               confirm: bool = False, dry_run: bool = True, expected_row_texts: list[str] | None = None) -> str:
    """Append native AudioVolume send row, listener_state0 inside/1 outside, count<128 guard.
    Empty sends/default deprecated source state; duplicate listener states allowed.
    Native setter/full array preservation/transaction/proxy update, no audio sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/volumes/audio/submix/send-row-add", json={
        "ActorPath": actor_path, "ActorGuid": actor_guid, "ExpectedLabel": expected_label,
        "ExpectedEntryCount": expected_count, "ScalarValue": listener_state,
        "ExpectedRowTexts": expected_row_texts or [], "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def add_audio_volume_submix_send(actor_path: str, actor_guid: str, expected_label: str,
                                  row_index: int, expected_row_count: int, expected_listener_state: int,
                                  expected_send_count: int, submix_path: str,
                                  confirm: bool = False, dry_run: bool = True, expected_row_texts: list[str] | None = None) -> str:
    """Append native-default send to inspected listener row, loaded USoundSubmixBase target.
    Exact row/count/listener/nested count<64 guards, unique target within row; inspect new defaults.
    Native setter/transaction/full array readback/proxy update, no audio sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/volumes/audio/submix/send-add", json={
        "ActorPath": actor_path, "ActorGuid": actor_guid, "ExpectedLabel": expected_label,
        "EntryIndex": row_index, "ExpectedEntryCount": expected_row_count,
        "ExpectedScalarValue": expected_listener_state, "ExpectedNestedCount": expected_send_count,
        "ObjectPath": submix_path, "ExpectedRowTexts": expected_row_texts or [], "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_audio_volume_send_numeric(actor_path: str, actor_guid: str, expected_label: str,
                                   row_index: int, expected_row_count: int, expected_listener_state: int,
                                   send_index: int, expected_send_count: int, expected_submix_path: str,
                                   field_name: str, expected_value: float, value: float,
                                   confirm: bool = False, dry_run: bool = True, expected_row_texts: list[str] | None = None) -> str:
    """Edit SendLevel/MinSendLevel/MaxSendLevel/MinSendDistance/MaxSendDistance with exact guards.
    Levels0..1 (unclamped manual SendLevel<=1000), distances0..1e9/min<=max. Inactive fields allowed.
    Native setter/full routing preservation/transaction, no curve evaluation/audio sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/volumes/audio/submix/send-numeric", json={
        "ActorPath": actor_path, "ActorGuid": actor_guid, "ExpectedLabel": expected_label,
        "EntryIndex": row_index, "ExpectedEntryCount": expected_row_count, "ExpectedListenerState": expected_listener_state,
        "NestedIndex": send_index, "ExpectedNestedCount": expected_send_count, "ExpectedObjectPath": expected_submix_path,
        "FieldName": field_name, "ExpectedScalarValue": expected_value, "ScalarValue": value,
        "ExpectedRowTexts": expected_row_texts or [], "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_audio_volume_send_control(actor_path: str, actor_guid: str, expected_label: str,
                                   row_index: int, expected_row_count: int, expected_listener_state: int,
                                   send_index: int, expected_send_count: int, expected_submix_path: str,
                                   field_name: str, expected_value: int, value: int,
                                   confirm: bool = False, dry_run: bool = True, expected_row_texts: list[str] | None = None) -> str:
    """Set SendLevelControlMethod0 Linear1 CustomCurve2 Manual, SendStage0 post1 pre, or DisableManualSendClamp0..1.
    Exact selected send/context/value guards; stored gains/distances/curve preserved, not evaluated.
    Native transaction/full routing readback/proxy update, no audio sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/volumes/audio/submix/send-control", json={
        "ActorPath": actor_path, "ActorGuid": actor_guid, "ExpectedLabel": expected_label,
        "EntryIndex": row_index, "ExpectedEntryCount": expected_row_count, "ExpectedListenerState": expected_listener_state,
        "NestedIndex": send_index, "ExpectedNestedCount": expected_send_count, "ExpectedObjectPath": expected_submix_path,
        "FieldName": field_name, "ExpectedScalarValue": expected_value, "ScalarValue": value,
        "ExpectedRowTexts": expected_row_texts or [], "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_audio_volume_send_curve(actor_path: str, actor_guid: str, expected_label: str,
                                 row_index: int, expected_row_count: int, expected_listener_state: int,
                                 send_index: int, expected_send_count: int, expected_submix_path: str,
                                 expected_curve_path: str, curve_path: str,
                                 confirm: bool = False, dry_run: bool = True, expected_row_texts: list[str] | None = None) -> str:
    """Assign loaded CurveFloat to selected AudioVolume send or empty clear, full reference/context guards.
    Inline curve keys/control preserved; clear exposes stored inline curve. No key/output validation.
    Native setter/full routing transaction/readback/proxy update, no audio sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/volumes/audio/submix/send-curve", json={
        "ActorPath": actor_path, "ActorGuid": actor_guid, "ExpectedLabel": expected_label,
        "EntryIndex": row_index, "ExpectedEntryCount": expected_row_count, "ExpectedListenerState": expected_listener_state,
        "NestedIndex": send_index, "ExpectedNestedCount": expected_send_count, "ExpectedObjectPath": expected_submix_path,
        "ExpectedCurvePath": expected_curve_path, "CurvePath": curve_path,
        "ExpectedRowTexts": expected_row_texts or [], "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_audio_volume_send_target(actor_path: str, actor_guid: str, expected_label: str,
                                  row_index: int, expected_row_count: int, expected_listener_state: int,
                                  send_index: int, expected_send_count: int, expected_submix_path: str,
                                  submix_path: str, confirm: bool = False, dry_run: bool = True, expected_row_texts: list[str] | None = None) -> str:
    """Reassign selected send to loaded USoundSubmixBase or empty repair-state clear.
    Exact target/context guards, rejects nonnull sibling duplicate; curves/control/gains preserved.
    Native setter/transaction/full routing readback, no graph/channel validation/audio sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/volumes/audio/submix/send-target", json={
        "ActorPath": actor_path, "ActorGuid": actor_guid, "ExpectedLabel": expected_label,
        "EntryIndex": row_index, "ExpectedEntryCount": expected_row_count, "ExpectedListenerState": expected_listener_state,
        "NestedIndex": send_index, "ExpectedNestedCount": expected_send_count, "ExpectedObjectPath": expected_submix_path,
        "ObjectPath": submix_path, "ExpectedRowTexts": expected_row_texts or [], "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def remove_audio_volume_submix_send(actor_path: str, actor_guid: str, expected_label: str,
                                     row_index: int, expected_row_count: int, expected_listener_state: int,
                                     send_index: int, expected_send_count: int, expected_submix_path: str,
                                     confirm: bool = False, dry_run: bool = True, expected_row_texts: list[str] | None = None) -> str:
    """Remove inspected AudioVolume destination send with target/row/count/listener guards.
    Preserves surviving send/curve data and referenced assets; empty row retained.
    Native setter/transaction/proxy update, no audio sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/volumes/audio/submix/send-remove", json={
        "ActorPath": actor_path, "ActorGuid": actor_guid, "ExpectedLabel": expected_label,
        "EntryIndex": row_index, "ExpectedEntryCount": expected_row_count, "ExpectedListenerState": expected_listener_state,
        "NestedIndex": send_index, "ExpectedNestedCount": expected_send_count, "ExpectedObjectPath": expected_submix_path,
        "ExpectedRowTexts": expected_row_texts or [], "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def remove_audio_volume_send_row(actor_path: str, actor_guid: str, expected_label: str,
                                  row_index: int, expected_count: int, expected_listener_state: int,
                                  expected_destination_paths: list[str], confirm: bool = False,
                                  dry_run: bool = True, expected_row_texts: list[str] | None = None) -> str:
    """Remove whole listener send row with exact state/count/full ordered destination guards.
    Inline row curves removed, referenced assets retained; native transaction/full survivor checks.
    No audio synchronization/playback/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/volumes/audio/submix/send-row-remove", json={
        "ActorPath": actor_path, "ActorGuid": actor_guid, "ExpectedLabel": expected_label,
        "EntryIndex": row_index, "ExpectedEntryCount": expected_count,
        "ExpectedListenerState": expected_listener_state, "ExpectedAssetPaths": expected_destination_paths,
        "ExpectedRowTexts": expected_row_texts or [], "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_audio_volume_submix_row_items(actor_path: str, collection: str, row_index: int,
                                           start: int = 0, count: int = 64) -> str:
    """Page all sends/effects within selected AudioVolume submix row, native order1..128.
    collection SubmixSendSettings/SubmixOverrideSettings; offset applies nested items, not rows.
    Parent settings included, no asset load/audio evaluation/mutation/save.
    """
    return httpx.post(f"{app.BASE_URL}/volumes/audio/submix/row-items", json={
        "ActorPath": actor_path, "FieldName": collection, "EntryIndex": row_index,
        "EntryStart": start, "EntryCount": count
    }, timeout=180).text


@mcp.tool()
def set_audio_volume_send_row_listener(actor_path: str, actor_guid: str, expected_label: str,
                                        row_index: int, expected_row_count: int, expected_send_count: int,
                                        expected_listener_state: int, listener_state: int,
                                        confirm: bool = False, dry_run: bool = True, expected_row_texts: list[str] | None = None) -> str:
    """Set existing listener row0 inside/1 outside, exact row/count/send-count/current state guards.
    Preserves destinations/inline curves/deprecated source state, duplicate listener rows allowed.
    Native setter/full routing transaction/readback, no audio evaluation/sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/volumes/audio/submix/send-row-listener", json={
        "ActorPath": actor_path, "ActorGuid": actor_guid, "ExpectedLabel": expected_label,
        "EntryIndex": row_index, "ExpectedEntryCount": expected_row_count, "ExpectedNestedCount": expected_send_count,
        "ExpectedListenerState": expected_listener_state, "ScalarValue": listener_state,
        "ExpectedRowTexts": expected_row_texts or [], "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def inspect_audio_volume_send_inline_curve(actor_path: str, row_index: int, send_index: int,
                                            start: int = 0, count: int = 64) -> str:
    """Inspect stored inline send-curve keys/tangents/weights/extrapolation, pages1..128.
    External reference can mask inline data; no curve evaluation/validation/external traversal/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/volumes/audio/submix/send-inline-curve/inspect", json={
        "ActorPath": actor_path, "EntryIndex": row_index, "NestedIndex": send_index,
        "EntryStart": start, "EntryCount": count
    }, timeout=180).text


@mcp.tool()
def replace_audio_volume_send_linear_keys(actor_path: str, actor_guid: str, expected_label: str,
                                           row_index: int, expected_row_count: int, expected_listener_state: int,
                                           send_index: int, expected_send_count: int, expected_submix_path: str,
                                           expected_curve_path: str, expected_keys: list[list[float]],
                                           keys: list[list[float]], confirm: bool = False, dry_run: bool = True, expected_row_texts: list[str] | None = None) -> str:
    """Replace entire inline send curve with linear keys<=256; discards old tangents/interpolation/handles.
    Strict float time ordering0..1/value0..1, empty clears; expected keys are full time/value pairs.
    External curve/default/extrapolation preserved, external can mask inline; no evaluation/audio sync/save.
    """
    if any(len(pair) != 2 for pair in expected_keys + keys):
        raise ValueError("Keys require time/value pairs")
    return httpx.post(f"{app.BASE_URL}/volumes/audio/submix/send-inline-curve/linear-keys", json={
        "ActorPath": actor_path, "ActorGuid": actor_guid, "ExpectedLabel": expected_label,
        "EntryIndex": row_index, "ExpectedEntryCount": expected_row_count, "ExpectedListenerState": expected_listener_state,
        "NestedIndex": send_index, "ExpectedNestedCount": expected_send_count, "ExpectedObjectPath": expected_submix_path,
        "ExpectedCurvePath": expected_curve_path, "ExpectedPairs": [{"X": p[0], "Y": p[1]} for p in expected_keys],
        "Pairs": [{"X": p[0], "Y": p[1]} for p in keys], "ExpectedRowTexts": expected_row_texts or [], "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def reorder_audio_volume_submix_sends(actor_path: str, actor_guid: str, expected_label: str,
                                       row_index: int, expected_row_count: int, expected_listener_state: int,
                                       expected_destination_paths: list[str], source_index_order: list[int],
                                       confirm: bool = False, dry_run: bool = True, expected_row_texts: list[str] | None = None) -> str:
    """Reorder all sends in selected listener row via unique permutation<=64/full target guards.
    Preserves curves/controls/gains and existing null/duplicate targets; native full routing transaction/readback.
    No routing evaluation/audio synchronization/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/volumes/audio/submix/send-reorder", json={
        "ActorPath": actor_path, "ActorGuid": actor_guid, "ExpectedLabel": expected_label,
        "EntryIndex": row_index, "ExpectedEntryCount": expected_row_count, "ExpectedListenerState": expected_listener_state,
        "ExpectedNestedCount": len(expected_destination_paths), "ExpectedAssetPaths": expected_destination_paths,
        "EntryOrder": source_index_order, "ExpectedRowTexts": expected_row_texts or [], "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def reorder_audio_volume_send_rows(actor_path: str, actor_guid: str, expected_label: str,
                                    expected_listener_states: list[int], source_index_order: list[int],
                                    confirm: bool = False, dry_run: bool = True, expected_row_texts: list[str] | None = None) -> str:
    """Reorder listener rows by complete unique permutation<=128/ordered current state guards.
    Preserves all destinations/curves; duplicate listener states retained, state guard not unique row identity.
    Native setter/full routing preservation/transaction/proxy update, no audio sync/load/save.
    """
    return httpx.post(f"{app.BASE_URL}/volumes/audio/submix/send-row-reorder", json={
        "ActorPath": actor_path, "ActorGuid": actor_guid, "ExpectedLabel": expected_label,
        "ExpectedEntryCount": len(expected_listener_states), "ExpectedListenerStates": expected_listener_states,
        "EntryOrder": source_index_order, "ExpectedRowTexts": expected_row_texts or [], "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_audio_volume_send_inline_key_setting(actor_path: str, actor_guid: str, expected_label: str,
                                              row_index: int, expected_row_count: int, expected_listener_state: int,
                                              send_index: int, expected_send_count: int, expected_submix_path: str,
                                              expected_external_curve_path: str, expected_row_texts: list[str],
                                              key_index: int, expected_key_count: int,
                                              field_name: str, expected_value: float, value: float,
                                              confirm: bool = False, dry_run: bool = True) -> str:
    """Edit stored inline send curve with mandatory full ordered untruncated native row snapshot texts.
    InterpMode0 Linear/1 Constant/2 Cubic; TangentMode0 Auto/1 User/2 Break/4 SmartAuto;
    TangentWeightMode0 None/1 Arrive/2 Leave/3 Both; ArriveTangent/LeaveTangent+/-1e6,
    ArriveTangentWeight/LeaveTangentWeight0..1e6. Preserves key time/value, resets key handles.
    Preserves other routing/interior/reverb settings; external curve can mask inline data.
    No tangent recalculation, curve evaluation, audio synchronization, playback, load or save.
    """
    return httpx.post(f"{app.BASE_URL}/volumes/audio/submix/send-inline-curve/key-setting", json={
        "ActorPath": actor_path, "ActorGuid": actor_guid, "ExpectedLabel": expected_label,
        "EntryIndex": row_index, "ExpectedEntryCount": expected_row_count, "ExpectedListenerState": expected_listener_state,
        "NestedIndex": send_index, "ExpectedNestedCount": expected_send_count, "ExpectedObjectPath": expected_submix_path,
        "ExpectedCurvePath": expected_external_curve_path, "ExpectedRowTexts": expected_row_texts,
        "KeyIndex": key_index, "ExpectedKeyCount": expected_key_count,
        "FieldName": field_name, "ExpectedScalarValue": expected_value, "ScalarValue": value,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def set_audio_volume_send_inline_curve_setting(actor_path: str, actor_guid: str, expected_label: str,
                                              row_index: int, expected_row_count: int, expected_listener_state: int,
                                              send_index: int, expected_send_count: int, expected_submix_path: str,
                                              expected_external_curve_path: str, expected_row_texts: list[str],
                                              field_name: str, expected_value: float, value: float,
                                              confirm: bool = False, dry_run: bool = True) -> str:
    """Edit stored inline send curve with mandatory full ordered untruncated native row snapshot texts.
    DefaultValue0..1, ClearDefaultValue(value1), PreInfinityExtrap/PostInfinityExtrap0..5:
    0 Cycle,1 CycleWithOffset,2 Oscillate,3 Linear,4 Constant,5 None. Expected raw default includes unset sentinel.
    Preserves other routing/interior/reverb settings; external curve can mask inline data.
    No tangent recalculation, curve evaluation, audio synchronization, playback, load or save.
    """
    return httpx.post(f"{app.BASE_URL}/volumes/audio/submix/send-inline-curve/setting", json={
        "ActorPath": actor_path, "ActorGuid": actor_guid, "ExpectedLabel": expected_label,
        "EntryIndex": row_index, "ExpectedEntryCount": expected_row_count, "ExpectedListenerState": expected_listener_state,
        "NestedIndex": send_index, "ExpectedNestedCount": expected_send_count, "ExpectedObjectPath": expected_submix_path,
        "ExpectedCurvePath": expected_external_curve_path, "ExpectedRowTexts": expected_row_texts,
        "FieldName": field_name, "ExpectedScalarValue": expected_value, "ScalarValue": value,
        "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text


@mcp.tool()
def edit_audio_volume_send_inline_keys(actor_path: str, actor_guid: str, expected_label: str,
                                        row_index: int, expected_row_count: int, expected_listener_state: int,
                                        send_index: int, expected_send_count: int, expected_submix_path: str,
                                        expected_external_curve_path: str, expected_row_texts: list[str],
                                        expected_key_count: int, operation: str, key_index: int = -1,
                                        time: float = 0, value: float = 0,
                                        confirm: bool = False, dry_run: bool = True) -> str:
    """Add one linear key or Remove key_index with mandatory full ordered native row snapshots.
    Unique normalized float time/value0..1, at most256 keys, empty permitted; preserves surviving keys/tangents.
    Native routing setter/full readback; resets key handles, no tangent recalculation/evaluation/audio sync/save.
    """
    return httpx.post(f"{app.BASE_URL}/volumes/audio/submix/send-inline-curve/keys", json={
        "ActorPath": actor_path, "ActorGuid": actor_guid, "ExpectedLabel": expected_label,
        "EntryIndex": row_index, "ExpectedEntryCount": expected_row_count, "ExpectedListenerState": expected_listener_state,
        "NestedIndex": send_index, "ExpectedNestedCount": expected_send_count, "ExpectedObjectPath": expected_submix_path,
        "ExpectedCurvePath": expected_external_curve_path, "ExpectedRowTexts": expected_row_texts,
        "ExpectedKeyCount": expected_key_count, "KeyIndex": key_index, "FieldName": operation,
        "Pair": {"X": time, "Y": value}, "bConfirm": confirm, "bDryRun": dry_run
    }, timeout=180).text
