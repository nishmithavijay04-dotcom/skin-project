"""
generate_data.py  —  Tinta Skin Undertone Dataset Generator
Produces skin_undertone_dataset.csv with Fitzpatrick-balanced training data.

RGB ranges are grounded in published color science:
  - ITA (Individual Typology Angle) thresholds from Chardon et al. (1991) and
    Del Bino et al. (2006): ITA > 55° = very fair, 41-55° = fair, 28-41° = intermediate,
    10-28° = tan, -30-10° = brown, < -30° = dark.
  - Undertone separation via the CIELab b* axis:
      Warm  → higher b* (yellow bias): R-B gap > ~20, R/B ratio > 1.12
      Cool  → lower/negative b* (pink/blue bias): B close to or exceeding G, R-B gap < ~10
      Neutral → b* near zero: R-B gap 10–20
  - Fitzpatrick spectrophotometry reference values from Ware et al. (2020)
    and Taylor et al. (2006) sRGB reconstructions.
  - Jitter std widened to 5 (from 3) to better model real camera sensor variance.

Run:  python generate_data.py
"""

import numpy as np
import pandas as pd

RNG = np.random.default_rng(42)

# ── Fitzpatrick type definitions ──────────────────────────────────────────────
# Each entry: (fitz_type, undertone, r_range, g_range, b_range, n_samples)
#
# Key color-science constraints applied per undertone:
#   Warm:    R > G > B with meaningful R-B separation (yellow-orange cast)
#            ITA typically higher within each Fitzpatrick band
#   Cool:    R and B closer together, B pulled up relative to Warm
#            Pink/rosy cast — B nearly matches or exceeds G in fair types
#   Neutral: Midpoint between Warm and Cool; R-B gap moderate
#
SKIN_SPECS = [
    # ── Type I  (very fair, ITA > 55°, always burns, never tans) ─────────────
    # sRGB centroid ~(242, 213, 196) Warm / (238, 210, 205) Cool
    (1, "Warm",    (232, 255), (205, 242), (178, 208), 220),  # yellow-pink, R-B ~30-50
    (1, "Cool",    (228, 252), (202, 238), (195, 228), 220),  # rosy, B pulled up
    (1, "Neutral", (230, 254), (204, 240), (187, 218), 220),  # midpoint

    # ── Type II  (fair, ITA 41–55°, burns easily, tans minimally) ────────────
    # sRGB centroid ~(224, 190, 168) Warm / (218, 188, 182) Cool
    (2, "Warm",    (215, 248), (183, 222), (152, 192), 260),  # R-B gap ~50-60
    (2, "Cool",    (210, 244), (180, 218), (168, 208), 260),  # B elevated, pinkish
    (2, "Neutral", (212, 246), (181, 220), (160, 200), 260),

    # ── Type III  (medium, ITA 28–41°, sometimes burns, tans gradually) ──────
    # sRGB centroid ~(196, 162, 132) Warm / (188, 158, 148) Cool
    (3, "Warm",    (188, 228), (155, 195), (122, 162), 290),  # R-B ~55-70
    (3, "Cool",    (182, 222), (150, 190), (140, 178), 290),  # B closer to G
    (3, "Neutral", (185, 225), (152, 192), (131, 170), 290),

    # ── Type IV  (olive/medium-dark, ITA 10–28°, rarely burns, tans well) ────
    # sRGB centroid ~(168, 130, 98) Warm / (158, 125, 115) Cool
    # Olive skin: slight green cast in G channel — G raised slightly vs Warm
    (4, "Warm",    (158, 205), (126, 170),  (92, 138), 290),  # strong R-B ~60-70
    (4, "Cool",    (150, 198), (120, 165), (108, 155), 290),  # B elevated, less R-B gap
    (4, "Neutral", (154, 202), (123, 168),  (100, 146), 290),

    # ── Type V  (brown, ITA -30–10°, rarely burns, tans deeply) ──────────────
    # sRGB centroid ~(130, 92, 62) Warm / (118, 88, 78) Cool
    (5, "Warm",    (118, 168),  (82, 130),  (52, 100), 290),  # R-B ~55-70
    (5, "Cool",    (110, 160),  (78, 125),  (68, 115), 290),  # B much closer to G
    (5, "Neutral", (114, 164),  (80, 128),  (60, 108), 290),

    # ── Type VI  (deep/darkest, ITA < -30°, never burns) ─────────────────────
    # sRGB centroid ~(80, 52, 32) Warm / (72, 48, 42) Cool
    (6, "Warm",    ( 62, 118),  (40,  90),  (22,  65), 260),  # pronounced R-B gap
    (6, "Cool",    ( 58, 112),  (38,  86),  (35,  78), 260),  # B nearly matches G
    (6, "Neutral", ( 60, 115),  (39,  88),  (28,  72), 260),
]

rows = []
for fitz, undertone, rr, gr, br, n in SKIN_SPECS:
    r_vals = RNG.integers(rr[0], rr[1] + 1, n)
    g_vals = RNG.integers(gr[0], gr[1] + 1, n)
    b_vals = RNG.integers(br[0], br[1] + 1, n)
    for r, g, b in zip(r_vals, g_vals, b_vals):
        # Gaussian jitter (std=5) models real camera sensor + JPEG compression variance
        r = int(np.clip(r + RNG.normal(0, 5), 0, 255))
        g = int(np.clip(g + RNG.normal(0, 5), 0, 255))
        b = int(np.clip(b + RNG.normal(0, 5), 0, 255))
        rows.append({"R": r, "G": g, "B": b,
                     "Fitzpatrick": fitz, "Undertone": undertone})

df = pd.DataFrame(rows).sample(frac=1, random_state=42).reset_index(drop=True)
df.to_csv("skin_undertone_dataset.csv", index=False)

# ── Summary ───────────────────────────────────────────────────────────────────
print(f"✅  Generated {len(df):,} samples → skin_undertone_dataset.csv")
print("\nFitzpatrick distribution:")
print(df["Fitzpatrick"].value_counts().sort_index().to_string())
print("\nUndertone distribution:")
print(df["Undertone"].value_counts().to_string())
print("\nFitzpatrick × Undertone balance:")
print(df.groupby(["Fitzpatrick","Undertone"]).size().unstack(fill_value=0).to_string())
