# Copyright Allve, Inc. All Rights Reserved.

import re

def is_match(pattern, strline) -> bool:
    return bool(pattern.match(strline))