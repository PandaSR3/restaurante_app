from datetime import datetime, date
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
import os
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

<a href='/admin/mesas_hoy'>🧾 Tickets Hoy</a>

<a href='/admin/platos_vendidos'>🏆 Ranking Platos</a>

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
        html += f"<option value='{plato.id}'>{plato.nombre} - ${plato.precio}</option>"

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

        — ${subtotal:.2f}

        ({pedido.estado})

        <br>

        <a href="/sumar/{pedido.id}">➕</a>
        <a href="/restar/{pedido.id}">➖</a>
        <a href="/eliminar/{pedido.id}">❌</a>

        </div>
        """

    html += f"""

    <div class="total">
    Total: ${total:.2f}
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
     </p>
     """

    html += "<br><a href='/'>⬅ Volver</a>"

    db.close()
    return html


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

            html += f"<p>Mesa {pedido.mesa} - {pedido.nombre} x{pedido.cantidad} = ${subtotal:.2f}</p>"

    html += f"<hr><h2>Total General: ${total:.2f}</h2>"
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

    for venta in ventas:
        if venta.fecha and venta.fecha.date() == hoy:
            total += venta.total

            if venta.metodo_pago == "Efectivo":
                efectivo += venta.total
            elif venta.metodo_pago == "Tarjeta":
                tarjeta += venta.total
            elif venta.metodo_pago == "Transferencia":
                transferencia += venta.total

    cantidad = len([v for v in ventas if v.fecha and v.fecha.date() == hoy])
    promedio = total / cantidad if cantidad > 0 else 0

    html = f"""
    <h1>Dashboard Hoy 📊</h1>
    <hr>
    <h2>Total Hoy: ${total:.2f}</h2>
    <h3>Efectivo: ${efectivo:.2f}</h3>
    <h3>Tarjeta: ${tarjeta:.2f}</h3>
    <h3>Transferencia: ${transferencia:.2f}</h3>
    <hr>
    <h3>Cantidad de Ventas: {cantidad}</h3>
    <h3>Ticket Promedio: ${promedio:.2f}</h3>
    <br>
    <a href='/'>⬅ Volver</a>
    """

    db.close()
    return html

@app.get("/admin/mesas_hoy", response_class=HTMLResponse)
def mesas_hoy():
    db = SessionLocal()

    hoy = date.today()

    ventas = db.query(VentaDB).all()

    html = """
    <h1>Mesas Cerradas Hoy 🍽️</h1>
    <hr>
    <table border="1" cellpadding="10">
    <tr>
        <th>Mesa</th>
        <th>Total</th>
        <th>Método de Pago</th>
        <th>Hora</th>
        <th>Ticket</th>
    </tr>
    """

    for venta in ventas:
        if venta.fecha and venta.fecha.date() == hoy:

            hora = venta.fecha.strftime("%H:%M")

            html += f"""
            <tr>
                <td>{venta.mesa}</td>
                <td>${venta.total:.2f}</td>
                <td>{venta.metodo_pago}</td>
                <td>{hora}</td>
                <td>
                    <a href="/ticket/{venta.id}">Ver Ticket</a>
                </td>
            </tr>
            """

    html += "</table><br><a href='/'>⬅ Volver</a>"

    db.close()
    return html

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
        return RedirectResponse("/admin/platos", status_code=303)
    else:
        return HTMLResponse("<h3>❌ Contraseña incorrecta</h3><a href='/admin/login'>Volver</a>")
    
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

@app.get("/admin/platos_vendidos", response_class=HTMLResponse)
def platos_vendidos():
    db = SessionLocal()

    pedidos = db.query(PedidoDB).filter(PedidoDB.cerrado == True).all()

    conteo = {}

    for p in pedidos:

        if p.nombre not in conteo:
            conteo[p.nombre] = 0

        conteo[p.nombre] += p.cantidad

    ranking = sorted(conteo.items(), key=lambda x: x[1], reverse=True)

    html = "<h1>Platos Más Vendidos 🍽️</h1><hr>"

    for nombre, cantidad in ranking:
        html += f"<p>{nombre} — {cantidad} vendidos</p>"

    html += "<br><a href='/'>⬅ Volver</a>"

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

@app.get("/admin/eliminar_plato/{plato_id}")
def eliminar_plato(plato_id: int):

    db = SessionLocal()

    plato = db.query(PlatoDB).filter(PlatoDB.id == plato_id).first()

    if plato:
        db.delete(plato)
        db.commit()

    db.close()

    return RedirectResponse("/admin/platos", status_code=303)

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
        ${subtotal:.2f}
        </p>
        """

    html += f"""
    <hr>
    <h3>Total: ${venta.total:.2f}</h3>
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