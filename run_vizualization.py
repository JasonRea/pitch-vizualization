import sys
from vizualization_builder import *

def print_usage():
    print("Usage: python3 run_vizualization.py [option] [argument]\n")
    print("Options:")
    print("  -d <date> <pitcher> [quality]                   Render all pitches from an outing on the given day")
    print('                                                  Example: python3 run_vizualization.py -d "2026-02-24" "Ranger Suarez" "high_quality"')
    print("  -h <date>                                       Generate and save the High Heat graphic for the given day")
    print('                                                  Example: python3 run_vizualization.py -h "2026-02-24"')
    sys.exit(1)

if __name__ == '__main__':
    
    flag = sys.argv[1] if len(sys.argv) > 1 else None
    arg_1 = sys.argv[2] if len(sys.argv) > 2 else None
    arg_2 = sys.argv[3] if len(sys.argv) > 3 else None
    arg_3 = sys.argv[4] if len(sys.argv) > 4 else None

    try:
        match flag:
            case "-d":
                scene_class = (
                    VizualizationBuilder()
                    .load_pitches(date=arg_1, pitcher=arg_2)
                    .buildm_pitches()
                )
                VizualizationBuilder.render(scene_class, quality=arg_3, filename=f"{arg_2} {arg_1}")

            case "-h":
                VizualizationBuilder().buildp_high_heat(date=arg_1)

            case _:
                print_usage()

    except Exception as e:
        print(e)
        print_usage()