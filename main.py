from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import create_engine, Column, Integer, String, Float
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

Base.metadata.create_all(bind=engine)

app = FastAPI()

class PlatoDB(Base):
    __tablename__ = "platos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True)
    precio = Column(Float)

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
    mesa = mesas[numero]
    
    html = f"<h1>Mesa {numero}</h1>"
    html += f"<p>Estado: {mesa['estado']}</p>"
    
    # Mostrar pedido actual
    total = 0
    html += "<h2>Pedido:</h2>"
    
    for item in mesa["pedido"]:
        subtotal = item["precio"] * item["cantidad"]
        total += subtotal
        html += f"<p>{item['nombre']} x{item['cantidad']} - S/ {subtotal}</p>"
    
    html += f"<h3>Total: S/ {total}</h3>"

    if mesa["pedido"]:
      html += f"""
      <form method='post' action='/finalizar/{numero}'>
        <button style='background-color:green;color:white;padding:10px;'>
            FINALIZAR SERVICIO
        </button>
    </form>
    """
    
    # Formulario para agregar platos
    html += f"""
    <h2>Agregar Plato</h2>
    <form method='post' action='/agregar_plato/{numero}'>
    """
    
    for id_plato, datos in menu.items():
        html += f"""
        <input type='radio' name='plato_id' value='{id_plato}' required>
        {datos['nombre']} - S/ {datos['precio']}<br>
        """
    
    html += """
        Cantidad: <input type='number' name='cantidad' min='1' value='1'><br>
        Comentario: <input type='text' name='comentario'><br><br>
        <button type='submit'>Agregar</button>
    </form>
    <br><a href='/'>Volver</a>
    """
    
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