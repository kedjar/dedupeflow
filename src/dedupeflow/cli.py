import sys

from termcolor import colored, cprint


def main():
    """Main entry point for the DedupeFlow application."""
    if len(sys.argv) < 2:
        print("Usage: python -m dedupeflow <data_file>")
        sys.exit(1)

    data_file = sys.argv[1]
    text = colored("Running DedupeFlow ...", "red", attrs=["bold"])
    cprint(text, "red", attrs=["bold"])
    # Here you would typically load the data and process it.
    # For demonstration, we will just print the file name.
    text = f"Processing data from {data_file}..."
    text = colored(text, "green", attrs=["bold"])
    cprint(text, "green", attrs=["bold"])
