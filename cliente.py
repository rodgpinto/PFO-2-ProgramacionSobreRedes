"""Cliente de consola para la API de tareas (usa requests.Session para conservar la cookie de sesión)."""
import os
import re

import requests

# Local por defecto; para la API desplegada: set API_URL=https://tu-app.onrender.com
URL = os.environ.get("API_URL", "http://127.0.0.1:5000")
s = requests.Session()


def pedir_credenciales():
    return {"usuario": input("Usuario: ").strip(), "contraseña": input("Contraseña: ")}


def mostrar(resp):
    try:
        print(f"[{resp.status_code}]", resp.json())
    except ValueError:
        texto = re.sub(r"<[^>]+>", " ", resp.text)  # quitar etiquetas HTML
        print(f"[{resp.status_code}]", " ".join(texto.split()))


def main():
    while True:
        print("\n1) Registrarse  2) Iniciar sesión  3) Ver tareas  4) Cerrar sesión  5) Salir")
        op = input("Opción: ").strip()
        try:
            if op == "1":
                mostrar(s.post(f"{URL}/registro", json=pedir_credenciales()))
            elif op == "2":
                mostrar(s.post(f"{URL}/login", json=pedir_credenciales()))
            elif op == "3":
                mostrar(s.get(f"{URL}/tareas"))
            elif op == "4":
                mostrar(s.post(f"{URL}/logout"))
            elif op == "5":
                break
            else:
                print("Opción inválida")
        except requests.ConnectionError:
            print("No se pudo conectar. ¿Está corriendo servidor.py?")


if __name__ == "__main__":
    main()