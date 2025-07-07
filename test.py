from cal_spread import cal_spread
import click

    
@click.command()
@click.option('--symbol', help='Symbol of the instrument to search for', required=True)
def main_no_gui(symbol):

    try:
        result, error = cal_spread(symbol)
        if type(result) is str:
            print(result)
        elif result is not None:
            print(result)
        else:
            print("Result is None")
    except Exception as e:
        print(e)
    

if __name__ == "__main__":
    main_no_gui()