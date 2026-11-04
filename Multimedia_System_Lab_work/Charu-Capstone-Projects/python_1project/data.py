"""
data.py — Waste item definitions for Swachh Indore - Waste Sorting Hero
"""

WASTE_ITEMS = [
    # GREEN bin - Wet Waste
    {"emoji": "🍌", "name": "Banana Peel",     "bin": "GREEN", "type": "Wet Waste"},
    {"emoji": "🍎", "name": "Apple",            "bin": "GREEN", "type": "Wet Waste"},
    {"emoji": "🫓", "name": "Roti",             "bin": "GREEN", "type": "Wet Waste"},
    {"emoji": "🍂", "name": "Dry Leaves",       "bin": "GREEN", "type": "Wet Waste"},
    {"emoji": "🌸", "name": "Flowers",          "bin": "GREEN", "type": "Wet Waste"},
    {"emoji": "🫖", "name": "Tea Bag",          "bin": "GREEN", "type": "Wet Waste"},
    {"emoji": "🥬", "name": "Vegetable Scraps", "bin": "GREEN", "type": "Wet Waste"},
    # BLUE bin - Dry Waste
    {"emoji": "🧴", "name": "Plastic Bottle",   "bin": "BLUE",  "type": "Dry Waste"},
    {"emoji": "📰", "name": "Newspaper",        "bin": "BLUE",  "type": "Dry Waste"},
    {"emoji": "🍾", "name": "Glass Bottle",     "bin": "BLUE",  "type": "Dry Waste"},
    {"emoji": "📦", "name": "Cardboard Box",    "bin": "BLUE",  "type": "Dry Waste"},
    {"emoji": "🥫", "name": "Tin Can",          "bin": "BLUE",  "type": "Dry Waste"},
    {"emoji": "🛍️", "name": "Polythene Bag",    "bin": "BLUE",  "type": "Dry Waste"},
    # RED bin - Hazardous
    {"emoji": "😷", "name": "Used Mask",        "bin": "RED",   "type": "Hazardous"},
    {"emoji": "🩹", "name": "Sanitary Pad",     "bin": "RED",   "type": "Hazardous"},
    {"emoji": "🧷", "name": "iron pin",           "bin": "RED",   "type": "Hazardous"},
    {"emoji": "💉", "name": "Syringe",          "bin": "RED",   "type": "Hazardous"},
    {"emoji": "🍷", "name": "Broken Glass",     "bin": "RED",   "type": "Hazardous"},
    {"emoji": "💊", "name": "Expired Medicine", "bin": "RED",   "type": "Hazardous"},
]

# Fallback ASCII labels when emoji font is unavailable
EMOJI_FALLBACK = {
    "🍌": "BANANA", "🍎": "APPLE",  "🫓": "ROTI",  "🍂": "LEAF",
    "🌸": "FLOWER", "🫖": "TEA",    "🥬": "VEG",   "🧴": "BOTTLE",
    "📰": "PAPER",  "🍾": "GLASS",  "📦": "BOX",   "🥫": "CAN",
    "🛍️": "BAG",   "😷": "MASK",   "🩹": "PAD",   "🧷": "iron pin",
    "💉": "SYRINGE","🍷": "BRKGLS", "💊": "PILLS",
}
