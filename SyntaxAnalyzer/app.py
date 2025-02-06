from pathlib import Path
import os

def process_file(filename):
    if not filename.endswith('.lit'):
        print(f"Error: '{filename}' is not a valid .lit file.")
        return

    try:
        downloads_folder = Path.home() / "Downloads"
        output_filename = downloads_folder / filename.replace('.lit', '_output.txt')

        if not output_filename.exists():
            print(f"\nError: The file '{filename}' does not exist in the Downloads folder.")
            return

        with open(output_filename, 'r', encoding='utf-8') as file:
            content = file.read()
            print("--------------- Output File Contents ---------------")
            print(content)

        print(f"\nOutput saved to {output_filename}")

    except UnicodeDecodeError as e:
        print(f"Encoding error: {e}")
        print("Try using a different encoding such as 'latin-1' or ensure the file is UTF-8 encoded.")
    except FileNotFoundError:
        print(f"Error: The file '{filename}' does not exist.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    filename = input("Enter the .lit file name from the Downloads folder: ").strip()
    process_file(filename)
