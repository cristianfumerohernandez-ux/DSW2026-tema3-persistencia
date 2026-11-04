import os
from werkzeug.utils import secure_filename
from flask import Flask, redirect, render_template, url_for, request, make_response, session, flash
from app.models import db, Producto
from app.forms import ProductoForm
from datetime import timedelta
from flask_debugtoolbar import DebugToolbarExtension

app = Flask(__name__)

#The toolbar is only enable in debug mode
app.debug = True

app.config["SECRET_KEY"] = "contraseña"

toolbar = DebugToolbarExtension(app)

# Configuración de la base de datos (En local = SQLite)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///tienda.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


# Configurar la carpeta destino para las imágenes
app.config["UPLOAD_FOLDER"] = os.path.join("app", "static", "img", "uploads")
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024  # Límite de 2MB por seguridad

# Configuración vida útil del las sesiones permanentes (2 días)
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=2)


# Vinculamos SQLAlchemy con nuestra aplicación de Flask
db.init_app(app)

with app.app_context():
    db.create_all()  # Crea las tablas en la base de datos (si no existieran)

    if not Producto.query.first():
        nuevo_producto = Producto(
            nombre="Teclado Mecánico RGB",
            precio=49.99,
        )
        db.session.add(nuevo_producto)
        db.session.commit()
        print(">>>>> Producto de prueba insertado en la BD <<<<<<<<<")


@app.route("/")
def home():
    return redirect(url_for("mostrar_catalogo"))


@app.route("/catalogo")
def mostrar_catalogo():
    productos = Producto.query.all()
    ultimo = request.cookies.get("ultimo_visto")
    
    return render_template("catalogo.html", lista_productos=productos, ultimo_visto = ultimo)


@app.route("/producto_nuevo", methods=["GET", "POST"])
def crear_producto():
    form = ProductoForm()
    if form.validate_on_submit():
        # Llega con POST
        nombre_imagen=None

        # Procesar el upload de la imagen
        if form.archivo_imagen.data :  # Chequea si se sube una imagen
            archivo = form.archivo_imagen.data
            nombre_imagen = secure_filename(archivo.filename)

            # Asegurar que la ruta existe
            os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

            # Guardar el fichero
            archivo.save(os.path.join(app.config["UPLOAD_FOLDER"], nombre_imagen))

        nuevo_producto = Producto(
            nombre=form.nombre.data,
            precio=form.precio.data,
            disponible=form.disponible.data,
            imagen=nombre_imagen
        )
        db.session.add(nuevo_producto)
        db.session.commit()
        # Patrón PRG: redirigir después de procesar
        return redirect(url_for("mostrar_catalogo"))
    # Llega con GET

    return render_template("producto_form.html", form=form)


@app.route("/producto/<int:prod_id>/editar", methods=["GET", "POST"])
def editar_producto(prod_id):
    producto = db.get_or_404(Producto, prod_id)

    form = ProductoForm(obj=producto)
    
    if form.validate_on_submit():
        # Se actualizan los datos
        producto.nombre = form.nombre.data
        producto.precio = form.precio.data
        producto.disponible = form.disponible.data

        # Procesar el upload de la imagen
        if form.archivo_imagen.data:  # Chequea si se sube una imagen
            archivo = form.archivo_imagen.data
            nombre_imagen = secure_filename(archivo.filename)
        
            # Asegurar que la ruta existe
            os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
        
            # Guardar el fichero
            archivo.save(os.path.join(app.config["UPLOAD_FOLDER"], nombre_imagen))
            #Eliminar el archivo anterior:
            if producto.imagen and producto.imagen != nombre_imagen:
                ruta_antigua = os.path.join(app.config["UPLOAD_FOLDER"], producto.imagen)
                if os.path.exists(ruta_antigua):
                    os.remove(ruta_antigua)
            producto.imagen = nombre_imagen
            
            
            
        db.session.commit()
        return redirect(url_for("mostrar_catalogo"))
    
    return render_template("producto_form.html", form=form, titulo="Editar producto", producto = producto)


@app.route("/producto/<int:prod_id>/eliminar", methods=["POST"])
def eliminar_producto(prod_id):
    producto = db.get_or_404(Producto, prod_id)
    db.session.delete(producto)
    db.session.commit()
    return redirect(url_for("mostrar_catalogo"))

@app.route("/producto/<int:prod_id>")
def ver_producto(prod_id):
    producto = db.get_or_404(Producto, prod_id)
    
    respuesta = make_response(render_template("producto_detalle.html", producto = producto))
    #Crea la Cookie
    respuesta.set_cookie(
        "ultimo_visto",
        value=producto.nombre,
        max_age= 60 * 60 * 24 * 7,
        httponly= True,
        samesite= "Lax"
    )
    return respuesta

@app.route("/carrito/anadir/<int:prod_id>", methods = ["POST"])
def anadir_al_carrito(prod_id):
    session.permanent = True
    
    if "carrito" not in session:
        session["carrito"] = []
        
    session["carrito"].append(prod_id)

    session.modified = True
    
    flash("añadido el producto al carrito", "exito")
    
    return redirect(url_for('mostrar_catalogo'))

# 2. Ver el contenido del carrito
@app.route("/carrito")
def ver_carrito():
    # Obtenemos la lista de IDs (o una lista vacía si no hay carrito)
    ids_carrito = session.get("carrito", [])
    
    # Consultamos en la base de datos los productos cuyos IDs estén en la lista
    if ids_carrito:
        productos_carrito = Producto.query.filter(Producto.id.in_(ids_carrito)).all()
    else:
        productos_carrito = []
        
    return render_template("carrito.html", productos=productos_carrito)

# 3. Vaciar el carrito (vía POST)
@app.route("/carrito/vaciar", methods=["POST"])
def vaciar_carrito():
    # Eliminamos únicamente la clave 'carrito' de la sesión
    session.pop("carrito", None)
    flash("Has vaciado tu carrito de la compra.", "info")
    return redirect(url_for("mostrar_catalogo"))

@app.route("/carrito/elimnar/<int:prod_id>", methods = ["POST"])
def eliminar_elemento_carrito(prod_id):
    ids_carrito = session.get("carrito")
    if prod_id in ids_carrito:
        session["carrito"].remove(prod_id)
        session.modified = True
        flash("Producto eliminado", "exito")
        return redirect(url_for("ver_carrito"))
    else:
        flash("No hay producto", "error")

if __name__ == "__main__":
    app.run(debug=True)
