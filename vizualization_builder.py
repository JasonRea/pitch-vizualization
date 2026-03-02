from fetch_data import fetch_pitch_data
import pandas as pd
import numpy as np
from scipy.optimize import brentq
from manim import *


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

        df = fetch_pitch_data(start_dt=date, pitcher=pitcher)

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

        axes      = self._axes
        scale     = self.SCALE
        pitches   = list(self._pitches)
        end_points = list(self._end_points)
        end_times = list(self._end_times)
        colors    = list(self._colors)

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