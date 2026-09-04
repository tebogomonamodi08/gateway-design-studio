from main import GatewayState
from model import GatewayConfig


def make_config():
    return GatewayConfig(
        model_list=[
            {
                "model_name": "GPT-4o",
                "litellm_params": {
                    "model": "openai/gpt-4o",
                },
            },
            {
                "model_name": "Claude",
                "litellm_params": {
                    "model": "anthropic/claude-3-5-sonnet",
                },
            },
        ]
    )


def test_gateway_state_reset():
    state = GatewayState()

    state.config = make_config()
    state.current_scenario = "failover"
    state.scenario_state = {
        "deployment-0": "failed"
    }

    state.reset()

    assert state.config is None
    assert state.topology is None
    assert state.current_scenario == "normal"
    assert state.scenario_state == {}


def test_scenario_status_mapping():
    state = GatewayState()

    assert state._get_node_status("normal") == "healthy"
    assert state._get_node_status("failover") == "failed"
    assert state._get_node_status("traffic_spike") == "stressed"
    assert state._get_node_status("load_test") == "busy"
    assert state._get_node_status("regional_failover") == "failed"


def test_failover_marks_affected_deployment_failed():
    state = GatewayState()

    state.set_scenario(
        "failover",
        ["deployment-0"],
    )

    assert state.current_scenario == "failover"
    assert state.scenario_state == {
        "deployment-0": "failed"
    }


def test_build_topology():
    state = GatewayState()
    state.config = make_config()

    state.build_topology()

    assert state.topology is not None

    assert len(state.topology["nodes"]) == 3
    assert len(state.topology["edges"]) == 2

    assert state.topology["nodes"][0] == {
        "id": "gateway",
        "name": "Gateway",
        "type": "gateway",
    }

    assert state.topology["nodes"][1]["id"] == "deployment-0"
    assert state.topology["nodes"][1]["name"] == "openai/gpt-4o"
    assert state.topology["nodes"][1]["display_name"] == "GPT-4o"

    assert state.topology["nodes"][2]["id"] == "deployment-1"
    assert state.topology["nodes"][2]["name"] == "anthropic/claude-3-5-sonnet"
    assert state.topology["nodes"][2]["display_name"] == "Claude"

    assert state.topology["edges"] == [
        {
            "source": "gateway",
            "target": "deployment-0",
        },
        {
            "source": "gateway",
            "target": "deployment-1",
        },
    ]