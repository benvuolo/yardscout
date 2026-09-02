/* Junkyard Hunter — static datasets: parts database, yard directory. */
const DATABASE = [
  {
    name: "Toyota 4Runner (3rd Gen)",
    make: "Toyota",
    years: "1996–2002",
    category: "SUV",
    frequency: "Common",
    notes: "Everywhere in yards. Off-road and overland culture keeps demand sky-high. Parts sell in hours on T4R.org and local Facebook groups.",
    parts: [
      { name: "Rear E-Locker Actuator Motor", rarity: "Legendary", priceRange: [250, 500], yardCost: 15, sellOn: "T4R.org, eBay" },
      { name: "Multi-Mode Transfer Case Shift Motor", rarity: "Epic", priceRange: [150, 350], yardCost: 15, sellOn: "eBay, Forums" },
      { name: "OEM Roof Rack Crossbars", rarity: "Rare", priceRange: [150, 300], yardCost: 20, sellOn: "eBay, Craigslist" },
      { name: "Limited Headlights (clear lens)", rarity: "Rare", priceRange: [100, 250], yardCost: 25, sellOn: "eBay" },
      { name: "Rear Hatch Glass (non-cracked)", rarity: "Uncommon", priceRange: [75, 175], yardCost: 20, sellOn: "eBay" },
      { name: "OEM Hood Scoop (SR5 Sport)", rarity: "Rare", priceRange: [80, 180], yardCost: 15, sellOn: "T4R.org" },
      { name: "Center Console Lid (uncracked)", rarity: "Rare", priceRange: [60, 140], yardCost: 8, sellOn: "eBay" },
      { name: "OEM Mudflaps (set)", rarity: "Uncommon", priceRange: [40, 90], yardCost: 8, sellOn: "eBay" },
      { name: "Heated Side Mirrors (pair)", rarity: "Rare", priceRange: [80, 175], yardCost: 15, sellOn: "eBay" },
      { name: "Rear Diff Locker Switch Assembly", rarity: "Epic", priceRange: [100, 225], yardCost: 8, sellOn: "T4R.org" },
    ]
  },
  {
    name: "Toyota 4Runner (4th Gen)",
    make: "Toyota",
    years: "2003–2009",
    category: "SUV",
    frequency: "Common",
    notes: "4th gens are hitting yards now as they age out. V8 models' parts are especially sought after. Trail Edition parts are gold.",
    parts: [
      { name: "KDSS Sway Bar Links/Actuators", rarity: "Legendary", priceRange: [200, 500], yardCost: 20, sellOn: "T4R.org, eBay" },
      { name: "Rear E-Locker Actuator", rarity: "Epic", priceRange: [200, 400], yardCost: 20, sellOn: "T4R.org" },
      { name: "OEM Roof Rack (full)", rarity: "Rare", priceRange: [150, 350], yardCost: 25, sellOn: "eBay" },
      { name: "Sport Edition Headlights (blacked out)", rarity: "Epic", priceRange: [150, 300], yardCost: 30, sellOn: "T4R.org" },
      { name: "Multi-Mode 4WD Actuator", rarity: "Rare", priceRange: [100, 250], yardCost: 15, sellOn: "eBay" },
      { name: "JBL Speaker/Amp System", rarity: "Rare", priceRange: [100, 225], yardCost: 20, sellOn: "eBay" },
      { name: "Heated Power Mirrors (pair)", rarity: "Uncommon", priceRange: [75, 175], yardCost: 15, sellOn: "eBay" },
      { name: "Rear Window Regulator", rarity: "Uncommon", priceRange: [50, 120], yardCost: 10, sellOn: "eBay" },
      { name: "OEM Running Boards", rarity: "Uncommon", priceRange: [75, 175], yardCost: 15, sellOn: "Facebook, CL" },
    ]
  },
  {
    name: "Toyota 4Runner (5th Gen)",
    make: "Toyota",
    years: "2010–2024",
    category: "SUV",
    frequency: "Occasional",
    notes: "Starting to trickle into yards (wrecks, flood). TRD Pro and Trail parts are instant money. OEM LED headlights are huge.",
    parts: [
      { name: "TRD Pro Grille (with TSS sensor)", rarity: "Legendary", priceRange: [300, 600], yardCost: 40, sellOn: "T4R.org, eBay" },
      { name: "OEM LED Headlights (pair)", rarity: "Epic", priceRange: [400, 800], yardCost: 60, sellOn: "eBay" },
      { name: "Crawl Control Module", rarity: "Epic", priceRange: [200, 450], yardCost: 25, sellOn: "T4R.org" },
      { name: "TRD Pro Skid Plate", rarity: "Rare", priceRange: [150, 350], yardCost: 30, sellOn: "eBay, Forums" },
      { name: "Entune Head Unit (8\" touchscreen)", rarity: "Rare", priceRange: [200, 400], yardCost: 40, sellOn: "eBay" },
      { name: "Power Rear Hatch Struts/Motor", rarity: "Uncommon", priceRange: [75, 175], yardCost: 15, sellOn: "eBay" },
      { name: "Rear Diff Lock Actuator", rarity: "Epic", priceRange: [150, 350], yardCost: 15, sellOn: "T4R.org" },
      { name: "TRD Shift Knob", rarity: "Uncommon", priceRange: [40, 100], yardCost: 5, sellOn: "eBay" },
      { name: "Blind Spot Monitor Sensors", rarity: "Rare", priceRange: [75, 200], yardCost: 10, sellOn: "eBay" },
    ]
  },
  {
    name: "Toyota Tacoma (1st Gen)",
    make: "Toyota",
    years: "1995–2004",
    category: "Truck",
    frequency: "Occasional",
    notes: "Taco tax is absurd. Even junked ones get stripped fast. TRD parts, clean body panels, and small trim pieces all sell. Rust-free beds from dry-climate yards ship to rust-belt buyers.",
    parts: [
      { name: "TRD Off-Road Decals / Badges", rarity: "Rare", priceRange: [30, 80], yardCost: 2, sellOn: "eBay" },
      { name: "OEM Fender Flares (color-matched)", rarity: "Epic", priceRange: [200, 500], yardCost: 30, sellOn: "Tacoma World, eBay" },
      { name: "Tailgate (clean, no dents)", rarity: "Rare", priceRange: [150, 400], yardCost: 30, sellOn: "Facebook, CL" },
      { name: "Headlights (clear, non-hazed)", rarity: "Rare", priceRange: [80, 200], yardCost: 20, sellOn: "eBay" },
      { name: "TRD Shift Knob", rarity: "Rare", priceRange: [50, 125], yardCost: 5, sellOn: "Tacoma World" },
      { name: "Leaf Spring Hangers (rust-free)", rarity: "Epic", priceRange: [100, 250], yardCost: 15, sellOn: "Tacoma World" },
      { name: "OEM Bed Mat / Liner", rarity: "Uncommon", priceRange: [50, 125], yardCost: 10, sellOn: "CL, Facebook" },
      { name: "Instrument Cluster (tach model)", rarity: "Rare", priceRange: [75, 175], yardCost: 15, sellOn: "eBay" },
      { name: "Door Handles (exterior chrome)", rarity: "Uncommon", priceRange: [25, 60], yardCost: 3, sellOn: "eBay" },
    ]
  },
  {
    name: "Toyota Tacoma (2nd Gen)",
    make: "Toyota",
    years: "2005–2015",
    category: "Truck",
    frequency: "Common",
    notes: "One of the most popular trucks in yards right now. TRD Sport and Off-Road parts have a huge aftermarket. Tons of local buyers.",
    parts: [
      { name: "TRD Off-Road/Sport Hood Scoop", rarity: "Rare", priceRange: [100, 250], yardCost: 20, sellOn: "Tacoma World, eBay" },
      { name: "OEM LED Taillights (2012+)", rarity: "Epic", priceRange: [150, 350], yardCost: 30, sellOn: "eBay" },
      { name: "Tailgate (clean)", rarity: "Rare", priceRange: [150, 350], yardCost: 30, sellOn: "CL, Facebook" },
      { name: "TRD Skid Plate (aluminum)", rarity: "Epic", priceRange: [150, 350], yardCost: 25, sellOn: "Tacoma World" },
      { name: "OEM Fog Lights + Bezels", rarity: "Uncommon", priceRange: [50, 130], yardCost: 10, sellOn: "eBay" },
      { name: "Power Heated Mirrors (pair)", rarity: "Uncommon", priceRange: [75, 175], yardCost: 15, sellOn: "eBay" },
      { name: "Bed Cleats / Tie-Downs (set)", rarity: "Uncommon", priceRange: [30, 75], yardCost: 5, sellOn: "eBay" },
      { name: "OEM Tonneau Cover Clamps", rarity: "Uncommon", priceRange: [20, 50], yardCost: 3, sellOn: "eBay" },
      { name: "Steering Wheel (leather w/ controls)", rarity: "Rare", priceRange: [75, 200], yardCost: 15, sellOn: "eBay, Tacoma World" },
    ]
  },
  {
    name: "Toyota Tacoma (3rd Gen)",
    make: "Toyota",
    years: "2016–2023",
    category: "Truck",
    frequency: "Occasional",
    notes: "Wrecked 3rd gens are goldmines. TRD Pro parts are absolute fire sellers. Even basic trim pieces from these are worth grabbing.",
    parts: [
      { name: "TRD Pro Grille (matte black)", rarity: "Legendary", priceRange: [200, 450], yardCost: 30, sellOn: "Tacoma World, eBay" },
      { name: "OEM LED Headlights (pair)", rarity: "Epic", priceRange: [350, 700], yardCost: 50, sellOn: "eBay" },
      { name: "TRD Pro Skid Plate", rarity: "Epic", priceRange: [200, 400], yardCost: 30, sellOn: "Tacoma World, eBay" },
      { name: "Tonneau Cover (OEM tri-fold)", rarity: "Rare", priceRange: [200, 450], yardCost: 40, sellOn: "CL, Facebook" },
      { name: "Infotainment Touchscreen (8\")", rarity: "Rare", priceRange: [200, 400], yardCost: 35, sellOn: "eBay" },
      { name: "TRD Shift Knob (manual)", rarity: "Rare", priceRange: [60, 150], yardCost: 5, sellOn: "eBay" },
      { name: "Blind Spot Monitor Mirrors", rarity: "Uncommon", priceRange: [100, 225], yardCost: 15, sellOn: "eBay" },
      { name: "OEM Bed Rack Accessory Mounts", rarity: "Rare", priceRange: [50, 125], yardCost: 8, sellOn: "Tacoma World" },
    ]
  },
  {
    name: "Toyota Tundra (1st Gen)",
    make: "Toyota",
    years: "2000–2006",
    category: "Truck",
    frequency: "Common",
    notes: "Tons of these in yards. Step bumpers, tailgates, and TRD bits are the targets. Full-size Toyota truck parts ship well.",
    parts: [
      { name: "Tailgate (clean, no dents)", rarity: "Rare", priceRange: [150, 350], yardCost: 30, sellOn: "Facebook, CL" },
      { name: "TRD Supercharger Intercooler", rarity: "Legendary", priceRange: [200, 500], yardCost: 25, sellOn: "TundraTalk, eBay" },
      { name: "Limited Headlights", rarity: "Rare", priceRange: [100, 225], yardCost: 25, sellOn: "eBay" },
      { name: "OEM Step Bumper (chrome)", rarity: "Uncommon", priceRange: [75, 175], yardCost: 15, sellOn: "CL" },
      { name: "Access Cab Rear Seats", rarity: "Uncommon", priceRange: [75, 175], yardCost: 15, sellOn: "eBay" },
      { name: "Steering Wheel w/ Audio Controls", rarity: "Uncommon", priceRange: [50, 125], yardCost: 10, sellOn: "eBay" },
    ]
  },
  {
    name: "Toyota Tundra (2nd Gen)",
    make: "Toyota",
    years: "2007–2021",
    category: "Truck",
    frequency: "Common",
    notes: "These are work trucks that get beat on. CrewMax beds are hard to find separately. TRD and Limited trim parts are premium.",
    parts: [
      { name: "OEM LED Headlights (2018+)", rarity: "Epic", priceRange: [300, 600], yardCost: 50, sellOn: "eBay" },
      { name: "TRD Pro Grille", rarity: "Epic", priceRange: [200, 400], yardCost: 30, sellOn: "TundraTalk, eBay" },
      { name: "Tailgate (w/ backup camera)", rarity: "Rare", priceRange: [200, 450], yardCost: 40, sellOn: "Facebook, CL" },
      { name: "JBL Premium Speakers + Amp", rarity: "Rare", priceRange: [150, 350], yardCost: 25, sellOn: "eBay" },
      { name: "Power Fold Tow Mirrors (pair)", rarity: "Rare", priceRange: [200, 400], yardCost: 30, sellOn: "eBay" },
      { name: "Tonneau Cover (OEM hard)", rarity: "Rare", priceRange: [200, 450], yardCost: 40, sellOn: "CL, Facebook" },
      { name: "Heated/Cooled Seat Module", rarity: "Rare", priceRange: [100, 225], yardCost: 15, sellOn: "eBay" },
      { name: "OEM Running Boards (chrome)", rarity: "Uncommon", priceRange: [75, 175], yardCost: 15, sellOn: "CL" },
    ]
  },
  {
    name: "Toyota Sequoia",
    make: "Toyota",
    years: "2001–2022",
    category: "SUV",
    frequency: "Occasional",
    notes: "Big family haulers are yard staples. These share tons of parts with Tundra. 3rd row seat hardware is always in demand.",
    parts: [
      { name: "3rd Row Seat (complete, clean)", rarity: "Rare", priceRange: [200, 450], yardCost: 40, sellOn: "eBay, CL" },
      { name: "Power Liftgate Struts/Motor", rarity: "Rare", priceRange: [100, 250], yardCost: 15, sellOn: "eBay" },
      { name: "JBL Amp + Sub", rarity: "Rare", priceRange: [100, 250], yardCost: 20, sellOn: "eBay" },
      { name: "Rear Air Suspension Bags", rarity: "Epic", priceRange: [150, 350], yardCost: 20, sellOn: "eBay" },
      { name: "Heated Side Mirrors (BSM)", rarity: "Uncommon", priceRange: [75, 175], yardCost: 15, sellOn: "eBay" },
      { name: "OEM Roof Rack Crossbars", rarity: "Uncommon", priceRange: [80, 200], yardCost: 15, sellOn: "eBay" },
    ]
  },
  {
    name: "Toyota FJ Cruiser",
    make: "Toyota",
    years: "2007–2014",
    category: "SUV",
    frequency: "Rare",
    notes: "FJs rarely hit yards and when they do, the vultures circle immediately. Even small trim is gold because no one wants to scrap their FJ.",
    parts: [
      { name: "OEM Roof Rack (full, with ladder)", rarity: "Legendary", priceRange: [300, 700], yardCost: 40, sellOn: "FJCruiserForums, eBay" },
      { name: "Front Grille (white or colored)", rarity: "Epic", priceRange: [150, 350], yardCost: 25, sellOn: "eBay" },
      { name: "Rear Swing-Out Tire Carrier", rarity: "Epic", priceRange: [200, 450], yardCost: 30, sellOn: "Forums, eBay" },
      { name: "Side Mirror Caps (color-matched)", rarity: "Rare", priceRange: [50, 125], yardCost: 8, sellOn: "eBay" },
      { name: "Rear Diff Locker Actuator", rarity: "Epic", priceRange: [150, 300], yardCost: 15, sellOn: "FJCruiserForums" },
      { name: "A-TRAC / Crawl Control Module", rarity: "Epic", priceRange: [150, 350], yardCost: 20, sellOn: "Forums" },
      { name: "Suicide Door Hinges + Latch", rarity: "Rare", priceRange: [75, 200], yardCost: 10, sellOn: "eBay" },
      { name: "OEM Fog Lights", rarity: "Uncommon", priceRange: [50, 125], yardCost: 10, sellOn: "eBay" },
    ]
  },
  {
    name: "Toyota Land Cruiser (80 Series)",
    make: "Toyota",
    years: "1990–1997",
    category: "SUV",
    frequency: "Rare",
    notes: "Land Cruiser tax is insane. An 80 in a yard is a feeding frenzy. Lockers and KDSS parts alone justify the trip.",
    parts: [
      { name: "Factory Front & Rear Locker Actuators", rarity: "Legendary", priceRange: [300, 700], yardCost: 25, sellOn: "IH8MUD, eBay" },
      { name: "Birfield Joint / CV Axle Shafts", rarity: "Epic", priceRange: [150, 350], yardCost: 25, sellOn: "IH8MUD" },
      { name: "Center Diff Lock CDL Actuator", rarity: "Epic", priceRange: [150, 350], yardCost: 15, sellOn: "IH8MUD" },
      { name: "Factory Roof Rack (heavy duty)", rarity: "Rare", priceRange: [200, 500], yardCost: 40, sellOn: "IH8MUD, eBay" },
      { name: "Rear Window Regulator Motor", rarity: "Rare", priceRange: [100, 225], yardCost: 15, sellOn: "eBay" },
      { name: "Front Grille (chrome/painted)", rarity: "Rare", priceRange: [75, 200], yardCost: 15, sellOn: "eBay" },
      { name: "Instrument Cluster", rarity: "Rare", priceRange: [100, 250], yardCost: 20, sellOn: "IH8MUD" },
      { name: "Uncracked Dash Pad", rarity: "Epic", priceRange: [150, 350], yardCost: 15, sellOn: "IH8MUD, eBay" },
    ]
  },
  {
    name: "Toyota Land Cruiser (100 Series)",
    make: "Toyota",
    years: "1998–2007",
    category: "SUV",
    frequency: "Rare",
    notes: "100 series are more common than 80s in yards but still rare. AHC suspension parts and center diff lock pieces move fast.",
    parts: [
      { name: "AHC (Active Height Control) Pump", rarity: "Legendary", priceRange: [400, 900], yardCost: 40, sellOn: "IH8MUD, eBay" },
      { name: "AHC Height Sensors", rarity: "Epic", priceRange: [100, 275], yardCost: 10, sellOn: "IH8MUD" },
      { name: "Center Diff Lock Actuator", rarity: "Epic", priceRange: [150, 350], yardCost: 15, sellOn: "IH8MUD" },
      { name: "Multi-Terrain Select Module", rarity: "Rare", priceRange: [100, 250], yardCost: 15, sellOn: "IH8MUD" },
      { name: "OEM Roof Rack", rarity: "Rare", priceRange: [200, 450], yardCost: 35, sellOn: "eBay" },
      { name: "Rear Liftgate Glass Struts", rarity: "Uncommon", priceRange: [30, 75], yardCost: 5, sellOn: "eBay" },
      { name: "Mark Levinson Amp/Speakers", rarity: "Rare", priceRange: [150, 350], yardCost: 25, sellOn: "eBay" },
    ]
  },
  {
    name: "Toyota Camry",
    make: "Toyota",
    years: "1997–2024",
    category: "Sedan",
    frequency: "Common",
    notes: "Camrys are everywhere. Most parts are cheap BUT: OEM headlights (especially LED), hybrid battery modules, and clean interiors sell consistently.",
    parts: [
      { name: "OEM LED Headlights (2018+, pair)", rarity: "Rare", priceRange: [250, 500], yardCost: 40, sellOn: "eBay" },
      { name: "Hybrid Battery Module (individual cells)", rarity: "Epic", priceRange: [100, 300], yardCost: 15, sellOn: "eBay, hybrid shops" },
      { name: "XSE/TRD Rear Spoiler", rarity: "Rare", priceRange: [75, 200], yardCost: 15, sellOn: "eBay" },
      { name: "Entune/Audio Plus Head Unit", rarity: "Uncommon", priceRange: [100, 250], yardCost: 20, sellOn: "eBay" },
      { name: "Power Seat Track Motor", rarity: "Uncommon", priceRange: [50, 125], yardCost: 10, sellOn: "eBay" },
      { name: "Side Mirror (BSM, heated, power fold)", rarity: "Uncommon", priceRange: [75, 175], yardCost: 15, sellOn: "eBay" },
    ]
  },
  {
    name: "Toyota Corolla",
    make: "Toyota",
    years: "1998–2024",
    category: "Sedan",
    frequency: "Common",
    notes: "Most common car in any yard. Low individual part values but volume makes up for it. OEM headlights and interior switches are consistent sellers.",
    parts: [
      { name: "OEM LED Headlights (2020+, pair)", rarity: "Rare", priceRange: [200, 450], yardCost: 35, sellOn: "eBay" },
      { name: "OEM Projector Headlights (pair)", rarity: "Uncommon", priceRange: [100, 225], yardCost: 25, sellOn: "eBay" },
      { name: "Steering Wheel (leather, w/ controls)", rarity: "Uncommon", priceRange: [50, 125], yardCost: 10, sellOn: "eBay" },
      { name: "Window Master Switch", rarity: "Uncommon", priceRange: [30, 75], yardCost: 5, sellOn: "eBay" },
      { name: "Climate Control Module", rarity: "Uncommon", priceRange: [40, 100], yardCost: 8, sellOn: "eBay" },
    ]
  },
  {
    name: "Toyota Highlander",
    make: "Toyota",
    years: "2001–2024",
    category: "Crossover",
    frequency: "Common",
    notes: "Family SUV staple. 3rd row parts, hybrid components, and power liftgate hardware are the money items.",
    parts: [
      { name: "3rd Row Seat (complete)", rarity: "Rare", priceRange: [200, 400], yardCost: 35, sellOn: "eBay, CL" },
      { name: "Power Liftgate Motor/Struts", rarity: "Rare", priceRange: [100, 250], yardCost: 15, sellOn: "eBay" },
      { name: "Hybrid Battery Cells", rarity: "Epic", priceRange: [100, 300], yardCost: 15, sellOn: "eBay, hybrid shops" },
      { name: "OEM Roof Rails + Crossbars", rarity: "Uncommon", priceRange: [100, 225], yardCost: 20, sellOn: "eBay" },
      { name: "JBL Speaker System", rarity: "Uncommon", priceRange: [75, 175], yardCost: 15, sellOn: "eBay" },
      { name: "Heated/Cooled Seat Module", rarity: "Rare", priceRange: [75, 200], yardCost: 10, sellOn: "eBay" },
    ]
  },
  {
    name: "Toyota RAV4",
    make: "Toyota",
    years: "2001–2024",
    category: "Crossover",
    frequency: "Common",
    notes: "One of the best-selling crossovers nationally. Adventure/TRD trim parts are the unobtanium here. Hybrid parts are great sellers.",
    parts: [
      { name: "Adventure/TRD Grille", rarity: "Rare", priceRange: [100, 250], yardCost: 20, sellOn: "eBay" },
      { name: "OEM LED Headlights (2019+)", rarity: "Rare", priceRange: [250, 500], yardCost: 40, sellOn: "eBay" },
      { name: "Power Liftgate Assembly", rarity: "Uncommon", priceRange: [100, 225], yardCost: 15, sellOn: "eBay" },
      { name: "Hybrid Inverter/Converter", rarity: "Epic", priceRange: [200, 500], yardCost: 30, sellOn: "eBay" },
      { name: "Entune Head Unit (newer touch)", rarity: "Uncommon", priceRange: [100, 250], yardCost: 20, sellOn: "eBay" },
      { name: "Roof Rails (Adventure model)", rarity: "Uncommon", priceRange: [75, 175], yardCost: 15, sellOn: "eBay" },
    ]
  },
  {
    name: "Toyota Prius",
    make: "Toyota",
    years: "2004–2024",
    category: "Hatchback",
    frequency: "Common",
    notes: "Surprisingly lucrative. Hybrid battery cells sell individually to rebuilders. Inverters, DC-DC converters, and catalytic converters are all high-value small pulls.",
    parts: [
      { name: "Hybrid Battery Cells (individual)", rarity: "Epic", priceRange: [20, 50], yardCost: 3, sellOn: "eBay (sell in bulk)" },
      { name: "DC-DC Converter", rarity: "Rare", priceRange: [150, 350], yardCost: 20, sellOn: "eBay" },
      { name: "Hybrid Inverter (Water Pump)", rarity: "Rare", priceRange: [100, 275], yardCost: 20, sellOn: "eBay" },
      { name: "Combination Meter / Dash Display", rarity: "Rare", priceRange: [100, 225], yardCost: 15, sellOn: "eBay" },
      { name: "Smart Key ECU Module", rarity: "Uncommon", priceRange: [50, 125], yardCost: 10, sellOn: "eBay" },
      { name: "Backup Camera", rarity: "Uncommon", priceRange: [40, 100], yardCost: 8, sellOn: "eBay" },
    ]
  },
  {
    name: "Toyota Sienna",
    make: "Toyota",
    years: "2004–2024",
    category: "Van",
    frequency: "Common",
    notes: "Big family vans everywhere. Power sliding door motors are CONSTANTLY failing and in demand. SE model parts are premium.",
    parts: [
      { name: "Power Sliding Door Motor", rarity: "Epic", priceRange: [150, 350], yardCost: 15, sellOn: "eBay" },
      { name: "Power Sliding Door Cable", rarity: "Rare", priceRange: [75, 200], yardCost: 10, sellOn: "eBay" },
      { name: "3rd Row Seat (Stow-n-Go style)", rarity: "Rare", priceRange: [150, 350], yardCost: 30, sellOn: "eBay, CL" },
      { name: "SE Rear Spoiler", rarity: "Rare", priceRange: [75, 175], yardCost: 15, sellOn: "eBay" },
      { name: "JBL Amp/Speakers", rarity: "Uncommon", priceRange: [75, 175], yardCost: 15, sellOn: "eBay" },
      { name: "Power Liftgate Struts", rarity: "Uncommon", priceRange: [50, 125], yardCost: 10, sellOn: "eBay" },
      { name: "Rear Entertainment Screen", rarity: "Rare", priceRange: [75, 200], yardCost: 15, sellOn: "eBay" },
    ]
  },
  {
    name: "Jeep Cherokee XJ",
    make: "Jeep",
    years: "1984–2001",
    category: "SUV",
    frequency: "Common",
    notes: "Jeep culture is massive. XJs are gateway off-roaders. Header panels, clean fenders, and small 4WD bits are instant sellers.",
    parts: [
      { name: "Header Panel (nose piece, clean)", rarity: "Legendary", priceRange: [200, 500], yardCost: 25, sellOn: "NAXJA, eBay" },
      { name: "Clean Fenders (no rust, no flares)", rarity: "Epic", priceRange: [100, 275], yardCost: 20, sellOn: "eBay, Facebook" },
      { name: "Overhead Console (digital readout)", rarity: "Rare", priceRange: [75, 200], yardCost: 10, sellOn: "eBay" },
      { name: "4WD Vacuum Switch / Actuator", rarity: "Rare", priceRange: [50, 125], yardCost: 8, sellOn: "eBay" },
      { name: "Dash Bezel / Climate Panel", rarity: "Rare", priceRange: [40, 100], yardCost: 5, sellOn: "eBay" },
      { name: "Door Hinges (rust-free pair)", rarity: "Uncommon", priceRange: [30, 75], yardCost: 5, sellOn: "eBay" },
      { name: "Headliner (clean, no sag)", rarity: "Epic", priceRange: [75, 200], yardCost: 10, sellOn: "NAXJA, eBay" },
      { name: "Rear Bumper (stock chrome)", rarity: "Uncommon", priceRange: [40, 100], yardCost: 10, sellOn: "CL" },
      { name: "Window Crank Handles (manual)", rarity: "Uncommon", priceRange: [15, 40], yardCost: 2, sellOn: "eBay" },
    ]
  },
  {
    name: "Jeep Grand Cherokee WJ/WK",
    make: "Jeep",
    years: "1999–2010",
    category: "SUV",
    frequency: "Common",
    notes: "Tons of these in yards. Transfer case motors, Quadra-Drive parts, and heated seats are the pulls. Overland edition bits are premium.",
    parts: [
      { name: "Transfer Case Shift Motor (NP247/242)", rarity: "Rare", priceRange: [75, 200], yardCost: 10, sellOn: "JeepForum, eBay" },
      { name: "Heated Leather Seats (pair)", rarity: "Rare", priceRange: [150, 350], yardCost: 30, sellOn: "CL, Facebook" },
      { name: "Instrument Cluster (no dead pixels)", rarity: "Rare", priceRange: [75, 175], yardCost: 15, sellOn: "eBay" },
      { name: "Infinity Gold Speakers + Amp", rarity: "Uncommon", priceRange: [50, 125], yardCost: 10, sellOn: "eBay" },
      { name: "OEM Roof Rack", rarity: "Uncommon", priceRange: [75, 175], yardCost: 15, sellOn: "eBay" },
      { name: "Power Seat Track Motor", rarity: "Uncommon", priceRange: [40, 100], yardCost: 8, sellOn: "eBay" },
      { name: "Headlights (non-hazed pair)", rarity: "Uncommon", priceRange: [75, 175], yardCost: 20, sellOn: "eBay" },
    ]
  },
  {
    name: "Jeep Wrangler TJ",
    make: "Jeep",
    years: "1997–2006",
    category: "SUV",
    frequency: "Occasional",
    notes: "TJs don't usually get junked — they get fixed. When one DOES show up, half-doors, hardtops, and soft top hardware are instant sells.",
    parts: [
      { name: "Hardtop (full, clean)", rarity: "Legendary", priceRange: [500, 1500], yardCost: 75, sellOn: "Wrangler Forum, CL" },
      { name: "Half Doors (pair)", rarity: "Legendary", priceRange: [300, 800], yardCost: 40, sellOn: "Wrangler Forum, eBay" },
      { name: "Soft Top Frame + Bows", rarity: "Epic", priceRange: [150, 350], yardCost: 25, sellOn: "eBay, CL" },
      { name: "OEM Bumpers (front or rear)", rarity: "Rare", priceRange: [75, 200], yardCost: 15, sellOn: "CL" },
      { name: "Roll Bar Padding (complete set)", rarity: "Rare", priceRange: [50, 125], yardCost: 8, sellOn: "eBay" },
      { name: "Center Console (Sahara/Rubicon)", rarity: "Rare", priceRange: [50, 125], yardCost: 8, sellOn: "eBay" },
      { name: "Dana 44 Locker Actuator (Rubicon)", rarity: "Epic", priceRange: [100, 275], yardCost: 10, sellOn: "Wrangler Forum" },
    ]
  },
  {
    name: "Jeep Wrangler JK",
    make: "Jeep",
    years: "2007–2018",
    category: "SUV",
    frequency: "Occasional",
    notes: "JKs are more common than TJs in yards now. Hardtop pieces, doors, and Rubicon-specific parts fly off the shelf.",
    parts: [
      { name: "Hardtop (Freedom top panels)", rarity: "Legendary", priceRange: [400, 1000], yardCost: 60, sellOn: "Wrangler Forum, CL" },
      { name: "Half Doors / Tube Doors (pair)", rarity: "Epic", priceRange: [200, 500], yardCost: 30, sellOn: "eBay, CL" },
      { name: "Rubicon E-Locker Actuators", rarity: "Epic", priceRange: [100, 275], yardCost: 10, sellOn: "Wrangler Forum" },
      { name: "Rubicon Rock Rails", rarity: "Rare", priceRange: [100, 250], yardCost: 20, sellOn: "eBay" },
      { name: "OEM LED Tail Lights", rarity: "Rare", priceRange: [75, 175], yardCost: 15, sellOn: "eBay" },
      { name: "Uconnect Touchscreen Head Unit", rarity: "Uncommon", priceRange: [75, 200], yardCost: 15, sellOn: "eBay" },
      { name: "Fender Flares (Rubicon wide)", rarity: "Uncommon", priceRange: [75, 175], yardCost: 15, sellOn: "eBay" },
    ]
  },
  {
    name: "Subaru Outback",
    make: "Subaru",
    years: "2000–2024",
    category: "Wagon",
    frequency: "Common",
    notes: "Outbacks are in every yard, especially in snow states. Headlights, Eyesight cameras, and roof rack parts are consistent sellers.",
    parts: [
      { name: "Eyesight Camera Module", rarity: "Epic", priceRange: [200, 500], yardCost: 25, sellOn: "eBay" },
      { name: "OEM LED Headlights (2020+, pair)", rarity: "Rare", priceRange: [250, 500], yardCost: 40, sellOn: "eBay" },
      { name: "OEM Roof Rails + Crossbars", rarity: "Uncommon", priceRange: [100, 250], yardCost: 20, sellOn: "eBay" },
      { name: "Harman Kardon Amp/Speakers", rarity: "Rare", priceRange: [100, 225], yardCost: 15, sellOn: "eBay" },
      { name: "Heated Seat Module", rarity: "Uncommon", priceRange: [50, 125], yardCost: 8, sellOn: "eBay" },
      { name: "Uncracked Dash Pad (older gens)", rarity: "Rare", priceRange: [75, 200], yardCost: 10, sellOn: "eBay, Forums" },
      { name: "Wilderness Grille/Bumper Cladding", rarity: "Epic", priceRange: [150, 350], yardCost: 25, sellOn: "eBay" },
    ]
  },
  {
    name: "Subaru Forester",
    make: "Subaru",
    years: "1998–2024",
    category: "Crossover",
    frequency: "Common",
    notes: "Second most common Subaru in yards. XT turbo parts cross-sell to WRX community. Wilderness edition parts are new but in demand.",
    parts: [
      { name: "XT Turbo Intercooler + Piping", rarity: "Epic", priceRange: [150, 350], yardCost: 20, sellOn: "NASIOC, eBay" },
      { name: "Eyesight Camera Module", rarity: "Epic", priceRange: [200, 450], yardCost: 25, sellOn: "eBay" },
      { name: "Panoramic Sunroof Glass", rarity: "Rare", priceRange: [150, 350], yardCost: 25, sellOn: "eBay" },
      { name: "XT Hood Scoop (functional)", rarity: "Rare", priceRange: [75, 175], yardCost: 10, sellOn: "NASIOC" },
      { name: "Sport Grille (blacked out)", rarity: "Uncommon", priceRange: [50, 125], yardCost: 10, sellOn: "eBay" },
      { name: "X-Mode Switch Assembly", rarity: "Uncommon", priceRange: [40, 100], yardCost: 8, sellOn: "eBay" },
      { name: "OEM Roof Rack", rarity: "Uncommon", priceRange: [75, 175], yardCost: 15, sellOn: "eBay" },
    ]
  },
  {
    name: "Subaru WRX / STI",
    make: "Subaru",
    years: "2002–2024",
    category: "Sport",
    frequency: "Occasional",
    notes: "STI parts are gold in the Subaru scene. Brembo brakes, STI wings, intercoolers, and interior bits — no need to touch the engine.",
    parts: [
      { name: "STI Brembo Brake Calipers (set)", rarity: "Epic", priceRange: [300, 700], yardCost: 60, sellOn: "NASIOC, eBay" },
      { name: "STI Wing / Spoiler (OEM)", rarity: "Rare", priceRange: [200, 450], yardCost: 40, sellOn: "NASIOC, eBay" },
      { name: "STI Steering Wheel (flat bottom)", rarity: "Rare", priceRange: [100, 275], yardCost: 15, sellOn: "NASIOC" },
      { name: "Top-Mount Intercooler (TMIC)", rarity: "Rare", priceRange: [100, 250], yardCost: 15, sellOn: "NASIOC, eBay" },
      { name: "STI Short Shifter Assembly", rarity: "Rare", priceRange: [75, 175], yardCost: 10, sellOn: "NASIOC" },
      { name: "DCCD Controller Switch", rarity: "Epic", priceRange: [75, 200], yardCost: 8, sellOn: "NASIOC" },
      { name: "Recaro/STI Seats (pair)", rarity: "Epic", priceRange: [400, 900], yardCost: 60, sellOn: "NASIOC, eBay" },
      { name: "Hood Scoop (functional)", rarity: "Uncommon", priceRange: [75, 175], yardCost: 15, sellOn: "eBay" },
    ]
  },
  {
    name: "Honda CR-V",
    make: "Honda",
    years: "1997–2024",
    category: "Crossover",
    frequency: "Common",
    notes: "Tons of CR-Vs in yards. 1st gen fold-out table is a cult item. Newer LED headlights and infotainment screens sell well.",
    parts: [
      { name: "1st Gen Fold-Out Picnic Table", rarity: "Legendary", priceRange: [100, 300], yardCost: 10, sellOn: "eBay, Honda-Tech" },
      { name: "OEM LED Headlights (2017+, pair)", rarity: "Rare", priceRange: [250, 500], yardCost: 40, sellOn: "eBay" },
      { name: "Rear Spare Tire Cover (1st/2nd gen)", rarity: "Rare", priceRange: [50, 125], yardCost: 8, sellOn: "eBay" },
      { name: "Tailgate (clean, w/ glass)", rarity: "Rare", priceRange: [100, 250], yardCost: 25, sellOn: "CL" },
      { name: "Honda Sensing Radar Module", rarity: "Rare", priceRange: [100, 250], yardCost: 15, sellOn: "eBay" },
      { name: "Power Liftgate Motor", rarity: "Uncommon", priceRange: [75, 175], yardCost: 12, sellOn: "eBay" },
    ]
  },
  {
    name: "Honda Civic (8th–11th Gen)",
    make: "Honda",
    years: "2006–2024",
    category: "Sedan",
    frequency: "Common",
    notes: "Si and Type R parts cross over to a huge mod community. Even base model LED headlights sell well. Consistent volume business.",
    parts: [
      { name: "Si/Type R Seats (pair)", rarity: "Epic", priceRange: [300, 700], yardCost: 50, sellOn: "Honda-Tech, eBay" },
      { name: "OEM LED Headlights (pair)", rarity: "Rare", priceRange: [200, 450], yardCost: 35, sellOn: "eBay" },
      { name: "Si Rear Spoiler (OEM)", rarity: "Rare", priceRange: [75, 175], yardCost: 15, sellOn: "eBay" },
      { name: "Si/Sport Steering Wheel", rarity: "Rare", priceRange: [75, 200], yardCost: 12, sellOn: "Honda-Tech" },
      { name: "Infotainment Touchscreen", rarity: "Uncommon", priceRange: [75, 200], yardCost: 15, sellOn: "eBay" },
      { name: "Si Front Lip (OEM)", rarity: "Rare", priceRange: [75, 175], yardCost: 12, sellOn: "Honda-Tech, eBay" },
    ]
  },
  {
    name: "Honda Accord",
    make: "Honda",
    years: "1998–2024",
    category: "Sedan",
    frequency: "Common",
    notes: "Always available. Sport and Touring trim parts are the play. LED headlights from 2018+ are money.",
    parts: [
      { name: "OEM LED Headlights (2018+, pair)", rarity: "Rare", priceRange: [300, 550], yardCost: 40, sellOn: "eBay" },
      { name: "Sport Front Lip / Underbody Kit", rarity: "Rare", priceRange: [75, 200], yardCost: 12, sellOn: "eBay, Honda-Tech" },
      { name: "Heated/Cooled Seat Modules", rarity: "Rare", priceRange: [75, 200], yardCost: 10, sellOn: "eBay" },
      { name: "Honda Sensing Radar Unit", rarity: "Uncommon", priceRange: [75, 200], yardCost: 12, sellOn: "eBay" },
      { name: "EX-L Leather Steering Wheel", rarity: "Uncommon", priceRange: [50, 125], yardCost: 10, sellOn: "eBay" },
    ]
  },
  {
    name: "Honda Odyssey",
    make: "Honda",
    years: "1999–2024",
    category: "Van",
    frequency: "Common",
    notes: "Another family-hauler staple. Power sliding door parts are ALWAYS needed. Rear entertainment systems sell well too.",
    parts: [
      { name: "Power Sliding Door Motor", rarity: "Epic", priceRange: [150, 350], yardCost: 15, sellOn: "eBay" },
      { name: "Power Sliding Door Latch/Cable", rarity: "Rare", priceRange: [75, 175], yardCost: 10, sellOn: "eBay" },
      { name: "Rear Entertainment System (screen)", rarity: "Rare", priceRange: [100, 250], yardCost: 20, sellOn: "eBay" },
      { name: "2nd Row Magic Seats (complete)", rarity: "Rare", priceRange: [200, 450], yardCost: 35, sellOn: "CL, eBay" },
      { name: "OEM Roof Rack + Crossbars", rarity: "Uncommon", priceRange: [75, 175], yardCost: 15, sellOn: "eBay" },
      { name: "Touring Navigation Unit", rarity: "Uncommon", priceRange: [75, 175], yardCost: 15, sellOn: "eBay" },
    ]
  },
  {
    name: "Honda Element",
    make: "Honda",
    years: "2003–2011",
    category: "Crossover",
    frequency: "Occasional",
    notes: "Cult car with a devoted community. Discontinued in 2011 so parts are drying up fast. Suicide doors, roof rack, and interior bits are all gold.",
    parts: [
      { name: "Rear Suicide Door Latch/Hinge", rarity: "Epic", priceRange: [75, 200], yardCost: 10, sellOn: "eBay, Element Owners Club" },
      { name: "OEM Roof Rack (full)", rarity: "Epic", priceRange: [150, 350], yardCost: 25, sellOn: "eBay" },
      { name: "Rubber Floor Mats (OEM set)", rarity: "Rare", priceRange: [50, 125], yardCost: 8, sellOn: "eBay" },
      { name: "SC/EX Front Bumper (clean)", rarity: "Rare", priceRange: [75, 200], yardCost: 15, sellOn: "eBay" },
      { name: "Tailgate (w/ glass, clean)", rarity: "Rare", priceRange: [100, 225], yardCost: 20, sellOn: "CL" },
      { name: "Side Mirror (pair)", rarity: "Uncommon", priceRange: [50, 125], yardCost: 10, sellOn: "eBay" },
      { name: "Center Console / Armrest", rarity: "Uncommon", priceRange: [40, 100], yardCost: 5, sellOn: "eBay" },
    ]
  },
  {
    name: "Ford F-150 (10th–14th Gen)",
    make: "Ford",
    years: "1997–2024",
    category: "Truck",
    frequency: "Common",
    notes: "Best-selling truck in America. Yards are full of them. Power-fold tow mirrors, FX4 bits, tailgates, and LED headlights are the money parts.",
    parts: [
      { name: "Power-Fold Tow Mirrors (pair)", rarity: "Epic", priceRange: [250, 550], yardCost: 40, sellOn: "eBay, F150Forum" },
      { name: "OEM LED Headlights (2015+, pair)", rarity: "Epic", priceRange: [300, 600], yardCost: 50, sellOn: "eBay" },
      { name: "Tailgate (w/ step & camera)", rarity: "Rare", priceRange: [200, 450], yardCost: 40, sellOn: "CL, Facebook" },
      { name: "FX4 Skid Plates (set)", rarity: "Rare", priceRange: [100, 225], yardCost: 15, sellOn: "F150Forum, eBay" },
      { name: "Raptor Grille / Raptor Letters", rarity: "Legendary", priceRange: [200, 500], yardCost: 25, sellOn: "eBay, F150Forum" },
      { name: "SYNC 3 Touchscreen (8\")", rarity: "Rare", priceRange: [150, 350], yardCost: 25, sellOn: "eBay" },
      { name: "Power Running Boards (retractable)", rarity: "Epic", priceRange: [300, 700], yardCost: 40, sellOn: "eBay" },
      { name: "Tonneau Cover (hard tri-fold)", rarity: "Rare", priceRange: [200, 450], yardCost: 40, sellOn: "CL, Facebook" },
      { name: "Blind Spot Monitoring Sensors", rarity: "Uncommon", priceRange: [50, 125], yardCost: 8, sellOn: "eBay" },
    ]
  },
  {
    name: "Ford Bronco (Full Size)",
    make: "Ford",
    years: "1980–1996",
    category: "SUV",
    frequency: "Occasional",
    notes: "OBS Broncos are collector vehicles now. Rust-free body panels from dry-climate yards ship to rust-belt buyers for serious money.",
    parts: [
      { name: "Removable Hardtop (full, clean)", rarity: "Legendary", priceRange: [1000, 3000], yardCost: 150, sellOn: "Bronco forums, eBay" },
      { name: "Tailgate (complete, no rust)", rarity: "Epic", priceRange: [300, 700], yardCost: 40, sellOn: "Forums, CL" },
      { name: "Eddie Bauer Interior Trim", rarity: "Rare", priceRange: [100, 300], yardCost: 20, sellOn: "eBay" },
      { name: "Clean Dash Pad (uncracked)", rarity: "Epic", priceRange: [100, 275], yardCost: 10, sellOn: "eBay, Forums" },
      { name: "Headlights / Grille Assembly", rarity: "Rare", priceRange: [75, 200], yardCost: 15, sellOn: "eBay" },
      { name: "Soft Top Bows + Hardware", rarity: "Rare", priceRange: [100, 250], yardCost: 15, sellOn: "Forums" },
    ]
  },
  {
    name: "Ford Explorer (3rd–5th Gen)",
    make: "Ford",
    years: "2002–2019",
    category: "SUV",
    frequency: "Common",
    notes: "Police interceptor parts cross-sell to the civilian Explorer market. 3rd row seats, tow packages, and brake parts from cop cars are great pulls.",
    parts: [
      { name: "3rd Row Seat (complete)", rarity: "Rare", priceRange: [150, 350], yardCost: 30, sellOn: "eBay, CL" },
      { name: "Police Interceptor Brake Calipers", rarity: "Rare", priceRange: [100, 225], yardCost: 15, sellOn: "eBay" },
      { name: "OEM Tow Hitch + Wiring", rarity: "Uncommon", priceRange: [75, 175], yardCost: 15, sellOn: "CL" },
      { name: "SYNC Touchscreen Head Unit", rarity: "Uncommon", priceRange: [75, 175], yardCost: 15, sellOn: "eBay" },
      { name: "Rear Air Suspension Compressor", rarity: "Rare", priceRange: [100, 250], yardCost: 15, sellOn: "eBay" },
      { name: "Power Liftgate Motor", rarity: "Uncommon", priceRange: [75, 175], yardCost: 12, sellOn: "eBay" },
    ]
  },
  {
    name: "Ford Ranger",
    make: "Ford",
    years: "1993–2024",
    category: "Truck",
    frequency: "Common",
    notes: "Compact trucks are getting popular again. FX4 parts, Tremor bits, and clean body panels are the items to target.",
    parts: [
      { name: "FX4 Skid Plates", rarity: "Rare", priceRange: [75, 175], yardCost: 12, sellOn: "TheRangerStation, eBay" },
      { name: "Flareside Bed Panels (clean)", rarity: "Rare", priceRange: [100, 250], yardCost: 20, sellOn: "Facebook, CL" },
      { name: "OEM Tonneau Cover", rarity: "Rare", priceRange: [100, 250], yardCost: 20, sellOn: "CL" },
      { name: "4WD Shift Motor (GEM module)", rarity: "Rare", priceRange: [75, 175], yardCost: 12, sellOn: "eBay" },
      { name: "Edge/Sport Bumper Cover", rarity: "Uncommon", priceRange: [50, 125], yardCost: 10, sellOn: "eBay" },
      { name: "Tailgate (w/ handle, clean)", rarity: "Uncommon", priceRange: [75, 175], yardCost: 15, sellOn: "CL" },
    ]
  },
  {
    name: "Ford Mustang (S197/S550)",
    make: "Ford",
    years: "2005–2024",
    category: "Sport",
    frequency: "Common",
    notes: "Mustangs crash a lot. GT/Shelby parts are premium. Brembo brakes, Performance Pack bits, and body panels are easy sells.",
    parts: [
      { name: "GT Brembo Brake Calipers (set)", rarity: "Epic", priceRange: [300, 600], yardCost: 50, sellOn: "Mustang6G, eBay" },
      { name: "GT350/PP2 Front Splitter", rarity: "Epic", priceRange: [200, 450], yardCost: 25, sellOn: "Mustang6G, eBay" },
      { name: "Performance Pack Rear Spoiler", rarity: "Rare", priceRange: [100, 250], yardCost: 20, sellOn: "eBay" },
      { name: "OEM LED Headlights (pair)", rarity: "Rare", priceRange: [250, 500], yardCost: 40, sellOn: "eBay" },
      { name: "Recaro Seats (pair, PP/GT350)", rarity: "Epic", priceRange: [500, 1200], yardCost: 75, sellOn: "Mustang6G, eBay" },
      { name: "Digital Gauge Cluster (2018+)", rarity: "Rare", priceRange: [200, 400], yardCost: 25, sellOn: "eBay" },
      { name: "GT Quad-Tip Exhaust Tips", rarity: "Uncommon", priceRange: [50, 125], yardCost: 10, sellOn: "eBay" },
    ]
  },
  {
    name: "Chevy Silverado / GMC Sierra (OBS)",
    make: "Chevrolet",
    years: "1988–1998",
    category: "Truck",
    frequency: "Common",
    notes: "OBS scene is exploding. Clean rust-free body panels from dry-climate yards are worth shipping nationwide. Interior parts and trim are in high demand.",
    parts: [
      { name: "Rust-Free Cab Corners / Rocker Panels", rarity: "Epic", priceRange: [150, 400], yardCost: 20, sellOn: "eBay (ship to rust belt)" },
      { name: "454 SS Badges / Trim", rarity: "Legendary", priceRange: [100, 300], yardCost: 5, sellOn: "eBay" },
      { name: "Bucket Seat Interior (Silverado trim)", rarity: "Rare", priceRange: [150, 350], yardCost: 30, sellOn: "GM-Trucks, eBay" },
      { name: "Full Gauge Cluster (tach, oil, temp)", rarity: "Rare", priceRange: [75, 175], yardCost: 12, sellOn: "eBay" },
      { name: "Clean Tailgate (no dents)", rarity: "Rare", priceRange: [100, 250], yardCost: 20, sellOn: "CL, Facebook" },
      { name: "SS Steering Wheel (leather)", rarity: "Rare", priceRange: [50, 150], yardCost: 8, sellOn: "eBay" },
      { name: "Bed-Side Trim / Moldings (rust-free)", rarity: "Uncommon", priceRange: [40, 100], yardCost: 5, sellOn: "eBay" },
      { name: "Power Window Switches", rarity: "Uncommon", priceRange: [25, 60], yardCost: 3, sellOn: "eBay" },
    ]
  },
  {
    name: "Chevy Silverado / Sierra (NBS+)",
    make: "Chevrolet",
    years: "1999–2024",
    category: "Truck",
    frequency: "Common",
    notes: "Always available. Power-fold mirrors, Z71 parts, tailgates with cameras, and LED headlights are the consistent money items.",
    parts: [
      { name: "Power-Fold Tow Mirrors (pair)", rarity: "Epic", priceRange: [200, 450], yardCost: 30, sellOn: "eBay" },
      { name: "OEM LED Headlights (2019+, pair)", rarity: "Epic", priceRange: [300, 600], yardCost: 50, sellOn: "eBay" },
      { name: "Z71 Skid Plates", rarity: "Rare", priceRange: [75, 175], yardCost: 12, sellOn: "eBay" },
      { name: "Tailgate (w/ EZ-Lift & camera)", rarity: "Rare", priceRange: [200, 450], yardCost: 40, sellOn: "CL, Facebook" },
      { name: "MultiPro Tailgate Steps", rarity: "Epic", priceRange: [200, 500], yardCost: 30, sellOn: "eBay" },
      { name: "Bose Speaker System + Amp", rarity: "Uncommon", priceRange: [75, 175], yardCost: 15, sellOn: "eBay" },
      { name: "Power Retractable Running Boards", rarity: "Epic", priceRange: [250, 600], yardCost: 35, sellOn: "eBay" },
      { name: "Tonneau Cover (hard)", rarity: "Rare", priceRange: [150, 350], yardCost: 30, sellOn: "CL, Facebook" },
    ]
  },
  {
    name: "Chevy Tahoe / Suburban / Yukon",
    make: "Chevrolet",
    years: "1995–2024",
    category: "SUV",
    frequency: "Common",
    notes: "The big-family vehicle of choice. 3rd row parts, rear air suspension, and AutoRide components are great pulls.",
    parts: [
      { name: "AutoRide Rear Shocks (pair)", rarity: "Epic", priceRange: [150, 350], yardCost: 20, sellOn: "eBay" },
      { name: "Rear Air Suspension Compressor", rarity: "Rare", priceRange: [100, 250], yardCost: 15, sellOn: "eBay" },
      { name: "3rd Row Seat (complete)", rarity: "Rare", priceRange: [200, 450], yardCost: 35, sellOn: "CL, eBay" },
      { name: "Power-Fold Tow Mirrors (pair)", rarity: "Rare", priceRange: [150, 350], yardCost: 25, sellOn: "eBay" },
      { name: "Rear Liftgate Glass Hinge (97-00)", rarity: "Rare", priceRange: [50, 125], yardCost: 5, sellOn: "eBay" },
      { name: "Bose Amp + Subwoofer", rarity: "Uncommon", priceRange: [75, 175], yardCost: 15, sellOn: "eBay" },
      { name: "Z71 / RST Badges + Trim", rarity: "Uncommon", priceRange: [25, 75], yardCost: 3, sellOn: "eBay" },
      { name: "Rear Entertainment Screen", rarity: "Rare", priceRange: [75, 200], yardCost: 15, sellOn: "eBay" },
    ]
  },
  {
    name: "Chevy Camaro (5th/6th Gen)",
    make: "Chevrolet",
    years: "2010–2024",
    category: "Sport",
    frequency: "Common",
    notes: "Camaros crash plenty. SS Brembo brakes, 1LE/ZL1 aero parts, and Recaro seats are the targets. No need to mess with the drivetrain.",
    parts: [
      { name: "SS Brembo Brake Calipers (set)", rarity: "Epic", priceRange: [300, 600], yardCost: 50, sellOn: "eBay, CamaroSix" },
      { name: "1LE/ZL1 Front Splitter", rarity: "Epic", priceRange: [200, 500], yardCost: 25, sellOn: "eBay, CamaroSix" },
      { name: "Recaro Seats (pair)", rarity: "Epic", priceRange: [400, 900], yardCost: 60, sellOn: "eBay" },
      { name: "OEM LED Headlights (pair)", rarity: "Rare", priceRange: [250, 500], yardCost: 40, sellOn: "eBay" },
      { name: "SS/ZL1 Rear Spoiler", rarity: "Rare", priceRange: [100, 250], yardCost: 20, sellOn: "eBay" },
      { name: "HUD (Heads-Up Display) Module", rarity: "Rare", priceRange: [150, 350], yardCost: 20, sellOn: "eBay" },
    ]
  },
  {
    name: "Ram 1500/2500/3500 (4th/5th Gen)",
    make: "Ram",
    years: "2009–2024",
    category: "Truck",
    frequency: "Common",
    notes: "Rams are everywhere. The 12\" Uconnect screens are goldmines. Power-fold mirrors, tow packages, and air suspension parts are big sellers.",
    parts: [
      { name: "12\" Uconnect Touchscreen (5th gen)", rarity: "Epic", priceRange: [400, 800], yardCost: 50, sellOn: "eBay" },
      { name: "Power-Fold Tow Mirrors (pair)", rarity: "Epic", priceRange: [250, 500], yardCost: 35, sellOn: "eBay" },
      { name: "Air Suspension Compressor (5th gen)", rarity: "Rare", priceRange: [200, 400], yardCost: 25, sellOn: "eBay" },
      { name: "Multifunction Tailgate (60/40 split)", rarity: "Epic", priceRange: [200, 450], yardCost: 35, sellOn: "eBay" },
      { name: "LED Headlights (pair)", rarity: "Rare", priceRange: [250, 500], yardCost: 40, sellOn: "eBay" },
      { name: "Tonneau Cover (RamBox)", rarity: "Rare", priceRange: [200, 450], yardCost: 35, sellOn: "CL" },
      { name: "Alpine/Harman Kardon Speaker + Amp", rarity: "Uncommon", priceRange: [100, 225], yardCost: 15, sellOn: "eBay" },
      { name: "Heated Steering Wheel Module", rarity: "Uncommon", priceRange: [50, 125], yardCost: 8, sellOn: "eBay" },
    ]
  },
  {
    name: "Dodge Durango",
    make: "Dodge",
    years: "2004–2024",
    category: "SUV",
    frequency: "Common",
    notes: "Family hauler that gets driven hard. R/T and SRT parts have crossover appeal. 3rd row and tow parts are consistent.",
    parts: [
      { name: "SRT/R/T Brembo Brakes", rarity: "Epic", priceRange: [250, 500], yardCost: 40, sellOn: "eBay" },
      { name: "3rd Row Seat (complete)", rarity: "Rare", priceRange: [150, 350], yardCost: 30, sellOn: "CL, eBay" },
      { name: "Uconnect 8.4\" Touchscreen", rarity: "Uncommon", priceRange: [100, 225], yardCost: 15, sellOn: "eBay" },
      { name: "SRT Hood (functional scoop)", rarity: "Epic", priceRange: [200, 500], yardCost: 30, sellOn: "eBay" },
      { name: "Power Liftgate Motor", rarity: "Uncommon", priceRange: [75, 175], yardCost: 12, sellOn: "eBay" },
      { name: "Rear Air Suspension Parts", rarity: "Rare", priceRange: [100, 225], yardCost: 15, sellOn: "eBay" },
    ]
  },
  {
    name: "Nissan Frontier",
    make: "Nissan",
    years: "1998–2024",
    category: "Truck",
    frequency: "Common",
    notes: "Budget truck that gets worked hard. PRO-4X parts and clean body panels are the play here.",
    parts: [
      { name: "PRO-4X Off-Road Skid Plates", rarity: "Rare", priceRange: [100, 225], yardCost: 15, sellOn: "ClubFrontier, eBay" },
      { name: "Bilstein Shocks (PRO-4X, set)", rarity: "Rare", priceRange: [150, 300], yardCost: 30, sellOn: "eBay" },
      { name: "Utili-Track Bed Channel System", rarity: "Uncommon", priceRange: [50, 125], yardCost: 8, sellOn: "eBay" },
      { name: "Clean Tailgate", rarity: "Uncommon", priceRange: [75, 175], yardCost: 15, sellOn: "CL" },
      { name: "Headlights (non-hazed pair)", rarity: "Uncommon", priceRange: [75, 175], yardCost: 15, sellOn: "eBay" },
      { name: "OEM Roof Rack", rarity: "Uncommon", priceRange: [50, 125], yardCost: 10, sellOn: "eBay" },
    ]
  },
  {
    name: "Nissan Xterra",
    make: "Nissan",
    years: "2000–2015",
    category: "SUV",
    frequency: "Occasional",
    notes: "Discontinued so parts are drying up. Overlanding crowd loves Xterras. Roof rack, bumper steps, and PRO-4X bits are prime targets.",
    parts: [
      { name: "OEM Roof Rack (full, tube-style)", rarity: "Epic", priceRange: [150, 350], yardCost: 25, sellOn: "TheNewX, eBay" },
      { name: "PRO-4X Bilstein Shocks (set)", rarity: "Rare", priceRange: [150, 300], yardCost: 30, sellOn: "eBay" },
      { name: "Rear Bumper Step", rarity: "Rare", priceRange: [75, 175], yardCost: 10, sellOn: "TheNewX, eBay" },
      { name: "OEM Skid Plates", rarity: "Rare", priceRange: [75, 175], yardCost: 12, sellOn: "TheNewX" },
      { name: "Clean Fender Flares", rarity: "Uncommon", priceRange: [50, 125], yardCost: 10, sellOn: "eBay" },
      { name: "Rear Diff Locker Switch", rarity: "Rare", priceRange: [50, 125], yardCost: 5, sellOn: "TheNewX" },
    ]
  },
  {
    name: "Nissan Pathfinder (R50/R51)",
    make: "Nissan",
    years: "1996–2012",
    category: "SUV",
    frequency: "Common",
    notes: "Solid off-road platform that shares parts with the Xterra/Frontier platform. Body panels and 4WD components are in demand.",
    parts: [
      { name: "Rear Diff Locker Actuator", rarity: "Rare", priceRange: [75, 175], yardCost: 10, sellOn: "eBay" },
      { name: "Running Boards (OEM)", rarity: "Uncommon", priceRange: [50, 125], yardCost: 10, sellOn: "eBay" },
      { name: "OEM Roof Rack", rarity: "Uncommon", priceRange: [50, 125], yardCost: 10, sellOn: "eBay" },
      { name: "Clean Headlights (pair)", rarity: "Uncommon", priceRange: [75, 175], yardCost: 15, sellOn: "eBay" },
      { name: "4WD Actuator Motor", rarity: "Rare", priceRange: [75, 175], yardCost: 10, sellOn: "eBay" },
    ]
  },
  {
    name: "Hyundai Tucson / Kia Sportage",
    make: "Hyundai/Kia",
    years: "2010–2024",
    category: "Crossover",
    frequency: "Common",
    notes: "Tons of these now due to engine recall junkers. Headlights, infotainment, and body panels from non-recalled models sell well as replacements.",
    parts: [
      { name: "OEM LED Headlights (pair)", rarity: "Rare", priceRange: [200, 400], yardCost: 30, sellOn: "eBay" },
      { name: "Touchscreen Infotainment (10.25\")", rarity: "Rare", priceRange: [200, 400], yardCost: 25, sellOn: "eBay" },
      { name: "Power Liftgate Motor", rarity: "Uncommon", priceRange: [75, 175], yardCost: 12, sellOn: "eBay" },
      { name: "Heated/Cooled Seat Module", rarity: "Uncommon", priceRange: [50, 125], yardCost: 8, sellOn: "eBay" },
      { name: "Panoramic Sunroof Glass", rarity: "Rare", priceRange: [150, 350], yardCost: 25, sellOn: "eBay" },
      { name: "Smart Cruise Radar Module", rarity: "Uncommon", priceRange: [75, 175], yardCost: 10, sellOn: "eBay" },
    ]
  },
  {
    name: "Hyundai Santa Fe / Kia Sorento",
    make: "Hyundai/Kia",
    years: "2007–2024",
    category: "SUV",
    frequency: "Common",
    notes: "Growing junkyard presence. Same engine recall issues mean bodies show up with good parts. 3rd row seats and infotainment are targets.",
    parts: [
      { name: "3rd Row Seat (complete)", rarity: "Rare", priceRange: [150, 300], yardCost: 25, sellOn: "eBay" },
      { name: "OEM LED Headlights (pair)", rarity: "Rare", priceRange: [200, 400], yardCost: 30, sellOn: "eBay" },
      { name: "Infinity/Harman Kardon Amp + Speakers", rarity: "Uncommon", priceRange: [75, 175], yardCost: 12, sellOn: "eBay" },
      { name: "Power Liftgate Assembly", rarity: "Uncommon", priceRange: [75, 175], yardCost: 12, sellOn: "eBay" },
      { name: "Smart Cruise/Lane Keep Camera", rarity: "Uncommon", priceRange: [100, 225], yardCost: 15, sellOn: "eBay" },
    ]
  },
  {
    name: "Ford Focus (ST/RS/SE)",
    make: "Ford",
    years: "2000–2018",
    category: "Hatchback",
    frequency: "Common",
    notes: "Common in yards. Most are base models, but ST and RS trims are goldmines. ST3 HID headlights, Recaro seats, and intercoolers cross-sell to a huge mod community. Even base model SYNC screens sell.",
    parts: [
      { name: "ST3/RS HID Headlights (pair)", rarity: "Epic", priceRange: [250, 500], yardCost: 45, sellOn: "FocusST.org, eBay" },
      { name: "Recaro Seats (pair, ST/RS)", rarity: "Epic", priceRange: [400, 900], yardCost: 71, sellOn: "FocusST.org, eBay" },
      { name: "ST/RS Intercooler", rarity: "Rare", priceRange: [100, 250], yardCost: 95, sellOn: "FocusST.org, eBay" },
      { name: "SYNC 3 Touchscreen (8\")", rarity: "Rare", priceRange: [150, 350], yardCost: 45, sellOn: "eBay" },
      { name: "ST/RS Steering Wheel (flat bottom)", rarity: "Rare", priceRange: [100, 225], yardCost: 37, sellOn: "FocusST.org, eBay" },
      { name: "ST Rear Spoiler (OEM)", rarity: "Uncommon", priceRange: [50, 125], yardCost: 40, sellOn: "eBay" },
      { name: "OEM Fog Lights + Bezels", rarity: "Uncommon", priceRange: [40, 100], yardCost: 22, sellOn: "eBay" },
      { name: "RS Brake Calipers (set)", rarity: "Epic", priceRange: [300, 600], yardCost: 28, sellOn: "FocusST.org, eBay" },
    ]
  },
  {
    name: "Ford Fusion (Sport/Titanium)",
    make: "Ford",
    years: "2006–2020",
    category: "Sedan",
    frequency: "Common",
    notes: "Common in yards. Titanium and Sport trims have the money parts. SYNC 3 screens, LED headlights, and front bumpers with parking sensor holes are consistent sellers.",
    parts: [
      { name: "OEM LED Headlights (2017+, pair)", rarity: "Rare", priceRange: [250, 500], yardCost: 45, sellOn: "eBay" },
      { name: "SYNC 3 Touchscreen (8\")", rarity: "Rare", priceRange: [150, 350], yardCost: 45, sellOn: "eBay" },
      { name: "Titanium Front Bumper (w/ sensors)", rarity: "Rare", priceRange: [100, 250], yardCost: 73, sellOn: "eBay" },
      { name: "Sport Twin-Turbo Intercooler", rarity: "Epic", priceRange: [150, 350], yardCost: 95, sellOn: "eBay" },
      { name: "Power Heated Mirrors (BSM, pair)", rarity: "Uncommon", priceRange: [75, 175], yardCost: 42, sellOn: "eBay" },
      { name: "Heated/Cooled Seat Module", rarity: "Uncommon", priceRange: [50, 125], yardCost: 29, sellOn: "eBay" },
      { name: "Sony Audio Amp + Speakers", rarity: "Uncommon", priceRange: [75, 175], yardCost: 44, sellOn: "eBay" },
    ]
  },
  {
    name: "Hyundai Elantra (Sport/N)",
    make: "Hyundai",
    years: "2001–2023",
    category: "Sedan",
    frequency: "Common",
    notes: "Common in yards. Engine recall junkers mean lots of good body/electrical parts on otherwise trashed cars. Sport and N parts have cross-appeal to the Kia Forte tuner crowd.",
    parts: [
      { name: "OEM LED Headlights (2017+, pair)", rarity: "Rare", priceRange: [200, 400], yardCost: 45, sellOn: "eBay" },
      { name: "N/Sport Front Bumper Assembly", rarity: "Epic", priceRange: [200, 450], yardCost: 73, sellOn: "eBay" },
      { name: "Touchscreen Infotainment (10.25\")", rarity: "Rare", priceRange: [200, 400], yardCost: 60, sellOn: "eBay" },
      { name: "N Line Steering Wheel (flat bottom)", rarity: "Rare", priceRange: [100, 225], yardCost: 37, sellOn: "eBay" },
      { name: "Smart Cruise Radar Module", rarity: "Uncommon", priceRange: [75, 175], yardCost: 22, sellOn: "eBay" },
      { name: "Sport/N Rear Spoiler", rarity: "Uncommon", priceRange: [50, 125], yardCost: 40, sellOn: "eBay" },
      { name: "Wireless Charging Pad Module", rarity: "Uncommon", priceRange: [40, 100], yardCost: 29, sellOn: "eBay" },
    ]
  },
  {
    name: "Dodge Grand Caravan",
    make: "Dodge",
    years: "1996–2020",
    category: "Van",
    frequency: "Common",
    notes: "Common in yards. Big family hauler like the Sienna. Power sliding door motors CONSTANTLY fail and owners need replacements. Stow-N-Go seats and rear entertainment systems are easy money.",
    parts: [
      { name: "Power Sliding Door Motor", rarity: "Epic", priceRange: [125, 300], yardCost: 47, sellOn: "eBay" },
      { name: "Power Sliding Door Control Module", rarity: "Rare", priceRange: [75, 200], yardCost: 29, sellOn: "eBay" },
      { name: "Stow-N-Go 2nd Row Seat (each)", rarity: "Rare", priceRange: [150, 350], yardCost: 55, sellOn: "eBay, CL" },
      { name: "Stow-N-Go 3rd Row Seat", rarity: "Rare", priceRange: [100, 250], yardCost: 34, sellOn: "eBay, CL" },
      { name: "Rear Entertainment Screen + DVD", rarity: "Rare", priceRange: [75, 200], yardCost: 60, sellOn: "eBay" },
      { name: "Power Sliding Door Cable/Track", rarity: "Uncommon", priceRange: [50, 125], yardCost: 29, sellOn: "eBay" },
      { name: "Uconnect Touchscreen Head Unit", rarity: "Uncommon", priceRange: [75, 175], yardCost: 45, sellOn: "eBay" },
    ]
  },
  {
    name: "Hyundai Sonata",
    make: "Hyundai",
    years: "1999–2023",
    category: "Sedan",
    frequency: "Common",
    notes: "Common in yards. Like the Elantra, engine recall junkers with perfectly good electronics and body parts. 2020+ touchscreens and LED headlights are big sellers. HUD modules from Limited trims are rare finds.",
    parts: [
      { name: "OEM LED Headlights (2018+, pair)", rarity: "Rare", priceRange: [250, 500], yardCost: 45, sellOn: "eBay" },
      { name: "Touchscreen Infotainment (10.25\")", rarity: "Rare", priceRange: [200, 450], yardCost: 60, sellOn: "eBay" },
      { name: "Heads-Up Display Module (Limited)", rarity: "Epic", priceRange: [300, 700], yardCost: 60, sellOn: "eBay" },
      { name: "Panoramic Sunroof Glass", rarity: "Rare", priceRange: [150, 350], yardCost: 44, sellOn: "eBay" },
      { name: "Bose/Infinity Amp + Speakers", rarity: "Uncommon", priceRange: [75, 175], yardCost: 44, sellOn: "eBay" },
      { name: "Smart Cruise Radar Module", rarity: "Uncommon", priceRange: [75, 175], yardCost: 22, sellOn: "eBay" },
      { name: "Wireless Charging Pad Module", rarity: "Uncommon", priceRange: [40, 100], yardCost: 29, sellOn: "eBay" },
    ]
  },
  {
    name: "Chevy K5 Blazer (Full Size)",
    make: "Chevrolet",
    years: "1973–1991",
    category: "SUV",
    frequency: "Occasional",
    notes: "These are collector trucks now. The removable top alone can pay for your yard admission 20x over. All trim and body parts have big value.",
    parts: [
      { name: "Removable Fiberglass Top (clean)", rarity: "Legendary", priceRange: [1500, 4000], yardCost: 150, sellOn: "K5Blazer.com, eBay" },
      { name: "Clean Dash Pad (uncracked)", rarity: "Epic", priceRange: [100, 300], yardCost: 10, sellOn: "eBay, K5Blazer.com" },
      { name: "Tailgate (clean, w/ glass)", rarity: "Rare", priceRange: [100, 275], yardCost: 20, sellOn: "eBay" },
      { name: "Bucket Seats (pair, clean)", rarity: "Rare", priceRange: [150, 350], yardCost: 25, sellOn: "eBay, Forums" },
      { name: "Side Moldings / Trim (set)", rarity: "Uncommon", priceRange: [50, 150], yardCost: 8, sellOn: "eBay" },
      { name: "OEM Fender Emblems", rarity: "Uncommon", priceRange: [25, 75], yardCost: 2, sellOn: "eBay" },
    ]
  },
  {
    name: "VW Golf / GTI / R (Mk5–Mk8)",
    make: "Volkswagen",
    years: "2006–2024",
    category: "Hatchback",
    frequency: "Occasional",
    notes: "GTI/R parts have a devoted mod community. Brakes, seats, and lighting upgrades from R models swap onto base GTIs.",
    parts: [
      { name: "Golf R Brake Calipers (set)", rarity: "Epic", priceRange: [200, 450], yardCost: 30, sellOn: "VWVortex, eBay" },
      { name: "Leather/Plaid Seats (GTI, pair)", rarity: "Rare", priceRange: [200, 450], yardCost: 35, sellOn: "VWVortex, eBay" },
      { name: "OEM LED Headlights (pair)", rarity: "Rare", priceRange: [250, 500], yardCost: 40, sellOn: "eBay" },
      { name: "Digital Cockpit Cluster (Mk8)", rarity: "Epic", priceRange: [200, 400], yardCost: 25, sellOn: "eBay" },
      { name: "GTI/R Steering Wheel (flat bottom)", rarity: "Rare", priceRange: [100, 250], yardCost: 15, sellOn: "VWVortex, eBay" },
      { name: "Fender Audio System", rarity: "Uncommon", priceRange: [75, 175], yardCost: 12, sellOn: "eBay" },
    ]
  },
  {
    name: "BMW 3-Series (E90/F30/G20)",
    make: "BMW",
    years: "2006–2024",
    category: "Sedan",
    frequency: "Common",
    notes: "BMWs end up in yards when repair costs exceed value. M-Sport bumpers, iDrive screens, and adaptive headlights are all premium parts.",
    parts: [
      { name: "M-Sport Front Bumper (complete)", rarity: "Epic", priceRange: [200, 500], yardCost: 30, sellOn: "eBay, Bimmerpost" },
      { name: "Adaptive LED Headlights (pair)", rarity: "Epic", priceRange: [300, 700], yardCost: 50, sellOn: "eBay" },
      { name: "iDrive Controller + Screen", rarity: "Rare", priceRange: [150, 350], yardCost: 20, sellOn: "eBay" },
      { name: "M-Sport Steering Wheel", rarity: "Rare", priceRange: [100, 275], yardCost: 15, sellOn: "eBay, Bimmerpost" },
      { name: "Sport Seats (pair)", rarity: "Rare", priceRange: [200, 450], yardCost: 35, sellOn: "eBay" },
      { name: "M-Sport Side Skirts (pair)", rarity: "Uncommon", priceRange: [75, 175], yardCost: 12, sellOn: "eBay" },
    ]
  },
  {
    name: "Audi A4 / Q5 / MMI era (B8+)",
    make: "Audi",
    years: "2009–2024",
    category: "Sedan / SUV",
    frequency: "Occasional",
    notes: "Strong eBay market for MMI screens, Virtual Cockpit, matrix LEDs, and B&O amps. Quattro/Haldex modules move when priced right.",
    parts: [
      { name: "Matrix / LED Headlights (pair)", rarity: "Epic", priceRange: [400, 1000], yardCost: 55, sellOn: "eBay, Audi forums" },
      { name: "MMI / Virtual Cockpit Assembly", rarity: "Epic", priceRange: [250, 700], yardCost: 42, sellOn: "eBay" },
      { name: "Bang & Olufsen Amp + Speakers", rarity: "Rare", priceRange: [200, 550], yardCost: 38, sellOn: "eBay" },
      { name: "Panoramic Roof Motor (Q5)", rarity: "Rare", priceRange: [180, 450], yardCost: 32, sellOn: "eBay" },
      { name: "Air Suspension Compressor (A6/A7/Q7)", rarity: "Legendary", priceRange: [350, 950], yardCost: 42, sellOn: "eBay" },
    ]
  },
  {
    name: "Lexus GX 470/460",
    make: "Lexus",
    years: "2003–2024",
    category: "SUV",
    frequency: "Occasional",
    notes: "GXs are the overlanding darlings. They share the Land Cruiser Prado platform. KDSS parts, AHC components, and OEM bumper bits are all hot.",
    parts: [
      { name: "KDSS Hydraulic Actuators", rarity: "Legendary", priceRange: [300, 700], yardCost: 30, sellOn: "IH8MUD, GXOR, eBay" },
      { name: "AHC Height Control Pump", rarity: "Epic", priceRange: [200, 500], yardCost: 25, sellOn: "GXOR, eBay" },
      { name: "OEM Roof Rack + Crossbars", rarity: "Rare", priceRange: [150, 350], yardCost: 25, sellOn: "eBay, GXOR" },
      { name: "Mark Levinson Amp/Speakers", rarity: "Rare", priceRange: [150, 350], yardCost: 25, sellOn: "eBay" },
      { name: "Rear Air Suspension Bags", rarity: "Rare", priceRange: [100, 250], yardCost: 15, sellOn: "eBay" },
      { name: "Center Diff Lock Switch/Actuator", rarity: "Epic", priceRange: [100, 250], yardCost: 10, sellOn: "GXOR" },
      { name: "OEM Running Boards", rarity: "Uncommon", priceRange: [75, 175], yardCost: 15, sellOn: "eBay" },
    ]
  },
  {
    name: "Lexus LX 470/570",
    make: "Lexus",
    years: "1998–2021",
    category: "SUV",
    frequency: "Rare",
    notes: "Luxury Land Cruiser. Extremely rare in yards. AHC parts, Mark Levinson audio, and interior bits are premium. Cross-references with 100/200 series Cruiser.",
    parts: [
      { name: "AHC Height Control Pump + Sensors", rarity: "Legendary", priceRange: [400, 900], yardCost: 40, sellOn: "IH8MUD, eBay" },
      { name: "Mark Levinson Full Audio System", rarity: "Epic", priceRange: [300, 700], yardCost: 40, sellOn: "eBay" },
      { name: "Night Vision Camera Module", rarity: "Legendary", priceRange: [200, 500], yardCost: 20, sellOn: "eBay" },
      { name: "OEM Roof Rack", rarity: "Rare", priceRange: [200, 450], yardCost: 30, sellOn: "eBay" },
      { name: "Heated/Cooled Seat Module", rarity: "Rare", priceRange: [100, 250], yardCost: 15, sellOn: "eBay" },
      { name: "Center Diff Lock Actuator", rarity: "Epic", priceRange: [100, 275], yardCost: 10, sellOn: "IH8MUD" },
    ]
  },
];


/* ===== Utility functions ===== */
function maxPartValue(car) { return Math.max(...car.parts.map(p => p.priceRange[1])); }
function totalPotentialValue(car) { return car.parts.reduce((sum, p) => sum + p.priceRange[1], 0); }
function avgROI(car) {
  const rois = car.parts.map(p => ((p.priceRange[0] + p.priceRange[1]) / 2) / p.yardCost);
  return rois.reduce((a, b) => a + b, 0) / rois.length;
}
function rarityRank(r) { return { Legendary: 4, Epic: 3, Rare: 2, Uncommon: 1 }[r] || 0; }
function categoryClass(cat) { return 'cat-' + cat.toLowerCase(); }
function rarityClass(r) { return 'rarity-' + r.toLowerCase(); }
function formatPrice(n) { return '$' + n.toLocaleString(); }
function isNew(dateStr) {
  if (!dateStr) return false;
  const d = new Date(dateStr);
  const now = new Date();
  return (now - d) / 86400000 <= 7;
}

function daysSinceAdded(dateStr) {
  if (!dateStr) return 999;
  return Math.max(0, (new Date() - new Date(dateStr)) / 86400000);
}

function freshnessMultiplier(dateStr) {
  const days = daysSinceAdded(dateStr);
  if (days <= 3) return 1.0;
  if (days <= 7) return 0.90;
  if (days <= 14) return 0.75;
  if (days <= 30) return 0.55;
  return 0.35;
}

function freshnessLabel(dateStr) {
  const days = daysSinceAdded(dateStr);
  if (days <= 3) return { text: 'Fresh', color: 'var(--accent2)' };
  if (days <= 7) return { text: 'Recent', color: 'var(--accent)' };
  if (days <= 14) return { text: '1-2 wks', color: 'var(--orange)' };
  if (days <= 30) return { text: '2-4 wks', color: 'var(--text-dim)' };
  return { text: '30+ days', color: 'var(--red)' };
}

