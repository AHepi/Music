# Fonts - where to get them

The lettering on the checkout's own things (the newspaper bill, the grocery labels, the CHECKOUT sign and the
petrol station's fascia) is drawn by `paint_checkout_pictures.py` with these free fonts. Anton and Oswald are not
kept in this repository because they are other people's work; their licence texts are here. Inter and Liberation
Serif come with the computer (the Debian packages fonts-inter and fonts-liberation).

Put the .ttf files in a folder and give it to `paint_checkout_pictures.py --fonts FOLDER` (build_checkout.sh fetches
them into its scratch folder):

| File | Font | Where | Licence | Used for |
|---|---|---|---|---|
| Anton-Regular.ttf | Anton | Google Fonts (fonts.google.com/specimen/Anton; raw.githubusercontent.com/google/fonts/main/ofl/anton/) | SIL Open Font Licence | the bill's big words |
| Oswald[wght].ttf | Oswald | Google Fonts (fonts.google.com/specimen/Oswald; raw.githubusercontent.com/google/fonts/main/ofl/oswald/) | SIL Open Font Licence | the grocery labels |
| InterDisplay-Black.otf, Inter-Bold.otf | Inter | /usr/share/fonts/opentype/inter | SIL Open Font Licence | CHECKOUT, PETROL · DIESEL |
| LiberationSerif-Bold.ttf | Liberation Serif | /usr/share/fonts/truetype/liberation | SIL Open Font Licence | the newspaper's name, BREAD |

The finished pictures (`assets/models/inflation-chapter-2-newcomers/checkout/textures/*`) already carry the
lettering, so the fonts are only needed to change the wording.
