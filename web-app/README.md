# LIF Neuron Web App

An interactive web app for teaching Leaky Integrate-and-Fire neuron dynamics.
It wraps the shared [`lif_core`](../lif_core) simulation engine (extracted from
`LIF Model.ipynb`, which stays untouched) in a zero-build Plotly frontend.

The frontend ships in two interchangeable modes:

- **Client-side (default / how it's deployed):** the simulation runs entirely in
  the browser via [`frontend/js/lif.js`](frontend/js/lif.js), a faithful
  JavaScript port of `lif_core`. No backend required — this is what gets
  published to **GitHub Pages**.
- **Backend mode:** a FastAPI REST API (`web-app/backend`) that imports the
  Python `lif_core` engine. Kept for local use and as the path to server-side
  hosting / heavier future models. To use it, load `js/api.js` instead of
  `js/lif.js` in `index.html`.

```
web-app/
├── backend/            FastAPI app (REST API + serves the frontend)
│   └── app/
│       ├── main.py             app, CORS, static mount, router include
│       ├── config.py           defaults + guard rails (max steps, etc.)
│       ├── schemas.py          Pydantic request/response models
│       └── routers/simulation.py   /api/run_simulation, /api/defaults, /api/health
└── frontend/           index.html + css/ + js/ (Plotly via CDN)
    └── js/lif.js       client-side engine (JS port of lif_core)
```

## Deployed site (GitHub Pages)

The static frontend is published by `.github/workflows/pages.yml` on every push
to `main` that touches `web-app/frontend/`.

**One-time setup:** in the repo on GitHub, go to **Settings → Pages → Build and
deployment → Source** and select **GitHub Actions**. After the next push (or a
manual run of the "Deploy frontend to GitHub Pages" workflow), the site is live
at <https://stridasaurus.github.io/LIF-project/>.

Because it's pure client-side, it stays up with no server and at no cost.

## Run the static site locally (no Python)

Just serve the `frontend/` folder with any static server, e.g.:

```bash
cd web-app/frontend && python3 -m http.server 8000   # then open http://localhost:8000
```

## Run the backend (optional, for backend mode)

> Use a **dedicated virtualenv** for the backend — *not* the conda `sandbox-env`.
> The repo's `.githooks/pre-commit` regenerates `environment.yml` from
> `sandbox-env`, so installing FastAPI there would leak web deps into the
> notebook environment.

```bash
# from the repo root
python -m venv web-app/backend/.venv
source web-app/backend/.venv/bin/activate      # Windows: web-app\backend\.venv\Scripts\activate

cd web-app/backend
pip install -r requirements.txt                # also installs -e ../../lif_core
uvicorn app.main:app --reload --port 8000
```

> Run `pip install` from `web-app/backend` so the `-e ../../lif_core` editable
> path (which pip resolves relative to the current directory) points at the
> repo-root engine package.

Open <http://localhost:8000>. The frontend is served by the same process, so
there is no separate server and no CORS setup. Interactive API docs live at
<http://localhost:8000/docs>.

### Alternative: serve the frontend separately

If you prefer to develop the frontend with its own static server (e.g. VS Code
Live Server on port 5500), the backend already allows that origin via CORS
(`app/config.py`). Point the frontend's `API_BASE` (in `js/api.js`) at
`http://localhost:8000` and run the backend as above.

## Using the app

Enter expressions in terms of `t` (ms); `math.*` and `np.*` are available:

- `I(t)`: `1.5`, `1.5 + math.sin(t / 10)`, `np.where(t > 100, 3.0, 0.5)`
- `V_thr(t)`: `-55`
- `R(t)`: `10`

Leave a field blank to fall back to its default. Click **Run Simulation** to
plot the membrane potential, threshold, spike markers, and input current.

## Tests

```bash
# engine
pip install -e lif_core[test]
pytest lif_core/tests

# backend (from web-app/backend, with deps installed)
pytest tests
```

## API

| Method | Path                  | Purpose                                  |
| ------ | --------------------- | ---------------------------------------- |
| POST   | `/api/run_simulation` | Run a simulation; returns traces + spikes |
| GET    | `/api/defaults`       | Default form values (single source)      |
| GET    | `/api/health`         | Liveness probe                           |

`POST /api/run_simulation` body:

```json
{
  "I": "1.5 + math.sin(t / 10)",
  "V_thr": "-55",
  "R": "10",
  "simulation_time": 200,
  "dt": 0.1
}
```

Errors: invalid/unsafe expressions return **400** with a readable `detail`;
oversized runs return **422**.

## Extending

- **New model** (Izhikevich, Hodgkin-Huxley): subclass `NeuronModel` in
  `lif_core/src/lif_core/models.py`, then add a `model` field to
  `SimulationRequest` and dispatch in the router.
- **Networks/synapses**: add `lif_core/src/lif_core/network.py` and a
  `/api/run_network` route. The frontend stays decoupled behind the REST contract.
- **Richer plots** (rasters, phase plots): the Plotly layout in
  `frontend/js/plot.js` is already split into linked subplots.
