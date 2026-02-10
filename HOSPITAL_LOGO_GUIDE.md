# Hospital Logo Setup Guide

## ✅ Changes Applied

1. **Hospital Name Updated:** "Tiwari Hospital" → **"Surya Hospital"**
2. **Hospital Address:** Tamkuhi Raj, Kushinagar, Uttar Pradesh - 274407
3. **Phone Number:** +91-9580845238
4. **Logo Support Added:** Print slip now includes hospital logo

## How to Add Your Hospital Logo

### Option 1: Upload Logo via GitHub (Recommended for Render)

1. **Prepare your logo:**
   - Format: PNG or JPG
   - Recommended size: 200x200 pixels or similar
   - Name it: `hospital_logo.png`

2. **Upload to GitHub:**
   ```bash
   # Place your logo in the static/images folder
   cp /path/to/your/logo.png static/images/hospital_logo.png
   
   # Commit and push
   git add static/images/hospital_logo.png
   git commit -m "Add hospital logo"
   git push origin main
   ```

3. **Render will automatically deploy** with the new logo

### Option 2: Upload Logo via Render Dashboard

1. Go to Render dashboard
2. Select your service
3. Go to "Shell" tab
4. Upload logo file to `/app/static/images/hospital_logo.png`

**Note:** This method is temporary - logo will be lost on next deployment

### Logo Specifications

**Recommended:**
- **Format:** PNG (with transparent background) or JPG
- **Size:** 200x200 pixels (square) or 300x100 pixels (rectangular)
- **File size:** Under 500KB
- **Colors:** Should work well in print (avoid very light colors)

**Current Logo Path:**
- Location: `static/images/hospital_logo.png`
- If logo doesn't exist, it will be hidden automatically (no broken image)

## What the Print Slip Shows Now

```
┌─────────────────────────────────────────────┐
│  SURYA HOSPITAL              [LOGO]         │
│  Tamkuhi Raj, Kushinagar, UP - 274407      │
│  Phone: +91-9580845238                      │
├─────────────────────────────────────────────┤
│  Dr. [Doctor Name]                          │
│  [Department]                               │
├─────────────────────────────────────────────┤
│  Patient Name: ............  Age/Sex: ...   │
│  Address: .......................            │
│  Mobile No: .........  Date: .........      │
│  Patient ID: .......  Visit ID: .......     │
└─────────────────────────────────────────────┘
```

## Testing After Deployment

1. **Wait for deployment** (2-3 minutes)
2. **Register a test patient**
3. **Click "Print Slip"**
4. **Verify:**
   - ✅ Hospital name shows "SURYA HOSPITAL"
   - ✅ Correct address and phone
   - ✅ Logo appears (if uploaded)
   - ✅ All patient details visible

## Troubleshooting

### Logo Not Showing?

**Check 1:** Is the logo file uploaded?
```bash
# Check if file exists
ls -la static/images/hospital_logo.png
```

**Check 2:** Is the file name correct?
- Must be exactly: `hospital_logo.png`
- Case-sensitive on Linux/Render

**Check 3:** Is the file format supported?
- Use PNG or JPG only
- Avoid WEBP, SVG, or other formats

### Logo Too Big/Small?

Edit the logo size in `app/api/v1/endpoints/slips.py`:
```python
<img src="/static/images/hospital_logo.png" 
     style="max-width: 100px; max-height: 80px;">
```

Change `max-width` and `max-height` values as needed.

## Next Steps

1. **Prepare your logo** (PNG, 200x200px recommended)
2. **Upload to GitHub** (recommended) or Render
3. **Test the print slip** after deployment
4. **Adjust logo size** if needed

## Need Help?

If you need help with:
- Logo not showing
- Logo size adjustment
- Different logo format
- Custom slip design

Just let me know and I'll help you fix it!
