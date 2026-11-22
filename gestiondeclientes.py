"""
Sistema Integral de Gestión de Clientes, Servicios y Reservas 
"""

import logging
import re
from abc import ABC, abstractmethod

#  LOGS
logging.basicConfig(
    filename="software_fj.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    encoding="utf-8",
)
log = logging.getLogger("SoftwareFJ")


#  EXCEPCIONES PROPIAS
class ErrorSistema(Exception):
    """Excepción base del sistema."""


class ClienteInvalidoError(ErrorSistema):
    """Datos de cliente inválidos."""


class ServicioInvalidoError(ErrorSistema):
    """Parámetros de servicio inválidos."""


class ServicioNoDisponibleError(ErrorSistema):
    """El servicio no está disponible."""


class ReservaInvalidaError(ErrorSistema):
    """Operación de reserva no permitida."""


class CalculoInconsistenteError(ErrorSistema):
    """Cálculo de costos con valores inconsistentes."""


#  CLASE ABSTRACTA
class Entidad(ABC):
    """Representa cualquier entidad general del sistema."""

    def __init__(self, id_entidad):
        self._id = id_entidad

    @property
    def id(self):
        return self._id

    @abstractmethod
    def mostrar_info(self):
        pass

    def __str__(self):
        return self.mostrar_info()


#  CLIENTE
class Cliente(Entidad):
    def __init__(self, id_cliente, nombre, correo, telefono):
        super().__init__(id_cliente)
        self.nombre = nombre      # usa los setters con validación
        self.correo = correo
        self.telefono = telefono

    @property
    def nombre(self):
        return self._nombre

    @nombre.setter
    def nombre(self, valor):
        if not isinstance(valor, str) or len(valor.strip()) < 3:
            raise ClienteInvalidoError("El nombre debe tener al menos 3 caracteres.")
        self._nombre = valor.strip()

    @property
    def correo(self):
        return self._correo

    @correo.setter
    def correo(self, valor):
        if not isinstance(valor, str) or not re.match(r"^[\w.+-]+@[\w-]+\.[\w.]+$", valor):
            raise ClienteInvalidoError(f"Correo inválido: {valor}")
        self._correo = valor

    @property
    def telefono(self):
        return self._telefono

    @telefono.setter
    def telefono(self, valor):
        if not isinstance(valor, str) or not valor.isdigit() or len(valor) != 10:
            raise ClienteInvalidoError(f"Teléfono inválido (deben ser 10 dígitos): {valor}")
        self._telefono = valor

    def mostrar_info(self):
        return f"Cliente #{self.id}: {self.nombre} | {self.correo} | {self.telefono}"


#  SERVICIOS
class Servicio(Entidad, ABC):
    def __init__(self, id_servicio, nombre, tarifa_hora):
        super().__init__(id_servicio)
        if not isinstance(nombre, str) or not nombre.strip():
            raise ServicioInvalidoError("El servicio requiere un nombre.")
        if not isinstance(tarifa_hora, (int, float)) or tarifa_hora <= 0:
            raise ServicioInvalidoError("La tarifa por hora debe ser un número mayor a 0.")
        self._nombre = nombre
        self._tarifa_hora = tarifa_hora
        self._disponible = True

    @property
    def nombre(self):
        return self._nombre

    @property
    def disponible(self):
        return self._disponible

    @disponible.setter
    def disponible(self, valor):
        self._disponible = bool(valor)

    @abstractmethod
    def calcular_costo(self, horas, impuesto=0.0, descuento=0.0):
        """Método sobrecargado mediante parámetros opcionales:
        calcular_costo(h) / calcular_costo(h, impuesto) / calcular_costo(h, impuesto, descuento)
        """

    @abstractmethod
    def describir(self):
        pass

    @abstractmethod
    def validar_parametros(self, horas):
        pass

    def _aplicar_extras(self, subtotal, impuesto, descuento):
        if not (0 <= impuesto <= 1) or not (0 <= descuento <= 1):
            raise CalculoInconsistenteError("Impuesto y descuento deben estar entre 0 y 1.")
        total = subtotal * (1 - descuento) * (1 + impuesto)
        if total < 0:
            raise CalculoInconsistenteError("El costo calculado es negativo.")
        return round(total, 2)

    def mostrar_info(self):
        return self.describir()


class ReservaSala(Servicio):
    def __init__(self, id_servicio, nombre, tarifa_hora, capacidad):
        super().__init__(id_servicio, nombre, tarifa_hora)
        if not isinstance(capacidad, int) or capacidad <= 0:
            raise ServicioInvalidoError("La capacidad de la sala debe ser un entero positivo.")
        self._capacidad = capacidad

    def validar_parametros(self, horas):
        if not isinstance(horas, (int, float)) or not (1 <= horas <= 8):
            raise ServicioInvalidoError("Una sala se reserva entre 1 y 8 horas.")

    def calcular_costo(self, horas, impuesto=0.0, descuento=0.0):
        self.validar_parametros(horas)
        subtotal = self._tarifa_hora * horas + 20000  # cargo fijo de limpieza
        return self._aplicar_extras(subtotal, impuesto, descuento)

    def describir(self):
        return f"Sala '{self._nombre}' (capacidad {self._capacidad}) - ${self._tarifa_hora}/h"


class AlquilerEquipo(Servicio):
    def __init__(self, id_servicio, nombre, tarifa_hora, tipo_equipo):
        super().__init__(id_servicio, nombre, tarifa_hora)
        if not tipo_equipo or not isinstance(tipo_equipo, str):
            raise ServicioInvalidoError("Debe indicar el tipo de equipo.")
        self._tipo_equipo = tipo_equipo

    def validar_parametros(self, horas):
        if not isinstance(horas, (int, float)) or not (1 <= horas <= 72):
            raise ServicioInvalidoError("Un equipo se alquila entre 1 y 72 horas.")

    def calcular_costo(self, horas, impuesto=0.0, descuento=0.0):
        self.validar_parametros(horas)
        subtotal = self._tarifa_hora * horas * 1.05  # 5% de seguro
        return self._aplicar_extras(subtotal, impuesto, descuento)

    def describir(self):
        return f"Equipo '{self._nombre}' ({self._tipo_equipo}) - ${self._tarifa_hora}/h + 5% seguro"


class Asesoria(Servicio):
    NIVELES = {"junior": 1.0, "senior": 1.5, "experto": 2.0}

    def __init__(self, id_servicio, nombre, tarifa_hora, nivel):
        super().__init__(id_servicio, nombre, tarifa_hora)
        if nivel not in self.NIVELES:
            raise ServicioInvalidoError(f"Nivel inválido: {nivel}. Use {list(self.NIVELES)}")
        self._nivel = nivel

    def validar_parametros(self, horas):
        if not isinstance(horas, (int, float)) or not (0.5 <= horas <= 6):
            raise ServicioInvalidoError("Una asesoría dura entre 0.5 y 6 horas.")

    def calcular_costo(self, horas, impuesto=0.0, descuento=0.0):
        self.validar_parametros(horas)
        subtotal = self._tarifa_hora * horas * self.NIVELES[self._nivel]
        return self._aplicar_extras(subtotal, impuesto, descuento)

    def describir(self):
        return f"Asesoría '{self._nombre}' nivel {self._nivel} - ${self._tarifa_hora}/h"


# RESERVA
class Reserva(Entidad):
    PENDIENTE, CONFIRMADA, CANCELADA = "PENDIENTE", "CONFIRMADA", "CANCELADA"

    def __init__(self, id_reserva, cliente, servicio, horas):
        super().__init__(id_reserva)
        if not isinstance(cliente, Cliente):
            raise ReservaInvalidaError("La reserva requiere un cliente válido.")
        if not isinstance(servicio, Servicio):
            raise ReservaInvalidaError("La reserva requiere un servicio válido.")
        self._cliente = cliente
        self._servicio = servicio
        self._horas = horas
        self._estado = self.PENDIENTE

    @property
    def estado(self):
        return self._estado

    def confirmar(self):
        if self._estado != self.PENDIENTE:
            raise ReservaInvalidaError(f"No se puede confirmar una reserva {self._estado}.")
        if not self._servicio.disponible:
            raise ServicioNoDisponibleError(f"El servicio '{self._servicio.nombre}' no está disponible.")
        self._estado = self.CONFIRMADA

    def cancelar(self):
        if self._estado == self.CANCELADA:
            raise ReservaInvalidaError("La reserva ya estaba cancelada.")
        self._estado = self.CANCELADA

    def procesar(self, impuesto=0.19, descuento=0.0):
        """Valida, calcula el costo y confirma, usando try/except/else/finally."""
        try:
            costo = self._servicio.calcular_costo(self._horas, impuesto, descuento)
            self.confirmar()
        except ServicioInvalidoError as e:
            # Encadenamiento de excepciones
            raise ReservaInvalidaError(f"Reserva {self.id} rechazada por parámetros inválidos") from e
        else:
            log.info("Reserva %s confirmada. Costo total: $%s", self.id, costo)
            return costo
        finally:
            log.info("Procesamiento de la reserva %s finalizado (estado: %s)", self.id, self._estado)

    def mostrar_info(self):
        return (f"Reserva #{self.id} | {self._cliente.nombre} | "
                f"{self._servicio.nombre} | {self._horas}h | {self._estado}")


# SIMULACIÓN
def ejecutar(descripcion, accion):
    """Ejecuta una operación; si falla, registra el error y el programa continúa."""
    print(f"\n>> {descripcion}")
    try:
        resultado = accion()
    except ErrorSistema as e:
        causa = f" | causa: {e.__cause__}" if e.__cause__ else ""
        print(f"   [ERROR CONTROLADO] {e}{causa}")
        log.error("%s -> %s%s", descripcion, e, causa)
    except Exception as e:  # cualquier error inesperado tampoco detiene el sistema
        print(f"   [ERROR INESPERADO] {e}")
        log.critical("%s -> error inesperado: %r", descripcion, e)
    else:
        print(f"   [OK] {resultado}")
        log.info("%s -> OK", descripcion)
        return resultado
    return None


def main():
    log.info("===== INICIO DE LA SIMULACIÓN =====")
    clientes, servicios, reservas = [], [], []

    # 1-3: Clientes
    c1 = ejecutar("1. Registrar cliente válido",
                  lambda: Cliente(1, "Daniel Moreno", "danielmoreno200410@gmail.com", "3148561626"))
    c2 = ejecutar("2. Registrar cliente con correo inválido",
                  lambda: Cliente(2, "Andres Merchan", "Andres@gamil", "3109876543"))
    c3 = ejecutar("3. Registrar cliente con teléfono inválido",
                  lambda: Cliente(3, "Marta Ruiz", "marta@gmail", "123"))
    clientes.extend(c for c in (c1, c2, c3) if c)

    # 4-6: Servicios
    s1 = ejecutar("4. Crear sala válida",
                  lambda: ReservaSala(1, "Sala Ejecutiva", 50000, 10))
    s2 = ejecutar("5. Crear equipo con tarifa inválida",
                  lambda: AlquilerEquipo(2, "Portátil", -100, "Computador"))
    s3 = ejecutar("6. Crear asesoría válida",
                  lambda: Asesoria(3, "Asesoría en Python", 80000, "senior"))
    s4 = ejecutar("7. Crear equipo válido",
                  lambda: AlquilerEquipo(4, "Proyector", 15000, "Video"))
    servicios.extend(s for s in (s1, s2, s3, s4) if s)

    # 8-12: Reservas
    r1 = ejecutar("8. Reserva exitosa de sala (2h)",
                  lambda: Reserva(1, c1, s1, 2))
    if r1:
        ejecutar("   Procesar reserva 1 (impuesto 19%)", lambda: f"Costo: ${r1.procesar()}")
        reservas.append(r1)

    r2 = ejecutar("9. Reserva de asesoría con 10h (fuera de rango)",
                  lambda: Reserva(2, c1, s3, 10))
    if r2:
        ejecutar("   Procesar reserva 2", lambda: r2.procesar())
        reservas.append(r2)

    ejecutar("10. Reserva sin cliente (None)", lambda: Reserva(3, None, s1, 2))

    if s4:
        s4.disponible = False
    r4 = ejecutar("11. Reserva de equipo NO disponible",
                  lambda: Reserva(4, c1, s4, 5))
    if r4:
        ejecutar("   Procesar reserva 4", lambda: r4.procesar())
        reservas.append(r4)

    if r1:
        ejecutar("12. Cancelar reserva 1 dos veces",
                 lambda: (r1.cancelar(), r1.cancelar()))

    ejecutar("13. Costo con descuento inválido (150%)",
             lambda: s3.calcular_costo(2, 0.19, 1.5))
    ejecutar("14. Costo sobrecargado: solo horas / con impuesto / con descuento",
             lambda: (s3.calcular_costo(2), s3.calcular_costo(2, 0.19), s3.calcular_costo(2, 0.19, 0.10)))

    # Polimorfismo: mismo método,  pero distinto comportamiento
    print("\n--- Servicios (polimorfismo) ---")
    for s in servicios:
        print(" ", s.describir())

    print("\n--- Reservas registradas ---")
    for r in reservas:
        print(" ", r.mostrar_info())

    print("\nSimulación terminada. Revise 'software_fj.log' para ver los eventos y errores.")
    log.info("===== FIN DE LA SIMULACIÓN =====")



main()