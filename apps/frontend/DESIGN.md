# Design: Darya dashboard

The full design system is TBD. Until it's written, follow the rules below.

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
