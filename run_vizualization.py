import sys
from vizualization_builder import *
from fetch_data import *

def print_usage():
    print("Usage: python3 run_vizualization.py [option] [argument]\n")
    print("Options:")
    print("  -d <date> <pitcher> [quality]                   Render all pitches from an outing on the given day")
    print('                                                  Example: python3 run_vizualization.py -d "2026-02-24" "Ranger Suarez" "high_quality"')
    print("  -h <date>                                       Generate and save the High Heat graphic for the given day")
    print('                                                  Example: python3 run_vizualization.py -h "2026-02-24"')
    print("  -m <date>                                       Generate and save the Absolute Missiles graphic for the given day")
    print('                                                  Example: python3 run_vizualization.py -m "2026-02-24"')
    print("  -w <date>                                       Generate and save the Wheeeee! graphic for the given day")
    print('                                                  Example: python3 run_vizualization.py -w "2026-02-24"')
    print("  -a <date>                                       Generate and save all three graphics for the given day")
    print('                                                  Example: python3 run_vizualization.py -a "2026-02-24"')
    print("  -dA <date> [quality]                            Render all three splits for every pitcher on the given day")
    print('                                                  Example: python3 run_vizualization.py -dA "2026-02-24" "low_quality"')
    sys.exit(1)

if __name__ == '__main__':

    flag  = sys.argv[1] if len(sys.argv) > 1 else None
    arg_1 = sys.argv[2] if len(sys.argv) > 2 else None
    arg_2 = sys.argv[3] if len(sys.argv) > 3 else None
    arg_3 = sys.argv[4] if len(sys.argv) > 4 else None

    builder = VizualizationBuilder()

    try:
        match flag:
            case "-d":
                scene_class = (
                    builder
                    .load_pitches(date=arg_1, pitcher=arg_2, filter=pitches_filter)
                    .buildm_pitches()
                )
                VizualizationBuilder.render(scene_class, quality=arg_3, filename=f"{arg_2} {arg_1}")

            case "-dl":
                scene_class = (
                    builder
                    .load_pitches(date=arg_1, pitcher=arg_2, filter=pitches_filter_vs_left)
                    .buildm_pitches()
                )
                VizualizationBuilder.render(scene_class, quality=arg_3, filename=f"{arg_2} {arg_1} vs Left")

            case "-dr":
                scene_class = (
                    builder
                    .load_pitches(date=arg_1, pitcher=arg_2, filter=pitches_filter_vs_right)
                    .buildm_pitches()
                )
                VizualizationBuilder.render(scene_class, quality=arg_3, filename=f"{arg_2} {arg_1} vs Right")

            case "-da":
                scene_class = (
                    builder
                    .load_pitches(date=arg_1, pitcher=arg_2, filter=pitches_filter)
                    .buildm_pitches()
                )
                VizualizationBuilder.render(scene_class, quality=arg_3, filename=f"{arg_2} {arg_1}")

                scene_class_left = (
                    builder
                    .load_pitches(date=arg_1, pitcher=arg_2, filter=pitches_filter_vs_left)
                    .buildm_pitches()
                )
                VizualizationBuilder.render(scene_class_left, quality=arg_3, filename=f"{arg_2} {arg_1} vs Left")

                scene_class_right = (
                    builder
                    .load_pitches(date=arg_1, pitcher=arg_2, filter=pitches_filter_vs_right)
                    .buildm_pitches()
                )
                VizualizationBuilder.render(scene_class_right, quality=arg_3, filename=f"{arg_2} {arg_1} vs Right")

            case "-dA":
                day_df = daily_pitches(arg_1)
                for pitcher_id, pitcher_df in day_df.groupby("pitcher"):
                    pitcher_name = player_bio(pitcher_id)[0]
                    for filt, label in [
                        (pitches_filter,           ""),
                        (pitches_filter_vs_left,   " vs Left"),
                        (pitches_filter_vs_right,  " vs Right"),
                    ]:
                        builder.load_pitches_from_df(pitcher_df, filt)
                        if builder._axes is None:
                            continue
                        scene_class = builder.buildm_pitches()
                        VizualizationBuilder.render(
                            scene_class,
                            quality=arg_2,
                            filename=f"{pitcher_name} {arg_1}{label}",
                        )

            case "-h":
                builder.buildp(date=arg_1, config=VizualizationBuilder._high_heat_config())

            case "-m":
                builder.buildp(date=arg_1, config=VizualizationBuilder._absolute_missiles_config())

            case "-w":
                builder.buildp(date=arg_1, config=VizualizationBuilder._big_five_config())

            case "-a":
                builder.buildp(date=arg_1, config=VizualizationBuilder._high_heat_config())
                builder.buildp(date=arg_1, config=VizualizationBuilder._absolute_missiles_config())
                builder.buildp(date=arg_1, config=VizualizationBuilder._big_five_config())

            case _:
                print_usage()

    except Exception as e:
        print(e)
        print_usage()