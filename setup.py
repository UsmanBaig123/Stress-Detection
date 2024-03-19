from cx_Freeze import setup, Executable

# Executable definition
executables = [Executable("Main.py")]

# Setup configuration
setup(
    name="Sress Checker",
    version="1.0",
    description="No descrition",
    executables=executables
)