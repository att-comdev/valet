#!/usr/bin/env python

import sys
import valetcli


if __name__ == "__main__":
    try:
        valetcli.main(sys.argv)
    except Exception:
        import traceback
        traceback.format_exc()
