# Simple .class decompiler

Minimalist Python wrapper for CFR Decompiler to quickly handle `.jar` files.

## Functions
1. **Inplace**: Replaces `.class` with `.java` inside the original JAR.
2. **Unpack**: Extracts everything (sources + resources) to a folder.
3. **Project**: Creates a structured Gradle project (`src/main/java`, `src/main/resources`).

## Requirements
* Java installed (`java` command available).
* `cfr-0.152.jar` in the script folder.
* Python 3.x.

## Quick Start
1. Download files(with `cfr-0.152.jar` inside).
2. Run: `python cfr_decompiler.py`
3. Enter the path to your JAR and choose a mode.
4. Done!

## Library Usage
```python
from cfr_decompiler import CFRDecompiler
decompiler = CFRDecompiler("cfr-0.152.jar")
decompiler.mode_2_to_folder("target.jar", "output_dir")
```
