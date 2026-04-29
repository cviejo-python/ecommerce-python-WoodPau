# PROYECTO FINAL CURSO PYTHON
from flask import Flask, render_template, request, redirect, url_for, session, abort
from sqlalchemy import or_
from sqlalchemy.orm import selectinload
from functools import wraps
from database import engine, Base, SessionLocal
from models import Usuario, Direccion, Producto, Categoria, ImagenProducto, Favorito, Pedido, LineaPedido, MensajeContacto
import os
from werkzeug.utils import secure_filename
app = Flask(__name__) # En app se encuentra nuestro servidor web de Flask
app.secret_key = "woodpau_secret_key" #Eso sirve para la seguridad interna de una app Flask


#Funcion para obtener el nombre de usario sabiendo el id
def obtener_usuario_por_id(user_id):
    return db.get(Usuario, user_id)

# Buscamos en la sesión si existe un usuario logueado
@app.context_processor
def inject_usuario():
    usuario = None

    user_id = session.get("usuario_id")
    if user_id:
        usuario = obtener_usuario_por_id(user_id)

    return dict(usuario=usuario)


# Funcion que comprueba si el usuario está logueado y si tiene permisos de administrador
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):

        if "usuario_id" not in session:
            return redirect(url_for("login"))

        db = SessionLocal()
        usuario = db.get(Usuario, session["usuario_id"])
        db.close()

        if not usuario or not usuario.es_admin:
            abort(403)

        return f(*args, **kwargs)

    return decorated_function

# Consultamos los mensajes pendientes que tiene el usuario aministrador
@app.route("/admin")
@admin_required
def admin_panel():

    db = SessionLocal()
    mensajes_pendientes = db.query(MensajeContacto)\
        .filter(MensajeContacto.estado == "pendiente")\
        .count()
    db.close()
    # Con esto mostramos los mensajes de usuarios enviados desde la web que tenemos pendientes de ver
    return render_template("admin/dashboard.html", mensajes_pendientes=mensajes_pendientes)

#solo para el usuario administrador, se consultan todos los productos existentes
@app.route("/admin/productos")
@admin_required
def admin_productos():
    db = SessionLocal()
    productos = db.query(Producto).all()
    db.close()
    return render_template("admin/productos.html", productos=productos)

#solo para el usuario administrador, se consultan todas las categorias existentes
@app.route("/admin/categorias")
@admin_required
def admin_categorias():

    db = SessionLocal()
    categorias = db.query(Categoria).all()
    db.close()

    return render_template(
        "admin/categorias.html",
        categorias=categorias
    )

#solo para el usuario administrador, se crea una categoria nueva
@app.route("/admin/categorias/nueva", methods=["GET", "POST"])
@admin_required
def admin_nueva_categoria():

    db = SessionLocal()

    if request.method == "POST":

        nombre = request.form["nombre_categoria"].strip()

        # Evitar duplicados
        existente = db.query(Categoria)\
            .filter(Categoria.nombre_categoria == nombre)\
            .first()

        if existente:
            db.close()
            return "La categoría ya existe"

        nueva = Categoria(nombre_categoria=nombre)
        db.add(nueva)
        db.commit()
        db.close()

        return redirect(url_for("admin_categorias"))

    db.close()
    return render_template("admin/nueva_categoria.html")

#solo para el usuario administrador, con esta funcion editamos una categoria existente
@app.route("/admin/categorias/editar/<int:id>", methods=["GET", "POST"])
@admin_required
def admin_editar_categoria(id):

    db = SessionLocal()
    categoria = db.get(Categoria, id)

    if not categoria:
        db.close()
        return "Categoría no encontrada", 404

    if request.method == "POST":

        nuevo_nombre = request.form["nombre_categoria"].strip()

        categoria.nombre_categoria = nuevo_nombre
        db.commit()
        db.close()

        return redirect(url_for("admin_categorias"))

    return render_template(
        "admin/editar_categoria.html",
        categoria=categoria
    )

#solo para el usuario administrador, con esta funcion eliminamos una categoria existente
@app.route("/admin/categorias/eliminar/<int:id>")
@admin_required
def admin_eliminar_categoria(id):

    db = SessionLocal()
    categoria = db.get(Categoria, id)

    if not categoria:
        db.close()
        return "Categoría no encontrada", 404

    # aqui nos aseguramos que la categoria no tiene productos asociado y no la podemos eliminar
    if categoria.productos:
        db.close()
        return "No puedes eliminar una categoría con productos asociados"

    db.delete(categoria)
    db.commit()
    db.close()

    return redirect(url_for("admin_categorias"))

#solo para el usuario administrador, accedemos a ver todos los pedidos
@app.route("/admin/pedidos")
@admin_required
def admin_pedidos():

    db = SessionLocal()

    pedidos = db.query(Pedido)\
        .order_by(Pedido.fecha.desc())\
        .all()

    return render_template("admin/pedidos.html", pedidos=pedidos)
    db.close()

#solo para el usuario administrador, accede al numero de pedido seleccionado
@app.route("/admin/pedidos/<int:id>")
@admin_required
def admin_ver_pedido(id):

    db = SessionLocal()

    pedido = db.get(Pedido, id)

    if not pedido:
        db.close()
        return "Pedido no encontrado", 404

    return render_template("admin/ver_pedido.html", pedido=pedido)
    db.close()


#solo para el usuario administrador, modificamos el estado de un pedido
@app.route("/admin/pedidos/<int:id_pedido>/estado", methods=["POST"])
@admin_required
def admin_actualizar_estado_pedido(id_pedido):

    db = SessionLocal()

    pedido = db.get(Pedido, id_pedido)

    if not pedido:
        db.close()
        return "Pedido no encontrado", 404

    nuevo_estado = request.form["estado"]

    pedido.estado = nuevo_estado

    db.commit()
    db.close()

    return redirect(url_for("admin_ver_pedido", id=id_pedido))

#solo para el usuario administrador, accedemos a la parte de mensajes del contacto
@app.route("/admin/mensajes")
@admin_required
def admin_mensajes():

    db = SessionLocal()

    mensajes = db.query(MensajeContacto)\
                 .order_by(MensajeContacto.fecha_envio.desc())\
                 .all()

    db.close()

    return render_template("admin/mensajes.html", mensajes=mensajes)

#solo para el usuario administrador, accedemos al mesaje de contacto seleccionado
@app.route("/admin/mensajes/<int:id>")
@admin_required
def admin_ver_mensaje(id):

    db = SessionLocal()
    mensaje = db.get(MensajeContacto, id)

    if not mensaje:
        db.close()
        return "Mensaje no encontrado", 404

    return render_template("admin/ver_mensaje.html", mensaje=mensaje)

@app.route("/admin/mensajes/marcar-leido/<int:id>")
@admin_required
def admin_marcar_mensaje_leido(id):

    db = SessionLocal()
    mensaje = db.get(MensajeContacto, id)

    if mensaje:
        mensaje.estado = "leido"
        db.commit()

    db.close()

    return redirect(url_for("admin_mensajes"))

#solo para el usuario administrador, marcamos el mensaje de contacto como respondido
@app.route("/admin/mensajes/marcar-respondido/<int:id>", methods=["POST"])
@admin_required
def admin_marcar_mensaje_respondido(id):

    db = SessionLocal()
    mensaje = db.get(MensajeContacto, id)

    if mensaje and mensaje.estado != "respondido":
        mensaje.estado = "respondido"
        db.commit()

    db.close()

    return redirect(url_for("admin_mensajes"))


#solo para el usuario administrador, editamos el producto seleccionado
@app.route("/admin/productos/editar/<int:id>", methods=["GET", "POST"])
@admin_required
def admin_editar_producto(id):

    db = SessionLocal()

    producto = db.get(Producto, id)
    categorias = db.query(Categoria).all()

    if not producto:
        db.close()
        return "Producto no encontrado", 404

    if request.method == "POST":

        # Actualizamos los datos
        producto.nombre_producto = request.form["nombre_producto"]
        producto.descripcion = request.form["descripcion"]
        producto.precio = float(request.form["precio"])
        producto.stock = int(request.form["stock"])
        producto.altura = float(request.form["altura"]
        )
        producto.ancho = float(request.form["ancho"])
        producto.fondo = float(request.form["fondo"])

        categorias_ids = [int(c) for c in request.form.getlist("categorias")]

        producto.categorias = db.query(Categoria)\
            .filter(Categoria.id_categoria.in_(categorias_ids))\
            .all()

        # Cambiamos la imagen principal
        imagen_principal_id = request.form.get("imagen_principal")

        if imagen_principal_id:
            for img in producto.imagenes:
                img.es_principal = (str(img.id_imagen) == imagen_principal_id)

        # eliminamos imagenes
        eliminar_ids = request.form.getlist("eliminar_imagen")

        for img in producto.imagenes[:]:
            if str(img.id_imagen) in eliminar_ids:

                # borrar archivo físico
                if os.path.exists(img.ruta_imagen):
                    os.remove(img.ruta_imagen)

                db.delete(img)

        # añadimos nuevas imagenes dentro de static/img
        imagenes = request.files.getlist("imagenes")
        # creamos la carpeta static/img, si ya existe no hace nada
        os.makedirs("static/img", exist_ok=True)

        for imagen in imagenes:

            if imagen.filename == "":
                continue

            filename = f"{producto.id_producto}_{secure_filename(imagen.filename)}"
            ruta_guardado = os.path.join("static/img", filename)

            imagen.save(ruta_guardado)

            nueva = ImagenProducto(
                producto_id=producto.id_producto,
                ruta_imagen=f"img/{filename}",
                es_principal=False
            )

            db.add(nueva)

        db.commit()
        db.close()

        return redirect(url_for("admin_productos"))

    return render_template("admin/editar_producto.html", producto=producto, categorias=categorias)

# Solo para el usuario administrador, eliminamos el producto seleccionado dentro de gestion de productos
@app.route("/admin/productos/eliminar/<int:id>")
@admin_required
def admin_eliminar_producto(id):

    db = SessionLocal()
    producto = db.get(Producto, id)

    if not producto:
        db.close()
        return "Producto no encontrado", 404

    db.delete(producto)
    db.commit()
    db.close()

    return redirect(url_for("admin_productos"))


# Solo para el usuario administrador,
@app.route("/admin/productos/nuevo", methods=["GET", "POST"])
@admin_required
def admin_nuevo_producto():

    db = SessionLocal()

    if request.method == "POST":

        # Creamos un nuevo producto
        nuevo_producto = Producto(
            nombre_producto=request.form["nombre_producto"],
            descripcion=request.form["descripcion"],
            precio=float(request.form["precio"]),
            stock=int(request.form["stock"]),
            altura=float(request.form["altura"]),
            ancho=float(request.form["ancho"]),
            fondo=float(request.form["fondo"])
        )

        # Categorías seleccionadas
        categorias_ids = request.form.getlist("categorias")
        if categorias_ids:
            categorias = db.query(Categoria).filter(
                Categoria.id_categoria.in_(categorias_ids)
            ).all()
            nuevo_producto.categorias = categorias

        db.add(nuevo_producto)
        db.commit()
        db.refresh(nuevo_producto)  #obtenemos el id_producto

        # guardamos las imagenes
        imagenes = request.files.getlist("imagenes")

        for i, imagen in enumerate(imagenes):

            if imagen.filename == "":
                continue

            # Subimos la imagen con el id de producto y nombre de la imagen para no tener problemas con imagenes que se llamen igual
            filename = f"{nuevo_producto.id_producto}_{imagen.filename}"

            ruta_guardado = os.path.join("static/img/", filename)
            imagen.save(ruta_guardado)

            nueva_imagen = ImagenProducto(
                producto_id=nuevo_producto.id_producto,
                ruta_imagen=f"img/{filename}",
                es_principal=(i == 0)  # La primera es principal
            )

            db.add(nueva_imagen)

        db.commit()
        db.close()

        return redirect(url_for("admin_productos"))

    categorias = db.query(Categoria).all()
    db.close()

    return render_template("admin/nuevo_producto.html", categorias=categorias)




# Definimos la pagina principal
@app.route('/')
def home():
    return render_template("index.html")

@app.route("/logout")
def logout(): # Con esta funcion cerramos la sesion, eliminamos lo guardado en session y redirige a la pagina pricipal
    session.clear()
    return redirect(url_for("home"))


@app.route("/login", methods=["GET", "POST"])
def login(): # Con esta funcion autenticamos a un usuario y abreimos sesion.
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        db = SessionLocal()
        usuario = db.query(Usuario).filter_by(
            email=email,
            password=password
        ).first()
        db.close()

        if usuario:
            session["usuario_id"] = usuario.id_usuario

            # Si el usuario es administrador redirige a panel admin
            if usuario.es_admin:
                return redirect(url_for("admin_panel"))

            # Si es un usuario normal redirige a home
            return redirect(url_for("home"))

    return render_template("login.html")



@app.route("/buscar")
def buscar():
    # En q metemos los datos escritos en el boton BUSCAR
    q = request.args.get("q", "").strip()

    db = SessionLocal()

    # En resultados metemos la busqueda de lo que hemos escrito en BUSCAR y miramos en nombre_producto y descripcion
    resultados = db.query(Producto).filter(
        or_(
            Producto.nombre_producto.ilike(f"%{q}%"),
            Producto.descripcion.ilike(f"%{q}%")
        )
    ).all()

    db.close()

    return render_template("buscar.html", query=q, resultados=resultados)

# Funcion para ver y modificar los datos de perfil del usuario
@app.route("/perfil")
def perfil():
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    db = SessionLocal()

    usuario = db.get(Usuario, session["usuario_id"])

    if not usuario:
        db.close()
        return redirect(url_for("login"))

    # mostramos los favoritos del usuario
    favoritos = (
        db.query(Producto)
        .join(Favorito)
        .filter(Favorito.id_usuario == usuario.id_usuario)
        .all()
    )

    # mostramos los pedidos del usuario
    pedidos = (
        db.query(Pedido)
        .options(selectinload(Pedido.lineas))
        .filter(Pedido.usuario_id == usuario.id_usuario)
        .order_by(Pedido.id_pedido.desc())
        .all()
    )

    #db.close()

    return render_template("perfil.html", usuario=usuario, favoritos=favoritos, pedidos=pedidos)

# Funcion para registrar un nuevo usuario
@app.route("/registro", methods=["GET", "POST"])
def registro():

    db = SessionLocal()

    if request.method == "POST":

        nombre = request.form["nombre"]
        apellidos = request.form["apellidos"]
        email = request.form["email"]
        password = request.form["password"]
        telefono = request.form["telefono"]
        confirmar_password = request.form["confirmar_password"]

        #comprobamos que las contraseñas coinciden
        if password != confirmar_password:
            db.close()
            return "Las contraseñas no coinciden"
        # comprobamos si el email ya existe
        usuario_existente = db.query(Usuario).filter_by(email=email).first()

        if usuario_existente:
            db.close()
            return "Este email ya está registrado"

        nuevo_usuario = Usuario(
            nombre_cliente=nombre,
            apellidos_cliente=apellidos,
            email=email,
            password=password,
            telefono=telefono,
            es_admin=False
        )

        db.add(nuevo_usuario)
        db.commit()
        db.refresh(nuevo_usuario)

        # una vez registrado el usiario hace login automatico
        session["usuario_id"] = nuevo_usuario.id_usuario


        db.close()

        return redirect(url_for("home"))

    return render_template("registro.html")

# funcion para alternar entre añadir o quitar un producto como favorito
@app.route("/favorito/<int:id_producto>")
def cambiar_favorito(id_producto):

    if "usuario_id" not in session:
        return redirect(url_for("login"))

    db = SessionLocal()
    id_usuario = session["usuario_id"]

    favorito = db.query(Favorito).filter_by(
        id_usuario=id_usuario,
        producto_id=id_producto
    ).first()

    if favorito:
        db.delete(favorito)
    else:
        db.add(Favorito(
            id_usuario=id_usuario,
            producto_id=id_producto
        ))

    db.commit()
    db.close()

    return redirect(url_for("producto_detalle", id_producto=id_producto))



# Con esta funcion mostramos los detalles de un producto
@app.route("/producto/<int:id_producto>")
def producto_detalle(id_producto):
    db = SessionLocal()

    producto = db.get(Producto, id_producto)

    if not producto:
        abort(404)

    img_activa = request.args.get("img")

    # si no se pasa imagen ponemos las primera por defecto
    if img_activa is None and producto.imagenes:
        img_activa = producto.imagenes[0].ruta_imagen

    # verificamos si es favorito
    es_favorito = False
    if "usuario_id" in session:
        favorito = db.query(Favorito).filter_by(
            id_usuario=session["usuario_id"],
            producto_id=id_producto
        ).first()
        es_favorito = favorito is not None

    db.close()

    return render_template("producto_detalle.html", producto=producto, img_activa=img_activa, es_favorito=es_favorito)

# Con esta funcion mostramos lo que contiene el carrito
@app.route("/carrito")
def ver_carrito():

    if "usuario_id" not in session:
        return redirect(url_for("login"))

    carrito = session.get("carrito", {})

    db = SessionLocal()
    productos_carrito = []
    total = 0

    for id_producto, datos in carrito.items():
        producto = db.get(Producto, int(id_producto))

        if producto:
            subtotal = producto.precio * datos["cantidad"]
            total += subtotal

            productos_carrito.append({
                "producto": producto,
                "cantidad": datos["cantidad"],
                "subtotal": subtotal
            })

    db.close()

    return render_template("carrito.html", productos_carrito=productos_carrito, total=total)


# Con esta funcion aumentamos la cantidad de un producto en el carrito
@app.route("/carrito/sumar/<int:id_producto>")
def sumar_cantidad(id_producto):

    carrito = session.get("carrito", {})
    id_str = str(id_producto)

    if id_str in carrito:
        carrito[id_str]["cantidad"] += 1

    session["carrito"] = carrito
    session.modified = True

    return redirect(url_for("ver_carrito"))

# Con esta funcion disminuimos la cantidad de un producto en el carrito
@app.route("/carrito/restar/<int:id_producto>")
def restar_cantidad(id_producto):

    carrito = session.get("carrito", {})
    id_str = str(id_producto)

    if id_str in carrito:
        carrito[id_str]["cantidad"] -= 1

        if carrito[id_str]["cantidad"] <= 0:
            del carrito[id_str]

    session["carrito"] = carrito
    session.modified = True

    return redirect(url_for("ver_carrito"))

# Con esta funcion eliminamos un producto del carrito
@app.route("/carrito/eliminar/<int:id_producto>")
def eliminar_producto(id_producto):

    carrito = session.get("carrito", {})
    id_str = str(id_producto)

    if id_str in carrito:
        del carrito[id_str]

    session["carrito"] = carrito
    session.modified = True

    return redirect(url_for("ver_carrito"))

# Con esta funcion agregamos un producto en el carrito
@app.route("/carrito/agregar/<int:id_producto>")
def agregar_carrito(id_producto):
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    carrito = session.get("carrito", {})
    id_str = str(id_producto)

    if id_str in carrito:
        carrito[id_str]["cantidad"] += 1
    else:
        db = SessionLocal()
        producto = db.get(Producto, id_producto)
        db.close()

        if not producto:
            abort(404)

        carrito[id_str] = {
            "nombre": producto.nombre_producto,
            "precio": producto.precio,
            "cantidad": 1
        }

    session["carrito"] = carrito
    session.modified = True

    return redirect(url_for("producto_detalle", id_producto=id_producto))

# Esta funcion nos sirve para contar los productos que tenemos en el carrito y mostrarlo en todas las plantillas html
@app.context_processor
def inject_carrito():
    carrito = session.get("carrito", {})

    total_items = sum(
        item["cantidad"] for item in carrito.values()
    )

    return dict(carrito_items=total_items)

# Con esta funcion mostramos las direcciones de envio
@app.route("/direcciones", methods=["GET", "POST"])
def direcciones():

    if "usuario_id" not in session:
        return redirect(url_for("login"))

    db = SessionLocal()

    usuario = db.get(Usuario, session["usuario_id"])

    # solo mostramos las direcciones activas
    direcciones_activas = [
        d for d in usuario.direcciones if d.activa
    ]

    # si el usuario ya tiene direccion activa
    if direcciones_activas:
        return render_template(
            "direccion_existente.html",
            direcciones=direcciones_activas
        )

    # si el usuario no tiene direcciobn
    if request.method == "POST":

        calle = request.form["calle"]
        numero = request.form["numero"]
        ciudad = request.form["ciudad"]
        provincia = request.form["provincia"]
        codigo_postal = request.form["codigo_postal"]
        pais = request.form["pais"]

        nueva_direccion = Direccion(
            calle=calle,
            numero=numero,
            ciudad=ciudad,
            provincia=provincia,
            codigo_postal=codigo_postal,
            pais=pais,
            usuario_id=usuario.id_usuario,
            activa=True
        )

        db.add(nueva_direccion)
        db.commit()

        return redirect(url_for("direcciones"))

    return render_template("nueva_direccion.html")

#Con esta funcion podrmos editar las direcciones que tiene asignadas el usuario
@app.route("/editar_direccion/<int:id_direccion>", methods=["GET", "POST"])
def editar_direccion(id_direccion):

    db = SessionLocal()

    direccion = db.get(Direccion, id_direccion)

    if request.method == "POST":

        direccion.calle = request.form["calle"]
        direccion.numero = request.form["numero"]
        direccion.ciudad = request.form["ciudad"]
        direccion.provincia = request.form["provincia"]
        direccion.codigo_postal = request.form["codigo_postal"]
        direccion.pais = request.form["pais"]

        db.commit()

        return redirect(url_for("direcciones"))

    return render_template("editar_direccion.html", direccion=direccion)

# Esta funcion sirve para añadir una nueva direccion
@app.route("/nueva_direccion", methods=["GET", "POST"])
def nueva_direccion():

    if "usuario_id" not in session:
        return redirect(url_for("login"))

    db = SessionLocal()

    if request.method == "POST":

        nueva = Direccion(
            usuario_id=session["usuario_id"],
            calle=request.form["calle"],
            numero=request.form["numero"],
            ciudad=request.form["ciudad"],
            provincia=request.form["provincia"],
            codigo_postal=request.form["codigo_postal"],
            pais=request.form["pais"],
            activa=True
        )

        db.add(nueva)
        db.commit()
        db.close()

        return redirect(url_for("direcciones"))

    db.close()

    return render_template("nueva_direccion.html")

# Esta funcion nos vale para eliminar una direccion, solo la desactivamos no la eliminasmo definitivamente
@app.route("/eliminar_direccion/<int:id_direccion>")
def eliminar_direccion(id_direccion):

    db = SessionLocal()

    direccion = db.get(Direccion, id_direccion)

    if not direccion:
        return "Dirección no encontrada"

    # desactivamos la direccion en vez de borrarla
    direccion.activa = False

    db.commit()

    return redirect(url_for("direcciones"))


# Con esta funcion editamos el perfil de usuario
@app.route("/editar_perfil", methods=["GET", "POST"])
def editar_perfil():

    if "usuario_id" not in session:
        return redirect(url_for("login"))

    db = SessionLocal()

    usuario = db.get(Usuario, session["usuario_id"])

    if request.method == "POST":

        usuario.nombre_cliente = request.form["nombre"]
        usuario.apellidos_cliente = request.form["apellidos"]
        usuario.email = request.form["email"]
        usuario.telefono = request.form["telefono"]

        db.commit()

        return redirect(url_for("perfil"))

    return render_template("editar_perfil.html", usuario=usuario)

#Esta funcion es para mostrar el estado de todos los pedidos que tiene el usuario
@app.route("/pedidos")
def pedidos():

    if "usuario_id" not in session:
        return redirect(url_for("login"))

    db = SessionLocal()

    pedidos = (
        db.query(Pedido)
        .filter(Pedido.usuario_id == session["usuario_id"])
        .order_by(Pedido.fecha.desc())
        .all()
    )

    return render_template("pedidos.html", pedidos=pedidos)


#Funcion para realizar el pago
@app.route("/pagar")
def pagar():

    # comprobamos que el usuario esté logueado
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    # obtenemos el carrito de la sesión
    carrito = session.get("carrito", {})

    # si el carrito está vacío volvemos al carrito
    if not carrito:
        return redirect(url_for("ver_carrito"))

    # obtenemos la dirección seleccionada en el checkout
    direccion_id = session.get("direccion_id")

    # Con esto nos aseguramos que el usuario elija una direccion antes de realizar el pago
    if not direccion_id:
        return redirect(url_for("direcciones"))

    db = SessionLocal()

    usuario_id = session["usuario_id"]

    total = 0

    # calculamos el total del pedido
    for id_producto, datos in carrito.items():

        producto = db.get(Producto, int(id_producto))

        if producto:
            subtotal = producto.precio * datos["cantidad"]
            total += subtotal

    # creamos el pedido
    pedido = Pedido(
        total=total,
        usuario_id=usuario_id,
        direccion_id=direccion_id
    )

    db.add(pedido)
    db.commit()

    # guardamos el id del pedido recién creado
    pedido_id = pedido.id_pedido

    # creamos la linea de pedido
    for id_producto, datos in carrito.items():

        producto = db.get(Producto, int(id_producto))

        if producto:

            linea = LineaPedido(
                nombre_producto=producto.nombre_producto,
                precio_unitario=producto.precio,
                cantidad=datos["cantidad"],
                pedido_id=pedido_id,
                producto_id=producto.id_producto
            )

            db.add(linea)

            # reducimos el stock del producto
            producto.stock -= datos["cantidad"]

    db.commit()
    db.close()

    # eliminamos la dirección guardada en sesión
    session.pop("direccion_id", None)

    # vaciamos el carrito
    session["carrito"] = {}
    session.modified = True

    return redirect(url_for("pedido_confirmado", id_pedido=pedido_id))


# Funcion para seleccionar la direccion antes de realizar el pago
@app.route("/seleccionar_direccion/<int:id_direccion>")
def seleccionar_direccion(id_direccion):

    # Guardamos la direccion elegida en la sesión
    session["direccion_id"] = id_direccion

    # Redirigimos al pago
    return redirect(url_for("pagar"))


#Funcion para confirmar el pedido tramitado
@app.route("/pedido/<int:id_pedido>")
def pedido_confirmado(id_pedido):

    if "usuario_id" not in session:
        return redirect(url_for("login"))

    db = SessionLocal()

    pedido = db.get(Pedido, id_pedido)

    if not pedido:
        db.close()
        abort(404)

    #con esto nos aseguramos que nadie puede poner directamente el numero de pedido en el navegador
    if pedido.usuario_id != session["usuario_id"]:
        db.close()
        abort(403)

    db.close()

    return render_template("pedido_confirmado.html", pedido=pedido)


# Con esta funcion mostramos los productos segun en la opcion que pinchemos dentro de el menu productos en la cabecera principal, en
# nav.html le el menu de producto segun el tipo de producto le paso la o las categorias que quiero que muestre
@app.route("/productos")
def productos():
    db = SessionLocal()

    categorias = request.args.getlist("categoria")

    query = db.query(Producto).options(selectinload(Producto.imagenes))

    if categorias:
        query = (
            query.join(Producto.categorias)
            .filter(Categoria.nombre_categoria.in_(categorias))
            .distinct()
        )
        titulo = " ".join(categorias)
    else:
        titulo = "Todos los productos"

    productos = query.all()
    db.close()

    return render_template("productos.html", productos=productos, titulo=titulo
    )

# Funcion creada para acceder dentro del menu Colecciones a la seccion Camas Casita
@app.route("/colecciones/camas-casita")
def coleccion_camas_casita():
    db = SessionLocal()

    productos = (
        db.query(Producto)
        .join(Producto.categorias)
        .filter(Categoria.nombre_categoria == "Camas")
        .all()
    )

    db.close()

    return render_template("colecciones_camas_casita.html", productos=productos)

# Funcion creada para acceder dentro del menu Colecciones a la seccion Muebles
@app.route("/colecciones/muebles")
def coleccion_muebles():
    db = SessionLocal()

    productos = (
        db.query(Producto)
        .options(selectinload(Producto.imagenes))
        .join(Producto.categorias)
        .filter(Categoria.nombre_categoria == "Muebles")
        .all()
    )

    db.close()

    return render_template("colecciones_muebles.html", productos=productos)

# Funcion creada para acceder dentro del menu Colecciones a la seccion Decoracion
@app.route("/colecciones/decoracion")
def coleccion_decoracion():
    db = SessionLocal()

    productos = (
        db.query(Producto)
        .options(selectinload(Producto.imagenes))
        .join(Producto.categorias)
        .filter(Categoria.nombre_categoria == "Decoracion")
        .all()
    )

    db.close()

    return render_template("colecciones_decoracion.html", productos=productos)


# Funcion creada para acceder dentro del menu Colecciones a la seccion Temporada
@app.route("/colecciones/temporada")
def coleccion_temporada():
    db = SessionLocal()

    productos = (
        db.query(Producto)
        .options(selectinload(Producto.imagenes))
        .join(Producto.categorias)
        .filter(Categoria.nombre_categoria == "Temporada")
        .all()
    )

    db.close()

    return render_template("colecciones_temporada.html", productos=productos)

# Funcion creada para acceder al menu Collecciones
@app.route("/colecciones")
def colecciones():
    return render_template("colecciones.html")

# Funcion creada para acceder al menu Experiencia
@app.route("/experiencia")
def experiencia():
    return render_template("experiencia.html")

# Funcion creada para acceder al menu Contacto
@app.route("/contacto", methods=["GET", "POST"])
def contacto():
    if request.method == "POST":

        nombre = request.form["nombre"]
        email = request.form["email"]
        telefono = request.form.get("telefono")
        mensaje = request.form["mensaje"]

        nuevo_mensaje = MensajeContacto(
            nombre=nombre,
            email=email,
            telefono=telefono,
            mensaje=mensaje
        )

        db = SessionLocal()
        db.add(nuevo_mensaje)
        db.commit()
        db.close()

        return redirect("/contacto")

    return render_template("contacto.html")

if __name__ == '__main__':


    db = SessionLocal()
    Base.metadata.drop_all(bind=engine, checkfirst=True)# reseteamos el esquema de la base de datos (estructura),
                                                          # pero no borramos la base de datos en sí, solo las tablas.
    Base.metadata.create_all(bind=engine) #creamos tablas definidas en models, no borra nada y no recrea tablas existentes.




##------------AQUI DECLARAMOS UN DATOS PARA QUE SE INTRODUZCAN EN LA BASE DE DATOS Y ASI PODER REALIZAR PRUEBAS CON LA APLICACION

####====== DECLARAMOS USUARIO DE PRUEBA
    usuarios = [
        Usuario("Juan", "Pérez", "juan1@email.com", "1234", "600000001", False),
        Usuario("Ana", "Gómez", "ana2@email.com", "1234", "600000002", False),
        Usuario("Luis", "Martín", "luis3@email.com", "1234", "600000003", False),
        Usuario("Laura", "Sánchez", "laura4@email.com", "1234", "600000004", False),
        Usuario("Carlos", "Ruiz", "carlos5@email.com", "1234", "600000005", False),
        Usuario("Marta", "López", "marta6@email.com", "1234", "600000006", False),
        Usuario("David", "Fernández", "david7@email.com", "1234", "600000007", False),
        Usuario("Sara", "Díaz", "sara8@email.com", "1234", "600000008", False),
        Usuario("Pablo", "Torres", "pablo9@email.com", "1234", "60000000", False),
        Usuario("Lucía", "Navarro", "lucia10@email.com", "1234", "600000010", False),
        Usuario("Carlos", "Viejo", "admin@email.com", "1234", "676805869", True)
    ]

####====== DECLARAMOS DIRECCIONES DE PRUEBA
    direcciones = [
        Direccion("Calle Mayor", 1, "Madrid", "Madrid", "28001", "España", "1", True),
        Direccion("Gran Vía", 25, "Madrid", "Madrid", "28013", "España", "2", True),
        Direccion("Diagonal", 100, "Barcelona", "Barcelona", "08019", "España", "3", True),
        Direccion("Serrano", 45, "Madrid", "Madrid", "28006", "España", "4", True),
        Direccion("Alameda", 12, "Sevilla", "Sevilla", "41001", "España", "5", True),
        Direccion("Colón", 8, "Valencia", "Valencia", "46004", "España", "6", True),
        Direccion("Avenida Mar", 77, "Málaga", "Málaga", "29001", "España", "56", True),
        Direccion("Plaza Norte", 3, "Bilbao", "Bizkaia", "48001", "España", "12", True),
        Direccion("Camino Real", 55, "Toledo", "Toledo", "45001", "España", "22", True),
        Direccion("Ronda Sur", 9, "Granada", "Granada", "18001", "España", "54", True),
    ]

####====== DECLARAMOS PRODUCTOS DE PRUEBA
    lista_productos = [
        Producto("Mesa Roble", "Mesa maciza de roble", 450, 10, 75, 150, 90),
        Producto("Silla Nórdica", "Silla estilo nórdico", 120, 30, 90, 45, 45),
        Producto("Estantería", "Estantería de madera", 300, 15, 180, 80, 30),
        Producto("Cama King", "Cama tamaño king", 950, 5, 60, 200, 200),
        Producto("Casita Arbol", "Casita", 400, 12, 75, 140, 70),
        Producto("Armario", "Armario empotrado", 1200, 3, 220, 180, 60),
        Producto("Banco", "Banco de madera", 180, 20, 45, 120, 40),
        Producto("Cómoda", "Cómoda clásica", 520, 8, 110, 100, 45),
        Producto("Mesilla", "Mesilla de noche", 150, 25, 55, 50, 40),
        Producto("Vitrina", "Vitrina de cristal", 780, 4, 200, 90, 40),
        Producto("Zorro", "Zorrillos de decoracion", 50, 25, 90, 45, 4),
        Producto("Escritorio", "Escritorio de decoracion", 170, 25, 90, 45, 4),
        Producto("Papa Noel", "Papa Noel de decoracion", 70, 25, 90, 45, 4),
        Producto("Llavero Papa Noel", "Llavero decoracion", 10, 25, 90, 45, 4),
        Producto("Arbol", "Arbol decoracion", 30, 25, 90, 45, 4),
        Producto("Litera Casita", "Litera Infantil", 1130, 25, 90, 45, 4),
        Producto("Casita Arbol Deluxe", "Casita Deluxe", 5400, 12, 75, 140, 70),
        Producto("Cabeceros", "Cabeceros variados", 100, 12, 75, 140, 70),
        Producto("Cama Infantil", "Cama Infantil", 300, 12, 75, 140, 70),
        Producto("Zorrillos", "Zorrillos decoracion", 60, 12, 75, 140, 70),
        Producto("Pueblos", "Pueblos decoracion", 60, 12, 75, 140, 70),
        Producto("Renos", "Renos decoracion", 60, 12, 75, 140, 70),
    ]

####====== DECLARAMOS CATEGORIAS DE PRUEBA

    categorias = [
        Categoria("Salón"),
        Categoria("Dormitorio"),
        Categoria("Casitas"),
        Categoria("Camas"),
        Categoria("Exterior"),
        Categoria("Infantiles"),
        Categoria("Almacenaje"),
        Categoria("Temporada"),
        Categoria("Muebles"),
        Categoria("Minimalista"),
        Categoria("Arbol"),
        Categoria("Mesa"),
        Categoria("Cabecero"),
        Categoria("Decoracion"),
    ]

####====== DECLARAMOS IMAGENES DE PRUEBA

    imagenes = [
        ImagenProducto(1, "img/mesa_roble.jpg", True),
        ImagenProducto(2, "img/silla_nordica.jpg", True),
        ImagenProducto(3, "img/estanteria.jpg", True),
        ImagenProducto(4, "img/cama_king_01.jpg", True),
        ImagenProducto(4, "img/cama_king_02.jpg", False),
        ImagenProducto(4, "img/cama_king_03.jpg", False),
        ImagenProducto(5, "img/casita_arbol_01.jpg", True),
        ImagenProducto(5, "img/casita_arbol_02.jpg", False),
        ImagenProducto(6, "img/armario.jpg", True),
        ImagenProducto(7, "img/banco.jpg", True),
        ImagenProducto(8, "img/comoda.jpg", True),
        ImagenProducto(9, "img/mesilla.jpg", True),
        ImagenProducto(10, "img/mueble_vitrina_01.jpg", True),
        ImagenProducto(11, "img/decoracion_01.jpg", True),
        ImagenProducto(12, "img/escritorio.jpg", True),
        ImagenProducto(13, "img/papa_noel.jpg", True),
        ImagenProducto(14, "img/Lavero_papanoel.jpg", True),
        ImagenProducto(15, "img/arbol.jpg", True),
        ImagenProducto(16, "img/litera_casita_11.jpg", True),
        ImagenProducto(17, "img/casita_arbol_11.jpg", True),
        ImagenProducto(18, "img/cabecero_04.jpg", True),
        ImagenProducto(18, "img/cabecero_01.jpg", False),
        ImagenProducto(18, "img/cabecero_02.jpg", False),
        ImagenProducto(18, "img/cabecero_03.jpg", False),
        ImagenProducto(19, "img/cama_infantil_01.jpg", True),
        ImagenProducto(20, "img/zorrillos_02.jpg", True),
        ImagenProducto(21, "img/pueblo_01.jpg", True),
        ImagenProducto(22, "img/renos_02.jpg", True),
        ImagenProducto(22, "img/renos_01.jpg", False),
    ]

####====== DECLARAMOS PEDIDOS DE PRUEBA

    pedidos = [
        Pedido(750, 1, "pagado", 1),
        Pedido(2990, 2, "enviado",2),
        Pedido(900, 3, "entregado", 3),
        Pedido( 1200,1,"preparando", 1),
    ]
    # ===== PEDIDOS =====
    db.add_all(pedidos)
    db.commit()

####====== DECLARAMOS LAS LINEAS DE PEDIDO CORRESPONDIENTES A LOS PEDIDOS REALIZADOS DE PRUEBA

    lineas_pedido = [
        LineaPedido("Mesa Roble", 450, 1, 1, 1),
        LineaPedido("Silla Nórdica", 120, 1, 1, 2),
        LineaPedido("Banco", 180, 1, 1, 7),
        LineaPedido("Cama King", 950, 1, 2, 4),
        LineaPedido("Mesilla", 150, 1, 2, 9),
        LineaPedido("Cómoda", 520, 1, 2, 8),
        LineaPedido("Armario", 1200, 1, 2, 6),
        LineaPedido("Escritorio", 170, 1, 2, 12),
        LineaPedido("Mesa Roble", 450, 1, 3, 1),
        LineaPedido("Silla Nórdica", 120, 2, 3, 2),
        LineaPedido("Banco", 180, 1, 3, 7),
        LineaPedido("Llavero Papa Noel", 10, 3, 3, 14),
        LineaPedido( "Estanteria", 300, 4,4,3),
    ]
    # ===== LINEAS DE PEDIDOS =====
    db.add_all(lineas_pedido)
    db.commit()

####====== DECLARAMOS MENSAJES DE CONTACTO DE PRUEBA

    mensajes_contacto = [

        MensajeContacto(
            "Laura Martínez",
            "laura.martinez@gmail.com",
            "Hola, me gustaría saber si hacéis muebles a medida. Estoy interesada en una mesa de roble personalizada.",
            "612345678"
        ),

        MensajeContacto(
            "Carlos Gómez",
            "carlosgomez@hotmail.com",
            "Buenas tardes, ¿cuál es el plazo de entrega aproximado para una Cama King?",
            "699112233"
        ),

        MensajeContacto(
            "Marta Sánchez",
            "marta.sanchez@yahoo.es",
            "He realizado un pedido pero no he recibido el correo de confirmación. ¿Podríais revisarlo?",
            "655443322"
        ),

        MensajeContacto(
            "Javier Ruiz",
            "jruiz@email.com",
            "Estoy interesado en comprar varias sillas nórdicas para un restaurante. ¿Ofrecéis descuentos por volumen?",
            "677889900"
        ),

        MensajeContacto(
            "Ana López",
            "ana.lopez@gmail.com",
            "¿Es posible recoger el pedido en tienda en lugar de envío a domicilio?",
            "600123987"
        )

    ]

    # ===== MENSAJE CONTACTOS =====
    db.add_all(mensajes_contacto)
    db.commit()

    # ===== USUARIOS =====
    db.add_all(usuarios)
    db.commit()

    # ===== DIRECCIONES =====
    db.add_all(direcciones)
    db.commit()

    # ===== PRODUCTOS =====
    db.add_all(lista_productos)
    db.commit()

    # ===== CATEGORIAS =====
    db.add_all(categorias)
    db.commit()

####====== DECLARAMOS LAS RELACIONES DE PRODUCTO Y SUS CATEGORIAS

    # ===== RELACIÓN N:N PRODUCTO ↔ CATEGORIA =====
    lista_productos[0].categorias.extend([categorias[0], categorias[9], categorias[11]])  #  → Salón, Muebles, Mesa
    lista_productos[1].categorias.extend([categorias[0], categorias[9]])  # Silla → Salón, Minimalista
    lista_productos[2].categorias.extend([categorias[8]])  # Estantería → Almacenaje
    lista_productos[3].categorias.extend([categorias[3], categorias[5]])  # Cama → Infantiles
    lista_productos[4].categorias.extend([categorias[2], categorias[10]])  # Casitas -> Arbol
    lista_productos[5].categorias.extend([categorias[1], categorias[6], categorias[9]])  # Dormitorio → Almacenaje -> Muebles
    lista_productos[6].categorias.extend([categorias[8]])  # Banco → Mueble
    lista_productos[7].categorias.extend([categorias[8]])  # Cómoda → Clásico
    lista_productos[8].categorias.extend([categorias[8]])  # Mesilla → Dormitorio
    lista_productos[9].categorias.extend([categorias[8]])  # Vitrina → Mueble
    lista_productos[10].categorias.extend([categorias[13]])  # Decoracion
    lista_productos[11].categorias.extend([categorias[8]])  # Temporada
    lista_productos[12].categorias.extend([categorias[7], categorias[13]])  # Temporada
    lista_productos[13].categorias.extend([categorias[7], categorias[13]])  # Temporada
    lista_productos[14].categorias.extend([categorias[7], categorias[13]])  # Temporada
    lista_productos[15].categorias.extend([categorias[1], categorias[3], categorias[5]])  # Dormitorio -> Cama -> Infantil
    lista_productos[16].categorias.extend([categorias[2], categorias[10]])  # Casitas -> Arbol
    lista_productos[17].categorias.extend([categorias[1], categorias[3], categorias[5], categorias[12]])  # Dormitorio → Cama → Infantiles -> Cabecero
    lista_productos[18].categorias.extend([categorias[1], categorias[3], categorias[5]])  # Dormitorio → Cama → Infantiles -> Cabecero
    lista_productos[19].categorias.extend([categorias[13]])  # Temporada
    lista_productos[20].categorias.extend([categorias[13]])  # Temporada
    lista_productos[21].categorias.extend([categorias[7], categorias[13]])   # Temporada -> Decoracion
    db.commit()

    # ===== IMÁGENES =====
    db.add_all(imagenes)
    db.commit()



    app.run(debug=True, port=5001) # Arranca el servidor de desarrollo de Flask.
