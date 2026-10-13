# TSP Route Optimizer

A Streamlit application that constructs a Traveling Salesperson Problem (TSP)
tour with Nearest Neighbor from multiple deterministic starting cities, then
improves the best initial tour using locally implemented 2-opt and relocate
moves. The optimization algorithms use only Python code in this project; no
optimization library is used.

## Run locally

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Use the built-in demo on the first visit or upload a dataset in the sidebar and
select **Solve route**.

## Dataset formats

- CSV with `x` and `y` columns, optionally with an `id`, `city`, `name`, or
  `node` column. Header names also accept `lon`/`longitude` and
  `lat`/`latitude`.
- Headerless CSV with either `x,y` or `id,x,y` columns.
- TSPLIB `.tsp` coordinate files declaring `EDGE_WEIGHT_TYPE: EUC_2D`.

CSV instances use Euclidean edge lengths. TSPLIB `EUC_2D` uses nearest-integer
edge weights as specified by that distance type. Each tour returns to its
starting city.

## Solver and displayed metrics

For repeatable multistart search, start cities are evenly distributed through
the input row order. The app selects the shortest Nearest Neighbor tour from
those starts, applies improving 2-opt reversals and single-city relocate moves
until neither move improves the route, and reports initial and final route
length, percentage improvement, and solver execution time. The route chart and
expanded route listing show the resulting cycle.

## Run tests

```powershell
python -m unittest discover -v
```

## Deploy to Streamlit Community Cloud

1. Push this project to a GitHub repository. Keep `app.py`, the `tsp/` package,
   `requirements.txt`, and `tests/` at the repository root.
2. Sign in at [share.streamlit.io](https://share.streamlit.io) with GitHub and
   grant access to the repository.
3. Choose **Create app**, select the repository and branch, and set the main
   file path to `app.py`.
4. Select **Deploy**. Community Cloud installs `requirements.txt` and launches
   the Streamlit app. No secrets or external services are required.
