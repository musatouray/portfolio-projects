"""
Generate randomized unique product names based on product categories.

This script reads the products CSV, generates meaningful product names
based on category, and updates the CSV with a new 'product_name' column.
"""

import random
from pathlib import Path

import pandas as pd

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"

# Product name components by category
CATEGORY_PRODUCTS = {
    "Health & Beauty": {
        "types": ["Skincare Set", "Face Cream", "Hair Serum", "Body Lotion", "Makeup Kit",
                  "Facial Cleanser", "Anti-Aging Serum", "Moisturizer", "Lip Balm", "Sunscreen",
                  "Hair Mask", "Nail Polish Set", "Eye Cream", "Toner", "Face Mask"],
        "brands": ["GlowPro", "BeautyElite", "SkinLux", "VitaGlow", "PureRadiance",
                   "NaturaBella", "DermaCare", "Velvet Touch", "AquaFresh", "ZenBeauty"]
    },
    "Computers & Accessories": {
        "types": ["Wireless Mouse", "Mechanical Keyboard", "USB Hub", "Laptop Stand", "Webcam",
                  "Monitor Arm", "Cable Organizer", "Mouse Pad", "Headset", "SSD Drive",
                  "RAM Module", "Graphics Card", "CPU Cooler", "Power Supply", "PC Case"],
        "brands": ["TechPro", "ByteForce", "CyberLink", "QuantumTech", "NexGen",
                   "DataCore", "PowerByte", "UltraComp", "MegaHertz", "ProGear"]
    },
    "Automotive": {
        "types": ["Car Cover", "Floor Mats", "Phone Mount", "Dash Cam", "Seat Covers",
                  "Air Freshener", "Tire Gauge", "Jump Starter", "Car Vacuum", "LED Lights",
                  "Steering Wheel Cover", "Trunk Organizer", "Window Shades", "Oil Filter", "Wiper Blades"],
        "brands": ["AutoPro", "DriveMaster", "RoadKing", "CarElite", "MotorGuard",
                   "SpeedZone", "TurboMax", "VehicleCare", "DriveShield", "AutoLux"]
    },
    "Bed & Bath": {
        "types": ["Sheet Set", "Towel Set", "Comforter", "Pillow", "Bath Mat",
                  "Duvet Cover", "Mattress Pad", "Shower Curtain", "Blanket", "Bed Skirt",
                  "Pillowcase Set", "Bath Robe", "Hand Towels", "Quilted Throw", "Memory Foam Topper"],
        "brands": ["DreamWeave", "SleepLux", "CozyNest", "SoftTouch", "ComfortPlus",
                   "RestWell", "CloudSoft", "PureCotton", "SilkDreams", "NightBliss"]
    },
    "Furniture & Home Decor": {
        "types": ["Accent Chair", "Coffee Table", "Wall Art", "Table Lamp", "Bookshelf",
                  "Area Rug", "Throw Pillow", "Vase Set", "Mirror", "Side Table",
                  "Ottoman", "Plant Stand", "Picture Frame", "Candle Holder", "Wall Clock"],
        "brands": ["HomeStyle", "ModernNest", "UrbanLiving", "ClassicHome", "ArtisanCraft",
                   "EliteDecor", "CozyCorner", "PrimeSpace", "LuxeLiving", "DesignHaus"]
    },
    "Sports & Outdoors": {
        "types": ["Yoga Mat", "Dumbbell Set", "Resistance Bands", "Running Shoes", "Backpack",
                  "Water Bottle", "Fitness Tracker", "Camping Tent", "Sleeping Bag", "Hiking Poles",
                  "Jump Rope", "Exercise Ball", "Foam Roller", "Sport Watch", "Bike Helmet"],
        "brands": ["FitPro", "ActiveLife", "SportMax", "TrailBlazer", "EnduranceX",
                   "PowerFit", "OutdoorElite", "AthletePro", "PeakPerform", "VitalMove"]
    },
    "Fragrances": {
        "types": ["Eau de Parfum", "Cologne", "Body Mist", "Perfume Set", "Scented Candle",
                  "Essential Oil", "Room Spray", "Diffuser Set", "Aromatherapy Kit", "Travel Spray"],
        "brands": ["ScentLux", "AromaElite", "Essence", "FragranceHouse", "PureScent",
                   "VelvetMist", "NobleAura", "CrystalBreeze", "GoldenMusk", "SilkAroma"]
    },
    "Kitchen & Housewares": {
        "types": ["Cookware Set", "Knife Set", "Blender", "Coffee Maker", "Toaster",
                  "Food Processor", "Mixing Bowls", "Cutting Board", "Utensil Set", "Storage Containers",
                  "Bakeware Set", "Spice Rack", "Kitchen Scale", "Can Opener", "Measuring Cups"],
        "brands": ["ChefPro", "KitchenElite", "CookMaster", "HomeCuisine", "CulinaryPro",
                   "PrimeKitchen", "MasterChef", "GourmetPlus", "KitchenAid", "CookWell"]
    },
    "Cell Phones & Accessories": {
        "types": ["Phone Case", "Screen Protector", "Wireless Charger", "Car Mount", "Power Bank",
                  "Bluetooth Earbuds", "Phone Stand", "Charging Cable", "Pop Socket", "Armband",
                  "Lens Kit", "Selfie Stick", "Phone Wallet", "Ring Holder", "Fast Charger"],
        "brands": ["TechShield", "MobileMax", "PhonePro", "SmartGear", "ConnectPlus",
                   "CellElite", "PowerLink", "MobiTech", "SignalMax", "ChargePro"]
    },
    "Watches & Gifts": {
        "types": ["Analog Watch", "Digital Watch", "Smartwatch", "Watch Band", "Jewelry Box",
                  "Cufflinks", "Wallet", "Keychain", "Gift Set", "Watch Case",
                  "Bracelet", "Pendant", "Tie Clip", "Money Clip", "Engraved Pen"],
        "brands": ["TimeElite", "LuxWatch", "GiftCraft", "ClassicTime", "PremiumGifts",
                   "ElegantHour", "TimePiece", "GoldenMoment", "CrystalTime", "NobleGift"]
    },
    "Food & Beverages": {
        "types": ["Coffee Beans", "Tea Collection", "Snack Box", "Chocolate Set", "Honey Jar",
                  "Spice Set", "Olive Oil", "Pasta Set", "Granola Mix", "Protein Bars",
                  "Dried Fruits", "Nut Mix", "Hot Sauce Set", "Jam Collection", "Energy Drink Pack"],
        "brands": ["GourmetSelect", "TasteElite", "FreshFarm", "PureFlavor", "NaturalChoice",
                   "PrimeTaste", "OrganicBest", "FlavorHouse", "CulinaryGems", "TasteCraft"]
    },
    "Baby Products": {
        "types": ["Baby Monitor", "Stroller", "Car Seat", "Diaper Bag", "Baby Carrier",
                  "Bottle Set", "Pacifier Pack", "Baby Blanket", "Crib Mobile", "Teething Toy",
                  "High Chair", "Play Mat", "Baby Bath Set", "Swaddle Set", "Nursing Pillow"],
        "brands": ["BabyJoy", "LittleOne", "TinySteps", "CuddleCare", "InfantPro",
                   "BabyBliss", "SweetDreams", "TinyTots", "BabyLux", "GentleCare"]
    },
    "Office Supplies & Stationery": {
        "types": ["Notebook Set", "Pen Collection", "Desk Organizer", "Planner", "Sticky Notes",
                  "File Folders", "Stapler Set", "Paper Clips", "Desk Lamp", "Calculator",
                  "Whiteboard", "Marker Set", "Tape Dispenser", "Scissors", "Letter Tray"],
        "brands": ["OfficePro", "DeskElite", "WriteWell", "PaperCraft", "WorkSpace",
                   "ProDesk", "ClearWrite", "OfficeLux", "DeskMaster", "NeatWork"]
    },
    "Toys & Games": {
        "types": ["Building Blocks", "Board Game", "Action Figure", "Puzzle Set", "RC Car",
                  "Plush Toy", "Art Set", "Science Kit", "Card Game", "Drone",
                  "Dollhouse", "Train Set", "Robot Toy", "Outdoor Game", "Educational Toy"],
        "brands": ["FunTime", "PlayPro", "ToyWorld", "GameMaster", "KidZone",
                   "HappyPlay", "JoyToys", "SmartKids", "PlayElite", "FunFactory"]
    },
    "Tools & Home Improvement": {
        "types": ["Drill Set", "Screwdriver Kit", "Tool Box", "Level", "Tape Measure",
                  "Wrench Set", "Saw", "Hammer", "Paint Roller Set", "Ladder",
                  "Work Light", "Safety Glasses", "Gloves", "Sanding Kit", "Nail Gun"],
        "brands": ["ToolPro", "BuildMaster", "CraftMax", "ProBuild", "HandyMan",
                   "PowerCraft", "FixIt", "WorkForce", "ToolElite", "BuildRight"]
    },
    "Fashion & Apparel": {
        "types": ["T-Shirt", "Jeans", "Sneakers", "Dress", "Jacket",
                  "Handbag", "Sunglasses", "Belt", "Scarf", "Hat",
                  "Sweater", "Shorts", "Sandals", "Hoodie", "Socks Pack"],
        "brands": ["StylePro", "FashionElite", "TrendSet", "UrbanWear", "ClassicFit",
                   "ModernStyle", "ChicWear", "PrimeThreads", "VogueLine", "StreetStyle"]
    },
    "Media & Entertainment": {
        "types": ["Vinyl Record", "Blu-ray Set", "Gaming Controller", "Headphones", "Speaker",
                  "Microphone", "Webcam", "Streaming Device", "DVD Collection", "Music Box",
                  "Turntable", "Soundbar", "Karaoke System", "Projector", "VR Headset"],
        "brands": ["SoundWave", "MediaPro", "EntertainX", "AudioElite", "ScreenMaster",
                   "PlaySound", "VibeMax", "ClearTone", "MediaLux", "SonicPro"]
    },
    "Electronics": {
        "types": ["Smart TV", "Tablet", "Smartwatch", "Wireless Speaker", "E-Reader",
                  "Digital Camera", "Portable Charger", "Smart Display", "Router", "Smart Plug",
                  "Fitness Band", "Drone", "Action Camera", "Smart Thermostat", "Security Camera"],
        "brands": ["TechVision", "SmartLife", "ElectroPro", "DigitalMax", "NextGen",
                   "PowerTech", "ConnectPro", "SmartWave", "TechElite", "InnovateTech"]
    },
    "Major Appliances": {
        "types": ["Refrigerator", "Washing Machine", "Dryer", "Dishwasher", "Microwave",
                  "Air Conditioner", "Vacuum Cleaner", "Air Purifier", "Dehumidifier", "Range Hood",
                  "Freezer", "Wine Cooler", "Garbage Disposal", "Water Heater", "Oven"],
        "brands": ["HomePro", "ApplianceMax", "CoolTech", "CleanMaster", "PowerHome",
                   "EcoAppliance", "SmartHome", "EliteAppliance", "PrimeHome", "FreshAir"]
    },
    "Pet Supplies": {
        "types": ["Pet Bed", "Food Bowl", "Leash", "Collar", "Pet Carrier",
                  "Scratching Post", "Pet Toy", "Grooming Kit", "Pet Feeder", "Aquarium",
                  "Bird Cage", "Pet Brush", "Training Pads", "Pet Treats", "Pet Shampoo"],
        "brands": ["PetCare", "HappyPet", "FurryFriend", "PawPro", "PetElite",
                   "AnimalLove", "PetJoy", "FurBuddy", "PetLux", "TailWag"]
    },
    "Luggage & Travel Gear": {
        "types": ["Carry-On", "Suitcase", "Backpack", "Duffel Bag", "Packing Cubes",
                  "Travel Pillow", "Luggage Tag", "Passport Holder", "Toiletry Bag", "Garment Bag",
                  "Laptop Bag", "Weekender Bag", "Travel Adapter", "Luggage Lock", "Compression Bags"],
        "brands": ["TravelPro", "JourneyMax", "Wanderlust", "GlobeTrek", "VoyageElite",
                   "TripMaster", "ExploreGear", "TravelLux", "RoadTrip", "AdventurePro"]
    },
    "Heating Cooling & Air": {
        "types": ["Space Heater", "Fan", "Humidifier", "Dehumidifier", "Air Purifier",
                  "Portable AC", "Tower Fan", "Heating Pad", "Air Circulator", "Evaporative Cooler",
                  "Radiator Heater", "Ceiling Fan", "Window Fan", "HEPA Filter", "Thermostat"],
        "brands": ["ClimatePro", "AirFlow", "CoolBreeze", "HeatMaster", "FreshAir",
                   "ComfortZone", "AirElite", "TempControl", "PureAir", "ClimateMax"]
    },
    "Industrial & Business": {
        "types": ["Safety Vest", "Hard Hat", "Work Gloves", "First Aid Kit", "Fire Extinguisher",
                  "Pallet Jack", "Shelving Unit", "Label Maker", "Safety Signs", "Tool Belt",
                  "Cargo Straps", "Moving Dolly", "Storage Bins", "Safety Cones", "Work Boots"],
        "brands": ["IndustrialPro", "SafetyFirst", "WorkMax", "ProGrade", "HeavyDuty",
                   "BuildSafe", "JobSite", "ProIndustry", "SafeWork", "DutyMax"]
    },
    "Books": {
        "types": ["Novel", "Cookbook", "Self-Help Book", "Biography", "History Book",
                  "Science Book", "Art Book", "Travel Guide", "Business Book", "Children's Book",
                  "Poetry Collection", "Reference Book", "Textbook", "Memoir", "Graphic Novel"],
        "brands": ["PageTurner", "BookWorld", "LitElite", "ReadMore", "StoryHouse",
                   "BookCraft", "WisdomPress", "NovelIdeas", "PaperDreams", "WordSmith"]
    },
    "Musical Instruments": {
        "types": ["Acoustic Guitar", "Electric Guitar", "Keyboard", "Drum Set", "Violin",
                  "Ukulele", "Microphone", "Amp", "Music Stand", "Guitar Strings",
                  "Capo", "Tuner", "Drumsticks", "Piano Bench", "Sheet Music"],
        "brands": ["MelodyPro", "SoundCraft", "MusicMaster", "HarmonyElite", "ToneWood",
                   "RhythmMax", "NoteWorthy", "StringPro", "BeatMaker", "TuneCraft"]
    },
    "Cameras & Photography": {
        "types": ["DSLR Camera", "Mirrorless Camera", "Camera Lens", "Tripod", "Camera Bag",
                  "Memory Card", "Flash", "Filter Set", "Camera Strap", "Cleaning Kit",
                  "Light Box", "Backdrop", "Lens Hood", "Remote Shutter", "Battery Pack"],
        "brands": ["PhotoPro", "LensMaster", "CapturePlus", "ImageElite", "FocusCraft",
                   "SnapShot", "FramePerfect", "VisionPro", "ClearShot", "PhotoLux"]
    },
    "Tablets Printers & Imaging": {
        "types": ["Tablet", "Printer", "Scanner", "Ink Cartridge", "Photo Paper",
                  "Tablet Case", "Stylus", "Printer Stand", "Label Printer", "3D Printer",
                  "Document Feeder", "Toner", "Print Server", "Drawing Tablet", "Portable Printer"],
        "brands": ["PrintPro", "TabletMax", "ImageCraft", "ScanElite", "DigitalPrint",
                   "TechPrint", "SmartTab", "PrintMaster", "ClearImage", "DocuPro"]
    },
    "Landline Phones": {
        "types": ["Cordless Phone", "Answering Machine", "Conference Phone", "Desk Phone", "Phone Combo",
                  "Caller ID Unit", "Phone Headset", "Phone Stand", "Extension Cord", "Phone Book"],
        "brands": ["TelePro", "ClearCall", "PhoneMaster", "ConnectLine", "VoiceElite",
                   "RingClear", "TalkPro", "PhoneLux", "CallMax", "LineConnect"]
    },
    "Party Supplies": {
        "types": ["Balloon Set", "Banner", "Tableware Set", "Party Hats", "Streamers",
                  "Confetti", "Party Favors", "Cake Topper", "Photo Booth Props", "Piñata",
                  "Gift Bags", "Invitation Cards", "Centerpiece", "Party Lights", "Costume Set"],
        "brands": ["PartyPro", "CelebratePlus", "FestiveJoy", "PartyTime", "EventElite",
                   "HappyParty", "FunFest", "PartyLux", "CelebrationCo", "JoyfulEvents"]
    },
    "Bedding & Home Comfort": {
        "types": ["Memory Foam Pillow", "Weighted Blanket", "Mattress Topper", "Heated Blanket", "Body Pillow",
                  "Silk Pillowcase", "Down Comforter", "Cooling Sheets", "Throw Blanket", "Bed Wedge",
                  "Lumbar Pillow", "Neck Pillow", "Floor Cushion", "Seat Cushion", "Bolster Pillow"],
        "brands": ["ComfortRest", "DreamCloud", "SleepWell", "CozyCare", "RestEasy",
                   "CloudNine", "SoftSlumber", "NightComfort", "PeacefulSleep", "RestLux"]
    },
    "Fine Art": {
        "types": ["Oil Painting", "Canvas Print", "Sculpture", "Art Print", "Watercolor",
                  "Framed Artwork", "Abstract Art", "Photography Print", "Art Poster", "Metal Art",
                  "Glass Art", "Mixed Media", "Charcoal Drawing", "Digital Art Print", "Limited Edition"],
        "brands": ["ArtisanGallery", "MasterPiece", "CreativeVision", "ArtElite", "GalleryPro",
                   "CanvasCraft", "ArtHouse", "VisionArt", "FrameWorthy", "StudioPrime"]
    },
    "Holiday & Christmas Decor": {
        "types": ["Christmas Tree", "Ornament Set", "String Lights", "Wreath", "Nativity Set",
                  "Stockings", "Tree Skirt", "Advent Calendar", "Door Mat", "Yard Decoration",
                  "Table Runner", "Candle Set", "Snow Globe", "Tree Topper", "Gift Wrap Set"],
        "brands": ["HolidayJoy", "FestiveHome", "SeasonsBest", "MerryDecor", "WinterWonder",
                   "HolidayMagic", "YuletidePro", "CelebrateSeason", "JollyDecor", "FestiveLux"]
    },
    "Flowers & Plants": {
        "types": ["Orchid Plant", "Succulent Set", "Flower Bouquet", "Rose Arrangement", "Herb Garden Kit",
                  "Potted Plant", "Flower Seeds", "Planter Set", "Bonsai Tree", "Terrarium Kit",
                  "Hanging Plant", "Cactus Set", "Flower Vase", "Plant Stand", "Garden Starter Kit"],
        "brands": ["BloomPro", "GreenThumb", "FloralElite", "NaturePlant", "GardenJoy",
                   "PetalPerfect", "PlantLife", "BlossomCare", "GreenLeaf", "FloraLux"]
    },
    "Arts & Crafts": {
        "types": ["Paint Set", "Sketchbook", "Brush Set", "Clay Kit", "Sewing Kit",
                  "Yarn Bundle", "Craft Paper", "Bead Set", "Stencil Kit", "Embroidery Kit",
                  "Scrapbook Set", "Calligraphy Set", "Candle Making Kit", "Jewelry Kit", "Knitting Needles"],
        "brands": ["CraftPro", "ArtSupply", "CreatePlus", "CraftyHands", "ArtisanKit",
                   "CreativeCraft", "MakerSpace", "CraftElite", "DIYMaster", "HandMadePro"]
    },
    "Diapers & Baby Care": {
        "types": ["Diaper Pack", "Baby Wipes", "Diaper Cream", "Changing Pad", "Diaper Pail",
                  "Baby Powder", "Diaper Bag", "Rash Ointment", "Baby Lotion", "Baby Oil",
                  "Wet Bag", "Diaper Caddy", "Training Pants", "Swim Diapers", "Overnight Diapers"],
        "brands": ["BabySoft", "TenderCare", "GentleTouch", "PureBaby", "ComfortBaby",
                   "LittleCare", "SoftSteps", "BabyFresh", "CuddleSoft", "DryComfort"]
    },
    "Insurance & Services": {
        "types": ["Gift Card", "Service Plan", "Extended Warranty", "Membership", "Subscription Box",
                  "Consultation", "Installation Service", "Repair Service", "Maintenance Plan", "Support Package"],
        "brands": ["ServicePro", "CarePlus", "ProtectMax", "CoverageElite", "PlanPro",
                   "ServiceLux", "CareFirst", "ProtectPlus", "PremiumService", "TotalCare"]
    },
    "Trending Products": {
        "types": ["Gadget", "Novelty Item", "Smart Device", "Unique Gift", "Viral Product",
                  "Innovation Kit", "Tech Accessory", "Lifestyle Product", "Eco-Friendly Item", "Designer Piece"],
        "brands": ["TrendSet", "CoolFinds", "ViralPicks", "NextBig", "TrendElite",
                   "HotItems", "MustHave", "TrendyTech", "CoolStuff", "NewWave"]
    },
    "Uncategorized": {
        "types": ["General Item", "Miscellaneous Product", "Assorted Item", "Multi-Purpose Product", "Variety Pack",
                  "Starter Kit", "Value Set", "Basic Set", "Essential Item", "Standard Product"],
        "brands": ["ValuePro", "BasicPlus", "GeneralGoods", "EssentialPicks", "StandardLine",
                   "CoreItems", "SimpleBest", "EverydayValue", "BasicElite", "GeneralPro"]
    }
}

# Descriptors to add variety
DESCRIPTORS = ["Premium", "Classic", "Pro", "Elite", "Essential", "Deluxe", "Ultra",
               "Modern", "Signature", "Advanced", "Compact", "Original", "Plus", "Max", "Basic"]

COLORS = ["Black", "White", "Silver", "Gold", "Navy", "Gray", "Red", "Blue", "Green", "Rose"]

SIZES = ["XS", "S", "M", "L", "XL", "Mini", "Standard", "Large", "Compact", "Full-Size"]


def get_category_components(category: str) -> dict:
    """Get product name components for a category, with fallback."""
    if category in CATEGORY_PRODUCTS:
        return CATEGORY_PRODUCTS[category]
    return CATEGORY_PRODUCTS["Uncategorized"]


def generate_product_name(category: str, index: int) -> str:
    """Generate a unique product name based on category."""
    components = get_category_components(category)

    brand = random.choice(components["brands"])
    product_type = random.choice(components["types"])

    # Add variety with different patterns
    pattern = index % 5

    if pattern == 0:
        # Brand + Descriptor + Type
        descriptor = random.choice(DESCRIPTORS)
        return f"{brand} {descriptor} {product_type}"
    elif pattern == 1:
        # Brand + Type + Color
        color = random.choice(COLORS)
        return f"{brand} {product_type} - {color}"
    elif pattern == 2:
        # Brand + Type + Model Number
        model = f"{random.randint(100, 9999)}"
        return f"{brand} {product_type} {model}"
    elif pattern == 3:
        # Brand + Type + Size
        size = random.choice(SIZES)
        return f"{brand} {product_type} ({size})"
    else:
        # Brand + Type + Version
        version = f"V{random.randint(1, 5)}.{random.randint(0, 9)}"
        return f"{brand} {product_type} {version}"


def main():
    """Main entry point."""
    random.seed(42)  # For reproducibility

    print("=" * 60)
    print("Product Name Generator")
    print("=" * 60)

    # Read products CSV
    products_path = DATA_RAW_DIR / "olist_products_dataset.csv"
    translation_path = DATA_RAW_DIR / "product_category_name_translation.csv"

    print(f"\nReading products from: {products_path}")
    products_df = pd.read_csv(products_path)
    print(f"  Found {len(products_df):,} products")

    # Read translation for category mapping
    print(f"\nReading translations from: {translation_path}")
    translation_df = pd.read_csv(translation_path)
    translation_map = dict(zip(
        translation_df["product_category_name"],
        translation_df["product_category_name_english"]
    ))
    print(f"  Found {len(translation_map)} category translations")

    # Generate product names
    print("\nGenerating product names...")
    product_names = []
    used_names = set()

    for idx, row in products_df.iterrows():
        portuguese_category = row.get("product_category_name", "")

        # Get English category
        if pd.isna(portuguese_category) or portuguese_category == "":
            english_category = "Uncategorized"
        else:
            english_category = translation_map.get(portuguese_category, "Uncategorized")

        # Generate unique name
        attempts = 0
        while attempts < 100:
            name = generate_product_name(english_category, idx + attempts)
            if name not in used_names:
                used_names.add(name)
                break
            attempts += 1
        else:
            # Fallback: add product_id suffix for uniqueness
            name = f"{name} #{row['product_id'][:8]}"

        product_names.append(name)

        if (idx + 1) % 5000 == 0:
            print(f"  Processed {idx + 1:,} products...")

    # Add product_name column
    products_df["product_name"] = product_names

    # Reorder columns to put product_name after product_id
    cols = products_df.columns.tolist()
    cols.remove("product_name")
    cols.insert(1, "product_name")
    products_df = products_df[cols]

    # Save updated CSV
    print(f"\nSaving updated products to: {products_path}")
    products_df.to_csv(products_path, index=False)
    print(f"  Saved {len(products_df):,} products with names")

    # Show sample
    print("\n" + "=" * 60)
    print("Sample Product Names")
    print("=" * 60)
    sample = products_df[["product_id", "product_name", "product_category_name"]].head(15)
    for _, row in sample.iterrows():
        print(f"  {row['product_name'][:50]:<50} ({row['product_category_name']})")

    print("\nDone!")


if __name__ == "__main__":
    main()
