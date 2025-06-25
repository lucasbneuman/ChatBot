# 1. Definición de la Clase
class Coche:
    # Método constructor (se llama automáticamente al crear un nuevo objeto)
    # 'self' se refiere a la instancia del objeto que se está creando
    def __init__(self, marca, modelo, color):
        self.marca = marca      # Atributo de instancia
        self.modelo = modelo    # Atributo de instancia
        self.color = color      # Atributo de instancia
        self.velocidad = 0      # Atributo con valor inicial

    # Método para acelerar
    def acelerar(self, incremento):
        self.velocidad += incremento
        print(f"El {self.marca} {self.modelo} ha acelerado a {self.velocidad} km/h.")

    # Método para frenar
    def frenar(self, decremento):
        self.velocidad -= decremento
        if self.velocidad < 0:
            self.velocidad = 0
        print(f"El {self.marca} {self.modelo} ha frenado a {self.velocidad} km/h.")

    # Método para obtener la información del coche
    def obtener_info(self):
        return f"Marca: {self.marca}, Modelo: {self.modelo}, Color: {self.color}, Velocidad: {self.velocidad} km/h"

# 2. Creación de Objetos (Instancias de la Clase Coche)

# Creamos el primer coche
coche1 = Coche("Toyota", "Corolla", "Rojo")
print(f"Coche 1 creado: {coche1.obtener_info()}")

# Creamos el segundo coche
coche2 = Coche("Ford", "Focus", "Azul")
print(f"Coche 2 creado: {coche2.obtener_info()}")

# 3. Interacción con los Objetos (Llamada a Métodos y Acceso a Atributos)

print("\n--- Interacciones con Coche 1 ---")
coche1.acelerar(50)
coche1.acelerar(30)
print(f"Velocidad actual de Coche 1: {coche1.velocidad} km/h")
coche1.frenar(20)
print(f"Velocidad actual de Coche 1: {coche1.velocidad} km/h")
print(f"Coche 1 final: {coche1.obtener_info()}")


print("\n--- Interacciones con Coche 2 ---")
coche2.acelerar(70)
print(f"Velocidad actual de Coche 2: {coche2.velocidad} km/h")
# Podemos cambiar un atributo directamente si es necesario
coche2.color = "Verde"
print(f"Nuevo color de Coche 2: {coche2.color}")
print(f"Coche 2 final: {coche2.obtener_info()}")