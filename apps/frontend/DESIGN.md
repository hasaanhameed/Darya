# Design: Darya dashboard

Read this before any UI work. Part 1 is the design system: what to use. Part 2 is the list of things never to use. Stack choices are in `docs/DECISIONS.md` (ADR-010 to ADR-016).

# Part 1: Design system

## Who it is for
A duty officer at FFD, WAPDA or a provincial irrigation department, at a desk during the monsoon. They need to see in seconds which reach is in trouble, how bad it is, how sure the forecast is, and when it will happen.
It should feel **calm and exact, like a control-room schematic**.

**The idea:** water is blue, danger is warm. The frame around the map takes its color from the river (deep water for the header, shallow water for the rail), so the page is never a sheet of white.

## Signature elements
- **River schematic.** The left rail draws the river system as a vertical line diagram, with upstream at the top. Nodes are stations on the line, and each reach segment is colored by its risk.
  - This is the style of diagram IRSA and WAPDA use.
  - It works as navigation, and as a keyboard- and screen-reader-friendly alternative to the map.
- **Threshold staff.** A vertical bar modeled on the painted gauge staff at a barrage.
  - It shows the site's FFD flood limits (from `docs/DATA.md`).
  - A solid marker shows the current flow, and a hollow marker shows the forecast peak.

## Color tokens
Defined once in `src/app/globals.css` (Tailwind `@theme`). Never write raw hex in components.

| Token | Hex | Use |
|---|---|---|
| `silt` | `#F1F2EF` | Page background |
| `sheet` | `#FAFAF8` | Panels, tables, charts |
| `ink` | `#1B2126` | Primary text (14.5:1 on silt) |
| `ink-2` | `#46515A` | Labels, secondary text (7.2:1) |
| `ink-3` | `#5F6B74` | Timestamps and metadata (4.9:1, the lowest allowed for text) |
| `channel` | `#1F66A3` | **Water only**: river lines at Normal, water extent, focus ring |
| `rule` | `rgba(27,33,38,0.12)` | Hairline borders |
| `rule-strong` | `rgba(27,33,38,0.24)` | Input outlines, the schematic line |
| `deep` | `#15324A` | Header and disclaimer line, count chips |
| `deep-ink` / `deep-ink-2` | `#E8EFF4` / `#B4C6D4` | Text on `deep` |
| `shallows` | `#E3EBF0` | Left rail, reach panel header |
| `shallows-2` / `shallows-3` | `#D3DFE7` / `#C6D5E0` | Section header bars, hover. Only `ink` and `ink-2` text on these |
| `map-land` / `map-water` | `#E7E5DA` / `#B9D2E4` | Basemap tint (copied as hex in `RiverMap`) |

### Risk scale (PMD-FFD categories)
| Normal | Low | Medium | High | Very High | Exceptional |
|---|---|---|---|---|---|
| `#1F66A3` | `#DC9130` | `#D07226` | `#BC561E` | `#9A3B18` | `#672514` |

- **Normal** uses the river color, because a normal river is just water.
- **Low to Exceptional** is one warm ramp that gets darker as the risk rises. It passed the dataviz ordinal check on both `silt` and `sheet`: lightness steps evenly, it stays in one hue family, and the light end is above 2:1.
- Normal and Low stay clearly apart under colorblind simulation (ΔE 25).
- **Risk color is never shown without a way to read it.** Lists (alerts, schematic) show a color square or segment and rely on the key on the map; the category name is always in the accessible label and the hover title. The reach panel names the category in text.
- No traffic-light green/yellow/red.

## Type
- **Font:** IBM Plex Sans (ADR-014), with weights 400, 500 and 600. There is no second family, and monospace is never used for data.
- **Scale:** ratio 1.2. Use only these sizes.

| px | Use |
|---|---|
| 12 | Timestamps, units, captions |
| 14 | Body and table text |
| 17 | Panel titles |
| 20 | Page titles |
| 24 | Major page headings |
| 29 | The single focal value on a screen (e.g. a reach's risk level) |

- **Hierarchy** comes from weight and color before size:
  - Values: 600, `ink`
  - Labels: 500, `ink-2`
  - Metadata: 400, `ink-3`
- **Numbers:** tabular figures (`tabular-nums`) in tables, lists and charts. Units follow the value in smaller `ink-2` text, e.g. **312,400** cusecs. Show flow as "cusecs" (the word WAPDA and FFD use), never "cfs". Field names in code keep `_cfs`.
- **Text:** sentence case everywhere. No ALL-CAPS labels.

## Space, depth, corners, motion
- **Spacing:** 4px base.
  - 8–12px inside controls
  - 16px panel padding
  - 24px between groups
- **Depth:** borders only. Surfaces are flat. A popover gets one hairline ring and no soft shadow.
- **Corners:** 4px on controls and chips, 6px on panels, 8px on dialogs.
- **Motion:**
  - Only for data or map updates and for skeletons.
  - Under 200ms, using `cubic-bezier(0.23, 1, 0.32, 1)`.
  - Off when the user has reduced motion enabled.
  - No hover animation. A hover changes color only.
- **Focus:** a 2px `channel` outline with a 2px offset on every interactive element.

## Layout
- **`/` (map dashboard):**
  - Header (48px), then a disclaimer line.
  - Left rail (272px by default, drag or arrow keys to resize from 220 to 480px, remembered per browser): collapsible "Active alerts" and "River system" sections. Each river in the schematic collapses too, and shows its highest risk when closed.
  - The key (risk colors with counts, station shapes, what a cusec is) sits in a collapsible box at the top-left of the map.
  - The map fills the rest of the screen. The time slider runs along the bottom.
- **Reach panel:** 360px wide, over the right side of the map.
  - The risk level is the focal point (29px/600, at the top).
  - Then the reasons, current values with their update times, the threshold staff, the chart, and the sources.
- **Tables (e.g. `/alerts`):** plain rows separated by hairlines. Show the category as a small color square plus its name. Rows have no left stripe and are not cards.
- **Alignment:** everything is left-aligned. Numbers in table columns are right-aligned.

## Map
- **Basemap:** OpenFreeMap Positron, tinted with `map-land` and `map-water`, with place names faded. Rivers and risk colors are the only strong color on the map.
- **Reaches:** lines colored by risk, 3px wide (4px when selected). An invisible 16px line on top gives a bigger click target.
- **Node markers:** small custom shapes by type, in `ink` on `sheet`.

| Node type | Shape |
|---|---|
| Dam | Square |
| Barrage / headworks | Diamond |
| Gauge | Circle |
| Confluence | Small dot |

## Copy
- Use plain, specific sentences.
- Times are shown in PKT and labeled "PKT".
- Every value has its unit.
- Alerts and risk text follow the research-prototype framing and never sound like an official warning.

# Part 2: Never use these

## Avoid the "vibe-coded" look
Darya should look like a serious tool built for flood agencies, not a generic AI-generated template. Don't use any of the following unless the team explicitly decides otherwise.

**Color**
- No harsh or showy gradients, and no rainbow coloring.
- No neon colors, no basic pastel palettes, and no purple-on-black theme.
- No pure white (`#FFFFFF`) page background. Use a slightly tinted neutral instead.
- Use color only where it carries meaning, such as risk levels or water on the map. Never use it as decoration.

**Decoration and effects**
- No radial glow orbs and no dot-grid backgrounds.
- No "liquid glass" or glassmorphism panels, and no heavy drop shadows.
- No overly soft, pill-like corner radius everywhere. Keep corners small and consistent.
- No colored stripe down the left edge of cards or alerts.

**Layout**
- No bento grids.
- No row of three identical feature cards.
- No fake terminal or code windows used as decoration.

**Icons and type**
- No emojis in the UI.
- No sparkle ✨ icons, and no animated arrows.
- Don't just use the default Lucide icon set as-is. Choose icons deliberately and keep them consistent.
- No default "AI template" fonts: Inter, Geist or Space Grotesk.

**Motion**
- No hover animations on everything. Use motion only where it helps the user, e.g. showing that data is loading or that the map has changed.

**Copy and text**
- No em dashes (—) in UI text.
- No "It's not X, it's Y" style phrasing.
- No checkmark-bullet lists of features.
- Write plainly and specifically.

**Content and trust**
- No fake testimonials, no made-up numbers, and no placeholder "real-time" claims. Show only real data and real sources.
- No generic three-tier pricing section.
- **Do** show the real product, i.e. the actual map and data, rather than mockups.
- **Do** use skeleton loaders while data is loading, never blank screens or bare spinners.
- **Do** include Terms of Use and a Privacy Policy before any public release.
