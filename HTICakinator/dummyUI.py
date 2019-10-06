#!/usr/bin/env python3
import math
import json
import collections as cl
import argparse
import numpy as np
import heapq
import HTICakinator


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='HTIC akinator')
    parser.add_argument('database_path', help='Path to database.json')
    args = parser.parse_args()
   
    hticakinator = HTICakinator.HTICakinator(args.database_path)
    hticakinator.main()

