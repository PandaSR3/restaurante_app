from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime, date, timedelta
import pandas as pd
import os

app = FastAPI()

# ---------------- CONFIG ----------------

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(
    DATABASE_URL,
    connect_args={"sslmode": "require"},
    pool_pre_ping=True
)
    
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

RESTAURANTE = "Arrecife del Norte"
MONEDA = "S/"

# ---------------- MODELOS ----------------

class PedidoDB(Base):

    __tablename__ = "pedidos"

    id = Column(Integer, primary_key=True)
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

    id = Column(Integer, primary_key=True)
    nombre = Column(String)
    precio = Column(Float)


class VentaDB(Base):

    __tablename__ = "ventas"

    id = Column(Integer, primary_key=True)
    mesa = Column(Integer)
    total = Column(Float)
    metodo_pago = Column(String)
    fecha = Column(DateTime, default=datetime.utcnow)


Base.metadata.create_all(bind=engine)

@app.get("/")
def home():
    return RedirectResponse("/dashboard")

# ---------------- DASHBOARD ----------------

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():

    db = SessionLocal()

    html = f"""
    <h1>{RESTAURANTE}</h1>

    <style>

    body{{font-family:Arial}}

    .grid{{
    display:grid;
    grid-template-columns:repeat(5,1fr);
    gap:20px;
    }}

    .mesa{{
    padding:30px;
    text-align:center;
    color:white;
    font-size:22px;
    text-decoration:none;
    border-radius:10px;
    }}

    .libre{{background:#27ae60}}
    .ocupada{{background:#e74c3c}}

    </style>

    <div class="grid">
    """

    for i in range(1,11):

        pedidos = db.query(PedidoDB).filter(
            PedidoDB.mesa==i,
            PedidoDB.cerrado==False
        ).all()

        total = sum(p.precio*p.cantidad for p in pedidos)

        estado = "ocupada" if pedidos else "libre"

        html += f"""
        <a class="mesa {estado}" href="/mesa/{i}">
        Mesa {i}<br>
        Total {MONEDA}{total}
        </a>
        """

    html += "</div>"

    db.close()

    return html

# ---------------- VER MESA ----------------

@app.get("/mesa/{numero}", response_class=HTMLResponse)
def mesa(numero:int):

    db = SessionLocal()

    platos = db.query(PlatoDB).all()

    pedidos = db.query(PedidoDB).filter(
        PedidoDB.mesa==numero,
        PedidoDB.cerrado==False
    ).all()

    total = sum(p.precio*p.cantidad for p in pedidos)

    html = f"""
    <h1>Mesa {numero}</h1>

    <a href="/dashboard">⬅ Volver</a>

    <h3>Agregar plato</h3>

    <form method="post" action="/agregar/{numero}">
    <select name="plato_id">
    """

    for p in platos:

        html += f"""
        <option value="{p.id}">
        {p.nombre} {MONEDA}{p.precio}
        </option>
        """

    html += """

    </select>

    Cantidad
    <input type="number" name="cantidad" value="1">

    Comentario
    <input name="comentario">

    <button>Agregar</button>

    </form>

    <hr>
    """

    for p in pedidos:

        subtotal = p.precio * p.cantidad

        html += f"""
        <p>

        {p.nombre} x{p.cantidad}
        {MONEDA}{subtotal}

        <a href="/sumar/{p.id}">➕</a>
        <a href="/restar/{p.id}">➖</a>
        <a href="/eliminar/{p.id}">❌</a>

        </p>
        """

    html += f"<h2>Total {MONEDA}{total}</h2>"

    html += f"""
    <form method="post" action="/cerrar/{numero}">

    <select name="metodo">
    <option>Efectivo</option>
    <option>Tarjeta</option>
    <option>Transferencia</option>
    </select>

    <button>Cerrar cuenta</button>

    </form>
    """

    db.close()

    return html

# ---------------- AGREGAR ----------------

@app.post("/agregar/{mesa}")
def agregar(mesa:int, plato_id:int=Form(...), cantidad:int=Form(...), comentario:str=Form("")):

    db = SessionLocal()

    plato = db.query(PlatoDB).filter(PlatoDB.id==plato_id).first()

    pedido = PedidoDB(
        mesa=mesa,
        nombre=plato.nombre,
        cantidad=cantidad,
        comentario=comentario,
        estado="pendiente",
        precio=plato.precio
    )

    db.add(pedido)

    db.commit()
    db.close()

    return RedirectResponse(f"/mesa/{mesa}",303)

# ---------------- SUMAR ----------------

@app.get("/sumar/{pedido_id}")
def sumar(pedido_id:int):

    db = SessionLocal()

    p = db.query(PedidoDB).get(pedido_id)

    mesa = p.mesa

    p.cantidad +=1

    db.commit()
    db.close()

    return RedirectResponse(f"/mesa/{mesa}",303)

# ---------------- RESTAR ----------------

@app.get("/restar/{pedido_id}")
def restar(pedido_id:int):

    db = SessionLocal()

    p = db.query(PedidoDB).get(pedido_id)

    mesa = p.mesa

    if p.cantidad>1:
        p.cantidad-=1
    else:
        db.delete(p)

    db.commit()
    db.close()

    return RedirectResponse(f"/mesa/{mesa}",303)

# ---------------- ELIMINAR ----------------

@app.get("/eliminar/{pedido_id}")
def eliminar(pedido_id:int):

    db = SessionLocal()

    p = db.query(PedidoDB).get(pedido_id)

    mesa = p.mesa

    db.delete(p)

    db.commit()
    db.close()

    return RedirectResponse(f"/mesa/{mesa}",303)

# ---------------- CERRAR MESA ----------------

@app.post("/cerrar/{mesa}")
def cerrar(mesa:int, metodo:str=Form(...)):

    db = SessionLocal()

    pedidos = db.query(PedidoDB).filter(
        PedidoDB.mesa==mesa,
        PedidoDB.cerrado==False
    ).all()

    total = sum(p.precio*p.cantidad for p in pedidos)

    venta = VentaDB(
        mesa=mesa,
        total=total,
        metodo_pago=metodo
    )

    db.add(venta)

    for p in pedidos:
        p.cerrado=True

    db.commit()

    venta_id = venta.id

    db.close()

    return RedirectResponse(f"/ticket/{venta_id}",303)

# ---------------- TICKET ----------------

@app.get("/ticket/{venta_id}", response_class=HTMLResponse)
def ticket(venta_id:int):

    db = SessionLocal()

    venta = db.query(VentaDB).get(venta_id)

    pedidos = db.query(PedidoDB).filter(
        PedidoDB.mesa==venta.mesa,
        PedidoDB.cerrado==True
    ).all()

    html = f"""
    <h2>{RESTAURANTE}</h2>

    Mesa {venta.mesa}

    <hr>
    """

    for p in pedidos:

        html += f"""
        {p.nombre} x{p.cantidad}
        {MONEDA}{p.precio*p.cantidad}<br>
        """

    html += f"""

    <hr>

    TOTAL {MONEDA}{venta.total}

    Pago: {venta.metodo_pago}

    <br><br>

    <button onclick="window.print()">🖨 Imprimir</button>

    <br><br>

    <a href="/dashboard">Volver</a>
    """

    db.close()

    return html

# ---------------- TOP PLATOS ----------------

@app.get("/admin/top", response_class=HTMLResponse)
def top():

    db = SessionLocal()

    pedidos = db.query(PedidoDB).filter(PedidoDB.cerrado==True).all()

    ranking = {}

    for p in pedidos:

        ranking[p.nombre] = ranking.get(p.nombre,0)+p.cantidad

    ranking = sorted(ranking.items(),key=lambda x:x[1],reverse=True)

    html="<h1>Platos más vendidos</h1>"

    for r in ranking:

        html+=f"{r[0]} {r[1]}<br>"

    html+='<br><a href="/dashboard">Volver</a>'

    db.close()

    return html

# ---------------- EXPORTAR EXCEL ----------------

@app.get("/admin/excel")
def excel():

    db = SessionLocal()

    ventas = db.query(VentaDB).all()
    pedidos = db.query(PedidoDB).all()

    ventas_data=[]
    platos_data=[]
    mesas_data=[]

    for v in ventas:

        ventas_data.append({
            "Mesa":v.mesa,
            "Total":v.total,
            "Metodo":v.metodo_pago,
            "Fecha":v.fecha
        })

    for p in pedidos:

        platos_data.append({
            "Plato":p.nombre,
            "Cantidad":p.cantidad
        })

        mesas_data.append({
            "Mesa":p.mesa,
            "Plato":p.nombre,
            "Cantidad":p.cantidad
        })

    df1=pd.DataFrame(ventas_data)
    df2=pd.DataFrame(platos_data).groupby("Plato").sum()
    df3=pd.DataFrame(mesas_data)

    archivo="reporte.xlsx"

    with pd.ExcelWriter(archivo) as writer:

        df1.to_excel(writer,sheet_name="Ventas",index=False)
        df2.to_excel(writer,sheet_name="Platos Vendidos")
        df3.to_excel(writer,sheet_name="Consumo por Mesa",index=False)

    db.close()

    return FileResponse(archivo,filename=archivo)