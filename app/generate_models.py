import os
import subprocess
import sys

from dotenv import load_dotenv

def main():
    env_file = ".env" if len(sys.argv) < 2 else f".env.{sys.argv[1]}"

    load_dotenv(dotenv_path=env_file)

    db_ulr = os.getenv("DATABASE_URL")
    if not db_ulr:
        print("DATABASE_URL not found in", env_file)
        sys.exit(1)

    command = f"sqlacodegen {db_ulr} > db/models.py"
    subprocess.run(command, shell=True)
    print("Models generated")


if __name__ == "__main__":
    main()