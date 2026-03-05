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
    pool_pre_ping=True
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


Base.metadata.create_all(bind=engine)

class VentaDB(Base):
    __tablename__ = "ventas"

    id = Column(Integer, primary_key=True)
    mesa = Column(Integer)
    total = Column(Float)
    metodo_pago = Column(String)
    fecha = Column(DateTime, default=datetime.utcnow)

# -------------------- INICIO --------------------

@app.get("/", response_class=HTMLResponse)
def home():
    html = "<h1>Mesas Restaurante 🍽️</h1><br>"

    html += "<a href='/admin/login'>⚙️ Administrar Platos</a><br>"
    html += "<a href='/admin/historial'>📊 Historial</a><br>"
    html += "<a href='/admin/hoy'>📅 Ventas de Hoy</a><br>"
    html += "<a href='/cocina'>👩‍🍳 Cocina</a><br><br>"

    for i in range(1, 11):
        html += f"<a href='/mesa/{i}'>Mesa {i}</a><br>"

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

    html = f"<h1>Mesa {numero}</h1>"

    html += f"""
    <form method="post" action="/agregar_plato/{numero}">
        <select name="plato_id">
    """

    for plato in platos:
        html += f"<option value='{plato.id}'>{plato.nombre} - ${plato.precio}</option>"

    html += """
        </select>
        Cantidad: <input type="number" name="cantidad" value="1">
        Comentario: <input name="comentario">
        <button type="submit">Agregar</button>
    </form>
    <hr>
    """

    total = sum(p.precio * p.cantidad for p in pedidos)

    for pedido in pedidos:
        subtotal = pedido.precio * pedido.cantidad

        html += f"""
        <p>
        {pedido.nombre} x{pedido.cantidad}
        - ${subtotal:.2f}
        ({pedido.estado})
        </p>
        """

    html += f"<h2>Total actual: ${total:.2f}</h2>"

    html += f"""
<form method="post" action="/cerrar_mesa/{numero}">
    <h3>Seleccionar Método de Pago</h3>
    <select name="metodo_pago">
        <option value="Efectivo">Efectivo</option>
        <option value="Tarjeta">Tarjeta</option>
        <option value="Transferencia">Transferencia</option>
    </select>
    <br><br>
    <button type="submit" style="background:red;color:white;">
        💰 Cerrar Cuenta
    </button>
</form>
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

    html = "<h1>Vista Cocina 👩‍🍳</h1><br>"

    for pedido in pedidos:
        color = "orange" if pedido.estado == "Pendiente" else "green"

        html += f"""
        <div style='border:1px solid black;margin:10px;padding:10px;'>
            <h3>Mesa {pedido.mesa}</h3>
            <p>{pedido.nombre} x{pedido.cantidad}</p>
            <p>Comentario: {pedido.comentario}</p>
            <p>Estado: <b style='color:{color}'>{pedido.estado}</b></p>
        """

        if pedido.estado == "Pendiente":
            html += f"""
            <form method='post' action='/cambiar_estado/{pedido.id}'>
                <button type='submit'>Marcar como Listo</button>
            </form>
            """

        html += "</div>"

    html += "<br><a href='/'>Volver</a>"

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
        html += f"<p>{plato.nombre} - ${plato.precio}</p>"

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
    pedidos = db.query(PedidoDB).filter(PedidoDB.cerrado == True).all()

    html = "<h1>Ventas de Hoy 📅</h1><hr>"

    total = 0

    for pedido in pedidos:
        if pedido.fecha and pedido.fecha.date() == hoy: 
                subtotal = pedido.precio * pedido.cantidad
                total += subtotal
                html += f"<p>Mesa {pedido.mesa} - {pedido.nombre} x{pedido.cantidad} = ${subtotal:.2f}</p>"

    html += f"<hr><h2>Total Hoy: ${total:.2f}</h2>"
    html += "<br><a href='/'>⬅ Volver</a>"

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