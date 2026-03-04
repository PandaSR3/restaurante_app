from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse

app = FastAPI()

# Simulación simple de 10 mesas
mesas = {i: "Libre" for i in range(1, 11)}

@app.get("/", response_class=HTMLResponse)
def home():
    html = "<h1>Mesas Restaurante 🍽️</h1><br>"
    
    for numero, estado in mesas.items():
        color = "green" if estado == "Libre" else "red"
        
        html += f"""
        <div style='margin:10px; padding:10px; border:1px solid black;'>
            <h3>Mesa {numero}</h3>
            <p>Estado: <b style='color:{color}'>{estado}</b></p>
            <form method='post' action='/cambiar_estado/{numero}'>
                <button type='submit'>Cambiar Estado</button>
            </form>
        </div>
        """
    
    return html

@app.post("/cambiar_estado/{numero}")
def cambiar_estado(numero: int):
    if mesas[numero] == "Libre":
        mesas[numero] = "Ocupada"
    else:
        mesas[numero] = "Libre"
    
    return """
    <script>
        window.location.href = "/";
    </script>
    """