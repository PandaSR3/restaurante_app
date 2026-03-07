from datetime import datetime, date, timedelta
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
import os
import pandas as pd
import matplotlib.pyplot as plt
ADMIN_PASSWORD = "1234"
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(
    DATABASE_URL,
    connect_args={"sslmode": "require"},
    pool_pre_ping=True,
    pool_recycle=300
)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

app = FastAPI()

def generar_grafico_metodos(db):

    ventas = db.query(VentaDB).all()

    metodos = {
        "Efectivo":0,
        "Tarjeta":0,
        "Transferencia":0
    }

    for v in ventas:
        if v.metodo_pago in metodos:
            metodos[v.metodo_pago] += v.total

    nombres = list(metodos.keys())
    valores = list(metodos.values())

    plt.figure(figsize=(6,4))
    plt.bar(nombres, valores)

    plt.title("Ventas por Método de Pago")
    plt.ylabel("Total")

    ruta = "grafico_metodos.png"
    plt.savefig(ruta)
    plt.close()

    return ruta

def plantilla(titulo, contenido):

    return f"""
    <html>

    <head>

    <title>{titulo}</title>

    <style>

    body {{
        font-family: Arial;
        background:#f4f6f9;
        margin:0;
        padding:0;
    }}

    header {{
        background:#2c3e50;
        color:white;
        padding:15px;
        text-align:center;
    }}

    .container {{
        padding:30px;
    }}

    .grid {{
        display:grid;
        grid-template-columns:repeat(auto-fit,minmax(200px,1fr));
        gap:20px;
    }}

    .card {{
        background:white;
        padding:20px;
        border-radius:10px;
        box-shadow:0px 4px 10px rgba(0,0,0,0.1);
        text-align:center;
        text-decoration:none;
        color:black;
        font-weight:bold;
    }}

    .card:hover {{
        background:#ecf0f1;
    }}

    button {{
        padding:10px 20px;
        border:none;
        border-radius:8px;
        background:#3498db;
        color:white;
        cursor:pointer;
    }}

    table {{
        width:100%;
        border-collapse:collapse;
        background:white;
    }}

    th,td {{
        padding:10px;
        border-bottom:1px solid #ddd;
        text-align:center;
    }}

    th {{
        background:#34495e;
        color:white;
    }}

    </style>

    </head>

    <body>

    <header>

    <h1>{titulo}</h1>

    </header>

    <div class="container">

    {contenido}

    </div>

    </body>

    </html>
    """

# -------------------- MODELOS --------------------

class PedidoDB(Base):
    __tablename__ = "pedidos"

    id = Column(Integer, primary_key=True, index=True)
    mesa = Column(Integer)
    nombre = Column(String)
    cantidad = Column(Integer)
    comentario = Column(String)
    estado = Column(String)
    precio = Column(Float)
    cerrado = Column(Boolean, default=False)
    fecha = Column(DateTime, default=datetime.utcnow)


class PlatoDB(Base):
    __tablename__ = "platos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True)
    precio = Column(Float)


class VentaDB(Base):
    __tablename__ = "ventas"

    id = Column(Integer, primary_key=True)
    mesa = Column(Integer)
    total = Column(Float)
    metodo_pago = Column(String)
    fecha = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# -------------------- INICIO --------------------

@app.get("/", response_class=HTMLResponse)
def home():
    html = """
    <html>
    <head>
        <title>POS Restaurante</title>
        <style>

body{
font-family:Arial;
background:#f4f6f9;
margin:0;
padding:0;
}

h1{
background:#2c3e50;
color:white;
padding:20px;
margin:0;
}

.menu{
padding:15px;
background:white;
box-shadow:0px 2px 10px rgba(0,0,0,0.1);
}

.menu a{
margin-right:15px;
padding:10px 20px;
background:#3498db;
color:white;
text-decoration:none;
border-radius:6px;
font-weight:bold;
}

.mesas{
display:grid;
grid-template-columns:repeat(auto-fill,minmax(150px,1fr));
gap:20px;
padding:30px;
}

.mesa{
background:white;
padding:30px;
border-radius:12px;
box-shadow:0px 4px 10px rgba(0,0,0,0.15);
font-size:20px;
text-align:center;
text-decoration:none;
color:#333;
transition:0.2s;
}

.mesa:hover{
background:#2ecc71;
color:white;
transform:scale(1.05);
}

</style>
    </head>
    <body>
        <h1>🍽️ Sistema POS Restaurante</h1>

        <div class="menu">

<a href='/dashboard'>🍽️ Mesas</a>

<a href='/cocina'>👩‍🍳 Cocina</a>

<a href='/admin/login'>⚙️ Admin</a>

<a href='/admin/hoy'>📊 Ventas Hoy</a>

<a href='/admin/ventas'>🧾 Tickets Hoy</a>

<a href='/admin/platos_vendidos'>🏆 Ranking Platos</a>

<a href='/admin/mesas_hoy'>📊 Mesas Hoy</a>

</div>

        <div class="mesas">
    """

    for i in range(1, 11):
        html += f"<a class='mesa' href='/mesa/{i}'>Mesa {i}</a>"

    html += """
        </div>
    </body>
    </html>
    """

    return html

# -------------------- MESA --------------------

@app.get("/mesa/{numero}", response_class=HTMLResponse)
def ver_mesa(numero: int):

    db = SessionLocal()

    platos = db.query(PlatoDB).all()

    pedidos = db.query(PedidoDB).filter(
        PedidoDB.mesa == numero,
        PedidoDB.cerrado == False
    ).all()

    total = sum(p.precio * p.cantidad for p in pedidos)

    html = f"""
    <html>

    <head>

    <style>

    body{{
    font-family:Arial;
    background:#f4f6f9;
    padding:30px;
    }}

    h1{{
    text-align:center;
    }}

    .contenedor{{
    display:grid;
    grid-template-columns:1fr 1fr;
    gap:30px;
    }}

    .card{{
    background:white;
    padding:20px;
    border-radius:12px;
    box-shadow:0px 4px 10px rgba(0,0,0,0.1);
    }}

    select,input,button{{
    padding:8px;
    margin-top:5px;
    }}

    .pedido{{
    border-bottom:1px solid #ddd;
    padding:10px 0;
    }}

    .total{{
    font-size:22px;
    font-weight:bold;
    margin-top:20px;
    }}

    .cerrar{{
    background:red;
    color:white;
    padding:12px;
    border:none;
    border-radius:6px;
    }}

    </style>

    </head>

    <body>

    <h1>Mesa {numero}</h1>

    <a href="/dashboard">⬅ Volver</a>

    <div class="contenedor">

    <div class="card">

    <h2>Agregar Plato</h2>

    <form method="post" action="/agregar_plato/{numero}">

    Plato

    <br>

    <select name="plato_id">
    """

    for plato in platos:
        html += f"<option value='{plato.id}'>{plato.nombre} - S/{plato.precio}</option>"

    html += """
    </select>

    <br>

    Cantidad

    <br>

    <input type="number" name="cantidad" value="1">

    <br>

    Comentario

    <br>

    <input name="comentario">

    <br><br>

    <button>Agregar</button>

    </form>

    </div>

    <div class="card">

    <h2>Pedido Actual</h2>
    """

    for pedido in pedidos:

        subtotal = pedido.precio * pedido.cantidad

        html += f"""
        <div class="pedido">

        {pedido.nombre} x{pedido.cantidad}

        — S/{subtotal:.2f}

        ({pedido.estado})

        <br>

        <a href="/sumar/{pedido.id}">➕</a>
        <a href="/restar/{pedido.id}">➖</a>
        <a href="/eliminar/{pedido.id}">❌</a>

        </div>
        """

    html += f"""

    <div class="total">
    Total: S/{total:.2f}
    </div>

    <form method="post" action="/cerrar_mesa/{numero}"
    onsubmit="return confirm('¿Cerrar cuenta?')">

    <br>

    <select name="metodo_pago">

    <option>Efectivo</option>
    <option>Tarjeta</option>
    <option>Transferencia</option>

    </select>

    <br><br>

    <button class="cerrar">
    💰 Cerrar Cuenta
    </button>

    </form>

    </div>

    </div>

    </body>

    </html>
    """

    db.close()

    return html
# -------------------- AGREGAR PLATO --------------------

@app.post("/agregar_plato/{numero}")
def agregar_plato(numero: int, plato_id: int = Form(...), cantidad: int = Form(...), comentario: str = Form("")):
    db = SessionLocal()

    plato = db.query(PlatoDB).filter(PlatoDB.id == plato_id).first()

    if plato:
        nuevo = PedidoDB(
            mesa=numero,
            nombre=plato.nombre,
            cantidad=cantidad,
            comentario=comentario,
            estado="Pendiente",
            precio=plato.precio 
        )
        db.add(nuevo)
        db.commit()

    db.close()
    return RedirectResponse(f"/mesa/{numero}", status_code=303)

# -------------------- CERRAR MESA --------------------

@app.post("/cerrar_mesa/{numero}")
def cerrar_mesa(numero: int, metodo_pago: str = Form(...)):
    db = SessionLocal()

    pedidos = db.query(PedidoDB).filter(
        PedidoDB.mesa == numero,
        PedidoDB.cerrado == False
    ).all()

    total = sum(p.precio * p.cantidad for p in pedidos)

    # Crear registro de venta
    nueva_venta = VentaDB(
        mesa=numero,
        total=total,
        metodo_pago=metodo_pago
    )

    db.add(nueva_venta)

    # Cerrar pedidos
    for pedido in pedidos:
        pedido.cerrado = True

    db.commit()
    db.close()

    return RedirectResponse("/", status_code=303)

# -------------------- COCINA --------------------

@app.get("/cocina", response_class=HTMLResponse)
def cocina():
    db = SessionLocal()

    pedidos = db.query(PedidoDB).filter(
        PedidoDB.cerrado == False
    ).order_by(PedidoDB.id.desc()).all()


    html = """
    <html>
    <head>
    <meta http-equiv="refresh" content="5">
    <style>
    body{
        font-family:Arial;
        background:#111;
        color:white;
        text-align:center;
    }

    .pedido{
        background:#222;
        margin:15px;
        padding:15px;
        border-radius:10px;
    }

    .pendiente{
        color:orange;
        font-weight:bold;
    }

    .listo{
        color:lightgreen;
        font-weight:bold;
    }
    </style>
    </head>
    <body>

    <h1>👩‍🍳 Cocina</h1>
    """

    for pedido in pedidos:

        clase = "pendiente" if pedido.estado == "Pendiente" else "listo"

        html += f"""
        <div class='pedido'>
        <h2>Mesa {pedido.mesa}</h2>
        <h3>{pedido.nombre} x{pedido.cantidad}</h3>
        <p>Comentario: {pedido.comentario}</p>
        <p class='{clase}'>{pedido.estado}</p>
        """

        if pedido.estado == "Pendiente":

            html += f"""
            <form method='post' action='/cambiar_estado/{pedido.id}'>
            <button style='padding:10px;'>Marcar Listo</button>
            </form>
            """

        html += "</div>"

    html += "<br><a href='/'>⬅ Volver</a></body></html>"

    db.close()
    return html


@app.post("/cambiar_estado/{pedido_id}")
def cambiar_estado(pedido_id: int):
    db = SessionLocal()
    pedido = db.query(PedidoDB).filter(PedidoDB.id == pedido_id).first()

    if pedido:
        pedido.estado = "Listo"
        db.commit()

    db.close()
    return RedirectResponse("/cocina", status_code=303)

# -------------------- ADMIN PLATOS --------------------

@app.get("/admin/platos", response_class=HTMLResponse)
def admin_platos():
    db = SessionLocal()
    platos = db.query(PlatoDB).all()

    html = "<h1>Administrador de Platos 🍽️</h1>"

    html += """
    <form method="post" action="/admin/platos">
        Nombre: <input name="nombre">
        Precio: <input name="precio" type="number" step="0.01">
        <button type="submit">Agregar</button>
    </form>
    <hr>
    """

    for plato in platos:
      html += f"""
    <p>
    {plato.nombre} - ${plato.precio}
    <form method="post" action="/admin/eliminar_plato/{plato.id}" style="display:inline;">
    <button style="background:red;color:white;">Eliminar</button>
    </form>
    </p>
    """

    html += "<br><a href='/'>⬅ Volver</a>"

    db.close()
    return html

@app.post("/admin/eliminar_plato/{plato_id}")
def eliminar_plato(plato_id: int):

    db = SessionLocal()

    plato = db.query(PlatoDB).filter(PlatoDB.id == plato_id).first()

    if plato:
        db.delete(plato)
        db.commit()

    db.close()

    return RedirectResponse("/admin/platos", status_code=303)


@app.post("/admin/platos")
def agregar_plato_admin(nombre: str = Form(...), precio: float = Form(...)):
    db = SessionLocal()
    nuevo = PlatoDB(nombre=nombre, precio=precio)
    db.add(nuevo)
    db.commit()
    db.close()
    return RedirectResponse("/admin/platos", status_code=303)

# -------------------- HISTORIAL --------------------

@app.get("/admin/historial", response_class=HTMLResponse)
def historial():
    db = SessionLocal()

    pedidos = db.query(PedidoDB).filter(PedidoDB.cerrado == True).all()

    html = "<h1>Historial de Ventas 💰</h1><hr>"

    total = 0

    for pedido in pedidos:
            subtotal = pedido.precio * pedido.cantidad
            total += subtotal

            html += f"<p>Mesa {pedido.mesa} - {pedido.nombre} x{pedido.cantidad} = S/{subtotal:.2f}</p>"

    html += f"<hr><h2>Total General: S/{total:.2f}</h2>"
    html += "<br><a href='/'>⬅ Volver</a>"

    db.close()
    return html

# -------------------- VENTAS HOY --------------------

@app.get("/admin/hoy", response_class=HTMLResponse)
def ventas_hoy():

    db = SessionLocal()

    hoy = date.today()

    ventas = db.query(VentaDB).all()

    total = 0
    efectivo = 0
    tarjeta = 0
    transferencia = 0

    cantidad = 0

    for venta in ventas:

        if venta.fecha and venta.fecha.date() == hoy:

            cantidad += 1
            total += venta.total

            if venta.metodo_pago == "Efectivo":
                efectivo += venta.total

            elif venta.metodo_pago == "Tarjeta":
                tarjeta += venta.total

            elif venta.metodo_pago == "Transferencia":
                transferencia += venta.total

    promedio = total / cantidad if cantidad > 0 else 0
    grafico = generar_grafico_metodos(db)

    html = f"""

    <h1>📊 Ventas de Hoy</h1>

    <br>
    <img src="/grafico_metodos" width="400">

<a href="/admin/exportar/dia">
<button>📥 Excel Hoy</button>
</a>

<a href="/admin/exportar/semana">
<button>📥 Excel Semana</button>
</a>

<a href="/admin/exportar/mes">
<button>📥 Excel Mes</button>
</a>

<br><br>

    <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:20px;padding:20px;">

    <div style="background:white;padding:20px;border-radius:10px;">
    <h2>Total del Día</h2>
    <h1>S/{total:.2f}</h1>
    </div>

    <div style="background:white;padding:20px;border-radius:10px;">
    <h2>Ventas</h2>
    <h1>{cantidad}</h1>
    </div>

    <div style="background:white;padding:20px;border-radius:10px;">
    <h2>Ticket Promedio</h2>
    <h1>S/{promedio:.2f}</h1>
    </div>

    <div style="background:white;padding:20px;border-radius:10px;">
    <h2>Efectivo</h2>
    <h1>S/{efectivo:.2f}</h1>
    </div>

    <div style="background:white;padding:20px;border-radius:10px;">
    <h2>Tarjeta</h2>
    <h1>S/{tarjeta:.2f}</h1>
    </div>

    <div style="background:white;padding:20px;border-radius:10px;">
    <h2>Transferencia</h2>
    <h1>S/{transferencia:.2f}</h1>
    </div>

    </div>

    <br>

    <a href="/">⬅ Volver</a>

    """

    db.close()

    return html

# -------------------- EXPORTAR EXCEL --------------------

@app.get("/admin/login", response_class=HTMLResponse)
def login_admin():
    return """
    <h1>Login Administrador 🔐</h1>
    <form method="post" action="/admin/login">
        Contraseña: <input type="password" name="password">
        <button type="submit">Entrar</button>
    </form>
    <br><a href='/'>⬅ Volver</a>
    """

@app.post("/admin/login")
def validar_login(password: str = Form(...)):
    if password == ADMIN_PASSWORD:
        return RedirectResponse("/admin", status_code=303)
    else:
        return HTMLResponse("<h3>❌ Contraseña incorrecta</h3><a href='/admin/login'>Volver</a>")
    
@app.get("/admin", response_class=HTMLResponse)
def panel_admin():

    contenido = """

    <div class="grid">

    <a class="card" href="/admin/platos">
    🍽️ Gestionar Platos
    </a>

    <a class="card" href="/admin/hoy">
    📊 Ventas Hoy
    </a>

    <a class="card" href="/admin/historial">
    📜 Historial
    </a>

    <a class="card" href="/admin/mesas_hoy">
    🪑 Mesas Cerradas Hoy
    </a>

    <a class="card" href="/admin/platos_vendidos">
    🏆 Ranking de Platos
    </a>

    <a class="card" href="/admin/reportes">
    📁 Exportar Excel
    </a>

    <a class="card" href="/admin/graficas">
    📈 Gráficas de Ventas
    </a>

    <a class="card" href="/admin/exportar/dia">
📅 Excel del Día
</a>

<a class="card" href="/admin/exportar/semana">
📆 Excel de la Semana
</a>

<a class="card" href="/admin/exportar/mes">
🗓 Excel del Mes
</a>

    </div>

    <br>

    <a href="/">⬅ Volver</a>

    """

    return plantilla("Panel Administrador", contenido)
    
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    db = SessionLocal()

    html = """
    <h1>Dashboard Mesas 🍽️</h1>
    <style>
    .grid{
        display:grid;
        grid-template-columns:repeat(5,1fr);
        gap:20px;
        margin-top:30px;
    }

    .mesa{
        padding:30px;
        border-radius:12px;
        text-align:center;
        font-size:20px;
        font-weight:bold;
        text-decoration:none;
        color:white;
    }

    .libre{
        background-color:green;
    }

    .ocupada{
        background-color:red;
    }
    </style>

    <div class='grid'>
    """

    for i in range(1, 11):

        pedidos = db.query(PedidoDB).filter(
            PedidoDB.mesa == i,
            PedidoDB.cerrado == False
        ).count()

        estado = "ocupada" if pedidos > 0 else "libre"

        html += f"""
        <a class='mesa {estado}' href='/mesa/{i}'>
        Mesa {i}
        </a>
        """

    html += "</div><br><a href='/'>⬅ Volver</a>"

    db.close()
    return html

# -------------------- SUMAR CANTIDAD --------------------

@app.get("/sumar/{pedido_id}")
def sumar(pedido_id: int):
    db = SessionLocal()

    pedido = db.query(PedidoDB).filter(PedidoDB.id == pedido_id).first()

    if pedido:
        pedido.cantidad += 1
        mesa = pedido.mesa
        db.commit()
    else:
        mesa = 1

    db.close()

    return RedirectResponse(f"/mesa/{mesa}", status_code=303)


# -------------------- RESTAR CANTIDAD --------------------

@app.get("/restar/{pedido_id}")
def restar(pedido_id: int):
    db = SessionLocal()

    pedido = db.query(PedidoDB).filter(PedidoDB.id == pedido_id).first()

    if pedido:

        mesa = pedido.mesa

        if pedido.cantidad > 1:
            pedido.cantidad -= 1
        else:
            db.delete(pedido)

        db.commit()

    else:
        mesa = 1

    db.close()

    return RedirectResponse(f"/mesa/{mesa}", status_code=303)


# -------------------- ELIMINAR PEDIDO --------------------

@app.get("/eliminar/{pedido_id}")
def eliminar(pedido_id: int):
    db = SessionLocal()

    pedido = db.query(PedidoDB).filter(PedidoDB.id == pedido_id).first()

    if pedido:
        mesa = pedido.mesa
        db.delete(pedido)
        db.commit()
    else:
        mesa = 1

    db.close()

    return RedirectResponse(f"/mesa/{mesa}", status_code=303)

# -------------------- ELIMINAR PLATO MENU --------------------

@app.get("/ticket/{venta_id}", response_class=HTMLResponse)
def ticket(venta_id: int):

    db = SessionLocal()

    venta = db.query(VentaDB).filter(VentaDB.id == venta_id).first()

    pedidos = db.query(PedidoDB).filter(
        PedidoDB.mesa == venta.mesa,
        PedidoDB.cerrado == True
    ).all()

    html = f"""
    <html>
    <body style="font-family:monospace;text-align:center;">
    
    <h2>🍽️ Restaurante</h2>
    <p>Mesa {venta.mesa}</p>
    <p>{venta.fecha.strftime("%d/%m/%Y %H:%M")}</p>

    <hr>
    """

    for pedido in pedidos:

        subtotal = pedido.precio * pedido.cantidad

        html += f"""
        <p>
        {pedido.nombre} x{pedido.cantidad}
        S/{subtotal:.2f}
        </p>
        """

    html += f"""
    <hr>
    <h3>Total: S/{venta.total:.2f}</h3>
    <p>Pago: {venta.metodo_pago}</p>

    <br>

    <button onclick="window.print()">🖨️ Imprimir</button>

    <br><br>
    <a href="/">Volver</a>

    </body>
    </html>
    """

    db.close()
    return html

@app.get("/admin/reportes", response_class=HTMLResponse)
def reportes():

    return """

    <h1>📁 Reportes</h1>

    <a href="/admin/excel/dia">Descargar Excel Hoy</a>

    <br><br>

    <a href="/admin/excel/semana">Descargar Excel Semana</a>

    <br><br>

    <a href="/admin/excel/mes">Descargar Excel Mes</a>

    <br><br>

    <a href="/admin">⬅ Volver</a>

    """


@app.get("/admin/mesas_hoy", response_class=HTMLResponse)
def mesas_hoy():

    db = SessionLocal()

    hoy = date.today()

    ventas = db.query(VentaDB).all()

    filas = ""

    for v in ventas:

        if v.fecha.date() == hoy:

            filas += f"""
            <tr>
            <td>Mesa {v.mesa}</td>
            <td>S/{v.total:.2f}</td>
            <td>{v.metodo_pago}</td>
            <td>{v.fecha}</td>
            </tr>
            """

    contenido = f"""

    <table>

    <tr>
    <th>Mesa</th>
    <th>Total</th>
    <th>Pago</th>
    <th>Fecha</th>
    </tr>

    {filas}

    </table>

    <br>

    <a href="/admin">⬅ Volver</a>

    """

    db.close()

    return plantilla("Mesas Cerradas Hoy", contenido)

@app.get("/admin/platos_vendidos", response_class=HTMLResponse)
def ranking_platos():

    db = SessionLocal()

    pedidos = db.query(PedidoDB).filter(
        PedidoDB.cerrado == True
    ).all()

    conteo = {}

    for p in pedidos:

        if p.nombre not in conteo:
            conteo[p.nombre] = 0

        conteo[p.nombre] += p.cantidad

    filas = ""

    ranking = sorted(conteo.items(), key=lambda x: x[1], reverse=True)

    for plato, cantidad in ranking:

        filas += f"""
        <tr>
        <td>{plato}</td>
        <td>{cantidad}</td>
        </tr>
        """

    contenido = f"""

    <table>

    <tr>
    <th>Plato</th>
    <th>Cantidad Vendida</th>
    </tr>

    {filas}

    </table>

    <br>

    <a href="/admin">⬅ Volver</a>

    """

    db.close()

    return plantilla("Ranking de Platos", contenido)

@app.get("/admin/graficas", response_class=HTMLResponse)
def graficas():

    db = SessionLocal()

    ventas = db.query(VentaDB).all()

    dias = {}
    
    for v in ventas:

        dia = v.fecha.date()

        if dia not in dias:
            dias[dia] = 0

        dias[dia] += v.total

    labels = list(dias.keys())
    valores = list(dias.values())

    contenido = f"""

    <canvas id="grafica"></canvas>

    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

    <script>

    const ctx = document.getElementById('grafica');

    new Chart(ctx, {{
        type: 'bar',
        data: {{
            labels: {labels},
            datasets: [{{
                label: 'Ventas',
                data: {valores}
            }}]
        }}
    }});

    </script>

    <br><br>

    <a href="/admin">⬅ Volver</a>

    """

    db.close()

    return plantilla("Gráficas de Ventas", contenido)

@app.get("/admin/exportar/{tipo}")
def exportar_excel(tipo: str):

    db = SessionLocal()
    hoy = date.today()

    if tipo == "dia":
        inicio = hoy

    elif tipo == "semana":
        inicio = hoy - timedelta(days=7)

    elif tipo == "mes":
        inicio = hoy - timedelta(days=30)

    else:
        inicio = hoy

    ventas = db.query(VentaDB).all()
    pedidos = db.query(PedidoDB).all()

    ventas_data = []
    platos_data = []
    mesas_data = []

    total = 0

    metodos = {
        "Efectivo":0,
        "Tarjeta":0,
        "Transferencia":0
    }

    for venta in ventas:

        if venta.fecha.date() >= inicio:

            ventas_data.append({
                "Mesa": venta.mesa,
                "Total": venta.total,
                "Metodo": venta.metodo_pago,
                "Fecha": venta.fecha
            })

            total += venta.total
            metodos[venta.metodo_pago] += venta.total

    for pedido in pedidos:

        if pedido.fecha.date() >= inicio:

            platos_data.append({
                "Plato": pedido.nombre,
                "Cantidad": pedido.cantidad
            })

            mesas_data.append({
                "Mesa": pedido.mesa,
                "Plato": pedido.nombre,
                "Cantidad": pedido.cantidad
            })

    df_ventas = pd.DataFrame(ventas_data)

    df_platos = pd.DataFrame(platos_data).groupby("Plato").sum().sort_values(by="Cantidad", ascending=False)

    df_mesas = pd.DataFrame(mesas_data)

    df_metodos = pd.DataFrame([
        {"Metodo":"Efectivo","Total":metodos["Efectivo"]},
        {"Metodo":"Tarjeta","Total":metodos["Tarjeta"]},
        {"Metodo":"Transferencia","Total":metodos["Transferencia"]}
    ])

    ticket_promedio = total / len(ventas_data) if ventas_data else 0

    df_resumen = pd.DataFrame([
        {"Metrica":"Total Ventas","Valor":total},
        {"Metrica":"Cantidad Ventas","Valor":len(ventas_data)},
        {"Metrica":"Ticket Promedio","Valor":ticket_promedio}
    ])

    archivo = f"reporte_restaurante_{tipo}.xlsx"

    with pd.ExcelWriter(archivo) as writer:

        df_ventas.to_excel(writer, sheet_name="Ventas", index=False)
        df_platos.to_excel(writer, sheet_name="Platos Vendidos")
        df_mesas.to_excel(writer, sheet_name="Consumo por Mesa", index=False)
        df_metodos.to_excel(writer, sheet_name="Metodos Pago", index=False)
        df_resumen.to_excel(writer, sheet_name="Resumen", index=False)

    db.close()

    return FileResponse(
        archivo,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=archivo
    )

@app.get("/admin/ticket/{mesa}", response_class=HTMLResponse)
def ticket_mesa(mesa:int):

    db = SessionLocal()

    pedidos = db.query(PedidoDB).filter(
        PedidoDB.mesa == mesa
    ).all()

    html = f"<h1>Ticket Mesa {mesa}</h1><hr>"

    total = 0

    for p in pedidos:

        subtotal = p.precio * p.cantidad
        total += subtotal

        html += f"""
        <p>{p.nombre} x{p.cantidad} - S/{subtotal:.2f}</p>
        """

    html += f"<hr><h2>Total S/{total:.2f}</h2>"

    html += "<br><a href='/admin'>Volver</a>"

    db.close()

    return html
