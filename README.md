# Darya

**A satellite-driven digital twin for real-time flood monitoring and prediction of Pakistan's rivers.**
*Darya* (دریا) is Urdu for "river". 

## Why
- Pakistan's river data is spread across agencies such as WAPDA, PMD-FFD, SUPARCO and IRSA. Each source updates at a different rate and covers a different part of the basin.
- Satellite imagery, gauge readings, rainfall and history are rarely combined into one view that shows the present and also looks ahead.
- Decision-makers cannot easily answer three questions:
  - What is happening now?
  - Where is water spreading?
  - What will happen downstream next?

## What Darya does
**Observe → Understand → Represent → Predict → Warn → Visualize**

| Step | What happens |
|---|---|
| Observe | Collect satellite (Sentinel-1/2), rainfall (GPM) and river data (gauges, dams, barrages) on a schedule. |
| Understand | Clean the data and detect surface water in Sentinel-1 radar images. |
| Represent | Keep a live, versioned state for every river reach. This is the **digital twin**. |
| Predict | Forecast river flow or level 1–3 days ahead. A graph neural network is compared against simple baselines. |
| Warn | Turn forecasts into risk levels. Each level comes with its reasons and an uncertainty range. |
| Visualize | Show everything on an interactive web map with a time slider and alerts. |

## Prototype scope
**Rivers covered** (about two dozen dam, barrage and gauge nodes):
- The Indus from Tarbela to Kotri
- The Kabul below Nowshera
- The Jhelum below Mangla
- The Chenab, Ravi and Sutlej through Punjab down to Panjnad

**Evaluation:** the 2022 and 2025 flood seasons are held out for testing.

**Out of scope:** urban flooding, small-stream flash floods, glacial lake outburst floods (GLOFs), and issuing official warnings.

## Stack
| | |
|---|---|
| **Confirmed** | FastAPI (Python) backend, Next.js frontend, PostgreSQL |
| **Planned** | PostGIS, PyTorch + PyTorch Geometric, Rasterio/GDAL/GeoPandas, MapLibre map, Docker Compose |

Decisions are tracked in [docs/DECISIONS.md](docs/DECISIONS.md).

## Repository layout
```
app/
  backend/     FastAPI service: ingestion, twin, forecasting, risk, API
  frontend/    Next.js dashboard
data/          raw and derived data (git-ignored; see docs/DATA.md)
docs/          project documentation
```

## Docs
| File | Read it when... |
|---|---|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | you need the big picture: components, core concepts, invariants |
| [docs/FLOW.md](docs/FLOW.md) | you want to know how data and operations move through the system |
| [docs/DATA.md](docs/DATA.md) | you work with any data source (including the raw WAPDA files) |
| [docs/DECISIONS.md](docs/DECISIONS.md) | you make or question a technical choice |
| [docs/PROGRESS.md](docs/PROGRESS.md) | you want to see where the project stands |
| [app/backend/CLAUDE.md](app/backend/CLAUDE.md) | you work on the backend |
| [app/frontend/DESIGN.md](app/frontend/DESIGN.md) | you work on the dashboard UI |

## Getting started
The code is not scaffolded yet. Setup steps will be added here.

Raw data is **not** in git. Get it from the team drive and place it under `data/`. For example, the WAPDA archives go in `data/wapda/`. See [docs/DATA.md](docs/DATA.md).

## Team
| | |
|---|---|
| Students | M. Ali Mubashir, Rohail Najmi, Hasaan Hameed |
| Advisor | Dr. Ayesha Maqbool |
| School | School of Electrical Engineering and Computer Science, NUST, Islamabad |

> Darya is a research prototype. It supports the agencies responsible for floods. It does **not** issue official warnings.
