"""Lumen Goods' catalog: products, their seeded reviews, today's deals and the coupon codes."""

PRODUCTS = [
    {"id": 1, "name": "Desk Lamp", "category": "Office", "price": 34.99, "stock": 12},
    {"id": 2, "name": "Ceramic Mug", "category": "Kitchen", "price": 12.5, "stock": 40},
    {"id": 3, "name": "Linen Throw Blanket", "category": "Home", "price": 59.0, "stock": 8},
    {"id": 4, "name": "Camping Lantern", "category": "Outdoor", "price": 24.99, "stock": 0},
    {"id": 5, "name": "Chef's Knife", "category": "Kitchen", "price": 89.99, "stock": 5},
    {"id": 6, "name": "Notebook Set", "category": "Office", "price": 9.99, "stock": 100},
    {"id": 7, "name": "Cotton Bath Towel", "category": "Home", "price": 19.99, "stock": 25},
    {"id": 8, "name": "Trail Water Bottle", "category": "Outdoor", "price": 18.0, "stock": 30},
    {"id": 9, "name": "Cast Iron Skillet", "category": "Kitchen", "price": 45.0, "stock": 9},
    {"id": 10, "name": "Ergonomic Chair", "category": "Office", "price": 249.0, "stock": 3},
    {"id": 11, "name": "Scented Candle", "category": "Home", "price": 15.99, "stock": 0},
    {"id": 12, "name": "Folding Camp Chair", "category": "Outdoor", "price": 39.99, "stock": 14},
    {"id": 13, "name": "Pour-Over Coffee Set", "category": "Kitchen", "price": 54.99, "stock": 11},
    {"id": 14, "name": "Wireless Mouse", "category": "Office", "price": 29.99, "stock": 22},
    {"id": 15, "name": "Wall Clock", "category": "Home", "price": 27.5, "stock": 6},
    {"id": 16, "name": "Hiking Backpack", "category": "Outdoor", "price": 119.0, "stock": 7},
    {"id": 17, "name": "Glass Storage Jars", "category": "Kitchen", "price": 22.0, "stock": 0},
    {"id": 18, "name": "Monitor Stand", "category": "Office", "price": 64.0, "stock": 10},
    {"id": 19, "name": "Table Plant Pot", "category": "Home", "price": 16.0, "stock": 18},
    {"id": 20, "name": "Picnic Blanket", "category": "Outdoor", "price": 32.0, "stock": 13},
]

DESCRIPTIONS = {
    1: "An adjustable aluminium lamp with a warm, flicker-free LED and a weighted base.",
    2: "A 350 ml stoneware mug, glazed by hand. Dishwasher and microwave safe.",
    3: "Stonewashed linen, 130 x 170 cm, soft from the first use and softer every wash.",
    4: "A rechargeable LED lantern with three brightness levels and 40 hours of light.",
    5: "A 20 cm chef's knife forged from a single piece of high-carbon steel.",
    6: "Three A5 notebooks with dotted pages, lay-flat binding and recycled covers.",
    7: "Heavy 600 gsm cotton towel that dries quickly and stays fluffy.",
    8: "A 750 ml insulated steel bottle that keeps water cold for 24 hours.",
    9: "A pre-seasoned 26 cm skillet for searing, baking and everything in between.",
    10: "Adjustable lumbar support, breathable mesh back and 4D armrests.",
    11: "Soy wax candle with cedar and bergamot, about 45 hours of burn time.",
    12: "Lightweight aluminium chair that folds into its own carry bag.",
    13: "A glass dripper, carafe and 100 filters for a clean, bright cup.",
    14: "A quiet, rechargeable mouse that pairs with up to three devices.",
    15: "A 30 cm silent-sweep clock with an oak frame.",
    16: "A 40 l pack with a ventilated back, rain cover and hip-belt pockets.",
    17: "A set of four borosilicate jars with airtight bamboo lids.",
    18: "A solid walnut riser that lifts your screen to eye level.",
    19: "A matte ceramic pot with a drainage hole and a cork saucer.",
    20: "A water-resistant 150 x 200 cm blanket that rolls up with a leather strap.",
}

# (name, stars, text) per product; the average shown on the site is computed from these.
REVIEWS = {
    1: [
        ("Priya", 5, "Bright, warm light and a sturdy base."),
        ("Marco", 4, "Great lamp, the arm is a little stiff at first."),
        ("Lena", 4, "Looks good on my desk and the light is easy on the eyes."),
        ("Tom", 3, "Fine, but I expected a dimmer at this price."),
    ],
    2: [
        ("Aisha", 5, "My favourite mug, holds heat well."),
        ("Ben", 5, "Beautiful glaze, every one is a little different."),
        ("Chloe", 4, "Lovely, slightly smaller than I imagined."),
    ],
    3: [("Dev", 4, "Soft and warm, a bit of shedding at first."), ("Emma", 5, "Gorgeous colour and texture.")],
    4: [
        ("Farid", 4, "Bright enough for the whole tent."),
        ("Gina", 3, "The battery lasts, the clip feels flimsy."),
        ("Hugo", 5, "Survived a rainy week in the hills."),
    ],
    5: [
        ("Ines", 5, "Razor sharp out of the box."),
        ("Jack", 5, "Perfect balance, a joy to use."),
        ("Kira", 5, "Best knife I have owned."),
        ("Liam", 4, "Excellent, needs drying straight after washing."),
    ],
    6: [("Mona", 4, "Nice paper, fountain pen friendly."), ("Nils", 4, "Good value for three notebooks.")],
    7: [
        ("Omar", 3, "Absorbent, but it took a few washes to stop shedding."),
        ("Pia", 4, "Thick and soft."),
        ("Quinn", 5, "Hotel quality at home."),
    ],
    8: [("Rosa", 5, "Ice still in it the next day."), ("Sam", 4, "Great bottle, the lid is a bit tight.")],
    9: [
        ("Tara", 5, "Perfect sear every time."),
        ("Umar", 4, "Heavy, as it should be."),
        ("Vera", 5, "Came well seasoned."),
    ],
    10: [
        ("Will", 4, "My back thanks me."),
        ("Xia", 3, "Comfortable, assembly took an hour."),
        ("Yusuf", 4, "Sturdy and adjustable."),
    ],
    11: [("Zara", 5, "Smells amazing, fills the room."), ("Adam", 4, "Lovely scent, burns evenly.")],
    12: [
        ("Bea", 4, "Light and easy to carry."),
        ("Carl", 4, "Comfortable for long evenings."),
        ("Dina", 3, "Good chair, the bag is a tight fit."),
    ],
    13: [
        ("Eli", 5, "Makes a lovely clean cup."),
        ("Fay", 4, "Easy to use and clean."),
        ("Gus", 4, "Nice set, the carafe is thinner than expected."),
    ],
    14: [("Hana", 4, "Quiet clicks, good battery."), ("Ivan", 5, "Switching between laptops is seamless.")],
    15: [("Jade", 3, "Pretty, a bit smaller than pictured."), ("Kai", 4, "Truly silent, no ticking.")],
    16: [
        ("Leo", 5, "Carried it for a week, no sore shoulders."),
        ("Mia", 5, "So many useful pockets."),
        ("Ned", 4, "Great pack, the rain cover is snug."),
    ],
    17: [
        ("Ola", 4, "Airtight and pretty."),
        ("Pat", 4, "Good jars, lids need hand washing."),
        ("Raj", 5, "My pantry looks so tidy now."),
    ],
    18: [
        ("Sia", 4, "Solid wood, looks great."),
        ("Teo", 5, "Fixed my neck pain."),
        ("Uma", 4, "Sturdy, holds a 27 inch screen."),
    ],
    19: [("Val", 5, "My fern loves it."), ("Wes", 4, "Nice matte finish.")],
    20: [("Xander", 4, "Big enough for four."), ("Yara", 5, "Stayed dry on damp grass.")],
}

# Today's deals: the product, its deal price, and in how many days (after today) the deal ends.
DEALS = [
    {"product_id": 3, "deal_price": 47.2, "days": 0},
    {"product_id": 9, "deal_price": 36.0, "days": 1},
    {"product_id": 16, "deal_price": 95.2, "days": 2},
]

COUPONS = {"SAVE10": 0.10}

CATEGORY_COLORS = {"Home": "#c9734f", "Kitchen": "#3f7d6e", "Office": "#4b5f9e", "Outdoor": "#7a8a2e"}

BY_ID = {p["id"]: p for p in PRODUCTS}
