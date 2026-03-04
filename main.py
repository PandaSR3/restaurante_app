from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse

app = FastAPI()

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
    html = "<h1>Vista Cocina 👩‍🍳</h1><br>"
    
    for i, pedido in enumerate(pedidos_cocina):
        color = "orange" if pedido["estado"] == "Pendiente" else "green"
        
        html += f"""
        <div style='border:1px solid black;margin:10px;padding:10px;'>
            <h3>Mesa {pedido['mesa']}</h3>
            <p>{pedido['nombre']} x{pedido['cantidad']}</p>
            <p>Comentario: {pedido['comentario']}</p>
            <p>Estado: <b style='color:{color}'>{pedido['estado']}</b></p>
            <form method='post' action='/cambiar_estado_cocina/{i}'>
                <button type='submit'>Marcar como Listo</button>
            </form>
        </div>
        """
    
    html += "<br><a href='/'>Volver</a>"
    return html

@app.post("/cambiar_estado_cocina/{index}")
def cambiar_estado_cocina(index: int):
    pedidos_cocina[index]["estado"] = "Listo"
    return RedirectResponse(url="/cocina", status_code=303)