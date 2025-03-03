# Color Transfer & Dynamic Color Picker Web App

This is a one-page Flask web app that performs image color transfer (processing happens entirely in memory) and includes a dynamic color picker module. The color picker section uses a canvas-based magnifier effect that shows a zoomed-in area of the image and updates the color code dynamically as you hover over it. A placeholder ad section is also included for future ads.

## Features

- **Color Transfer:**  
  Upload a sample (reference) image and a user image, then click "Match Colors" to transfer the reference’s tone to the user image.

- **Dynamic Color Picker:**  
  Upload an image, then hover over it to see a magnified view and dynamically updated color code (HEX and RGB).

- **Ad Placeholder:**  
  A designated area for future advertisements.

## How to Run

1. **Install dependencies:**

   ```bash
   pip install -r requirements.txt