import pytest

from pyomnilogic_local.models.mspconfig import MSPConfig

from .test_fixtures import load_fixture


class TestBowIdPropagation:
    """Test that bow_id is correctly propagated to sub-devices."""

    @pytest.fixture
    def config(self) -> MSPConfig:
        data = load_fixture("issue-144.json")
        return MSPConfig.load_xml(data["mspconfig"])

    def test_backyard_bow_id(self, config: MSPConfig):
        """Backyard and its direct non-BoW children should have default bow_id (-1)."""
        # Backyard itself
        assert config.backyard.bow_id == -1

        # Backyard sensors (e.g. AirSensor)
        if config.backyard.sensor:
            for sensor in config.backyard.sensor:
                assert sensor.bow_id == -1, f"Backyard sensor {sensor.name} should have bow_id -1"

    def test_bow_propagation(self, config: MSPConfig):
        """BoW and its children should have bow_id equal to BoW system_id."""
        assert config.backyard.bow
        pool = config.backyard.bow[0]

        # The BoW itself should have bow_id = system_id
        assert pool.bow_id == pool.system_id
        assert pool.system_id == 3

        # Verify Filter
        assert pool.filter
        for flt in pool.filter:
            assert flt.bow_id == pool.system_id, f"Filter {flt.name} should have bow_id {pool.system_id}"

        # Verify CSAD
        assert pool.csad
        for csad in pool.csad:
            assert csad.bow_id == pool.system_id
            # Verify nested CSAD Equipment
            if csad.csad_equipment:
                for eq in csad.csad_equipment:
                    assert eq.bow_id == pool.system_id

        # Verify Chlorinator
        assert pool.chlorinator
        assert pool.chlorinator.bow_id == pool.system_id
        # Verify nested Chlorinator Equipment
        if pool.chlorinator.chlorinator_equipment:
            for eq in pool.chlorinator.chlorinator_equipment:
                assert eq.bow_id == pool.system_id

        # Verify ColorLogic Light
        assert pool.colorlogic_light
        for light in pool.colorlogic_light:
            assert light.bow_id == pool.system_id

        # Verify Sensors inside BoW (Water, Flow)
        assert pool.sensor
        for sensor in pool.sensor:
            assert sensor.bow_id == pool.system_id

        # Verify Heater (Virtual Heater)
        assert pool.heater
        assert pool.heater.bow_id == pool.system_id
        # Verify Heater Equipment (nested)
        if pool.heater.heater_equipment:
            for eq in pool.heater.heater_equipment:
                assert eq.bow_id == pool.system_id

    def test_bow_propagation_issue_163(self):
        """Test bow_id propagation with Pump and Chlorinator (issue-163)."""
        data = load_fixture("issue-163.json")
        config = MSPConfig.load_xml(data["mspconfig"])

        assert config.backyard.bow
        pool = config.backyard.bow[0]
        assert pool.system_id == 10
        assert pool.bow_id == 10

        # Verify Pump
        assert pool.pump
        for pump in pool.pump:
            assert pump.bow_id == pool.system_id, f"Pump {pump.name} should have bow_id {pool.system_id}"

        # Verify Chlorinator
        assert pool.chlorinator
        assert pool.chlorinator.bow_id == pool.system_id

    def test_bow_propagation_issue_60(self):
        """Test bow_id propagation with Relays and multiple Heaters (issue-60)."""
        data = load_fixture("issue-60.json")
        config = MSPConfig.load_xml(data["mspconfig"])

        assert config.backyard.bow
        pool = config.backyard.bow[0]
        assert pool.system_id == 1

        # Verify Relay
        assert pool.relay
        for relay in pool.relay:
            assert relay.bow_id == pool.system_id, f"Relay {relay.name} should have bow_id {pool.system_id}"

        # Verify Heater Equipment
        # In issue-60, heaters might be directly under BoW or inside VirtualHeater?
        # Checking logic: MSPBoW has 'heater' which is MSPVirtualHeater.
        # MSPVirtualHeater has 'heater_equipment'.
        if pool.heater:
            assert pool.heater.bow_id == pool.system_id
            if pool.heater.heater_equipment:
                for eq in pool.heater.heater_equipment:
                    assert eq.bow_id == pool.system_id, f"Heater equipment {eq.name} should have bow_id {pool.system_id}"
