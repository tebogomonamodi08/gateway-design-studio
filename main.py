"""
Gateway Design Studio v1

Pipeline:

    Upload → Parse → Validate → Store → Visualize → Simulate

V2 Roadmap:

    Natural Language → Scenario Interpretation → Targeted Simulation
                     → Routing Recommendation
"""

import json

import yaml
from nicegui import ui
from pydantic import ValidationError

from model import GatewayConfig


# ============================================================
# STYLING
# ============================================================

ui.add_head_html(
    """
    <script src="https://unpkg.com/cytoscape/dist/cytoscape.min.js"></script>

    <link
        rel="stylesheet"
        href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"
    >

    <style>

        body {
            transition: opacity 0.3s ease-in-out;
        }

        body.fade-out {
            opacity: 0;
        }

        .glow {
            box-shadow:
                0 0 10px rgba(59, 130, 246, 0.35),
                0 0 30px rgba(59, 130, 246, 0.15);
        }

        .topology-container {
            background:
                linear-gradient(
                    135deg,
                    #0B1220 0%,
                    #0F1729 100%
                );

            position: relative;
            overflow: hidden;
        }

        .topology-container::before {
            content: '';

            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;

            background:
                radial-gradient(
                    circle at 20% 50%,
                    rgba(59, 130, 246, 0.05) 0%,
                    transparent 50%
                ),
                radial-gradient(
                    circle at 80% 80%,
                    rgba(34, 197, 94, 0.05) 0%,
                    transparent 50%
                );

            pointer-events: none;
        }

        #simulation-topology {
            position: relative;
            z-index: 1;
        }

    </style>
    """,
    shared=True,
)


# ============================================================
# APPLICATION STATE
# ============================================================


class GatewayState:
    """
    Stores the current gateway configuration,
    topology and simulation state.
    """

    def __init__(self) -> None:
        self.config: GatewayConfig | None = None
        self.topology: dict | None = None

        self.current_scenario: str = "normal"

        # Example:
        #
        # {
        #     "deployment-0": "failed"
        # }
        #
        self.scenario_state: dict = {}

    def reset(self) -> None:
        """Reset the gateway application state."""

        self.config = None
        self.topology = None
        self.current_scenario = "normal"
        self.scenario_state = {}

    def set_scenario(
        self,
        scenario: str,
        affected_nodes: list[str] | None = None,
    ) -> None:
        """Set the active simulation scenario."""

        self.current_scenario = scenario
        self.scenario_state = {}

        if affected_nodes:
            for node_id in affected_nodes:
                self.scenario_state[node_id] = (
                    self._get_node_status(scenario)
                )

    def _get_node_status(self, scenario: str) -> str:
        """Translate a scenario into a deployment status."""

        status_map = {
            "normal": "healthy",
            "failover": "failed",
            "traffic_spike": "stressed",
            "load_test": "busy",
            "regional_failover": "failed",
        }

        return status_map.get(
            scenario,
            "healthy",
        )

    def build_topology(self) -> None:
        """Build a graph representation from the validated configuration."""

        if self.config is None:
            self.topology = None
            return

        nodes = [
            {
                "id": "gateway",
                "name": "Gateway",
                "type": "gateway",
            }
        ]

        edges = []

        for index, deployment in enumerate(
            self.config.model_list
        ):
            node_id = f"deployment-{index}"

            nodes.append(
                {
                    "id": node_id,
                    "name": deployment.litellm_params.model,
                    "display_name": deployment.model_name,
                    "type": "deployment",
                }
            )

            edges.append(
                {
                    "source": "gateway",
                    "target": node_id,
                }
            )

        self.topology = {
            "nodes": nodes,
            "edges": edges,
        }


app_state = GatewayState()


# ============================================================
# NAVIGATION
# ============================================================


def open_simulation() -> None:
    """Navigate to the simulation page."""

    if app_state.topology is None:
        ui.notify(
            "No valid gateway configuration available.",
            color="negative",
        )
        return

    ui.run_javascript(
        """
        document.body.classList.add('fade-out');

        setTimeout(() => {
            window.location.href = '/simulation';
        }, 300);
        """
    )


def go_home() -> None:
    """Return to the Gateway Design Studio."""

    ui.run_javascript(
        """
        document.body.classList.add('fade-out');

        setTimeout(() => {
            window.location.href = '/';
        }, 300);
        """
    )


# ============================================================
# UPLOAD / PARSING / VALIDATION
# ============================================================


def handle_upload(event) -> None:
    """
    Process an uploaded gateway configuration.

    Pipeline:

        Upload
          ↓
        Parse
          ↓
        Validate
          ↓
        Store
          ↓
        Build topology
    """

    # --------------------------------------------------------
    # Clear previous UI
    # --------------------------------------------------------

    config_container.clear()
    advisor_container.clear()
    error_container.clear()
    preview_container.clear()

    # Reset application state
    app_state.reset()

    # --------------------------------------------------------
    # Read uploaded file
    # --------------------------------------------------------

    try:
        content = event.file._data.decode("utf-8")

    except Exception as exc:
        ui.notify(
            f"Could not read configuration: {exc}",
            color="negative",
        )
        return

    if not content.strip():
        ui.notify(
            "No content in the uploaded file.",
            color="warning",
        )
        return

    # --------------------------------------------------------
    # Parse YAML
    # --------------------------------------------------------

    try:
        raw_config = yaml.safe_load(content)

    except yaml.YAMLError as exc:
        ui.notify(
            "Invalid YAML syntax.",
            color="negative",
        )

        show_yaml_error(exc)
        return

    ui.notify(
        "Configuration parsed successfully.",
        color="green",
    )

    # --------------------------------------------------------
    # Configuration Preview
    # --------------------------------------------------------

    show_configuration_preview(content)

    # --------------------------------------------------------
    # Validate configuration
    # --------------------------------------------------------

    try:
        gateway_config = GatewayConfig.model_validate(
            raw_config
        )

    except ValidationError as error:
        show_validation_errors(error)
        return

    # --------------------------------------------------------
    # Store validated configuration
    # --------------------------------------------------------

    app_state.config = gateway_config

    app_state.build_topology()

    ui.notify(
        "Configuration validated successfully.",
        color="green",
    )

    # --------------------------------------------------------
    # Display configuration
    # --------------------------------------------------------

    show_validated_configuration(
        gateway_config
    )


# ============================================================
# CONFIGURATION PREVIEW
# ============================================================


def show_configuration_preview(
    content: str,
) -> None:
    """Render the uploaded YAML configuration."""

    with preview_container.classes(
        "w-full max-w-4xl items-center"
    ):
        with ui.card().classes(
            """
            w-full
            p-5
            rounded-xl
            border
            border-blue-400
            bg-slate-900
            """
        ):
            ui.label(
                "Configuration Preview"
            ).classes(
                "text-xl font-bold text-white"
            )

            ui.label(
                "Raw gateway configuration received from upload."
            ).classes(
                "text-gray-400 text-sm mb-3"
            )

            with ui.column().classes(
                """
                w-full
                p-4
                rounded-lg
                bg-[#0B1220]
                gap-1
                overflow-auto
                """
            ):
                for line_number, line in enumerate(
                    content.splitlines(),
                    start=1,
                ):
                    with ui.row().classes(
                        "w-full gap-3"
                    ):
                        ui.label(
                            str(line_number)
                        ).classes(
                            "text-gray-500 font-mono w-8"
                        )

                        ui.label(
                            line
                        ).classes(
                            "text-white font-mono whitespace-pre"
                        )


# ============================================================
# YAML ERRORS
# ============================================================


def show_yaml_error(
    error: yaml.YAMLError,
) -> None:
    """Display YAML parsing errors."""

    with error_container:
        with ui.card().classes(
            """
            w-full
            p-5
            rounded-xl
            bg-slate-900
            border
            border-red-500
            """
        ):
            ui.label(
                "YAML Parsing Error"
            ).classes(
                "text-xl font-bold text-red-400"
            )

            ui.label(
                str(error)
            ).classes(
                "text-gray-300 mt-2"
            )


# ============================================================
# VALIDATION ERRORS
# ============================================================


def show_validation_errors(
    error: ValidationError,
) -> None:
    """Display Pydantic validation diagnostics."""

    with error_container:
        with ui.card().classes(
            """
            w-full
            p-5
            rounded-xl
            bg-slate-900
            border
            border-red-500
            """
        ):
            with ui.row().classes(
                "w-full justify-between items-center"
            ):
                ui.label(
                    "Configuration Diagnostics"
                ).classes(
                    "text-xl font-bold text-red-400"
                )

                ui.badge(
                    "VALIDATION FAILED"
                ).props(
                    "color=red"
                )

            ui.separator()

            for validation_error in error.errors():

                field = " → ".join(
                    str(item)
                    for item in validation_error["loc"]
                )

                with ui.column().classes(
                    """
                    w-full
                    p-3
                    rounded-lg
                    bg-slate-800
                    border
                    border-red-500/40
                    gap-1
                    """
                ):
                    ui.label(
                        field
                    ).classes(
                        "text-red-300 font-semibold"
                    )

                    ui.label(
                        validation_error["msg"]
                    ).classes(
                        "text-gray-300"
                    )


# ============================================================
# VALIDATED CONFIGURATION
# ============================================================


def show_validated_configuration(
    config: GatewayConfig,
) -> None:
    """Display validated gateway deployments."""

    with config_container.classes(
        "w-full max-w-4xl items-center"
    ):
        with ui.card().classes(
            """
            w-full
            p-6
            rounded-xl
            border
            border-green-500/50
            bg-slate-900
            """
        ):

            # ------------------------------------------------
            # Header
            # ------------------------------------------------

            with ui.row().classes(
                "w-full justify-between items-center"
            ):
                ui.label(
                    "Deployment Configuration"
                ).classes(
                    "text-2xl font-bold text-white"
                )

                ui.badge(
                    "VALIDATED"
                ).props(
                    "color=green"
                )

            ui.separator()

            ui.label(
                f"{len(config.model_list)} "
                "model deployment(s) discovered"
            ).classes(
                "text-gray-400"
            )

            # ------------------------------------------------
            # Deployments
            # ------------------------------------------------

            for index, deployment in enumerate(
                config.model_list,
                start=1,
            ):
                with ui.row().classes(
                    """
                    w-full
                    justify-between
                    items-center
                    p-4
                    mt-3
                    rounded-xl
                    bg-slate-800
                    border
                    border-blue-500/30
                    """
                ):

                    with ui.column().classes(
                        "gap-1"
                    ):
                        ui.label(
                            deployment.model_name
                        ).classes(
                            "text-lg font-semibold text-white"
                        )

                        ui.label(
                            deployment.litellm_params.model
                        ).classes(
                            "text-gray-400 font-mono"
                        )

                    ui.badge(
                        f"DEPLOYMENT {index}"
                    ).props(
                        "color=blue"
                    )

            # ------------------------------------------------
            # Simulation Button
            # ------------------------------------------------

            ui.button(
                "Open Simulation Studio →",
                on_click=open_simulation,
            ).classes(
                """
                w-full
                mt-5
                px-6
                py-4
                bg-blue-600
                hover:bg-blue-500
                text-white
                rounded-xl
                text-lg
                font-semibold
                transition-all
                duration-300
                """
            )


# ============================================================
# SIMULATION PAGE
# ============================================================


@ui.page("/simulation")
def simulation_page() -> None:
    """Display the gateway topology simulation."""

    if app_state.topology is None:
        show_empty_simulation()
        return

    topology_data = app_state.topology

    # ========================================================
    # PAGE
    # ========================================================

    with ui.column().classes(
        """
        w-full
        min-h-screen
        bg-slate-950
        text-white
        p-8
        gap-6
        """
    ):

        # ====================================================
        # HEADER
        # ====================================================

        with ui.row().classes(
            """
            w-full
            max-w-6xl
            mx-auto
            justify-between
            items-center
            """
        ):

            with ui.column().classes(
                "gap-1"
            ):
                ui.label(
                    "Simulation Studio"
                ).classes(
                    "text-4xl font-bold"
                )

                ui.label(
                    "Gateway topology and operational scenarios"
                ).classes(
                    "text-gray-400 text-lg"
                )

            ui.button(
                "← Back",
                on_click=go_home,
            ).props(
                "outline color=blue"
            )

        # ====================================================
        # GATEWAY STATUS
        # ====================================================

        show_gateway_status(
            topology_data
        )

        # ====================================================
        # SCENARIO RESULTS CONTAINER
        # ====================================================

        results_container = ui.column().classes(
            "w-full max-w-6xl mx-auto"
        )

        # ====================================================
        # SCENARIO RESULT FUNCTION
        # ====================================================

        def show_scenario_results(
            scenario: str,
            deployment_count: int,
        ) -> None:

            results_container.clear()

            with results_container:

                scenario_info = {

                    "normal": (
                        "All Systems Operational",
                        "green",
                        (
                            "All deployments are healthy and available. "
                            "The gateway is operating normally and routing "
                            "traffic across the configured deployments."
                        ),
                    ),

                    "failover": (
                        "Deployment Failure Detected",
                        "red",
                        (
                            "An unhealthy deployment has been detected. "
                            "The gateway can remove the failed deployment "
                            "from the active routing pool and redistribute "
                            "traffic across healthy deployments."
                        ),
                    ),

                    "traffic_spike": (
                        "High Traffic Detected",
                        "yellow",
                        (
                            "Incoming traffic has increased significantly. "
                            "The gateway distributes requests across the "
                            "available deployments to maintain service "
                            "availability."
                        ),
                    ),

                    "load_test": (
                        "Load Distribution Test",
                        "blue",
                        (
                            "The gateway is evaluating request distribution "
                            "across deployments and observing deployment "
                            "capacity."
                        ),
                    ),

                    "regional_failover": (
                        "Regional Outage Simulation",
                        "red",
                        (
                            "A regional deployment is unavailable. "
                            "The gateway activates alternative routing "
                            "to maintain service availability."
                        ),
                    ),
                }

                (
                    title,
                    color,
                    result_text,
                ) = scenario_info.get(
                    scenario,
                    (
                        "Scenario Running",
                        "gray",
                        "Simulation in progress...",
                    ),
                )

                with ui.card().classes(
                    """
                    w-full
                    p-6
                    bg-slate-900
                    border
                    border-blue-500/40
                    """
                ):

                    ui.label(
                        title
                    ).classes(
                        f"text-2xl font-bold text-{color}-400"
                    )

                    ui.label(
                        f"Configured Deployments: "
                        f"{deployment_count}"
                    ).classes(
                        "text-gray-400 mt-2"
                    )

                    ui.label(
                        result_text
                    ).classes(
                        "text-gray-300 mt-4 leading-relaxed"
                    )

        # ====================================================
        # SCENARIO CONTROL PANEL
        # ====================================================

        with ui.card().classes(
            """
            w-full
            max-w-6xl
            mx-auto
            p-6
            bg-slate-900
            border
            border-emerald-500/40
            """
        ):

            ui.label(
                "⚡ Simulation Scenarios"
            ).classes(
                "text-2xl font-bold mb-4"
            )

            with ui.row().classes(
                "w-full gap-4 items-end"
            ):

                scenario_selector = ui.select(
                    label="Select Scenario",
                    value="normal",
                    options={
                        "normal": "🟢 Normal Operation",
                        "failover": "🔴 Deployment Failover",
                        "traffic_spike": "🟡 Traffic Spike",
                        "load_test": "🔵 Load Distribution Test",
                    },
                ).classes(
                    "flex-1"
                )

                def run_scenario() -> None:
                    """Execute the selected simulation scenario."""

                    scenario = scenario_selector.value

                    deployment_count = (
                        len(topology_data["nodes"]) - 1
                    )

                    # ----------------------------------------
                    # IMPORTANT DEMO BEHAVIOR
                    #
                    # Failover affects ONE deployment.
                    #
                    # This makes the simulation demonstrate
                    # a realistic targeted deployment failure.
                    # ----------------------------------------

                    if (
                        scenario == "failover"
                        and deployment_count > 0
                    ):
                        affected = [
                            "deployment-0"
                        ]

                    else:
                        affected = []

                    app_state.set_scenario(
                        scenario,
                        affected,
                    )

                    render_topology_with_scenario()

                    show_scenario_results(
                        scenario,
                        deployment_count,
                    )

                ui.button(
                    "▶ Run Scenario",
                    on_click=run_scenario,
                ).props(
                    "color=green"
                ).classes(
                    "px-8"
                )

            # =================================================
            # FUTURE INTELLIGENT ANALYSIS
            # =================================================

            with ui.card().classes(
                """
                w-full
                mt-6
                p-5
                rounded-xl
                bg-slate-950/70
                border
                border-purple-500/30
                """
            ):

                with ui.row().classes(
                    "w-full items-center justify-between"
                ):

                    with ui.column().classes(
                        "gap-1"
                    ):
                        ui.label(
                            "Intelligent Scenario Analysis"
                        ).classes(
                            "text-lg font-semibold text-white"
                        )

                        ui.label(
                            "Natural-language operational analysis"
                        ).classes(
                            "text-sm text-gray-500"
                        )

                    ui.badge(
                        "COMING NEXT"
                    ).props(
                        "color=purple"
                    )

                ui.separator().classes(
                    "my-3"
                )

                with ui.row().classes(
                    "w-full items-center gap-3"
                ):

                    ui.input(
                        placeholder=(
                            "e.g. What happens if the "
                            "Claude deployment fails?"
                        )
                    ).props(
                        "outlined disable"
                    ).classes(
                        "flex-1"
                    )

                    ui.button(
                        "Analyze"
                    ).props(
                        "disable color=purple"
                    )

                ui.label(
                    "Future capability: describe an operational "
                    "condition in natural language and translate "
                    "it into a targeted gateway simulation."
                ).classes(
                    "text-sm text-gray-500 mt-2"
                )

                with ui.row().classes(
                    "w-full gap-2 mt-2"
                ):

                    ui.badge(
                        "Deployment failures"
                    ).props(
                        "outline"
                    )

                    ui.badge(
                        "Traffic analysis"
                    ).props(
                        "outline"
                    )

                    ui.badge(
                        "Routing recommendations"
                    ).props(
                        "outline"
                    )

        # ====================================================
        # TOPOLOGY
        # ====================================================

        with ui.card().classes(
            """
            w-full
            max-w-6xl
            mx-auto
            p-6
            bg-slate-900
            border
            border-blue-500/40
            glow
            """
        ):

            with ui.row().classes(
                """
                w-full
                justify-between
                items-center
                mb-4
                """
            ):

                with ui.column().classes(
                    "gap-1"
                ):

                    ui.label(
                        "Gateway Topology"
                    ).classes(
                        "text-2xl font-bold"
                    )

                    ui.label(
                        "Live representation of configured deployments"
                    ).classes(
                        "text-gray-400"
                    )

                ui.badge(
                    "SIMULATION READY"
                ).props(
                    "color=green"
                )

            ui.html(
                """
                <div
                    id="simulation-topology"
                    style="width:100%; height:500px;"
                    class="topology-container"
                ></div>
                """
            ).classes(
                """
                w-full
                rounded-xl
                bg-gradient-to-br
                from-[#0B1220]
                to-[#0F1729]
                border
                border-slate-700/50
                """
            )

        # ====================================================
        # DEPLOYMENTS
        # ====================================================

        show_deployments()


# ============================================================
# EMPTY SIMULATION
# ============================================================


def show_empty_simulation() -> None:
    """Display the simulation empty state."""

    with ui.column().classes(
        """
        w-full
        min-h-screen
        items-center
        justify-center
        bg-slate-950
        """
    ):

        ui.label(
            "No Gateway Configuration"
        ).classes(
            "text-3xl font-bold text-white"
        )

        ui.label(
            "Upload and validate a configuration first."
        ).classes(
            "text-gray-400"
        )

        ui.button(
            "← Back to Design Studio",
            on_click=go_home,
        ).props(
            "outline color=blue"
        )


# ============================================================
# GATEWAY STATUS
# ============================================================


def show_gateway_status(
    topology: dict,
) -> None:
    """Display gateway operational status."""

    deployment_count = (
        len(topology["nodes"]) - 1
    )

    with ui.row().classes(
        """
        w-full
        max-w-6xl
        mx-auto
        gap-4
        """
    ):

        create_status_card(
            "Gateway Status",
            "OPERATIONAL",
            "text-green-400",
        )

        create_status_card(
            "Deployments",
            str(deployment_count),
            "text-blue-400",
        )

        create_status_card(
            "Configuration",
            "VALIDATED",
            "text-green-400",
        )

        create_status_card(
            "Routing",
            "READY",
            "text-blue-400",
        )


# ============================================================
# STATUS CARD
# ============================================================


def create_status_card(
    title: str,
    value: str,
    value_class: str,
) -> None:
    """Create a status card."""

    with ui.card().classes(
        """
        flex-1
        p-4
        bg-slate-900
        border
        border-blue-500/40
        """
    ):

        ui.label(
            title
        ).classes(
            "text-gray-400 text-sm"
        )

        ui.label(
            value
        ).classes(
            f"{value_class} text-xl font-bold"
        )


# ============================================================
# DEPLOYMENTS
# ============================================================


def show_deployments() -> None:
    """Display configured model deployments."""

    with ui.card().classes(
        """
        w-full
        max-w-6xl
        mx-auto
        p-6
        bg-slate-900
        border
        border-blue-500/40
        """
    ):

        ui.label(
            "Configured Deployments"
        ).classes(
            "text-2xl font-bold mb-4"
        )

        for index, deployment in enumerate(
            app_state.config.model_list,
            start=1,
        ):

            node_id = (
                f"deployment-{index - 1}"
            )

            status = app_state.scenario_state.get(
                node_id,
                "healthy",
            )

            status_labels = {
                "healthy": "HEALTHY",
                "stressed": "STRESSED",
                "busy": "BUSY",
                "failed": "FAILED",
            }

            status_colors = {
                "healthy": "green",
                "stressed": "orange",
                "busy": "blue",
                "failed": "red",
            }

            with ui.row().classes(
                """
                w-full
                justify-between
                items-center
                p-4
                rounded-lg
                bg-slate-800
                border
                border-slate-700
                """
            ):

                with ui.column().classes(
                    "gap-1"
                ):

                    ui.label(
                        deployment.model_name
                    ).classes(
                        "text-lg font-semibold"
                    )

                    ui.label(
                        deployment.litellm_params.model
                    ).classes(
                        "text-gray-400 font-mono"
                    )

                with ui.row().classes(
                    "items-center gap-3"
                ):

                    ui.badge(
                        status_labels.get(
                            status,
                            "UNKNOWN",
                        )
                    ).props(
                        f"color={status_colors.get(status, 'gray')}"
                    )

                    ui.badge(
                        f"DEPLOYMENT {index}"
                    ).props(
                        "color=blue"
                    )

    # Render topology after deployment section
    render_topology()


# ============================================================
# CYTOSCAPE
# ============================================================


def render_topology() -> None:
    """Render the current gateway topology."""

    render_topology_with_scenario()


def render_topology_with_scenario() -> None:
    """
    Render gateway topology using Cytoscape.

    Deployment status is derived from app_state.scenario_state.
    """

    if app_state.topology is None:
        return

    topology_json = json.dumps(
        app_state.topology
    )

    scenario_state_json = json.dumps(
        app_state.scenario_state
    )

    ui.run_javascript(
        f"""
        setTimeout(() => {{

            const topologyData = {topology_json};

            const scenarioState = {scenario_state_json};

            const elements = [];

            // ----------------------------------------------
            // Nodes
            // ----------------------------------------------

            topologyData.nodes.forEach(node => {{

                elements.push({{
                    data: {{
                        id: node.id,
                        label: node.name,
                        type: node.type,
                        status:
                            scenarioState[node.id]
                            || 'healthy'
                    }}
                }});

            }});

            // ----------------------------------------------
            // Edges
            // ----------------------------------------------

            topologyData.edges.forEach(edge => {{

                elements.push({{
                    data: {{
                        id:
                            edge.source
                            + '-'
                            + edge.target,

                        source: edge.source,

                        target: edge.target
                    }}
                }});

            }});

            // ----------------------------------------------
            // Container
            // ----------------------------------------------

            const container =
                document.getElementById(
                    'simulation-topology'
                );

            if (!container) {{
                console.error(
                    'Topology container not found'
                );
                return;
            }}

            if (typeof cytoscape === 'undefined') {{
                console.error(
                    'Cytoscape failed to load'
                );
                return;
            }}

            // ----------------------------------------------
            // Gateway Icon
            // ----------------------------------------------

            const computerIcon =
                'data:image/svg+xml;base64,' +
                'PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAxMDAgMTAwIj48Y2lyY2xlIGN4PSI1MCIgY3k9IjUwIiByPSIyMiIgZmlsbD0ibm9uZSIgc3Ryb2tlPSIjM2I4MmY2IiBzdHJva2Utd2lkdGg9IjMiLz48Y2lyY2xlIGN4PSI1MCIgY3k9IjUwIiByPSIxNCIgZmlsbD0iIzFlNDBhZiIvPjwvc3ZnPg==';

            // ----------------------------------------------
            // Deployment Icon
            // ----------------------------------------------

            const cloudIcon =
                'data:image/svg+xml;base64,' +
                'PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAxMDAgMTAwIj48cGF0aCBkPSJNIDMwIDYwIFEgMjAgNjAgMjAgNTAgUSAyMCA0MiAyNiAzOCBRIDMwIDI1IDQ1IDI1IFEgNTUgMjUgNTggMzUgUSA3MCAzNSA3NSA0NSBRIDgwIDUwIDgwIDYwIFoiIGZpbGw9Im5vbmUiIHN0cm9rZT0iIzJkZDRiZiIgc3Ryb2tlLXdpZHRoPSIyLjUiLz48L3N2Zz4=';

            // ----------------------------------------------
            // Cytoscape
            // ----------------------------------------------

            const cy = cytoscape({{

                container: container,

                elements: elements,

                style: [

                    // --------------------------------------
                    // Gateway
                    // --------------------------------------

                    {{
                        selector:
                            'node[type="gateway"]',

                        style: {{

                            'label':
                                'data(label)',

                            'background-color':
                                'transparent',

                            'background-image':
                                computerIcon,

                            'background-fit':
                                'contain',

                            'background-opacity':
                                1,

                            'color':
                                '#60a5fa',

                            'font-size':
                                '14px',

                            'font-weight':
                                'bold',

                            'text-valign':
                                'bottom',

                            'text-halign':
                                'center',

                            'text-margin-y':
                                '15px',

                            'width':
                                '100px',

                            'height':
                                '100px',

                            'border-width':
                                '2px',

                            'border-color':
                                '#3b82f6',

                            'border-opacity':
                                0.7,

                            'shadow-blur':
                                '15px',

                            'shadow-color':
                                '#3b82f6',

                            'shadow-opacity':
                                0.6,

                            'shape':
                                'ellipse',

                            'z-index':
                                10
                        }}
                    }},

                    // --------------------------------------
                    // Healthy Deployment
                    // --------------------------------------

                    {{
                        selector:
                            'node[type="deployment"][status="healthy"]',

                        style: {{

                            'label':
                                'data(label)',

                            'background-color':
                                'transparent',

                            'background-image':
                                cloudIcon,

                            'background-fit':
                                'contain',

                            'background-opacity':
                                1,

                            'color':
                                '#2dd4bf',

                            'font-size':
                                '11px',

                            'font-weight':
                                'bold',

                            'text-valign':
                                'bottom',

                            'text-halign':
                                'center',

                            'text-margin-y':
                                '12px',

                            'width':
                                '120px',

                            'height':
                                '80px',

                            'shape':
                                'round-rectangle',

                            'border-width':
                                '1.5px',

                            'border-color':
                                '#2dd4bf',

                            'border-opacity':
                                0.6,

                            'shadow-blur':
                                '12px',

                            'shadow-color':
                                '#14b8a6',

                            'shadow-opacity':
                                0.5,

                            'padding':
                                '4px'
                        }}
                    }},

                    // --------------------------------------
                    // Stressed Deployment
                    // --------------------------------------

                    {{
                        selector:
                            'node[type="deployment"][status="stressed"]',

                        style: {{

                            'label':
                                'data(label)',

                            'background-color':
                                'transparent',

                            'background-image':
                                cloudIcon,

                            'background-fit':
                                'contain',

                            'color':
                                '#fbbf24',

                            'font-size':
                                '11px',

                            'font-weight':
                                'bold',

                            'text-valign':
                                'bottom',

                            'text-halign':
                                'center',

                            'text-margin-y':
                                '12px',

                            'width':
                                '120px',

                            'height':
                                '80px',

                            'shape':
                                'round-rectangle',

                            'border-width':
                                '2px',

                            'border-color':
                                '#f59e0b',

                            'shadow-blur':
                                '20px',

                            'shadow-color':
                                '#f59e0b',

                            'shadow-opacity':
                                0.8,

                            'padding':
                                '4px'
                        }}
                    }},

                    // --------------------------------------
                    // Busy Deployment
                    // --------------------------------------

                    {{
                        selector:
                            'node[type="deployment"][status="busy"]',

                        style: {{

                            'label':
                                'data(label)',

                            'background-color':
                                'transparent',

                            'background-image':
                                cloudIcon,

                            'background-fit':
                                'contain',

                            'color':
                                '#60a5fa',

                            'font-size':
                                '11px',

                            'font-weight':
                                'bold',

                            'text-valign':
                                'bottom',

                            'text-halign':
                                'center',

                            'text-margin-y':
                                '12px',

                            'width':
                                '120px',

                            'height':
                                '80px',

                            'shape':
                                'round-rectangle',

                            'border-width':
                                '2px',

                            'border-color':
                                '#60a5fa',

                            'shadow-blur':
                                '18px',

                            'shadow-color':
                                '#3b82f6',

                            'shadow-opacity':
                                0.7,

                            'padding':
                                '4px'
                        }}
                    }},

                    // --------------------------------------
                    // Failed Deployment
                    // --------------------------------------

                    {{
                        selector:
                            'node[type="deployment"][status="failed"]',

                        style: {{

                            'label':
                                'data(label)',

                            'background-color':
                                '#450a0a',

                            'background-image':
                                cloudIcon,

                            'background-fit':
                                'contain',

                            'background-opacity':
                                0.4,

                            'color':
                                '#ef4444',

                            'font-size':
                                '11px',

                            'font-weight':
                                'bold',

                            'text-valign':
                                'bottom',

                            'text-halign':
                                'center',

                            'text-margin-y':
                                '12px',

                            'width':
                                '120px',

                            'height':
                                '80px',

                            'shape':
                                'round-rectangle',

                            'border-width':
                                '3px',

                            'border-color':
                                '#dc2626',

                            'border-opacity':
                                1,

                            'shadow-blur':
                                '25px',

                            'shadow-color':
                                '#dc2626',

                            'shadow-opacity':
                                0.9,

                            'padding':
                                '4px'
                        }}
                    }},

                    // --------------------------------------
                    // Edges
                    // --------------------------------------

                    {{
                        selector:
                            'edge',

                        style: {{

                            'width':
                                2.5,

                            'line-color':
                                '#3b82f6',

                            'target-arrow-color':
                                '#3b82f6',

                            'target-arrow-shape':
                                'triangle',

                            'curve-style':
                                'bezier',

                            'opacity':
                                0.8
                        }}
                    }},

                    // --------------------------------------
                    // Edge Hover
                    // --------------------------------------

                    {{
                        selector:
                            'edge:active',

                        style: {{

                            'width':
                                4,

                            'line-color':
                                '#60a5fa',

                            'target-arrow-color':
                                '#60a5fa',

                            'opacity':
                                1
                        }}
                    }}
                ],

                layout: {{

                    name:
                        'breadthfirst',

                    directed:
                        true,

                    roots:
                        '#gateway',

                    padding:
                        80,

                    spacingFactor:
                        2.2,

                    avoidOverlap:
                        true,

                    nodeDimensionsIncludeLabels:
                        true
                }}
            }});

            // ----------------------------------------------
            // Node interaction
            // ----------------------------------------------

            cy.on(
                'tap',
                'node',
                function(evt) {{

                    const node = evt.target;

                    node.animate({{
                        duration: 300,
                        queue: false
                    }});

                    console.log(
                        'Selected node:',
                        node.id()
                    );
                }}
            );

            console.log(
                'Gateway topology rendered:',
                topologyData
            );

        }}, 200);
        """
    )


# ============================================================
# MAIN PAGE
# ============================================================


@ui.page("/")
def index() -> None:
    """Gateway Design Studio landing page."""

    with ui.column().classes(
        """
        w-full
        min-h-screen
        bg-slate-950
        items-center
        p-8
        gap-6
        """
    ):

        # ====================================================
        # HEADER
        # ====================================================

        with ui.column().classes(
            """
            w-full
            max-w-4xl
            gap-1
            """
        ):

            ui.label(
                "Gateway Design Studio"
            ).classes(
                "text-4xl font-bold text-white"
            )

            ui.label(
                "Configuration Management & Observability"
            ).classes(
                "text-gray-400 text-lg"
            )

            ui.label(
                "Upload → Validate → Visualize → Simulate"
            ).classes(
                "text-blue-400 text-sm mt-2"
            )

        # ====================================================
        # UPLOAD
        # ====================================================

        with ui.card().classes(
            """
            w-full
            max-w-4xl
            p-8
            rounded-2xl
            border-2
            border-dashed
            border-blue-400
            bg-slate-900
            """
        ):

            with ui.column().classes(
                """
                w-full
                items-center
                gap-3
                """
            ):

                ui.icon(
                    "cloud_upload"
                ).classes(
                    "text-6xl text-blue-400"
                )

                ui.label(
                    "Upload Gateway Configuration"
                ).classes(
                    "text-2xl font-bold text-white"
                )

                ui.label(
                    "Upload a config.yaml file to initialize the gateway."
                ).classes(
                    "text-gray-400"
                )

                ui.upload(
                    on_upload=handle_upload
                ).props(
                    'label="Choose config.yaml" '
                    "color=primary "
                    "unelevated"
                ).classes(
                    """
                    mt-3
                    px-8
                    py-3
                    rounded-xl
                    text-lg
                    font-semibold
                    bg-blue-500
                    hover:bg-blue-400
                    text-white
                    """
                )

        # ====================================================
        # DYNAMIC CONTAINERS
        # ====================================================

        global preview_container
        global config_container
        global advisor_container
        global error_container

        preview_container = ui.column().classes(
            "w-full max-w-4xl"
        )

        config_container = ui.column().classes(
            "w-full max-w-4xl"
        )

        advisor_container = ui.column().classes(
            "w-full max-w-4xl"
        )

        error_container = ui.column().classes(
            "w-full max-w-4xl"
        )


# ============================================================
# APPLICATION
# ============================================================


ui.run(
    dark=True,
    title="Gateway Design Studio",
)