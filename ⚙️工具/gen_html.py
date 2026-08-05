import base64, os, sys

charts_dir = "I:\\阿飞说球\\20260726\\charts"
encodings = {}
for f in ["radar.svg", "bar_comparison.svg", "pie_anyang.svg", "pie_gwangju.svg"]:
    with open(os.path.join(charts_dir, f), "rb") as fh:
        encodings[f.replace(".svg","")] = base64.b64encode(fh.read()).decode("utf-8")

radar_b64 = encodings["radar"]
bar_b64 = encodings["bar_comparison"]
pie_a_b64 = encodings["pie_anyang"]
pie_g_b64 = encodings["pie_gwangju"]

# Read from template
with open(os.path.join(charts_dir, "_template.html"), "r", encoding="utf-8") as f:
    tmpl = f.read()

html = tmpl.replace("__RADAR_B64__", radar_b64)
html = html.replace("__BAR_B64__", bar_b64)
html = html.replace("__PIE_A_B64__", pie_a_b64)
html = html.replace("__PIE_G_B64__", pie_g_b64)

with open("I:\\阿飞说球\\20260726\\韩K联第20轮_头条版.html", "w", encoding="utf-8") as f:
    f.write(html)

print(f"HTML generated: {len(html)} chars")
