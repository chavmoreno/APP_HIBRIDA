"""Genera docs/diagramas/Arquitectura.drawio (diagrama de arquitectura para draw.io / diagrams.net).

Uso:
    python docs/diagramas/generar_arquitectura_drawio.py

Mantiene el estilo del diagrama original (fuente Recursive, sombras, colores) y refleja la arquitectura
actual: contenedores en una VM de Oracle Cloud Always Free (Caddy + DuckDNS), MySQL de XAMPP en el PC de casa (túnel SSH inverso) y
flujo Kaggle → Colab.
"""

import pathlib
from xml.sax.saxutils import quoteattr

SALIDA = pathlib.Path(__file__).with_name("Arquitectura.drawio")

# ---- Estilos (copiados del diagrama original) ----
FUENTE = "fontFamily=Recursive;fontSource=https%3A%2F%2Ffonts.googleapis.com%2Fcss%3Ffamily%3DRecursive;"
SOMBRA = "shadow=1;shadowColor=#000000;shadowOffsetX=4;shadowOffsetY=4;shadowBlur=0;shadowOpacity=6;"
NODO = "html=1;whiteSpace=wrap;strokeWidth=2;fillColor=#ffffff;strokeColor=#28253D;fontColor=#28253D;fontSize=14;" + FUENTE + SOMBRA
BD = "shape=cylinder3;boundedLbl=1;backgroundOutline=1;size=10;" + NODO
CONTENEDOR = "html=1;whiteSpace=wrap;strokeWidth=1;verticalAlign=top;align=left;spacingLeft=10;spacingTop=4;fontColor=#000000;fontSize=14;" + FUENTE + SOMBRA
LOCAL = CONTENEDOR + "fillColor=#FDF4FF;strokeColor=#E879F9;"
XAMPP = CONTENEDOR + "fillColor=#F0FDFA;strokeColor=#2DD4BF;" + "verticalAlign=bottom;spacingBottom=4;"  # Rótulo abajo: las flechas entran por arriba
DOCKER = CONTENEDOR + "fillColor=#EFF6FF;strokeColor=#3B82F6;strokeWidth=2;"
NUBE = CONTENEDOR + "fillColor=#FFFBEB;strokeColor=#F59E0B;"
OCI = CONTENEDOR + "fillColor=#FFF7ED;strokeColor=#FB923C;"
FLECHA = (
    "edgeStyle=orthogonalEdgeStyle;rounded=1;curved=0;html=1;startArrow=none;endArrow=block;endSize=8;"
    "jumpStyle=arc;jumpSize=12;strokeColor=#000000;strokeWidth=2;fontSize=13;labelBackgroundColor=#cccccc;"
    "fontColor=#28253D;" + FUENTE
)
DISCONTINUA = FLECHA + "dashed=1;dashPattern=2 2;fixDash=1;"
NOTA = "text;html=1;fillColor=none;strokeColor=none;align=left;verticalAlign=top;whiteSpace=wrap;fontSize=12;fontColor=#28253D;" + FUENTE

celdas: list[str] = []


def caja(id_: str, texto: str, x: int, y: int, w: int, h: int, estilo: str = NODO) -> None:
    """Agrega un vértice con posición absoluta."""
    celdas.append(
        f'<mxCell id="{id_}" value={quoteattr(texto)} style={quoteattr(estilo)} vertex="1" parent="1">'
        f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>'
    )


def flecha(id_: str, origen: str, destino: str, texto: str = "", estilo: str = FLECHA,
           puntos: list[tuple[int, int]] | None = None, extra: str = "", pos: float = 0) -> None:
    """Agrega una arista; 'extra' fija exitX/entryX, etc.; 'puntos' son quiebres; 'pos' (-1..1) mueve el rótulo."""
    pts = ""
    if puntos:
        pts = '<Array as="points">' + "".join(f'<mxPoint x="{x}" y="{y}"/>' for x, y in puntos) + "</Array>"
    celdas.append(
        f'<mxCell id="{id_}" value={quoteattr(texto)} style={quoteattr(estilo + extra)} edge="1" parent="1" '
        f'source="{origen}" target="{destino}"><mxGeometry x="{pos}" relative="1" as="geometry">{pts}</mxGeometry></mxCell>'
    )


# ---------------- Contenedores (se dibujan primero para quedar al fondo) ----------------
caja("nube", "<b>Nube</b> (Google / DuckDNS)", 20, 0, 960, 360, NUBE)
caja("vm", "<b>Oracle Cloud Always Free</b> · VM Ampere A1 (Ubuntu 24.04, ARM) · públicos: 22, 80, 443", 20, 390, 960, 450, OCI)
caja("docker", "<b>Docker</b> · network_mode host · servicios internos sólo en 127.0.0.1<br>"
     "<font style='font-size:12px'>usuario sin privilegios · sólo lectura · restart: unless-stopped</font>",
     40, 485, 920, 245, DOCKER)
caja("local", "<b>PC de casa</b> (Windows) · lo único local", 20, 870, 960, 330, LOCAL)
caja("xampp", "<b>XAMPP</b> · MySQL (MariaDB), sólo 127.0.0.1:3306", 60, 990, 460, 190, XAMPP)

# ---------------- Nube ----------------
caja("U", "Usuario (navegador)", 360, 40, 180, 45)
caja("FE", "<b>Frontend SPA</b> - Firebase Hosting<br>Nueva consulta / Histórico<br>Páginas 404 · 401 · 500 · ErrorBoundary",
     320, 120, 260, 100)
caja("FA", "<b>Firebase Authentication</b><br>correo/contraseña o Google", 40, 255, 220, 70)
caja("KG", "<b>Kaggle</b><br>stroke-prediction-dataset", 720, 30, 220, 55)
caja("CO", "<b>Google Colab</b><br>EDA + preprocesamiento<br>+ entrenamiento", 720, 125, 220, 80)
caja("CF", "<b>DuckDNS</b><br>tu-app.duckdns.org", 360, 270, 180, 60)

# ---------------- VM de Oracle Cloud ----------------
caja("CFD", "<b>Caddy</b> :443 · Let's Encrypt", 360, 415, 180, 45)
caja("MW", "Middleware X-Request-ID<br>+ manejadores de excepciones", 60, 530, 220, 60)
caja("API", "<b>API Gateway</b> FastAPI :8000<br>(HTTPS)", 340, 530, 220, 60)
caja("MS", "<b>Microservicio inferencia</b> :8001<br>HTTPS · healthcheck", 640, 530, 280, 65)
caja("FB", "Respaldo: archivo .log rotativo<br>si MySQL no responde", 60, 640, 220, 60)
caja("MR", "<b>Model registry</b><br>models/model_v1.joblib<br>(volumen de sólo lectura)", 340, 640, 280, 70)
caja("AL", "<b>Worker de alertas</b><br>CRITICAL pendientes", 640, 640, 280, 60)
caja("T", "<b>127.0.0.1:3306</b><br>extremo del túnel (sshd, usuario <i>tunel</i>)", 300, 760, 220, 60)
caja("ADM", "<b>Telegram / correo</b><br>(servicios externos)", 640, 760, 280, 60)

# ---------------- PC de casa ----------------
caja("SSH", "<b>ssh -R</b> (tunel_mysql.bat)<br>ssh incluido en Windows", 300, 900, 220, 60)
caja("DB2", "<b>consultas_db</b><br>consultas y resultados", 90, 1035, 170, 120, BD)
caja("DB4", "<b>errores_db</b><br>log de errores", 320, 1035, 170, 120, BD)

# ---------------- Fuera ----------------
caja("leyenda", "<b>Leyenda</b><br>── flujo principal<br>- - - errores / respaldo / subida manual del modelo",
     560, 1220, 400, 70, NOTA)

# ---------------- Flechas ----------------
flecha("e1", "U", "FE", "HTTPS")
flecha("e2", "FE", "FA", "Login correo o Google", puntos=[(150, 170)],
       extra="exitX=0;exitY=0.5;entryX=0.5;entryY=0;")
flecha("e3", "FE", "CF", "HTTPS + Bearer token", extra="exitX=0.4;exitY=1;entryX=0.37;entryY=0;")
flecha("e4", "FE", "CF", "POST /api/errores<br>errores de JS", DISCONTINUA,
       puntos=[(620, 200), (620, 300)], extra="exitX=1;exitY=0.8;entryX=1;entryY=0.5;")
flecha("e5", "KG", "CO", "kagglehub (sin descarga manual)")
flecha("e6", "CO", "MR", "model_v1.joblib<br>(subida manual a la VM)", DISCONTINUA,
       puntos=[(965, 165), (965, 745), (480, 745)], extra="exitX=1;exitY=0.5;entryX=0.5;entryY=1;", pos=-0.55)
flecha("e7", "CF", "CFD", "HTTPS :443")
flecha("e8", "CFD", "MW", "HTTPS 127.0.0.1:8000", puntos=[(450, 505), (170, 505)],
       extra="exitX=0.5;exitY=1;entryX=0.5;entryY=0;")
flecha("e9", "MW", "API")
flecha("e10", "API", "MS", extra="exitX=1;exitY=0.5;entryX=0;entryY=0.46;")
flecha("e11", "MS", "MR", "lee los pesos", puntos=[(780, 620), (480, 620)],
       extra="exitX=0.5;exitY=1;entryX=0.5;entryY=0;")
flecha("e12", "MW", "FB", estilo=DISCONTINUA, extra="exitX=0.5;exitY=1;entryX=0.5;entryY=0;")
flecha("e13", "docker", "T", "MySQL: consultas, errores, alertas",
       extra="exitX=0.402;exitY=1;entryX=0.5;entryY=0;")
flecha("e14", "SSH", "T", "SSH cifrado<br>(conexión saliente del PC)", extra="exitX=0.5;exitY=0;entryX=0.5;entryY=1;")
flecha("e15", "SSH", "xampp", "127.0.0.1:3306", extra="exitX=0.5;exitY=1;entryX=0.761;entryY=0;")
flecha("e16", "AL", "ADM", extra="exitX=0.5;exitY=1;entryX=0.5;entryY=0;")

xml = (
    '<mxfile host="app.diagrams.net">\n'
    '  <diagram name="Arquitectura" id="arquitectura-stroke">\n'
    '    <mxGraphModel dx="1200" dy="900" grid="0" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" '
    'fold="1" page="0" pageScale="1" pageWidth="1100" pageHeight="1100" math="0" shadow="0">\n'
    '      <root>\n        <mxCell id="0"/>\n        <mxCell id="1" parent="0"/>\n'
    + "".join(f"        {c}\n" for c in celdas)
    + "      </root>\n    </mxGraphModel>\n  </diagram>\n</mxfile>\n"
)
SALIDA.write_text(xml, encoding="utf-8")
print(f"Escrito {SALIDA} ({len(celdas)} celdas)")
