import os
os.environ["PGCLIENTENCODING"] = "UTF8"

import psycopg2
from datetime import date

print("ZAI PRO iniciado...")

# 🔌 Conexión
conn = psycopg2.connect(
    "dbname=hotel_db user=postgres password=12345 host=localhost port=5432"
)

cursor = conn.cursor()

# 🔍 Ver disponibilidad con fechas
def habitaciones_disponibles():
    hoy = date.today()

    query = """
    SELECT numero FROM habitaciones h
    WHERE NOT EXISTS (
        SELECT 1 FROM reservas r
        WHERE r.habitacion_id = h.id
        AND r.estado = 'confirmada'
        AND %s BETWEEN r.fecha_inicio AND r.fecha_fin
    );
    """

    cursor.execute(query, (hoy,))
    return cursor.fetchall()

# 🏨 Crear reserva PRO
def crear_reserva(habitacion_numero, cliente, inicio, fin):
    cursor.execute(
        "SELECT id FROM habitaciones WHERE numero = %s;",
        (habitacion_numero,)
    )
    resultado = cursor.fetchone()

    if resultado is None:
        print("ZAI: Habitación no existe")
        return

    habitacion_id = resultado[0]

    # Validar conflicto de fechas
    cursor.execute("""
        SELECT 1 FROM reservas
        WHERE habitacion_id = %s
        AND estado = 'confirmada'
        AND NOT (%s >= fecha_fin OR %s <= fecha_inicio)
    """, (habitacion_id, inicio, fin))

    conflicto = cursor.fetchone()

    if conflicto:
        print("ZAI: Esa habitación ya está reservada en esas fechas")
        return

    # Crear reserva
    cursor.execute("""
        INSERT INTO reservas (habitacion_id, cliente, fecha_inicio, fecha_fin, estado)
        VALUES (%s, %s, %s, %s, 'confirmada');
    """, (habitacion_id, cliente, inicio, fin))

    conn.commit()

    print(f"ZAI: Reserva creada para {cliente} en habitación {habitacion_numero}")

# 🤖 CHAT ZAI
while True:
    pregunta = input("Tú: ").lower()

    if pregunta == "salir":
        print("ZAI: Hasta luego 👋")
        break

    # 🔍 Disponibilidad
    elif any(p in pregunta for p in ["habitaciones", "cuartos", "disponibles", "libres"]):
        disponibles = habitaciones_disponibles()

        if disponibles:
            print("ZAI: Habitaciones disponibles hoy:")
            for hab in disponibles:
                print("-", hab[0])
        else:
            print("ZAI: No hay habitaciones disponibles")

    # 🏨 Reservar PRO
    elif "reservar" in pregunta:
        partes = pregunta.split()

        try:
            numero = partes[1]
            cliente = partes[2]
            inicio = partes[3]
            fin = partes[4]

            crear_reserva(numero, cliente, inicio, fin)

        except:
            print("ZAI: Usa este formato:")
            print("reservar 02 Carlos 2026-03-25 2026-03-27")

    else:
        print("ZAI: No entendí")

# 🔒 Cerrar conexión
conn.close()