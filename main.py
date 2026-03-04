from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class PedidoDB(Base):
    __tablename__ = "pedidos"

    id = Column(Integer, primary_key=True, index=True)
    mesa = Column(Integer)
    nombre = Column(String)
    cantidad = Column(Integer)
    comentario = Column(String)
    estado = Column(String)
    cerrado = Column(Boolean, default=False)
app = FastAPI()

class PlatoDB(Base):
    __tablename__ = "platos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True)
    precio = Column(Float)

Base.metadata.create_all(bind=engine)

# 10 mesas
mesas = {i: {"estado": "Libre", "pedido": []} for i in range(1, 11)}

# Carta simple
menu = {
    1: {"nombre": "Lomo Saltado", "precio": 25},
    2: {"nombre": "Ají de Gallina", "precio": 22},
    3: {"nombre": "Arroz Chaufa", "precio": 20},
}
pedidos_cocina = []

@app.get("/", response_class=HTMLResponse)
def home():
    html = "<h1>Mesas Restaurante 🍽️</h1><br>"
    html += "<br><a href='/admin/platos'>⚙️ Administrar Platos</a><br><br>"
    html += "<br><a href='/admin/historial'>📊 Ver Historial</a><br>"
    
    for numero, datos in mesas.items():
        estado = datos["estado"]
        color = "green" if estado == "Libre" else "red"
        
        html += f"""
        <div style='margin:10px; padding:10px; border:1px solid black;'>
            <h3>Mesa {numero}</h3>
            <p>Estado: <b style='color:{color}'>{estado}</b></p>
            <a href='/mesa/{numero}'>Entrar</a>
        </div>
        """
    
    return html


@app.get("/mesa/{numero}", response_class=HTMLResponse)
def ver_mesa(numero: int):
    db = SessionLocal()

    platos = db.query(PlatoDB).all()
    pedidos = db.query(PedidoDB).filter(
    PedidoDB.mesa == numero,
    PedidoDB.cerrado == False
).all()

    html = f"<h1>Mesa {numero}</h1>"

    # ----- FORMULARIO -----
    html += f"""
    <form method="post" action="/agregar_plato_db/{numero}">
        <label>Plato:</label>
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

    # ----- PEDIDOS ACTUALES -----
    html += "<h3>Pedidos:</h3>"

    total = 0

    for pedido in pedidos:
        subtotal = 0

        # Obtener precio del plato
        plato_db = db.query(PlatoDB).filter(PlatoDB.nombre == pedido.nombre).first()
        if plato_db:
            subtotal = plato_db.precio * pedido.cantidad
            total += subtotal

        html += f"""
        <p>
        {pedido.nombre} x{pedido.cantidad} 
        - ${subtotal:.2f} 
        ({pedido.estado})
        </p>
        """

    html += f"<h2>Total: ${total:.2f}</h2>"

    html += f"""
<form method="post" action="/cerrar_mesa/{numero}">
    <button type="submit" style="background:red;color:white;">
        💰 Cerrar Cuenta
    </button>
</form>
"""
    html += "<br><a href='/'>⬅ Volver al inicio</a>"

    db.close()
    return html


@app.post("/agregar_plato/{numero}")
def agregar_plato(numero: int, plato_id: int = Form(...), cantidad: int = Form(...), comentario: str = Form("")):
    
    plato = menu[plato_id]
    
    mesas[numero]["estado"] = "Ocupada"
    mesas[numero]["pedido"].append({
        "nombre": plato["nombre"],
        "precio": plato["precio"],
        "cantidad": cantidad,
        "comentario": comentario
    })

    # 🔥 Guardar en base de datos
    db = SessionLocal()
    nuevo_pedido = PedidoDB(
        mesa=numero,
        nombre=plato["nombre"],
        cantidad=cantidad,
        comentario=comentario,
        estado="Pendiente"
    )
    db.add(nuevo_pedido)
    db.commit()
    db.close()

    pedidos_cocina.append({
        "mesa": numero,
        "nombre": plato["nombre"],
        "cantidad": cantidad,
        "comentario": comentario,
        "estado": "Pendiente"
    })
    
    return RedirectResponse(url=f"/mesa/{numero}", status_code=303)

@app.post("/finalizar/{numero}")
def finalizar(numero: int):
    mesas[numero]["pedido"] = []
    mesas[numero]["estado"] = "Libre"
    
    return RedirectResponse(url="/", status_code=303)

@app.get("/cocina", response_class=HTMLResponse)
def vista_cocina():
    db = SessionLocal()
    pedidos = db.query(PedidoDB).order_by(PedidoDB.id.desc()).all()
    
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
            <form method='post' action='/cambiar_estado_db/{pedido.id}'>
                <button type='submit'>Marcar como Listo</button>
            </form>
            """

        html += "</div>"

    db.close()
    html += "<br><a href='/'>Volver</a>"
    return html

@app.post("/cambiar_estado_cocina/{index}")
def cambiar_estado_cocina(index: int):
    
    pedidos_cocina[index]["estado"] = "Listo"

    # 🔥 Actualizar en base de datos
    db = SessionLocal()
    pedido_db = db.query(PedidoDB).filter(
        PedidoDB.mesa == pedidos_cocina[index]["mesa"],
        PedidoDB.nombre == pedidos_cocina[index]["nombre"],
        PedidoDB.estado == "Pendiente"
    ).first()

    if pedido_db:
        pedido_db.estado = "Listo"
        db.commit()

    db.close()

    return RedirectResponse(url="/cocina", status_code=303)

@app.post("/cambiar_estado_db/{pedido_id}")
def cambiar_estado_db(pedido_id: int):
    db = SessionLocal()
    pedido = db.query(PedidoDB).filter(PedidoDB.id == pedido_id).first()

    if pedido:
        pedido.estado = "Listo"
        db.commit()

    db.close()
    return RedirectResponse(url="/cocina", status_code=303)

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

@app.post("/agregar_plato_db/{numero}")
def agregar_plato_db(numero: int, plato_id: int = Form(...), cantidad: int = Form(...), comentario: str = Form("")):
    db = SessionLocal()

    plato = db.query(PlatoDB).filter(PlatoDB.id == plato_id).first()

    if plato:
        nuevo_pedido = PedidoDB(
            mesa=numero,
            nombre=plato.nombre,
            cantidad=cantidad,
            comentario=comentario,
            estado="Pendiente"
        )
        db.add(nuevo_pedido)
        db.commit()

    db.close()
    return RedirectResponse(f"/mesa/{numero}", status_code=303)

@app.post("/cerrar_mesa/{numero}")
def cerrar_mesa(numero: int):
    db = SessionLocal()

    pedidos = db.query(PedidoDB).filter(
        PedidoDB.mesa == numero,
        PedidoDB.cerrado == False
    ).all()

    for pedido in pedidos:
        pedido.cerrado = True

    db.commit()
    db.close()

    return RedirectResponse("/", status_code=303)

@app.get("/admin/historial", response_class=HTMLResponse)
def ver_historial():
    db = SessionLocal()

    pedidos = db.query(PedidoDB).filter(PedidoDB.cerrado == True).all()

    html = "<h1>Historial de Ventas 💰</h1><hr>"

    total_general = 0

    for pedido in pedidos:
        plato = db.query(PlatoDB).filter(PlatoDB.nombre == pedido.nombre).first()
        if plato:
            subtotal = plato.precio * pedido.cantidad
            total_general += subtotal

            html += f"""
            <p>
            Mesa {pedido.mesa} - 
            {pedido.nombre} x{pedido.cantidad} 
            = ${subtotal:.2f}
            </p>
            """

    html += f"<hr><h2>Total Vendido: ${total_general:.2f}</h2>"
    html += "<br><a href='/'>⬅ Volver</a>"

    db.close()
    return html