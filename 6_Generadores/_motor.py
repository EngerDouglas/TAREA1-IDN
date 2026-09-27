# =====================================================================================
# RENDERIZADO
# =====================================================================================
CSS = """
@page { size: Letter; margin: 20mm 18mm 16mm 18mm;
        @bottom-center { content: counter(page); font: 9pt Arial, sans-serif; color: #7a8394; } }
@page :first { @bottom-center { content: none; } }
* { box-sizing: border-box; }
body { font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 10.5pt; line-height: 1.55; color: #1c2430; margin: 0; }

.portada { height: 240mm; display: flex; flex-direction: column; text-align: center; break-after: page; }
.portada .univ { font-family: Georgia, serif; font-size: 13pt; margin-top: 18mm; line-height: 1.6; }
.portada .escuela, .portada .asignatura { font-size: 11pt; color: #44506a; }
.portada .bloque { margin-top: 42mm; }
.portada h1 { font-family: Georgia, serif; font-size: 25pt; line-height: 1.25; margin: 0 auto 10px; max-width: 150mm; color: #14243d; }
.portada .entrega { font-size: 14pt; color: #1f4e79; margin-bottom: 6px; }
.portada .linea { width: 70px; height: 3px; background: #1f4e79; margin: 16px auto 0; }
.portada .datos { margin-top: auto; margin-bottom: 14mm; font-size: 11.5pt; line-height: 2; }
.portada .datos b { color: #14243d; }

h2 { font-family: Georgia, serif; font-size: 15pt; color: #14243d; margin: 22px 0 8px; break-after: avoid;
     border-bottom: 1.5px solid #1f4e79; padding-bottom: 5px; }
h3 { font-size: 11.5pt; color: #1f4e79; margin: 16px 0 6px; break-after: avoid; }
p { margin: 0 0 9px; text-align: justify; }
ul { margin: 0 0 10px; padding-left: 20px; }
li { margin-bottom: 4px; text-align: justify; }

table { width: 100%; border-collapse: collapse; margin: 8px 0 14px; font-size: 9.2pt; break-inside: avoid; }
th { background: #14243d; color: #fff; text-align: left; padding: 6px 8px; font-weight: 600; }
td { border: 1px solid #ccd3de; padding: 5px 8px; vertical-align: top; }
tr:nth-child(even) td { background: #f5f7fa; }

.nota { background: #fff8e6; border-left: 4px solid #d99a00; padding: 10px 14px; margin: 6px 0 14px;
        font-size: 9.8pt; break-inside: avoid; }
.diagrama { width: 88%; display: block; height: auto; margin: 6px auto 14px; break-inside: avoid; }
.diagrama .cat { fill: #eef2f8; stroke: #7d8ca5; stroke-width: 1.5; }
.diagrama .tx { fill: #14243d; stroke: #14243d; }
.diagrama .tx2 { fill: #1f4e79; stroke: #1f4e79; }
"""


def esc(t):
    return html.escape(t)


def fmt(t):
    t = esc(t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"`(.+?)`", r"<code>\1</code>", t)
    return t


def render_html():
    o = ["<!doctype html><html lang='es'><head><meta charset='utf-8'><title>",
         esc("Práctica 1 — Actividad 1"), "</title><style>", CSS, "</style></head><body>"]
    o.append(
        "<div class='portada'><div class='univ'>%s<div class='escuela'>%s</div>"
        "<div class='asignatura'>%s</div></div>"
        "<div class='bloque'><div class='entrega'>%s</div><h1>%s</h1><div class='linea'></div></div>"
        "<div class='datos'><div><b>Estudiante:</b> %s</div><div><b>ID:</b> %s</div>"
        "<div><b>Profesora:</b> %s</div><div><b>Fecha:</b> %s</div></div></div>"
        % (esc(UNIVERSIDAD), esc(ESCUELA), esc(ASIGNATURA), esc(ENTREGA), esc(PRACTICA),
           esc(ESTUDIANTE), esc(MATRICULA), esc(PROFESORA), esc(FECHA)))

    for b in BLOQUES:
        k = b[0]
        if k == "h2":
            o.append("<h2>%s</h2>" % esc(b[1]))
        elif k == "h3":
            o.append("<h3>%s</h3>" % esc(b[1]))
        elif k == "p":
            o.append("<p>%s</p>" % fmt(b[1]))
        elif k == "li":
            o.append("<ul>%s</ul>" % "".join("<li>%s</li>" % fmt(i) for i in b[1]))
        elif k == "nota":
            o.append("<div class='nota'>%s</div>" % fmt(b[1]))
        elif k == "svg":
            o.append(b[1])
        elif k == "salto":
            o.append("<div style='break-after:page'></div>")
        elif k == "tabla":
            _, hd, filas, anchos, aligns = b
            cols = "".join("<col style='width:%s%%'>" % w for w in anchos)
            th = "".join("<th%s>%s</th>" % (" style='text-align:%s'" % a if a else "", esc(h)) for h, a in zip(hd, aligns))
            trs = "".join("<tr>%s</tr>" % "".join(
                "<td%s>%s</td>" % (" style='text-align:%s'" % a if a else "", fmt(c)) for c, a in zip(f, aligns))
                for f in filas)
            o.append("<table><colgroup>%s</colgroup><tr>%s</tr>%s</table>" % (cols, th, trs))

    o.append("</body></html>")
    return "".join(o)


if __name__ == "__main__":
    pdf = os.path.join(TAREA, "3_Informes", "Practica1_Actividad2y3_Modelo.pdf")
    with tempfile.TemporaryDirectory() as tmp:
        h = os.path.join(tmp, "doc.html")
        with open(h, "w", encoding="utf-8") as f:
            f.write(render_html())
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                        "--allow-file-access-from-files", "--print-to-pdf=" + pdf, "file://" + h],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("PDF:", pdf)
