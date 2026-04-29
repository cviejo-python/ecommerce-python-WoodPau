from datetime import datetime
from sqlalchemy import Integer, Float, Boolean, ForeignKey, DateTime, String, Text, Table, Column
from sqlalchemy.orm import Mapped, relationship, mapped_column
from database import Base


# ===================== RELACIÓN N:N: Producto ↔ Categoria =====================
# Tabla intermedia para la relación muchos a muchos
producto_categoria = Table(
    "producto_categoria",
    Base.metadata,
    Column("producto_id", Integer, ForeignKey("productos.id_producto"), primary_key=True),
    Column("categoria_id", Integer, ForeignKey("categorias.id_categoria"), primary_key=True)
)


# ===================== CLASE USUARIO=====================
class Usuario(Base):
    __tablename__ = "usuarios"
    __table_args__ = {
        "sqlite_autoincrement": True,
        "comment" : "Tabla de usuarios"
    }
    # Mapeo por columnas
    id_usuario: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre_cliente: Mapped[str] = mapped_column(String(50), nullable=False)
    apellidos_cliente: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(50), nullable=False)
    telefono: Mapped[str] = mapped_column(String(20), nullable=False)
    es_admin: Mapped[bool] = mapped_column(Boolean, default=False)

    # ===== RELACIÓN 1:N CON DIRECCION =====
    direcciones: Mapped[list["Direccion"]] = relationship("Direccion", back_populates="usuario", cascade="all, delete-orphan")
    # ===== RELACIÓN 1:N CON PEDIDO=====
    pedidos: Mapped[list["Pedido"]] = relationship("Pedido", back_populates="usuario", cascade="all, delete-orphan")


    # ===== RELACIÓN N:N CON FAVORITOS =====
    favoritos: Mapped[list["Favorito"]] = relationship("Favorito",back_populates="usuario", cascade="all, delete-orphan")

    def __init__(self, nombre_cliente, apellidos_cliente, email, password, telefono, es_admin):
        self.nombre_cliente = nombre_cliente
        self.apellidos_cliente = apellidos_cliente
        self.email = email
        self.password = password
        self.telefono = telefono
        self.es_admin = es_admin

    def __repr__(self):
        return f"<Usuario:({self.nombre_cliente} Email:{self.email})>"

    def __str__(self):
        return f"<Usuario:({self.nombre_cliente} Email:{self.email})>"

# ===================== CLASE DIRECCION=====================
class Direccion(Base):
    __tablename__ = "direcciones"
    __table_args__ = {"sqlite_autoincrement": True, "comment" : "Tabla datos usuario"}

    # Mapeo por columnas

    id_direccion: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    calle: Mapped[str] = mapped_column(String(50), nullable=False)
    numero: Mapped[int] = mapped_column(String(10), nullable=False)
    ciudad: Mapped[str] = mapped_column(String(50), nullable=False)
    provincia: Mapped[str] = mapped_column(String(50), nullable=False)
    codigo_postal: Mapped[str] = mapped_column(String(10), nullable=False)
    pais: Mapped[str] = mapped_column(String(50), nullable=False)
    activa: Mapped[bool] = mapped_column(Boolean, default=True)

    # ===== FK → USUARIO =====
    usuario_id: Mapped[int] = mapped_column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)

    # Relaciones 1:N con USUARIO
    usuario: Mapped["Usuario"] = relationship("Usuario", back_populates="direcciones")

    # Relaciones 1:N con PEDIDO
    pedidos: Mapped[list["Pedido"]] = relationship("Pedido", back_populates="direccion")

    def __init__(self, calle, numero, ciudad, provincia, codigo_postal, pais, usuario_id, activa):
        self.calle = calle
        self.numero = numero
        self.ciudad = ciudad
        self.provincia = provincia
        self.codigo_postal = codigo_postal
        self.pais = pais
        self.usuario_id = usuario_id
        self.activa = activa

    def __repr__(self):
        return f"<Direccion({self.calle}, {self.numero} {self.ciudad})>"

    def __str__(self):
        return f"<Direccion({self.calle}, {self.numero} {self.ciudad})>"

# ===================== CLASE PRODUCTO=====================
class Producto(Base):
    __tablename__ = "productos"
    __table_args__ = {
        "sqlite_autoincrement": True,
        "comment" : "Tabla de productos"
    }

    # Mapeo por columnas

    id_producto: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre_producto: Mapped[str] = mapped_column(String(50),nullable=False)
    descripcion: Mapped[str] = mapped_column(String(350), nullable=False)
    precio: Mapped[float] = mapped_column(Float, nullable=False)
    stock: Mapped[int] = mapped_column(Integer, nullable=False)
    # Medidas en centímetros
    altura: Mapped[float] = mapped_column(Float, nullable=False)
    ancho: Mapped[float] = mapped_column(Float, nullable=False)
    fondo: Mapped[float] = mapped_column(Float, nullable=False)

    # ===== RELACIÓN 1:N CON IMAGENPRODUCTO=====
    imagenes: Mapped[list["ImagenProducto"]] = relationship("ImagenProducto", back_populates="producto", cascade="all, delete-orphan",lazy="selectin")

    # ===== RELACIÓN N:N CON CATEGORIA=====
    categorias: Mapped[list["Categoria"]] = relationship("Categoria", secondary=producto_categoria, back_populates="productos", lazy="selectin")

    # ===== RELACIÓN N:N CON FAVORITOS =====
    favoritos: Mapped[list["Favorito"]] = relationship("Favorito", back_populates="producto", cascade="all, delete-orphan")

    # ===== RELACIÓN 1:N CON LINEAS DE PEDIDO =====
    lineas_pedido: Mapped[list["LineaPedido"]] = relationship("LineaPedido", back_populates="producto", cascade="all, delete-orphan")

    def __init__(self, nombre_producto, descripcion, precio, stock, altura, ancho, fondo):
        self.nombre_producto = nombre_producto
        self.descripcion = descripcion
        self.precio = precio
        self.stock = stock
        self.altura = altura
        self.ancho = ancho
        self.fondo = fondo

    def __repr__(self):
        return f"<Producto({self.id_producto}, {self.precio}, {self.descripcion})>"
    def __str__(self):
        return f"<Producto({self.id_producto}, {self.precio}, {self.descripcion})>"

# ===================== CLASE IMAGEN PRODUCTO=====================
class ImagenProducto(Base):
    __tablename__ = "imagenes_productos"
    __table_args__ = {
        "sqlite_autoincrement": True,
        "comment" : "Tabla de imagenes productos"
    }

    id_imagen: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ruta_imagen: Mapped[str] = mapped_column(String(255), nullable=False)
    es_principal: Mapped[bool] = mapped_column(Boolean, nullable=False)

    # ===== FK → PRODUCTO =====
    producto_id: Mapped[int] = mapped_column(Integer, ForeignKey("productos.id_producto"), nullable=False)

    # Relaciones 1:N con Producto
    producto: Mapped["Producto"] = relationship("Producto", back_populates="imagenes")

    def __init__(self, producto_id, ruta_imagen, es_principal):
        self.producto_id = producto_id
        self.ruta_imagen = ruta_imagen
        self.es_principal = es_principal

    def __repr__(self):
        return f"Ruta({self.id_imagen}, {self.ruta_imagen})"
    def __str__(self):
        return f"<Ruta({self.id_imagen}, {self.ruta_imagen})>"

# ===================== CLASE CATEGORIA=====================
class Categoria(Base):
    __tablename__ = "categorias"
    __table_args__ = {
        "sqlite_autoincrement": True,
        "comment" : "Tabla de categoria productos"
    }


    # Mapeo por columnas
    id_categoria: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre_categoria: Mapped[str] = mapped_column(String(255), nullable=False)

    # ===== RELACIÓN N:N CON PRODUCTO =====
    productos: Mapped[list["Producto"]] = relationship("Producto", secondary=producto_categoria, back_populates="categorias", lazy="selectin")

    def __init__(self, nombre_categoria):
        self.nombre_categoria = nombre_categoria

    def __repr__(self):
        return  f"Categoria: {self.id_categoria}"
    def __str__(self):
        return f"<Categoria({self.id_categoria})>"



# ===================== CLASE PEDIDO =====================
class Pedido(Base):
    __tablename__ = "pedidos"
    __table_args__ = {
        "sqlite_autoincrement": True,
        "comment": "Pedido usuario con uno o varios productos"
    }

    # Mapeo por columnas
    id_pedido: Mapped[int] = mapped_column(Integer, primary_key=True)
    total: Mapped[float] = mapped_column(Float, nullable=False)
    estado: Mapped[str] = mapped_column(String(20), default="pagado")
    fecha: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # ===== FK → USUARIO =====
    usuario_id: Mapped[int] = mapped_column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)

    # ===== FK → DIRECCION =====
    direccion_id: Mapped[int] = mapped_column(ForeignKey("direcciones.id_direccion"), nullable=False)


    # Relaciones N:1 con Usuario
    usuario: Mapped["Usuario"] = relationship("Usuario", back_populates="pedidos")

    # Relaciones 1:N con Linea Pedido
    lineas: Mapped[list["LineaPedido"]] = relationship("LineaPedido", back_populates="pedido", cascade="all, delete-orphan")

    # Relaciones N:1 con DIRECCION
    direccion: Mapped["Direccion"] = relationship("Direccion")

    def __init__(self, total, usuario_id, estado="pagado", direccion_id=None):
        self.total = total
        self.usuario_id = usuario_id
        self.estado = estado
        self.direccion_id = direccion_id

    def __repr__(self):
        return (
            f"Pedido de {self.id_pedido} "
            f"({self.usuario_id})"
            f"({self.estado})"
        )
    def __str__(self):
        return (
            f"Pedido de {self.id_pedido} "
            f"({self.usuario_id})"
            f"({self.estado})"
        )


# ===================== CLASE LINEA PEDIDO =====================
class LineaPedido(Base):
    __tablename__ = "lineas_pedido"
    __table_args__ = {
        "sqlite_autoincrement": True,
        "comment": "Cada producto dentro de un pedido"
    }


    # Mapeo por columnas
    
    id_linea_pedido: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre_producto: Mapped[str] = mapped_column(String(150))
    precio_unitario: Mapped[float] = mapped_column(Float)
    cantidad: Mapped[int] = mapped_column(Integer)

    # ===== FK → PEDIDO =====
    pedido_id: Mapped[int] = mapped_column( Integer, ForeignKey("pedidos.id_pedido"), nullable=False)

    # ===== FK → PRODUCTO =====
    producto_id: Mapped[int] = mapped_column(Integer, ForeignKey("productos.id_producto"), nullable=False)


    # ===== RELACIÓN N:1 CON PEDIDO =====
    pedido: Mapped["Pedido"] = relationship("Pedido", back_populates="lineas")

    # ===== RELACIÓN N:1 CON PRODUCTO =====
    producto: Mapped["Producto"] = relationship("Producto", back_populates="lineas_pedido")

    def __init__(self, nombre_producto, precio_unitario, cantidad, pedido_id, producto_id):
        self.nombre_producto = nombre_producto
        self.precio_unitario = precio_unitario
        self.cantidad = cantidad
        self.pedido_id = pedido_id
        self.producto_id = producto_id

    def __repr__(self):
        return (
            f"<LineaPedido id={self.id_linea_pedido} "
            f"pedido_id={self.pedido_id} "
            f"producto_id={self.producto_id} "
            f"cantidad={self.cantidad}>"
        )

    def __str__(self):
        return (f"LineaPedido de {self.id_linea_pedido} "
                f"({self.pedido_id})"
                f"({self.producto_id})"
                f"({self.cantidad})"
                f"({self.pedido})"
                f"({self.producto})"
                )




# ===================== CLASE FAVORITO=====================
class Favorito(Base):

    __tablename__ = "favoritos"
    __table_args__ = {
        "sqlite_autoincrement": True,
        "comment": "Tabla de productos favoritos"
    }

    # Mapeo por columnas
    id_favorito: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # ===== FK → USUARIO =====
    id_usuario: Mapped[int] = mapped_column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)

    # ===== FK → PRODUCTO =====
    producto_id: Mapped[int] = mapped_column(Integer, ForeignKey("productos.id_producto"), nullable=False)

    # Relaciones N:N con Usuario
    usuario: Mapped["Usuario"] = relationship("Usuario", back_populates="favoritos")
    # Relaciones 1:N con Producto
    producto: Mapped["Producto"] = relationship("Producto", back_populates="favoritos")


    def __repr__(self):
        return f"<Favorito({self.id_favorito})>"

    def __str__(self):
        return f"<Favorito({self.id_favorito})>"



# ===================== CLASE MENSAJE CONTACTO =====================
class MensajeContacto(Base):
    __tablename__ = "mensajes_contacto"
    __table_args__ = {
        "sqlite_autoincrement": True,
        "comment": "Mensajes enviados desde el formulario de contacto"
    }

    id_mensaje: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(150), nullable=False)
    telefono: Mapped[str] = mapped_column(String(20), nullable=True)
    mensaje: Mapped[str] = mapped_column(Text, nullable=False)
    estado: Mapped[str] = mapped_column(String(20), default="pendiente")
    fecha_envio: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    def __init__(self, nombre, email, mensaje, telefono=None):
        self.nombre = nombre
        self.email = email
        self.telefono = telefono
        self.mensaje = mensaje

    def __repr__(self):
        return f"<MensajeContacto({self.nombre}, {self.email})>"