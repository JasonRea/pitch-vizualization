from fetch_data import *
import os
import pandas as pd
import numpy as np
from scipy.optimize import brentq
from manim import *
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.patheffects as pe
from matplotlib.patches import FancyBboxPatch, Circle
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from PIL import Image as PILImage
import requests
from io import BytesIO

# Borrowed from TJstats pitch color palette
PITCH_COLORS = {
    "FF": "#FF007D",  # 4-Seam Fastball
    "FA": "#FF007D",  # Fastball
    "SI": "#98165D",  # Sinker
    "FC": "#BE5FA0",  # Cutter
    "CH": "#F79E70",  # Changeup
    "FS": "#FE6100",  # Splitter
    "SC": "#F08223",  # Screwball
    "FO": "#FFB000",  # Forkball
    "SL": "#67E18D",  # Slider
    "ST": "#1BB999",  # Sweeper
    "SV": "#376748",  # Slurve
    "KC": "#311D8B",  # Knuckle Curve
    "CU": "#3025CE",  # Curveball
    "CS": "#274BFC",  # Slow Curve
    "EP": "#648FFF",  # Eephus
    "KN": "#867A08",  # Knuckleball
    "PO": "#472C30",  # Pitch Out
    "UN": "#9C8975",  # Unknown
}

# TODO Variable strike zone size dependent on batter height
# TODO Other POVs (not sure exactly but probably as LHB, RHB, pitcher)
# TODO Specify specific pitch types, vs rhb, lhb, vs particular batters
# TODO Setup s3 bucket + github actions (check w/ github student dev pack)


def position(
    t: float,
    x0: float, y0: float, z0: float,
    vx0: float, vy0: float, vz0: float,
    ax: float, ay: float, az: float,
) -> np.ndarray:
    x = x0 + vx0 * t + 0.5 * ax * t ** 2
    y = y0 + vy0 * t + 0.5 * ay * t ** 2
    z = z0 + vz0 * t + 0.5 * az * t ** 2
    return np.array([x, y, z])

class VizualizationBuilder:
    """
    Builder for Manim pitch trajectory visualizations.

    Usage:
        scene_class = (
            VizualizationBuilder()
            .load_pitches(date="2026-02-24", pitcher="Ranger Suarez")
            .buildm_pitches()
        )
        VizualizationBuilder.render(scene_class, quality="high_quality", filename=f"{date} {pitcher}")
    """

    # Manim units per foot
    SCALE: float = 6 / 10

    def __init__(self):
        self._pitches: list = []
        self._end_points: list = []
        self._end_times: list = []
        self._colors: list = []
        self._axes: ThreeDAxes | None = None

    # ------------------------------------------------------------------
    # Builder steps
    # ------------------------------------------------------------------

    def load_pitches(self, date: str, pitcher: str) -> "VizualizationBuilder":
        """Fetch Statcast data and build the parametric curves"""

        self._pitches.clear()
        self._end_points.clear()
        self._end_times.clear()
        self._colors.clear()

        df = pitch_data(start_dt=date, pitcher=pitcher)

        # Brief Data Cleaning
        columns_to_keep = [
            "vx0", "vy0", "vz0",
            "ax", "ay", "az",
            "release_pos_x", "release_pos_z", "release_pos_y",
            "pitch_type",
        ]
        df = df[columns_to_keep].dropna()

        self._axes = ThreeDAxes(
            x_range=[-5, 5, 1],
            y_range=[0, 60.5, 10],
            z_range=[0, 20, 1],
            x_length=self.SCALE * 10,
            y_length=self.SCALE * 60.5,
            z_length=self.SCALE * 20,
        )

        for _, row in df.iterrows():
            x0  = float(row["release_pos_x"])
            y0  = float(row["release_pos_y"])
            z0  = float(row["release_pos_z"])
            vx0 = float(row["vx0"])
            vy0 = float(row["vy0"])
            vz0 = float(row["vz0"])
            ax  = float(row["ax"])
            ay  = float(row["ay"])
            az  = float(row["az"])
            pitch_type = str(row["pitch_type"])

            t_end = brentq(
                lambda t: position(t, x0, y0, z0, vx0, vy0, vz0, ax, ay, az)[1],
                0, 1.0,
            )

            pitch = ParametricFunction(
                lambda t,
                    x0=x0, y0=y0, z0=z0,
                    vx0=vx0, vy0=vy0, vz0=vz0,
                    ax=ax, ay=ay, az=az,
                    t_end=t_end:
                    self._axes.c2p(*position(t * t_end, x0, y0, z0, vx0, vy0, vz0, ax, ay, az)),
                t_range=[0, 1],
                stroke_width=2,
                color=PITCH_COLORS.get(pitch_type, PITCH_COLORS["UN"]),
            )

            self._pitches.append(pitch)
            self._end_points.append(
                self._axes.c2p(*position(t_end, x0, y0, z0, vx0, vy0, vz0, ax, ay, az))
            )
            self._end_times.append(t_end)
            self._colors.append(PITCH_COLORS.get(pitch_type, PITCH_COLORS["UN"]))

        return self

    def buildm_pitches(self) -> type[ThreeDScene]:
        """Return a Manim ThreeDScene class of pitches ready to be rendered."""

        if self._axes is None:
            raise RuntimeError("Call load_pitches() before build().")

        axes       = self._axes
        scale      = self.SCALE
        pitches    = list(self._pitches)
        end_points = list(self._end_points)
        end_times  = list(self._end_times)
        colors     = list(self._colors)

        class PitchTrajectory(ThreeDScene):
            def construct(self):

                # Background grid
                grid = NumberPlane(
                    x_range=[-5, 5, 1],
                    y_range=[0, 20, 1],
                    x_length=scale * 10,
                    y_length=scale * 20,
                    background_line_style={
                        "stroke_color": BLUE,
                        "stroke_width": 1,
                        "stroke_opacity": 0.4,
                    },
                    axis_config={"stroke_opacity": 0},
                )
                grid.move_to(axes.c2p(0, 0, 10))
                grid.rotate(90 * DEGREES, axis=RIGHT)

                # Strike Zone Metrics
                sz_width  = 17 / 12          # in -> ft
                sz_bottom = 12 / 12          
                sz_top    = (12 + 20) / 12   
                sz_mid_z  = (sz_bottom + sz_top) / 2

                strike_zone = Rectangle(
                    width=sz_width * scale,
                    height=(sz_top - sz_bottom) * scale,
                )
                strike_zone.move_to(axes.c2p(0, 0, sz_mid_z))
                strike_zone.rotate(90 * DEGREES, axis=RIGHT)
                strike_zone.set_stroke(WHITE, 4)
                strike_zone.set_fill(opacity=0)

                # Camera (catcher's POV)
                self.set_camera_orientation(
                    phi=90 * DEGREES,
                    theta=-90 * DEGREES,
                    zoom=0.2,
                    frame_center=axes.c2p(0, 30, 3),
                )

                self.add(grid, strike_zone)

                # Animate each pitch
                for pitch, end_point, t_end, color in zip(
                    pitches, end_points, end_times, colors
                ):
                    end_dot = Dot3D(point=end_point, radius=0.05, color=color)
                    self.play(Create(pitch), run_time=t_end)
                    self.add(end_dot)
                    self.wait()

        return PitchTrajectory
    
    # TODO add background coloring for other percentiles
    def buildp_high_heat(self, date: str):
        '''
        Plots the High Heat graphic.
        '''

        df = daily_pitches(date)
        df = high_heat_filter(df)

        if df.empty:
            raise RuntimeError(f"No pitch data found for {date}.")

        pitcher_ids = df["pitcher"].astype(int).tolist()
        n = len(pitcher_ids)

        # Fetch assets
        headshots: list[PILImage.Image | None] = [None] * n
        bios:      list[tuple | None]          = [None] * n

        def _fetch_hs(idx, pid):
            try:    headshots[idx] = player_headshot(str(pid))
            except: pass

        def _fetch_bio(idx, pid):
            try:    bios[idx] = player_bio(str(pid))
            except: pass

        with ThreadPoolExecutor(max_workers=n * 2) as ex:
            futs = (
                [ex.submit(_fetch_hs,  i, pid) for i, pid in enumerate(pitcher_ids)] +
                [ex.submit(_fetch_bio, i, pid) for i, pid in enumerate(pitcher_ids)]
            )
            for f in as_completed(futs):
                f.result()

        # PALETTE (Some are not in use currently)
        BORDER   = "#e0e0e0"
        DARK     = "#1a1a1a"
        ACCENT   = "#DA2626"
        SUBTEXT  = "#666666"
        HDR_BG   = "#1a1a1a"

        COL_LABELS = ["Pitch", "Velo (mph)", "Spin (rpm)", "HB (in)", "iVB (in)"]
        N_COLS     = len(COL_LABELS)

        # Figure
        # Rows: title | col-headers | n player rows | footer
        ROW_H      = 1.3          # inches per player row
        TITLE_H    = 0.8
        HDR_H      = 0.40
        FOOTER_H   = 0.30
        FIG_H      = TITLE_H + HDR_H + n * ROW_H + FOOTER_H
        FIG_W      = 7.2

        fig = plt.figure(figsize=(FIG_W, FIG_H), facecolor="white", dpi=150)

        height_ratios = [TITLE_H, HDR_H] + [ROW_H] * n + [FOOTER_H]
        gs = gridspec.GridSpec(
            2 + n + 1, 1,
            figure=fig,
            height_ratios=height_ratios,
            hspace=0,
            left=0.03, right=0.97,
            top=1.0, bottom=0.0,
        )

        # Title

        # Fire emoji
        try:
            _emoji_resp = requests.get("https://em-content.zobj.net/source/apple/419/fire_1f525.png")
            _emoji_img  = PILImage.open(BytesIO(_emoji_resp.content)).convert("RGBA")
            _emoji_arr  = np.array(_emoji_img)
        except Exception:
            _emoji_arr = None

        ax_title = fig.add_subplot(gs[0])
        ax_title.axis("off")
        ax_title.text(0.5, 0.70, "High Heat",
                      transform=ax_title.transAxes, ha="center", va="center",
                      fontsize=22, fontweight="bold", color=DARK)
        ax_title.text(0.5, 0.22, f"Top 5 Hardest Pitches  ·  {date}",
                      transform=ax_title.transAxes, ha="center", va="center",
                      fontsize=11, color=SUBTEXT)
        
        if _emoji_arr is not None:
            for x_pos in (0.20, 0.76):
                ax_e = ax_title.inset_axes([x_pos, 0.38, 0.07, 0.58])
                ax_e.imshow(_emoji_arr)
                ax_e.axis("off")

        # ── Column header row ─────────────────────────────────────────
        # Left pane width matches headshot pane below (20% of figure width)
        HS_FRAC = 0.20
        ax_hdr = fig.add_subplot(gs[1])
        ax_hdr.set_xlim(0, 1)
        ax_hdr.set_ylim(0, 1)
        ax_hdr.axis("off")

        col_xs = [HS_FRAC + (1 - HS_FRAC) * (j + 0.5) / N_COLS for j in range(N_COLS)]
        for j, (label, cx) in enumerate(zip(COL_LABELS, col_xs)):
            ax_hdr.text(cx, 0.5, label,
                        transform=ax_hdr.transAxes,
                        ha="center", va="center",
                        fontsize=10, fontweight="bold", color=DARK,
                        linespacing=1.2, zorder=2)

        # Divider line below header
        ax_hdr.axhline(0, color=DARK, linewidth=1, xmin=0, xmax=1)

        # Player rows
        for i in range(n):
            row_bg = BORDER

            gs_row = gridspec.GridSpecFromSubplotSpec(
                1, 2,
                subplot_spec=gs[2 + i],
                width_ratios=[HS_FRAC, 1 - HS_FRAC],
                wspace=0,
            )

            # Headshot and Name on the left
            ax_hs = fig.add_subplot(gs_row[0])
            ax_hs.set_facecolor(row_bg)
            ax_hs.set_xlim(0, 1)
            ax_hs.set_ylim(0, 1)
            ax_hs.axis("off")

            hs_img = headshots[i]
            name = bios[i][0] if bios[i] else "Unknown"
            if hs_img is not None:
                inset = ax_hs.inset_axes([0.10, 0.20, 0.80, 0.75])
                inset.imshow(np.array(hs_img.convert("RGBA")))
                inset.axis("off")
            else:
                circle = plt.Circle((0.50, 0.60), 0.30,
                                    color="#cccccc", transform=ax_hs.transAxes,
                                    zorder=2)
                ax_hs.add_patch(circle)

            ax_hs.text(0.50, 0.10, name,
                       transform=ax_hs.transAxes,
                       ha="center", va="center",
                       fontsize=8, color=DARK)

            # Bottom divider
            ax_hs.axhline(0, color=DARK, linewidth=0.8)

            # On the right, single-row data tables
            ax_data = fig.add_subplot(gs_row[1])
            ax_data.set_facecolor(row_bg)
            ax_data.set_xlim(0, 1)
            ax_data.set_ylim(0, 1)
            ax_data.axis("off")

            pitch_type = df["pitch_type"].iloc[i]
            ptype = df["pitch_name"].iloc[i]
            velo  = df["release_speed"].iloc[i]
            spin  = df["release_spin_rate"].iloc[i]
            hb    = df["pfx_x"].iloc[i] * 12
            ivb   = df["pfx_z"].iloc[i] * 12

            pitch_bg = PITCH_COLORS.get(pitch_type, PITCH_COLORS["UN"])

            values = [
                ptype,
                f"{velo:.1f}",
                f"{int(spin):,}",
                f"{hb:+.1f}",
                f"{ivb:+.1f}",
            ]

            col_frac = 1 / N_COLS
            for j, val in enumerate(values):
                cx = (j + 0.5) * col_frac

                # Color box background + white text
                if j == 0:
                    pill = FancyBboxPatch(
                        (0.0, 0.30), col_frac, 0.40,
                        boxstyle="square,pad=0",
                        facecolor=pitch_bg, edgecolor="white",
                        transform=ax_data.transAxes, zorder=1, clip_on=False,
                    )
                    ax_data.add_patch(pill)
                    ax_data.text(cx, 0.50, val,
                                 transform=ax_data.transAxes,
                                 ha="center", va="center",
                                 fontsize=7.5, color="white", fontweight="bold",
                                 zorder=2)
                else:
                    color  = DARK
                    weight = "bold"  if j == 1 else "normal"
                    ax_data.text(cx, 0.50, val,
                                 transform=ax_data.transAxes,
                                 ha="center", va="center",
                                 fontsize=10, color=color, fontweight=weight)

            # Bottom divider
            ax_data.axhline(0, color=DARK, linewidth=0.8)

        #Footer
        ax_footer = fig.add_subplot(gs[2 + n])
        ax_footer.axis("off")
        ax_footer.axhline(1.0, color=DARK, linewidth=1.0)
        ax_footer.text(0.02, 0.45, "By: @baseballfornerds",
                       transform=ax_footer.transAxes,
                       ha="left", va="center",
                       fontsize=8, color=SUBTEXT, style="italic")
        ax_footer.text(0.98, 0.45, "Data: MLB  |  Images: MLB, ESPN",
                       transform=ax_footer.transAxes,
                       ha="right", va="center",
                       fontsize=8, color=SUBTEXT, style="italic")

        # Save
        output_dir = "media/images/plots"
        os.makedirs(output_dir, exist_ok=True)
        fig.savefig(fname=f"{output_dir}/high_heat_{date}.png",
                    bbox_inches="tight", dpi=150, facecolor="white")

        return fig

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    @staticmethod
    def render(
        scene: type[Scene],
        quality: str | None = None,
        filename: str | None = None,
    ) -> None:
        """
        Render a Manim scene class.

        Args:
            scene:    A Scene subclass (e.g. the return value of build()).
            quality:  One of "low_quality", "medium_quality", "high_quality",
                      "fourk_quality". Defaults to Manim's current config.
            filename: Output filename (without extension).
        """
        if quality:
            config.quality = quality
        if filename:
            config.output_file = filename

        scene().render()