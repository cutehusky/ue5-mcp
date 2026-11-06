"""Verify Physics Asset validation detects invalid body settings on a copy."""

from pathlib import Path
import math
import uuid

from smoke_sequencer_live import request


PROJECT = Path(__file__).resolve().parents[5]
SOURCE = "/Game/Characters/Mannequins/Rigs/PA_Mannequin.PA_Mannequin"


def main():
    name = "PA_MCP_Validate_" + uuid.uuid4().hex[:8]
    destination = f"/Game/UE5MCP_Test/{name}"
    asset_file = PROJECT / "Content" / "UE5MCP_Test" / f"{name}.uasset"
    asset = ""
    try:
        asset = request("POST", "/assets/duplicate", {
            "AssetPath": SOURCE, "DestinationPath": destination})
        before = request("GET", "/physics-assets/validate", params={"asset_path": asset})
        assert before["valid"] and not before["errors"], before
        assert before["shape_count"] >= before["body_count"]

        runtime = request("GET", "/physics-assets/validate", params={
            "asset_path": asset, "include_runtime_cook": "true"})
        assert runtime["valid"] and runtime["runtime_cook_checked"] and runtime["runtime_ready"], runtime
        assert len(runtime["body_runtime_states"]) == runtime["body_count"], runtime
        assert all(body["ready"] and body["cooked_convex_count"] == body["convex_count"]
                   for body in runtime["body_runtime_states"]), runtime

        runtime_state = request("GET", "/physics-assets/validate", params={
            "asset_path": asset, "include_runtime_state": "true"})
        assert runtime_state["runtime_state_requested"] and runtime_state["runtime_state_checked"], runtime_state
        assert runtime_state["runtime_state_ready"], runtime_state
        assert len(runtime_state["runtime_body_instances"]) == runtime_state["body_count"], runtime_state
        assert len(runtime_state["runtime_constraint_instances"]) == runtime_state["constraint_count"], runtime_state
        assert all(body["valid"] for body in runtime_state["runtime_body_instances"]), runtime_state
        assert all(constraint["valid"] for constraint in runtime_state["runtime_constraint_instances"]), runtime_state

        simulation = request("GET", "/physics-assets/validate", params={
            "asset_path": asset, "include_simulation_step": "true"})
        assert simulation["runtime_state_checked"] and simulation["runtime_state_ready"], simulation
        assert simulation["simulation_step_requested"] and simulation["simulation_step_checked"], simulation
        assert simulation["simulation_step_ready"], simulation
        assert simulation["simulation_steps_requested"] == 1 and simulation["simulation_steps_completed"] == 1, simulation
        assert all(body["valid_after_step"] and body["simulating_after_step"]
                   for body in simulation["runtime_body_instances"]), simulation
        assert all(constraint["valid_after_step"]
                   for constraint in simulation["runtime_constraint_instances"]), simulation
        assert all(body["finite_after_step"] for body in simulation["runtime_body_instances"]), simulation

        request("GET", "/physics-assets/validate", params={
            "asset_path": asset, "simulation_steps": "601"}, expect_error=True)
        stability = request("GET", "/physics-assets/validate", params={
            "asset_path": asset, "include_stability_test": "true"})
        assert stability["simulation_stability_requested"] and stability["simulation_stability_checked"], stability
        assert stability["simulation_stability_ready"] and stability["simulation_step_ready"], stability
        assert stability["simulation_steps_requested"] == 600
        assert stability["simulation_steps_completed"] == 600, stability
        assert stability["simulation_body_samples_checked"] == 600 * stability["body_count"], stability
        assert stability["simulation_constraint_samples_checked"] == 600 * stability["constraint_count"], stability
        for metric in ("simulation_max_linear_speed_cm_s", "simulation_max_angular_speed_rad_s",
                       "simulation_max_displacement_cm"):
            assert math.isfinite(stability[metric]) and stability[metric] >= 0, stability
        assert all(body["valid_throughout"] and body["simulating_throughout"]
                   and body["finite_throughout"] for body in stability["runtime_body_instances"]), stability
        assert all(math.isfinite(body[key]) and body[key] >= 0
                   for body in stability["runtime_body_instances"]
                   for key in ("max_linear_speed_cm_s", "max_angular_speed_rad_s", "max_displacement_cm")), stability
        assert all(constraint["valid_throughout"]
                   for constraint in stability["runtime_constraint_instances"]), stability

        force_response = request("GET", "/physics-assets/validate", params={
            "asset_path": asset, "simulation_steps": "30", "simulation_impulse_z": "500"})
        assert force_response["simulation_step_checked"] and force_response["simulation_step_ready"], force_response
        assert force_response["simulation_steps_requested"] == 30
        assert force_response["simulation_steps_completed"] == 30, force_response
        assert force_response["simulation_impulse_applied"]
        assert force_response["simulation_impulse"]["z"] == 500
        assert force_response["simulation_impulse_displacement"] > 1.0, force_response
        assert all(body["finite_after_step"] and body["simulating_after_step"]
                   for body in force_response["runtime_body_instances"]), force_response

        request("PATCH", "/assets/properties", {"AssetPath": asset,
            "Properties": {"SkeletalBodySetups.0.DefaultInstance.MassScale": "-1"}})
        invalid = request("GET", "/physics-assets/validate", params={"asset_path": asset})
        assert not invalid["valid"]
        assert any("invalid mass scale" in error for error in invalid["errors"]), invalid
        invalid_runtime = request("GET", "/physics-assets/validate", params={
            "asset_path": asset, "include_runtime_state": "true"})
        assert not invalid_runtime["runtime_state_checked"]
        assert "structural validation errors" in invalid_runtime["runtime_state_skip_reason"], invalid_runtime
        invalid_simulation = request("GET", "/physics-assets/validate", params={
            "asset_path": asset, "include_simulation_step": "true"})
        assert invalid_simulation["simulation_step_requested"]
        assert not invalid_simulation["simulation_step_checked"], invalid_simulation
        assert invalid_simulation["simulation_steps_completed"] == 0, invalid_simulation
        invalid_stability = request("GET", "/physics-assets/validate", params={
            "asset_path": asset, "include_stability_test": "true"})
        assert invalid_stability["simulation_stability_requested"]
        assert not invalid_stability["simulation_stability_checked"], invalid_stability
        assert invalid_stability["simulation_steps_requested"] == 600
        assert invalid_stability["simulation_steps_completed"] == 0, invalid_stability
        original = request("GET", "/physics-assets/validate", params={"asset_path": SOURCE})
        assert original["valid"] and not original["errors"], original
        print("Physics Asset validation live smoke passed")
    finally:
        if asset:
            request("POST", "/assets/delete", {"AssetPath": asset})
        assert not asset_file.exists(), f"Test Physics Asset was not deleted: {asset_file}"


if __name__ == "__main__":
    main()
