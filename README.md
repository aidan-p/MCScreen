<h3 align="center" tabindex="-1" class="heading-element" dir="auto">MCScreen</h3>
<p align="center"><img src="https://github.com/user-attachments/assets/ace8951c-87a5-4e70-8ab5-79021a591dfe" width="600" /><br></p>
<p align="center">Doom being displayed inside of a Minecraft world</p>

## Features
- Display main monitor inside locally ran Minecraft server through RCON or plugin implementation

## Requirements
- Python 3.13.1 or higher
- Required Python packages (install using pip):
  ```bash
  pip install mcrcon Pillow mss numpy
- If using the plugin implementation, make sure to download it from the following repository: https://github.com/aidan-p/FastCommandPlugin/tree/main 
  
## Getting Started
- Download and install Python and all required packages.
- Download repo and unzip in any directory.
- Decide if you would like to use the RCON implementation (slower) or plugin implementation (quicker)
  - Change the "USE_FAST_PLUGIN" variable to "False" if you would like to use RCON, otherwise leave as "True" if you are using the plugin
- Modify "NUM_WORKERS" to the number of threads you would like to handle the display (for example, I have a Ryzen 7 5700x3d which is an 8c/16t chip, so I am using all 16 threads)
- Modify the "RCON_PORT"/"PLUGIN_PORT" and "PASSWORD" to the correct variables
- Modify the "START_X", "START_Y", and "START_Z" to the appropriate coordinates
- Run by executing:
  ```bash
  python .\mcscreen.py
