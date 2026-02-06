# Hospital Branding Guide - Surya City Hospital

## Current Configuration

**Hospital Name:** Surya City Hospital  
**Logo Location:** `static/images/hospital_logo.png` (or `.svg`)

## 🎯 Quick Start: Add Your Surya Hospital Logo

### Simple 3-Step Process

1. **Save the logo image** you shared to your computer
2. **Rename it** to `hospital_logo.png`
3. **Copy it** to the `static/images/` folder in your project
4. **Refresh** your browser - Done! ✅

The system will automatically display your logo in the header.

## How to Add Your Custom Hospital Logo

### Option 1: PNG Format (Recommended for Photos/Complex Logos)
1. Save your hospital logo as `hospital_logo.png`
2. Place it in the `static/images/` folder
3. Recommended size: 200x200 pixels minimum (for sharp display)
4. The logo will automatically appear in the header

### Option 2: SVG Format (Best for Vector Logos)
1. Save your logo as `hospital_logo.svg`
2. Place it in the `static/images/` folder
3. SVG scales perfectly at any size
4. The system tries PNG first, then falls back to SVG

### Logo Priority
The system tries to load logos in this order:
1. `hospital_logo.png` (tried first)
2. `hospital_logo.svg` (fallback if PNG not found)
3. If neither exists, only text name is shown

## Your Surya Hospital Logo

The Surya Hospital logo you provided features:
- **Stylized sun** with orange/yellow rays (representing "Surya" - Sun in Sanskrit)
- **Blue curved line** representing care and protection
- **"SURYA" text** in navy blue (#2C3E50)
- **"HOSPITAL" text** in orange (#FF8C42)
- Professional, warm, and welcoming design
- Perfect for a healthcare institution

### To Use Your Logo:
1. Save the Surya Hospital logo image from chat
2. Rename to: `hospital_logo.png`
3. Copy to: `static/images/hospital_logo.png`
4. Refresh browser (Ctrl+R or Cmd+R)
5. Your logo appears! ✨

## Logo Specifications

### For Best Results:
- **Format:** PNG (preferred) or SVG
- **Size:** 200x200 pixels minimum, 400x400 pixels recommended
- **Display Height:** 50px (width auto-scales)
- **Background:** Transparent or white
- **Aspect Ratio:** Square or horizontal rectangle works best
- **File Size:** Keep under 500KB for fast loading

### Logo Placement:
- Header (top-left): 50px height, auto width
- Print slips: Scales automatically
- Reports: Scales automatically

## Updating Hospital Information

### Update Hospital Name
Edit `.env` file:
```env
HOSPITAL_NAME=Surya City Hospital
```

### Update Hospital Address
Edit `.env` file:
```env
HOSPITAL_ADDRESS=Your Complete Address Here
```

After editing `.env`, restart the server:
```bash
# Stop the server (Ctrl+C)
# Start again
python run.py
```

## Testing Your Logo

After adding your logo:
1. Make sure file is at: `static/images/hospital_logo.png`
2. Refresh browser (Ctrl+R or Cmd+R)
3. Check if logo appears in the header
4. If logo doesn't appear, check browser console (F12) for errors

## Troubleshooting

### Logo Not Showing?
1. ✅ Check file exists: `static/images/hospital_logo.png`
2. ✅ Check file name is exactly: `hospital_logo.png` (lowercase, no spaces)
3. ✅ Check file permissions (should be readable)
4. ✅ Clear browser cache (Ctrl+Shift+R or Cmd+Shift+R)
5. ✅ Check browser console (F12) for 404 errors
6. ✅ Try renaming to `hospital_logo.svg` if it's an SVG file

### Logo Too Large/Small?
Edit `static/css/style.css` around line 52:
```css
.hospital-logo-img {
    height: 50px;  /* Change this value (try 60px or 70px) */
    width: auto;
    object-fit: contain;
}
```

### Logo Appears Blurry?
- Use a higher resolution PNG (at least 200x200 pixels)
- Or use SVG format for perfect scaling at any size
- Ensure you're using 2x resolution for retina displays (400x400 for 200px display)

### Logo Has Wrong Colors?
- Make sure you saved the correct image file
- Check if the image has transparency (PNG supports transparency)
- Try opening the image in an image viewer to verify it looks correct

## Brand Colors

Current Surya Hospital theme uses:
- **Primary Blue:** #1E88E5 (Medical Blue)
- **Secondary Green:** #2E7D32 (Calm Green)
- **Background:** #F5F7FA (Light Grey)
- **Orange Accent:** #FF8C42 (Warm Orange - matches your logo)

To update brand colors, edit `static/css/style.css`:
```css
:root {
    --primary-color: #1E88E5;
    --secondary-color: #2E7D32;
    --background-color: #F5F7FA;
}
```

## Files Involved

- **Logo image:** `static/images/hospital_logo.png` (or `.svg`)
- **Template:** `templates/base.html` (logo display code)
- **Styling:** `static/css/style.css` (logo sizing)
- **Configuration:** `.env` (HOSPITAL_NAME, HOSPITAL_ADDRESS)
- **Backend config:** `app/core/config.py`

## Step-by-Step Visual Guide

```
Your Computer                    Project Folder
┌─────────────┐                 ┌──────────────────┐
│ Downloads/  │                 │ static/          │
│  surya.png  │  ──────────>   │   images/        │
│             │     Copy        │     hospital_    │
│             │                 │     logo.png     │
└─────────────┘                 └──────────────────┘
                                         │
                                         ▼
                                  Browser Refresh
                                         │
                                         ▼
                                   Logo Appears! ✨
```

## Need Help?

If you need assistance with:
- ✅ Logo not appearing after following steps
- ✅ Logo size adjustments
- ✅ Logo quality issues
- ✅ Customizing the header layout
- ✅ Changing hospital colors

Check the troubleshooting section above or contact your system administrator.

## Quick Reference

| Task | File Location | Action |
|------|--------------|--------|
| Add logo | `static/images/hospital_logo.png` | Copy your logo file here |
| Change hospital name | `.env` | Edit `HOSPITAL_NAME=...` |
| Change address | `.env` | Edit `HOSPITAL_ADDRESS=...` |
| Adjust logo size | `static/css/style.css` | Edit `.hospital-logo-img { height: 50px; }` |
| View logo in browser | `http://localhost:8000` | Refresh after adding logo |

---

**Remember:** The system automatically tries PNG first, then SVG. Just copy your logo file and refresh! 🚀
