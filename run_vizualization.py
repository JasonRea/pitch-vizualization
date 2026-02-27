import sys
from pitch_vizualization import *

def print_usage():
    print("Usage: python3 run_vizualization.py [option] [argument]\n")
    print("Options:")
    print("  -d <date> <pitcher> [quality] [filename]        Render all pitches from an outing on the given day")
    print('                                                  Example: python3 run_vizualization.py -d "2026-02-24" "Ranger Suarez" "high_quality" "Ranger_Suarez_2026024"')
    sys.exit(1)

if __name__ == '__main__':
    
    flag = sys.argv[1] if len(sys.argv) > 1 else None
    arg_1 = sys.argv[2] if len(sys.argv) > 2 else None
    arg_2 = sys.argv[3] if len(sys.argv) > 3 else None
    arg_3 = sys.argv[4] if len(sys.argv) > 4 else None
    arg_4 = sys.argv[5] if len(sys.argv) > 5 else None

    try:
        match flag:
            case "-d":
                Pitches = construct_pitch_vizualization(arg_1, arg_2)
                render_scene(Pitches, quality=arg_3, filename=arg_4)

            case _:
                print_usage()

    except Exception as e:
        print(e)
        print_usage()