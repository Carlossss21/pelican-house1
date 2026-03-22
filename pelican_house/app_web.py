from flask import Flask, request, jsonify, render_template
import psycopg2
from datetime import date

app = Flask(__name__)

print("Pelican House LOCAL iniciado...")

# 🔌 CONEXIÓN LOCAL (TU PC)
conn = psycopg2.connect(
    "dbname=hotel_db user=postgres password=12345 host=localhost port=5432"
)
cursor = conn.cursor()

# 🏠 HOME
@app.route("/")
def home():
    return render_template("index.html")

# 🔍 DISPONIBLES
@app.route("/disponibles")
def disponibles():
    hoy = date.today()

    cursor.execute("""
    SELECT numero FROM habitaciones h
    WHERE NOT EXISTS (
        SELECT 1 FROM reservas r
        WHERE r.habitacion_id = h.id
        AND r.estado = 'confirmada'
        AND %s >= r.fecha_inicio
        AND %s < r.fecha_fin
    );
    """, (hoy, hoy))

    return jsonify([h[0] for h in cursor.fetchall()])

# 🏨 RESERVAR
@app.route("/reservar")
def reservar():
    numero = request.args.get("habitacion")
    cliente = request.args.get("cliente")
    inicio = request.args.get("inicio")
    fin = request.args.get("fin")

    try:
        cursor.execute("SELECT id FROM habitaciones WHERE numero = %s;", (numero,))
        resultado = cursor.fetchone()

        if not resultado:
            return "Habitación no existe ❌"

        habitacion_id = resultado[0]

        cursor.execute("""
        SELECT 1 FROM reservas
        WHERE habitacion_id = %s
        AND estado = 'confirmada'
        AND NOT (%s >= fecha_fin OR %s <= fecha_inicio)
        """, (habitacion_id, inicio, fin))

        if cursor.fetchone():
            return "Ya está reservada en esas fechas ❌"

        cursor.execute("""
        INSERT INTO reservas (habitacion_id, cliente, fecha_inicio, fecha_fin, estado)
        VALUES (%s, %s, %s, %s, 'confirmada');
        """, (habitacion_id, cliente, inicio, fin))

        conn.commit()
        return "Reserva creada ✅"

    except Exception as e:
        return f"Error: {e}"

# 📊 VER RESERVAS
@app.route("/reservas")
def ver_reservas():
    cursor.execute("""
    SELECT r.id, h.numero, r.cliente, r.fecha_inicio, r.fecha_fin
    FROM reservas r
    JOIN habitaciones h ON r.habitacion_id = h.id
    WHERE r.estado = 'confirmada'
    ORDER BY r.fecha_inicio;
    """)

    datos = cursor.fetchall()

    reservas = []
    for r in datos:
        reservas.append({
            "id": r[0],
            "habitacion": r[1],
            "cliente": r[2],
            "inicio": str(r[3]),
            "fin": str(r[4])
        })

    return jsonify(reservas)

# ❌ CANCELAR
@app.route("/cancelar")
def cancelar():
    reserva_id = request.args.get("id")

    try:
        cursor.execute("""
        UPDATE reservas
        SET estado = 'cancelada'
        WHERE id = %s;
        """, (reserva_id,))

        conn.commit()
        return "Reserva cancelada ✅"

    except Exception as e:
        return f"Error: {e}"

# ▶️ EJECUCIÓN LOCAL
if __name__ == "__main__":
    app.run(debug=True)