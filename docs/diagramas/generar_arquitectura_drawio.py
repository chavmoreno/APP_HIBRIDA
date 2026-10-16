"""Genera docs/diagramas/Arquitectura.drawio (diagrama de arquitectura para draw.io / diagrams.net).

Uso:
    python docs/diagramas/generar_arquitectura_drawio.py

Mantiene el estilo del diagrama original (fuente Recursive, sombras, colores) y refleja la arquitectura
actual: microservicio de inferencia en Docker, model registry montado como volumen y flujo Kaggle → Colab.
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
caja("nube", "<b>Nube</b> (Google / Cloudflare)", 20, 0, 960, 360, NUBE)
caja("local", "<b>Máquina local</b> (Windows)", 20, 390, 960, 560, LOCAL)
caja("xampp", "<b>XAMPP</b> · MySQL (MariaDB), sólo 127.0.0.1:3306", 60, 690, 460, 220, XAMPP)
caja("docker", "<b>Docker Desktop</b> · contenedor <i>stroke-inferencia</i><br>"
     "<font style='font-size:12px'>usuario sin privilegios · sólo lectura · restart: unless-stopped</font>",
     600, 470, 340, 180, DOCKER)

# ---------------- Nube ----------------
caja("U", "Usuario (navegador)", 360, 40, 180, 45)
caja("FE", "<b>Frontend SPA</b> - Firebase Hosting<br>Nueva consulta / Histórico<br>Páginas 404 · 401 · 500 · ErrorBoundary",
     320, 120, 260, 100)
caja("FA", "<b>Firebase Authentication</b><br>correo/contraseña o Google", 40, 255, 220, 70)
caja("KG", "<b>Kaggle</b><br>stroke-prediction-dataset", 720, 30, 220, 55)
caja("CO", "<b>Google Colab</b><br>EDA + preprocesamiento<br>+ entrenamiento", 720, 125, 220, 80)
caja("CF", "<b>Cloudflare Tunnel</b><br>api.tudominio.com", 360, 270, 180, 60)

# ---------------- Máquina local ----------------
caja("MW", "Middleware X-Request-ID<br>+ manejadores de excepciones", 340, 420, 220, 60)
caja("API", "<b>API Gateway</b> FastAPI :8000<br>(HTTPS, nativo)", 340, 520, 220, 60)
caja("FB", "Respaldo: archivo .log rotativo<br>si MySQL no responde", 60, 420, 220, 60)
caja("MS", "<b>Microservicio inferencia</b> :8001<br>HTTPS · publicado sólo en 127.0.0.1", 630, 530, 280, 65)
caja("MR", "<b>Model registry</b><br>inference-service/models/model_v1.joblib<br>(volumen de sólo lectura)",
     630, 780, 280, 75)
caja("DB2", "<b>consultas_db</b><br>consultas y resultados", 90, 745, 170, 130, BD)
caja("DB4", "<b>errores_db</b><br>log de errores", 320, 745, 170, 130, BD)

# ---------------- Fuera ----------------
caja("ADM", "<b>Panel admin / alertas</b><br>críticos a correo o Telegram", 300, 980, 240, 70)
caja("leyenda", "<b>Leyenda</b><br>── flujo principal<br>- - - errores / respaldo / copia manual del modelo",
     620, 975, 330, 70, NOTA)

# ---------------- Flechas ----------------
flecha("e1", "U", "FE", "HTTPS")
flecha("e2", "FE", "FA", "Login correo o Google", puntos=[(150, 170)],
       extra="exitX=0;exitY=0.5;entryX=0.5;entryY=0;")
flecha("e3", "FE", "CF", "HTTPS + Bearer token", extra="exitX=0.4;exitY=1;entryX=0.37;entryY=0;")
flecha("e4", "FE", "CF", "POST /api/errores<br>errores de JS", DISCONTINUA,
       puntos=[(620, 200), (620, 300)], extra="exitX=1;exitY=0.8;entryX=1;entryY=0.5;")
flecha("e5", "KG", "CO", "kagglehub (sin descarga manual)")
flecha("e6", "CO", "MR", "model_v1.joblib<br>(copia manual)", DISCONTINUA,
       puntos=[(960, 165), (960, 817)], extra="exitX=1;exitY=0.5;entryX=1;entryY=0.5;", pos=-0.6)
flecha("e7", "CF", "MW")
flecha("e8", "MW", "API")
flecha("e9", "API", "MS", extra="exitX=1;exitY=0.5;entryX=0;entryY=0.31;")
flecha("e10", "MS", "MR", "lee los pesos", extra="exitX=0.5;exitY=1;entryX=0.5;entryY=0;")
flecha("e11", "API", "DB2", "guarda consulta", puntos=[(450, 650), (175, 650)],
       extra="exitX=0.5;exitY=1;entryX=0.5;entryY=0;", pos=-0.3)
flecha("e12", "MW", "DB4", "Errores 4xx/5xx<br>sanitizados", puntos=[(300, 465), (300, 715), (405, 715)],
       extra="exitX=0;exitY=0.75;entryX=0.5;entryY=0;", pos=0.25)
flecha("e13", "MW", "FB", estilo=DISCONTINUA, extra="exitX=0;exitY=0.25;entryX=1;entryY=0.25;")
flecha("e14", "MS", "DB4", "Errores de inferencia<br>vía host.docker.internal", DISCONTINUA,
       puntos=[(580, 575), (580, 810)], extra="exitX=0;exitY=0.7;entryX=1;entryY=0.5;")
flecha("e15", "DB4", "ADM", extra="exitX=0.5;exitY=1;entryX=0.5;entryY=0;")

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
