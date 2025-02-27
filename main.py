import base64
import zlib
import hashlib
import os
import tempfile
import threading
import sys
import subprocess

SECRET_FOLDER = os.path.join(os.getcwd(), ".cache")
CACHE_FILE = os.path.join(SECRET_FOLDER, "cached_code.b64")


def ensure_secret_folder():
    if not os.path.exists(SECRET_FOLDER):
        os.makedirs(SECRET_FOLDER)


def hash_code(code):
    return hashlib.sha256(code.encode()).hexdigest()


def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "rb") as f:
            return f.read().decode()
    return None


def save_cache(compiled_code):
    compressed_code = base64.b64encode(zlib.compress(compiled_code.encode())).decode()
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        f.write(compressed_code)


VALID_COMMANDS = {
    "LET", "SET", "GET", "FD", "BK", "RT", "LT", "PENUP", "PENDOWN",
    "COLOR", "BG", "SCREENSIZE", "FOR", "WHILE", "FUNCTION", "CALL",
    "RETURN", "TITLE", "RESIZABLE", "RANDOM", "ONCLICK", "CIRCLE",
    "PENSIZE", "BEGINFILL", "ENDFILL", "NEXT", "END"
}


def compile_turtlebasic(code):
    lines = code.strip().split("\n")
    python_code = ["import turtle\n", "t = turtle.Turtle()", "screen = turtle.Screen()"]
    variables = {}
    colors = {
        "RED": "red",
        "GREEN": "green",
        "BLUE": "blue",
        "BLACK": "black",
        "WHITE": "white",
        "YELLOW": "yellow",
        "PURPLE": "purple",
    }

    indent_level = 0
    line_num = 0



    for line in lines:


        tokens = line.strip().split()
        if not tokens:
            continue

        cmd = tokens[0].upper()
        print(cmd)
        
        if cmd not in VALID_COMMANDS:
            raise ValueError(f"Syntax Error on line {line_num}: Unknown command '{cmd}'")

        indentation = "    " * indent_level

        if cmd == "LET":
            var_name = tokens[1]
            value = " ".join(tokens[3:])
            python_code.append(f"{indentation}{var_name} = {value}")
            variables[var_name] = value

        elif cmd == "SET":
            var_name = tokens[1]
            value = tokens[2]
            python_code.append(f"{indentation}{var_name} = {value}")
            variables[var_name] = value

        elif cmd == "GET":
            python_code.append(f"{indentation}print({tokens[1]})")

        elif cmd == "FD":
            python_code.append(f"{indentation}t.forward({tokens[1]})")

        elif cmd == "BK":
            python_code.append(f"{indentation}t.backward({tokens[1]})")

        elif cmd == "RT":
            python_code.append(f"{indentation}t.right({tokens[1]})")

        elif cmd == "LT":
            python_code.append(f"{indentation}t.left({tokens[1]})")

        elif cmd == "PENUP":
            python_code.append(f"{indentation}t.penup()")

        elif cmd == "PENDOWN":
            python_code.append(f"{indentation}t.pendown()")

        elif cmd == "COLOR":
            color = colors.get(tokens[1].upper(), tokens[1])
            python_code.append(f"{indentation}t.pencolor('{color}')")

        elif cmd == "BG":
            color = colors.get(tokens[1].upper(), tokens[1])
            python_code.append(f"{indentation}screen.bgcolor('{color}')")

        elif cmd == "SCREENSIZE":
            python_code.append(f"{indentation}screen.setup({tokens[1]}, {tokens[2]})")

        elif cmd == "FOR":
            var_name, start, end = tokens[1], tokens[3], tokens[5]
            python_code.append(f"{indentation}for {var_name} in range({start}, {end} + 1):")
            indent_level += 1  # Increase indentation for loop body

        elif cmd == "NEXT":
            indent_level -= 1  # Close loop indentation

        elif cmd == "WHILE":
            condition = " ".join(tokens[1:])
            python_code.append(f"{indentation}while {condition}:")
            indent_level += 1  # Increase indentation for while body

        elif cmd == "FUNCTION":
            func_name = tokens[1]
            python_code.append(f"{indentation}def {func_name}():")
            indent_level += 1  # Increase indentation for function body

        elif cmd == "CALL":
            python_code.append(f"{indentation}{tokens[1]}()")

        elif cmd == "RETURN":
            python_code.append(f"{indentation}return {tokens[1]}")

        elif cmd == "TITLE":
            python_code.append(f"{indentation}screen.title('{tokens[1]}')")

        elif cmd == "RESIZABLE":
            python_code.append(
                f"{indentation}screen.cv._rootwindow.resizable({tokens[1].upper() == 'ON'}, {tokens[1].upper() == 'ON'})"
            )

        elif cmd == "RANDOM":
            python_code.append(f"{indentation}{tokens[1]} = random.randint({tokens[2]}, {tokens[3]})")

        elif cmd == "ONCLICK":
            python_code.append(f"{indentation}screen.onclick(lambda x, y: {tokens[1]}())")

        elif cmd == "CIRCLE":
            python_code.append(f"{indentation}t.circle({tokens[1]})")

        elif cmd == "PENSIZE":
            python_code.append(f"{indentation}t.pensize({tokens[1]})")

        elif cmd == "BEGINFILL":
            python_code.append(f"{indentation}t.begin_fill()")

        elif cmd == "ENDFILL":
            python_code.append(f"{indentation}t.end_fill()")

        line_num += 1

    python_code.append("turtle.done()")
    return "\n".join(python_code)


def run_turtle_script(script):

    def run_code():
        """Writes compiled code to a temporary file and executes it."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".py", mode="w", encoding="utf-8") as tmp_file:
            tmp_file.write(script)
            tmp_file_path = tmp_file.name

        subprocess.run(["python", tmp_file_path], check=True)
        os.remove(tmp_file_path)


    thread = threading.Thread(target=run_code)
    thread.start()


def main():
    ensure_secret_folder()

    if len(sys.argv) > 1:
        # Read code from file
        if not os.path.exists(sys.argv[1]):
            print(f"⚠️ Error: File '{sys.argv[1]}' not found.")
            return

        with open(sys.argv[1], "r", encoding="utf-8") as f:
            input_code = f.read()
    else:
        # Default code
        input_code = """
        BG WHITE
        COLOR BLUE
        PENSIZE 3
        FOR i = 1 TO 4
            FD 100
            RT 90
        NEXT
        END
        """

    cached_code = load_cache()
    compiled_code = compile_turtlebasic(input_code)
    hashed_input = hash_code(input_code)

    if cached_code and hash_code(cached_code) == hashed_input:
        print("Running cached code...")
        run_turtle_script(base64.b64decode(cached_code).decode())
    else:
        print("Compiling and running new code...")
        save_cache(compiled_code)
        run_turtle_script(compiled_code)


if __name__ == "__main__":
    main()
