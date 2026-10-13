import plotly.graph_objects as go
import streamlit as st

from tsp.io import parse_instance
from tsp.models import City, TspInstance
from tsp.solver import solve_tsp


_DEMO_INSTANCE = TspInstance(
    name="Built-in demo",
    cities=(
        City("A", 0, 0),
        City("B", 2, 6),
        City("C", 5, 3),
        City("D", 6, 8),
        City("E", 8, 1),
        City("F", 10, 5),
        City("G", 3, 10),
        City("H", 9, 10),
    ),
)

st.set_page_config(page_title="TSP Route Optimizer", page_icon=":world_map:", layout="wide")
st.title("Traveling Salesperson Problem")
st.write(
    "Build a nearest-neighbor tour from multiple starting cities, then improve it "
    "with self-implemented 2-opt and relocate moves."
)

with st.sidebar:
    st.header("Dataset")
    st.caption("Upload a coordinate CSV or a TSPLIB .tsp file using EUC_2D weights.")
    with st.form("solver_settings"):
        uploaded_file = st.file_uploader(
            "City coordinates",
            type=["csv", "tsp", "tsplib", "txt"],
            help="CSV columns may be id, x, y; x and y alone are also accepted.",
        )
        starts = st.number_input(
            "Nearest-neighbor starting points",
            min_value=1,
            max_value=50,
            value=12,
            step=1,
            help="Starts are spread deterministically through the input city order.",
        )
        submitted = st.form_submit_button("Solve route", type="primary")

if submitted:
    try:
        if uploaded_file is None:
            instance = _DEMO_INSTANCE
        else:
            content = uploaded_file.getvalue().decode("utf-8-sig")
            instance = parse_instance(uploaded_file.name, content)
        result = solve_tsp(
            instance.cities,
            requested_starts=int(starts),
            round_distances=instance.round_distances,
        )
        st.session_state["instance"] = instance
        st.session_state["result"] = result
    except (UnicodeDecodeError, ValueError) as error:
        st.error(f"Could not load or solve this dataset: {error}")
elif "result" not in st.session_state:
    demo_result = solve_tsp(_DEMO_INSTANCE.cities, requested_starts=8)
    st.session_state["instance"] = _DEMO_INSTANCE
    st.session_state["result"] = demo_result

if "result" in st.session_state:
    instance = st.session_state["instance"]
    result = st.session_state["result"]
    st.caption(
        f"Showing **{instance.name}** · {len(instance.cities)} cities · "
        f"{instance.source_format} · {result.starts_used} starting points"
    )

    first, second, third, fourth = st.columns(4)
    first.metric("Best initial NN distance", f"{result.initial_distance:,.2f}")
    second.metric(
        "Optimized distance",
        f"{result.final_distance:,.2f}",
        delta=f"{result.final_distance - result.initial_distance:,.2f}",
        delta_color="inverse",
    )
    third.metric("Improvement", f"{result.improvement_percent:.2f}%")
    fourth.metric("Execution time", f"{result.elapsed_seconds:.4f} s")

    cities_by_index = instance.cities
    ordered_route = list(result.route) + [result.route[0]]
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=[cities_by_index[index].x for index in ordered_route],
            y=[cities_by_index[index].y for index in ordered_route],
            mode="lines",
            name="Tour",
            line={"color": "#2474d2", "width": 2},
            hoverinfo="skip",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=[city.x for city in instance.cities],
            y=[city.y for city in instance.cities],
            mode="markers",
            name="Cities",
            marker={"color": "#e4572e", "size": 8},
            text=[city.identifier for city in instance.cities],
            customdata=list(range(1, len(instance.cities) + 1)),
            hovertemplate="City %{text}<br>Input row %{customdata}<extra></extra>",
        )
    )
    figure.update_layout(
        title="Optimized closed tour",
        xaxis_title="X coordinate",
        yaxis_title="Y coordinate",
        yaxis={"scaleanchor": "x", "scaleratio": 1},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1},
        margin={"l": 20, "r": 20, "t": 60, "b": 20},
    )
    st.plotly_chart(figure, width="stretch")

    with st.expander("Route details"):
        route_labels = [instance.cities[index].identifier for index in result.route]
        st.write(" → ".join(route_labels + [route_labels[0]]))
        st.caption(
            "TSPLIB EUC_2D distances use nearest-integer edge weights; uploaded CSV "
            "coordinates use unrounded Euclidean distances."
        )
