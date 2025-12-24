# SULFUR Weapon Calculator

A web-based calculator for the game SULFUR that helps you calculate weapon statistics when oils and scrolls are applied.

## Features

- **Complete Weapon Database**: 46 weapons with full stats
- **Complete Enchantment Database**: 192 oils and 35 scrolls
- **Multiple Enchantment Support**: Apply up to 5 oils OR 4 oils + 1 scroll
- **Visual Display**: Weapon and enchantment images loaded from SULFUR wiki
- **Saved Builds**: Save and load your favorite weapon configurations
- **Total Damage Calculation**: See combined damage × projectile count
- **Special Scroll Mechanics**: Proper handling of ConvertWpn scrolls (Scroll of Light, etc.) where scroll modifiers apply before oil modifiers

## Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd sulfur-calculator-github
```

2. Install dependencies:
```bash
npm install
```

3. Run the development server:
```bash
npm run dev
```

4. Open your browser to the URL shown (typically http://localhost:5173)

## Building for Production

```bash
npm run build
```

The built files will be in the `dist` directory.

## How to Use

1. **Select a Weapon** from the dropdown
2. **Add Oils** (up to 5) or **Add a Scroll** (max 1)
3. View **Base Stats** and **Modified Stats** side-by-side
4. **Save Your Build** with a custom name for later use
5. Click any **Saved Build** to load it instantly

## Game Mechanics

### Oil & Scroll Limits
- Maximum 5 oils OR 4 oils + 1 scroll
- Cannot have more than 1 scroll at a time

### Modifier Types
- **Flat (Type 100)**: Direct addition/subtraction
- **PercentAdd (Type 200)**: Percentage-based modification
- **PercentMult (Type 300)**: Multiplicative percentage

### Special ConvertWpn Scrolls
Scrolls with the `ConvertWpn` property (Scroll of Light, Thunderbolt, Holy Fire, Toxic Lobotomy, etc.) have their modifiers applied BEFORE oil modifiers. This means oil percentage modifiers are calculated from the scroll-modified value.

**Example:**
- Base RPM: 80
- Scroll of Light (-50%): 80 × 0.5 = 40
- Attack Speed Oil (+25%): 40 + (40 × 0.25) = **50**

## Data Source

All weapon, oil, and scroll data is extracted from the official [SULFUR Wiki](https://sulfur.wiki.gg).

## Tech Stack

- **React 18** - UI framework
- **Vite 5** - Build tool and dev server
- **Tailwind CSS 3** - Styling
- **LocalStorage API** - Saved build persistence

## License

This is a fan-made tool for the game SULFUR. All game data and images are property of their respective owners.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
