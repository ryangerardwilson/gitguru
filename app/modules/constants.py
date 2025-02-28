import re

# ANSI color codes
HEADING_COLOR = '\033[92m'  # Bright green for headings
CONTENT_COLOR = '\033[94m'  # Bright blue for content
RESET_COLOR = '\033[0m'     # Reset to default

# Version
VERSION = "0.0.12-1"  # Initial version, will be updated by publish.py

# ASCII art banner
GITGURU_BANNER = r"""
   _______ __  ______                
  / ____(_) /_/ ____/_  _________  __
 / / __/ / __/ / __/ / / / ___/ / / /
/ /_/ / / /_/ /_/ / /_/ / /  / /_/ / 
\____/_/\__/\____/\__,_/_/   \__,_/  
                                     
=================================================
"""

# Valid branch types and naming pattern
VALID_TYPES = {'feature', 'bugfix', 'hotfix', 'release'}
BRANCH_PATTERN = re.compile(r'^\d+\.\d+(?:\.\d+)?/[a-z]+/(feature|bugfix|hotfix|release)(?:/[a-z0-9-]+)?$|^main$')
